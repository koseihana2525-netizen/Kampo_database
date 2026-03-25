"""
Duagnosis Kampo KB - 論文フィルター
分析対象の選定（Inclusion/Exclusion）

除外基準:
  1. 学会イベント（学術総会、セミナー、シンポジウム等）
  2. 学会運営（プログラム、目次、訂正、名簿等）
  3. 追悼・記念記事
  4. 書評・図書紹介

採用基準:
  除外されなかった論文のうち、タイトルに方剤名を1つ以上含むもの

Usage:
    python filter.py                  # フィルタリングレポート表示
    python filter.py --export         # フィルタ結果をdata/metadata_filtered.jsonに保存
"""

import argparse
import json
import re
from collections import Counter

from config import DATA_DIR, METADATA_PATH
from dictionaries import FORMULAS, EXTRA_FORMULAS


# ── 除外キーワード ──
EXCLUDE_KEYWORDS = {
    "学会イベント": [
        "学術総会", "セミナー", "シンポジウム", "ワークショップ",
        "講習会", "研修会", "質疑応答", "パネルディスカッション",
        "市民公開講座", "教育セッション", "ランチョン",
    ],
    "学会運営": [
        "プログラム", "日程", "会告", "名簿", "会則", "役員",
        "目次", "索引", "正誤", "訂正", "編集後記", "投稿規定",
        "事務局", "会員へ", "お知らせ", "各位に対する",
    ],
    "追悼/記念": [
        "追悼", "逝去", "哀悼", "祝辞", "挨拶", "就任",
    ],
    "書評/紹介": [
        "書評", "新刊紹介", "図書紹介",
    ],
}

# 方剤名パターン（辞書にない方剤もキャッチ）
FORMULA_PATTERN = re.compile(r'[\u4e00-\u9fff]{2,8}(?:湯|散|丸|飲|膏)')


def load_metadata(path=None):
    path = path or str(METADATA_PATH)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_formula_names_set():
    """辞書に登録された全方剤名のセット"""
    names = set()
    for info in FORMULAS.values():
        names.add(info["name"])
        for alias in info.get("aliases", []):
            names.add(alias)
    for info in EXTRA_FORMULAS.values():
        names.add(info["name"])
        for alias in info.get("aliases", []):
            names.add(alias)
    return names


def classify_article(title):
    """論文を分類する

    Returns:
        (status, reason)
        status: "excluded" | "included" | "no_formula"
        reason: 除外理由 or "方剤名あり" or "方剤名なし"
    """
    # Step 1: 除外判定
    for category, keywords in EXCLUDE_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return "excluded", category

    # Step 2: 方剤名の有無
    formula_names = get_all_formula_names_set()
    for name in formula_names:
        if name in title:
            return "included", "方剤名あり（辞書マッチ）"

    # パターンマッチ（辞書にない方剤）
    if FORMULA_PATTERN.search(title):
        return "included", "方剤名あり（パターンマッチ）"

    return "no_formula", "方剤名なし"


def filter_articles(articles):
    """全論文をフィルタリング"""
    results = {
        "included": [],
        "excluded": [],
        "no_formula": [],
    }
    details = []

    for art in articles:
        title = art.get("title_ja", "")
        status, reason = classify_article(title)
        results[status].append(art)
        details.append({
            "title": title,
            "status": status,
            "reason": reason,
            "pubyear": art.get("pubyear", ""),
            "doi": art.get("doi", ""),
        })

    return results, details


def print_report(results, details, articles):
    """フィルタリング結果のレポートを表示"""
    total = len(articles)
    n_included = len(results["included"])
    n_excluded = len(results["excluded"])
    n_no_formula = len(results["no_formula"])

    print("=" * 60)
    print("論文フィルタリングレポート")
    print("=" * 60)

    print(f"\n総論文数: {total}")
    print(f"  採用（方剤名あり）: {n_included} ({n_included/total*100:.1f}%)")
    print(f"  除外（非論文）    : {n_excluded} ({n_excluded/total*100:.1f}%)")
    print(f"  対象外（方剤名なし）: {n_no_formula} ({n_no_formula/total*100:.1f}%)")

    # 除外理由の内訳
    exclude_reasons = Counter(d["reason"] for d in details if d["status"] == "excluded")
    if exclude_reasons:
        print(f"\n── 除外理由の内訳 ──")
        for reason, count in exclude_reasons.most_common():
            print(f"  {reason}: {count}件")

    # 採用理由の内訳
    include_reasons = Counter(d["reason"] for d in details if d["status"] == "included")
    if include_reasons:
        print(f"\n── 採用理由の内訳 ──")
        for reason, count in include_reasons.most_common():
            print(f"  {reason}: {count}件")

    # 年別の採用数
    year_counts = Counter()
    for art in results["included"]:
        y = art.get("pubyear", "")
        if y:
            year_counts[y[:4] if len(y) >= 4 else y] += 1

    if year_counts:
        print(f"\n── 採用論文の年別分布 ──")
        for y in sorted(year_counts.keys()):
            bar = "#" * (year_counts[y] // 2)
            print(f"  {y}: {year_counts[y]:3d} {bar}")

    # 除外された論文の例
    print(f"\n── 除外論文の例 ──")
    for d in details:
        if d["status"] == "excluded":
            print(f"  [{d['reason']}] {d['title'][:50]}")
            if sum(1 for x in details if x["status"] == "excluded" and x["reason"] == d["reason"]) > 3:
                break

    # 方剤名なし論文の例
    print(f"\n── 方剤名なし論文の例（参考） ──")
    count = 0
    for d in details:
        if d["status"] == "no_formula" and d["title"]:
            print(f"  {d['title'][:60]}")
            count += 1
            if count >= 10:
                break


def main():
    parser = argparse.ArgumentParser(description="論文フィルタリング")
    parser.add_argument("--export", action="store_true", help="フィルタ結果をJSONで保存")
    args = parser.parse_args()

    articles = load_metadata()
    results, details = filter_articles(articles)

    print_report(results, details, articles)

    if args.export:
        # フィルタ済みデータを保存
        filtered_path = DATA_DIR / "metadata_filtered.json"
        with open(filtered_path, "w", encoding="utf-8") as f:
            json.dump(results["included"], f, ensure_ascii=False, indent=2)
        print(f"\n採用論文を保存: {filtered_path} ({len(results['included'])}件)")

        # フィルタリング詳細ログも保存
        log_path = DATA_DIR / "filter_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": len(articles),
                    "included": len(results["included"]),
                    "excluded": len(results["excluded"]),
                    "no_formula": len(results["no_formula"]),
                },
                "details": details,
            }, f, ensure_ascii=False, indent=2)
        print(f"フィルタリングログ: {log_path}")


if __name__ == "__main__":
    main()
