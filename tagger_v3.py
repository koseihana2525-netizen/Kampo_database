"""
統合タグ付けスクリプト (v3)

categories_v3.json の5軸カテゴリ体系を使い、
日本語誌(J-STAGE) + PubMed の全論文にタグ付けする。

Usage:
    python tagger_v3.py                    # 全データにタグ付け
    python tagger_v3.py --source pubmed    # PubMedのみ
    python tagger_v3.py --source jstage    # J-STAGEのみ
    python tagger_v3.py --dry-run          # 統計のみ（保存しない）
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import DATA_DIR

CATEGORIES_PATH = DATA_DIR / "categories_v3.json"
PUBMED_INPUT = DATA_DIR / "pubmed" / "pubmed_cleaned.json"
JSTAGE_INPUT = DATA_DIR / "merged_metadata.json"
OUTPUT_DIR = DATA_DIR / "tagged"


# ================================================================
# カテゴリ体系の読み込み・平坦化
# ================================================================

def load_categories():
    """categories_v3.json を読み込み、全leafノードをaxis別に平坦化"""
    with open(CATEGORIES_PATH, encoding="utf-8") as f:
        data = json.load(f)

    axes = {}
    for axis_name, axis_data in data["axes"].items():
        leaves = []
        _collect_leaves(axis_data, leaves, axis_name)
        axes[axis_name] = leaves

    return axes


def _collect_leaves(obj, leaves, axis_name, path=None):
    """再帰的にleafノード（keywords_ja or keywords_en を持つ）を収集"""
    if path is None:
        path = []

    if isinstance(obj, dict):
        # leafノード判定: keywords_ja or keywords_en がある
        if "keywords_ja" in obj or "keywords_en" in obj:
            leaf = {
                "id": obj.get("id", ""),
                "name_ja": obj.get("name_ja", ""),
                "name_en": obj.get("name_en", ""),
                "keywords_ja": [kw.lower() for kw in obj.get("keywords_ja", [])],
                "keywords_en": [kw.lower() for kw in obj.get("keywords_en", [])],
                "mesh_terms": [m.lower() for m in obj.get("mesh_terms", [])],
                "pub_type_match": obj.get("pub_type_match", []),
                "axis": axis_name,
                "path": path + [obj.get("name_ja", "")],
            }
            leaves.append(leaf)

        # 子要素を探索
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _collect_leaves(v, leaves, axis_name,
                                path + [obj.get("name_ja", "")] if "name_ja" in obj else path)

    elif isinstance(obj, list):
        for item in obj:
            _collect_leaves(item, leaves, axis_name, path)


# ================================================================
# タグ付けロジック
# ================================================================

def tag_article_pubmed(art, axes):
    """PubMed論文に5軸タグ付け"""
    title = (art.get("title", "") or "").lower()
    abstract = (art.get("abstract", "") or "").lower()
    text = title + " " + abstract
    mesh_set = set(m.lower() for m in art.get("mesh_terms", []))
    pub_types = set(art.get("pub_types", []))

    result = {}
    for axis_name, leaves in axes.items():
        matched = []
        for leaf in leaves:
            hit = False

            # 1. English keyword match
            if any(kw in text for kw in leaf["keywords_en"]):
                hit = True

            # 2. MeSH match
            if not hit and any(m in mesh_set for m in leaf["mesh_terms"]):
                hit = True

            # 3. PubMed publication type match (study_design axis)
            if not hit and leaf["pub_type_match"]:
                if any(pt in pub_types for pt in leaf["pub_type_match"]):
                    hit = True

            if hit:
                matched.append(leaf["id"])

        result[axis_name] = matched

    return result


def tag_article_jstage(art, axes):
    """J-STAGE論文に5軸タグ付け"""
    title_ja = (art.get("title_ja", "") or "").lower()
    title_en = (art.get("title_en", "") or "").lower()
    abstract_ja = (art.get("abstract_ja", "") or "").lower()
    abstract_en = (art.get("abstract_en", "") or "").lower()

    text_ja = title_ja + " " + abstract_ja
    text_en = title_en + " " + abstract_en

    result = {}
    for axis_name, leaves in axes.items():
        matched = []
        for leaf in leaves:
            hit = False

            # 1. Japanese keyword match
            if any(kw in text_ja for kw in leaf["keywords_ja"]):
                hit = True

            # 2. English keyword match (title_en / abstract_en がある場合)
            if not hit and text_en.strip():
                if any(kw in text_en for kw in leaf["keywords_en"]):
                    hit = True

            if hit:
                matched.append(leaf["id"])

        result[axis_name] = matched

    return result


# ================================================================
# メイン処理
# ================================================================

def process_pubmed(axes, dry_run=False):
    """PubMedデータのタグ付け"""
    print("\n" + "=" * 60)
    print("PubMed タグ付け")
    print("=" * 60)

    with open(PUBMED_INPUT, encoding="utf-8") as f:
        arts = json.load(f)

    print(f"入力: {len(arts)} 件")

    axis_stats = {ax: Counter() for ax in axes}
    tagged_any = 0
    per_axis_tagged = Counter()

    for art in arts:
        tags = tag_article_pubmed(art, axes)
        art["categories_v3"] = tags

        any_tag = False
        for ax, ids in tags.items():
            if ids:
                any_tag = True
                per_axis_tagged[ax] += 1
                for tag_id in ids:
                    axis_stats[ax][tag_id] += 1

        if any_tag:
            tagged_any += 1

    # 統計表示
    print(f"\n--- タグ付け結果 ---")
    print(f"少なくとも1軸にタグあり: {tagged_any}/{len(arts)} "
          f"({100 * tagged_any / len(arts):.1f}%)")

    for ax in axes:
        count = per_axis_tagged[ax]
        print(f"  {ax}: {count}/{len(arts)} ({100 * count / len(arts):.1f}%)")

    # 軸別トップカテゴリ
    for ax in axes:
        if axis_stats[ax]:
            print(f"\n  [{ax}] Top 10:")
            for tag_id, c in axis_stats[ax].most_common(10):
                # tag_idからname_jaを取得
                name = _find_name(axes[ax], tag_id)
                print(f"    {c:5d}  {tag_id}: {name}")

    if not dry_run:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / "pubmed_tagged_v3.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(arts, f, ensure_ascii=False, indent=2)
        print(f"\n保存: {out_path}")

    return arts


def process_jstage(axes, dry_run=False):
    """J-STAGEデータのタグ付け"""
    print("\n" + "=" * 60)
    print("J-STAGE タグ付け")
    print("=" * 60)

    with open(JSTAGE_INPUT, encoding="utf-8") as f:
        arts = json.load(f)

    print(f"入力: {len(arts)} 件")

    axis_stats = {ax: Counter() for ax in axes}
    tagged_any = 0
    per_axis_tagged = Counter()

    for art in arts:
        tags = tag_article_jstage(art, axes)
        art["categories_v3"] = tags

        any_tag = False
        for ax, ids in tags.items():
            if ids:
                any_tag = True
                per_axis_tagged[ax] += 1
                for tag_id in ids:
                    axis_stats[ax][tag_id] += 1

        if any_tag:
            tagged_any += 1

    # 統計表示
    print(f"\n--- タグ付け結果 ---")
    print(f"少なくとも1軸にタグあり: {tagged_any}/{len(arts)} "
          f"({100 * tagged_any / len(arts):.1f}%)")

    for ax in axes:
        count = per_axis_tagged[ax]
        print(f"  {ax}: {count}/{len(arts)} ({100 * count / len(arts):.1f}%)")

    # 軸別トップカテゴリ
    for ax in axes:
        if axis_stats[ax]:
            print(f"\n  [{ax}] Top 10:")
            for tag_id, c in axis_stats[ax].most_common(10):
                name = _find_name(axes[ax], tag_id)
                print(f"    {c:5d}  {tag_id}: {name}")

    if not dry_run:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / "jstage_tagged_v3.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(arts, f, ensure_ascii=False, indent=2)
        print(f"\n保存: {out_path}")

    return arts


def _find_name(leaves, tag_id):
    """leaf IDからname_jaを取得"""
    for l in leaves:
        if l["id"] == tag_id:
            return l["name_ja"]
    return "?"


def print_cross_tabulation(pubmed_arts, jstage_arts, axes):
    """日英統合のクロス集計サマリー"""
    print("\n" + "=" * 60)
    print("統合クロス集計")
    print("=" * 60)

    # disease × study_design のクロス集計（PubMedのみ）
    print("\n[PubMed] disease × study_design クロス集計 (Top 20):")
    cross = Counter()
    for art in pubmed_arts:
        cats = art.get("categories_v3", {})
        diseases = cats.get("disease", [])
        designs = cats.get("study_design", [])
        for d in diseases:
            for s in designs:
                cross[(d, s)] += 1

    for (d, s), c in cross.most_common(20):
        d_name = _find_name(axes["disease"], d)
        s_name = _find_name(axes["study_design"], s)
        print(f"  {c:4d}  {d_name} × {s_name}")

    # J-STAGE vs PubMed disease分布比較
    print("\n疾患カテゴリ: J-STAGE vs PubMed 比較:")
    jp_disease = Counter()
    pm_disease = Counter()
    for art in jstage_arts:
        for d in art.get("categories_v3", {}).get("disease", []):
            jp_disease[d] += 1
    for art in pubmed_arts:
        for d in art.get("categories_v3", {}).get("disease", []):
            pm_disease[d] += 1

    all_diseases = set(jp_disease.keys()) | set(pm_disease.keys())
    rows = []
    for d in all_diseases:
        name = _find_name(axes["disease"], d)
        rows.append((name, d, jp_disease.get(d, 0), pm_disease.get(d, 0)))

    rows.sort(key=lambda x: -(x[2] + x[3]))
    print(f"  {'疾患':<20s} {'J-STAGE':>8s} {'PubMed':>8s} {'合計':>8s}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8}")
    for name, _, jp, pm in rows[:25]:
        print(f"  {name:<20s} {jp:>8d} {pm:>8d} {jp+pm:>8d}")


def main():
    parser = argparse.ArgumentParser(description="統合タグ付け (v3)")
    parser.add_argument("--source", choices=["pubmed", "jstage"],
                        help="特定ソースのみ処理")
    parser.add_argument("--dry-run", action="store_true",
                        help="統計のみ表示（ファイル保存しない）")
    args = parser.parse_args()

    # カテゴリ読み込み
    axes = load_categories()
    print("カテゴリ体系 v3 読み込み完了:")
    for ax, leaves in axes.items():
        print(f"  {ax}: {len(leaves)} leaves")

    pubmed_arts = None
    jstage_arts = None

    if args.source != "jstage":
        pubmed_arts = process_pubmed(axes, dry_run=args.dry_run)

    if args.source != "pubmed":
        jstage_arts = process_jstage(axes, dry_run=args.dry_run)

    # 両方処理した場合はクロス集計
    if pubmed_arts and jstage_arts:
        print_cross_tabulation(pubmed_arts, jstage_arts, axes)


if __name__ == "__main__":
    main()
