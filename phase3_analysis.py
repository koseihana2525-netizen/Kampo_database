# -*- coding: utf-8 -*-
"""
phase3_analysis.py
DB再構築 + 辞書v2 + 全分析再実行
"""

import os, sys, json, random, importlib.util, re
from collections import Counter, defaultdict
from math import log, exp

sys.stdout.reconfigure(encoding='utf-8')

import subprocess
for pkg in ['pandas','matplotlib','seaborn','scipy','statsmodels','numpy','tqdm']:
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable,'-m','pip','install',pkg],
                                               stdout=subprocess.DEVNULL)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

import matplotlib.font_manager as fm
for _jp in ['MS Gothic','Meiryo','Yu Gothic','IPAexGothic']:
    if _jp in [f.name for f in fm.fontManager.ttflist]:
        plt.rcParams['font.family'] = _jp
        break

plt.rcParams.update({'axes.unicode_minus':False,'font.size':9,
                     'axes.spines.top':False,'axes.spines.right':False})

CB = {'blue':'#2166ac','red':'#b2182b','green':'#1b7837',
      'gray':'#969696','lblue':'#74add1','lred':'#f4a582',
      'orange':'#d6604d','purple':'#762a83'}

BASE   = r'C:\Users\kosei\Desktop\18_東洋医学雑誌'
DATA   = os.path.join(BASE, 'data')
OUTPUT = os.path.join(BASE, 'analysis_output', 'phase3')
os.makedirs(OUTPUT, exist_ok=True)

def save(fig, name, dpi=300):
    p = os.path.join(OUTPUT, name)
    fig.savefig(p, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {name}')

# ═══════════════════════════════════════════════════════════════
# PART 1: DB 再構築（T5: 非日本除外）
# ═══════════════════════════════════════════════════════════════
print('='*60)
print('PART 1: DB再構築（T5 非日本除外）')
print('='*60)

# PubMed tagged から PMID→affiliation マップを構築
with open(os.path.join(DATA,'pubmed','pubmed_tagged.json'),'r',encoding='utf-8') as f:
    pm_tagged = json.load(f)

pmid_affil = {a['pmid']: (a.get('affiliation','') or '') for a in pm_tagged}

def is_japan_affiliated(article):
    if article.get('source') in ('kampo','acupuncture'):
        return True
    pmid = article.get('id','')[3:]  # pm_XXXX -> XXXX
    affil = pmid_affil.get(pmid, '').lower()
    if not affil.strip():
        return True  # affiliationなし → 保守的に保持
    japan_indicators = ['japan','japanese','nippon','nihon']
    non_japan = ['china','chinese','korea','korean','taiwan','hong kong']
    has_jp  = any(j in affil for j in japan_indicators)
    has_nonj = any(n in affil for n in non_japan)
    if has_nonj and not has_jp:
        return False
    return True

with open(os.path.join(DATA,'integrated_db.json'),'r',encoding='utf-8') as f:
    db_orig = json.load(f)

articles_all = db_orig['articles']
excluded = [a for a in articles_all if not is_japan_affiliated(a)]
articles_jp = [a for a in articles_all if is_japan_affiliated(a)]

# 除外集計
src_excl = Counter(a['source'] for a in excluded)
country_excl = Counter()
for a in excluded:
    pmid = a.get('id','')[3:]
    affil = pmid_affil.get(pmid,'').lower()
    if 'china' in affil or 'chinese' in affil: country_excl['China'] += 1
    elif 'korea' in affil or 'korean' in affil: country_excl['Korea'] += 1
    elif 'taiwan' in affil: country_excl['Taiwan'] += 1
    elif 'hong kong' in affil: country_excl['Hong Kong'] += 1
    else: country_excl['Other'] += 1

print(f'元DB: {len(articles_all)}件')
print(f'除外: {len(excluded)}件  残存: {len(articles_jp)}件')
print(f'source別除外: {dict(src_excl)}')
print(f'国別除外: {dict(country_excl)}')

# 新DB保存
src_cnt_new = Counter(a['source'] for a in articles_jp)
years_new = [int(a['year']) for a in articles_jp if a.get('year','').isdigit()]
stats_new = {
    'total': len(articles_jp),
    **{k:v for k,v in src_cnt_new.items()},
    'jp_total': src_cnt_new.get('kampo',0)+src_cnt_new.get('acupuncture',0),
    'pm_total': len(articles_jp)-src_cnt_new.get('kampo',0)-src_cnt_new.get('acupuncture',0),
    'year_min': str(min(years_new)), 'year_max': str(max(years_new)),
    'with_abstract': sum(1 for a in articles_jp if a.get('abstract')),
}
db_japan = dict(db_orig)
db_japan['articles'] = articles_jp
db_japan['stats']    = stats_new
with open(os.path.join(DATA,'integrated_db_japan.json'),'w',encoding='utf-8') as f:
    json.dump(db_japan, f, ensure_ascii=False)
print(f'Saved: integrated_db_japan.json ({os.path.getsize(os.path.join(DATA,"integrated_db_japan.json"))//1024//1024} MB)')

# ═══════════════════════════════════════════════════════════════
# PART 2: 辞書 v2 構築（T1–T4）
# ═══════════════════════════════════════════════════════════════
print()
print('='*60)
print('PART 2: 辞書v2構築')
print('='*60)

spec = importlib.util.spec_from_file_location('dictionaries', os.path.join(BASE,'dictionaries.py'))
dmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmod)

