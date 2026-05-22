#!/usr/bin/env python3
"""結果ドラフトv1の★箇所に必要な数値を抽出"""

import json, os, sys
import pandas as pd
import numpy as np
from scipy.stats import fisher_exact
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'data', 'integrated_db_japan.json')
CLASSIFIED = os.path.join(BASE, 'analysis_output', 'phase3', 'papers_classified_v2.csv')
PUBTYPE_CSV = os.path.join(BASE, 'analysis_output', 'phase3b_pubtype', 'pubtype_classification.csv')
OUTPUT = os.path.join(BASE, 'analysis_output', 'phase3', 'results_draft_numbers.md')

# ============================================================
# データ読み込み
# ============================================================
with open(DB_PATH, 'r', encoding='utf-8') as f:
    db_raw = json.load(f)
articles = db_raw['articles'] if isinstance(db_raw, dict) and 'articles' in db_raw else db_raw

df = pd.read_csv(CLASSIFIED)
pt = pd.read_csv(PUBTYPE_CSV)
df = df.merge(pt[['id', 'pub_type']], on='id', how='left')

# source統合列
def merge_source(s):
    return 'kampo' if s in ('kampo', 'acupuncture') else 'pubmed'
df['sg'] = df['source'].map(merge_source)

# article dict by id
art_by_id = {a['id']: a for a in articles}

qcol = 'quad_conservative'

out = []
def sec(title):
    out.append(f"\n## {title}\n")
def line(s):
    out.append(s)

out.append("# 結果ドラフト用 数値一覧\n")
out.append("> 生成日: 2026-03-30\n> データ: integrated_db_japan.json (10,535件) + Conservative v2辞書\n")

# ============================================================
# 1. 基本統計
# ============================================================
sec("1. 基本統計（セクション1用）")

line("### source別の件数・抄録保有率・年代範囲\n")
line("| source | 件数 | 抄録あり | 抄録率 | year min | year max |")
line("|--------|------|---------|--------|----------|----------|")

for src in ['kampo', 'acupuncture', 'pubmed_kampo', 'pubmed_acupuncture', 'pubmed_pharma']:
    arts = [a for a in articles if a.get('source') == src]
    n = len(arts)
    has_abs = sum(1 for a in arts if a.get('abstract', '').strip())
    years = [a.get('year') for a in arts if a.get('year')]
    yr_int = [int(y) for y in years if y]
    yr_min = min(yr_int) if yr_int else '—'
    yr_max = max(yr_int) if yr_int else '—'
    line(f"| {src} | {n} | {has_abs} | {100*has_abs/n:.1f}% | {yr_min} | {yr_max} |")

# JP合計 / PM合計
jp = [a for a in articles if a.get('source') in ('kampo', 'acupuncture')]
pm = [a for a in articles if a.get('source') not in ('kampo', 'acupuncture')]
line(f"| **JP合計** | **{len(jp)}** | {sum(1 for a in jp if a.get('abstract','').strip())} | {100*sum(1 for a in jp if a.get('abstract','').strip())/len(jp):.1f}% | | |")
line(f"| **PM合計** | **{len(pm)}** | {sum(1 for a in pm if a.get('abstract','').strip())} | {100*sum(1 for a in pm if a.get('abstract','').strip())/len(pm):.1f}% | | |")
line(f"| **総計** | **{len(articles)}** | | | | |")

# ============================================================
# 2. 4象限の生数値
# ============================================================
sec("2. 4象限の生数値（セクション2.1用）")

line("### Conservative v2辞書: source別 quadrant分布\n")

# 全source
for src in ['kampo', 'acupuncture', 'pubmed_kampo', 'pubmed_acupuncture', 'pubmed_pharma']:
    sub = df[df['source'] == src]
    n = len(sub)
    line(f"#### {src} (n={n})\n")
    line("| Quadrant | 件数 | 比率 |")
    line("|----------|------|------|")
    for q in ['Q1_both', 'Q2_cognition_only', 'Q3_formula_only', 'Q4_neither']:
        cnt = (sub[qcol] == q).sum()
        line(f"| {q} | {cnt} | {100*cnt/n:.1f}% |")
    line("")

