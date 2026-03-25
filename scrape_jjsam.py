# -*- coding: utf-8 -*-
"""
scrape_jjsam.py - Scrape 全日本鍼灸学会雑誌 from J-STAGE
Step 1: Metadata via API (cdjournal=jjsam)
Step 2: Abstracts via HTML scraping
"""
import json
import time
import re
import sys
import os
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

JSTAGE_API_URL = "https://api.jstage.jst.go.jp/searchapi/do"
CDJOURNAL = "jjsam"
REQUEST_INTERVAL = 1.5

METADATA_PATH = os.path.join(DATA_DIR, "jjsam_metadata.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "jjsam_with_abstracts.json")
PROGRESS_PATH = os.path.join(DATA_DIR, "jjsam_scrape_progress.json")

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
}
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def text(el):
    return el.text.strip() if el is not None and el.text else ""


def find_no_ns(parent, tag):
    el = parent.find(tag)
    if el is not None:
        return el
    return parent.find(f"{ATOM_NS}{tag}")


def parse_entry(entry):
    title_ja = ""
    title_en = ""
    at = find_no_ns(entry, "article_title")
    if at is not None:
        title_ja = text(find_no_ns(at, "ja"))
        title_en = text(find_no_ns(at, "en"))
    if not title_ja:
        title_ja = text(entry.find("atom:title", NS))

    authors_ja = []
    authors_en = []
    author_el = find_no_ns(entry, "author")
    if author_el is not None:
        for lang, lst in [("ja", authors_ja), ("en", authors_en)]:
            block = find_no_ns(author_el, lang)
            if block is not None:
                for name_el in block.findall("name"):
                    n = text(name_el)
                    if n:
                        lst.append(n)
                if not lst:
                    for name_el in block:
                        if "name" in name_el.tag:
                            n = text(name_el)
                            if n:
                                lst.append(n)
    if not authors_ja:
        for a in entry.findall("atom:author", NS):
            n = text(a.find("atom:name", NS))
            if n:
                authors_ja.append(n)

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
    if not link_url:
        for link_el in entry.findall("atom:link", NS):
            href = link_el.get("href", "")
            if href:
                link_url = href
                break

    return {
        "title_ja": title_ja,
        "title_en": title_en,
        "authors_ja": authors_ja,
        "authors_en": authors_en,
        "doi": text(entry.find("prism:doi", NS)),
        "volume": text(entry.find("prism:volume", NS)),
        "number": text(entry.find("prism:number", NS)),
        "starting_page": text(entry.find("prism:startingPage", NS)),
        "ending_page": text(entry.find("prism:endingPage", NS)),
        "pubyear": text(find_no_ns(entry, "pubyear")),
        "journal": "全日本鍼灸学会雑誌",
        "link": link_url,
        "entry_id": text(entry.find("atom:id", NS)),
        "abstract_ja": "",
        "abstract_en": "",
        "cdjournal": "jjsam",
    }


def scrape_metadata():
    all_articles = []
    start = 1
    count = 100
    total = None
    print(f"J-STAGE API: cdjournal={CDJOURNAL}")
    while True:
        print(f"  Fetching start={start}...", end="")
        params = {"service": "3", "cdjournal": CDJOURNAL, "start": str(start), "count": str(count)}
        try:
            resp = requests.get(JSTAGE_API_URL, params=params, timeout=30)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as e:
            print(f" Error: {e}")
            break

        if total is None:
            total_el = root.find(".//opensearch:totalResults", {"opensearch": "http://a9.com/-/spec/opensearch/1.1/"})
            total = int(total_el.text) if total_el is not None and total_el.text else 0
            print(f" (total: {total})")
        else:
            print()

        entries = root.findall(".//atom:entry", NS)
        if not entries:
            break

        for entry in entries:
            art = parse_entry(entry)
            if art:
                all_articles.append(art)

        if len(all_articles) >= total:
            break
        start += count
        time.sleep(REQUEST_INTERVAL)

    print(f"Metadata: {len(all_articles)} articles")
    return all_articles


def scrape_abstract(url):
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "KampoEvidenceMap/1.0 (academic research)"})
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        abstract_ja = ""
        abstract_en = ""

        meta_abs = soup.find("meta", attrs={"name": "abstract"})
        if meta_abs and meta_abs.get("content", "").strip():
            txt = meta_abs["content"].strip()
            if re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', txt):
                abstract_ja = txt
            else:
                abstract_en = txt

        if not abstract_en:
            meta_cit = soup.find("meta", attrs={"name": "citation_abstract"})
            if meta_cit and meta_cit.get("content", "").strip():
                txt = meta_cit["content"].strip()
                if not re.search(r'[\u3040-\u309f\u30a0-\u30ff]', txt):
                    abstract_en = txt

        if not abstract_ja and not abstract_en:
            wrap = soup.find(id="article-overiew-abstract-wrap")
            if wrap:
                for div in wrap.find_all("div"):
                    txt = div.get_text(strip=True)
                    if txt and txt not in ("抄録", "Abstract"):
                        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', txt):
                            if not abstract_ja:
                                abstract_ja = txt
                        else:
                            if not abstract_en:
                                abstract_en = txt

        return abstract_ja, abstract_en
    except Exception:
        return "", ""


def scrape_abstracts(articles):
    total = len(articles)
    start_idx = 0

    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            progress = json.load(f)
        start_idx = progress.get("last_completed", 0)
        if os.path.exists(OUTPUT_PATH):
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
        print(f"Resuming from {start_idx}/{total}")

    print(f"Abstract scraping: {total} articles")
    print(f"Estimated time: ~{int(total * REQUEST_INTERVAL / 60)} min")

    found = 0
    for i in range(start_idx, total):
        art = articles[i]
        url = art.get("link", "")
        if not url:
            continue
        if art.get("abstract_ja") or art.get("abstract_en"):
            found += 1
            continue

        abs_ja, abs_en = scrape_abstract(url)
        art["abstract_ja"] = abs_ja
        art["abstract_en"] = abs_en
        if abs_ja or abs_en:
            found += 1

        if (i + 1) % 20 == 0 or i == total - 1:
            pct = (i + 1) / total * 100
            print(f"  [{i+1}/{total}] {pct:.1f}% | abstracts: {found} | {art.get('title_ja','')[:40]}")
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump({"last_completed": i + 1, "abstracts_found": found}, f)

        time.sleep(REQUEST_INTERVAL)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    if os.path.exists(PROGRESS_PATH):
        os.unlink(PROGRESS_PATH)

    print(f"\nDone! Abstracts found: {found}/{total}")
    return articles


if __name__ == "__main__":
    # Step 1: Metadata
    if not os.path.exists(METADATA_PATH):
        articles = scrape_metadata()
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"Saved: {METADATA_PATH}")
    else:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)
        print(f"Loaded existing: {METADATA_PATH} ({len(articles)} articles)")

    # Step 2: Abstracts
    articles = scrape_abstracts(articles)

    # Summary
    years = {}
    for a in articles:
        y = str(a.get("pubyear", ""))[:4]
        if y:
            years[y] = years.get(y, 0) + 1
    print("\nYear distribution:")
    for y in sorted(years.keys()):
        print(f"  {y}: {years[y]}")
    abs_count = sum(1 for a in articles if a.get("abstract_ja") or a.get("abstract_en"))
    print(f"\nWith abstract: {abs_count}/{len(articles)}")
