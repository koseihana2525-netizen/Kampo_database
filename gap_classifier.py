# -*- coding: utf-8 -*-
"""
gap_classifier.py - 「処方名への言及」×「漢方思考概念への言及」の4象限分類（単一の実装）

認知ギャップ = Q3 / (Q1 + Q3)
  Q1: 処方名あり・思考概念あり   Q2: 処方名なし・思考概念あり
  Q3: 処方名あり・思考概念なし   Q4: どちらもなし

variant
  "legacy"   phase3_analysis.py の処理の再現（投稿版 v3 の値を作った処理）。比較・感度分析用。
  "primary"  主解析。legacy からの修正点は次の4つ。
    1. 英語の処方名検出を広げた。空白・ハイフン・アポストロフィを除いて照合する（Sho-saiko-to, Oren-gedoku-to, Ninjin'yoei-to など）。
       全方剤（ツムラ128＋追加141）の読みから、英語論文の綴り（長音を畳んだ shosaikoto と、残した shousaikotou）を作って照合する。
       0埋めなしの TJ コード（TJ-54）も検出する。
       legacy は「ハイフン→空白」に置換した後、ハイフンなしの名前で照合していたため、ハイフン付きの表記を検出できなかった。
    2. 英語の思考概念語のうち、ハイフン語（yin-yang, kyo-jitsu, ho-sho-sotai, sho-based, mind-body unity）と
       末尾空白語（'sho ', 'hie '）が検出できなかった・偶然に当たっていた問題を修正した。語境界で照合する。
       末尾空白語は、ハイフンで他の語につながっている場合（Sho-saiko-to の Sho は小柴胡湯の「小」）には数えない。
       これを数えると、ハイフン付きの処方名を検出できるようにした分だけ、偽の「証」言及（Q1）が生じる。
    3. ラテン文字の発音記号を畳み込む（shō → sho）。日本語（濁点など）には触れない。
    4. 'running piglet'（奔豚の英訳。処方名ではない）を処方名リストから除いた。思考概念語としては残る。
  辞書B（思考概念語）の語の追加・削除は行っていない。

標準ライブラリ + dictionaries.py + romaji.py だけで動く（テストとCIで使うため）。
"""

import re
import unicodedata

import dictionaries as _dic
from romaji import yomi_to_romaji_variants

VARIANTS = ("legacy", "primary", "primary_ext")
CATEGORIES = ("sho_core", "pathology", "classical", "examination", "epistemological")

# ── 辞書B（漢方思考概念） ───────────────────────────
# phase3_analysis.py（投稿版 v3）の定義を、そのまま移したもの。
PTERM_CAT = {
    '八綱弁証': 'pathology',
    '気血津液弁証': 'pathology',
    '臓腑弁証': 'pathology',
    '六経弁証': 'classical',
}

BASE_EXTRA = {
    '随証': 'sho_core',
    '弁証': 'sho_core',
    '方証相対': 'sho_core',
    '証に基づ': 'sho_core',
    '証の変化': 'sho_core',
    '証を決定': 'sho_core',
    '気血水': 'pathology',
    'お血': 'pathology',
    '血瘀': 'pathology',
    '冷え症': 'pathology',
    '冷え性': 'pathology',
    '冷え': 'pathology',
    'のぼせ': 'pathology',
    '気鬱': 'pathology',
    '気うつ': 'pathology',
    '未病': 'epistemological',
    '養生': 'epistemological',
    '心身一如': 'epistemological',
    '同病異治': 'epistemological',
    '異病同治': 'epistemological',
    '君臣佐使': 'epistemological',
    '傷寒論': 'classical',
    '金匱要略': 'classical',
    '温病': 'classical',
    'sho ': 'sho_core',
    'sho-based': 'sho_core',
    'sho pattern': 'sho_core',
    'pattern diagnosis': 'sho_core',
    'pattern identification': 'sho_core',
    'pattern differentiation': 'sho_core',
    'ho-sho-sotai': 'sho_core',
    'qi deficiency': 'pathology',
    'blood deficiency': 'pathology',
    'qi stagnation': 'pathology',
    'blood stasis': 'pathology',
    'blood stagnation': 'pathology',
    'oketsu': 'pathology',
    'water toxin': 'pathology',
    'yin deficiency': 'pathology',
    'yang deficiency': 'pathology',
    'yin-yang': 'pathology',
    'cold sensitivity': 'pathology',
    'hie ': 'pathology',
    'deficiency pattern': 'pathology',
    'excess pattern': 'pathology',
    'kyo-jitsu': 'pathology',
    'spleen deficiency': 'pathology',
    'kidney deficiency': 'pathology',
    'liver qi': 'pathology',
    'taiyang': 'classical',
    'shaoyang': 'classical',
    'yangming': 'classical',
    'taiyin': 'classical',
    'shaoyin': 'classical',
    'jueyin': 'classical',
    'six stages': 'classical',
    'shanghan': 'classical',
    'shang han': 'classical',
    'jingui': 'classical',
    'fukushin': 'examination',
    'pulse diagnosis': 'examination',
    'tongue diagnosis': 'examination',
    'hypochondriac fullness': 'examination',
    'abdominal diagnosis': 'examination',
    'abdominal palpation': 'examination',
    'mibyou': 'epistemological',
    'mibyo': 'epistemological',
    'mind-body unity': 'epistemological',
    'same disease different treatment': 'epistemological',
}

