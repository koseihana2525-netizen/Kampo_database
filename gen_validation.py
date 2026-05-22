# -*- coding: utf-8 -*-
"""
gen_validation.py
サンプリング検証 + 小川先生用資料の生成
"""

import json, sys, random, importlib.util, os, shutil, pickle
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\kosei\Desktop\18_東洋医学雑誌'
OUTPUT = os.path.join(BASE, 'analysis_output', 'validation')
os.makedirs(OUTPUT, exist_ok=True)

# ─── 辞書ロード ───────────────────────────────────────────────────
spec = importlib.util.spec_from_file_location('dictionaries',
        os.path.join(BASE, 'dictionaries.py'))
dmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmod)

PTERM_CAT = {
    '八綱弁証':'pathology','気血津液弁証':'pathology',
    '臓腑弁証':'pathology','六経弁証':'classical',
}
ALL_TERMS = {}
for top_cat, sub in dmod.PATTERN_TERMS.items():
    cat = PTERM_CAT.get(top_cat, 'pathology')
    for subcat, tlist in sub.items():
        if isinstance(tlist, list):
            for t in tlist:
                ALL_TERMS[t] = cat
for t in dmod.ABDOMINAL_TERMS:
    ALL_TERMS[t] = 'examination'

extra_terms = {
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
for t, c in extra_terms.items():
    if t not in ALL_TERMS:
        ALL_TERMS[t] = c

FP_HARD = {'出血','発熱','浮腫','動悸'}

def filter_conservative(text_lower):
    hits = []
    for term, cat in ALL_TERMS.items():
        if term in FP_HARD or term == '冷え':
            continue
        if term in text_lower:
            hits.append((term, cat))
    return hits

formula_ja = []
for num, info in dmod.FORMULAS.items():
    formula_ja.append(info['name'])
    for alias in info.get('aliases', []):
        formula_ja.append(alias)
for key, info in dmod.EXTRA_FORMULAS.items():
    formula_ja.append(info['name'])
    for alias in info.get('aliases', []):
        formula_ja.append(alias)

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
]
for i in range(1, 154):
    FORMULA_ROMAJI.append(f'tj-{i:03d}')
    FORMULA_ROMAJI.append(f'tsumura no. {i}')
    FORMULA_ROMAJI.append(f'tsumura {i}')

formula_ja = sorted(set(formula_ja), key=len, reverse=True)
formula_en = sorted(set(FORMULA_ROMAJI), key=len, reverse=True)


def match_formulas(text, lang):
    found = []
    remaining = text
    if lang == 'ja':
        for name in formula_ja:
            if name in remaining:
                found.append(name)
                remaining = remaining.replace(name, '\x00' * len(name))
    else:
        text_l = text.lower()
        for name in formula_en:
            if name in text_l:
                found.append(name)
    return found


