"""
J-STAGE論文ページから抄録をスクレイピング
metadata.jsonの各論文のlinkにアクセスして抄録を取得

Usage:
    python scrape_abstracts.py
"""

import json
import time
import re
import sys

import requests
from bs4 import BeautifulSoup

from config import DATA_DIR, JSTAGE_REQUEST_INTERVAL

METADATA_PATH = DATA_DIR / "metadata.json"
OUTPUT_PATH = DATA_DIR / "metadata_with_abstracts.json"
PROGRESS_PATH = DATA_DIR / "scrape_progress.json"


def scrape_abstract(url):
    """1論文ページから抄録を取得"""
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "DuagnosisKampoKB/1.0 (academic research)"
        })
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        abstract_ja = ""
        abstract_en = ""

        # パターン0: <meta name="abstract"> — 最も確実（J-STAGE標準）
        meta_abs = soup.find("meta", attrs={"name": "abstract"})
        if meta_abs and meta_abs.get("content", "").strip():
            text = meta_abs["content"].strip()
            if re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', text):
                abstract_ja = text
            else:
                abstract_en = text

        # 英語抄録も別途取得（meta name="description" は使えないが、
        # citation_abstract があれば取る）
        if not abstract_en:
            meta_cit = soup.find("meta", attrs={"name": "citation_abstract"})
            if meta_cit and meta_cit.get("content", "").strip():
                text = meta_cit["content"].strip()
                if not re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                    abstract_en = text

        # パターン1: id="article-overiew-abstract-wrap"（フォールバック）
        if not abstract_ja and not abstract_en:
            wrap = soup.find(id="article-overiew-abstract-wrap")
            if wrap:
                for div in wrap.find_all("div"):
                    text = div.get_text(strip=True)
                    if text and text not in ("抄録", "Abstract"):
                        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                            if not abstract_ja:
                                abstract_ja = text
                        else:
                            if not abstract_en:
                                abstract_en = text

        return abstract_ja, abstract_en

    except Exception as e:
        return "", ""


def main():
    # メタデータ読み込み
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    total = len(articles)

    # 進捗復元（中断からの再開対応）
    start_idx = 0
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            progress = json.load(f)
        start_idx = progress.get("last_completed", 0)
        # 既に取得済みの抄録を復元
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
        print(f"前回の続きから再開: {start_idx}/{total}")

    print(f"抄録スクレイピング開始: {total}件")
    print(f"予想時間: 約{int(total * JSTAGE_REQUEST_INTERVAL / 60)}分")

    abstracts_found = 0
    for i in range(start_idx, total):
        art = articles[i]
        url = art.get("link", "")
        if not url:
            continue

        # 既に抄録がある場合はスキップ
        if art.get("abstract_ja") or art.get("abstract_en"):
            abstracts_found += 1
            continue

        abs_ja, abs_en = scrape_abstract(url)
        art["abstract_ja"] = abs_ja
        art["abstract_en"] = abs_en

        if abs_ja or abs_en:
            abstracts_found += 1

        # 進捗表示（20件ごと）
        if (i + 1) % 20 == 0 or i == total - 1:
            pct = (i + 1) / total * 100
            print(f"  [{i+1}/{total}] {pct:.1f}% | 抄録あり: {abstracts_found} | {art.get('title_ja','')[:30]}")

            # 中間保存（20件ごと）
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump({"last_completed": i + 1, "abstracts_found": abstracts_found}, f)

        time.sleep(JSTAGE_REQUEST_INTERVAL)

    # 最終保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    # 進捗ファイル削除
    if PROGRESS_PATH.exists():
        PROGRESS_PATH.unlink()

    print(f"\n完了！ 抄録あり: {abstracts_found}/{total}件")
    print(f"保存: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
