#!/usr/bin/env python3
"""
cognitive_gap_phase2.py
認知ギャップ Phase 2: 辞書クリーニング / 感度分析 / kampo×pubmed 深掘り
"""

import os, sys, re, json, importlib.util, warnings
from collections import Counter, defaultdict
from math import log, exp
warnings.filterwarnings('ignore')

# ─── Paths ─────────────────────────────────────────────────────
BASE_DIR   = r'C:\Users\kosei\Desktop\18_東洋医学雑誌'
DATA_DIR   = os.path.join(BASE_DIR, 'data')
PHASE1_DIR = os.path.join(BASE_DIR, 'analysis_output')
OUTPUT_DIR = os.path.join(BASE_DIR, 'analysis_output', 'phase2')
DICT_PY    = os.path.join(BASE_DIR, 'dictionaries.py')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Packages ──────────────────────────────────────────────────
import subprocess
for pkg in ['pandas', 'matplotlib', 'seaborn', 'scipy', 'statsmodels', 'tqdm', 'numpy']:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from tqdm import tqdm

# Japanese font
import matplotlib.font_manager as fm
for _jp in ['MS Gothic', 'Meiryo', 'Yu Gothic', 'IPAexGothic', 'Noto Sans CJK JP']:
    if _jp in [f.name for f in fm.fontManager.ttflist]:
        plt.rcParams['font.family'] = _jp
        break