PTERM_CAT = {'八綱弁証':'pathology','気血津液弁証':'pathology',
             '臓腑弁証':'pathology','六経弁証':'classical'}
ALL_TERMS_BASE = {}
for top_cat, sub in dmod.PATTERN_TERMS.items():
    cat = PTERM_CAT.get(top_cat, 'pathology')
    for subcat, tlist in sub.items():
        if isinstance(tlist, list):
            for t in tlist: ALL_TERMS_BASE[t] = cat
for t in dmod.ABDOMINAL_TERMS:
    ALL_TERMS_BASE[t] = 'examination'

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
    if t not in ALL_TERMS_BASE: ALL_TERMS_BASE[t] = c

# T1: 追加語
T1_ADDITIONS = {
    # classical
    '奔豚':'classical','奔豚気':'classical','奔豚病':'classical','煩躁':'classical',
    'hontonki':'classical','honton':'classical','running piglet':'classical',
    # sho_core
    '転方':'sho_core','switching formula':'sho_core',
    # examination
    '尿自利':'examination','小便自利':'examination',
    '小便不利':'examination','尿不利':'examination',
    'urinary dysfunction':'examination',
    # epistemological
    '瞑眩':'epistemological','menken':'epistemological','healing crisis':'epistemological',
    # pathology
    'heat syndrome':'pathology',
}

ALL_TERMS_V2 = dict(ALL_TERMS_BASE)
for t, c in T1_ADDITIONS.items():
    ALL_TERMS_V2[t] = c
print(f'辞書v2: {len(ALL_TERMS_V2)}語（base: {len(ALL_TERMS_BASE)}, 追加: {len(T1_ADDITIONS)}）')

# T3: 瘀血表記ゆれ（DB内の〓血件数を確認）
oketsu_variants = ['瘀血','お血','おけつ','オケツ','〓血']
garbled_count = sum(1 for a in articles_jp
                    if '〓血' in (a.get('title','')+a.get('abstract','')))
print(f'T3 文字化け（〓血）: {garbled_count}件')

# T2: テキスト正規化関数（ハイフン → スペース変換）
def normalize_text(text):
    """ハイフンをスペースに正規化 + 瘀血表記揺れを統一"""
    text = text.replace('-', ' ')
    for v in oketsu_variants:
        if v != '瘀血': text = text.replace(v, '瘀血')
    return text

# FP_HARD（Conservative辞書の除外語）
FP_HARD = {'出血','発熱','浮腫','動悸'}
STRICT_REMOVE = FP_HARD | {'冷え','冷え症','冷え性','のぼせ','陰虚','陽虚',
                            '悪寒','潮熱','微熱','yin-yang',
                            'yin deficiency','yang deficiency',
                            'yang deficiency ','yin deficiency '}

def filter_liberal(text_norm):
    return [(t,c) for t,c in ALL_TERMS_V2.items() if t in text_norm]

def filter_conservative_v2(text_norm, hits_liberal):
    """Conservative: FP_HARD除外 + T4随証共起ルール"""
    base = [(t,c) for t,c in hits_liberal if t not in FP_HARD and t != '冷え']
    # T4: 「随証」が含まれる場合、pathology/examination/classical の共起チェック
    result = []
    zuisho_hit = any(t == '随証' for t,c in base)
    non_sho_cats = {c for t,c in base if c in ('pathology','examination','classical')}
    for t, c in base:
        if t == '随証' and zuisho_hit and not non_sho_cats:
            continue  # 随証のみ → 除外
        result.append((t, c))
    return result

def filter_strict(text_norm, hits_liberal):
    base = [(t,c) for t,c in hints if t not in STRICT_REMOVE
            for hints in [(hits_liberal,)]][0]  # broken - use list comp below
    return [(t,c) for t,c in hits_liberal if t not in STRICT_REMOVE]

def apply_filters(article):
    """1論文に3辞書を適用"""
    title = article.get('title','') or ''
    ab    = article.get('abstract','') or ''
    raw   = (title + ' ' + ab).lower()
    norm  = normalize_text(raw)

    lib   = filter_liberal(norm)
    cons  = filter_conservative_v2(norm, lib)
    strict= [(t,c) for t,c in lib if t not in STRICT_REMOVE]

    return lib, cons, strict

# T4の効果を確認
zuisho_total = zuisho_reclassified = 0
for a in articles_jp:
    if a.get('source') not in ('kampo','pubmed_kampo'): continue
    lib, cons, _ = apply_filters(a)
    if any(t=='随証' for t,c in lib):
        zuisho_total += 1
        if not any(t=='随証' for t,c in cons):
            zuisho_reclassified += 1
print(f'T4 随証ヒット総数: {zuisho_total}件  再分類（除外）: {zuisho_reclassified}件')

