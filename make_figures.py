# -*- coding: utf-8 -*-
"""
make_figures.py - Generate publication-quality figures for JGFM paper
Figure 1: Top 30 formula frequency (horizontal bar chart)
Figure 2: ICD category × Top formula heatmap (evidence gap map)
Figure 3: Publication timeline with formula coverage
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from collections import Counter

rcParams['font.family'] = 'Yu Gothic'
rcParams['axes.unicode_minus'] = False
rcParams['savefig.dpi'] = 300
rcParams['savefig.bbox'] = 'tight'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

with open(os.path.join(BASE_DIR, "output/kampo_db_v3.json"), "r", encoding="utf-8") as f:
    DB = json.load(f)

# ────────────────────────────────────────
# Figure 1: Top 30 Formula Frequency
# ────────────────────────────────────────
def fig1_formula_frequency():
    top30 = list(DB['fs'].items())[:30]
    names = [f[0] for f in top30][::-1]
    counts = [f[1]['n'] for f in top30][::-1]
    origins = [f[1]['o'] for f in top30][::-1]
    colors = ['#c0392b' if o == '経方' else '#2980b9' for o in origins]

    fig, ax = plt.subplots(figsize=(8, 10))
    bars = ax.barh(range(len(names)), counts, color=colors, height=0.7, edgecolor='white', linewidth=0.5)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel('Number of Articles', fontsize=12)
    ax.set_title('Top 30 Kampo Formulas in the Japanese Journal of Oriental Medicine\n(1982-2025, N=2,003)', fontsize=13, fontweight='bold', pad=15)

    # Add count labels
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                str(cnt), va='center', fontsize=9, color='#555')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#c0392b', label='Keihō (傷寒論/金匱要略)'),
        Patch(facecolor='#2980b9', label='Goseihō (後世方)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(0, max(counts) * 1.15)

    path = os.path.join(FIG_DIR, "fig1_formula_frequency.png")
    fig.savefig(path)
    plt.close()
    print(f"Fig 1 saved: {path}")


# ────────────────────────────────────────
# Figure 2: ICD Category × Top Formula Evidence Gap Map
# ────────────────────────────────────────
def fig2_evidence_gap():
    # Get ICD categories (lv2 level)
    icd_cat = DB['ct'][0]  # ICD疾患分類
    lv2_names = [lv2['name'] for lv2 in icd_cat['children']]

    # Get top 20 formulas
    top20 = list(DB['fs'].items())[:20]
    formula_names = [f[0] for f in top20]

    # Build matrix: rows=ICD lv2, cols=formulas
    matrix = np.zeros((len(lv2_names), len(formula_names)))

    for i, lv2 in enumerate(icd_cat['children']):
        # Get all article indices for this lv2 category
        lv2_indices = set()
        for lv3 in lv2['children']:
            lv2_indices.update(DB['ci'].get(lv3['name'], []))
        # Count formulas
        for idx in lv2_indices:
            for f in DB['articles'][idx]['f']:
                if f in formula_names:
                    j = formula_names.index(f)
                    matrix[i][j] += 1

    fig, ax = plt.subplots(figsize=(16, 9))

    # Use bubble chart with larger scaling
    max_val = matrix.max()
    for i in range(len(lv2_names)):
        for j in range(len(formula_names)):
            val = matrix[i][j]
            if val > 0:
                size = max(val / max_val * 600, 30)
                alpha = min(0.35 + val / max_val * 0.6, 0.95)
                ax.scatter(j, i, s=size, c='#2980b9', alpha=alpha, edgecolors='#1a5276', linewidth=0.5)
                if val >= 2:
                    ax.text(j, i, str(int(val)), ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    ax.set_xticks(range(len(formula_names)))
    ax.set_xticklabels(formula_names, rotation=55, ha='right', fontsize=10)
    ax.set_yticks(range(len(lv2_names)))
    ax.set_yticklabels(lv2_names, fontsize=11)
    ax.set_title('Evidence Gap Map: ICD Disease Categories × Top 20 Kampo Formulas\n(Bubble size = number of articles)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(-0.7, len(formula_names) - 0.3)
    ax.set_ylim(-0.7, len(lv2_names) - 0.3)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.invert_yaxis()
    fig.subplots_adjust(bottom=0.22, left=0.15)

    path = os.path.join(FIG_DIR, "fig2_evidence_gap.png")
    fig.savefig(path)
    plt.close()
    print(f"Fig 2 saved: {path}")


# ────────────────────────────────────────
# Figure 3: Publication Timeline
# ────────────────────────────────────────
def fig3_timeline():
    years = sorted(DB['yd'].keys())
    counts = [DB['yd'][y] for y in years]

    # Count articles with formulas per year
    formula_counts = Counter()
    abstract_counts = Counter()
    for a in DB['articles']:
        y = a['y']
        if y:
            if a['f']:
                formula_counts[y] += 1
            if a['ab']:
                abstract_counts[y] += 1

    fc = [formula_counts.get(y, 0) for y in years]
    ac = [abstract_counts.get(y, 0) for y in years]
    no_formula = [c - f for c, f in zip(counts, fc)]

    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(years))
    width = 0.8

    ax.bar(x, fc, width, label='With formula identification', color='#2980b9', alpha=0.85)
    ax.bar(x, no_formula, width, bottom=fc, label='Without formula identification', color='#bdc3c7', alpha=0.7)
    ax.plot(x, ac, color='#e74c3c', linewidth=1.5, marker='.', markersize=4, label='With abstract', alpha=0.8)

    ax.set_xticks(x[::5])
    ax.set_xticklabels([years[i] for i in range(0, len(years), 5)], fontsize=9)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Number of Articles', fontsize=12)
    ax.set_title('Publication Timeline of the Japanese Journal of Oriental Medicine\n(1982-2025, N=2,003)', fontsize=13, fontweight='bold', pad=15)
    ax.legend(fontsize=10, loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    path = os.path.join(FIG_DIR, "fig3_timeline.png")
    fig.savefig(path)
    plt.close()
    print(f"Fig 3 saved: {path}")


if __name__ == '__main__':
    fig1_formula_frequency()
    fig2_evidence_gap()
    fig3_timeline()
    print("\nAll figures generated!")
