# -*- coding: utf-8 -*-
"""
run_update.py - DB 定期更新のオーケストレーター

J-STAGE 差分取得 → PubMed 取得 → ノイズ除去 → タグ付け → DB 構築 → index.html 生成
を順に実行し、更新前（コミット済みの index.html に埋め込まれた DB）と比較した
更新レポートを update_reports/ に出力する。
欠落の疑い（件数の大幅減少など）があれば、レポートを書いたうえで終了コード 1 で停止する。

Usage:
    python run_update.py                 # 全工程
    python run_update.py --skip-fetch    # 取得を省略し、data/pubmed/pubmed_all_merged.json から再構築

環境変数:
    NCBI_API_KEY / NCBI_EMAIL  PubMed 取得に使用（任意。scrape_pubmed.py 参照）
    PR_BODY_PATH               指定するとプルリクエスト本文用の要約をこのパスに書く
    GITHUB_STEP_SUMMARY        GitHub Actions 上では要約を実行結果ページにも出力する
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import EVIDENCE_MAP_PATH, INTEGRATED_DB_PATH, PROJECT_ROOT

REPORT_DIR = PROJECT_ROOT / "update_reports"

FETCH_STEPS = ["update_jstage.py", "scrape_pubmed.py"]
BUILD_STEPS = ["clean_pubmed.py", "tagger_v3.py", "build_integrated_db_v4.py", "build_html_v4.py"]

TAG_KEYS = ("d", "sx", "int", "sd", "set")

# 停止条件（これを下回る＝取得または処理で欠落した疑い）
MIN_TOTAL_RATIO = 0.98      # 総数が前回の98%未満
MIN_PUBMED_RATIO = 0.95     # PubMed が前回の95%未満
WARN_GROWTH = 0.20          # 総数が20%超増えたら入力データの変化を疑う
WARN_UNTAGGED_PP = 5.0      # タグ未付与率が5pp超悪化したら警告


# ── DB の読み込みと集計 ─────────────────────────────

def load_db_from_html(path: Path):
    """index.html に埋め込まれた `const DB = {...}` を取り出す。無ければ None"""
    if not path.exists():
        return None
    s = path.read_text(encoding="utf-8")
    i = s.find("const DB = ")
    if i < 0:
        return None
    obj, _ = json.JSONDecoder().raw_decode(s, s.index("{", i))
    return obj


def article_key(a: dict) -> str:
    return a.get("l") or a.get("doi") or a.get("t", "")


def _latest_year(arts, source):
    ys = [int(a["y"]) for a in arts if a.get("s") == source and str(a.get("y", "")).isdigit()]
    return max(ys) if ys else None


def summarize(db: dict) -> dict:
    arts = db["articles"]
    by_src = Counter(a.get("s") for a in arts)
    return {
        "total": len(arts),
        "jp": by_src.get("jp", 0),
        "pm": by_src.get("pm", 0),
        "with_abstract": sum(1 for a in arts if a.get("ab")),
        "untagged": sum(1 for a in arts if not any(a.get(k) for k in TAG_KEYS)),
        "foreign": sum(1 for a in arts if a.get("fgn")),
        "latest_jp": _latest_year(arts, "jp"),
        "latest_pm": _latest_year(arts, "pm"),
    }


def diff_dbs(prev: dict, new: dict):
    """(新たに載った記事, 前回あって今回無い記事) を返す"""
    pk = {article_key(a): a for a in prev["articles"]}
    nk = {article_key(a): a for a in new["articles"]}
    added = [nk[k] for k in nk if k not in pk]
    removed = [pk[k] for k in pk if k not in nk]
    return added, removed


def count_duplicates(db: dict) -> int:
    keys = [article_key(a) for a in db["articles"]]
    return len(keys) - len(set(keys))


# ── 判定 ─────────────────────────────────────────

def check_gates(prev_sum, new_sum, n_dupes: int, today_year: int):
    """(errors, warnings)。errors があれば更新を採用しない"""
    errors, warnings = [], []
    if n_dupes:
        errors.append(f"記事の重複キーが {n_dupes} 件あります")
    if prev_sum:
        if new_sum["total"] < prev_sum["total"] * MIN_TOTAL_RATIO:
            errors.append(f"総数が減少しました: {prev_sum['total']:,} → {new_sum['total']:,}"
                          f"（前回の{MIN_TOTAL_RATIO:.0%}未満）")
        if new_sum["pm"] < prev_sum["pm"] * MIN_PUBMED_RATIO:
            errors.append(f"PubMed 件数が減少しました: {prev_sum['pm']:,} → {new_sum['pm']:,}"
                          f"（前回の{MIN_PUBMED_RATIO:.0%}未満）")
        if new_sum["jp"] < prev_sum["jp"]:
            errors.append(f"J-STAGE 件数が減少しました: {prev_sum['jp']:,} → {new_sum['jp']:,}")
        growth = new_sum["total"] / prev_sum["total"] - 1
        if growth > WARN_GROWTH:
            warnings.append(f"総数が {growth:+.0%} 増加しました。新着論文だけでなく、入力データ・"
                            "検索式・フィルタの違いによる増加を含む可能性があります（下記の内訳を参照）")
        pp = (new_sum["untagged"] / new_sum["total"] - prev_sum["untagged"] / prev_sum["total"]) * 100
        if pp > WARN_UNTAGGED_PP:
            warnings.append(f"タグ未付与の割合が {pp:+.1f}pp 悪化しました。新着にカテゴリ辞書が合っていない可能性があります")
    if new_sum["latest_jp"] is not None and new_sum["latest_jp"] < today_year - 1:
        warnings.append(f"J-STAGE の最新発行年が {new_sum['latest_jp']} 年です。"
                        "J-STAGE への掲載が止まっていないか確認してください")
    if new_sum["latest_pm"] is not None and new_sum["latest_pm"] < today_year - 1:
        warnings.append(f"PubMed の最新発行年が {new_sum['latest_pm']} 年です。取得が古いままの可能性があります")
    return errors, warnings


# ── レポート ─────────────────────────────────────

def _esc(text: str) -> str:
    return (text or "").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def _delta(a, b) -> str:
    return "—" if a is None else f"{b - a:+,}"


def render_summary(today, prev_sum, new_sum, added, removed, errors, warnings, today_year) -> str:
    recent = [a for a in added if str(a.get("y", "")).isdigit() and int(a["y"]) >= today_year - 1]
    src = Counter(a.get("s") for a in added)
    lines = [f"# DB更新レポート {today}", ""]
    if errors:
        lines += ["## ❌ 停止条件に該当", ""] + [f"- {e}" for e in errors] + [""]
    if warnings:
        lines += ["## ⚠️ 要確認", ""] + [f"- {w}" for w in warnings] + [""]
    lines += ["## 件数", "", "| 項目 | 前回 | 今回 | 差 |", "|---|---:|---:|---:|"]
    rows = [("総数", "total"), ("J-STAGE", "jp"), ("PubMed", "pm"), ("抄録あり", "with_abstract"),
            ("タグ未付与", "untagged"), ("外国所属フラグ", "foreign")]
    for label, k in rows:
        p = prev_sum[k] if prev_sum else None
        lines.append(f"| {label} | {'—' if p is None else f'{p:,}'} | {new_sum[k]:,} | {_delta(p, new_sum[k])} |")
    prev_latest = "—" if not prev_sum else "%s / %s" % (prev_sum["latest_jp"], prev_sum["latest_pm"])
    new_latest = "%s / %s" % (new_sum["latest_jp"], new_sum["latest_pm"])
    lines += [f"| 最新発行年（J-STAGE / PubMed） | {prev_latest} | {new_latest} | |", ""]
    lines += [
        "## 新着の内訳", "",
        f"- 新たに載った記事: **{len(added):,} 件**（J-STAGE {src.get('jp', 0):,} / PubMed {src.get('pm', 0):,}）",
        f"  - うち発行年が {today_year - 1} 年以降（新着論文の候補）: {len(recent):,} 件",
        f"  - うち発行年が {today_year - 2} 年以前（収録範囲の拡大・遡及登録など）: {len(added) - len(recent):,} 件",
        f"- 前回あって今回無い記事: **{len(removed):,} 件**", "",
    ]
    return "\n".join(lines)


def render_report(summary: str, added, removed) -> str:
    out = [summary, "## 新着一覧（発行年の新しい順）", ""]
    by_year = defaultdict(list)
    for a in added:
        by_year[str(a.get("y", "不明"))].append(a)
    for y in sorted(by_year, reverse=True):
        out += [f"### {y}（{len(by_year[y])}件）", ""]
        for a in sorted(by_year[y], key=lambda x: x.get("t", "")):
            out.append(f"- [{_esc(a.get('t', ''))}]({a.get('l', '')}) — {_esc(a.get('j', ''))}")
        out.append("")
    if removed:
        out += ["## 前回あって今回無い記事", ""]
        for a in sorted(removed, key=lambda x: (str(x.get("y", "")), x.get("t", ""))):
            out.append(f"- {a.get('y', '')} [{_esc(a.get('t', ''))}]({a.get('l', '')}) — {_esc(a.get('j', ''))}")
        out.append("")
    return "\n".join(out)


# ── 実行 ─────────────────────────────────────────

def run_step(script: str):
    print(f"\n{'=' * 60}\n▶ {script}\n{'=' * 60}", flush=True)
    subprocess.run([sys.executable, script], cwd=PROJECT_ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description="DB 定期更新")
    parser.add_argument("--skip-fetch", action="store_true", help="取得を省略し、保存済みの PubMed データから再構築")
    args = parser.parse_args()

    today = datetime.date.today()
    prev = load_db_from_html(EVIDENCE_MAP_PATH)
    prev_sum = summarize(prev) if prev else None
    print(f"更新前: {prev_sum['total']:,} 件" if prev_sum else "更新前: なし（初回）")

    try:
        for script in ([] if args.skip_fetch else FETCH_STEPS) + BUILD_STEPS:
            run_step(script)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {e.cmd[-1]} が失敗しました（終了コード {e.returncode}）。"
              "更新を採用しないでください。\n作業ツリーを戻すには: git checkout -- index.html data/merged_metadata.json",
              file=sys.stderr)
        sys.exit(1)

    with open(INTEGRATED_DB_PATH, encoding="utf-8") as f:
        new = json.load(f)
    new_sum = summarize(new)
    added, removed = diff_dbs(prev, new) if prev else (new["articles"], [])
    errors, warnings = check_gates(prev_sum, new_sum, count_duplicates(new), today.year)

    summary = render_summary(today.isoformat(), prev_sum, new_sum, added, removed, errors, warnings, today.year)
    REPORT_DIR.mkdir(exist_ok=True)
    report_path = REPORT_DIR / f"{today.isoformat()}.md"
    report_path.write_text(render_report(summary, added, removed), encoding="utf-8")
    print(f"\nレポート: {report_path}")
    print(summary)

    if os.environ.get("PR_BODY_PATH"):
        Path(os.environ["PR_BODY_PATH"]).write_text(
            summary + f"\n詳細（新着一覧つき）: `update_reports/{today.isoformat()}.md`\n", encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary + "\n")

    if errors:
        print("\n❌ 停止条件に該当したため、更新を採用しません。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
