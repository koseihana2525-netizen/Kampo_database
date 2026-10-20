# -*- coding: utf-8 -*-
"""
run_gap_analysis.py - 認知ギャップの主解析（修正版 = gap_classifier の "primary"）

入力  data/integrated_db_japan.json   投稿版のデータの固定スナップショット（リポジトリには含まれない）
出力  analysis_output/gap_primary/    gitignore 対象。未公開の結果なので、公開リポジトリには載せない
        papers_classified.csv   全論文の分類（legacy と primary の両方）
        tables.md               表（件数・感度分析・論文タイプ別・MH調整・年代とトレンド・臨床研究限定・同一処方集合）

legacy は投稿版 v3 の値を作った処理の再現で、感度分析と比較のために併記する。

Usage
  python run_gap_analysis.py
  python run_gap_analysis.py --db PATH --out DIR
  python run_gap_analysis.py --verify-legacy PATH/papers_classified_v2.csv    legacy が投稿版の分類と一致するか確認して終了する
"""

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import fisher_exact
from scipy.stats.contingency import odds_ratio
from statsmodels.stats.contingency_tables import StratifiedTable

import gap_classifier as G
from analysis_set import GROUPS, NON_ARTICLE_TYPES, exclusion_reasons  # noqa: F401
from config import GAP_OUTPUT_DIR, PAPER_DB_PATH

sys.stdout.reconfigure(encoding="utf-8")

PERIODS = (("P1(~2000)", 0, 2000), ("P2(2001-10)", 2001, 2010), ("P3(2011-26)", 2011, 9999))
BINS = ((1960, 1985), (1986, 1990), (1991, 1995), (1996, 2000), (2001, 2005), (2006, 2010), (2011, 2015), (2016, 2020), (2021, 2026))

# 症例報告の定義（コード上に2つ存在した。どちらを主とするかは未決定なので両方を出す）
_CASE_A = [r"一例", r"一症例", r"1例", r"１例", r"二例", r"2例", r"２例", r"三例", r"3例", r"３例", r"\d+例", r"\d+症例",
           r"治験", r"奏効した", r"有効であった", r"が著効", r"が奏功", r"使用経験"]    # pubtype_analysis.py
_CASE_B = ["症例", "一例", "一症例", "の一例", "の1例", "1症例"]                          # run_revision_tasks.py
_CLIN = [r"臨床研究", r"臨床効果", r"臨床的検討", r"ランダム", r"無作為", r"二重盲検", r"比較試験", r"多施設", r"前向き", r"アンケート", r"調査"]
_BASIC = [r"薬理", r"in vitro", r"in vivo", r"マウス", r"ラット", r"培養", r"抽出物", r"成分", r"メカニズム"]
_REVIEW = [r"総説", r"概説", r"展望", r"考察", r"文献的", r"歴史的"]


def kampo_type(title, case_definition="A"):
    t = title or ""
    if case_definition == "A":
        if any(re.search(p, t) for p in _CASE_A):
            return "case_report"
    elif any(w in t for w in _CASE_B):
        return "case_report"
    for pats, name in ((_CLIN, "clinical_study"), (_BASIC, "basic_research"), (_REVIEW, "review_discussion")):
        if any(re.search(p, t) for p in pats):
            return name
    return "other"


def pubmed_type(pub_types):
    p = [x.lower() for x in (pub_types or [])]
    if any("case report" in x for x in p): return "case_report"
    if any("randomized controlled trial" in x for x in p): return "rct"
    if any("clinical trial" in x for x in p): return "clinical_trial"
    if any("review" in x for x in p) or any("meta-analysis" in x for x in p): return "review_meta"
    return "basic_other"


# ── 統計 ───────────────────────────────────────
def gap_pct(q1, q3):
    return q3 / (q1 + q3) * 100 if q1 + q3 else float("nan")


def exact_or(k, p):
    """k, p = (Q1, Q3)。OR = (p.Q3 * k.Q1) / (p.Q1 * k.Q3)（PubMed側が高いほど大きい）。
    条件付き最尤推定のOR、95%CI、Fisherの正確検定のp、標本OR を返す"""
    table = [[p[1], p[0]], [k[1], k[0]]]
    res = odds_ratio(table, kind="conditional")
    ci = res.confidence_interval(0.95)
    samp = (p[1] * k[0]) / (p[0] * k[1]) if p[0] * k[1] else float("inf")
    return res.statistic, ci.low, ci.high, fisher_exact(table)[1], samp