# 統合版（kampo+acu vs pubmed全体）
line("### 統合版\n")
line("| Quadrant | kampo (JP) | pubmed (EN) |")
line("|----------|-----------|-------------|")
for q in ['Q1_both', 'Q2_cognition_only', 'Q3_formula_only', 'Q4_neither']:
    k = (df[df['sg'] == 'kampo'][qcol] == q).sum()
    p = (df[df['sg'] == 'pubmed'][qcol] == q).sum()
    kn = len(df[df['sg'] == 'kampo'])
    pn = len(df[df['sg'] == 'pubmed'])
    line(f"| {q} | {k} ({100*k/kn:.1f}%) | {p} ({100*p/pn:.1f}%) |")

# 抄録ありのみ
line("\n### 抄録あり論文のみ\n")
line("| Quadrant | kampo (JP) | pubmed (EN) |")
line("|----------|-----------|-------------|")
ka = df[(df['sg'] == 'kampo') & (df['has_abstract'] == True)]
pa = df[(df['sg'] == 'pubmed') & (df['has_abstract'] == True)]
for q in ['Q1_both', 'Q2_cognition_only', 'Q3_formula_only', 'Q4_neither']:
    k = (ka[qcol] == q).sum()
    p = (pa[qcol] == q).sum()
    line(f"| {q} | {k} ({100*k/len(ka):.1f}%) | {p} ({100*p/len(pa):.1f}%) |")
line(f"\n抄録あり: kampo={len(ka)}, pubmed={len(pa)}")

# Q3/(Q1+Q3) の確認
k_q1 = (ka[qcol] == 'Q1_both').sum()
k_q3 = (ka[qcol] == 'Q3_formula_only').sum()
p_q1 = (pa[qcol] == 'Q1_both').sum()
p_q3 = (pa[qcol] == 'Q3_formula_only').sum()
line(f"\nkampo Q3/(Q1+Q3) = {k_q3}/{k_q1+k_q3} = {100*k_q3/(k_q1+k_q3):.1f}%")
line(f"pubmed Q3/(Q1+Q3) = {p_q3}/{p_q1+p_q3} = {100*p_q3/(p_q1+p_q3):.1f}%")

# OR + 95% CI
table = [[k_q1, k_q3], [p_q1, p_q3]]
or_val, p_val = fisher_exact(table)
# 95% CI for OR (Woolf logit method)
import math
a, b, c, d = k_q1, k_q3, p_q1, p_q3
log_or = math.log(or_val)
se_log_or = math.sqrt(1/a + 1/b + 1/c + 1/d)
ci_lo = math.exp(log_or - 1.96 * se_log_or)
ci_hi = math.exp(log_or + 1.96 * se_log_or)
line(f"\nOR = {or_val:.2f} (95% CI: {ci_lo:.2f}–{ci_hi:.2f}), p = {p_val:.2e}")

# ============================================================
# 3. 時系列データ
# ============================================================
sec("3. 時系列データ（セクション4用）")

line("### 5年単位のQ3/(Q1+Q3)推移\n")

bins = [(1980, 1985), (1986, 1990), (1991, 1995), (1996, 2000),
        (2001, 2005), (2006, 2010), (2011, 2015), (2016, 2020), (2021, 2026)]

line("| 期間 | kampo Q1 | kampo Q3 | kampo gap | pubmed Q1 | pubmed Q3 | pubmed gap |")
line("|------|----------|----------|-----------|-----------|-----------|------------|")

for y0, y1 in bins:
    for sg in ['kampo', 'pubmed']:
        pass  # computed below

