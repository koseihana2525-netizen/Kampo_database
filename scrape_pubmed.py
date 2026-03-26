"""
PubMed E-utilities: 日本発の東洋医学研究を包括的に取得する

3層検索戦略:
  Layer 1 (コア): Kampo/漢方 キーワード + MeSH + 方剤名 + TJ番号 + 和漢
  Layer 2 (鍼灸): acupuncture + 関連語 + Japan発
  Layer 3 (薬学): 生薬成分・学名・品質管理・薬理活性 + 漢方文脈

Usage:
    python scrape_pubmed.py --dry-run       # 件数確認のみ
    python scrape_pubmed.py                 # 全Layer実行
    python scrape_pubmed.py --layer 1       # Layer 1のみ
    python scrape_pubmed.py --layer 2       # Layer 2のみ
    python scrape_pubmed.py --layer 3       # Layer 3のみ
"""

import argparse
import json
import time
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

from config import DATA_DIR

# === PubMed E-utilities 設定 ===
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"

# APIキーなし: 3 req/sec → 安全に 0.4秒間隔
REQUEST_INTERVAL = 0.4
BATCH_SIZE = 200

# 出力先
PUBMED_DIR = DATA_DIR / "pubmed"
PUBMED_DIR.mkdir(exist_ok=True)

# ================================================================
# 検索クエリ定義（3層戦略）
# ================================================================

# --- Layer 1: コア（漢方・方剤） ---
LAYER1_QUERIES = {
    "L1_kampo_keywords": {
        "name": "L1: Kampo キーワード + MeSH",
        "query": (
            '('
            'Kampo OR Kanpo OR "Japanese Kampo" '
            'OR "traditional Japanese medicine" '
            'OR "Japanese herbal medicine" '
            'OR "Japanese oriental medicine" '
            'OR "medicine, Kampo"[MeSH] '
            'OR "medicine, East Asian traditional"[MeSH]'
            ') AND Japan'
        ),
    },
    "L1_wakan": {
        "name": "L1: 和漢 (Wakan)",
        "query": (
            '(Wakan OR "Wakan-yaku" OR "Sino-Japanese medicine" '
            'OR "Japanese-Chinese medicine") AND Japan'
        ),
    },
    "L1_formula_major": {
        "name": "L1: 主要方剤名 (Top 30)",
        "query": (
            '(Rikkunshito OR Daikenchuto OR Yokukansan OR Hochuekkito '
            'OR Shosaikoto OR Juzentaihoto OR Shakuyakukanzoto '
            'OR Bakumondoto OR Goshajinkigan OR Hangeshashinto '
            'OR Kakkonto OR Maoto OR Keishibukuryogan OR Kamishoyosan '
            'OR Tokishakuyakusan OR Saireito OR Ninjinyoeito '
            'OR Choreito OR Goreisan OR Bofutsushosan '
            'OR Daisaikoto OR Saikokeishito OR Orengedokuto '
            'OR Shoseiryuto OR Boiogito OR Yokukansankachinpihange '
            'OR Mashiningan OR Jumihaidokuto OR Unseiin '
            'OR Hachimijiogan)'
        ),
    },
    "L1_formula_minor": {
        "name": "L1: 追加方剤名",
        "query": (
            '(Shimotsuto OR Keishikajutsubuto OR Bukuryoingohangekobokuto '
            'OR Saikokaruyukotsuboreito OR Hangekobokuto OR Inchinkoto '
            'OR Daiokanzoto OR Tokikenchuto OR Shinbuto '
            'OR Goshuyuto OR Anchusan OR Chotosan '
            'OR Sansoninto OR Seishinrenshiin OR Kamikihito '
            'OR Kososan OR Shigyakusan OR Byakkokaninjinto '
            'OR Ninjinto OR Saikokeshikankyoto '
            'OR Tsudosan OR Yokuininto OR Keishito)'
        ),
    },
    "L1_tj_numbers": {
        "name": "L1: TJ番号 (ツムラ製品コード)",
        "query": (
            '("TJ-1" OR "TJ-9" OR "TJ-14" OR "TJ-16" OR "TJ-17" '
            'OR "TJ-19" OR "TJ-23" OR "TJ-24" OR "TJ-25" OR "TJ-27" '
            'OR "TJ-29" OR "TJ-41" OR "TJ-43" OR "TJ-48" OR "TJ-54" '
            'OR "TJ-68" OR "TJ-83" OR "TJ-100" OR "TJ-107" OR "TJ-108" '
            'OR "TJ-114" OR "TJ-128" OR "TJ-135" OR "TJ-137") '
            'AND Japan'
        ),
    },
}

