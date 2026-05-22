#!/usr/bin/env python3
"""論文タイプ別 認知ギャップ層別分析 (Phase 3b)

integrated_db_japan.json + papers_classified_v2.csv を用いて
論文タイプ別に認知ギャップ比率を算出する。
"""

import json, os, re, sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import fisher_exact

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'data', 'integrated_db_japan.json')
CSV_PATH = os.path.join(BASE, 'analysis_output', 'phase3', 'papers_classified_v2.csv')
OUTPUT = os.path.join(BASE, 'analysis_output', 'phase3b_pubtype')
os.makedirs(OUTPUT, exist_ok=True)

# ============================================================
# Part A: 論文タイプ分類
# ============================================================

def classify_pubtype_pubmed(pub_types):
    """PubMed論文のpub_typesからカテゴリを判定"""
    if not pub_types or not isinstance(pub_types, list):
        return 'basic_other'
    pt_lower = [p.lower() for p in pub_types]
    if any('case report' in p for p in pt_lower):
        return 'case_report'
    if any('randomized controlled trial' in p for p in pt_lower):
        return 'rct'
    if any('clinical trial' in p for p in pt_lower):
        return 'clinical_trial'
    if any('meta-analysis' in p for p in pt_lower):
        return 'review_meta'
    if any('systematic review' in p for p in pt_lower):
        return 'review_meta'
    if any('review' in p for p in pt_lower):
        return 'review_meta'
    return 'basic_other'


def classify_pubtype_kampo(title):
    """東洋医学雑誌のタイトルから論文タイプを推定"""
    if not title:
        return 'other'
    case_patterns = [
        r'一例', r'一症例', r'1例', r'１例',
        r'二例', r'2例', r'２例',
        r'三例', r'3例', r'３例',
        r'\d+例', r'\d+症例',
        r'治験', r'奏効した', r'有効であった',
        r'が著効', r'が奏功',
        r'使用経験',
    ]
    for pat in case_patterns:
        if re.search(pat, title):
            return 'case_report'
    clinical_patterns = [
        r'臨床研究', r'臨床効果', r'臨床的検討',
        r'ランダム', r'無作為', r'二重盲検',
        r'比較試験', r'多施設', r'前向き',
        r'アンケート', r'調査',
    ]
    for pat in clinical_patterns:
        if re.search(pat, title):
            return 'clinical_study'
    basic_patterns = [
        r'薬理', r'in vitro', r'in vivo',
        r'マウス', r'ラット', r'培養',
        r'抽出物', r'成分', r'メカニズム',
    ]
    for pat in basic_patterns:
        if re.search(pat, title):
            return 'basic_research'
    review_patterns = [
        r'総説', r'概説', r'展望', r'考察',
        r'文献的', r'歴史的',
    ]
    for pat in review_patterns:
        if re.search(pat, title):
            return 'review_discussion'
    return 'other'


print("=" * 60)
print("Part A: データ読み込み・論文タイプ分類")
print("=" * 60)

with open(DB_PATH, 'r', encoding='utf-8') as f:
    db_raw = json.load(f)
db = db_raw['articles'] if isinstance(db_raw, dict) and 'articles' in db_raw else db_raw
print(f"DB読み込み: {len(db)}件")

csv = pd.read_csv(CSV_PATH)
print(f"CSV読み込み: {len(csv)}行")

# 論文タイプ分類
id_to_pubtype = {}
for art in db:
    aid = art['id']
    src = art.get('source', '')
    if src in ('kampo', 'acupuncture'):
        pt = classify_pubtype_kampo(art.get('title', ''))
    else:
        pt = classify_pubtype_pubmed(art.get('pub_types', []))
    id_to_pubtype[aid] = pt

csv['pub_type'] = csv['id'].map(id_to_pubtype)

# source統合: kampo/acupuncture → "kampo", pubmed_* → "pubmed"
def merge_source(s):
    if s in ('kampo', 'acupuncture'):
        return 'kampo'
    return 'pubmed'

csv['source_group'] = csv['source'].map(merge_source)

# 分類分布
print("\n=== 論文タイプ分類結果 ===")
for sg in ['kampo', 'pubmed']:
    sub = csv[csv['source_group'] == sg]
    print(f"\n  [{sg}] (n={len(sub)})")
    vc = sub['pub_type'].value_counts()
    for pt, n in vc.items():
        print(f"    {pt:20s}: {n:5d} ({100*n/len(sub):5.1f}%)")