for y0, y1 in bins:
    vals = {}
    for sg in ['kampo', 'pubmed']:
        sub = df[(df['sg'] == sg) & (df['has_abstract'] == True) &
                 (df['year_int'] >= y0) & (df['year_int'] <= y1)]
        q1 = (sub[qcol] == 'Q1_both').sum()
        q3 = (sub[qcol] == 'Q3_formula_only').sum()
        gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else None
        vals[sg] = (q1, q3, gap)
    k = vals['kampo']
    p = vals['pubmed']
    kg = f"{k[2]:.1f}%" if k[2] is not None else "—"
    pg = f"{p[2]:.1f}%" if p[2] is not None else "—"
    line(f"| {y0}–{y1} | {k[0]} | {k[1]} | {kg} | {p[0]} | {p[1]} | {pg} |")

# トレンド分析
line("\n### kampo群のトレンド\n")
kampo_trend = []
for y0, y1 in bins:
    sub = df[(df['sg'] == 'kampo') & (df['has_abstract'] == True) &
             (df['year_int'] >= y0) & (df['year_int'] <= y1)]
    q1 = (sub[qcol] == 'Q1_both').sum()
    q3 = (sub[qcol] == 'Q3_formula_only').sum()
    if q1 + q3 > 0:
        gap = q3 / (q1 + q3) * 100
        kampo_trend.append((f"{y0}–{y1}", gap, q1 + q3))

if kampo_trend:
    best = min(kampo_trend, key=lambda x: x[1])
    worst = max(kampo_trend, key=lambda x: x[1])
    line(f"- 最小ギャップ: {best[0]} → {best[1]:.1f}% (n={best[2]})")
    line(f"- 最大ギャップ: {worst[0]} → {worst[1]:.1f}% (n={worst[2]})")
    # 最近5年 vs 全期間
    recent = [t for t in kampo_trend if '2021' in t[0] or '2016' in t[0]]
    if recent:
        line(f"- 直近期間: {recent[-1][0]} → {recent[-1][1]:.1f}%")

# ============================================================
# 4. カテゴリ別出現頻度
# ============================================================
sec("4. 認知辞書カテゴリ別の出現頻度（セクション6用）")

line("### matched_conservative列のカテゴリ分析\n")

# matched_conservative列にはマッチした用語が格納されている
# まずカテゴリ辞書を構築（phase3_analysis.pyから）
sys.path.insert(0, BASE)
try:
    from dictionaries import PATTERN_TERMS, ABDOMINAL_TERMS
except ImportError:
    PATTERN_TERMS = {}
    ABDOMINAL_TERMS = {}

# T1 additions
T1_ADDITIONS = {
    '奔豚':'classical', '奔豚気':'classical', '奔豚病':'classical', '煩躁':'classical',
    'hontonki':'classical', 'honton':'classical', 'running piglet':'classical',
    '転方':'sho_core', 'switching formula':'sho_core',
    '尿自利':'examination', '小便自利':'examination', '小便不利':'examination', '尿不利':'examination',
    'urinary dysfunction':'examination',
    '瞑眩':'epistemological', 'menken':'epistemological', 'healing crisis':'epistemological',
    'heat syndrome':'pathology',
}

# Build full term→category map from dictionaries.py
# We need to read phase3_analysis.py to get the full dictionary
# Instead, let's parse matched_conservative column directly and use the CSV data
# The matched_conservative column has comma-separated terms