# --- Layer 2: 鍼灸・手技 ---
LAYER2_QUERIES = {
    "L2_acupuncture": {
        "name": "L2: 鍼灸・手技 包括検索",
        "query": (
            '('
            'acupuncture OR moxibustion OR electroacupuncture '
            'OR "electro-acupuncture" OR "dry needling" '
            'OR acupressure OR "auricular acupuncture" '
            'OR moxa OR shiatsu OR anma '
            'OR "acupuncture therapy"[MeSH] '
            'OR "acupuncture points"[MeSH] '
            'OR "meridians"[MeSH] '
            'OR "acupuncture analgesia"[MeSH] '
            'OR "electroacupuncture"[MeSH]'
            ') AND (Japan[Affiliation] OR Japanese[Title/Abstract])'
        ),
    },
}

# --- Layer 3: 薬学・生薬・基礎研究 ---
LAYER3_QUERIES = {
    "L3_herbal_mesh": {
        "name": "L3: 生薬 MeSH (漢方文脈)",
        "query": (
            '('
            '"drugs, Chinese herbal"[MeSH] '
            'OR "phytotherapy"[MeSH] '
            'OR "plant extracts"[MeSH]'
            ') AND Japan[Affiliation] '
            'AND (Kampo OR "traditional Japanese" OR "Japanese herbal" '
            'OR "oriental medicine" OR "traditional medicine" '
            'OR "East Asian" OR "herbal medicine")'
        ),
    },
    "L3_crude_drug": {
        "name": "L3: 生薬学 (crude drug/pharmacognosy)",
        "query": (
            '('
            '"crude drug" OR "crude drugs" OR pharmacognosy '
            'OR "herbal drug" OR "medicinal plant" OR "medicinal plants" '
            'OR "medicinal herb"'
            ') AND Japan[Affiliation] '
            'AND (Kampo OR "traditional Japanese" OR "Japanese herbal" '
            'OR "oriental medicine" OR "traditional medicine")'
        ),
    },
    "L3_active_compounds": {
        "name": "L3: 生薬有効成分名",
        "query": (
            '('
            'glycyrrhizin OR berberine OR baicalin OR baicalein '
            'OR paeoniflorin OR ginsenoside OR saikosaponin '
            'OR atractylodin OR magnolol OR honokiol '
            'OR coptisine OR palmatine OR wogonin '
            'OR poricoic OR pachymic OR aucubin '
            'OR sennoside OR rhein OR emodin '
            'OR aconitine OR mesaconitine '
            'OR ephedrine OR pseudoephedrine '
            'OR shogaol OR gingerol'
            ') AND Japan[Affiliation] '
            'AND ("herbal" OR "crude drug" OR "Kampo" OR "traditional" '
            'OR "medicinal plant" OR "extract")'
        ),
    },
    "L3_botanical_names": {
        "name": "L3: 生薬学名 (主要15属)",
        "query": (
            '('
            'Glycyrrhiza OR Bupleurum OR Scutellaria OR Coptis '
            'OR Atractylodes OR Poria OR Rehmannia '
            'OR Angelica OR Cnidium OR Magnolia '
            'OR Ephedra OR Paeonia OR Zingiber '
            'OR Panax OR Cinnamomum'
            ') AND Japan[Affiliation] '
            'AND (Kampo OR "herbal medicine" OR "crude drug" '
            'OR "traditional medicine" OR "medicinal" OR "pharmacognosy")'
        ),
    },
    "L3_pharma_analysis": {
        "name": "L3: 品質管理・分析化学",
        "query": (
            '('
            '"quality control" OR standardization OR HPLC '
            'OR "LC-MS" OR "mass spectrometry" '
            'OR "chemical analysis" OR "fingerprint" '
            'OR "authentication" OR "adulteration" '
            'OR "DNA barcoding"'
            ') AND ("herbal medicine" OR "crude drug" OR Kampo '
            'OR "medicinal plant") '
            'AND Japan[Affiliation]'
        ),
    },
    "L3_pharmacology": {
        "name": "L3: 薬理活性 (漢方文脈)",
        "query": (
            '('
            '"anti-inflammatory" OR antioxidant OR anticancer OR antitumor '
            'OR immunomodulatory OR neuroprotective '
            'OR hepatoprotective OR gastroprotective '
            'OR "anti-allergic" OR "anti-obesity"'
            ') AND ("herbal" OR "crude drug" OR "plant extract" OR Kampo) '
            'AND Japan[Affiliation]'
        ),
    },
    "L3_safety": {
        "name": "L3: 安全性・毒性・相互作用",
        "query": (
            '('
            '"adverse effect" OR "side effect" OR toxicity '
            'OR hepatotoxicity OR "interstitial pneumonia" '
            'OR "drug interaction" OR "herb-drug interaction" '
            'OR "CYP" OR "cytochrome P450" '
            'OR pharmacokinetics'
            ') AND (Kampo OR "herbal medicine" OR "crude drug") '
            'AND Japan[Affiliation]'
        ),
    },
    "L3_microbiome": {
        "name": "L3: 腸内細菌・マイクロバイオーム",
        "query": (
            '('
            '"gut microbiota" OR "intestinal bacteria" OR microbiome '
            'OR "gut flora" OR "intestinal flora"'
            ') AND (Kampo OR "herbal medicine" OR "crude drug" '
            'OR "traditional medicine") '
            'AND Japan[Affiliation]'
        ),
    },
    "L3_rwd_epi": {
        "name": "L3: RWD・疫学・医療政策",
        "query": (
            '('
            '"DPC database" OR "national database" OR "NDB" '
            'OR "claims data" OR "real-world data" '
            'OR "real-world evidence" '
            'OR "health insurance" OR "prescription"'
            ') AND (Kampo OR "herbal medicine" OR acupuncture) '
            'AND Japan'
        ),
    },
    "L3_manufacturer": {
        "name": "L3: 製薬企業関連",
        "query": (
            '("Tsumura" OR "Kracie" OR "Kotaro" OR "JPS") '
            'AND Japan '
            'AND ("herbal" OR "extract" OR "granule" OR "formulation" '
            'OR "Kampo" OR "medicine")'
        ),
    },
    "L3_network_pharma": {
        "name": "L3: ネットワーク薬理学・systems biology",
        "query": (
            '('
            '"network pharmacology" OR "systems pharmacology" '
            'OR "molecular docking" OR "target prediction" '
            'OR "systems biology"'
            ') AND (Kampo OR "herbal medicine" OR "traditional Japanese") '
            'AND Japan[Affiliation]'
        ),
    },
}

