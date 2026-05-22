"""
Duagnosis Kampo KB - J-STAGEメタデータ取得スクリプト
日本東洋医学雑誌（ISSN: 0287-4857）の論文メタデータをJ-STAGE WebAPIから取得

Usage:
    python scraper.py                          # 2020-2025年のメタデータを取得
    python scraper.py --year-from 2015 --year-to 2025  # 年範囲指定
    python scraper.py --all                    # 全年取得
"""

import argparse
import json
import time
import sys
from xml.etree import ElementTree as ET

import requests

from config import JSTAGE_API_URL, JSTAGE_ISSN, JSTAGE_REQUEST_INTERVAL, METADATA_PATH


# J-STAGE WebAPI の名前空間
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def fetch_articles(issn, pubyearfrom=None, pubyearto=None, start=1, count=100):
    """J-STAGE WebAPIから論文メタデータを取得"""
    params = {
        "service": "3",
        "issn": issn,
        "start": str(start),
        "count": str(count),
    }
    if pubyearfrom:
        params["pubyearfrom"] = str(pubyearfrom)
    if pubyearto:
        params["pubyearto"] = str(pubyearto)

    resp = requests.get(JSTAGE_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    # J-STAGEはUTF-8で返すが、requestsがISO-8859-1と誤判定するため
    # バイト列を直接返す
    return resp.content


def parse_response(xml_bytes):
    """XMLレスポンスをパースして論文メタデータのリストを返す"""
    root = ET.fromstring(xml_bytes)

    # 総件数
    total_el = root.find("opensearch:totalResults", NS)
    total_results = int(total_el.text) if total_el is not None and total_el.text else 0

    articles = []
    for entry in root.findall("atom:entry", NS):
        article = parse_entry(entry)
        if article:
            articles.append(article)

    return articles, total_results


def parse_entry(entry):
    """1つのentryからメタデータを抽出

    J-STAGE XMLの構造:
    - article_title/ja, article_title/en: Atom名前空間外の独自タグ
    - author/ja/name, author/en/name: ネスト構造
    - pubyear: Atom名前空間外
    - prism:volume, prism:doi 等: PRISM名前空間
    - atom:title, atom:link: Atom名前空間（フォールバック用）
    """
    ATOM_NS = "{http://www.w3.org/2005/Atom}"

    def text(el):
        return el.text.strip() if el is not None and el.text else ""

    def find_no_ns(parent, tag):
        """名前空間なしのタグを検索（J-STAGE独自タグ用）"""
        # まず名前空間なしで試す
        el = parent.find(tag)
        if el is not None:
            return el
        # Atom名前空間付きで試す
        el = parent.find(f"{ATOM_NS}{tag}")
        return el

    # ── タイトル（article_title/ja, article_title/en） ──
    title_ja = ""
    title_en = ""
    at = find_no_ns(entry, "article_title")
    if at is not None:
        ja_el = find_no_ns(at, "ja")
        en_el = find_no_ns(at, "en")
        title_ja = text(ja_el)
        title_en = text(en_el)
    # フォールバック: atom:title
    if not title_ja:
        title_el = entry.find("atom:title", NS)
        if title_el is not None:
            title_ja = text(title_el)

    # ── 著者（author/ja/name, author/en/name） ──
    authors_ja = []
    authors_en = []
    author_el = find_no_ns(entry, "author")
    if author_el is not None:
        ja_block = find_no_ns(author_el, "ja")
        if ja_block is not None:
            for name_el in ja_block.findall("name"):
                n = text(name_el)
                if n:
                    authors_ja.append(n)
            if not authors_ja:
                for name_el in ja_block:
                    if name_el.tag.endswith("name") or "name" in name_el.tag:
                        n = text(name_el)
                        if n:
                            authors_ja.append(n)
        en_block = find_no_ns(author_el, "en")
        if en_block is not None:
            for name_el in en_block.findall("name"):
                n = text(name_el)
                if n:
                    authors_en.append(n)
            if not authors_en:
                for name_el in en_block:
                    if name_el.tag.endswith("name") or "name" in name_el.tag:
                        n = text(name_el)
                        if n:
                            authors_en.append(n)
    # フォールバック: atom:author
    if not authors_ja:
        for a in entry.findall("atom:author", NS):
            name_el = a.find("atom:name", NS)
            n = text(name_el)
            if n:
                authors_ja.append(n)

    # ── リンク（article_link/ja） ──
    link_url = ""
    al = find_no_ns(entry, "article_link")
    if al is not None:
        ja_link = find_no_ns(al, "ja")
        if ja_link is not None:
            link_url = text(ja_link)
        if not link_url:
            en_link = find_no_ns(al, "en")
            if en_link is not None:
                link_url = text(en_link)
    # フォールバック: atom:link
    if not link_url:
        for link_el in entry.findall("atom:link", NS):
            href = link_el.get("href", "")
            if href:
                link_url = href
                break

    # ── DOI ──
    doi_el = entry.find("prism:doi", NS)
    doi = text(doi_el)

    # ── 巻・号・ページ ──
    volume = text(entry.find("prism:volume", NS))
    number = text(entry.find("prism:number", NS))
    starting_page = text(entry.find("prism:startingPage", NS))
    ending_page = text(entry.find("prism:endingPage", NS))

    # ── 発行年（pubyear: 名前空間なし独自タグ） ──
    pubyear_el = find_no_ns(entry, "pubyear")
    pubyear = text(pubyear_el)

    # ── 雑誌名 ──
    journal_title = ""
    mt = find_no_ns(entry, "material_title")
    if mt is not None:
        ja_mt = find_no_ns(mt, "ja")
        journal_title = text(ja_mt)

    # ── cdjournal ──
    cdj = find_no_ns(entry, "cdjournal")
    cdjournal = text(cdj)

    # ── ID ──
    entry_id = text(entry.find("atom:id", NS))

    # ── 抄録（J-STAGE APIではservice=3で抄録は返らないことが多い） ──
    abstract_ja = ""
    abstract_en = ""

    return {
        "title_ja": title_ja,
        "title_en": title_en,
        "authors_ja": authors_ja,
        "authors_en": authors_en,
        "doi": doi,
        "volume": volume,
        "number": number,
        "starting_page": starting_page,
        "ending_page": ending_page,
        "pubyear": pubyear,
        "journal": journal_title or "日本東洋医学雑誌",
        "link": link_url,
        "entry_id": entry_id,
        "abstract_ja": abstract_ja,
        "abstract_en": abstract_en,
        "cdjournal": cdjournal,
    }


def scrape_metadata(issn, year_from=None, year_to=None):
    """全論文メタデータをページネーションしながら取得"""
    all_articles = []
    start = 1
    count = 100
    total = None

    print(f"J-STAGE WebAPI: ISSN={issn}")
    if year_from or year_to:
        print(f"  対象期間: {year_from or '---'} 〜 {year_to or '---'}")

    while True:
        print(f"  取得中... start={start}, count={count}", end="")
        try:
            xml_text = fetch_articles(issn, year_from, year_to, start, count)
            articles, total_results = parse_response(xml_text)
        except requests.RequestException as e:
            print(f" エラー: {e}")
            break
        except ET.ParseError as e:
            print(f" XMLパースエラー: {e}")
            break

        if total is None:
            total = total_results
            print(f" (総件数: {total})")
        else:
            print(f" ({len(articles)}件)")

        if not articles:
            break

        all_articles.extend(articles)

        if len(all_articles) >= total:
            break

        start += count
        time.sleep(JSTAGE_REQUEST_INTERVAL)

    print(f"\n取得完了: {len(all_articles)}件")
    return all_articles


def save_metadata(articles, path):
    """メタデータをJSONで保存"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"保存: {path} ({len(articles)}件)")


def load_metadata(path=None):
    """保存済みメタデータを読み込み"""
    path = path or METADATA_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="J-STAGE 日本東洋医学雑誌 メタデータ取得")
    parser.add_argument("--year-from", type=int, default=2020, help="開始年 (default: 2020)")
    parser.add_argument("--year-to", type=int, default=2025, help="終了年 (default: 2025)")
    parser.add_argument("--all", action="store_true", help="全年取得")
    parser.add_argument("--output", type=str, default=None, help="出力ファイルパス")
    args = parser.parse_args()

    year_from = None if args.all else args.year_from
    year_to = None if args.all else args.year_to
    output_path = args.output or str(METADATA_PATH)

    articles = scrape_metadata(JSTAGE_ISSN, year_from, year_to)

    if articles:
        save_metadata(articles, output_path)

        # サマリー表示
        years = [a["pubyear"] for a in articles if a["pubyear"]]
        if years:
            year_counts = {}
            for y in years:
                yr = y[:4] if len(y) >= 4 else y
                year_counts[yr] = year_counts.get(yr, 0) + 1
            print("\n年別件数:")
            for yr in sorted(year_counts.keys()):
                print(f"  {yr}: {year_counts[yr]}件")

        abstracts = [a for a in articles if a["abstract_ja"] or a["abstract_en"]]
        print(f"\n抄録あり: {len(abstracts)}/{len(articles)}件")
    else:
        print("論文が取得できませんでした。")
        sys.exit(1)


if __name__ == "__main__":
    main()