T1_ADDITIONS = {
    '奔豚': 'classical',
    '奔豚気': 'classical',
    '奔豚病': 'classical',
    '煩躁': 'classical',
    'hontonki': 'classical',
    'honton': 'classical',
    'running piglet': 'classical',
    '転方': 'sho_core',
    'switching formula': 'sho_core',
    '尿自利': 'examination',
    '小便自利': 'examination',
    '小便不利': 'examination',
    '尿不利': 'examination',
    'urinary dysfunction': 'examination',
    '瞑眩': 'epistemological',
    'menken': 'epistemological',
    'healing crisis': 'epistemological',
    'heat syndrome': 'pathology',
    '脾虚': 'pathology',
    '腎虚': 'pathology',
    '肝鬱': 'pathology',
    'liver stagnation': 'pathology',
}

FP_HARD = [
    '出血', '動悸', '浮腫', '発熱',
]   # Conservative 版で除く語

STRICT_EXTRA = [
    'yang deficiency', 'yang deficiency ', 'yin deficiency', 'yin deficiency ', 'yin-yang', 'のぼせ',
    '冷え', '冷え性', '冷え症', '微熱', '悪寒', '潮熱', '陰虚', '陽虚',
]   # Strict 版で、FP_HARD に加えて除く語

OKETSU_VARIANTS = [
    '瘀血', 'お血', 'おけつ', 'オケツ', '〓血',
]   # 瘀血の表記ゆれ（'瘀血' に統一）

# 英語の処方名（ローマ字）。TJ コードと tsumura 番号は下で追加する。
ROMAJI_NAMES = [
    'yokukansan', 'goreisan', 'goshajinkigan', 'daikenchuto', 'rikkunshito', 'hochuekkito',
    'keishibukuryogan', 'juzentaihoto', 'ninjinyoeito', 'hachimijiogan', 'bofutsushosan',
    'shosaikoto', 'daisaikoto', 'saireito', 'hangeshashinto', 'kakkonto', 'maoto', 'shoseiryuto',
    'bakumondoto', 'shinbuto', 'tokishakuyakusan', 'kamishoyosan', 'shakuyakukanzoto',
    'orengedokuto', 'jumihaidokuto', 'unseiin', 'chotosan', 'ninjinto', 'keishi-karyukotsuboreito',
    'saikokaryukotsuboreito', 'yokukansan-ka-chinpi-hange', 'hangekobokuto', 'boiogito',
    'choreito', 'saibokuto', 'keishikajutsubuto', 'yokukansankachinpihange', 'inchinkoto',
    'seihinto', 'anchusan', 'kososan', 'kamikihito', 'sansoninto', 'bu-zhong-yi-qi-tang',
    'da-jian-zhong-tang', 'liu-jun-zi-tang', 'ge-gen-tang', 'running piglet',
]

STRICT_REMOVE = frozenset(FP_HARD) | frozenset(STRICT_EXTRA)


def _build_concept_terms():
    terms = {}
    for top, sub in _dic.PATTERN_TERMS.items():
        cat = PTERM_CAT.get(top, "pathology")
        for tl in sub.values():
            if isinstance(tl, list):
                for t in tl:
                    terms[t] = cat
    for t in _dic.ABDOMINAL_TERMS:
        terms[t] = "examination"
    for t, c in BASE_EXTRA.items():
        terms.setdefault(t, c)
    terms.update(T1_ADDITIONS)
    return terms