# For category mapping, load from phase3_analysis.py's logic
# Since we can import dictionaries, build the map
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location('dictionaries', os.path.join(BASE, 'dictionaries.py'))
    dmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dmod)

    PTERM_CAT = {'八綱弁証':'pathology','気血津液弁証':'pathology',
                 '臓腑弁証':'pathology','六経弁証':'classical'}
    term_to_cat = {}
    for top_cat, sub in dmod.PATTERN_TERMS.items():
        cat = PTERM_CAT.get(top_cat, 'pathology')
        for subcat, tlist in sub.items():
            if isinstance(tlist, list):
                for t in tlist: term_to_cat[t] = cat
    for t in dmod.ABDOMINAL_TERMS:
        term_to_cat[t] = 'examination'

    base_extra = {
        '随証':'sho_core','弁証':'sho_core','方証相対':'sho_core',
        '証に基づ':'sho_core','証の変化':'sho_core','証を決定':'sho_core',
        '気血水':'pathology','お血':'pathology','血瘀':'pathology',
        '冷え症':'pathology','冷え性':'pathology','冷え':'pathology',
        'のぼせ':'pathology','気鬱':'pathology','気うつ':'pathology',
        '未病':'epistemological','養生':'epistemological',
        '心身一如':'epistemological','同病異治':'epistemological',
        '異病同治':'epistemological','君臣佐使':'epistemological',
        '傷寒論':'classical','金匱要略':'classical','温病':'classical',
        'sho ':'sho_core','sho-based':'sho_core','sho pattern':'sho_core',
        'pattern diagnosis':'sho_core','pattern identification':'sho_core',
        'pattern differentiation':'sho_core','ho-sho-sotai':'sho_core',
        'qi deficiency':'pathology','blood deficiency':'pathology',
        'qi stagnation':'pathology','blood stasis':'pathology',
        'blood stagnation':'pathology','oketsu':'pathology',
        'water toxin':'pathology','yin deficiency':'pathology',
        'yang deficiency':'pathology','yin-yang':'pathology',
        'cold sensitivity':'pathology','hie ':'pathology',
        'deficiency pattern':'pathology','excess pattern':'pathology',
        'kyo-jitsu':'pathology','spleen deficiency':'pathology',
        'kidney deficiency':'pathology','liver qi':'pathology',
        'taiyang':'classical','shaoyang':'classical','yangming':'classical',
        'taiyin':'classical','shaoyin':'classical','jueyin':'classical',
        'six stages':'classical','shanghan':'classical','shang han':'classical',
        'jingui':'classical',
        'fukushin':'examination','pulse diagnosis':'examination',
        'tongue diagnosis':'examination','hypochondriac fullness':'examination',
        'abdominal diagnosis':'examination','abdominal palpation':'examination',
        'mibyou':'epistemological','mibyo':'epistemological',
        'mind-body unity':'epistemological',
        'same disease different treatment':'epistemological',
    }
    for t, c in base_extra.items():
        if t not in term_to_cat: term_to_cat[t] = c
    for t, c in T1_ADDITIONS.items(): term_to_cat[t] = c
    HAS_DICT = True
except Exception as e:
    print(f"辞書構築失敗: {e}")
    HAS_DICT = False
    term_to_cat = {}

# Parse matched_conservative column
FP_HARD = {'出血','発熱','浮腫','動悸'}

if HAS_DICT:
    # For each Q1 article, extract which categories are present
    for sg_label, sg_val in [('kampo (JP)', 'kampo'), ('pubmed (EN)', 'pubmed')]:
        sub = df[(df['sg'] == sg_val) & (df['has_abstract'] == True)]
        q1_sub = sub[sub[qcol] == 'Q1_both']
        formula_sub = sub[sub[qcol].isin(['Q1_both', 'Q3_formula_only'])]
        n_q1 = len(q1_sub)
        n_formula = len(formula_sub)

        cat_counts_q1 = Counter()
        cat_counts_formula = Counter()

        for _, row in q1_sub.iterrows():
            matched = str(row.get('matched_conservative', ''))
            if matched and matched != 'nan':
                terms = [t.strip() for t in matched.split(',')]
                cats_found = set()
                for t in terms:
                    if t in term_to_cat:
                        cats_found.add(term_to_cat[t])
                for c in cats_found:
                    cat_counts_q1[c] += 1

        # Also count per formula-mentioning article (Q1+Q3)
        for _, row in formula_sub.iterrows():
            matched = str(row.get('matched_conservative', ''))
            if matched and matched != 'nan':
                terms = [t.strip() for t in matched.split(',')]
                cats_found = set()
                for t in terms:
                    if t in term_to_cat:
                        cats_found.add(term_to_cat[t])
                for c in cats_found:
                    cat_counts_formula[c] += 1

        line(f"\n#### {sg_label}\n")
        line(f"Q1論文数: {n_q1}  |  処方言及論文数(Q1+Q3): {n_formula}\n")
        line("| カテゴリ | Q1内件数 | Q1内出現率 | 処方言及内件数 | 処方言及内出現率 |")
        line("|---------|---------|-----------|-------------|---------------|")
        for cat in ['sho_core', 'pathology', 'classical', 'examination', 'epistemological']:
            c_q1 = cat_counts_q1.get(cat, 0)
            c_f = cat_counts_formula.get(cat, 0)
            line(f"| {cat} | {c_q1} | {100*c_q1/n_q1:.1f}% | {c_f} | {100*c_f/n_formula:.1f}% |")
