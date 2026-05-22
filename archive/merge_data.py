# -*- coding: utf-8 -*-
"""
merge_data.py - Merge kampo + jjsam metadata into single dataset
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

KAMPO_PATH = os.path.join(DATA_DIR, "metadata_with_abstracts.json")
JJSAM_PATH = os.path.join(DATA_DIR, "jjsam_with_abstracts.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "merged_metadata.json")


def main():
    with open(KAMPO_PATH, "r", encoding="utf-8") as f:
        kampo = json.load(f)
    print(f"Kampo: {len(kampo)} articles")

    with open(JJSAM_PATH, "r", encoding="utf-8") as f:
        jjsam = json.load(f)
    print(f"JJSAM: {len(jjsam)} articles")

    # Ensure cdjournal is set
    for a in kampo:
        if not a.get("cdjournal"):
            a["cdjournal"] = "kampo"
    for a in jjsam:
        if not a.get("cdjournal"):
            a["cdjournal"] = "jjsam"

    merged = kampo + jjsam
    print(f"Merged: {len(merged)} articles")

    # Stats
    kampo_abs = sum(1 for a in kampo if a.get("abstract_ja") or a.get("abstract_en"))
    jjsam_abs = sum(1 for a in jjsam if a.get("abstract_ja") or a.get("abstract_en"))
    print(f"Kampo with abstract: {kampo_abs}/{len(kampo)}")
    print(f"JJSAM with abstract: {jjsam_abs}/{len(jjsam)}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
