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

VARIANTS = ("legacy", "primary")
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


def _formula_romaji():
    """全方剤（ツムラ128＋追加141）の読みから、英語論文の綴り（shosaikoto / shousaikotou）を作る。8文字以上のみ"""
    out = set()
    for info in list(_dic.FORMULAS.values()) + list(_dic.EXTRA_FORMULAS.values()):
        yomi = info.get("yomi", "")
        if yomi:
            out |= {r for r in yomi_to_romaji_variants(yomi) if len(r) >= 8}
    return out


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


def _compact(text):
    """空白・ハイフン・アポストロフィを除く（Ninjin'yoeito → ninjinyoeito）"""
    return re.sub(r"[\s\-'’‘]+", "", text)


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
_COMPACT_NAMES = sorted(
    _formula_romaji()
    | {_compact(_norm_legacy(r)) for r in ROMAJI_LEGACY
       if r != "running piglet" and not r.startswith(("tj-", "tsumura")) and len(r) >= 8},
    key=len, reverse=True)


_HYPHENS = "-‐‑‒–—"


def _compile_terms():
    out = []
    for t, c in CONCEPT_TERMS.items():
        if t.endswith(" "):
            # 'sho ' 'hie ' は語境界で照合する。ハイフンで他の語につながる場合は除く
            # （Sho-saiko-to の Sho は小柴胡湯の「小」で、証ではない）。ハイフンを残した文字列に対して照合する。
            core = _norm_legacy(t.strip())
            out.append((t, c, re.compile(r"(?<![a-z" + _HYPHENS + "])" + re.escape(core) + r"(?![a-z" + _HYPHENS + "])")))
        else:
            out.append((t, c, _norm_legacy(t)))
    return out


_TERMS_PRIMARY = _compile_terms()


def _formulas_primary(text, lang):
    if lang == "ja":
        return _formulas_ja(text)
    norm = _norm_primary(text)
    found = [n for n in _ROMAJI_PRIMARY if n in norm]
    comp = _compact(norm)
    for n in _COMPACT_NAMES:   # 長い名前から照合し、見つけた箇所は伏せる（keishito が saikokeishito の一部に当たらないように）
        if n in comp:
            found.append(n)
            comp = comp.replace(n, "\x00" * len(n))
    m = _TJ_CODE.search(norm)
    if m and 1 <= int(m.group(1)) <= 153:
        found.append("tj-" + m.group(1))
    return list(dict.fromkeys(found))


def _concepts_primary(text):
    norm = _norm_primary(text)
    folded = fold_diacritics(text.lower())   # ハイフンを残したまま（語境界の判定用）
    lib = [(t, c) for t, c, m in _TERMS_PRIMARY if (m.search(folded) if hasattr(m, "search") else m in norm)]
    return _filters(lib)


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
        formulas = _formulas_primary(text, lang)
        lib, cons, strict = _concepts_primary(text)
    has_f = bool(formulas)
    return {
        "formula": has_f, "formulas": formulas,
        "liberal": lib, "conservative": cons, "strict": strict,
        "quad_liberal": quadrant(has_f, lib),
        "quad_conservative": quadrant(has_f, cons),
        "quad_strict": quadrant(has_f, strict),
    }