CONCEPT_TERMS = _build_concept_terms()   # 辞書B（Liberal 版）: 語 -> カテゴリ


# ── 処方名 ─────────────────────────────────────
def _build_formula_ja():
    names = []
    for info in list(_dic.FORMULAS.values()) + list(_dic.EXTRA_FORMULAS.values()):
        names.append(info["name"])
        names += info.get("aliases", [])
    return sorted(set(names), key=len, reverse=True)


def tsumura_formula_names():
    """ツムラ128処方の名称と別名（同一処方集合での日英比較に使う）"""
    names = []
    for info in _dic.FORMULAS.values():
        names.append(info["name"])
        names += info.get("aliases", [])
    return sorted(set(names), key=len, reverse=True)


FORMULA_JA = _build_formula_ja()
ROMAJI_LEGACY = list(ROMAJI_NAMES)
for _i in range(1, 154):
    ROMAJI_LEGACY += [f"tj-{_i:03d}", f"tsumura no. {_i}", f"tsumura {_i}"]
_TJ_CODE = re.compile(r"(?<![a-z0-9])tj[-\s]?0{0,2}(\d{1,3})(?!\d)")


# ── 正規化 ─────────────────────────────────────
def _norm_legacy(text):
    """legacy の正規化: ハイフンを空白に、瘀血の表記ゆれを統一"""
    text = text.replace("-", " ")
    for v in OKETSU_VARIANTS:
        if v != "瘀血":
            text = text.replace(v, "瘀血")
    return text


def fold_diacritics(text):
    """ラテン文字の発音記号だけを畳み込む（shō → sho）。日本語には触れない"""
    out = []
    for ch in text:
        if ord(ch) > 127 and unicodedata.name(ch, "").startswith("LATIN"):
            ch = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
        out.append(ch)
    return "".join(out)


_SEPARATORS = "-'\u2019\u2018\u2010\u2011\u2012\u2013\u2014"


def _compact(text):
    """空白・ハイフン・アポストロフィを除く（Ninjin'yoeito → ninjinyoeito）"""
    return "".join(ch for ch in text if not ch.isspace() and ch not in _SEPARATORS)


def _compact_with_index(text):
    """_compact と同じ。戻り値の2つ目は、除いた後の各文字が元の文字列の何文字目だったか"""
    chars, idx = [], []
    for i, ch in enumerate(text):
        if not ch.isspace() and ch not in _SEPARATORS:
            chars.append(ch)
            idx.append(i)
    return "".join(chars), idx


# 英語の綴りゆれを畳む: 長音（Shosaikoto / Shousaikotou / Shohsaikoh…）、訓令式（Syo, Jyo）、b・p の前の m（Shimbu）
_CANON_RULES = (
    (re.compile(r"ou|oo|oh|uu"), lambda m: m.group()[0]),
    (re.compile(r"sy"), lambda m: "sh"),
    (re.compile(r"[jz]y"), lambda m: "j"),
    (re.compile(r"m(?=[bp])"), lambda m: "n"),
)


def _canon(s):
    for pat, f in _CANON_RULES:
        s = pat.sub(f, s)
    return s


def _canon_with_spans(s):
    """_canon と同じ。戻り値の2つ目は、畳んだ後の各文字が s の何文字目から何文字目だったか"""
    spans = [(i, i + 1) for i in range(len(s))]
    for pat, f in _CANON_RULES:
        out, new, pos = [], [], 0
        for m in pat.finditer(s):
            a, b = m.span()
            out.append(s[pos:a])
            new += spans[pos:a]
            r = f(m)
            out.append(r)
            new += spans[a:b] if len(r) == b - a else [(spans[a][0], spans[b - 1][1])]
            pos = b
        out.append(s[pos:])
        new += spans[pos:]
        s, spans = "".join(out), new
    return s, spans


def _norm_primary(text):
    return _norm_legacy(fold_diacritics(text.lower()))


# ── legacy ─────────────────────────────────────
_ROMAJI_LEGACY_SORTED = sorted(set(ROMAJI_LEGACY), key=len, reverse=True)