# T1追加語の効果
t1_hits = Counter()
for a in articles_jp:
    title = a.get('title','') or ''
    ab    = a.get('abstract','') or ''
    raw   = (title+' '+ab).lower()
    norm  = normalize_text(raw)
    for t in T1_ADDITIONS:
        if t in norm: t1_hits[t] += 1
print(f'T1 追加語ヒット件数（上位10）:')
for t,c in t1_hits.most_common(10):
    print(f'  {c:4d}  {t}')

# ═══════════════════════════════════════════════════════════════
# PART 3: 全分析再実行
# ═══════════════════════════════════════════════════════════════
print()
print('='*60)
print('PART 3: 全分析再実行')
print('='*60)

# 処方辞書
formula_ja = []
for num, info in dmod.FORMULAS.items():
    formula_ja.append(info['name'])
    for alias in info.get('aliases',[]): formula_ja.append(alias)
for key, info in dmod.EXTRA_FORMULAS.items():
    formula_ja.append(info['name'])
    for alias in info.get('aliases',[]): formula_ja.append(alias)
FORMULA_ROMAJI = [
    'yokukansan','goreisan','goshajinkigan','daikenchuto','rikkunshito',
    'hochuekkito','keishibukuryogan','juzentaihoto','ninjinyoeito',
    'hachimijiogan','bofutsushosan','shosaikoto','daisaikoto','saireito',
    'hangeshashinto','kakkonto','maoto','shoseiryuto','bakumondoto',
    'shinbuto','tokishakuyakusan','kamishoyosan','shakuyakukanzoto',
    'orengedokuto','jumihaidokuto','unseiin','chotosan','ninjinto',
    'keishi-karyukotsuboreito','saikokaryukotsuboreito',
    'yokukansan-ka-chinpi-hange','hangekobokuto','boiogito','choreito',
    'saibokuto','keishikajutsubuto','yokukansankachinpihange',
    'inchinkoto','seihinto','anchusan','kososan','kamikihito','sansoninto',
    'bu-zhong-yi-qi-tang','da-jian-zhong-tang','liu-jun-zi-tang','ge-gen-tang',
    'running piglet',  # T1
]
for i in range(1,154):
    FORMULA_ROMAJI += [f'tj-{i:03d}',f'tsumura no. {i}',f'tsumura {i}']
formula_ja = sorted(set(formula_ja), key=len, reverse=True)
formula_en = sorted(set(FORMULA_ROMAJI), key=len, reverse=True)

def match_formulas(text, lang):
    found = []; remaining = text
    if lang == 'ja':
        for name in formula_ja:
            if name in remaining:
                found.append(name)
                remaining = remaining.replace(name, '\x00'*len(name))
    else:
        text_l = normalize_text(text.lower())
        for name in formula_en:
            if name in text_l: found.append(name)
    return found

# 全論文を3辞書で分類
print('  全論文を分類中...')
rows = []
for a in articles_jp:
    title = a.get('title','') or ''
    ab    = a.get('abstract','') or ''
    has_ab = bool(ab.strip())
    year = a.get('year','')
    year_int = int(year) if year.isdigit() else None

    f_hits = match_formulas(title+' '+ab, a['lang'])
    f_hit  = bool(f_hits)

    lib, cons, strict_hits = apply_filters(a)

    def quad(f, c_hits):
        if   f and c_hits: return 'Q1_both'
        elif c_hits:       return 'Q2_cognition_only'
        elif f:            return 'Q3_formula_only'
        else:              return 'Q4_neither'

    row = {
        'id': a['id'], 'source': a['source'], 'lang': a['lang'],
        'year': year, 'year_int': year_int,
        'has_abstract': has_ab,
        'formula_in_text': f_hit,
        'formulas_matched': '|'.join(f_hits[:5]),
        'quad_liberal':      quad(f_hit, lib),
        'quad_conservative': quad(f_hit, cons),
        'quad_strict':       quad(f_hit, strict_hits),
        'cog_liberal':       bool(lib),
        'cog_conservative':  bool(cons),
        'cog_strict':        bool(strict_hits),
        'matched_conservative': '|'.join(sorted(set(t for t,c in cons))),
        'year_bin': (year_int//10*10) if year_int else None,
    }
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUTPUT,'papers_classified_v2.csv'), index=False, encoding='utf-8-sig')
print(f'  papers_classified_v2.csv: {len(df)}行')

# 3-2: 主要指標
print()
print('  === 主要指標 (Conservative v2) ===')
sens_rows = []
for src in ['kampo','acupuncture','pubmed_kampo','pubmed_acupuncture','pubmed_pharma']:
    sub = df[df['source']==src]
    for name in ['liberal','conservative','strict']:
        qcol = f'quad_{name}'
        ccol = f'cog_{name}'
        has_abs = sub[sub['has_abstract']]
        q1 = (has_abs[qcol]=='Q1_both').sum()
        q3 = (has_abs[qcol]=='Q3_formula_only').sum()
        gap = q3/(q1+q3) if (q1+q3) > 0 else float('nan')
        cog_rate = has_abs[ccol].mean() if len(has_abs) > 0 else float('nan')
        sens_rows.append({'source':src,'dict':name,'n':len(sub),'n_abs':len(has_abs),
                          'Q1':q1,'Q3':q3,'gap':gap,'cog_rate':cog_rate})
        if name == 'conservative':
            print(f'  {src:24s} [conservative] cog={cog_rate:.1%}  Q3/(Q1+Q3)={gap:.1%}  Q1={q1} Q3={q3}')