plt.rcParams.update({
    'axes.unicode_minus': False,
    'font.size': 9,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# Colorblind-safe
CB = {'blue': '#2166ac', 'red': '#b2182b', 'green': '#1b7837',
      'gray': '#969696', 'lblue': '#74add1', 'lred': '#f4a582',
      'orange': '#d6604d', 'purple': '#762a83'}

QUAD_ORDER  = ['Q1_both', 'Q2_cognition_only', 'Q3_formula_only', 'Q4_neither']
QUAD_LABELS = ['Q1: Formula+Cognition', 'Q2: Cognition only',
               'Q3: Formula only (gap)', 'Q4: Neither']
QUAD_COLORS = [CB['blue'], CB['green'], CB['red'], CB['gray']]
CAT_ORDER   = ['sho_core', 'pathology', 'classical', 'examination', 'epistemological']

def save(fig, name, dpi=300):
    fig.savefig(os.path.join(OUTPUT_DIR, name), dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {name}")

def get_terms(val):
    if pd.isna(val) or not val:
        return []
    return [t for t in str(val).split('|') if t.strip()]

# ─────────────────────────────────────────────────────────────
# Load Phase 1 CSV + rebuild cognition dict
# ─────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading Phase 1 data")
print("=" * 60)

df = pd.read_csv(os.path.join(PHASE1_DIR, 'papers_classified.csv'),
                 encoding='utf-8-sig', low_memory=False)
df['year_bin'] = pd.to_numeric(df['year_bin'], errors='coerce')
print(f"  {len(df):,} rows, columns: {list(df.columns)}")

# Rebuild ALL_TERMS (term -> category) from dictionaries.py
spec = importlib.util.spec_from_file_location("dicts", DICT_PY)
dmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmod)

PTERM_CAT = {'八綱弁証': 'pathology', '気血津液弁証': 'pathology',
             '臓腑弁証': 'pathology',  '六経弁証': 'classical'}

ALL_TERMS = {}
for top_cat, sub in dmod.PATTERN_TERMS.items():
    cat = PTERM_CAT.get(top_cat, 'pathology')
    for subcat, tlist in sub.items():
        if isinstance(tlist, list):
            for t in tlist:
                ALL_TERMS[t] = cat

for t in dmod.ABDOMINAL_TERMS:
    ALL_TERMS[t] = 'examination'

for t, c in {
    '随証': 'sho_core', '弁証': 'sho_core', '方証相対': 'sho_core',
    '証に基づ': 'sho_core', '証の変化': 'sho_core', '証を決定': 'sho_core',
    '気血水': 'pathology', 'お血': 'pathology', '血瘀': 'pathology',
    '冷え症': 'pathology', '冷え性': 'pathology', '冷え': 'pathology',
    'のぼせ': 'pathology', '気鬱': 'pathology', '気うつ': 'pathology',
    '未病': 'epistemological', '養生': 'epistemological',
    '心身一如': 'epistemological', '同病異治': 'epistemological',
    '異病同治': 'epistemological', '君臣佐使': 'epistemological',
    '傷寒論': 'classical', '金匱要略': 'classical', '温病': 'classical',
}.items():
    if t not in ALL_TERMS:
        ALL_TERMS[t] = c

for t, c in {
    'sho ': 'sho_core', 'sho-based': 'sho_core', 'sho pattern': 'sho_core',
    'pattern diagnosis': 'sho_core', 'pattern identification': 'sho_core',
    'pattern differentiation': 'sho_core', 'ho-sho-sotai': 'sho_core',
    'qi deficiency': 'pathology', 'blood deficiency': 'pathology',
    'qi stagnation': 'pathology', 'blood stasis': 'pathology',
    'blood stagnation': 'pathology', 'oketsu': 'pathology',
    'water toxin': 'pathology', 'yin deficiency': 'pathology',
    'yang deficiency': 'pathology', 'yin-yang': 'pathology',
    'cold sensitivity': 'pathology', 'hie ': 'pathology',
    'deficiency pattern': 'pathology', 'excess pattern': 'pathology',
    'kyo-jitsu': 'pathology', 'spleen deficiency': 'pathology',
    'kidney deficiency': 'pathology', 'liver qi': 'pathology',
    'taiyang': 'classical', 'shaoyang': 'classical', 'yangming': 'classical',
    'taiyin': 'classical', 'shaoyin': 'classical', 'jueyin': 'classical',
    'six stages': 'classical', 'shanghan': 'classical', 'shang han': 'classical',
    'jingui': 'classical',
    'fukushin': 'examination', 'pulse diagnosis': 'examination',
    'tongue diagnosis': 'examination', 'hypochondriac fullness': 'examination',
    'abdominal diagnosis': 'examination', 'abdominal palpation': 'examination',
    'mibyou': 'epistemological', 'mibyo': 'epistemological',
    'mind-body unity': 'epistemological',
    'same disease different treatment': 'epistemological',
}.items():
    if t not in ALL_TERMS:
        ALL_TERMS[t] = c

# ─────────────────────────────────────────────────────────────
# Part 1: 3-level dictionary + sensitivity analysis
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Part 1: Sensitivity Analysis")
print("=" * 60)

# False positives to remove
FP_HARD = {'出血', '発熱', '浮腫', '動悸'}

def filter_liberal(terms):
    return [(t, ALL_TERMS[t]) for t in terms if t in ALL_TERMS]

def filter_conservative(terms):
    result = []
    for t in terms:
        if t not in ALL_TERMS: continue
        if t in FP_HARD:       continue
        if t == '冷え':        continue  # 複合語の冷え症/冷え性は残す
        result.append((t, ALL_TERMS[t]))
    return result

STRICT_REMOVE = FP_HARD | {'冷え', '冷え症', '冷え性', 'のぼせ', '陰虚', '陽虚',
                            '悪寒', '潮熱', '微熱', 'yin-yang',
                            'yin deficiency', 'yang deficiency'}

def filter_strict(terms):
    return [(t, ALL_TERMS[t]) for t in terms
            if t in ALL_TERMS and t not in STRICT_REMOVE]

FILTERS = [('liberal', filter_liberal),
           ('conservative', filter_conservative),
           ('strict', filter_strict)]

# Apply to entire df (using matched_cognition from Phase 1 CSV)
def apply_filter(df_in, ffn, name):
    cog_hits, quads, cats_list = [], [], []
    for _, row in df_in.iterrows():
        terms  = get_terms(row.get('matched_cognition', ''))
        fil    = ffn(terms)
        c_hit  = len(fil) > 0
        f_hit  = bool(row.get('formula_in_text', False))
        if   f_hit and     c_hit: quad = 'Q1_both'
        elif not f_hit and c_hit: quad = 'Q2_cognition_only'
        elif f_hit and not c_hit: quad = 'Q3_formula_only'
        else:                     quad = 'Q4_neither'
        cog_hits.append(c_hit)
        quads.append(quad)
        cats_list.append('|'.join(sorted(set(c for _, c in fil))))
    df_in = df_in.copy()
    df_in[f'cog_{name}']  = cog_hits
    df_in[f'quad_{name}'] = quads
    df_in[f'cats_{name}'] = cats_list
    return df_in

print("  Applying 3 filters to all articles...")
for name, ffn in FILTERS:
    df = apply_filter(df, ffn, name)
    q1 = (df[f'quad_{name}'] == 'Q1_both').sum()
    q3 = (df[f'quad_{name}'] == 'Q3_formula_only').sum()
    gap = q3 / (q1 + q3) if (q1 + q3) > 0 else float('nan')
    print(f"  [{name:12s}] cog={df[f'cog_{name}'].mean():.1%}  Q3/(Q1+Q3)={gap:.1%}")

# Source-level sensitivity table
sens_rows = []
for src in df['source'].dropna().unique():
    sub = df[df['source'] == src]
    row = {'source': src, 'n': len(sub)}
    for name, _ in FILTERS:
        q1 = (sub[f'quad_{name}'] == 'Q1_both').sum()
        q3 = (sub[f'quad_{name}'] == 'Q3_formula_only').sum()
        gap = q3 / (q1 + q3) if (q1 + q3) > 0 else float('nan')
        row[f'gap_{name}']  = round(gap, 4)
        row[f'cog_{name}']  = round(sub[f'cog_{name}'].mean(), 4)
        row[f'q1_{name}']   = q1
        row[f'q3_{name}']   = q3
    sens_rows.append(row)

sens_df = pd.DataFrame(sens_rows)
sens_df.to_csv(os.path.join(OUTPUT_DIR, 'sensitivity_analysis.csv'),
               index=False, encoding='utf-8-sig')
print("\n  Source-level sensitivity:")
for row in sens_rows:
    src = row['source']
    for name, _ in FILTERS:
        print(f"    {src:25s} [{name:12s}] "
              f"cog={row[f'cog_{name}']:.1%} gap={row.get(f'gap_{name}', float('nan')):.1%}")

# ── Fig P2-1: Sensitivity heatmap ──────────────────────────────
# Rows = source, Cols = dict version
# Two panels: Q3/(Q1+Q3) and cognition rate
gap_mat = pd.DataFrame(
    {n: [r[f'gap_{n}'] for r in sens_rows] for n, _ in FILTERS},
    index=[r['source'] for r in sens_rows]
) * 100  # percent

cog_mat = pd.DataFrame(
    {n: [r[f'cog_{n}'] for r in sens_rows] for n, _ in FILTERS},
    index=[r['source'] for r in sens_rows]
) * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.5))
sns.heatmap(gap_mat, annot=True, fmt='.1f', cmap='RdYlBu_r', vmin=0, vmax=100,
            ax=ax1, cbar_kws={'label': 'Q3/(Q1+Q3) %'}, linewidths=0.4)
