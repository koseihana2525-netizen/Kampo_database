#!/usr/bin/env python3
"""
漢方論文データベース 認知ギャップ分析
cognitive_gap_analysis.py

「処方言及率」vs「証・漢方思考言及率」を年代別・ジャーナル別に可視化し
「思考なき処方」率 Q3/(Q1+Q3) を算出する。
"""

import os, sys, re, json, importlib.util
from collections import Counter

# ─── パス定義 ──────────────────────────────────────────────────
BASE_DIR   = r'C:\Users\kosei\Desktop\18_東洋医学雑誌'
DATA_DIR   = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'analysis_output')
DICT_PY    = os.path.join(BASE_DIR, 'dictionaries.py')
CAT_JSON   = os.path.join(DATA_DIR, 'categories_v3.json')
MAIN_DB    = os.path.join(DATA_DIR, 'integrated_db.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── 依存パッケージ確認 ─────────────────────────────────────────
import subprocess
for pkg in ['pandas', 'matplotlib', 'seaborn', 'tqdm']:
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from tqdm import tqdm

# 日本語フォント設定（japanize-matplotlib は Python 3.13 非対応のため直接設定）
import matplotlib.font_manager as fm
_JP_FONTS = ['MS Gothic', 'Meiryo', 'Yu Gothic', 'IPAexGothic', 'Noto Sans CJK JP']
_found = [f.name for f in fm.fontManager.ttflist]
for _jp in _JP_FONTS:
    if _jp in _found:
        plt.rcParams['font.family'] = _jp
        break
else:
    # フォールバック: システムフォントを探す
    for _jp in _JP_FONTS:
        try:
            fm.findfont(_jp, fallback_to_default=False)
            plt.rcParams['font.family'] = _jp
            break
        except Exception:
            pass

plt.rcParams.update({'figure.dpi': 100, 'axes.unicode_minus': False})

# ─────────────────────────────────────────────────────────────────
# Step 0: 既存辞書の読み込み
# ─────────────────────────────────────────────────────────────────
print("=" * 60)
print("Step 0: 辞書読み込み")
print("=" * 60)

# dictionaries.py を動的インポート
spec = importlib.util.spec_from_file_location("dictionaries", DICT_PY)
dicts_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dicts_mod)

FORMULAS        = dicts_mod.FORMULAS
EXTRA_FORMULAS  = dicts_mod.EXTRA_FORMULAS
PATTERN_TERMS   = dicts_mod.PATTERN_TERMS     # 気虚・瘀血・八綱・六経 等
ABDOMINAL_TERMS = dicts_mod.ABDOMINAL_TERMS   # 胸脇苦満・心下痞 等

print(f"  FORMULAS     : {len(FORMULAS)} 処方 (ツムラ)")
print(f"  EXTRA_FORMULAS: {len(EXTRA_FORMULAS)} 処方 (非ツムラ)")

# categories_v3.json
with open(CAT_JSON, encoding='utf-8') as f:
    categories_v3 = json.load(f)

# ─── 辞書A: 処方名辞書 ──────────────────────────────────────────
# 日本語（漢字・カタカナ・TJ番号）
formula_ja = []
for num, info in FORMULAS.items():
    formula_ja.append(info['name'])
    for alias in info.get('aliases', []):
        formula_ja.append(alias)
for key, info in EXTRA_FORMULAS.items():
    formula_ja.append(info['name'])
    for alias in info.get('aliases', []):
        formula_ja.append(alias)

# ローマ字処方名（PubMed英語論文用）
FORMULA_ROMAJI = [
    "yokukansan", "yokukansan-ka-chinpi-hange", "yokukansankachimpihange",
    "goreisan", "goshajinkigan", "daikenchuto", "rikkunshito",
    "hochuekkito", "hochuekkito", "keishibukuryogan", "juzentaihoto",
    "ninjinyoeito", "hachimijiogan", "rokumigan", "bofutsushosan",
    "boiogito", "boi-ogi-to", "shosaikoto", "daisaikoto", "saireito",
    "saikokeitshito", "hangeshashinto", "kakkonto", "maoto",
    "shoseiryuto", "bakumondoto", "shinbuto", "tokishakuyakusan",
    "kamishoyosan", "keishi-bukuryo-gan", "shakuyakukanzoto",
    "orengedokuto", "ohrengedokuto", "inchingoreisan", "saibokuto",
    "hangekobokuto", "chotosan", "ninjinto", "seihinto",
    "keishi-karyukotsuboreito", "saikokaryukotsuboreito", "unseiin",
    "unkeito", "sanoshashinto", "jumihaidokuto", "yokuinin",
    "boihuangqitang", "ge-gen-tang", "da-jian-zhong-tang",
    "liu-jun-zi-tang", "bu-zhong-yi-qi-tang",
    # 英語論文でよく見るTsumura製品表記
    *[f"tj-{i:03d}" for i in range(1, 154)],
    *[f"tsumura no. {i}" for i in range(1, 154)],
    *[f"tsumura {i}" for i in range(1, 154)],
]