sens_df = pd.DataFrame(sens_rows)
sens_df.to_csv(os.path.join(OUTPUT,'sensitivity_analysis_v2.csv'), index=False, encoding='utf-8-sig')

# OR + Fisher
from scipy.stats import fisher_exact
k_row = sens_df[(sens_df['source']=='kampo')&(sens_df['dict']=='conservative')].iloc[0]
pm_row = sens_df[(sens_df['source']=='pubmed_kampo')&(sens_df['dict']=='conservative')].iloc[0]
k_q1, k_q3 = int(k_row['Q1']), int(k_row['Q3'])
pm_q1, pm_q3 = int(pm_row['Q1']), int(pm_row['Q3'])
tbl = [[k_q1, k_q3],[pm_q1, pm_q3]]
oddsratio, pval = fisher_exact(tbl, alternative='two-sided')
from scipy.stats.contingency import odds_ratio as odds_ratio_ci
res_ci = odds_ratio_ci(tbl)
ci_low, ci_high = res_ci.confidence_interval(confidence_level=0.95)
print(f'\n  Fisher OR={oddsratio:.2f} (95%CI: {ci_low:.2f}–{ci_high:.2f}) p={pval:.2e}')
print(f'  kampo  Q3/(Q1+Q3)={k_q3/(k_q1+k_q3):.1%}  (Q1={k_q1} Q3={k_q3})')
print(f'  pubmed Q3/(Q1+Q3)={pm_q3/(pm_q1+pm_q3):.1%}  (Q1={pm_q1} Q3={pm_q3})')

# 3-5: 言語間認知格差
print()
print('  === 言語間認知格差 ===')
FORMULA_MAP = {
    '抑肝散':['yokukansan','yokukansankachinpihange','yokukansan-ka-chinpi-hange'],
    '五苓散':['goreisan'],'牛車腎気丸':['goshajinkigan'],
    '大建中湯':['daikenchuto'],'六君子湯':['rikkunshito'],
    '補中益気湯':['hochuekkito','bu-zhong-yi-qi-tang'],
    '桂枝茯苓丸':['keishibukuryogan'],'十全大補湯':['juzentaihoto'],
    '人参養栄湯':['ninjinyoeito'],'八味地黄丸':['hachimijiogan'],
    '小柴胡湯':['shosaikoto'],'大柴胡湯':['daisaikoto'],
    '五苓散2':['goreisan'],'柴苓湯':['saireito'],
    '半夏瀉心湯':['hangeshashinto'],
}
cliff_rows = []
for jp_name, romaji_list in list(FORMULA_MAP.items())[:15]:
    for src_key, src_label, lang in [('kampo','東洋医学雑誌','ja'),
                                      ('pubmed_kampo','PubMed Kampo','en')]:
        sub = df[(df['source']==src_key)&(df['has_abstract'])].copy()
        # formula hit
        col = 'formulas_matched'
        all_pats = [jp_name] + (romaji_list if lang=='en' else [])
        has_formula = sub[col].apply(
            lambda x: any(p in str(x) for p in ([jp_name] if lang=='ja' else romaji_list)))
        sub_f = sub[has_formula]
        if len(sub_f) == 0:
            cliff_rows.append({'formula_jp':jp_name,'source':src_label,
                                'n_formula':0,'n_cog':0,'cog_rate':float('nan')})
            continue
        cog_rate = sub_f['cog_conservative'].mean()
        cliff_rows.append({'formula_jp':jp_name,'source':src_label,
                            'n_formula':len(sub_f),'n_cog':int(sub_f['cog_conservative'].sum()),
                            'cog_rate':cog_rate})

cliff_df = pd.DataFrame(cliff_rows)
cliff_df.to_csv(os.path.join(OUTPUT,'translation_cliff_v2.csv'), index=False, encoding='utf-8-sig')
# top 3
cliff_pivot = cliff_df.pivot(index='formula_jp',columns='source',values='cog_rate').dropna()
cliff_pivot.columns.name = None
if '東洋医学雑誌' in cliff_pivot.columns and 'PubMed Kampo' in cliff_pivot.columns:
    cliff_pivot['diff'] = cliff_pivot['東洋医学雑誌'] - cliff_pivot['PubMed Kampo']
    top3 = cliff_pivot.sort_values('diff', ascending=False).head(3)
    print('  言語間認知格差トップ3:')
    for idx, row in top3.iterrows():
        print(f'    {idx}: JP={row["東洋医学雑誌"]:.1%} → PM={row["PubMed Kampo"]:.1%}  (Δ={row["diff"]:.1%})')