ax1.set_title('Q3/(Q1+Q3) [%] by Dict Version', fontweight='bold', fontsize=9)
ax1.set_xlabel('Dictionary'); ax1.set_ylabel('Source')

sns.heatmap(cog_mat, annot=True, fmt='.1f', cmap='Blues', vmin=0,
            ax=ax2, cbar_kws={'label': 'Cognition rate %'}, linewidths=0.4)
ax2.set_title('Cognition Mention Rate [%]', fontweight='bold', fontsize=9)
ax2.set_xlabel('Dictionary'); ax2.set_ylabel('')

fig.suptitle('Fig P2-1: Sensitivity Analysis - 3 Dictionary Versions',
             fontweight='bold', fontsize=10)
plt.tight_layout()
save(fig, 'Fig_P2_1_sensitivity_table.png')

# ── Fig P2-2: Sensitivity band timeseries (all sources) ────────
MIN_N = 15
fig, ax = plt.subplots(figsize=(11, 5))

has_abs = df[df['has_abstract'] == True].copy()
g_f = has_abs.groupby('year_bin')['formula_in_text'].mean()
g_f = g_f[has_abs.groupby('year_bin')['formula_in_text'].count() >= MIN_N]
x_all = g_f.index.astype(int)
ax.plot(x_all, g_f.values * 100, color=CB['red'], lw=2.5, marker='o', ms=4,
        label='Formula mention rate', zorder=5)

# Conservative: main line + fill
g_c = has_abs.groupby('year_bin')['cog_conservative'].mean().reindex(g_f.index)
ax.plot(x_all, g_c.values * 100, color=CB['blue'], lw=2.5, marker='s', ms=4,
        label='Cognition rate [Conservative]', zorder=5)
ax.fill_between(x_all, g_c.values * 100, g_f.values * 100,
                where=g_f.values >= g_c.values, alpha=0.18, color=CB['blue'])

# Liberal / Strict: thin bands
for name, color, ls in [('liberal', CB['lblue'], '--'), ('strict', CB['lblue'], ':')]:
    g_x = has_abs.groupby('year_bin')[f'cog_{name}'].mean().reindex(g_f.index)
    ax.plot(x_all, g_x.values * 100, color=color, lw=1.2, linestyle=ls, alpha=0.7,
            label=f'Cognition rate [{name}]')

ax.set_ylim(-2, 100)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_xlabel('Year (5-year bins)', fontsize=10)
ax.set_ylabel('Mention rate (%)', fontsize=10)
ax.set_title('Fig P2-2: Cognitive Gap with Sensitivity Bands\n'
             '(Conservative = solid; Liberal/Strict = dashed sensitivity range)',
             fontweight='bold')
ax.legend(fontsize=8, ncol=2)
ax.grid(axis='y', alpha=0.25, lw=0.8)
save(fig, 'Fig_P2_2_sensitivity_gap.png')

# ─────────────────────────────────────────────────────────────
# Part 2: kampo × pubmed_kampo deep dive (Conservative dict)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Part 2: Deep dive - kampo vs pubmed_kampo  [Conservative dict]")
print("=" * 60)

DV = 'conservative'

k_df  = df[df['source'] == 'kampo'].copy()
pm_df = df[df['source'] == 'pubmed_kampo'].copy()
print(f"  kampo:        {len(k_df):,}  (abs={k_df['has_abstract'].mean():.1%})")
print(f"  pubmed_kampo: {len(pm_df):,}  (abs={pm_df['has_abstract'].mean():.1%})")

