"""
PubMedデータのノイズ除去スクリプト

戦略:
  - L1(漢方) or L2(鍼灸) にヒット → 自動採用
  - L3(薬学)のみ → title/abstract/MeSH に漢方・生薬関連語が含まれれば採用
  - それ以外 → ノイズとして除去

主なノイズ原因:
  - "JPS" → J Physiol Sci (略称衝突)
  - "Tsumura", "Kotaro" → 人名ヒット
  - "Kracie" → 社名だが漢方と無関係な文脈
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import DATA_DIR

# ─── 方剤ローマ字辞書生成 ─────────────────────────
import importlib.util

spec = importlib.util.spec_from_file_location("dictionaries", "dictionaries.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

HEPBURN = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "っ": "t",
}


def yomi_to_romaji(yomi):
    result = ""
    i = 0
    while i < len(yomi):
        if i + 1 < len(yomi) and yomi[i : i + 2] in HEPBURN:
            result += HEPBURN[yomi[i : i + 2]]
            i += 2
        elif yomi[i] in HEPBURN:
            result += HEPBURN[yomi[i]]
            i += 1
        else:
            i += 1
    return result


formula_romaji = set()
for num, f in mod.FORMULAS.items():
    yomi = f.get("yomi", "")
    if yomi:
        rom = yomi_to_romaji(yomi)
        if len(rom) >= 6:
            formula_romaji.add(rom)

# ─── 関連語辞書 ─────────────────────────────────
RELEVANT_TERMS = [
    # 漢方直接
    "kampo", "kanpo", "wakan", "traditional japanese", "japanese herbal",
    "oriental medicine", "east asian medicine", "traditional medicine",
    "traditional chinese", "chinese medicine", "tcm",
    # 生薬
    "herbal medicine", "herbal drug", "herbal formula", "herbal extract",
    "crude drug", "medicinal plant", "medicinal herb",
    "phytotherapy", "pharmacognosy", "ethnopharmacol",
    "plant extract", "botanical",
    # 鍼灸
    "acupuncture", "moxibustion", "electroacupuncture", "shiatsu",
    "dry needling", "acupressure",
    # 有効成分
    "glycyrrhizin", "berberine", "baicalin", "baicalein", "paeoniflorin",
    "ginsenoside", "saikosaponin", "magnolol", "honokiol", "wogonin",
    "ephedrine", "shogaol", "gingerol", "sennoside", "aconitine",
    # 学名
    "glycyrrhiza", "bupleurum", "scutellaria", "coptis", "atractylodes",
    "poria", "rehmannia", "angelica sinensis", "cnidium", "magnolia",
    "ephedra", "paeonia", "zingiber", "panax", "cinnamomum",
    # 企業（所属文脈で限定）
    "tsumura co", "kracie pharma", "kotaro pharma",
]

RELEVANT_MESH = [
    "drugs, chinese herbal",
    "medicine, east asian traditional",
    "medicine, kampo",
    "phytotherapy",
    "plant extracts",
    "acupuncture therapy",
    "acupuncture points",
    "moxibustion",
    "electroacupuncture",
    "acupuncture analgesia",
]


def is_relevant(art):
    """論文が東洋医学関連かどうか判定"""
    text = (art.get("title", "") + " " + art.get("abstract", "")).lower()
    mesh_text = " ".join(art.get("mesh_terms", [])).lower()

    for term in RELEVANT_TERMS:
        if term in text:
            return True
    for mesh in RELEVANT_MESH:
        if mesh in mesh_text:
            return True
    for rom in formula_romaji:
        if rom in text:
            return True
    return False


def main():
    pubmed_dir = DATA_DIR / "pubmed"
    input_path = pubmed_dir / "pubmed_all_merged.json"

    with open(input_path, encoding="utf-8") as f:
        arts = json.load(f)

    print(f"入力: {len(arts)} 件")

    cleaned = []
    noise = []

    for a in arts:
        layers = set(
            t[0:2] for t in a.get("search_layers", []) if t.startswith("L")
        )
        if layers & {"L1", "L2"}:
            a["noise_filter"] = "pass_l1l2"
            cleaned.append(a)
        elif is_relevant(a):
            a["noise_filter"] = "pass_l3_relevant"
            cleaned.append(a)
        else:
            a["noise_filter"] = "removed_noise"
            noise.append(a)

    # 保存
    clean_path = pubmed_dir / "pubmed_cleaned.json"
    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    noise_path = pubmed_dir / "pubmed_noise_removed.json"
    with open(noise_path, "w", encoding="utf-8") as f:
        json.dump(noise, f, ensure_ascii=False, indent=2)

    print(f"\n=== ノイズ除去結果 ===")
    print(f"クリーン: {len(cleaned)} → {clean_path.name}")
    print(f"ノイズ除去: {len(noise)} → {noise_path.name}")

    # ─── サマリー ───
    pass_type = Counter(a["noise_filter"] for a in cleaned)
    print(f"\n採用理由:")
    for k, v in pass_type.most_common():
        print(f"  {k}: {v}")

    # 国別
    countries = Counter()
    for a in cleaned:
        aff = (a.get("affiliation", "") or "").lower()
        if "japan" in aff:
            countries["Japan"] += 1
        elif "china" in aff or "chinese" in aff:
            countries["China"] += 1
        elif "korea" in aff:
            countries["Korea"] += 1
        elif aff == "":
            countries["不明"] += 1
        else:
            countries["その他"] += 1
    print(f"\n所属国:")
    for k, v in countries.most_common():
        print(f"  {k}: {v} ({100*v/len(cleaned):.1f}%)")

    # 研究デザイン
    print(f"\n研究デザイン:")
    for pt_name in [
        "Randomized Controlled Trial", "Systematic Review", "Meta-Analysis",
        "Case Reports", "Clinical Trial", "Observational Study", "Review",
    ]:
        c = sum(1 for a in cleaned if pt_name in a.get("pub_types", []))
        print(f"  {pt_name}: {c}")

    # 年代別
    decades = Counter()
    for a in cleaned:
        y = a.get("year", "")
        if y and y.isdigit():
            decade = f"{y[:3]}0s"
            decades[decade] += 1
    print(f"\n年代別:")
    for d in sorted(decades.keys()):
        print(f"  {d}: {decades[d]}")

    # アブストラクト
    with_abs = sum(1 for a in cleaned if a.get("abstract", "").strip())
    print(f"\nアブストラクトあり: {with_abs}/{len(cleaned)} ({100*with_abs/len(cleaned):.1f}%)")

    # 上位雑誌
    journals = Counter()
    for a in cleaned:
        j = a.get("journal_abbr", "") or a.get("journal", "") or "Unknown"
        journals[j] += 1
    print(f"\n上位15雑誌:")
    for j, c in journals.most_common(15):
        print(f"  {c:5d}  {j}")

    # 日本語誌との統合後の全体像
    print(f"\n{'='*60}")
    print(f"統合後のエビデンスマップ規模:")
    print(f"  PubMed (クリーン): {len(cleaned)}")
    print(f"  日本語誌 (既存):   2,653")
    print(f"  合計:              {len(cleaned) + 2653}")


if __name__ == "__main__":
    main()