# ═══════════════════════════════════════════════════════════════
# PART 3-3: 図の生成
# ═══════════════════════════════════════════════════════════════
print()
print('='*60)
print('PART 3-3: 図の生成')
print('='*60)

df_plot = df[df['has_abstract']&df['year_bin'].notna()].copy()
df_plot['year_bin'] = df_plot['year_bin'].astype(int)
DECADE_LABELS = {1950:'1950s',1960:'1960s',1970:'1970s',1980:'1980s',
                 1990:'1990s',2000:'2000s',2010:'2010s',2020:'2020s'}

# ── Fig_final_1: 認知ギャップ時系列（kampo vs pubmed_kampo）──
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

for ax, src, label, clr in [
    (axes[0], 'kampo',       '東洋医学雑誌\n(Japanese)',  CB['blue']),
    (axes[1], 'pubmed_kampo','PubMed Kampo\n(English)',   CB['red']),
]:
    sub = df_plot[df_plot['source']==src]
    g = sub.groupby('year_bin').agg(
        n=('id','count'),
        n_cog=('cog_conservative','sum'),
        n_formula=('formula_in_text','sum'),
    ).reset_index()
    g = g[g['n']>=3]
    g['cog_rate']     = g['n_cog']/g['n']
    g['formula_rate'] = g['n_formula']/g['n']

    # Q3/(Q1+Q3) per decade
    gaps = []
    for yb, grp in sub.groupby('year_bin'):
        q1 = (grp['quad_conservative']=='Q1_both').sum()
        q3 = (grp['quad_conservative']=='Q3_formula_only').sum()
        gaps.append({'year_bin':yb,'gap':q3/(q1+q3) if q1+q3>0 else float('nan')})
    gap_df = pd.DataFrame(gaps).set_index('year_bin')

    bins = sorted(g['year_bin'].unique())
    x = range(len(bins))
    xlabels = [DECADE_LABELS.get(b, str(b)) for b in bins]

    ax.bar(x, g.set_index('year_bin').loc[bins,'formula_rate'],
           color=CB['gray'], alpha=0.4, label='Formula rate', zorder=1)
    ax.plot(x, g.set_index('year_bin').loc[bins,'cog_rate'],
            'o-', color=clr, lw=2, ms=5, label='Cognition rate (Conservative)', zorder=3)
    # gap line
    gap_vals = [gap_df.loc[b,'gap'] if b in gap_df.index else float('nan') for b in bins]
    ax2 = ax.twinx()
    ax2.plot(x, gap_vals, 's--', color=CB['orange'], lw=1.5, ms=4,
             label='Q3/(Q1+Q3)', alpha=0.8)
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel('Q3/(Q1+Q3)', fontsize=8, color=CB['orange'])
    ax2.tick_params(axis='y', colors=CB['orange'], labelsize=7)
    ax2.spines['right'].set_visible(True)
    ax2.spines['top'].set_visible(False)

    ax.set_xticks(list(x))
    ax.set_xticklabels(xlabels, rotation=45, ha='right', fontsize=7)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('Rate', fontsize=9)
    ax.set_title(label, fontsize=10, fontweight='bold')
    ax.legend(loc='upper left', fontsize=7)

fig.suptitle('Cognitive Gap Analysis: Formula vs. Cognition Mention Rates by Decade',
             fontsize=11, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_final_1_gap_comparison.png')

# ── Fig_final_2: 言語間認知格差 ──
if not cliff_pivot.empty and 'diff' in cliff_pivot.columns:
    sorted_cliff = cliff_pivot.sort_values('diff', ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(10, 6))
    formulas = list(sorted_cliff.index)
    y = np.arange(len(formulas))
    jp_vals  = [sorted_cliff.loc[f,'東洋医学雑誌']  if '東洋医学雑誌'  in sorted_cliff.columns else 0 for f in formulas]
    pm_vals  = [sorted_cliff.loc[f,'PubMed Kampo'] if 'PubMed Kampo' in sorted_cliff.columns else 0 for f in formulas]
    diffs    = [sorted_cliff.loc[f,'diff'] for f in formulas]

    ax.barh(y, jp_vals,  0.35, color=CB['blue'], alpha=0.85, label='東洋医学雑誌')
    ax.barh(y-0.35, pm_vals, 0.35, color=CB['red'],  alpha=0.85, label='PubMed Kampo')
    for i, (jp, pm, d) in enumerate(zip(jp_vals, pm_vals, diffs)):
        if not (np.isnan(jp) or np.isnan(pm)):
            ax.annotate(f'Δ{d:.0%}', xy=(max(jp,pm)+0.01, y[i]-0.175),
                        fontsize=7, color=CB['orange'], va='center')

    ax.set_yticks(y - 0.175)
    ax.set_yticklabels(formulas, fontsize=8)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel('Cognition Mention Rate (articles with formula name, Conservative dict)', fontsize=9)
    ax.set_title('Cross-linguistic Cognition Gap: Cognition Co-mention Rate by Formula\n'
                 '(Japanese Journals vs. PubMed)', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)
    ax.axvline(0, color='black', lw=0.5)
    plt.tight_layout()
    save(fig, 'Fig_final_2_translation_cliff.png')

# ── Fig_final_3: 思考カテゴリ比較（kampo vs pubmed_kampo） ──
cat_order = ['sho_core','pathology','classical','examination','epistemological']
cat_labels = {'sho_core':'Shō core','pathology':'Qi-Blood-\nPathology',
              'classical':'Classical\nTexts','examination':'Physical\nExam',
              'epistemological':'Epistemological'}
fig, axes = plt.subplots(1, 2, figsize=(11, 5))
for ax, src, label, clr in [
    (axes[0],'kampo','東洋医学雑誌\n(Japanese)',CB['blue']),
    (axes[1],'pubmed_kampo','PubMed Kampo\n(English)',CB['red']),
]:
    sub = df[(df['source']==src)&df['has_abstract']]
    cat_counts = Counter()
    for _, row in sub.iterrows():
        matched = row.get('matched_conservative','')
        if not matched: continue
        for t in matched.split('|'):
            t = t.strip()
            if t in ALL_TERMS_V2: cat_counts[ALL_TERMS_V2[t]] += 1
    vals  = [cat_counts.get(c,0)/len(sub)*100 for c in cat_order]
    xlbls = [cat_labels[c] for c in cat_order]
    bars  = ax.bar(range(len(cat_order)), vals, color=[
        CB['blue'],CB['red'],CB['green'],CB['orange'],CB['purple']], alpha=0.8)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+0.3, f'{v:.1f}%',
                ha='center', va='bottom', fontsize=7)
    ax.set_xticks(range(len(cat_order)))
    ax.set_xticklabels(xlbls, fontsize=8, ha='center')
    ax.set_ylabel('% of articles with ≥1 cognition term', fontsize=8)
    ax.set_title(label, fontsize=10, fontweight='bold')
    ax.set_ylim(0, max(vals)*1.3+2 if vals else 10)