def _formulas_ja(text):
    found, remaining = [], text
    for name in FORMULA_JA:
        if name in remaining:
            found.append(name)
            remaining = remaining.replace(name, "\x00" * len(name))
    return found


def _formulas_legacy(text, lang):
    if lang == "ja":
        return _formulas_ja(text)
    tl = _norm_legacy(text.lower())
    return [n for n in _ROMAJI_LEGACY_SORTED if n in tl]


def _concepts_legacy(text):
    norm = _norm_legacy(text.lower())
    lib = [(t, c) for t, c in CONCEPT_TERMS.items() if t in norm]
    return _filters(lib)


def _filters(lib):
    base = [(t, c) for t, c in lib if t not in FP_HARD and t != "冷え"]
    zuisho = any(t == "随証" for t, _ in base)
    non_sho = {c for t, c in base if c in ("pathology", "examination", "classical")}
    cons = [(t, c) for t, c in base if not (t == "随証" and zuisho and not non_sho)]   # 随証のみは除外
    strict = [(t, c) for t, c in lib if t not in STRICT_REMOVE]
    return lib, cons, strict


# ── primary ────────────────────────────────────
_ROMAJI_PRIMARY = sorted({_norm_legacy(r) for r in ROMAJI_LEGACY if r != "running piglet"}, key=len, reverse=True)


def _formula_names_canonical():
    """全方剤（ツムラ128＋追加141）の読みから英語論文の綴りを作り、綴りゆれを畳んだ形にする。
    戻り値: (8文字以上: 部分文字列として照合, 5〜7文字: 1語まるごとの一致のみ)"""
    longn, shortn = set(), set()
    for info in list(_dic.FORMULAS.values()) + list(_dic.EXTRA_FORMULAS.values()):
        r = _canon(max(yomi_to_romaji_variants(info["yomi"]), key=len))
        if len(r) >= 8:
            longn.add(r)
        elif len(r) >= 5:
            shortn.add(r)
    return longn, shortn


_LONG_NAMES, _SHORT_NAMES = _formula_names_canonical()
_COMPACT_NAMES = sorted(
    _LONG_NAMES
    | {_canon(_compact(_norm_legacy(r))) for r in ROMAJI_LEGACY
       if r != "running piglet" and not r.startswith(("tj-", "tsumura")) and len(_compact(r)) >= 8},
    key=len, reverse=True)
_TOKEN = re.compile(r"[a-z]+(?:[-'\u2019\u2018][a-z]+)*")
_HYPHENS = "-\u2010\u2011\u2012\u2013\u2014"


def _compile_terms():
    out = []
    for t, c in CONCEPT_TERMS.items():
        if t.endswith(" "):
            # 'sho ' 'hie ' は語境界で照合する。次の場合は数えない（ハイフンを残し、大文字小文字を区別した文字列に対して照合する）。
            #  ・ハイフンで他の語につながる: Sho-saiko-to の Sho は小柴胡湯の「小」で、証ではない
            #  ・すべて大文字: SHO（Shosaiko-to の略）、HIE（低酸素性虚血性脳症）
            core = _norm_legacy(t.strip())
            out.append((t, c, re.compile(r"(?<![A-Za-z" + _HYPHENS + "])[" + core[0].upper() + core[0] + "]" + re.escape(core[1:])
                                         + r"(?![A-Za-z" + _HYPHENS + "])")))
        else:
            out.append((t, c, _norm_legacy(t)))
    return out


_TERMS_PRIMARY = _compile_terms()