# ── 2-1 Basic comparison ────────────────────────────────────────
def src_stats(sub):
    ha = sub[sub['has_abstract'] == True]
    q1 = (ha[f'quad_{DV}'] == 'Q1_both').sum()
    q3 = (ha[f'quad_{DV}'] == 'Q3_formula_only').sum()
    gap = q3 / (q1 + q3) if (q1 + q3) > 0 else float('nan')
    all_f = [t for v in ha['matched_formulas'] for t in get_terms(v)]
    all_c = [t for v in ha['matched_cognition']
             for t, _ in filter_conservative(get_terms(v))]
    return {
        'n': len(sub), 'n_abs': len(ha), 'abs_rate': len(ha)/len(sub),
        'f_rate': ha['formula_in_text'].mean(),
        'c_rate': ha[f'cog_{DV}'].mean(),
        'gap': gap,
        'Q1': q1, 'Q2': (ha[f'quad_{DV}'] == 'Q2_cognition_only').sum(),
        'Q3': q3, 'Q4': (ha[f'quad_{DV}'] == 'Q4_neither').sum(),
        'top5f': [f for f, _ in Counter(all_f).most_common(5)],
        'top5c': [t for t, _ in Counter(all_c).most_common(5)],
    }

ks  = src_stats(k_df)
pms = src_stats(pm_df)

comp = pd.DataFrame({
    'Metric': ['n_total', 'n_with_abstract', 'abstract_rate',
               'formula_rate', 'cognition_rate', 'Q3/(Q1+Q3)',
               'Q1', 'Q2', 'Q3', 'Q4', 'top5_formulas', 'top5_cognition'],
    'kampo': [ks['n'], ks['n_abs'], f"{ks['abs_rate']:.1%}",
              f"{ks['f_rate']:.1%}", f"{ks['c_rate']:.1%}", f"{ks['gap']:.1%}",
              ks['Q1'], ks['Q2'], ks['Q3'], ks['Q4'],
              ' / '.join(ks['top5f']), ' / '.join(ks['top5c'])],
    'pubmed_kampo': [pms['n'], pms['n_abs'], f"{pms['abs_rate']:.1%}",
                     f"{pms['f_rate']:.1%}", f"{pms['c_rate']:.1%}", f"{pms['gap']:.1%}",
                     pms['Q1'], pms['Q2'], pms['Q3'], pms['Q4'],
                     ' / '.join(pms['top5f']), ' / '.join(pms['top5c'])],
})
comp.to_csv(os.path.join(OUTPUT_DIR, 'kampo_vs_pubmed_comparison.csv'),
            index=False, encoding='utf-8-sig')
print(f"  kampo   gap={ks['gap']:.1%}  cog={ks['c_rate']:.1%}")
print(f"  pubmed  gap={pms['gap']:.1%}  cog={pms['c_rate']:.1%}")

# ── Fig P2-3: Gap comparison (* main figure candidate) ─────────
def plot_gap_panel(sub, ax, title, min_n=8):
    ha = sub[sub['has_abstract'] == True].copy()
    g = ha.groupby('year_bin').agg(
        n=('formula_in_text', 'count'),
        pf=('formula_in_text', 'mean'),
        pc=(f'cog_{DV}', 'mean'),
    ).reset_index()
    g = g[g['n'] >= min_n].dropna()
    if g.empty:
        ax.text(0.5, 0.5, 'n < threshold', transform=ax.transAxes,
                ha='center', va='center', color='gray')
        ax.set_title(title); return
    x = g['year_bin'].astype(int)
    ax.plot(x, g['pf'] * 100, color=CB['red'],  lw=2.5, marker='o', ms=5,
            label='Formula mention rate', zorder=4)
    ax.plot(x, g['pc'] * 100, color=CB['blue'], lw=2.5, marker='s', ms=5,
            label='Cognition mention rate', zorder=4)
    ax.fill_between(x, g['pc']*100, g['pf']*100,
                    where=g['pf'] >= g['pc'],
                    alpha=0.18, color=CB['blue'], label='Cognitive gap')
    # annotate Q ratio
    q1 = (ha[f'quad_{DV}'] == 'Q1_both').sum()
    q3 = (ha[f'quad_{DV}'] == 'Q3_formula_only').sum()
    gap_r = q3 / (q1 + q3) if (q1 + q3) > 0 else float('nan')
    ax.text(0.97, 0.96, f'Q3/(Q1+Q3)={gap_r:.1%}',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=CB['gray'], alpha=0.9))
    ax.set_ylim(-2, 105)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_xlabel('Year (5-year bins)', fontsize=10)
    ax.set_ylabel('Mention rate (%)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.grid(axis='y', alpha=0.25, lw=0.8)
    ax.legend(fontsize=9, loc='upper left')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
plot_gap_panel(k_df,  ax1, 'Journal of Kampo Medicine\n(Japanese, n=2,003)')
plot_gap_panel(pm_df, ax2, 'PubMed Kampo Articles\n(English, n=5,544)')
fig.suptitle('Fig P2-3: The Cognitive Gap - Japanese vs. English Kampo Literature\n'
             '(Conservative dictionary; articles with abstract)',
             fontsize=11, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, 'Fig_P2_3_gap_comparison.png')

# ── Fig P2-4: Quadrant stacked area comparison ─────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
for ax, sub, title in [(ax1, k_df, 'Kampo Journal (JP)'),
                        (ax2, pm_df, 'PubMed Kampo (EN)')]:
    qt = (sub.groupby('year_bin')[f'quad_{DV}']
              .value_counts(normalize=True)
              .unstack(fill_value=0)
              .reindex(columns=QUAD_ORDER, fill_value=0))
    qt.index = qt.index.astype(int)
    qt.columns = QUAD_LABELS
    qt.plot(kind='area', stacked=True, ax=ax, color=QUAD_COLORS, alpha=0.82)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_ylim(0, 1)
    ax.set_ylabel('Proportion', fontsize=9)
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.legend(fontsize=8, loc='lower left')
    ax.grid(axis='y', alpha=0.25)
ax2.set_xlabel('Year (5-year bins)', fontsize=10)
fig.suptitle('Fig P2-4: 4-Quadrant Composition - kampo vs pubmed_kampo',
             fontsize=11, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_P2_4_quadrant_comparison.png')

# ── Fig P2-5: Cognition category comparison ────────────────────
def cat_rates(sub):
    ha = sub[sub['has_abstract'] == True]
    return {cat: ha[f'cats_{DV}'].apply(
                lambda x: cat in get_terms(x)).mean() * 100
            for cat in CAT_ORDER}

kc  = cat_rates(k_df)
pmc = cat_rates(pm_df)

fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(CAT_ORDER)); w = 0.38
b1 = ax.bar(x-w/2, [kc[c]  for c in CAT_ORDER], w, color=CB['blue'],
            alpha=0.85, label='Kampo Journal (JP)')
b2 = ax.bar(x+w/2, [pmc[c] for c in CAT_ORDER], w, color=CB['red'],
            alpha=0.85, label='PubMed Kampo (EN)')
ax.bar_label(b1, fmt='%.1f%%', fontsize=7, padding=2)
ax.bar_label(b2, fmt='%.1f%%', fontsize=7, padding=2)
ax.set_xticks(x); ax.set_xticklabels(CAT_ORDER, fontsize=9)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_ylabel('Articles mentioning category (%)', fontsize=9)
ax.set_title('Fig P2-5: Cognition Category Distribution\n'
             'Kampo Journal vs PubMed Kampo (Conservative dict)',
             fontweight='bold')
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.25)
ax.set_ylim(0, max(max(kc.values()), max(pmc.values())) * 1.35)
save(fig, 'Fig_P2_5_cognition_category_comparison.png')

