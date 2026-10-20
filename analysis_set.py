# -*- coding: utf-8 -*-
"""
analysis_set.py - 認知ギャップ解析の対象とする記録の選び方（標準ライブラリのみ）

run_gap_analysis.py と、検証用シートの作成（validation/make_validation_sheet.py）が共有する。
"""

import re

GROUPS = ("kampo", "pubmed_kampo")
# 解析対象から外す PubMed の記録: 正誤表・撤回通知・コメントは研究論文ではない。抄録が同一の記録は最初の1件だけ残す
NON_ARTICLE_TYPES = {"published erratum", "retraction notice", "retraction of publication", "comment"}


def has_abstract(article):
    return bool((article.get("abstract") or "").strip())


def exclusion_reasons(articles):
    """解析対象の2群（抄録あり）から外す記録: {id: 理由}"""
    out, seen = {}, set()
    for a in articles:
        if a["source"] not in GROUPS or not has_abstract(a):
            continue
        reason = next((t for t in (x.lower() for x in (a.get("pub_types") or [])) if t in NON_ARTICLE_TYPES), "")
        key = (a["source"], re.sub(r"\s+", " ", a["abstract"].strip().lower()))
        if not reason and key in seen:
            reason = "duplicate abstract"
        seen.add(key)
        if reason:
            out[a["id"]] = reason
    return out


def analysis_records(articles):
    """解析対象の記録（抄録あり・2群・除外後）を、元の順序で返す"""
    ex = exclusion_reasons(articles)
    return [a for a in articles if a["source"] in GROUPS and has_abstract(a) and a["id"] not in ex]