# pubtype_classification.csv 出力
csv[['id', 'source', 'source_group', 'pub_type']].to_csv(
    os.path.join(OUTPUT, 'pubtype_classification.csv'), index=False)
print(f"\n  Saved: pubtype_classification.csv")

# ============================================================
# Part B: 層別ギャップ分析
# ============================================================

print("\n" + "=" * 60)
print("Part B: 層別ギャップ分析")
print("=" * 60)

qcol = 'quad_conservative'

# 全体値の整合性確認
for sg in ['kampo', 'pubmed']:
    sub = csv[csv['source_group'] == sg]
    has_abs = sub[sub['has_abstract'] == True]
    q1 = (has_abs[qcol] == 'Q1_both').sum()
    q3 = (has_abs[qcol] == 'Q3_formula_only').sum()
    gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else float('nan')
    print(f"  {sg} 全体: Q1={q1}, Q3={q3}, gap={gap:.1f}%")

# 層別テーブル
rows = []
pub_types_order = ['case_report', 'rct', 'clinical_trial', 'clinical_study',
                   'review_meta', 'review_discussion', 'basic_research', 'basic_other', 'other']

for sg in ['kampo', 'pubmed']:
    sub = csv[csv['source_group'] == sg]
    has_abs = sub[sub['has_abstract'] == True]
    for pt in pub_types_order:
        ptsub = has_abs[has_abs['pub_type'] == pt]
        if len(ptsub) == 0:
            continue
        n = len(ptsub)
        q1 = (ptsub[qcol] == 'Q1_both').sum()
        q3 = (ptsub[qcol] == 'Q3_formula_only').sum()
        gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else float('nan')
        rows.append({
            'source_group': sg,
            'pub_type': pt,
            'n_total': n,
            'Q1': q1,
            'Q3': q3,
            'Q1_plus_Q3': q1 + q3,
            'gap_pct': round(gap, 1) if not np.isnan(gap) else None,
        })

gap_df = pd.DataFrame(rows)
gap_df.to_csv(os.path.join(OUTPUT, 'pubtype_gap_table.csv'), index=False)

print("\n  === 層別ギャップテーブル ===")
print(f"  {'source':8s} {'pub_type':20s} {'n':>6s} {'Q1':>5s} {'Q3':>5s} {'gap%':>7s}")
print("  " + "-" * 55)
for _, r in gap_df.iterrows():
    g = f"{r['gap_pct']:.1f}" if r['gap_pct'] is not None else "N/A"
    print(f"  {r['source_group']:8s} {r['pub_type']:20s} {r['n_total']:6d} {r['Q1']:5d} {r['Q3']:5d} {g:>7s}")

# Fisher: 症例報告 vs 非症例報告 (kampo内)
print("\n  === 仮説検証: Fisher's exact test ===")
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True)]
    case = sub[sub['pub_type'] == 'case_report']
    noncase = sub[sub['pub_type'] != 'case_report']
    c_q1 = (case[qcol] == 'Q1_both').sum()
    c_q3 = (case[qcol] == 'Q3_formula_only').sum()
    n_q1 = (noncase[qcol] == 'Q1_both').sum()
    n_q3 = (noncase[qcol] == 'Q3_formula_only').sum()
    if c_q1 + c_q3 > 0 and n_q1 + n_q3 > 0:
        table = [[c_q1, c_q3], [n_q1, n_q3]]
        oddsratio, pval = fisher_exact(table)
        c_gap = c_q3 / (c_q1 + c_q3) * 100
        n_gap = n_q3 / (n_q1 + n_q3) * 100
        print(f"\n  [{sg}] 症例報告 vs 非症例報告:")
        print(f"    症例報告:   Q1={c_q1}, Q3={c_q3}, gap={c_gap:.1f}%")
        print(f"    非症例報告: Q1={n_q1}, Q3={n_q3}, gap={n_gap:.1f}%")
        print(f"    OR={oddsratio:.2f}  p={pval:.2e}")

# 症例報告の kampo vs pubmed
print("\n  === 症例報告の翻訳の断崖 ===")
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True) & (csv['pub_type'] == 'case_report')]
    q1 = (sub[qcol] == 'Q1_both').sum()
    q3 = (sub[qcol] == 'Q3_formula_only').sum()
    gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else float('nan')
    print(f"  {sg} 症例報告: Q1={q1}, Q3={q3}, gap={gap:.1f}%")