# ── 2-5: Formula × Cognition co-occurrence ──────────────────────
print("  Co-occurrence matrix...")
all_f_combined = []
for sub in [k_df, pm_df]:
    for v in sub['matched_formulas']:
        all_f_combined.extend(get_terms(v))
top15_formulas = [f for f, _ in Counter(all_f_combined).most_common(15)]

def coocmat(sub, formulas):
    mat = np.zeros((len(formulas), len(CAT_ORDER)), dtype=int)
    for _, row in sub.iterrows():
        rf = set(get_terms(row.get('matched_formulas', '')))
        rc = set(get_terms(row.get(f'cats_{DV}', '')))
        for i, f in enumerate(formulas):
            if f in rf:
                for j, c in enumerate(CAT_ORDER):
                    if c in rc:
                        mat[i, j] += 1
    return mat

k_mat  = coocmat(k_df,  top15_formulas)
pm_mat = coocmat(pm_df, top15_formulas)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
for ax, mat, title, cmap in [(ax1, k_mat, 'Kampo Journal (JP)', 'Blues'),
                              (ax2, pm_mat, 'PubMed Kampo (EN)', 'Reds')]:
    sns.heatmap(mat, annot=True, fmt='d', cmap=cmap,
                xticklabels=CAT_ORDER, yticklabels=top15_formulas,
                ax=ax, cbar_kws={'label': 'Co-occurrence count'},
                linewidths=0.3, vmin=0)
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.set_xlabel('Cognition Category', fontsize=9)
    ax.set_ylabel('Formula', fontsize=9)
    ax.tick_params(axis='x', rotation=30)
    ax.tick_params(axis='y', rotation=0, labelsize=8)