def mantel_haenszel(strata):
    """strata: [((k_Q1, k_Q3), (p_Q1, p_Q3)), ...] -> MH-OR, 95%CI, Breslow-Day の p"""
    tabs = [np.array([[p[1], p[0]], [k[1], k[0]]], dtype=float) for k, p in strata if sum(k) + sum(p) > 0 and sum(k) > 0 and sum(p) > 0]
    st = StratifiedTable(tabs)
    lo, hi = st.oddsratio_pooled_confint()
    return st.oddsratio_pooled, lo, hi, st.test_equal_odds(adjust=False).pvalue


def woolf_or(case, non):
    """kampo群内: 非症例報告 vs 症例報告のギャップのOR（標本OR、Woolf法の95%CI）"""
    o = (non[1] / non[0]) / (case[1] / case[0])
    se = math.sqrt(1 / case[0] + 1 / case[1] + 1 / non[0] + 1 / non[1])
    return o, math.exp(math.log(o) - 1.96 * se), math.exp(math.log(o) + 1.96 * se)


def q13(df, col):
    c = df[col].value_counts()
    return int(c.get("Q1_both", 0)), int(c.get("Q3_formula_only", 0))


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3g}"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ── データ ─────────────────────────────────────
def classify_all(articles):
    rows = []
    for a in articles:
        row = {"id": a["id"], "source": a["source"], "lang": a["lang"], "year": a.get("year"),
               "has_abstract": bool((a.get("abstract") or "").strip()), "title": a.get("title") or "",
               "pub_types": a.get("pub_types") or [], "mesh": a.get("mesh") or []}
        for variant in G.VARIANTS:
            c = G.classify(a, variant)
            row[f"formula_{variant}"] = c["formula"]
            row[f"formulas_{variant}"] = "|".join(c["formulas"][:5])
            for k in ("liberal", "conservative", "strict"):
                row[f"quad_{k}_{variant}"] = c["quad_" + k]
            row[f"concepts_{variant}"] = "|".join(sorted({t for t, _ in c["conservative"]}))
        rows.append(row)
    df = pd.DataFrame(rows)
    df["bracketed"] = df.title.str.strip().str.startswith("[")   # PubMed は英語以外の論文の題名を [ ] で囲む（言語欄はこのDBに無い）
    reasons = exclusion_reasons(articles)
    df["excluded"] = df["id"].isin(reasons)
    df["excluded_reason"] = df["id"].map(reasons).fillna("")
    df["year_int"] = pd.to_numeric(df["year"], errors="coerce")
    df["period"] = df["year_int"].map(lambda y: None if pd.isna(y) else next(n for n, lo, hi in PERIODS if lo <= y <= hi))
    return df


def verify_legacy(articles, csv_path):
    ref = {r["id"]: r for r in csv.DictReader(open(csv_path, encoding="utf-8-sig"))}
    bad = {}
    for a in articles:
        r, c = ref[a["id"]], G.classify(a, "legacy")
        checks = {"formula_in_text": str(c["formula"]) == r["formula_in_text"],
                  "quad_liberal": c["quad_liberal"] == r["quad_liberal"],
                  "quad_conservative": c["quad_conservative"] == r["quad_conservative"],
                  "quad_strict": c["quad_strict"] == r["quad_strict"],
                  "matched_conservative": "|".join(sorted({t for t, _ in c["conservative"]})) == r["matched_conservative"]}
        for k, ok in checks.items():
            if not ok:
                bad[k] = bad.get(k, 0) + 1
    print(f"legacy を {len(articles)} 件で再分類し、{csv_path} と比較: 不一致 {bad or 'なし'}")
    return not bad