# ============================================================
# Part C: 可視化
# ============================================================

print("\n" + "=" * 60)
print("Part C: 可視化")
print("=" * 60)

plt.rcParams['font.family'] = ['MS Gothic', 'Yu Gothic', 'Meiryo', 'sans-serif']

# --- Fig 1: 論文タイプ別ギャップ ---
# 表示用ラベルとマッピング
display_map = {
    'case_report': '症例報告\nCase Reports',
    'rct': 'RCT',
    'clinical_trial': '臨床試験\nClinical Trial',
    'clinical_study': '臨床研究\nClinical Study',
    'review_meta': '総説/メタ\nReview/Meta',
    'review_discussion': '総説/考察',
    'basic_research': '基礎研究\nBasic Research',
    'basic_other': '基礎/その他\nBasic/Other',
    'other': 'その他\nOther',
}

# 表示する論文タイプを統合（kampo用とpubmed用で異なるカテゴリがあるため）
# kampoの clinical_study ↔ pubmedの clinical_trial を「臨床研究」に統合
# kampoの review_discussion ↔ pubmedの review_meta を「総説」に統合
# kampoの basic_research ↔ pubmedの basic_other を「基礎研究」に統合
def merge_pubtype(pt, sg):
    if pt in ('clinical_trial', 'clinical_study'):
        return 'clinical'
    if pt in ('review_meta', 'review_discussion'):
        return 'review'
    if pt in ('basic_research', 'basic_other'):
        return 'basic'
    if pt == 'rct':
        return 'rct'
    if pt == 'case_report':
        return 'case_report'
    return 'other'

csv['pub_type_merged'] = csv.apply(lambda r: merge_pubtype(r['pub_type'], r['source_group']), axis=1)

merged_order = ['case_report', 'rct', 'clinical', 'review', 'basic', 'other']
merged_labels = {
    'case_report': '症例報告\nCase Reports',
    'rct': 'RCT',
    'clinical': '臨床研究\nClinical',
    'review': '総説\nReview',
    'basic': '基礎/その他\nBasic/Other',
    'other': 'その他\nOther',
}

# ギャップ値を再計算（統合カテゴリで）
fig_data = {}
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True)]
    for pt in merged_order:
        ptsub = sub[sub['pub_type_merged'] == pt]
        q1 = (ptsub[qcol] == 'Q1_both').sum()
        q3 = (ptsub[qcol] == 'Q3_formula_only').sum()
        gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else None
        n = q1 + q3
        fig_data[(sg, pt)] = (gap, n)

# 全体値
overall = {}
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True)]
    q1 = (sub[qcol] == 'Q1_both').sum()
    q3 = (sub[qcol] == 'Q3_formula_only').sum()
    overall[sg] = q3 / (q1 + q3) * 100

fig, ax = plt.subplots(figsize=(10, 6))
y_pos = np.arange(len(merged_order))
bar_h = 0.35

kampo_vals = []
pubmed_vals = []
kampo_ns = []
pubmed_ns = []
for pt in merged_order:
    g_k, n_k = fig_data.get(('kampo', pt), (None, 0))
    g_p, n_p = fig_data.get(('pubmed', pt), (None, 0))
    kampo_vals.append(g_k if g_k is not None else 0)
    pubmed_vals.append(g_p if g_p is not None else 0)
    kampo_ns.append(n_k)
    pubmed_ns.append(n_p)

bars1 = ax.barh(y_pos - bar_h/2, kampo_vals, bar_h, label='東洋医学雑誌 (kampo)', color='#4472C4')
bars2 = ax.barh(y_pos + bar_h/2, pubmed_vals, bar_h, label='PubMed', color='#C00000')

# n数をバーの右に表示
for i, (v, n) in enumerate(zip(kampo_vals, kampo_ns)):
    if n > 0:
        ax.text(v + 1, i - bar_h/2, f'n={n}', va='center', fontsize=8, color='#4472C4')
for i, (v, n) in enumerate(zip(pubmed_vals, pubmed_ns)):
    if n > 0:
        ax.text(v + 1, i + bar_h/2, f'n={n}', va='center', fontsize=8, color='#C00000')