else:
    line("*dictionaries.pyのインポートに失敗。カテゴリ別集計はスキップ。*")

# カテゴリ別の日英比較（処方言及論文ベース）
line("\n### カテゴリ別 認知概念出現率（処方言及論文ベース: Q1+Q3が分母）\n")
if HAS_DICT:
    line("| カテゴリ | kampo | pubmed | 減少率 |")
    line("|---------|-------|--------|-------|")
    k_form = df[(df['sg'] == 'kampo') & (df['has_abstract'] == True) & (df[qcol].isin(['Q1_both', 'Q3_formula_only']))]
    p_form = df[(df['sg'] == 'pubmed') & (df['has_abstract'] == True) & (df[qcol].isin(['Q1_both', 'Q3_formula_only']))]
    for cat in ['sho_core', 'pathology', 'classical', 'examination', 'epistemological']:
        k_cnt = 0
        p_cnt = 0
        for _, row in k_form.iterrows():
            matched = str(row.get('matched_conservative', ''))
            if matched and matched != 'nan':
                terms = [t.strip() for t in matched.split(',')]
                if any(term_to_cat.get(t) == cat for t in terms):
                    k_cnt += 1
        for _, row in p_form.iterrows():
            matched = str(row.get('matched_conservative', ''))
            if matched and matched != 'nan':
                terms = [t.strip() for t in matched.split(',')]
                if any(term_to_cat.get(t) == cat for t in terms):
                    p_cnt += 1
        k_pct = 100 * k_cnt / len(k_form) if len(k_form) > 0 else 0
        p_pct = 100 * p_cnt / len(p_form) if len(p_form) > 0 else 0
        reduction = ((k_pct - p_pct) / k_pct * 100) if k_pct > 0 else 0
        line(f"| {cat} | {k_pct:.1f}% ({k_cnt}/{len(k_form)}) | {p_pct:.1f}% ({p_cnt}/{len(p_form)}) | {reduction:.1f}%減 |")

# ============================================================
# 5. OR=1.88の95%CI（セクション7.1用）
# ============================================================
sec("5. 論文タイプ別OR（セクション7.1用）")

# kampo内: 症例報告 vs 非症例報告
ka_abs = df[(df['sg'] == 'kampo') & (df['has_abstract'] == True)]
case_k = ka_abs[ka_abs['pub_type'] == 'case_report']
noncase_k = ka_abs[ka_abs['pub_type'] != 'case_report']

c_q1 = (case_k[qcol] == 'Q1_both').sum()
c_q3 = (case_k[qcol] == 'Q3_formula_only').sum()
n_q1 = (noncase_k[qcol] == 'Q1_both').sum()
n_q3 = (noncase_k[qcol] == 'Q3_formula_only').sum()

line(f"\n### kampo内: 症例報告 vs 非症例報告\n")
line(f"- 症例報告: Q1={c_q1}, Q3={c_q3}, gap={100*c_q3/(c_q1+c_q3):.1f}%")
line(f"- 非症例報告: Q1={n_q1}, Q3={n_q3}, gap={100*n_q3/(n_q1+n_q3):.1f}%")

table2 = [[c_q1, c_q3], [n_q1, n_q3]]
or2, p2 = fisher_exact(table2)
log_or2 = math.log(or2)
se2 = math.sqrt(1/c_q1 + 1/c_q3 + 1/n_q1 + 1/n_q3)
ci2_lo = math.exp(log_or2 - 1.96 * se2)
ci2_hi = math.exp(log_or2 + 1.96 * se2)
line(f"- OR = {or2:.2f} (95% CI: {ci2_lo:.2f}–{ci2_hi:.2f}), p = {p2:.2e}")