# ── 解析 ───────────────────────────────────────
def analyses(df):
    d = df[df.has_abstract & df.source.isin(GROUPS) & ~df.excluded].copy()
    km, pm = d[d.source == "kampo"].copy(), d[d.source == "pubmed_kampo"].copy()
    km["typeA"] = km.title.map(lambda t: kampo_type(t, "A"))
    km["typeB"] = km.title.map(lambda t: kampo_type(t, "B"))
    pm["ptype"] = pm.pub_types.map(pubmed_type)
    pm["humans"] = pm.mesh.map(lambda m: "Humans" in m)
    ex = df[df.excluded]
    reason_counts = {k: int(v) for k, v in ex.excluded_reason.value_counts().items()}
    out = ["\n## 解析対象\n",
           f"抄録あり: kampo群 {int(((df.source == 'kampo') & df.has_abstract).sum())}件、pubmed_kampo群 {int(((df.source == 'pubmed_kampo') & df.has_abstract).sum())}件。"
           f"そこから除外: {len(ex)}件（{reason_counts}）→ kampo群 {len(km)}件、pubmed_kampo群 {len(pm)}件。\n"]
    for variant in ("primary", "legacy"):   # 主解析を先に出す
        col = f"quad_conservative_{variant}"
        title = "主解析（primary）" if variant == "primary" else "比較: 旧処理（legacy、投稿版 v3 の再現）"
        out.append(f"\n## {title}\n")

        k, p = q13(km, col), q13(pm, col)
        o, lo, hi, pv, samp = exact_or(k, p)
        rows = []
        for name, g in (("kampo群", km), ("pubmed_kampo群", pm)):
            c = g[col].value_counts()
            q1, q3 = q13(g, col)
            rows.append([name, len(g), int(c.get("Q1_both", 0)), int(c.get("Q2_cognition_only", 0)), q3, int(c.get("Q4_neither", 0)), q1 + q3,
                         f"{(q1 + q3) / len(g) * 100:.1f}%", f"{gap_pct(q1, q3):.1f}%"])
        out += ["### 1. 4象限（Conservative、抄録あり）", "",
                md_table(["群", "n", "Q1", "Q2", "Q3", "Q4", "処方言及", "処方言及率", "ギャップ"], rows), "",
                f"日英OR: 標本OR {samp:.2f}／条件付きMLE {o:.2f}（95%CI {lo:.2f}–{hi:.2f}）／Fisher p={pv:.3g}", ""]

        rows = []
        for name, g in (("kampo群", km), ("pubmed_kampo群", pm)):
            rows.append([name] + [f"{gap_pct(*q13(g, f'quad_{v}_{variant}')):.1f}%" for v in ("liberal", "conservative", "strict")])
        out += ["### 2. 感度分析（辞書の3段階）", "", md_table(["群", "Liberal", "Conservative", "Strict"], rows), "",
                "注: 3段階の辞書の差になる語（出血・発熱・浮腫・動悸・冷え・のぼせ・陰虚・陽虚・悪寒・潮熱・微熱 など）は、ほぼ日本語の語。"
                "英語の文章で3版が同じ結果になるのは構造上のことで、辞書設定に頑健であることの証拠ではない。", ""]

        rows = []
        for cd in ("A", "B"):
            kc = q13(km[km["type" + cd] == "case_report"], col)
            kn = q13(km[km["type" + cd] != "case_report"], col)
            o1, l1, h1 = woolf_or(kc, kn)
            pc = q13(pm[pm.ptype == "case_report"], col)
            o2, l2, h2, p2, _ = exact_or(kc, pc)
            rows.append([f"定義{cd}", f"{sum(kc)}（{gap_pct(*kc):.1f}%）", f"{sum(kn)}（{gap_pct(*kn):.1f}%）", f"{o1:.2f}（{l1:.2f}–{h1:.2f}）",
                         f"{sum(pc)}（{gap_pct(*pc):.1f}%）", f"{o2:.2f}（{l2:.2f}–{h2:.2f}）"])
        out += ["### 3. 論文タイプ別", "",
                "kampo群は鍼灸誌を含まない。症例報告の定義はA（pubtype_analysis.py）とB（run_revision_tasks.py、Methodsの記述）の両方を出す。", "",
                md_table(["症例報告の定義", "kampo 症例報告 n（ギャップ）", "kampo 非症例報告 n（ギャップ）", "kampo内 OR（症例 vs 非症例、Woolf）",
                          "PubMed 症例報告 n（ギャップ）", "日英OR（症例報告同士、条件付き）"], rows), ""]
        rows = [[t, sum(q13(km[km.typeA == t], col)), f"{gap_pct(*q13(km[km.typeA == t], col)):.1f}%"] for t in
                ("case_report", "clinical_study", "basic_research", "review_discussion", "other")]
        out += [md_table(["kampo群（定義A）のタイプ", "n", "ギャップ"], rows), ""]
        rows = [[t, sum(q13(pm[pm.ptype == t], col)), f"{gap_pct(*q13(pm[pm.ptype == t], col)):.1f}%"] for t in
                ("case_report", "rct", "clinical_trial", "review_meta", "basic_other")]
        rows += [["MeSH: Humans", sum(q13(pm[pm.humans], col)), f"{gap_pct(*q13(pm[pm.humans], col)):.1f}%"]]
        out += [md_table(["pubmed_kampo群のタイプ", "n", "ギャップ"], rows), ""]

        crude = samp
        rows = []
        for cd in ("A", "B"):
            strata = [(q13(km[(km["type" + cd] == "case_report") == flag], col), q13(pm[(pm.ptype == "case_report") == flag], col)) for flag in (True, False)]
            m, lo_, hi_, bd = mantel_haenszel(strata)
            rows.append([f"論文タイプ（症例報告の定義{cd}）", f"{m:.2f}（{lo_:.2f}–{hi_:.2f}）", f"{(m - crude) / crude * 100:+.1f}%", fmt_p(bd)])
        strata = [(q13(km[km.period == n], col), q13(pm[pm.period == n], col)) for n, _, _ in PERIODS]
        m, lo_, hi_, bd = mantel_haenszel(strata)
        rows.append(["年代（P1/P2/P3）", f"{m:.2f}（{lo_:.2f}–{hi_:.2f}）", f"{(m - crude) / crude * 100:+.1f}%", fmt_p(bd)])
        out += ["### 4. Mantel–Haenszel 調整OR", "", f"粗OR（標本）= {crude:.2f}", "",
                md_table(["調整因子", "MH-OR（95%CI）", "粗ORからの変化", "Breslow–Day p"], rows), ""]

        rows = []
        for n, _, _ in PERIODS:
            kk, pp = q13(km[km.period == n], col), q13(pm[pm.period == n], col)
            orr = (pp[1] * kk[0]) / (pp[0] * kk[1]) if pp[0] * kk[1] else float("inf")
            rows.append([n, f"{sum(kk)}（{gap_pct(*kk):.1f}%）", f"{sum(pp)}（{gap_pct(*pp):.1f}%）", f"{orr:.2f}"])
        out += ["### 5. 年代別", "", md_table(["時期", "kampo 処方言及 n（ギャップ）", "pubmed 処方言及 n（ギャップ）", "日英OR（標本）"], rows), ""]
        t = d[d[col].isin(["Q1_both", "Q3_formula_only"]) & d.year_int.notna()].copy()
        t["y"] = (t[col] == "Q3_formula_only").astype(int)
        t["dec"] = (t.year_int - 2000) / 10
        lines = []
        for src in GROUPS:
            s = t[t.source == src]
            m = sm.Logit(s.y, sm.add_constant(s[["dec"]])).fit(disp=0)
            ci = np.exp(m.conf_int().loc["dec"])
            lines.append(f"- {src}: n={len(s)}、10年あたりのOR（ギャップ側）= {np.exp(m.params['dec']):.2f}（{ci[0]:.2f}–{ci[1]:.2f}）p={m.pvalues['dec']:.3g}")
        t["pm"] = (t.source == "pubmed_kampo").astype(int)
        t["int"] = t.dec * t.pm
        m = sm.Logit(t.y, sm.add_constant(t[["dec", "pm", "int"]])).fit(disp=0)
        lines.append(f"- 交互作用（年×PubMed群）: OR {np.exp(m.params['int']):.2f}、p={m.pvalues['int']:.3g}")
        out += ["ロジスティック回帰（ギャップ = Q3 vs Q1、処方言及論文のみ）:", ""] + lines + [""]

        kc_sel = km[km.typeA.isin(["case_report", "clinical_study"])]
        pc_sel = pm[pm.ptype.isin(["case_report", "rct", "clinical_trial"])]
        rows = []
        for lab, ps in (("臨床デザイン", pc_sel), ("臨床デザイン かつ MeSH Humans", pc_sel[pc_sel.humans])):
            kk, pp = q13(kc_sel, col), q13(ps, col)
            o, lo_, hi_, pv, _ = exact_or(kk, pp)
            rows.append([lab, f"{sum(kk)}（{gap_pct(*kk):.1f}%）", f"{sum(pp)}（{gap_pct(*pp):.1f}%）", f"{o:.2f}（{lo_:.2f}–{hi_:.2f}）", f"{pv:.3g}"])
        out += ["### 6. 臨床研究に限定", "",
                "kampo群は症例報告+臨床研究（定義A）、PubMed群は症例報告+RCT+臨床試験。", "",
                md_table(["PubMed側の条件", "kampo n（ギャップ）", "pubmed n（ギャップ）", "日英OR（条件付き）", "Fisher p"], rows), ""]

    # 追加の感度分析（primary のみ）
    col = "quad_conservative_primary"
    kk, pp = q13(km, col), q13(pm, col)
    out.append("\n## 感度分析（primary）\n")
    kb = q13(km, "quad_conservative_base")
    o, lo_, hi_, pv, _ = exact_or(kb, pp)
    hits = km[(km["quad_conservative_base"] == "Q3_formula_only") & (km[col] == "Q1_both")]
    out += ["### 7. 日本語側に概念語を足さない場合（base）", "",
            "primary は、日本語の草稿が辞書Bにあると説明していた語（腹診・腹証・舌診・脈診・虚実・陰陽・寒熱・表裏・「○○湯証」）を日本語側に足している。"
            "足さない版（辞書Bは投稿版の181語のまま）の結果:", "",
            f"kampo群: Q1={kb[0]}、Q3={kb[1]}、ギャップ{gap_pct(*kb):.1f}%（primary {gap_pct(*kk):.1f}%、足した語で Q3→Q1 に移った {len(hits)}件）／"
            f"日英OR {o:.2f}（{lo_:.2f}–{hi_:.2f}）", ""]
    pm_en = pm[~pm.bracketed]
    pe = q13(pm_en, col)
    o, lo_, hi_, pv, _ = exact_or(kk, pe)
    pb = q13(pm[pm.bracketed], col)
    out += ["### 8. 英語の論文だけ（題名が [ ] で囲まれていない PubMed 記録）", "",
            f"除いた記録（非英語の論文）: {int(pm.bracketed.sum())}件（ギャップ {gap_pct(*pb):.1f}%、処方言及 {sum(pb)}件）。"
            f"残り: 処方言及 {sum(pe)}件、ギャップ{gap_pct(*pe):.1f}%、日英OR {o:.2f}（{lo_:.2f}–{hi_:.2f}）", ""]
    rows = []
    for lo, hi in BINS:
        r = [f"{lo}–{hi}"]
        for src in GROUPS:
            allr = df[(df.source == src) & (df.year_int >= lo) & (df.year_int <= hi)]
            g = d[(d.source == src) & (d.year_int >= lo) & (d.year_int <= hi)]
            q1, q3 = q13(g, col)
            r += [len(allr), f"{(len(allr) and int(allr.has_abstract.sum()) / len(allr) * 100):.1f}%", q1 + q3, f"{gap_pct(q1, q3):.1f}%" if q1 + q3 else "-"]
        rows.append(r)
    out += ["### 9. 抄録のある記録の割合と時期", "",
            "抄録のない記録は解析から外れるので、抄録保有率が時期で変わると、時期ごとのギャップの比較に選択が入る。", "",
            md_table(["期間", "kampo 全記録", "抄録あり", "処方言及 n", "ギャップ", "pubmed 全記録", "抄録あり", "処方言及 n", "ギャップ"], rows), ""]

    # 同一処方集合（primary のみ）
    names = G.tsumura_formula_names()
    col = "quad_conservative_primary"
    km2 = km.copy()
    has_c = km2["concepts_primary"].map(bool)
    f_tsu = [any(n in t for n in names) for t in (km2.title + " " + km2.abstract_text)] if "abstract_text" in km2 else None
    out.append("\n## 同一処方集合（ツムラ128処方）での日英比較（primary）\n")
    if f_tsu is not None:
        q = np.where(np.array(f_tsu) & has_c, "Q1", np.where(has_c, "Q2", np.where(f_tsu, "Q3", "Q4")))
        k1, k3 = int((q == "Q1").sum()), int((q == "Q3").sum())
        pp = q13(pm, col)
        o, lo_, hi_, pv, _ = exact_or((k1, k3), pp)
        out.append(f"kampo群（日本語側もツムラ128処方だけで処方判定）: Q1={k1}、Q3={k3}、ギャップ{gap_pct(k1, k3):.1f}% ／ "
                   f"pubmed群: ギャップ{gap_pct(*pp):.1f}% ／ OR {o:.2f}（{lo_:.2f}–{hi_:.2f}）\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="認知ギャップ主解析（修正版）")
    ap.add_argument("--db", default=str(PAPER_DB_PATH), help="integrated_db_japan.json のパス")
    ap.add_argument("--out", default=str(GAP_OUTPUT_DIR), help="出力先（gitignore 対象の場所に置くこと）")
    ap.add_argument("--verify-legacy", metavar="CSV", help="legacy が投稿版の papers_classified_v2.csv と一致するか確認して終了")
    args = ap.parse_args()

    articles = json.load(open(args.db, encoding="utf-8"))["articles"]
    print(f"{args.db}: {len(articles)} 件")
    if args.verify_legacy:
        sys.exit(0 if verify_legacy(articles, args.verify_legacy) else 1)

    df = classify_all(articles)
    abstracts = {a["id"]: (a.get("abstract") or "") for a in articles}
    df["abstract_text"] = df["id"].map(abstracts)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["abstract_text"]).to_csv(out_dir / "papers_classified.csv", index=False, encoding="utf-8-sig")
    report = "# 認知ギャップ 主解析\n\n入力: " + args.db + "\n" + analyses(df)
    (out_dir / "tables.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\n出力: {out_dir / 'tables.md'}, {out_dir / 'papers_classified.csv'}")


if __name__ == "__main__":
    main()
