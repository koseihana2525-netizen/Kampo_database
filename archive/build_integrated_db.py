# -*- coding: utf-8 -*-
"""
build_integrated_db.py — 日本語誌 + PubMed 統合データベース構築

出力: data/integrated_db.json
  - stats: 統計サマリー
  - articles: 全論文 (日本語誌 + PubMed)
  - categories: カテゴリ別集計
  - yearly: 年別×ソース別集計
  - design: 研究デザイン集計
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import DATA_DIR, OUTPUT_DIR

def main():
    # === データ読み込み ===
    with open(OUTPUT_DIR / "kampo_db_v3.json", encoding="utf-8") as f:
        jp_db = json.load(f)
    jp_articles = jp_db["articles"]

    with open(DATA_DIR / "pubmed" / "pubmed_tagged.json", encoding="utf-8") as f:
        pm_articles = json.load(f)

    # === 統合論文リスト ===
    integrated = []

    # 日本語誌
    for a in jp_articles:
        source = "kampo" if a.get("j") == "漢方" else "acupuncture"
        integrated.append({
            "id": f"jp_{len(integrated)}",
            "title": a.get("t", ""),
            "year": a.get("y", ""),
            "authors": a.get("a", ""),
            "journal": "日本東洋医学雑誌" if source == "kampo" else "全日本鍼灸学会雑誌",
            "journal_short": "東洋医学" if source == "kampo" else "鍼灸学会",
            "link": a.get("l", ""),
            "abstract": a.get("ab", ""),
            "categories": a.get("c", []),
            "formulas": a.get("f", []),
            "source": source,
            "lang": "ja",
            "pub_types": [],
            "mesh": [],
        })

    # PubMed
    for a in pm_articles:
        # ソース分類
        layers = set(t[0:2] for t in a.get("search_layers", []) if t.startswith("L"))
        if "L2" in layers and "L1" not in layers:
            source = "pubmed_acupuncture"
        elif "L1" in layers:
            source = "pubmed_kampo"
        else:
            source = "pubmed_pharma"

        integrated.append({
            "id": f"pm_{a.get('pmid', '')}",
            "title": a.get("title", ""),
            "year": a.get("year", ""),
            "authors": ", ".join(a.get("authors", [])[:3]),
            "journal": a.get("journal", ""),
            "journal_short": a.get("journal_abbr", ""),
            "link": a.get("pubmed_url", ""),
            "abstract": a.get("abstract", "") or "",
            "categories": a.get("disease_categories", []),
            "formulas": [],
            "source": source,
            "lang": "en",
            "pub_types": a.get("pub_types", []),
            "mesh": a.get("mesh_terms", [])[:10],
        })

    # === カテゴリ別集計 ===
    cat_stats = defaultdict(lambda: {
        "kampo": 0, "acupuncture": 0,
        "pubmed_kampo": 0, "pubmed_acupuncture": 0, "pubmed_pharma": 0,
        "total": 0,
    })
    for a in integrated:
        for cat in a["categories"]:
            cat_stats[cat][a["source"]] += 1
            cat_stats[cat]["total"] += 1

    # === 年別集計 ===
    yearly = defaultdict(lambda: {
        "kampo": 0, "acupuncture": 0,
        "pubmed_kampo": 0, "pubmed_acupuncture": 0, "pubmed_pharma": 0,
    })
    for a in integrated:
        y = a["year"]
        if y and y.isdigit():
            yearly[y][a["source"]] += 1

    # === 研究デザイン ===
    design_counts = Counter()
    for a in integrated:
        if a["lang"] == "en":
            for pt in a["pub_types"]:
                if pt in ("Randomized Controlled Trial", "Systematic Review",
                          "Meta-Analysis", "Case Reports", "Clinical Trial",
                          "Observational Study", "Review"):
                    design_counts[pt] += 1
        else:
            design_counts["Case Report (JP)"] += 1

    # === 上位雑誌 ===
    journal_counts = Counter()
    for a in integrated:
        j = a["journal_short"] or a["journal"]
        if j:
            journal_counts[j] += 1

    # === 統計サマリー ===
    source_counts = Counter(a["source"] for a in integrated)
    stats = {
        "total": len(integrated),
        "jp_kampo": source_counts.get("kampo", 0),
        "jp_acupuncture": source_counts.get("acupuncture", 0),
        "pm_kampo": source_counts.get("pubmed_kampo", 0),
        "pm_acupuncture": source_counts.get("pubmed_acupuncture", 0),
        "pm_pharma": source_counts.get("pubmed_pharma", 0),
        "jp_total": source_counts.get("kampo", 0) + source_counts.get("acupuncture", 0),
        "pm_total": (source_counts.get("pubmed_kampo", 0) +
                     source_counts.get("pubmed_acupuncture", 0) +
                     source_counts.get("pubmed_pharma", 0)),
        "categories": len(cat_stats),
        "journals": len(journal_counts),
        "year_min": min(y for y in yearly.keys() if y.isdigit()),
        "year_max": max(y for y in yearly.keys() if y.isdigit()),
        "with_abstract": sum(1 for a in integrated if a["abstract"]),
    }

    # === 出力 ===
    db = {
        "stats": stats,
        "articles": integrated,
        "categories": {k: v for k, v in sorted(cat_stats.items(), key=lambda x: -x[1]["total"])},
        "yearly": dict(sorted(yearly.items())),
        "design": dict(design_counts.most_common()),
        "top_journals": dict(journal_counts.most_common(30)),
    }

    out_path = DATA_DIR / "integrated_db.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

    print(f"統合DB: {out_path}")
    print(f"総論文数: {stats['total']}")
    print(f"  日本語誌: {stats['jp_total']} (漢方{stats['jp_kampo']}, 鍼灸{stats['jp_acupuncture']})")
    print(f"  PubMed: {stats['pm_total']} (漢方{stats['pm_kampo']}, 鍼灸{stats['pm_acupuncture']}, 薬学{stats['pm_pharma']})")
    print(f"カテゴリ数: {stats['categories']}")
    print(f"雑誌数: {stats['journals']}")
    print(f"年範囲: {stats['year_min']}-{stats['year_max']}")

    # ファイルサイズ
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"ファイルサイズ: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