fig.suptitle('Cognition Category Rates by Source (Conservative Dictionary v2)',
             fontsize=10, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_final_3_category_comparison.png')

# ── Fig_final_S1: 感度分析ヒートマップ ──
pivot_data = []
for src in ['kampo','pubmed_kampo','acupuncture','pubmed_acupuncture','pubmed_pharma']:
    for d in ['liberal','conservative','strict']:
        row = sens_df[(sens_df['source']==src)&(sens_df['dict']==d)]
        if len(row): pivot_data.append({'source':src,'dict':d,'gap':row.iloc[0]['gap']*100})
piv_df = pd.DataFrame(pivot_data)
if not piv_df.empty:
    piv = piv_df.pivot(index='source',columns='dict',values='gap')
    piv = piv.reindex(columns=['liberal','conservative','strict'])
    fig, ax = plt.subplots(figsize=(7, 4))
    mask = piv.isna()
    sns.heatmap(piv, ax=ax, annot=True, fmt='.1f', cmap='RdYlBu_r',
                vmin=0, vmax=100, mask=mask,
                cbar_kws={'label':'Q3/(Q1+Q3) [%]'}, linewidths=0.4)
    ax.set_title('Sensitivity Analysis: Q3/(Q1+Q3) [%] by Dictionary Version',
                 fontsize=9, fontweight='bold')
    ax.set_xlabel('Dictionary version'); ax.set_ylabel('')
    plt.tight_layout()
    save(fig, 'Fig_final_S1_sensitivity.png')

# ── Fig_final_S2: 時系列 × 認知カテゴリ ヒートマップ ──
decades = sorted(df_plot['year_bin'].unique())
sub_k = df_plot[(df_plot['source']=='kampo')&df_plot['has_abstract']]
heat_data = {}
for cat in cat_order:
    vals = []
    for d in decades:
        g = sub_k[sub_k['year_bin']==d]
        if len(g) < 3: vals.append(float('nan')); continue
        cnt = sum(1 for _, row in g.iterrows()
                  if any(ALL_TERMS_V2.get(t)==cat
                         for t in (row.get('matched_conservative','') or '').split('|') if t))
        vals.append(cnt/len(g)*100)
    heat_data[cat_labels[cat]] = vals

heat_df = pd.DataFrame(heat_data, index=[DECADE_LABELS.get(d,str(d)) for d in decades]).T
fig, ax = plt.subplots(figsize=(10, 4))
sns.heatmap(heat_df, ax=ax, annot=True, fmt='.1f', cmap='Blues',
            linewidths=0.3, cbar_kws={'label':'% articles'})
ax.set_title('Cognition Category × Decade Heatmap (東洋医学雑誌, Conservative v2)',
             fontsize=9, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_final_S2_heatmap_temporal.png')

# ── Fig_final_S3: 4象限の年代別推移 ──
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
quad_colors = {'Q1_both':CB['blue'],'Q2_cognition_only':CB['green'],
               'Q3_formula_only':CB['red'],'Q4_neither':CB['gray']}
quad_labels_map = {'Q1_both':'Q1: Formula+Cognition','Q2_cognition_only':'Q2: Cognition only',
                   'Q3_formula_only':'Q3: Formula only (Gap)','Q4_neither':'Q4: Neither'}

for ax, src, label in [(axes[0],'kampo','東洋医学雑誌'),(axes[1],'pubmed_kampo','PubMed Kampo')]:
    sub = df_plot[df_plot['source']==src]
    decades_sub = sorted(sub['year_bin'].unique())
    stacks = {q: [] for q in ['Q1_both','Q2_cognition_only','Q3_formula_only','Q4_neither']}
    for d in decades_sub:
        g = sub[sub['year_bin']==d]
        tot = len(g)
        for q in stacks:
            stacks[q].append((g['quad_conservative']==q).sum()/tot*100 if tot else 0)
    x = range(len(decades_sub))
    xlbls = [DECADE_LABELS.get(d,str(d)) for d in decades_sub]
    bottom = np.zeros(len(decades_sub))
    for q in ['Q1_both','Q2_cognition_only','Q3_formula_only','Q4_neither']:
        vals = np.array(stacks[q])
        ax.bar(x, vals, bottom=bottom, color=quad_colors[q],
               label=quad_labels_map[q], alpha=0.85)
        bottom += vals
    ax.set_xticks(list(x)); ax.set_xticklabels(xlbls, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('% articles'); ax.set_ylim(0, 105)
    ax.set_title(label, fontsize=10, fontweight='bold')
    if ax == axes[0]: ax.legend(fontsize=7, loc='upper left')
fig.suptitle('Quadrant Distribution by Decade (Conservative v2)',
             fontsize=10, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_final_S3_quadrant_timeseries.png')

# ── Fig_final_S4: 処方 × 認知カテゴリ 共起ヒートマップ ──
top_formulas_jp = [f for f,_ in Counter(
    f for a in articles_jp if a['source']=='kampo'
    for f in (a.get('formulas') or [])
).most_common(15)]
heat_fc = pd.DataFrame(0, index=top_formulas_jp, columns=cat_order)
sub_k2 = df[df['source']=='kampo']
for _, row in sub_k2.iterrows():
    fms = (row.get('formulas_matched','') or '').split('|')
    cog = (row.get('matched_conservative','') or '').split('|')
    for fm in fms:
        if fm in top_formulas_jp:
            for t in cog:
                t = t.strip()
                if t in ALL_TERMS_V2:
                    heat_fc.loc[fm, ALL_TERMS_V2[t]] += 1
heat_fc_pct = heat_fc.div(heat_fc.sum(axis=1)+1, axis=0)*100
heat_fc_pct.columns = [cat_labels[c] for c in cat_order]
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(heat_fc_pct, ax=ax, annot=True, fmt='.0f', cmap='YlOrRd',
            linewidths=0.3, cbar_kws={'label':'% co-mentions'})
ax.set_title('Formula × Cognition Category Co-occurrence\n(東洋医学雑誌, Conservative v2)',
             fontsize=9, fontweight='bold')
plt.tight_layout()
save(fig, 'Fig_final_S4_cooccurrence.png')

# ═══════════════════════════════════════════════════════════════
# PART 4: DB再構築レポート + Phase3サマリー
# ═══════════════════════════════════════════════════════════════
print()
print('='*60)
print('PART 4: レポート出力')
print('='*60)

# Compare with Phase 2
# Phase 2 conservative: kampo Q3/(Q1+Q3)=55.3%  cog=33.5%
#                       pubmed Q3/(Q1+Q3)=97.0%  cog=3.7%
PHASE2_REF = {
    'kampo':        {'gap':0.553,'cog':0.335},
    'pubmed_kampo': {'gap':0.970,'cog':0.037},
}

db_report_lines = [
    '# DB再構築レポート（Phase 3）',
    '',
    f'> 生成日: 2026-03-29',
    '',
    '## 1. T5: 非日本論文の除外',
    '',
    f'| 指標 | 値 |',
    f'|------|---|',
    f'| 元DB総件数 | {len(articles_all):,} |',
    f'| 除外件数 | {len(excluded):,} |',
    f'| 残存件数 | {len(articles_jp):,} |',
    '',
    '### source別除外件数',
    '',
    '| source | 除外 | 元件数 |',
    '|--------|------|------|',
]
src_orig = Counter(a['source'] for a in articles_all)
for src in sorted(src_excl.keys()):
    db_report_lines.append(f'| {src} | {src_excl[src]} | {src_orig[src]} |')

db_report_lines += [
    '',
    '### 国別除外内訳',
    '',
    '| 国 | 件数 |',
    '|----|------|',
]
for ctry, cnt in sorted(country_excl.items(), key=lambda x:-x[1]):
    db_report_lines.append(f'| {ctry} | {cnt} |')

db_report_lines += [
    '',
    '## 2. 新DB件数（integrated_db_japan.json）',
    '',
    '| source | 件数 |',
    '|--------|------|',
]
src_new = Counter(a['source'] for a in articles_jp)
for src, cnt in sorted(src_new.items(), key=lambda x:-x[1]):
    db_report_lines.append(f'| {src} | {cnt} |')
db_report_lines += [
    f'| **合計** | **{len(articles_jp):,}** |',
    '',
    f'抄録あり率: {stats_new["with_abstract"]/len(articles_jp):.1%}',
]

with open(os.path.join(OUTPUT,'db_reconstruction_report.md'),'w',encoding='utf-8') as f:
    f.write('\n'.join(db_report_lines))
print(f'  Written: db_reconstruction_report.md')

# Phase3 report
k_new  = sens_df[(sens_df['source']=='kampo')&(sens_df['dict']=='conservative')].iloc[0]
pm_new = sens_df[(sens_df['source']=='pubmed_kampo')&(sens_df['dict']=='conservative')].iloc[0]

p3_lines = [
    '# Phase 3 分析レポート',
    '',
    f'> 生成日: 2026-03-29',
    f'> 辞書: Conservative v2（T1–T4適用）',
    f'> DB: integrated_db_japan.json（T5 非日本除外後）',
    '',
    '## 1. 主要指標',
    '',
    '### Conservative v2 @ Japan-only DB',
    '',
    '| | 東洋医学雑誌 (kampo) | PubMed Kampo |',
    '|---|---|---|',
    f'| n（抄録あり） | {int(k_new["n_abs"])} | {int(pm_new["n_abs"])} |',
    f'| 認知言及率 | {k_new["cog_rate"]:.1%} | {pm_new["cog_rate"]:.1%} |',
    f'| Q3/(Q1+Q3) | {k_new["gap"]:.1%} | {pm_new["gap"]:.1%} |',
    f'| Q1 | {int(k_new["Q1"])} | {int(pm_new["Q1"])} |',
    f'| Q3 | {int(k_new["Q3"])} | {int(pm_new["Q3"])} |',
    '',
    f'**Fisher OR = {oddsratio:.2f} (95% CI: {ci_low:.2f}–{ci_high:.2f}), p = {pval:.2e}**',
    '',
    '## 2. Phase 2との差分',
    '',
    '| 指標 | Phase 2 | Phase 3 | Δ |',
    '|------|---------|---------|---|',
    f'| kampo Q3/(Q1+Q3) | {PHASE2_REF["kampo"]["gap"]:.1%} | {k_new["gap"]:.1%} | {k_new["gap"]-PHASE2_REF["kampo"]["gap"]:+.1%} |',
    f'| kampo cog rate | {PHASE2_REF["kampo"]["cog"]:.1%} | {k_new["cog_rate"]:.1%} | {k_new["cog_rate"]-PHASE2_REF["kampo"]["cog"]:+.1%} |',
    f'| pubmed Q3/(Q1+Q3) | {PHASE2_REF["pubmed_kampo"]["gap"]:.1%} | {pm_new["gap"]:.1%} | {pm_new["gap"]-PHASE2_REF["pubmed_kampo"]["gap"]:+.1%} |',
    f'| pubmed cog rate | {PHASE2_REF["pubmed_kampo"]["cog"]:.1%} | {pm_new["cog_rate"]:.1%} | {pm_new["cog_rate"]-PHASE2_REF["pubmed_kampo"]["cog"]:+.1%} |',
    '',
    '## 3. 辞書v2の効果',
    '',
    f'- T1 追加語マッチ（上位3）: ' + ', '.join(f'{t}={c}件' for t,c in t1_hits.most_common(3)),
    f'- T3 文字化け（〓血）: {garbled_count}件',
    f'- T4 随証共起ルールで再分類: {zuisho_reclassified}件',
    '',
    '## 4. 感度分析（3辞書 × Conservative DB）',
    '',
    '| source | Liberal | Conservative | Strict |',
    '|--------|---------|-------------|--------|',
]
for src in ['kampo','pubmed_kampo']:
    vals = []
    for d in ['liberal','conservative','strict']:
        row = sens_df[(sens_df['source']==src)&(sens_df['dict']==d)]
        vals.append(f'{row.iloc[0]["gap"]:.1%}' if len(row) else 'n/a')
    p3_lines.append(f'| {src} | ' + ' | '.join(vals) + ' |')

p3_lines += [
    '',
    '## 5. 言語間認知格差',
    '',
    '| 処方 | 東洋医学雑誌 | PubMed | Δ |',
    '|------|------------|--------|---|',
]
if not cliff_pivot.empty and 'diff' in cliff_pivot.columns:
    for idx, row in cliff_pivot.sort_values('diff',ascending=False).head(8).iterrows():
        jp = row.get('東洋医学雑誌', float('nan'))
        pm = row.get('PubMed Kampo', float('nan'))
        diff = row.get('diff', float('nan'))
        if not (np.isnan(jp) or np.isnan(pm)):
            p3_lines.append(f'| {idx} | {jp:.1%} | {pm:.1%} | {diff:+.1%} |')

with open(os.path.join(OUTPUT,'phase3_report.md'),'w',encoding='utf-8') as f:
    f.write('\n'.join(p3_lines))
print(f'  Written: phase3_report.md')

# Final file listing
print()
print('=== 出力ファイル ===')
for fn in sorted(os.listdir(OUTPUT)):
    sz = os.path.getsize(os.path.join(OUTPUT,fn))
    print(f'  {fn} ({sz//1024} KB)')