# 全体値の点線
ax.axvline(overall['kampo'], color='#4472C4', linestyle='--', alpha=0.5, linewidth=1)
ax.axvline(overall['pubmed'], color='#C00000', linestyle='--', alpha=0.5, linewidth=1)
ax.text(overall['kampo'] + 0.5, len(merged_order) - 0.3, f'kampo全体\n{overall["kampo"]:.1f}%',
        fontsize=7, color='#4472C4', va='top')
ax.text(overall['pubmed'] + 0.5, len(merged_order) - 0.8, f'PubMed全体\n{overall["pubmed"]:.1f}%',
        fontsize=7, color='#C00000', va='top')

ax.set_yticks(y_pos)
ax.set_yticklabels([merged_labels[pt] for pt in merged_order])
ax.set_xlabel('Cognitive Gap: Q3/(Q1+Q3) (%)')
ax.set_title('Publication Type × Cognitive Gap (Conservative v2)')
ax.legend(loc='lower right')
ax.set_xlim(0, 105)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'Fig_pubtype_1_gap_by_type.png'), dpi=300)
plt.close()
print("  Saved: Fig_pubtype_1_gap_by_type.png")

# --- Fig 2: 論文タイプ構成比 ---
fig, ax = plt.subplots(figsize=(8, 5))
colors = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5', '#70AD47']

for sg_idx, sg in enumerate(['kampo', 'pubmed']):
    sub = csv[csv['source_group'] == sg]
    counts = []
    for pt in merged_order:
        counts.append((sub['pub_type_merged'] == pt).sum())
    total = sum(counts)
    pcts = [c / total * 100 for c in counts]
    bottom = 0
    for i, (pct, pt) in enumerate(zip(pcts, merged_order)):
        bar = ax.bar(sg_idx, pct, bottom=bottom, color=colors[i],
                     label=merged_labels[pt] if sg_idx == 0 else None)
        if pct > 3:
            ax.text(sg_idx, bottom + pct/2, f'{pct:.0f}%', ha='center', va='center', fontsize=9)
        bottom += pct

ax.set_xticks([0, 1])
ax.set_xticklabels(['東洋医学雑誌\n(kampo)', 'PubMed'])
ax.set_ylabel('構成比 (%)')
ax.set_title('Publication Type Composition: Kampo vs PubMed')
ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'Fig_pubtype_2_composition.png'), dpi=300)
plt.close()
print("  Saved: Fig_pubtype_2_composition.png")

# ============================================================
# Part D: レポート出力
# ============================================================

print("\n" + "=" * 60)
print("Part D: レポート出力")
print("=" * 60)

# 構成比テーブル（レポート用）
comp_lines = []
for sg in ['kampo', 'pubmed']:
    sub = csv[csv['source_group'] == sg]
    total = len(sub)
    for pt in merged_order:
        n = (sub['pub_type_merged'] == pt).sum()
        comp_lines.append(f"| {sg:8s} | {merged_labels[pt].replace(chr(10), ' '):30s} | {n:5d} | {100*n/total:5.1f}% |")

# 層別ギャップテーブル（レポート用、統合カテゴリ）
gap_lines = []
for sg in ['kampo', 'pubmed']:
    for pt in merged_order:
        g, n = fig_data.get((sg, pt), (None, 0))
        sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True) & (csv['pub_type_merged'] == pt)]
        q1 = (sub[qcol] == 'Q1_both').sum()
        q3 = (sub[qcol] == 'Q3_formula_only').sum()
        g_str = f"{g:.1f}%" if g is not None else "N/A"
        gap_lines.append(f"| {sg:8s} | {merged_labels[pt].replace(chr(10), ' '):30s} | {len(sub):5d} | {q1:4d} | {q3:4d} | {g_str:>7s} |")

report = f"""# 論文タイプ別 認知ギャップ層別分析 (Phase 3b)

> 生成日: 2026-03-30
> データ: integrated_db_japan.json (10,535件) + Conservative v2辞書

---

## 1. 論文タイプ分類

### 分類方法
- **PubMed論文**: `pub_types` フィールド（Case Reports, RCT, Clinical Trial, Review, Meta-Analysis等）
- **東洋医学雑誌**: タイトルの正規表現マッチ（一例/症例/奏効 → 症例報告、臨床研究/調査 → 臨床研究 等）

### 構成比

| source   | 論文タイプ                       |     n |   比率 |
|----------|--------------------------------|------:|-------:|
{chr(10).join(comp_lines)}

---

## 2. 層別認知ギャップ

| source   | 論文タイプ                       |     n |  Q1  |  Q3  |    gap  |
|----------|--------------------------------|------:|-----:|-----:|--------:|
{chr(10).join(gap_lines)}

**全体値（参考）**: kampo = {overall['kampo']:.1f}%, PubMed = {overall['pubmed']:.1f}%

---

## 3. 仮説検証

### 3-1. 症例報告は思考の記述率が高いか？
"""