# 症例報告のkampo vs pubmed
line(f"\n### 症例報告のみ: kampo vs pubmed\n")
case_p = df[(df['sg'] == 'pubmed') & (df['has_abstract'] == True) & (df['pub_type'] == 'case_report')]
ck_q1 = (case_k[qcol] == 'Q1_both').sum()
ck_q3 = (case_k[qcol] == 'Q3_formula_only').sum()
cp_q1 = (case_p[qcol] == 'Q1_both').sum()
cp_q3 = (case_p[qcol] == 'Q3_formula_only').sum()

line(f"- kampo症例報告: Q1={ck_q1}, Q3={ck_q3}, gap={100*ck_q3/(ck_q1+ck_q3):.1f}%")
line(f"- pubmed症例報告: Q1={cp_q1}, Q3={cp_q3}, gap={100*cp_q3/(cp_q1+cp_q3):.1f}%")

table3 = [[ck_q1, ck_q3], [cp_q1, cp_q3]]
or3, p3 = fisher_exact(table3)
log_or3 = math.log(or3)
se3 = math.sqrt(1/max(ck_q1,1) + 1/max(ck_q3,1) + 1/max(cp_q1,1) + 1/max(cp_q3,1))
ci3_lo = math.exp(log_or3 - 1.96 * se3)
ci3_hi = math.exp(log_or3 + 1.96 * se3)
line(f"- OR = {or3:.2f} (95% CI: {ci3_lo:.2f}–{ci3_hi:.2f}), p = {p3:.2e}")

# ============================================================
# 6. サンプリング検証の数値（セクション8用）
# ============================================================
sec("6. サンプリング検証の数値（セクション8用）")

line("""
サンプリング検証は手動レビューの結果であり、データファイルからの自動抽出は不可。
引き継ぎ文書セクション7の定性的記載を参照:

| Group | 説明 | n | 正分類 | 偽陽性 | 偽陰性 | グレー/判定不能 |
|-------|------|---|--------|--------|--------|---------------|
| A: kampo Q1 | JP思考あり | 10 | 7 | 2 | — | 1 |
| B: kampo Q3 | JP思考なし | 10 | 4 | — | 3 | 3(抄録なし2+不明1) |
| C: pubmed Q1 | EN思考あり | 10 | 3 | 2 | — | 5(TCM4+判定不能1) |
| D: pubmed Q3 | EN思考なし | 10 | 8 | — | 1 | 1 |
| **合計** | | **40** | **22** | **4** | **4** | **10** |

**注意**: これらの数値は未確定。`sampling_validation.md` の
チェックボックスは未記入（小川先生のレビュー待ち）。
上記は引き継ぎ文書の推定値。
""")

# ============================================================
# 7. 追加: 翻訳の断崖テーブル
# ============================================================
sec("7. 翻訳の断崖（セクション5用）")

cliff_csv = os.path.join(BASE, 'analysis_output', 'phase3', 'translation_cliff_v2.csv')
if os.path.exists(cliff_csv):
    cliff = pd.read_csv(cliff_csv)
    line("### translation_cliff_v2.csv の内容\n")
    line(cliff.to_csv(index=False, sep='|'))
else:
    line("*translation_cliff_v2.csv が見つかりません*")

# ============================================================
# 8. 追加: 感度分析テーブル
# ============================================================
sec("8. 感度分析（セクション3用）")

sens_csv = os.path.join(BASE, 'analysis_output', 'phase3', 'sensitivity_analysis_v2.csv')
if os.path.exists(sens_csv):
    sens = pd.read_csv(sens_csv)
    line("### sensitivity_analysis_v2.csv の内容\n")
    line(sens.to_csv(index=False, sep='|'))
else:
    line("*sensitivity_analysis_v2.csv が見つかりません*")

# ============================================================
# 出力
# ============================================================
import math  # already used above but ensure available

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print(f"Saved: {OUTPUT}")
print(f"行数: {len(out)}")