fig.suptitle('Fig P2-6: Formula x Cognition Category Co-occurrence',
             fontsize=11, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_P2_6_formula_cognition_heatmap.png')

# ── 2-6: Translation cliff ──────────────────────────────────────
print("  Translation cliff...")

# Mapping kanji -> romaji for PubMed formula matching
FORMULA_MAP = {
    '抑肝散':    ['yokukansan'],
    '五苓散':    ['goreisan'],
    '牛車腎気丸':['goshajinkigan'],
    '大建中湯':  ['daikenchuto'],
    '補中益気湯':['hochuekkito'],
    '桂枝茯苓丸':['keishibukuryogan', 'keishi-bukuryo-gan'],
    '十全大補湯':['juzentaihoto'],
    '人参養栄湯':['ninjinyoeito'],
    '小柴胡湯':  ['shosaikoto'],
    '六君子湯':  ['rikkunshito'],
    '八味地黄丸':['hachimijiogan'],
    '当帰芍薬散':['tokishakuyakusan'],
    '防風通聖散':['bofutsushosan'],
    '半夏瀉心湯':['hangeshashinto'],
    '加味逍遥散':['kamishoyosan'],
}

cliff_rows = []
for jp_name, romaji_list in FORMULA_MAP.items():
    for sub, src in [(k_df, 'kampo'), (pm_df, 'pubmed_kampo')]:
        if src == 'kampo':
            match_terms = {jp_name}
        else:
            match_terms = set(romaji_list)
        has_f = sub[sub['matched_formulas'].apply(
            lambda x: bool(match_terms & set(get_terms(x))))]
        if len(has_f) == 0:
            cliff_rows.append({'formula': jp_name, 'source': src,
                               'n': 0, 'n_cog': 0, 'cog_rate': float('nan')})
            continue
        n_cog = has_f[f'cog_{DV}'].sum()
        cliff_rows.append({'formula': jp_name, 'source': src,
                           'n': len(has_f), 'n_cog': int(n_cog),
                           'cog_rate': n_cog / len(has_f)})

cliff_df = pd.DataFrame(cliff_rows)
cliff_df.to_csv(os.path.join(OUTPUT_DIR, 'translation_cliff.csv'),
                index=False, encoding='utf-8-sig')

# Filter to formulas with n >= 5 in kampo
k_n = cliff_df[(cliff_df['source'] == 'kampo') & (cliff_df['n'] >= 5)]['formula'].tolist()
cliff_plot = cliff_df[cliff_df['formula'].isin(k_n)].pivot(
    index='formula', columns='source', values='cog_rate').fillna(0)

fig, ax = plt.subplots(figsize=(11, 5))
x = np.arange(len(cliff_plot))
w = 0.38
k_vals  = cliff_plot.get('kampo', pd.Series([0]*len(cliff_plot))).values * 100
pm_vals = cliff_plot.get('pubmed_kampo', pd.Series([0]*len(cliff_plot))).values * 100

b1 = ax.bar(x-w/2, k_vals,  w, color=CB['blue'], alpha=0.87, label='Kampo Journal (JP)')
b2 = ax.bar(x+w/2, pm_vals, w, color=CB['red'],  alpha=0.87, label='PubMed Kampo (EN)')

# Annotate cliff size (diff > 5pp)
for xi, kv, pv in zip(x, k_vals, pm_vals):
    diff = kv - pv
    if diff > 5:
        ax.annotate('', xy=(xi+w/2, max(pv+0.5, 1)),
                    xytext=(xi-w/2, kv),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.3))
        ax.text(xi, max(kv, pv) + 3, f'-{diff:.0f}pp',
                ha='center', fontsize=7, color='black')

ax.set_xticks(x)
ax.set_xticklabels(cliff_plot.index, rotation=40, ha='right', fontsize=8)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_ylabel('Cognition co-mention rate\namong formula-citing articles (%)', fontsize=9)
ax.set_title(
    'Fig P2-7: The Translation Cliff\n'
    '% of formula-citing articles that also mention cognition terms [Conservative dict]',
    fontweight='bold')
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.25)
ax.set_ylim(0, max(k_vals.max(), pm_vals.max()) * 1.30)
save(fig, 'Fig_P2_7_translation_cliff.png')

# ── 2-7: Temporal heatmap ───────────────────────────────────────
print("  Temporal heatmap...")
all_cog_cb = []
for sub in [k_df, pm_df]:
    for v in sub['matched_cognition']:
        all_cog_cb.extend(t for t, _ in filter_conservative(get_terms(v)))
top15_cog = [t for t, _ in Counter(all_cog_cb).most_common(15)]

def temporal_heat(sub, terms, min_n=5):
    rows = []
    for yb, grp in sub.groupby('year_bin'):
        if pd.isna(yb) or len(grp) < min_n: continue
        row = {'year': int(yb)}
        for t in terms:
            row[t] = grp['matched_cognition'].apply(
                lambda x: t in get_terms(x)).mean() * 100
        rows.append(row)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).set_index('year')[terms]