# ─── DB ロード ────────────────────────────────────────────────────
with open(os.path.join(BASE, 'data', 'integrated_db.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)
articles = data['articles']

# ─── 分類 ─────────────────────────────────────────────────────────
groups = {'kampo_Q1': [], 'kampo_Q3': [], 'pubmed_Q1': [], 'pubmed_Q3': []}
for a in articles:
    src = a['source']
    if src not in ('kampo', 'pubmed_kampo'):
        continue
    ab = a.get('abstract', '') or ''
    title = a.get('title', '') or ''
    if not (title + ab).strip():
        continue
    combined = (title + ' ' + ab).lower()
    f_hits = match_formulas(title + ' ' + ab, a['lang'])
    if not f_hits:
        continue
    c_hits = filter_conservative(combined)
    quad = 'Q1' if c_hits else 'Q3'
    k = ('kampo' if src == 'kampo' else 'pubmed') + '_' + quad
    groups[k].append({'article': a, 'formulas': f_hits, 'cognition': c_hits})

for k, v in groups.items():
    print(f'{k}: {len(v)}件')

# ─── サンプリング ──────────────────────────────────────────────────
random.seed(42)
group_meta = [
    ('A', 'kampo_Q1',   '東洋医学雑誌',  'Q1（処方＋思考）'),
    ('B', 'kampo_Q3',   '東洋医学雑誌',  'Q3（処方のみ・認知ギャップ）'),
    ('C', 'pubmed_Q1',  'PubMed Kampo', 'Q1（処方＋思考）'),
    ('D', 'pubmed_Q3',  'PubMed Kampo', 'Q3（処方のみ・認知ギャップ）'),
]
samples = {}
for gname, gkey, src_label, quad_label in group_meta:
    pool = groups[gkey]
    n = min(10, len(pool))
    selected = random.sample(pool, n)
    samples[gname] = (src_label, quad_label, selected)
    print(f'Group {gname} ({src_label}/{quad_label}): {n}件')


# ─── Part 1: sampling_validation.md ─────────────────────────────
lines = []
lines.append('# サンプリング検証レポート')
lines.append('')
lines.append('> **目的**: Conservative辞書による4象限分類の妥当性を人間の目で確認する。')
lines.append('> **方法**: `random.seed(42)` による再現可能な無作為抽出（各グループ10件）。')
lines.append('> **辞書バージョン**: Conservative（FP_HARD除外: 出血・発熱・浮腫・動悸・冷え単独）')
lines.append('')
lines.append('**検証の観点**:')
lines.append('- Q1記事: 処方名と思考概念のマッチは文脈的に妥当か？（偽陽性でないか）')
lines.append('- Q3記事: 思考概念が本当にないか？（辞書の取りこぼしでないか）')
lines.append('')
lines.append('---')
lines.append('')

group_labels = {
    'A': '東洋医学雑誌・Q1（処方＋思考）— 真のポジティブ候補',
    'B': '東洋医学雑誌・Q3（処方のみ）— 認知ギャップ候補',
    'C': 'PubMed Kampo・Q1（処方＋思考）— 真のポジティブ候補',
    'D': 'PubMed Kampo・Q3（処方のみ）— 認知ギャップ候補',
}

for gname, gkey, src_label, quad_label in group_meta:
    src_l, quad_l, selected = samples[gname]
    pool_size = len(groups[gkey])
    lines.append(f'## グループ {gname}: {group_labels[gname]}')
    lines.append('')
    lines.append(f'母集団: {pool_size}件 → ランダムサンプル: {len(selected)}件')
    lines.append('')

    for i, item in enumerate(selected, 1):
        a = item['article']
        formulas = item['formulas'][:8]
        cognition = item['cognition'][:10]
        ab = a.get('abstract', '') or ''
        title = a.get('title', '') or ''
        year = a.get('year', '')
        aid = a.get('id', '')
        link = a.get('link', '')

        lines.append(f'---')
        lines.append(f'### [{gname}-{i:02d}] {src_label} — {quad_l[:15]}')
        lines.append(f'- **ID**: `{aid}`')
        lines.append(f'- **Year**: {year}')
        if link:
            lines.append(f'- **Link**: {link}')
        lines.append(f'- **Title**: {title}')
        lines.append(f'- **マッチした処方名** ({len(item["formulas"])}語): '
                     + ', '.join(f'`{f}`' for f in formulas)
                     + ('…' if len(item['formulas']) > 8 else ''))
        if cognition:
            # deduplicate by term
            seen = {}
            for t, c in cognition:
                if t not in seen:
                    seen[t] = c
            lines.append(f'- **マッチした思考概念** ({len(item["cognition"])}語): '
                         + ', '.join(f'`{t}`（{c}）' for t, c in list(seen.items())[:8])
                         + ('…' if len(seen) > 8 else ''))
        else:
            lines.append(f'- **マッチした思考概念**: なし')

        lines.append(f'- **抄録**:')
        if ab:
            # 抄録全文を引用形式で
            ab_disp = ab[:1200] + ('…（以下省略）' if len(ab) > 1200 else '')
            for para in ab_disp.split('\n'):
                lines.append(f'  > {para}' if para.strip() else '  >')
        else:
            lines.append('  > （抄録なし）')
        lines.append('')
        lines.append('**検証チェック**:')
        if cognition:
            lines.append('- [ ] 思考概念のマッチは文脈的に妥当か（漢方の思考を反映しているか）')
            lines.append('- [ ] 偽陽性語はないか')
        else:
            lines.append('- [ ] 思考概念が本当に言及されていないか確認')
            lines.append('- [ ] 辞書で取りこぼしている重要な概念はないか')
        lines.append('')

    lines.append('')

lines.append('---')
lines.append('## 検証サマリー（記入欄）')
lines.append('')
lines.append('| グループ | 確認件数 | 妥当と判断 | 偽陽性 | 偽陰性 | コメント |')
lines.append('|---------|---------|----------|--------|--------|---------|')
for gname, _, src_label, quad_label in group_meta:
    n = len(samples[gname][2])
    lines.append(f'| {gname}: {src_label}/{quad_label[:12]} | {n} | | | | |')
lines.append('')
lines.append('**特記事項**:')
lines.append('')
lines.append('（ここに手書きメモ）')

out = os.path.join(OUTPUT, 'sampling_validation.md')
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'Written: {out}')


# ─── Part 2-1: ogawa_sensei_briefing.md ──────────────────────────
briefing = """\
# 漢方文献の「認知ギャップ」分析：研究概要と辞書レビューのお願い

> **作成日**: 2026-03-29
> **宛先**: 小川恵子先生
> **件名**: 研究への参加・辞書レビューのご相談

---

## 1. 研究の目的

漢方関連の学術文献（約11,800件）を対象にテキストマイニングを行い、
**「漢方薬の処方名への言及」と「漢方医学の思考概念（証・気血水・腹診等）への言及」が
どの程度乖離しているか**を定量化しました。

仮説：現代の漢方論文は処方名（方剤）には言及するが、
漢方独自の診断・思考枠組み（証論治、気血水、腹診など）への言及が
系統的に失われているのではないか。

---

## 2. データソース

| ソース | 件数 | 期間 | 言語 |
|--------|------|------|------|
| 日本東洋医学雑誌（J-STAGE） | 2,003 | 1982–2025 | 日本語 |
| 全日本鍼灸学会雑誌（J-STAGE） | 650 | 2007–2025 | 日本語 |
| PubMed（漢方・鍼灸・薬理研究） | 9,193 | 1954–2026 | 英語 |
| **合計** | **11,846** | | |

---

## 3. 主要な発見

### 3-1. 認知ギャップ比率（Conservative辞書）

処方名に言及する論文のうち、漢方の思考概念に言及しない割合：

| ソース | Q3/(Q1+Q3) | 件数（Q1+Q3） |
|--------|-----------|-------------|
| **東洋医学雑誌（日本語）** | **56.3%** | 1,133件 |
| **PubMed漢方論文（英語）** | **97.0%** | 1,592件 |

**Odds Ratio = 25.7（95% CI: 18.8–35.2）**

→ PubMed漢方論文では処方言及論文の97%が漢方思考に一切言及していない。
→ 東洋医学雑誌でも56%が思考なし（改善傾向あり：2000年代以降で低下）。

### 3-2. 翻訳の断崖（Translation Cliff）

同一処方名の日英比較（処方言及論文中の思考概念共起率）：

全15処方で思考概念の共起率が日本語→英語で25–56ポイント低下。
唯一 **「blood stasis（瘀血）」** のみが英語文献で部分的に生存（10–20%程度）。

### 3-3. Uneda（2024）との三角測量

> Uneda et al. (2024) の調査：現役漢方処方医の48.3%が
> 「証（しょう）をルーティンに使用しない」と回答。

本分析の東洋医学雑誌データ（56.3%が思考に言及しない）と独立に近似し、
**臨床実態の文献的裏付け**として機能します。

---

## 4. 論文の位置づけ

**投稿先（第一候補）**: BMJ Open または JGFM
**論文種別**: Original Research（bibliometric analysis with systematic search elements）
**duagnosis論文との関係**: FMCH投稿中のduagnosis概念論文が提起した
「modality（処方）≠ cognition（思考）」の区別を、
10,000件規模のテキストデータで実証するcompanion論文として位置づけます。

---

## 5. 小川先生へのお願い

### 5-1. 認知辞書のレビュー（最優先）

別添の「認知辞書レビューシート」をご確認ください。
本研究で「漢方の思考体系」の指標として使用した辞書（約140語）について、
以下の観点からご意見をいただけますと幸いです：

1. **不足している重要な概念**（辞書に含まれていないが本来カウントすべき語）
2. **除外すべき語**（西洋医学でも使われる一般語、偽陽性のリスクがある語）
3. **分類の妥当性**（5カテゴリへの割り当てが適切か）

### 5-2. 共著者としてのご参加（ご検討ください）

辞書の専門家レビュー（Clinical expert validation）はMethodsの核心的要件です。
下記の貢献を想定しています：
- 認知辞書の内容妥当性のご確認（Contribution: Methods/Results）
- Discussionへの臨床的解釈のご寄与（「証の現代的意義」等）
- 日本東洋医学会の観点からのコメント

### 5-3. 投稿先についてのご相談

BMJ OpenとJGFMのどちらが適切かについて、先生のご見解をお聞きしたいと思っています。

---

## 6. 次のステップ（提案）

- [ ] 辞書レビューシートへのご記入（2週間以内にいただけると幸いです）
- [ ] オンライン打ち合わせの日程調整（30分程度）
- [ ] 論文Draftのご共有（Methods完成後）

ご多忙のところ恐縮ですが、何卒よろしくお願いいたします。

---

*添付資料:*
- *Fig_P2_3: 認知ギャップ比率の比較（東洋医学雑誌 vs PubMed）*
- *Fig_P2_7: 翻訳の断崖（処方別思考概念共起率の日英比較）*
- *cognition_dictionary_review.md: 認知辞書レビューシート*
- *sampling_validation.md: サンプル論文40件（辞書検証用）*
"""

out2 = os.path.join(OUTPUT, 'ogawa_sensei_briefing.md')
with open(out2, 'w', encoding='utf-8') as f:
    f.write(briefing)
print(f'Written: {out2}')


# ─── Part 2-2: cognition_dictionary_review.md ────────────────────
# 実際の辞書から全語を抽出してカテゴリ別に整理
cat_terms = {'sho_core': [], 'pathology': [], 'classical': [],
             'examination': [], 'epistemological': []}
for term, cat in ALL_TERMS.items():
    cat_terms[cat].append(term)
# sort each
for c in cat_terms:
    cat_terms[c] = sorted(cat_terms[c], key=lambda x: (0 if '\u4e00' <= x[0] <= '\u9fff' else 1, x))

def split_jpen(term_list):
    """日本語語と英語語に分割"""
    ja = [t for t in term_list if any('\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u9fff' for ch in t)]
    en = [t for t in term_list if t not in ja]
    return ja, en

review_lines = []
review_lines.append('# 認知辞書レビューシート')
review_lines.append('')
review_lines.append('> **作成日**: 2026-03-29')
review_lines.append('> **バージョン**: Conservative辞書（FP_HARD除外済み）')
review_lines.append('')
review_lines.append('本辞書は漢方関連文献の抄録に対して辞書マッチングを行い、')
review_lines.append('「漢方医学の思考体系に基づく概念がテキストに出現するか」を検出するために')
review_lines.append('構築しました。処方名とは独立に、著者が漢方の思考枠組みで論じているか')
review_lines.append('を判定することを目的としています。')
review_lines.append('')
review_lines.append('## レビューの観点')
review_lines.append('')
review_lines.append('各語について以下の欄に記入してください：')
review_lines.append('- **✓** = 適切（漢方の思考を反映、偽陽性リスク低）')
review_lines.append('- **✗** = 除外すべき（西洋医学でも使われる一般語、または不適切）')
review_lines.append('- **?** = 要議論（文脈依存、判断が難しい）')
review_lines.append('- **コメント欄**: 修正案、追加すべき同義語など')
review_lines.append('')
review_lines.append('---')
review_lines.append('')

cat_info = {
    'sho_core': ('カテゴリ1: 証（shō）の核心概念', '''\
証論治の核心を表す概念です。「証」単独は「認証」「検証」等の誤マッチを避けるため
使用せず、文脈を限定した複合語パターンのみを採用しています。'''),
    'pathology': ('カテゴリ2: 気血水・陰陽・虚実・病理概念', '''\
漢方医学の病態を記述する概念群です。「冷え」単独は一般症状語としても使われるため
Conservative辞書では除外しています（「冷え症」「冷え性」は残存）。'''),
    'classical': ('カテゴリ3: 古典・六病位', '''\
傷寒論・金匱要略等の古典文献名および六経病位の概念です。'''),
    'examination': ('カテゴリ4: 診察法（腹診・脈診・舌診）', '''\
漢方独自の診察法に関する語群です。腹診（fukushin）は英語文献でも使用されます。'''),
    'epistemological': ('カテゴリ5: 認識論的概念', '''\
漢方医学の世界観・哲学を反映する概念です。'''),
}

for cat, (title, desc) in cat_info.items():
    terms = cat_terms[cat]
    ja_terms, en_terms = split_jpen(terms)

    review_lines.append(f'## {title}')
    review_lines.append('')
    review_lines.append(desc)
    review_lines.append('')
    review_lines.append(f'**該当語数**: 日本語 {len(ja_terms)}語 + 英語 {len(en_terms)}語')
    review_lines.append('')

    if ja_terms:
        review_lines.append('### 日本語キーワード')
        review_lines.append('')
        review_lines.append('| No | 語 | 判定（✓/✗/?） | コメント |')
        review_lines.append('|----|----|--------------|---------|')
        for i, t in enumerate(ja_terms, 1):
            review_lines.append(f'| {i} | {t} | | |')
        review_lines.append('')

    if en_terms:
        review_lines.append('### 英語キーワード')
        review_lines.append('')
        review_lines.append('| No | 語 | 判定（✓/✗/?） | コメント |')
        review_lines.append('|----|----|--------------|---------|')
        for i, t in enumerate(en_terms, 1):
            review_lines.append(f'| {i} | `{t}` | | |')
        review_lines.append('')

review_lines.append('---')
review_lines.append('')
review_lines.append('## Conservative辞書で除外済みの語（偽陽性リスク）')
review_lines.append('')
review_lines.append('以下の語はLiberal辞書には含まれていますが、Conservative辞書では除外しています。')
review_lines.append('復活させるべきかについてもご意見をください。')
review_lines.append('')
review_lines.append('| 語 | 除外理由 | 復活すべき？（✓/✗/?） | コメント |')
review_lines.append('|----|---------|---------------------|---------|')
fp_info = [
    ('冷え（単独）', '「冷え込み」「冷え性」以外の文脈でも使われる一般症状語'),
    ('出血', '西洋医学の一般語として頻出'),
    ('発熱', '西洋医学の一般語として頻出'),
    ('浮腫', '西洋医学の一般語として頻出'),
    ('動悸', '西洋医学の一般語として頻出'),
    ('yin deficiency', 'Strict辞書では除外（Conservative辞書には含む）'),
    ('yang deficiency', 'Strict辞書では除外（Conservative辞書には含む）'),
    ('yin-yang', 'Strict辞書では除外（Conservative辞書には含む）'),
]
for term, reason in fp_info:
    review_lines.append(f'| `{term}` | {reason} | | |')

review_lines.append('')
review_lines.append('---')
review_lines.append('')
review_lines.append('## 追加提案欄')
review_lines.append('')
review_lines.append('辞書に含まれていないが追加すべき概念があればご記入ください：')
review_lines.append('')
review_lines.append('| 提案語（日本語） | 提案語（英語） | 想定カテゴリ | 追加の理由 |')
review_lines.append('|---------------|-------------|------------|---------|')
for _ in range(8):
    review_lines.append('| | | | |')
review_lines.append('')
review_lines.append('---')
review_lines.append('')
review_lines.append('## 総評欄')
review_lines.append('')
review_lines.append('（辞書全体の妥当性、感度・特異度のバランスについてご意見をお聞かせください）')
review_lines.append('')

# 辞書統計をフッターに
review_lines.append('---')
review_lines.append('## 辞書統計（参考）')
review_lines.append('')
review_lines.append(f'| カテゴリ | 日本語語数 | 英語語数 | 合計 |')
review_lines.append('|---------|----------|---------|------|')
total_ja = total_en = 0
for cat, (title, _) in cat_info.items():
    ja, en = split_jpen(cat_terms[cat])
    review_lines.append(f'| {title[5:]} | {len(ja)} | {len(en)} | {len(ja)+len(en)} |')
    total_ja += len(ja); total_en += len(en)
review_lines.append(f'| **合計** | **{total_ja}** | **{total_en}** | **{total_ja+total_en}** |')

out3 = os.path.join(OUTPUT, 'cognition_dictionary_review.md')
with open(out3, 'w', encoding='utf-8') as f:
    f.write('\n'.join(review_lines))
print(f'Written: {out3}')


# ─── Part 2-3: キー図コピー ────────────────────────────────────────
P2_DIR = os.path.join(BASE, 'analysis_output', 'phase2')
for fig in ['Fig_P2_3_gap_comparison.png', 'Fig_P2_7_translation_cliff.png']:
    src = os.path.join(P2_DIR, fig)
    dst = os.path.join(OUTPUT, fig)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f'Copied: {fig}')
    else:
        print(f'Not found: {fig}')

print('\n=== 完了 ===')
print(f'出力先: {OUTPUT}')
for f in sorted(os.listdir(OUTPUT)):
    size = os.path.getsize(os.path.join(OUTPUT, f))
    print(f'  {f} ({size//1024} KB)')
