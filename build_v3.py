# -*- coding: utf-8 -*-
"""
build_v3.py - Build Kampo Evidence Map v3
3-layer category UI + author search + standalone HTML
"""
import json
import os
import re
from collections import Counter, OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load data ──
MERGED_PATH = os.path.join(BASE_DIR, "data/merged_metadata.json")
LEGACY_PATH = os.path.join(BASE_DIR, "data/metadata_with_abstracts.json")
INPUT_PATH = MERGED_PATH if os.path.exists(MERGED_PATH) else LEGACY_PATH

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    articles = json.load(f)
print(f"Loaded {len(articles)} articles from {os.path.basename(INPUT_PATH)}")

with open(os.path.join(BASE_DIR, "data/categories_v2.json"), "r", encoding="utf-8") as f:
    categories_v2 = json.load(f)

from dictionaries import FORMULAS, EXTRA_FORMULAS

# ── Build formula info ──
formula_info = {}
for k, v in FORMULAS.items():
    formula_info[v["name"]] = {"origin": v.get("origin", ""), "number": str(k), "yomi": v.get("yomi", "")}
for k, v in EXTRA_FORMULAS.items():
    formula_info[v["name"]] = {"origin": v.get("origin", ""), "number": str(v.get("number", "")), "yomi": v.get("yomi", "")}

all_formula_names = sorted(formula_info.keys(), key=len, reverse=True)

def extract_formulas(text):
    found = []
    remaining = text
    for name in all_formula_names:
        if name in remaining:
            found.append(name)
            remaining = remaining.replace(name, chr(0) * len(name))
    return found

# ── Build flat keyword map from categories_v2 ──
# lv3_name -> {keywords, path: [lv1, lv2, lv3]}
lv3_keyword_map = {}
for lv1 in categories_v2:
    for lv2 in lv1["children"]:
        for lv3 in lv2["children"]:
            lv3_keyword_map[lv3["name"]] = {
                "keywords": lv3["keywords"],
                "path": [lv1["name"], lv2["name"], lv3["name"]],
            }

# ── Process articles ──
structured = []
author_index = {}  # author_name -> [article_indices]

for i, a in enumerate(articles):
    title = a.get("title_ja", "") or ""
    abstract = a.get("abstract_ja", "") or ""
    combined = title + " " + abstract
    year = str(a.get("pubyear", ""))[:4]
    formulas = extract_formulas(combined)

    # Category matching: find all lv3 categories
    matched_categories = []
    for lv3_name, info in lv3_keyword_map.items():
        if any(kw in combined for kw in info["keywords"]):
            matched_categories.append(lv3_name)

    # Author extraction
    authors_raw = a.get("authors_ja", "")
    if isinstance(authors_raw, list):
        author_names = authors_raw
    elif isinstance(authors_raw, str) and authors_raw:
        author_names = [x.strip() for x in re.split(r'[,、，]', authors_raw) if x.strip()]
    else:
        author_names = []

    # Clean author names (remove spaces between family/given name for indexing)
    clean_authors = []
    for name in author_names:
        clean = name.replace(" ", "").replace("　", "")
        if clean:
            clean_authors.append(clean)
            author_index.setdefault(clean, []).append(i)

    # Journal source
    cdj = a.get("cdjournal", "")
    journal_short = "鍼灸" if cdj == "jjsam" else "漢方"

    structured.append({
        "t": title,  # short keys to save space
        "y": year,
        "a": ", ".join(author_names) if author_names else "",
        "l": a.get("link", ""),
        "ab": abstract[:500] if abstract else "",
        "f": formulas,
        "c": matched_categories,  # lv3 category names
        "j": journal_short,  # journal source
    })

# ── Build indices ──
formula_index = {}
for i, s in enumerate(structured):
    for f in s["f"]:
        formula_index.setdefault(f, []).append(i)

category_index = {}  # lv3_name -> [article indices]
for i, s in enumerate(structured):
    for c in s["c"]:
        category_index.setdefault(c, []).append(i)

# ── Formula summary ──
formula_summary = {}
for fname in sorted(formula_index.keys(), key=lambda x: -len(formula_index[x])):
    indices = formula_index[fname]
    info = formula_info.get(fname, {})
    cat_counter = Counter()
    for idx in indices:
        for c in structured[idx]["c"]:
            cat_counter[c] += 1
    formula_summary[fname] = {
        "n": len(indices),
        "o": info.get("origin", ""),
        "y": info.get("yomi", ""),
        "num": info.get("number", ""),
        "top": cat_counter.most_common(5),
    }

# ── Category tree with article counts (recalculated from actual matches) ──
cat_tree = []
for lv1 in categories_v2:
    lv1_obj = {"name": lv1["name"], "children": []}
    lv1_articles = set()
    for lv2 in lv1["children"]:
        lv2_obj = {"name": lv2["name"], "children": []}
        lv2_articles = set()
        for lv3 in lv2["children"]:
            indices = category_index.get(lv3["name"], [])
            lv3_obj = {"name": lv3["name"], "count": len(indices)}
            lv2_articles.update(indices)
            lv2_obj["children"].append(lv3_obj)
        lv2_obj["count"] = len(lv2_articles)
        lv1_articles.update(lv2_articles)
        lv1_obj["children"].append(lv2_obj)
    lv1_obj["count"] = len(lv1_articles)
    cat_tree.append(lv1_obj)

# ── Top authors ──
top_authors = sorted(author_index.items(), key=lambda x: -len(x[1]))[:200]
author_data = {name: indices for name, indices in top_authors}

# ── Year distribution ──
year_counts = Counter(s["y"] for s in structured if s["y"])
year_dist = dict(sorted(year_counts.items()))

# ── Build DB ──
db = {
    "articles": structured,
    "fi": {k: v for k, v in sorted(formula_index.items(), key=lambda x: -len(x[1]))},
    "ci": {k: v for k, v in sorted(category_index.items(), key=lambda x: -len(x[1]))},
    "fs": formula_summary,
    "ct": cat_tree,
    "au": author_data,
    "yd": year_dist,
    "stats": {
        "total": len(articles),
        "withFormula": sum(1 for s in structured if s["f"]),
        "withAbstract": sum(1 for s in structured if s["ab"]),
        "formulas": len(formula_index),
        "categories": len(category_index),
    }
}

# Save DB
out_path = os.path.join(BASE_DIR, "output/kampo_db_v3.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, separators=(',', ':'))

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"DB saved: {out_path} ({size_mb:.1f} MB)")
print(f"Articles: {db['stats']['total']}")
print(f"With formula: {db['stats']['withFormula']}")
print(f"With abstract: {db['stats']['withAbstract']}")
print(f"Formulas: {db['stats']['formulas']}")
print(f"Categories: {db['stats']['categories']}")
print(f"Authors indexed: {len(author_data)}")
print(f"Year range: {min(year_dist.keys())}-{max(year_dist.keys())}")