# 仮説3-1の数値
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True)]
    case = sub[sub['pub_type_merged'] == 'case_report']
    noncase = sub[sub['pub_type_merged'] != 'case_report']
    c_q1 = (case[qcol] == 'Q1_both').sum()
    c_q3 = (case[qcol] == 'Q3_formula_only').sum()
    n_q1 = (noncase[qcol] == 'Q1_both').sum()
    n_q3 = (noncase[qcol] == 'Q3_formula_only').sum()
    if c_q1 + c_q3 > 0 and n_q1 + n_q3 > 0:
        c_gap = c_q3 / (c_q1 + c_q3) * 100
        n_gap = n_q3 / (n_q1 + n_q3) * 100
        table_arr = [[c_q1, c_q3], [n_q1, n_q3]]
        oddsratio, pval = fisher_exact(table_arr)
        report += f"""
**{sg}**:
- 症例報告: gap = {c_gap:.1f}% (Q1={c_q1}, Q3={c_q3})
- 非症例報告: gap = {n_gap:.1f}% (Q1={n_q1}, Q3={n_q3})
- OR = {oddsratio:.2f}, p = {pval:.2e}
"""

report += """
### 3-2. 翻訳の断崖は症例報告でも存在するか？
"""

# 症例報告のkampo vs pubmed
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True) & (csv['pub_type_merged'] == 'case_report')]
    q1 = (sub[qcol] == 'Q1_both').sum()
    q3 = (sub[qcol] == 'Q3_formula_only').sum()
    gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else float('nan')
    report += f"- {sg} 症例報告: gap = {gap:.1f}% (Q1={q1}, Q3={q3})\n"

# 症例報告のOR
case_k = csv[(csv['source_group'] == 'kampo') & (csv['has_abstract'] == True) & (csv['pub_type_merged'] == 'case_report')]
case_p = csv[(csv['source_group'] == 'pubmed') & (csv['has_abstract'] == True) & (csv['pub_type_merged'] == 'case_report')]
k_q1 = (case_k[qcol] == 'Q1_both').sum()
k_q3 = (case_k[qcol] == 'Q3_formula_only').sum()
p_q1 = (case_p[qcol] == 'Q1_both').sum()
p_q3 = (case_p[qcol] == 'Q3_formula_only').sum()
if k_q1 + k_q3 > 0 and p_q1 + p_q3 > 0:
    t = [[k_q1, k_q3], [p_q1, p_q3]]
    or_val, p_val = fisher_exact(t)
    report += f"\n**症例報告のみで比較した翻訳の断崖**: OR = {or_val:.2f}, p = {p_val:.2e}\n"

report += """
### 3-3. 基礎研究の認知ギャップ
"""
for sg in ['kampo', 'pubmed']:
    sub = csv[(csv['source_group'] == sg) & (csv['has_abstract'] == True) & (csv['pub_type_merged'] == 'basic')]
    q1 = (sub[qcol] == 'Q1_both').sum()
    q3 = (sub[qcol] == 'Q3_formula_only').sum()
    gap = q3 / (q1 + q3) * 100 if (q1 + q3) > 0 else float('nan')
    report += f"- {sg} 基礎研究: gap = {gap:.1f}% (Q1={q1}, Q3={q3})\n"

report += """
---

## 4. 解釈

（分析者が結果を見て記入）

---

*生成スクリプト: pubtype_analysis.py*
"""

with open(os.path.join(OUTPUT, 'pubtype_analysis_report.md'), 'w', encoding='utf-8') as f:
    f.write(report)
print("  Saved: pubtype_analysis_report.md")

# 出力ファイル一覧
print("\n=== 出力ファイル ===")
for fn in sorted(os.listdir(OUTPUT)):
    fp = os.path.join(OUTPUT, fn)
    sz = os.path.getsize(fp)
    print(f"  {fn} ({sz // 1024} KB)")