ALL_LAYERS = {
    1: LAYER1_QUERIES,
    2: LAYER2_QUERIES,
    3: LAYER3_QUERIES,
}


# ================================================================
# PubMed API 関数
# ================================================================

def esearch(query: str) -> tuple:
    """PubMed検索 → WebEnvキーを返す"""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": "0",
        "usehistory": "y",
        "retmode": "json",
    }
    resp = requests.get(ESEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["esearchresult"]
    count = int(data["count"])
    webenv = data["webenv"]
    query_key = data["querykey"]
    return count, webenv, query_key


def efetch_batch(webenv: str, query_key: str, retstart: int, retmax: int) -> str:
    """WebEnvでメタデータXMLを取得"""
    params = {
        "db": "pubmed",
        "WebEnv": webenv,
        "query_key": query_key,
        "retstart": str(retstart),
        "retmax": str(retmax),
        "rettype": "xml",
        "retmode": "xml",
    }
    resp = requests.get(EFETCH_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.text


def parse_articles(xml_text: str) -> list:
    """PubMed XMLをパースして論文リストを返す"""
    articles = []
    root = ET.fromstring(xml_text)

    for article_elem in root.findall(".//PubmedArticle"):
        try:
            art = article_elem.find(".//Article")
            if art is None:
                continue

            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            title_elem = art.find(".//ArticleTitle")
            title = "".join(title_elem.itertext()) if title_elem is not None else ""

            authors = []
            for author in art.findall(".//Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

            journal_elem = art.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else ""

            journal_abbr_elem = art.find(".//Journal/ISOAbbreviation")
            journal_abbr = journal_abbr_elem.text if journal_abbr_elem is not None else ""

            year = ""
            pub_date = art.find(".//Journal/JournalIssue/PubDate")
            if pub_date is not None:
                y = pub_date.findtext("Year", "")
                if y:
                    year = y
                else:
                    medline = pub_date.findtext("MedlineDate", "")
                    if medline:
                        year = medline[:4]

            doi = ""
            for id_elem in article_elem.findall(".//ArticleId"):
                if id_elem.get("IdType") == "doi":
                    doi = id_elem.text or ""
                    break

            abstract_parts = []
            for abs_text in art.findall(".//Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = "".join(abs_text.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = "\n".join(abstract_parts)

            mesh_terms = []
            for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
                mesh_terms.append(mesh.text or "")

            pub_types = []
            for pt in art.findall(".//PublicationTypeList/PublicationType"):
                pub_types.append(pt.text or "")

            affiliation = ""
            aff_elem = art.find(".//AuthorList/Author[1]/AffiliationInfo/Affiliation")
            if aff_elem is not None:
                affiliation = aff_elem.text or ""

            # PMC ID があれば取得
            pmc_id = ""
            for id_elem in article_elem.findall(".//ArticleId"):
                if id_elem.get("IdType") == "pmc":
                    pmc_id = id_elem.text or ""
                    break

            articles.append({
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "journal_abbr": journal_abbr,
                "year": year,
                "doi": doi,
                "pmc_id": pmc_id,
                "abstract": abstract,
                "mesh_terms": mesh_terms,
                "pub_types": pub_types,
                "affiliation": affiliation,
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        except Exception as e:
            print(f"  Warning: parse error for PMID: {e}", file=sys.stderr)
            continue

    return articles


def fetch_all(query_name: str, query_str: str, dry_run: bool = False) -> list:
    """1つのクエリの全結果を取得"""
    print(f"  {query_name}")
    print(f"    検索式: {query_str[:100]}...")

    count, webenv, query_key = esearch(query_str)
    print(f"    ヒット: {count:,} 件")

    if dry_run:
        return []

    all_articles = []
    for start in range(0, count, BATCH_SIZE):
        end = min(start + BATCH_SIZE, count)
        print(f"    取得中: {start+1}-{end} / {count}", end="", flush=True)

        try:
            xml_text = efetch_batch(webenv, query_key, start, BATCH_SIZE)
            batch = parse_articles(xml_text)
            all_articles.extend(batch)
            print(f"  -> {len(batch)} 件")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        time.sleep(REQUEST_INTERVAL)

    print(f"    完了: {len(all_articles)} 件")
    return all_articles


def deduplicate(all_articles: list) -> list:
    """PMIDで重複除去"""
    seen = set()
    unique = []
    for art in all_articles:
        if art["pmid"] and art["pmid"] not in seen:
            seen.add(art["pmid"])
            unique.append(art)
    return unique


def print_summary(unique: list):
    """サマリー表示"""
    journals = {}
    years = {}
    for art in unique:
        j = art["journal_abbr"] or art["journal"] or "Unknown"
        journals[j] = journals.get(j, 0) + 1
        y = art["year"] or "Unknown"
        years[y] = years.get(y, 0) + 1

    print(f"\n{'='*60}")
    print(f"ユニーク論文数: {len(unique):,}")
    print(f"掲載雑誌数: {len(journals):,}")

    valid_years = [y for y in years.keys() if y != "Unknown" and y.isdigit()]
    if valid_years:
        print(f"年範囲: {min(valid_years)} - {max(valid_years)}")

    with_abstract = sum(1 for a in unique if a["abstract"])
    print(f"アブストラクト取得率: {with_abstract:,}/{len(unique):,} "
          f"({100*with_abstract/max(len(unique),1):.1f}%)")

    with_mesh = sum(1 for a in unique if a["mesh_terms"])
    print(f"MeSH付与率: {with_mesh:,}/{len(unique):,} "
          f"({100*with_mesh/max(len(unique),1):.1f}%)")

    print(f"\n上位20雑誌:")
    for j, c in sorted(journals.items(), key=lambda x: -x[1])[:20]:
        print(f"  {c:5d}  {j}")

    # 年代別
    decades = {}
    for y, c in years.items():
        if y.isdigit():
            decade = f"{y[:3]}0s"
            decades[decade] = decades.get(decade, 0) + c
    print(f"\n年代別:")
    for d in sorted(decades.keys()):
        print(f"  {d}: {decades[d]:,} 件")


def main():
    parser = argparse.ArgumentParser(
        description="PubMed E-utilities: 日本発東洋医学研究の包括的取得"
    )
    parser.add_argument("--dry-run", action="store_true", help="件数確認のみ")
    parser.add_argument(
        "--layer", type=int, choices=[1, 2, 3],
        help="特定Layerのみ実行 (省略時: 全Layer)"
    )
    args = parser.parse_args()

    # 実行するLayerを決定
    if args.layer:
        layers = {args.layer: ALL_LAYERS[args.layer]}
    else:
        layers = ALL_LAYERS

    grand_total = 0
    all_articles = []

    for layer_num, queries in sorted(layers.items()):
        print(f"\n{'='*60}")
        print(f"Layer {layer_num}")
        print(f"{'='*60}")

        layer_articles = []
        for key, q in queries.items():
            articles = fetch_all(q["name"], q["query"], dry_run=args.dry_run)

            if not args.dry_run and articles:
                # 個別保存
                out_path = PUBMED_DIR / f"pubmed_{key}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                print(f"    保存: {out_path.name} ({len(articles)} 件)")

            layer_articles.extend(articles)
            time.sleep(REQUEST_INTERVAL)

        if not args.dry_run:
            layer_unique = deduplicate(layer_articles)
            print(f"\n  Layer {layer_num} 小計: {len(layer_articles)} -> "
                  f"重複除去: {len(layer_unique)}")

            # Layer別保存
            layer_path = PUBMED_DIR / f"pubmed_layer{layer_num}.json"
            with open(layer_path, "w", encoding="utf-8") as f:
                json.dump(layer_unique, f, ensure_ascii=False, indent=2)

        all_articles.extend(layer_articles)

    if args.dry_run:
        print(f"\n{'='*60}")
        print("dry-run 完了")
        return

    # 全Layer統合
    unique = deduplicate(all_articles)
    print(f"\n{'='*60}")
    print(f"全Layer合計: {len(all_articles):,} 件")
    print(f"重複除去後: {len(unique):,} 件")

    # タグ付け: 各論文がどのLayerに該当するか記録
    pmid_to_layers = {}
    for layer_num, queries in ALL_LAYERS.items():
        if layer_num not in layers:
            continue
        for key, q in queries.items():
            layer_path = PUBMED_DIR / f"pubmed_{key}.json"
            if layer_path.exists():
                with open(layer_path, encoding="utf-8") as f:
                    for art in json.load(f):
                        pmid = art["pmid"]
                        if pmid not in pmid_to_layers:
                            pmid_to_layers[pmid] = set()
                        pmid_to_layers[pmid].add(f"L{layer_num}")
                        pmid_to_layers[pmid].add(key)

    for art in unique:
        tags = pmid_to_layers.get(art["pmid"], set())
        art["search_layers"] = sorted(tags)

    # 統合ファイル保存
    merged_path = PUBMED_DIR / "pubmed_all_merged.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"\n統合ファイル: {merged_path}")

    print_summary(unique)


if __name__ == "__main__":
    main()