k_th  = temporal_heat(k_df,  top15_cog)
pm_th = temporal_heat(pm_df, top15_cog)
vmax  = max(k_th.max().max() if not k_th.empty else 0,
            pm_th.max().max() if not pm_th.empty else 0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
for ax, mat, title, cmap in [(ax1, k_th, 'Kampo Journal (JP)', 'Blues'),
                              (ax2, pm_th, 'PubMed Kampo (EN)', 'Reds')]:
    if mat.empty:
        ax.text(0.5, 0.5, 'Insufficient data', transform=ax.transAxes,
                ha='center', va='center', color='gray')
        ax.set_title(title); continue
    sns.heatmap(mat.T, annot=True, fmt='.1f', cmap=cmap,
                vmin=0, vmax=vmax, ax=ax,
                cbar_kws={'label': 'Mention rate (%)'},
                linewidths=0.2)
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.set_xlabel('Year (5-year bins)', fontsize=9)
    ax.set_ylabel('Cognition term', fontsize=9)
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='y', rotation=0, labelsize=8)
fig.suptitle('Fig P2-8: Temporal Distribution of Cognition Terms',
             fontsize=11, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_P2_8_temporal_heatmap.png')

# ─────────────────────────────────────────────────────────────
# Part 3: Statistical tests
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Part 3: Statistical Tests")
print("=" * 60)

stat_lines = [
    "# Statistical Tests - Cognitive Gap Phase 2\n",
    f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n",
    f"Dictionary: Conservative\n\n",
]

# 3-1: Chi-square / Fisher for Q3/(Q1+Q3)
k_q1, k_q3   = ks['Q1'], ks['Q3']
pm_q1, pm_q3 = pms['Q1'], pms['Q3']
cont = np.array([[k_q1, k_q3], [pm_q1, pm_q3]])
chi2, p_chi2, dof, _ = stats.chi2_contingency(cont)
or_fisher, p_fisher   = stats.fisher_exact(cont)

def or_ci(a, b, c, d, alpha=0.05):
    if 0 in (a, b, c, d):
        return float('nan'), float('nan'), float('nan')
    or_v = (a*d)/(b*c)
    se   = (1/a+1/b+1/c+1/d)**0.5
    z    = stats.norm.ppf(1-alpha/2)
    return or_v, exp(log(or_v)-z*se), exp(log(or_v)+z*se)

or_v, ci_lo, ci_hi = or_ci(k_q1, k_q3, pm_q1, pm_q3)

stat_lines += [
    "## 3-1: Q3/(Q1+Q3) - kampo vs pubmed_kampo\n",
    f"  2x2 table: kampo(Q1={k_q1}, Q3={k_q3})  pubmed(Q1={pm_q1}, Q3={pm_q3})\n",
    f"  kampo   Q3/(Q1+Q3) = {ks['gap']:.1%}\n",
    f"  pubmed  Q3/(Q1+Q3) = {pms['gap']:.1%}\n\n",
    f"  Chi-square: chi2={chi2:.2f}, df={dof}, p={p_chi2:.2e}\n",
    f"  Fisher:     OR={or_fisher:.3f}, p={p_fisher:.2e}\n",
    f"  Odds Ratio: {or_v:.3f} (95% CI: {ci_lo:.3f}-{ci_hi:.3f})\n",
    f"  Interpretation: Kampo Journal articles are {or_v:.1f}x more likely to\n"
    f"  mention cognition terms alongside formula names vs PubMed articles.\n\n",
]
print(f"  3-1: chi2={chi2:.2f} p={p_chi2:.2e}  OR={or_v:.2f} (95%CI {ci_lo:.2f}-{ci_hi:.2f})")

# 3-2: Cochran-Armitage trend test
def cochran_armitage(n_pos, n_total, years):
    years, n_pos, n_total = (np.array(v, float) for v in (years, n_pos, n_total))
    mask = n_total > 0
    years, n_pos, n_total = years[mask], n_pos[mask], n_total[mask]
    if len(years) < 3: return float('nan'), float('nan')
    p_pool = n_pos.sum() / n_total.sum()
    t = years - years.mean()
    T = (t * n_pos).sum()
    V = p_pool * (1-p_pool) * (n_total * t**2).sum()
    if V <= 0: return float('nan'), float('nan')
    z = T / V**0.5
    return z, 2*(1-stats.norm.cdf(abs(z)))

stat_lines.append("## 3-2: Cochran-Armitage Trend Test (cognition rate over time)\n")
for src, sub, label in [('kampo', k_df, 'Kampo Journal'),
                          ('pubmed_kampo', pm_df, 'PubMed Kampo')]:
    ha = sub[sub['has_abstract'] == True]
    g = ha.groupby('year_bin').agg(
        n=('formula_in_text', 'count'),
        nc=(f'cog_{DV}', 'sum'),
    ).dropna().reset_index()
    g = g[g['n'] >= 5]
    z, p = cochran_armitage(g['nc'].values, g['n'].values, g['year_bin'].values)
    dir_ = 'increasing' if z > 0 else 'decreasing'
    stat_lines.append(f"  {label}: z={z:.3f}, p={p:.2e} ({dir_} trend)\n")
    print(f"  3-2 {label}: z={z:.3f}  p={p:.2e}")

stat_lines.append(f"\n## 3-3: Effect Size Summary\n")
stat_lines.append(f"  OR = {or_v:.3f} (95% CI: {ci_lo:.3f}-{ci_hi:.3f})\n")
stat_lines.append(f"  Kampo Journal is ~{or_v:.1f}x more likely to co-mention\n")
stat_lines.append(f"  cognition terms with formula names.\n")

with open(os.path.join(OUTPUT_DIR, 'statistical_tests.md'), 'w', encoding='utf-8') as f:
    f.writelines(stat_lines)

# ─────────────────────────────────────────────────────────────
# Phase 2 Report
# ─────────────────────────────────────────────────────────────
print("\n  Generating phase2_report.md...")

# Sensitivity robustness
sens_k  = {n: next(r[f'gap_{n}'] for r in sens_rows if r['source']=='kampo')
           for n, _ in FILTERS}
sens_pm = {n: next(r[f'gap_{n}'] for r in sens_rows if r['source']=='pubmed_kampo')
           for n, _ in FILTERS}

# Top cliff formulas
if not cliff_df.empty and 'kampo' in cliff_df['source'].values:
    cpiv = cliff_df[cliff_df['n'] >= 5].pivot(
        index='formula', columns='source', values='cog_rate').dropna()
    if 'kampo' in cpiv and 'pubmed_kampo' in cpiv:
        cpiv['cliff'] = cpiv['kampo'] - cpiv['pubmed_kampo']
        top3_cliff = cpiv.nlargest(3, 'cliff')
        cliff_str = top3_cliff[['kampo','pubmed_kampo','cliff']].to_string()
    else:
        cliff_str = 'N/A'
else:
    cliff_str = 'N/A'

robust_k  = abs(sens_k['liberal'] - sens_k['strict']) < 0.08
robust_pm = abs(sens_pm['liberal'] - sens_pm['strict']) < 0.08

report2 = f"""# Cognitive Gap Analysis - Phase 2 Report
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## 1. Sensitivity Analysis

| Source | Liberal | Conservative | Strict | Robust? |
|--------|---------|--------------|--------|---------|
| kampo | {sens_k['liberal']:.1%} | {sens_k['conservative']:.1%} | {sens_k['strict']:.1%} | {'YES' if robust_k else 'NO'} |
| pubmed_kampo | {sens_pm['liberal']:.1%} | {sens_pm['conservative']:.1%} | {sens_pm['strict']:.1%} | {'YES' if robust_pm else 'NO'} |

Conservative dictionary removed: {', '.join(FP_HARD)} + '冷え' (standalone)

## 2. Main Results (Conservative dict)

### kampo (Journal of Kampo Medicine, JP)
- n={ks['n']:,}, abstract={ks['abs_rate']:.1%}
- Formula mention: {ks['f_rate']:.1%}
- Cognition mention: {ks['c_rate']:.1%}
- **Q3/(Q1+Q3) = {ks['gap']:.1%}**  <- cognitive gap indicator
- Top 5 formulas: {', '.join(ks['top5f'])}
- Top 5 cognition: {', '.join(ks['top5c'])}

### pubmed_kampo (PubMed Kampo, EN)
- n={pms['n']:,}, abstract={pms['abs_rate']:.1%}
- Formula mention: {pms['f_rate']:.1%}
- Cognition mention: {pms['c_rate']:.1%}
- **Q3/(Q1+Q3) = {pms['gap']:.1%}**  <- cognitive gap indicator
- Top 5 formulas: {', '.join(pms['top5f'])}
- Top 5 cognition: {', '.join(pms['top5c'])}

## 3. Statistical Tests

- Chi-square (2x2): chi2={chi2:.2f}, p={p_chi2:.2e}
- Fisher's exact: OR={or_fisher:.3f}, p={p_fisher:.2e}
- **Odds Ratio: {or_v:.3f} (95% CI: {ci_lo:.3f}-{ci_hi:.3f})**
- Interpretation: Kampo Journal {or_v:.1f}x more likely to co-mention
  cognition terms with formula names than PubMed articles.

## 4. Translation Cliff - Top 3 formulas by cliff size

{cliff_str}

## 5. Figure Quality Notes

- **Fig_P2_3** (main figure): Clear side-by-side gap visualization
- **Fig_P2_7** (main figure): Formula-level cliff with annotation
- Fig_P2_6 (supplementary): Co-occurrence heatmap
- Fig_P2_8 (supplementary): Temporal heatmap

## 6. Remaining Issues

- Terms like 'yin-yang', 'liver qi' may appear in pharmacology context
  -> check term_frequencies.csv for pubmed_pharma distribution
- pubmed_acupuncture has very low formula rate (0%)
  -> acupuncture articles don't cite Kampo formulas; gap ratio is undefined
"""

with open(os.path.join(OUTPUT_DIR, 'phase2_report.md'), 'w', encoding='utf-8') as f:
    f.write(report2)

# ─── Final ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("DONE Phase 2")
print("=" * 60)
print(f"  Output: {OUTPUT_DIR}")
print(f"\n  KEY RESULTS:")
print(f"    kampo        Q3/(Q1+Q3) = {ks['gap']:.1%}   (Liberal={sens_k['liberal']:.1%}"
      f"  Strict={sens_k['strict']:.1%})")
print(f"    pubmed_kampo Q3/(Q1+Q3) = {pms['gap']:.1%}   (Liberal={sens_pm['liberal']:.1%}"
      f"  Strict={sens_pm['strict']:.1%})")
print(f"    OR = {or_v:.2f} (95% CI: {ci_lo:.2f}-{ci_hi:.2f})  p={p_chi2:.2e}")
print(f"\n  Files:")
for fname in sorted(os.listdir(OUTPUT_DIR)):
    sz = os.path.getsize(os.path.join(OUTPUT_DIR, fname))
    print(f"    {fname:<52} {sz/1024:>6.0f} KB")