formula_ja = sorted(set(formula_ja), key=len, reverse=True)
formula_en = sorted(set(FORMULA_ROMAJI), key=len, reverse=True)
print(f"  処方辞書: 日本語 {len(formula_ja)}語, 英語 {len(formula_en)}パターン")

# ─── 辞書B: 証・漢方思考辞書 ─────────────────────────────────────
# PATTERN_TERMS のカテゴリマッピング
PTERM_CATEGORY_MAP = {
    "八綱弁証": "pathology",
    "気血津液弁証": "pathology",
    "臓腑弁証": "pathology",
    "六経弁証": "classical",
}

cognition_ja = {}   # term → category
# PATTERN_TERMS から
for top_cat, sub in PATTERN_TERMS.items():
    mapped_cat = PTERM_CATEGORY_MAP.get(top_cat, "pathology")
    for subcat, terms in sub.items():
        if isinstance(terms, list):
            for term in terms:
                cognition_ja[term] = mapped_cat

# ABDOMINAL_TERMS から
for term in ABDOMINAL_TERMS:
    cognition_ja[term] = "examination"

# 追加（dictionaries.pyにないもの）
extra_ja = {
    # sho_core
    "随証":     "sho_core",
    "弁証":     "sho_core",
    "方証相対": "sho_core",
    "証に基づ": "sho_core",
    "証の変化": "sho_core",
    "証を決定": "sho_core",
    # pathology（PATTERN_TERMSにない表現）
    "気血水":   "pathology",
    "お血":     "pathology",
    "血瘀":     "pathology",
    "冷え症":   "pathology",
    "冷え性":   "pathology",
    "冷え":     "pathology",   # 単体は文脈依存、正規表現フィルタで補正
    "のぼせ":   "pathology",
    "気鬱":     "pathology",
    "気うつ":   "pathology",
    # epistemological
    "未病":         "epistemological",
    "養生":         "epistemological",
    "心身一如":     "epistemological",
    "同病異治":     "epistemological",
    "異病同治":     "epistemological",
    "君臣佐使":     "epistemological",
    "傷寒論":   "classical",
    "金匱要略": "classical",
    "温病":     "classical",
}
for term, cat in extra_ja.items():
    if term not in cognition_ja:
        cognition_ja[term] = cat

# 英語辞書
cognition_en = {
    # sho_core
    "sho ":                             "sho_core",
    "shō":                              "sho_core",
    "sho-based":                        "sho_core",
    "sho pattern":                      "sho_core",
    "pattern diagnosis":                "sho_core",
    "pattern identification":           "sho_core",
    "pattern differentiation":         "sho_core",
    "ho-sho-sotai":                     "sho_core",
    "hoshotai":                         "sho_core",
    # pathology
    "qi deficiency":                    "pathology",
    "blood deficiency":                 "pathology",
    "qi stagnation":                    "pathology",
    "qi counterflow":                   "pathology",
    "blood stasis":                     "pathology",
    "blood stagnation":                 "pathology",
    "oketsu":                           "pathology",
    "water toxin":                      "pathology",
    "fluid disturbance":                "pathology",
    "tan-in":                           "pathology",
    "phlegm-dampness":                  "pathology",
    "yin deficiency":                   "pathology",
    "yang deficiency":                  "pathology",
    "yin-yang":                         "pathology",
    "ki-ketsu-sui":                     "pathology",
    "cold sensitivity":                 "pathology",
    "hie ":                             "pathology",
    "deficiency pattern":               "pathology",
    "excess pattern":                   "pathology",
    "kyo-jitsu":                        "pathology",
    "kyojitsu":                         "pathology",
    "spleen deficiency":                "pathology",
    "kidney deficiency":                "pathology",
    "liver qi":                         "pathology",
    # classical
    "taiyang":                          "classical",
    "shaoyang":                         "classical",
    "yangming":                         "classical",
    "taiyin":                           "classical",
    "shaoyin":                          "classical",
    "jueyin":                           "classical",
    "six stages":                       "classical",
    "shanghan":                         "classical",
    "shang han":                        "classical",
    "jingui":                           "classical",
    "jin gui yao lue":                  "classical",
    # examination
    "abdominal diagnosis":              "examination",
    "fukushin":                         "examination",
    "pulse diagnosis":                  "examination",
    "tongue diagnosis":                 "examination",
    "hypochondriac fullness":           "examination",
    "kyokyo-kuman":                     "examination",
    "splashing sound":                  "examination",
    "abdominal palpation":              "examination",
    # epistemological
    "mibyou":                           "epistemological",
    "mibyo":                            "epistemological",
    "yangsheng":                        "epistemological",
    "yojo ":                            "epistemological",
    "mind-body unity":                  "epistemological",
    "same disease different treatment": "epistemological",
}