def _english_formulas(folded):
    """英語の本文から処方名を探す。folded は発音記号を畳んだ文字列。
    戻り値: (見つかった名前, 処方名が占める範囲 [(開始, 終了)]。思考概念語の照合から外すために使う)"""
    low = folded.lower()
    track = len(low) == len(folded)
    found, spans = [], []
    low_h = low.replace("-", " ")
    for n in _ROMAJI_PRIMARY:   # 手書きの綴り。短いもの（maoto など）は語の途中に当たらないよう、語境界で照合する
        if len(_compact(n)) < 8:
            hits = [m.span() for m in re.finditer(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", low_h)]
        else:
            hits, i = [], low_h.find(n)
            while i >= 0:
                hits.append((i, i + len(n)))
                i = low_h.find(n, i + len(n))
        if hits:
            found.append(n)
            spans += hits
    comp, idx = _compact_with_index(low)
    canon, cspans = _canon_with_spans(comp)
    for n in _COMPACT_NAMES:   # 読みから作った綴り。長い名前から照合し、見つけた箇所は伏せる（keishito が saikokeishito の一部に当たらない）
        i = canon.find(n)
        if i < 0:
            continue
        found.append(n)
        while i >= 0:
            spans.append((idx[cspans[i][0]], idx[cspans[i + len(n) - 1][1] - 1] + 1))
            canon = canon[:i] + "\x00" * len(n) + canon[i + len(n):]
            i = canon.find(n)
    for m in _TOKEN.finditer(low):   # 短い名前（Mao-to, Kanzo-to）は、1語まるごとの一致だけ
        tok = _canon("".join(ch for ch in m.group() if ch not in _SEPARATORS))
        if tok in _SHORT_NAMES:
            found.append(tok)
            spans.append(m.span())
    m = _TJ_CODE.search(low_h)
    if m and 1 <= int(m.group(1)) <= 153:
        found.append("tj-" + m.group(1))
    return list(dict.fromkeys(found)), (spans if track else [])


def _mask(text, spans):
    if not spans:
        return text
    chars = list(text)
    for a, b in spans:
        chars[a:b] = " " * (b - a)
    return "".join(chars)


def _concepts_primary(text):
    low = text.lower()
    norm = _norm_legacy(low)
    lib = [(t, c) for t, c, m in _TERMS_PRIMARY if (m.search(text) if hasattr(m, "search") else m in norm)]
    return _filters(lib)


# 日本語の拡張（primary_ext）。日本語の草稿の説明（証の核心概念に 虚実・陰陽・寒熱・表裏、診察法に 腹診・腹証・舌診・脈診）にあるが、
# 実装の辞書B（181語）には無い語と、「○○湯証」の形。主解析には入れず、感度分析として別に出す。採否は漢方の専門家の判断。
EXTENSION_TERMS_JA = {
    "腹診": "examination", "腹証": "examination", "脈診": "examination", "舌診": "examination",
    "虚実": "sho_core", "陰陽": "sho_core", "寒熱": "sho_core", "表裏": "sho_core",
    "気血両虚": "pathology", "裏寒": "pathology",
}
_FORMULA_SHO = re.compile(r"[湯散丸飲]証")


# ── 公開API ────────────────────────────────────
def quadrant(has_formula, concept_hits):
    if has_formula and concept_hits:
        return "Q1_both"
    if concept_hits:
        return "Q2_cognition_only"
    return "Q3_formula_only" if has_formula else "Q4_neither"


def classify(article, variant="primary"):
    """1論文を分類する。article: {'title', 'abstract', 'lang'('ja'|'en')}。

    戻り値: formula(bool), formulas(list), liberal/conservative/strict(各 [(語, カテゴリ)]),
            quad_liberal / quad_conservative / quad_strict
    """
    if variant not in VARIANTS:
        raise ValueError(f"variant は {VARIANTS} のいずれか: {variant!r}")
    text = (article.get("title") or "") + " " + (article.get("abstract") or "")
    lang = article.get("lang", "en")
    if variant == "legacy":
        formulas = _formulas_legacy(text, lang)
        lib, cons, strict = _concepts_legacy(text)
    else:
        folded = fold_diacritics(text)
        if lang == "ja":
            formulas, masked = _formulas_ja(text), folded
        else:
            formulas, spans = _english_formulas(folded)
            masked = _mask(folded, spans)   # 処方名の中の sho などを概念語として数えない
        lib, cons, strict = _concepts_primary(masked)
        if variant == "primary_ext" and lang == "ja":
            add = [(t, c) for t, c in EXTENSION_TERMS_JA.items() if t in text]
            if _FORMULA_SHO.search(text):
                add.append(("○○湯証", "sho_core"))
            lib, cons, strict = lib + add, cons + add, strict + add
    has_f = bool(formulas)
    return {
        "formula": has_f, "formulas": formulas,
        "liberal": lib, "conservative": cons, "strict": strict,
        "quad_liberal": quadrant(has_f, lib),
        "quad_conservative": quadrant(has_f, cons),
        "quad_strict": quadrant(has_f, strict),
    }
