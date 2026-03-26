# -*- coding: utf-8 -*-
"""
build_integrated_db_v4.py — 5軸カテゴリ対応 統合データベース構築

入力:
  - data/tagged/jstage_tagged_v3.json  (2,653 J-STAGE 論文)
  - data/tagged/pubmed_tagged_v3.json  (9,193 PubMed 論文)
  - data/categories_v3.json            (5軸カテゴリ体系)
  - dictionaries.py                    (方剤辞書)

出力: data/integrated_db_v4.json
  コンパクトな統合JSONデータベース（HTML埋め込み用）
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import DATA_DIR
from dictionaries import FORMULAS, EXTRA_FORMULAS

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
ABSTRACT_MAX = 500          # 抄録の最大文字数
AUTHOR_MIN_ARTICLES = 3     # 著者インデックスに含める最低論文数
INST_TOP_N = 100            # 所属インデックスの上位件数

TAGGED_DIR = DATA_DIR / "tagged"
JSTAGE_PATH = TAGGED_DIR / "jstage_tagged_v3.json"
PUBMED_PATH = TAGGED_DIR / "pubmed_tagged_v3.json"
CATEGORIES_PATH = DATA_DIR / "categories_v3.json"
OUTPUT_PATH = DATA_DIR / "integrated_db_v4.json"


# ---------------------------------------------------------------------------
# 方剤マッチング準備
# ---------------------------------------------------------------------------
def build_formula_lookup():
    """方剤辞書から検索用ルックアップを構築する。

    Returns:
        all_formulas: {formula_key: {name, num, origin}} — 全方剤マスター
        ja_patterns:  [(検索文字列, formula_key), ...] — 日本語名マッチ用
        en_patterns:  [(検索文字列(小文字), formula_key), ...] — ローマ字マッチ用
    """
    all_formulas = {}
    ja_patterns = []   # (日本語名, formula_key)
    en_patterns = []   # (ローマ字名(小文字), formula_key)

    # ツムラ方剤
    for num, info in FORMULAS.items():
        key = info["name"]
        all_formulas[key] = {"name": key, "num": num, "origin": info["origin"]}
        # 日本語パターン: 方剤名 + aliases
        ja_patterns.append((key, key))
        for alias in info.get("aliases", []):
            if not alias.startswith("TJ-") and not alias.isascii():
                ja_patterns.append((alias, key))
        # ローマ字パターン: yomi をヘボン式に変換
        romaji = yomi_to_romaji(info["yomi"])
        if romaji:
            en_patterns.append((romaji, key))

    # 非ツムラ方剤
    for eid, info in EXTRA_FORMULAS.items():
        key = info["name"]
        if key not in all_formulas:
            all_formulas[key] = {"name": key, "num": eid, "origin": info["origin"]}
            ja_patterns.append((key, key))
            for alias in info.get("aliases", []):
                if not alias.isascii():
                    ja_patterns.append((alias, key))
            romaji = yomi_to_romaji(info["yomi"])
            if romaji:
                en_patterns.append((romaji, key))

    # 長い名前を先にマッチさせるためソート（「桂枝茯苓丸加薏苡仁」→「桂枝茯苓丸」の順）
    ja_patterns.sort(key=lambda x: -len(x[0]))
    en_patterns.sort(key=lambda x: -len(x[0]))

    return all_formulas, ja_patterns, en_patterns


def yomi_to_romaji(yomi: str) -> str:
    """ひらがな読みをヘボン式ローマ字に簡易変換する。
    PubMed論文タイトルで使われるような表記にする。"""
    table = {
        "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
        "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
        "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
        "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
        "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
        "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
        "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
        "や": "ya", "ゆ": "yu", "よ": "yo",
        "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
        "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o",
        "ん": "n",
        "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
        "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
        "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
        "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
        "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
        # 拗音
        "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
        "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
        "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
        "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
        "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
        "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
        "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
        "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
        "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
        "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
        "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
        # 促音はあとで処理
        "っ": "",  # placeholder
        # 長音
        "ー": "",
    }
    result = []
    i = 0
    while i < len(yomi):
        # 拗音チェック（2文字）
        if i + 1 < len(yomi) and yomi[i:i+2] in table:
            result.append(table[yomi[i:i+2]])
            i += 2
        elif yomi[i] == "っ":
            # 促音: 次の子音を重ねる
            if i + 1 < len(yomi):
                # 次の文字のローマ字の最初の子音を取得
                if i + 2 < len(yomi) and yomi[i+1:i+3] in table:
                    nxt = table[yomi[i+1:i+3]]
                elif yomi[i+1] in table:
                    nxt = table[yomi[i+1]]
                else:
                    nxt = ""
                if nxt:
                    result.append(nxt[0])  # 子音を重ねる
            i += 1
        elif yomi[i] in table:
            result.append(table[yomi[i]])
            i += 1
        else:
            i += 1
    return "".join(result)


def match_formulas_ja(text: str, ja_patterns: list) -> list:
    """日本語テキストから方剤名をマッチさせる。"""
    if not text:
        return []
    found = []
    for pattern, key in ja_patterns:
        if pattern in text:
            if key not in found:
                found.append(key)
    return found


def match_formulas_en(text: str, en_patterns: list) -> list:
    """英語テキストから方剤のローマ字名をマッチさせる。"""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for pattern, key in en_patterns:
        if pattern in text_lower:
            if key not in found:
                found.append(key)
    return found


# ---------------------------------------------------------------------------
# カテゴリ体系の読み込み
# ---------------------------------------------------------------------------
def load_axes(categories: dict) -> tuple:
    """categories_v3.json から axes (リーフノード) と axis_chapters を構築する。

    Returns:
        axes:          {tag_id: {ja, en, ch}} — 全リーフノード
        axis_chapters: {axis_name: [{id, ja, en, leaves}, ...]}
    """
    axes_data = {}          # tag_id -> {ja, en, ch}
    axis_chapters = {}      # axis_name -> list of chapter dicts

    for axis_name, axis_info in categories["axes"].items():
        chapters_list = []

        if axis_name == "disease":
            # disease: chapters > children (leaf nodes)
            for ch_id, ch in axis_info.get("chapters", {}).items():
                ch_entry = {
                    "id": ch_id,
                    "ja": ch["name_ja"],
                    "en": ch["name_en"],
                    "leaves": [],
                }
                for child in ch.get("children", []):
                    leaf_id = child["id"]
                    axes_data[leaf_id] = {
                        "ja": child["name_ja"],
                        "en": child["name_en"],
                        "ch": ch_id,
                    }
                    ch_entry["leaves"].append(leaf_id)
                chapters_list.append(ch_entry)

        elif axis_name in ("symptom", "intervention"):
            # groups > children
            for grp_id, grp in axis_info.get("groups", {}).items():
                grp_entry = {
                    "id": grp_id,
                    "ja": grp.get("name_ja", grp_id),
                    "en": grp.get("name_en", grp_id),
                    "leaves": [],
                }
                for child in grp.get("children", []):
                    leaf_id = child["id"]
                    axes_data[leaf_id] = {
                        "ja": child["name_ja"],
                        "en": child["name_en"],
                        "ch": grp_id,
                    }
                    grp_entry["leaves"].append(leaf_id)
                if grp_entry["leaves"]:
                    chapters_list.append(grp_entry)

        elif axis_name == "study_design":
            # levels (flat list)
            grp_entry = {
                "id": "study_design",
                "ja": axis_info["name_ja"],
                "en": axis_info["name_en"],
                "leaves": [],
            }
            for lv in axis_info.get("levels", []):
                leaf_id = lv["id"]
                axes_data[leaf_id] = {
                    "ja": lv["name_ja"],
                    "en": lv["name_en"],
                    "ch": "study_design",
                }
                grp_entry["leaves"].append(leaf_id)
            if grp_entry["leaves"]:
                chapters_list.append(grp_entry)

        elif axis_name == "setting":
            # items (flat list)
            grp_entry = {
                "id": "setting",
                "ja": axis_info["name_ja"],
                "en": axis_info["name_en"],
                "leaves": [],
            }
            for item in axis_info.get("items", []):
                leaf_id = item["id"]
                axes_data[leaf_id] = {
                    "ja": item["name_ja"],
                    "en": item["name_en"],
                    "ch": "setting",
                }
                grp_entry["leaves"].append(leaf_id)
            if grp_entry["leaves"]:
                chapters_list.append(grp_entry)

        axis_chapters[axis_name] = chapters_list

    return axes_data, axis_chapters


# ---------------------------------------------------------------------------
# 所属名の正規化
# ---------------------------------------------------------------------------
INST_PATTERNS = [
    # 日本語大学
    re.compile(r"([\w\u3000-\u9fff]+大学[\w\u3000-\u9fff]*(?:病院|医学部|薬学部|附属病院)?)"),
    # English university/hospital
    re.compile(r"((?:University|School|College|Hospital|Institute|Center|Centre)"
               r"[\w\s,]*?)(?:\.|,|;|$)", re.IGNORECASE),
    # "Dept of ..., Univ ..." patterns
    re.compile(r",\s*([\w\s]+(?:University|Hospital|Institute|School)[\w\s]*?)(?:\.|,|$)",
               re.IGNORECASE),
]


def extract_institution(affiliation: str) -> str | None:
    """所属文字列から大学・病院名を抽出する。"""
    if not affiliation:
        return None
    for pat in INST_PATTERNS:
        m = pat.search(affiliation)
        if m:
            inst = m.group(1).strip().rstrip(",.")
            if len(inst) > 5:
                return inst
    return None


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("build_integrated_db_v4.py — 5軸統合DB構築")
    print("=" * 60)

    # --- データ読み込み ---
    print("\n[1/6] データ読み込み...")
    with open(JSTAGE_PATH, encoding="utf-8") as f:
        jstage_articles = json.load(f)
    print(f"  J-STAGE: {len(jstage_articles):,} 件")

    with open(PUBMED_PATH, encoding="utf-8") as f:
        pubmed_articles = json.load(f)
    print(f"  PubMed:  {len(pubmed_articles):,} 件")

    with open(CATEGORIES_PATH, encoding="utf-8") as f:
        categories = json.load(f)

    # --- カテゴリ体系 ---
    print("\n[2/6] カテゴリ体系構築...")
    axes_data, axis_chapters = load_axes(categories)
    print(f"  リーフノード数: {len(axes_data)}")
    for axis_name, chs in axis_chapters.items():
        leaf_count = sum(len(c["leaves"]) for c in chs)
        print(f"    {axis_name}: {len(chs)} グループ, {leaf_count} リーフ")

    # --- 方剤辞書 ---
    print("\n[3/6] 方剤辞書構築...")
    all_formulas, ja_patterns, en_patterns = build_formula_lookup()
    print(f"  方剤数: {len(all_formulas)}")
    print(f"  日本語パターン: {len(ja_patterns)}")
    print(f"  英語パターン: {len(en_patterns)}")

    # --- 統合論文リスト構築 ---
    print("\n[4/6] 統合論文リスト構築...")
    articles = []
    formula_counter = Counter()     # formula_name -> count
    axis_index = defaultdict(list)  # tag_id -> [article_idx, ...]
    formula_index = defaultdict(list)  # formula_name -> [article_idx, ...]
    author_counter = Counter()
    author_articles = defaultdict(list)  # author_name -> [article_idx, ...]
    inst_counter = Counter()
    inst_articles = defaultdict(list)
    year_dist = defaultdict(lambda: {"jp": 0, "pm": 0})
    with_abstract_count = 0
    all_years = []

    # --- J-STAGE 論文 ---
    print("  J-STAGE 処理中...")
    for art in jstage_articles:
        idx = len(articles)
        cats_v3 = art.get("categories_v3", {})

        # タイトル（日本語優先）
        title_ja = art.get("title_ja", "")
        title_en = art.get("title_en", "")
        title = title_ja if title_ja else title_en

        # 著者
        authors_ja = art.get("authors_ja", [])
        authors_en = art.get("authors_en", [])
        if isinstance(authors_ja, str):
            authors_ja = [a.strip() for a in authors_ja.split(",") if a.strip()]
        if isinstance(authors_en, str):
            authors_en = [a.strip() for a in authors_en.split(",") if a.strip()]
        author_str = ", ".join(authors_ja) if authors_ja else ", ".join(authors_en)

        # 抄録（日本語優先）
        abstract_ja = art.get("abstract_ja", "") or ""
        abstract_en = art.get("abstract_en", "") or ""
        abstract = abstract_ja if abstract_ja else abstract_en
        abstract = abstract[:ABSTRACT_MAX]
        if abstract:
            with_abstract_count += 1

        # 年
        year = str(art.get("pubyear", ""))
        if year:
            all_years.append(int(year))
            year_dist[year]["jp"] += 1

        # リンク
        link = art.get("link", "")

        # 方剤マッチング
        search_text_ja = (title_ja or "") + " " + (abstract_ja or "")
        matched_formulas = match_formulas_ja(search_text_ja, ja_patterns)
        for fm in matched_formulas:
            formula_counter[fm] += 1
            formula_index[fm].append(idx)

        # 方剤インデックス（articles内はインデックス番号で保持 → 後で変換）
        formula_names = matched_formulas

        # カテゴリタグ
        d_tags = cats_v3.get("disease", [])
        sx_tags = cats_v3.get("symptom", [])
        int_tags = cats_v3.get("intervention", [])
        sd_tags = cats_v3.get("study_design", [])
        set_tags = cats_v3.get("setting", [])

        # 軸インデックス更新
        for tag in d_tags + sx_tags + int_tags + sd_tags + set_tags:
            axis_index[tag].append(idx)

        # 著者インデックス
        for a_name in authors_ja:
            author_counter[a_name] += 1
            author_articles[a_name].append(idx)
        for a_name in authors_en:
            author_counter[a_name] += 1
            author_articles[a_name].append(idx)

        entry = {
            "t": title,
            "y": year,
            "a": author_str,
            "j": art.get("journal", "日本東洋医学雑誌"),
            "l": link,
            "ab": abstract,
            "f": formula_names,
            "s": "jp",
            "d": d_tags,
            "sx": sx_tags,
            "int": int_tags,
            "sd": sd_tags,
            "set": set_tags,
            "doi": art.get("doi", ""),
        }
        # title_en は J-STAGE のみ付与
        if title_en and title_ja:
            entry["te"] = title_en

        articles.append(entry)

    print(f"    {len(jstage_articles):,} 件処理完了")

    # --- PubMed 論文 ---
    print("  PubMed 処理中...")
    for art in pubmed_articles:
        idx = len(articles)
        cats_v3 = art.get("categories_v3", {})

        title = art.get("title", "")
        authors = art.get("authors", [])
        if isinstance(authors, list):
            author_str = ", ".join(authors[:10])  # 多すぎる場合は10名まで
            if len(authors) > 10:
                author_str += f" et al. ({len(authors)})"
        else:
            author_str = str(authors)

        abstract = (art.get("abstract", "") or "")[:ABSTRACT_MAX]
        if abstract:
            with_abstract_count += 1

        year = str(art.get("year", ""))
        if year:
            all_years.append(int(year))
            year_dist[year]["pm"] += 1

        link = art.get("pubmed_url", "")
        affiliation = art.get("affiliation", "") or ""

        # 方剤マッチング（英語タイトル+抄録）
        search_text_en = (title or "") + " " + (art.get("abstract", "") or "")
        matched_formulas = match_formulas_en(search_text_en, en_patterns)
        # 日本語方剤名もタイトルに含まれることがある
        matched_formulas_ja = match_formulas_ja(search_text_en, ja_patterns)
        for fm in matched_formulas_ja:
            if fm not in matched_formulas:
                matched_formulas.append(fm)

        for fm in matched_formulas:
            formula_counter[fm] += 1
            formula_index[fm].append(idx)

        # カテゴリタグ
        d_tags = cats_v3.get("disease", [])
        sx_tags = cats_v3.get("symptom", [])
        int_tags = cats_v3.get("intervention", [])
        sd_tags = cats_v3.get("study_design", [])
        set_tags = cats_v3.get("setting", [])

        for tag in d_tags + sx_tags + int_tags + sd_tags + set_tags:
            axis_index[tag].append(idx)

        # 著者インデックス
        for a_name in (authors if isinstance(authors, list) else []):
            author_counter[a_name] += 1
            author_articles[a_name].append(idx)

        # 所属インデックス
        inst = extract_institution(affiliation)
        if inst:
            inst_counter[inst] += 1
            inst_articles[inst].append(idx)

        # Japan affiliation フラグ
        is_japan = "japan" in affiliation.lower() if affiliation else False

        entry = {
            "t": title,
            "y": year,
            "a": author_str,
            "j": art.get("journal", art.get("journal_abbr", "")),
            "l": link,
            "ab": abstract,
            "f": matched_formulas,
            "s": "pm",
            "d": d_tags,
            "sx": sx_tags,
            "int": int_tags,
            "sd": sd_tags,
            "set": set_tags,
            "doi": art.get("doi", ""),
        }
        if affiliation:
            entry["af"] = affiliation
        if not is_japan:
            entry["fgn"] = 1  # foreign flag (non-Japan)

        articles.append(entry)

    print(f"    {len(pubmed_articles):,} 件処理完了")

    # --- 空リストの除去（サイズ削減） ---
    print("\n[5/6] データ最適化...")
    for art in articles:
        for key in ("d", "sx", "int", "sd", "set", "f"):
            if not art.get(key):
                del art[key]
        if not art.get("ab"):
            if "ab" in art:
                del art["ab"]
        if not art.get("doi"):
            if "doi" in art:
                del art["doi"]
        if not art.get("af"):
            if "af" in art:
                del art["af"]
        if not art.get("te"):
            if "te" in art:
                del art["te"]

    # --- 方剤マスター ---
    formulas_out = {}
    for fname, finfo in all_formulas.items():
        count = formula_counter.get(fname, 0)
        if count > 0:
            formulas_out[fname] = {
                "num": finfo["num"],
                "origin": finfo["origin"],
                "count": count,
            }

    # --- 著者インデックス（AUTHOR_MIN_ARTICLES 以上の著者のみ） ---
    print(f"  著者: {len(author_counter):,} 名 → ", end="")
    au_index = {}
    for name, count in author_counter.most_common():
        if count < AUTHOR_MIN_ARTICLES:
            break
        au_index[name] = author_articles[name]
    print(f"{len(au_index):,} 名（{AUTHOR_MIN_ARTICLES}件以上）")

    # --- 所属インデックス（上位 INST_TOP_N） ---
    print(f"  所属: {len(inst_counter):,} 機関 → ", end="")
    inst_index = {}
    for inst_name, count in inst_counter.most_common(INST_TOP_N):
        inst_index[inst_name] = inst_articles[inst_name]
    print(f"{len(inst_index):,} 機関（上位{INST_TOP_N}）")

    # --- 年範囲 ---
    year_min = min(all_years) if all_years else 0
    year_max = max(all_years) if all_years else 0

    # --- 統計 ---
    jp_count = sum(1 for a in articles if a["s"] == "jp")
    pm_count = sum(1 for a in articles if a["s"] == "pm")

    stats = {
        "total": len(articles),
        "jp": jp_count,
        "pm": pm_count,
        "with_abstract": with_abstract_count,
        "year_range": [year_min, year_max],
    }

    # --- 出力JSON ---
    print("\n[6/6] JSON出力...")
    output = {
        "stats": stats,
        "articles": articles,
        "axes": axes_data,
        "axis_chapters": axis_chapters,
        "formulas": formulas_out,
        "fi": {k: v for k, v in formula_index.items() if v},
        "ai": {k: v for k, v in axis_index.items() if v},
        "au": au_index,
        "inst": inst_index,
        "yd": dict(year_dist),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    file_size = OUTPUT_PATH.stat().st_size
    print(f"\n  出力: {OUTPUT_PATH}")
    print(f"  サイズ: {file_size / 1024 / 1024:.1f} MB")

    # --- サマリー ---
    print("\n" + "=" * 60)
    print("統計サマリー")
    print("=" * 60)
    print(f"  総論文数:       {stats['total']:,}")
    print(f"    J-STAGE:      {stats['jp']:,}")
    print(f"    PubMed:       {stats['pm']:,}")
    print(f"  抄録あり:       {stats['with_abstract']:,}")
    print(f"  年範囲:         {year_min}–{year_max}")
    print(f"  方剤（出現あり）: {len(formulas_out):,}")
    print(f"  軸タグ（使用中）: {len([k for k, v in axis_index.items() if v]):,}")
    print(f"  著者インデックス: {len(au_index):,} 名")
    print(f"  所属インデックス: {len(inst_index):,} 機関")

    # トップ方剤
    print("\n  方剤トップ20:")
    for fname, count in formula_counter.most_common(20):
        print(f"    {fname}: {count}")

    # 軸別タグ件数トップ5
    prefix_map = {
        "disease": "ICD",
        "symptom": "SX_",
        "intervention": "INT_",
        "study_design": "SD_",
        "setting": "SET_",
    }
    for axis_name in ["disease", "symptom", "intervention", "study_design", "setting"]:
        print(f"\n  {axis_name} トップ5:")
        prefix = prefix_map[axis_name]
        axis_tags = [(tag, len(idxs)) for tag, idxs in axis_index.items()
                     if tag.startswith(prefix)]
        axis_tags.sort(key=lambda x: -x[1])
        for tag, count in axis_tags[:5]:
            info = axes_data.get(tag, {})
            print(f"    {tag} ({info.get('ja', '?')}): {count}")

    print("\n完了!")


if __name__ == "__main__":
    main()