print(f"  認知辞書: 日本語 {len(cognition_ja)}語, 英語 {len(cognition_en)}語")

# ──「証」単独の偽陽性除去
# 「認証」「検証」「論証」「保証」「立証」「保証書」等を除外するため
# 安全な複合語パターンのみをカウントする正規表現
SHO_SAFE_RE = re.compile(
    r'(随証|弁証|方証|虚証|実証|虚実|寒証|熱証|表証|裏証|陰証|陽証'
    r'|少陽証|太陽病|少陽病|陽明病|太陰病|少陴病|厥陰病'
    r'|証に基づ|証の変化|証を決定|証型)'
)

# ─────────────────────────────────────────────────────────────────
# Step 1: データ読み込みと基本統計
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 1: データ読み込み")
print("=" * 60)

with open(MAIN_DB, encoding='utf-8') as f:
    raw = json.load(f)

# integrated_db.json の構造を吸収（dict or list）
if isinstance(raw, dict):
    articles = raw.get('articles', [])
    if not articles:
        # キーを探索
        for k, v in raw.items():
            if isinstance(v, list) and len(v) > 100:
                articles = v
                print(f"  articles を '{k}' キーから取得 (n={len(v)})")
                break
elif isinstance(raw, list):
    articles = raw
else:
    raise ValueError(f"未知のJSON構造: {type(raw)}")

df = pd.DataFrame(articles)
print(f"  総件数       : {len(df):,}")
print(f"  カラム一覧   : {list(df.columns)}")

# source, lang
for col in ['source', 'lang']:
    if col in df.columns:
        print(f"\n  {col}別件数:")
        print(df[col].value_counts().to_string())

# year処理
df['year_int'] = pd.to_numeric(df['year'], errors='coerce')
bad_year = df['year_int'].isna().sum()
print(f"\n  year: {int(df['year_int'].min())}-{int(df['year_int'].max())}"
      f", 変換失敗: {bad_year}件")
