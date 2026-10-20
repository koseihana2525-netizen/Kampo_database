# -*- coding: utf-8 -*-
"""
update_jstage.py - J-STAGE 差分取得

data/merged_metadata.json に無い新着記事だけを J-STAGE API から取得して追記する。
抄録は新着記事（と、直近の抄録未取得記事）のページだけをスクレイピングする。

Usage:
    python update_jstage.py              # 直近2年分を確認して追記
    python update_jstage.py --years 3    # 遡る年数を変更
    python update_jstage.py --dry-run    # 件数のみ表示（ファイルは変更しない）
"""

import argparse
import datetime
import json
import time
from xml.etree import ElementTree as ET

import requests

import scrape_jjsam as sj
from config import DATA_DIR, JSTAGE_API_URL, JSTAGE_ISSN

MERGED_PATH = DATA_DIR / "merged_metadata.json"

# 取得対象誌。api は J-STAGE WebAPI の絞り込みパラメータ（過去の取得時と同じ指定）
JOURNALS = {
    "kampomed": {"name": "日本東洋医学雑誌", "api": {"issn": JSTAGE_ISSN}},
    "jjsam": {"name": "全日本鍼灸学会雑誌", "api": {"cdjournal": "jjsam"}},
}

PAGE_SIZE = 100
MAX_RETRIES = 3
ABSTRACT_BACKFILL_YEARS = 1   # 抄録が空の記事を再取得する範囲（今年と前年）


def _get(params: dict) -> requests.Response:
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(JSTAGE_API_URL, params=params, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"J-STAGE API への接続に失敗（{MAX_RETRIES}回試行）: {last_err}")


def parse_journal_entry(entry, journal_name: str, default_cdjournal: str) -> dict:
    """Atom エントリを merged_metadata.json と同じ形式の辞書に変換する"""
    art = sj.parse_entry(entry)
    art["journal"] = journal_name
    cdj = sj.text(sj.find_no_ns(entry, "cdjournal"))
    art["cdjournal"] = cdj or default_cdjournal
    return art


def fetch_journal(key: str, year_from: int) -> list:
    """1誌ぶんの記事メタデータを year_from 年以降について全ページ取得する"""
    cfg = JOURNALS[key]
    articles = []
    total = None
    start = 1
    while True:
        params = {"service": "3", "start": str(start), "count": str(PAGE_SIZE),
                  "pubyearfrom": str(year_from), **cfg["api"]}
        root = ET.fromstring(_get(params).content)
        if total is None:
            el = root.find(".//opensearch:totalResults", sj.NS)
            total = int(el.text) if el is not None and el.text else 0
        entries = root.findall(".//atom:entry", sj.NS)
        if not entries:
            break
        for entry in entries:
            art = parse_journal_entry(entry, cfg["name"], key)
            if art:
                articles.append(art)
        if len(articles) >= total:
            break
        start += PAGE_SIZE
        time.sleep(sj.REQUEST_INTERVAL)
    if len(articles) < total:
        raise RuntimeError(f"{cfg['name']}: 取得 {len(articles)} 件 < API報告の {total} 件")
    return articles


def known_keys(records: list) -> set:
    """既存記事の識別子（entry_id / link / doi）の集合"""
    keys = set()
    for r in records:
        for k in ("entry_id", "link", "doi"):
            if r.get(k):
                keys.add(r[k])
    return keys


def select_new(fetched: list, known: set) -> list:
    """既存に無い記事だけを返す。識別子のどれかが既知なら既存扱い。取得内の重複も除く"""
    new, seen = [], set(known)
    for art in fetched:
        ids = [art.get(k) for k in ("entry_id", "link", "doi") if art.get(k)]
        if not ids or any(i in seen for i in ids):
            continue
        seen.update(ids)
        new.append(art)
    return new


def fill_abstract(art: dict) -> bool:
    abs_ja, abs_en = sj.scrape_abstract(art.get("link", ""))
    art["abstract_ja"], art["abstract_en"] = abs_ja, abs_en
    time.sleep(sj.REQUEST_INTERVAL)
    return bool(abs_ja or abs_en)


def main():
    parser = argparse.ArgumentParser(description="J-STAGE 差分取得")
    parser.add_argument("--years", type=int, default=2, help="遡る年数（既定: 今年と前年）")
    parser.add_argument("--dry-run", action="store_true", help="件数のみ表示")
    args = parser.parse_args()

    this_year = datetime.date.today().year
    year_from = this_year - (args.years - 1)

    with open(MERGED_PATH, encoding="utf-8") as f:
        records = json.load(f)
    known = known_keys(records)
    print(f"既存: {len(records):,} 件 / {year_from}年以降を確認")

    added = []
    for key in JOURNALS:
        fetched = fetch_journal(key, year_from)
        new = select_new(fetched, known | known_keys(added))
        print(f"  {JOURNALS[key]['name']}: API {len(fetched)} 件 → 新着 {len(new)} 件")
        added.extend(new)

    # 抄録の再取得対象: 直近年で抄録が空の既存記事（掲載直後は抄録が未公開のことがある）
    backfill = [r for r in records
                if str(r.get("pubyear", "")).isdigit()
                and int(r["pubyear"]) >= this_year - ABSTRACT_BACKFILL_YEARS
                and not (r.get("abstract_ja") or r.get("abstract_en"))]
    print(f"抄録の再取得対象: {len(backfill)} 件")

    if args.dry_run:
        return

    got_new = sum(fill_abstract(a) for a in added)
    got_back = sum(fill_abstract(r) for r in backfill)
    print(f"抄録取得: 新着 {got_new}/{len(added)} 件、再取得 {got_back}/{len(backfill)} 件")

    if added or got_back:
        records.extend(added)
        with open(MERGED_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"保存: {MERGED_PATH.name}（{len(records):,} 件）")
    else:
        print("変更なし")


if __name__ == "__main__":
    main()