df['year_bin'] = (df['year_int'] // 5 * 5).astype('Int64')

# abstract 有無
df['has_abstract'] = df['abstract'].apply(
    lambda x: bool(x and str(x).strip()) if x is not None else False
)
print("\n  abstract有無 (source別):")
print(df.groupby('source')['has_abstract'].agg(['sum', 'mean']).rename(
    columns={'sum': 'n_with', 'mean': 'rate'}).round(3).to_string())

# formulas有無（日本語論文のみ有効）
df['has_formulas_field'] = df['formulas'].apply(
    lambda x: bool(x) if isinstance(x, list) else False
)
print("\n  formulas field有無 (source別):")
print(df.groupby('source')['has_formulas_field'].mean().round(3).to_string())

# ─────────────────────────────────────────────────────────────────
# Step 2-3: テキストマッチング
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 2-3: テキストマッチング")
print("=" * 60)

def get_text(row):
    parts = []
    if row.get('title') and str(row['title']).strip():
        parts.append(str(row['title']))
    if row.get('abstract') and str(row['abstract']).strip():
        parts.append(str(row['abstract']))
    return ' '.join(parts)

def match_formula(text, lang):
    """処方名マッチング → マッチした処方名リスト"""
    found = []
    text_lower = text.lower()
    if lang == 'ja':
        for term in formula_ja:
            if term in text:
                found.append(term)
    # 英語パターン（全言語対象: 英語論文 + 日本語論文内の英語表記）
    for term in formula_en:
        if term in text_lower:
            found.append(term)
    return list(set(found))

def match_cognition(text, lang):
    """認知用語マッチング → {term: category}"""
    found = {}
    text_lower = text.lower()
    # 日本語辞書（日本語論文のみ）
    if lang == 'ja':
        for term, cat in cognition_ja.items():
            if term == '証':
                # 安全な複合語パターンのみ
                if SHO_SAFE_RE.search(text):
                    found[term] = cat
            elif term in text:
                found[term] = cat
    # 英語辞書（全言語対象）
    for term, cat in cognition_en.items():
        if term in text_lower:
            found[term] = cat
    return found

match_results = []
for _, row in tqdm(df.iterrows(), total=len(df), desc="Matching"):
    text = get_text(row)
    lang = row.get('lang', 'en') or 'en'

    mf = match_formula(text, lang) if text else []
    mc = match_cognition(text, lang) if text else {}

    f_hit = len(mf) > 0
    c_hit = len(mc) > 0

    if   f_hit and     c_hit: quad = "Q1_both"
    elif not f_hit and c_hit: quad = "Q2_cognition_only"
    elif f_hit and not c_hit: quad = "Q3_formula_only"
    else:                     quad = "Q4_neither"

    # categories field の漢方概念チェック（クロスチェック用）
    cats = row.get('categories', []) or []
    kampo_concept_markers = [
        'blood stasis', 'qi deficiency', 'water retention', 'cold sensitivity',
        '瘀血', '気虚', '水毒', '冷え', '気滞', '血虚', 'phlegm',
    ]
    cog_in_cats = any(
        any(m in str(c).lower() for m in kampo_concept_markers) for c in cats
    )

    match_results.append({
        'formula_in_text':      f_hit,
        'cognition_in_text':    c_hit,
        'formula_in_field':     row['has_formulas_field'],
        'cognition_in_cats':    cog_in_cats,
        'quadrant':             quad,
        'matched_formulas':     '|'.join(mf[:15]),
        'matched_cognition':    '|'.join(list(mc.keys())[:15]),
        'cognition_categories': '|'.join(set(mc.values())),
    })

res = pd.DataFrame(match_results)
df = pd.concat([df.reset_index(drop=True), res.reset_index(drop=True)], axis=1)

# サマリ表示
print(f"\n  処方言及率（全体）: {df['formula_in_text'].mean():.1%}")
print(f"  認知言及率（全体）: {df['cognition_in_text'].mean():.1%}")
print("\n  4象限（全体）:")
print(df['quadrant'].value_counts().to_string())

q1 = (df['quadrant'] == 'Q1_both').sum()
q3 = (df['quadrant'] == 'Q3_formula_only').sum()
GAP_RATIO = q3 / (q1 + q3) if (q1 + q3) > 0 else 0.0
print(f"\n  ★ Q3/(Q1+Q3) = {GAP_RATIO:.1%}  （思考なき処方率）")

print("\n  source別 処方/認知言及率:")
src_stats = df.groupby('source').agg(
    n=('formula_in_text', 'count'),
    formula_rate=('formula_in_text', 'mean'),
    cognition_rate=('cognition_in_text', 'mean'),
).round(3)
src_stats['gap'] = (src_stats['formula_rate'] - src_stats['cognition_rate']).round(3)
print(src_stats.to_string())

# source別 Q3/(Q1+Q3)
print("\n  source別 Q3/(Q1+Q3):")
for src in df['source'].unique():
    sub = df[df['source'] == src]
    s_q1 = (sub['quadrant'] == 'Q1_both').sum()
    s_q3 = (sub['quadrant'] == 'Q3_formula_only').sum()
    ratio = s_q3 / (s_q1 + s_q3) if (s_q1 + s_q3) > 0 else float('nan')
    print(f"    {src:30s}: {ratio:.1%}  (Q1={s_q1}, Q3={s_q3})")

# ─────────────────────────────────────────────────────────────────
# Step 5: 可視化
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 5: 可視化")
print("=" * 60)

SOURCE_ORDER = ['kampo', 'acupuncture', 'pubmed_kampo', 'pubmed_acupuncture', 'pubmed_pharma']
SOURCE_LABELS = {
    'kampo':              '東洋医学雑誌\n(Kampo)',
    'acupuncture':        '全日本鍼灸\n(Acu)',
    'pubmed_kampo':       'PubMed\nKampo',
    'pubmed_acupuncture': 'PubMed\nAcu',
    'pubmed_pharma':      'PubMed\nPharma',
}
QUAD_ORDER  = ['Q1_both', 'Q2_cognition_only', 'Q3_formula_only', 'Q4_neither']
QUAD_LABELS = ['Q1: Formula+Cognition', 'Q2: Cognition only',
               'Q3: Formula only\n(cognitive gap)', 'Q4: Neither']
QUAD_COLORS = ['#2196F3', '#4CAF50', '#FF5722', '#9E9E9E']

def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  保存: {name}")

# ── Fig 0a: source別・年代別論文数 ──────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4))
pivot = (df.groupby(['year_bin', 'source'])
           .size().unstack(fill_value=0)
           .reindex(columns=[s for s in SOURCE_ORDER if s in df['source'].unique()]))
pivot.plot(kind='bar', stacked=True, ax=ax, width=0.85)
ax.set_xlabel('Year (5-year bins)')
ax.set_ylabel('Articles')
ax.set_title('Fig 0a: Articles by Source and Year (5-year bins)', fontweight='bold')
ax.set_xticklabels([str(int(y)) for y in pivot.index], rotation=45, ha='right', fontsize=7)
ax.legend(title='Source', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8)
save(fig, 'Fig_0a_papers_by_source_year.png')

# ── Fig 0b: source別抄録有無 ────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.5, 3.5))
abs_r = df.groupby('source')['has_abstract'].mean().reindex(
    [s for s in SOURCE_ORDER if s in df['source'].unique()])
abs_r.index = [SOURCE_LABELS.get(s, s) for s in abs_r.index]
bars = ax.bar(abs_r.index, abs_r.values * 100, color='steelblue', width=0.55)
ax.bar_label(bars, fmt='%.0f%%', fontsize=8)
ax.set_ylim(0, 110)
ax.set_ylabel('% with abstract')
ax.set_title('Fig 0b: Abstract Availability by Source', fontweight='bold')
plt.xticks(rotation=25, ha='right')
save(fig, 'Fig_0b_abstract_availability.png')

# ── helper: ギャップ時系列描画 ─────────────────────────────────
def plot_gap_series(sub_df, ax, title, min_n=10, show_legend=True):
    has_abs = sub_df[sub_df['has_abstract']].copy()
    g = has_abs.groupby('year_bin').agg(
        n=('formula_in_text', 'count'),
        pf=('formula_in_text', 'mean'),
        pc=('cognition_in_text', 'mean'),
    ).reset_index()
    g = g[g['n'] >= min_n]
    if g.empty:
        ax.text(0.5, 0.5, 'n < threshold', transform=ax.transAxes,
                ha='center', va='center', color='gray')
        ax.set_title(title, fontsize=8)
        return
    x = g['year_bin'].astype(int)
    ax.plot(x, g['pf'] * 100, 'b-o', ms=4, lw=1.5, label='Formula mention %')
    ax.plot(x, g['pc'] * 100, 'r-s', ms=4, lw=1.5, label='Cognition mention %')
    ax.fill_between(x, g['pc'] * 100, g['pf'] * 100,
                    where=g['pf'] >= g['pc'],
                    alpha=0.18, color='royalblue', label='Gap')
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_title(title, fontsize=8, fontweight='bold')
    ax.set_xlabel('Year', fontsize=7)
    ax.set_ylabel('%', fontsize=7)
    ax.grid(axis='y', alpha=0.3)
    if show_legend:
        ax.legend(fontsize=7)

# ── Fig 1: 認知ギャップ時系列（全体） ───────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
plot_gap_series(df, ax,
    f'Fig 1: Cognitive Gap Over Time (All Sources)\n'
    f'Q3/(Q1+Q3) = {GAP_RATIO:.1%}', min_n=15)
save(fig, 'Fig_1_cognitive_gap_timeseries.png')

# ── Fig 2: source別認知ギャップ ──────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()
existing_sources = [s for s in SOURCE_ORDER if s in df['source'].unique()]
for i, src in enumerate(existing_sources):
    sub = df[df['source'] == src]
    s_q1 = (sub['quadrant'] == 'Q1_both').sum()
    s_q3 = (sub['quadrant'] == 'Q3_formula_only').sum()
    ratio = s_q3 / (s_q1 + s_q3) if (s_q1 + s_q3) > 0 else float('nan')
    plot_gap_series(sub, axes[i],
        f'{SOURCE_LABELS.get(src, src)}\n(n={len(sub):,}  gap={ratio:.0%})',
        min_n=8, show_legend=(i == 0))
for j in range(len(existing_sources), len(axes)):
    axes[j].set_visible(False)
fig.suptitle('Fig 2: Cognitive Gap by Source', fontsize=12, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_2_gap_by_source.png')

# ── Fig 3a: 4象限 全体円グラフ ──────────────────────────────────
counts_q = df['quadrant'].value_counts().reindex(QUAD_ORDER, fill_value=0)
fig, ax = plt.subplots(figsize=(6.5, 5.5))
wedges, texts, autotexts = ax.pie(
    counts_q, labels=QUAD_LABELS, colors=QUAD_COLORS,
    autopct='%1.1f%%', startangle=90, pctdistance=0.78,
    wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
)
for at in autotexts:
    at.set_fontsize(8)
ax.set_title(
    f'Fig 3a: 4-Quadrant Distribution (n={len(df):,})\n'
    f'★ Q3/(Q1+Q3) = {GAP_RATIO:.1%}  [Cognitive Gap Ratio]',
    fontweight='bold')
save(fig, 'Fig_3a_quadrant_overall.png')

# ── Fig 3b: source別4象限 積み上げ棒グラフ ─────────────────────
fig, ax = plt.subplots(figsize=(8.5, 4.5))
qbs = (df.groupby('source')['quadrant']
         .value_counts(normalize=True)
         .unstack(fill_value=0)
         .reindex(columns=QUAD_ORDER, fill_value=0)
         .reindex([s for s in SOURCE_ORDER if s in df['source'].unique()]))
qbs.index = [SOURCE_LABELS.get(s, s) for s in qbs.index]
qbs.columns = QUAD_LABELS
qbs.plot(kind='bar', stacked=True, ax=ax, color=QUAD_COLORS, width=0.65)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_ylim(0, 1)
ax.set_title('Fig 3b: 4-Quadrant Distribution by Source', fontweight='bold')
ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=7)
plt.xticks(rotation=25, ha='right')
save(fig, 'Fig_3b_quadrant_by_source.png')

# ── Fig 4: 4象限年代別推移 面グラフ ─────────────────────────────
qt = (df.groupby('year_bin')['quadrant']
        .value_counts(normalize=True)
        .unstack(fill_value=0)
        .reindex(columns=QUAD_ORDER, fill_value=0))
qt.index = qt.index.astype(int)
qt.columns = QUAD_LABELS
fig, ax = plt.subplots(figsize=(11, 5))
qt.plot(kind='area', stacked=True, ax=ax, color=QUAD_COLORS, alpha=0.82)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_ylim(0, 1)
ax.set_xlabel('Year (5-year bins)')
ax.set_ylabel('Proportion')
ax.set_title('Fig 4: 4-Quadrant Composition Over Time', fontweight='bold')
ax.legend(loc='lower left', fontsize=7)
save(fig, 'Fig_4_quadrant_timeseries.png')

# ── Fig 5a: 認知用語頻度 Top30 ──────────────────────────────────
all_cog = []
for v in df['matched_cognition']:
    if v:
        all_cog.extend(t for t in v.split('|') if t)
cog_counter = Counter(all_cog)
top30 = pd.DataFrame(cog_counter.most_common(30), columns=['term', 'count'])
fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(top30['term'][::-1], top30['count'][::-1], color='#E57373')
ax.set_xlabel('Number of articles')
ax.set_title('Fig 5a: Top 30 Cognition Terms (text match)', fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_5a_cognition_terms_top30.png')

# ── Fig 5b: 認知カテゴリ別頻度 ───────────────────────────────────
all_cats = []
for v in df['cognition_categories']:
    if v:
        all_cats.extend(c for c in v.split('|') if c)
cat_counter = Counter(all_cats)
cat_order = ['sho_core', 'pathology', 'classical', 'examination', 'epistemological']
cat_vals  = [cat_counter.get(c, 0) for c in cat_order]
fig, ax = plt.subplots(figsize=(6.5, 4))
bars = ax.bar(cat_order, cat_vals,
              color=['#E91E63', '#9C27B0', '#3F51B5', '#009688', '#FF9800'],
              width=0.55)
ax.bar_label(bars)
ax.set_xlabel('Category')
ax.set_ylabel('Articles')
ax.set_title('Fig 5b: Cognition Terms by Category', fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_5b_cognition_by_category.png')

# ── Fig 6: 認知用語年代別推移（Top10） ──────────────────────────
top10_terms = [t for t, _ in cog_counter.most_common(10)]
tmp_cols = []
for term in top10_terms:
    col = f'__cog_{len(tmp_cols)}'
    df[col] = df['matched_cognition'].apply(
        lambda x, t=term: t in (x or '').split('|'))
    tmp_cols.append((term, col))

cog_time_rows = {}
for term, col in tmp_cols:
    g = df.groupby('year_bin').agg(n=(col, 'count'), hits=(col, 'sum'))
    g['rate'] = g['hits'] / g['n']
    cog_time_rows[term] = g['rate']
cog_time_df = pd.DataFrame(cog_time_rows).fillna(0)
cog_time_df.index = cog_time_df.index.astype(int)
# 一時カラム削除
df.drop(columns=[c for _, c in tmp_cols], inplace=True)

fig, ax = plt.subplots(figsize=(11, 5))
for term in top10_terms:
    ax.plot(cog_time_df.index, cog_time_df[term] * 100,
            marker='o', ms=3, lw=1.2, label=term)
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_xlabel('Year (5-year bins)')
ax.set_ylabel('Mention rate (%)')
ax.set_title('Fig 6: Top Cognition Term Trends Over Time', fontweight='bold')
ax.legend(fontsize=7, bbox_to_anchor=(1.01, 1), loc='upper left')
ax.grid(alpha=0.3)
save(fig, 'Fig_6_cognition_trends.png')

# ── Fig 7: 処方名頻度 Top30 ─────────────────────────────────────
all_f = []
for v in df['matched_formulas']:
    if v:
        all_f.extend(t for t in v.split('|') if t)
formula_counter = Counter(all_f)
top30f = pd.DataFrame(formula_counter.most_common(30), columns=['formula', 'count'])
fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(top30f['formula'][::-1], top30f['count'][::-1], color='#64B5F6')
ax.set_xlabel('Number of articles')
ax.set_title('Fig 7: Top 30 Formula Terms (text match)', fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_7_formula_top30.png')

# ── Fig 8: 検証図（formula_in_text vs formula_in_field） ─────────
ja = df[df['lang'] == 'ja'].copy()
both_f   = ((ja['formula_in_text']) &  (ja['formula_in_field'])).sum()
text_only = ((ja['formula_in_text']) & (~ja['formula_in_field'])).sum()
field_only = ((~ja['formula_in_text']) & (ja['formula_in_field'])).sum()
neither_f = ((~ja['formula_in_text']) & (~ja['formula_in_field'])).sum()
agree_rate = both_f / (both_f + text_only + field_only) if (both_f + text_only + field_only) > 0 else 0

fig, ax = plt.subplots(figsize=(6.5, 4.5))
bars = ax.bar(
    ['Text ∩ Field\n(agree)', 'Text only', 'Field only', 'Neither'],
    [both_f, text_only, field_only, neither_f],
    color=['#4CAF50', '#2196F3', '#FF9800', '#9E9E9E'], width=0.5
)
ax.bar_label(bars)
ax.set_ylabel('Articles (Japanese only)')
ax.set_title(f'Fig 8: Formula Detection Validation (JP, n={len(ja):,})\n'
             f'Agreement = {agree_rate:.1%}', fontweight='bold')
save(fig, 'Fig_8_validation.png')

# ─────────────────────────────────────────────────────────────────
# Step 7: CSV出力
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 7: CSV出力")
print("=" * 60)

# papers_classified.csv
out_cols = ['id', 'title', 'year', 'year_bin', 'source', 'lang', 'has_abstract',
            'formula_in_text', 'cognition_in_text', 'formula_in_field',
            'cognition_in_cats', 'quadrant', 'matched_formulas',
            'matched_cognition', 'cognition_categories']
out_cols = [c for c in out_cols if c in df.columns]
df[out_cols].to_csv(os.path.join(OUTPUT_DIR, 'papers_classified.csv'),
                    index=False, encoding='utf-8-sig')
print(f"  papers_classified.csv: {len(df)} rows")

# yearly_gap_stats.csv
abs_df = df[df['has_abstract']].copy()
yearly = abs_df.groupby('year_bin').agg(
    n=('formula_in_text', 'count'),
    n_formula=('formula_in_text', 'sum'),
    n_cognition=('cognition_in_text', 'sum'),
).reset_index()
yearly['pct_formula']   = (yearly['n_formula']   / yearly['n']).round(4)
yearly['pct_cognition'] = (yearly['n_cognition'] / yearly['n']).round(4)
yearly['gap']           = (yearly['pct_formula'] - yearly['pct_cognition']).round(4)
yearly.to_csv(os.path.join(OUTPUT_DIR, 'yearly_gap_stats.csv'),
              index=False, encoding='utf-8-sig')

# source_yearly_gap.csv
src_yearly = abs_df.groupby(['source', 'year_bin']).agg(
    n=('formula_in_text', 'count'),
    n_formula=('formula_in_text', 'sum'),
    n_cognition=('cognition_in_text', 'sum'),
).reset_index()
src_yearly['pct_formula']   = (src_yearly['n_formula']   / src_yearly['n']).round(4)
src_yearly['pct_cognition'] = (src_yearly['n_cognition'] / src_yearly['n']).round(4)
src_yearly['gap']           = (src_yearly['pct_formula'] - src_yearly['pct_cognition']).round(4)
src_yearly.to_csv(os.path.join(OUTPUT_DIR, 'source_yearly_gap.csv'),
                  index=False, encoding='utf-8-sig')

# term_frequencies.csv
term_rows = []
all_terms = {**{t: c for t, c in cognition_ja.items()},
             **{t: c for t, c in cognition_en.items()}}
for term, cat in all_terms.items():
    row = {'term': term, 'category': cat, 'n_total': cog_counter.get(term, 0)}
    for src in SOURCE_ORDER:
        row[f'n_{src}'] = df[df['source'] == src]['matched_cognition'].apply(
            lambda x, t=term: t in (x or '').split('|')).sum()
    term_rows.append(row)
pd.DataFrame(term_rows).sort_values('n_total', ascending=False).to_csv(
    os.path.join(OUTPUT_DIR, 'term_frequencies.csv'), index=False, encoding='utf-8-sig')

# formula_frequencies.csv
f_rows = []
for formula, count in formula_counter.most_common():
    row = {'formula': formula, 'n_total': count}
    for src in SOURCE_ORDER:
        row[f'n_{src}'] = df[df['source'] == src]['matched_formulas'].apply(
            lambda x, f=formula: f in (x or '').split('|')).sum()
    f_rows.append(row)
pd.DataFrame(f_rows).to_csv(os.path.join(OUTPUT_DIR, 'formula_frequencies.csv'),
                             index=False, encoding='utf-8-sig')

print("  CSV出力完了")

# ─────────────────────────────────────────────────────────────────
# サマリーレポート生成
# ─────────────────────────────────────────────────────────────────
gap_max = yearly.loc[yearly['gap'].idxmax()]

q_src_lines = []
for src in SOURCE_ORDER:
    sub = df[df['source'] == src]
    s_q1 = (sub['quadrant'] == 'Q1_both').sum()
    s_q3 = (sub['quadrant'] == 'Q3_formula_only').sum()
    ratio = s_q3 / (s_q1 + s_q3) if (s_q1 + s_q3) > 0 else float('nan')
    q_src_lines.append(f"| {src} | {s_q1} | {s_q3} | {ratio:.1%} |")

report = f"""# 漢方論文データベース 認知ギャップ分析レポート
生成: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## 1. データ概要
- 総件数: {len(df):,}件
- source別: {df['source'].value_counts().to_dict()}
- year範囲: {int(df['year_int'].min())}–{int(df['year_int'].max())}
- 抄録有り率: 全体 {df['has_abstract'].mean():.1%}

## 2. 辞書
- 処方名辞書: 日本語 {len(formula_ja)}語, 英語パターン {len(formula_en)}語
- 認知辞書: 日本語 {len(cognition_ja)}語 + 英語 {len(cognition_en)}語
  - sho_core: {sum(1 for v in cognition_ja.values() if v=='sho_core')}語
  - pathology: {sum(1 for v in cognition_ja.values() if v=='pathology')}語
  - classical: {sum(1 for v in cognition_ja.values() if v=='classical')}語
  - examination: {sum(1 for v in cognition_ja.values() if v=='examination')}語
  - epistemological: {sum(1 for v in cognition_ja.values() if v=='epistemological')}語

## 3. マッチング結果
- 処方言及率（全体）: {df['formula_in_text'].mean():.1%}
- 認知言及率（全体）: {df['cognition_in_text'].mean():.1%}

### source別
| source | formula | cognition | gap |
|--------|---------|-----------|-----|
{chr(10).join(
    f"| {s} | {df[df['source']==s]['formula_in_text'].mean():.1%} | "
    f"{df[df['source']==s]['cognition_in_text'].mean():.1%} | "
    f"{df[df['source']==s]['formula_in_text'].mean() - df[df['source']==s]['cognition_in_text'].mean():+.1%} |"
    for s in SOURCE_ORDER if s in df['source'].unique()
)}

## 4. 認知ギャップの要約

### ★ Q3/(Q1+Q3) = {GAP_RATIO:.1%}
「処方に言及する論文のうち、漢方思考に言及しない割合」

| source | Q1 | Q3 | Q3/(Q1+Q3) |
|--------|----|----|------------|
{chr(10).join(q_src_lines)}

- ギャップが最大の年代: {int(gap_max['year_bin'])}年代 (gap = {gap_max['gap']:.1%})

## 5. 頻出語（Top 20）
### 処方名
{chr(10).join(f'- {f}: {c}件' for f, c in formula_counter.most_common(20))}

### 認知用語
{chr(10).join(f'- {t}: {c}件' for t, c in cog_counter.most_common(20))}

## 6. 検証（日本語論文: formula_in_text vs formula_in_field）
- Text ∩ Field (agree): {both_f}
- Text only: {text_only}
- Field only: {field_only}
- Agreement rate: {agree_rate:.1%}

## 7. 方法論上の注意
- PubMed論文の `formulas` フィールドは常に空 → テキストマッチで補完
- 「証」単独は `認証`/`検証`/`論証` 等の誤マッチを防ぐため複合語パターンのみ計上
- 抄録なし論文 ({(~df['has_abstract']).sum():,}件) は言及率計算から除外
- 「認知言及」= テキストへの言及であり著者の意図的使用の直接証拠ではない
- `冷え`・`動悸`・`浮腫` は一般症状語でもある点に注意

## 8. 次のステップの提案
- `term_frequencies.csv` で偽陽性候補の用語を確認（source別分布が不自然なもの）
- Q3が大きいsourceについてサンプル論文を確認（質的検証）
- 年代別ギャップのχ²検定または傾向検定
- 認知語の共起分析（どの処方と共起するか）
- 「冷え」等の曖昧語のさらなる絞り込み
"""

with open(os.path.join(OUTPUT_DIR, 'cognitive_gap_report.md'), 'w', encoding='utf-8') as f:
    f.write(report)

# ─── 完了サマリ ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
print(f"  出力先: {OUTPUT_DIR}")
print(f"\n  [*] Q3/(Q1+Q3) = {GAP_RATIO:.1%}  (思考なき処方率)")
print(f"\n  生成ファイル:")
for fname in sorted(os.listdir(OUTPUT_DIR)):
    sz = os.path.getsize(os.path.join(OUTPUT_DIR, fname))
    print(f"    {fname:<45} {sz/1024:>6.0f} KB")
