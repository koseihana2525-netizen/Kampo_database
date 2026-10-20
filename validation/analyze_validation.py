# -*- coding: utf-8 -*-
"""
analyze_validation.py - 第2評価者の検証結果を集計する

入力: make_validation_sheet.py が作った answer_key.csv と、評価者が記入した validation_sheet.xlsx（評価者ごと）
出力: 評価者間の一致（Cohen の κ）、判定器の正確さ（PPV・NPV・感度・特異度。層の母集団で重み付け）、
      補正後のギャップ（95%信頼区間は層内の再抽出）

判定の読み替え
  処方名: 有 = 1、無 = 0、不明 = 欠測（除く）
  漢方診断: 厳密 = 『有』のみ 1（『背景のみ』『無』は 0）、寛容 = 『有』『背景のみ』を 1。不明 = 欠測

Usage
  python validation/analyze_validation.py --key answer_key.csv --rater 河原=sheet_kawahara.xlsx [--rater 華岡=sheet_hanaoka.xlsx] [--out report.md]
標準ライブラリ + openpyxl。
"""

import argparse
import csv
import math
import random
import sys
from collections import defaultdict
from pathlib import Path


def load_key(path):
    rows = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = dict(set=r["set"], stratum=r["stratum"], population=int(r["stratum_population"]), formula=int(r["classifier_formula"]),
                                 concept=int(r["classifier_concept"]))
    return rows


def load_rater(path):
    from openpyxl import load_workbook
    ws = load_workbook(path, data_only=True)["評価シート"]
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:
            out[str(row[0])] = (row[2], row[3])
    return out


def to_formula(v):
    return {"有": 1, "無": 0}.get(v)


def to_diag(v, strict=True):
    if v == "有":
        return 1
    if v == "背景のみ":
        return 0 if strict else 1
    if v == "無":
        return 0
    return None


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return float("nan"), 0
    po = sum(1 for a, b in pairs if a == b) / n
    pa = sum(1 for a, _ in pairs if a == 1) / n
    pb = sum(1 for _, b in pairs if b == 1) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan"), n


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def weighted(items, f):
    """items: [(stratum_key, population, value_dict)] 。層ごとの重み N_s / n_s で f(value_dict) を合計"""
    n_s = defaultdict(int)
    for k, _, _ in items:
        n_s[k] += 1
    return sum(pop / n_s[k] * f(v) for k, pop, v in items)


def estimates(items):
    """items の各 value: dict(cf=判定器の処方, cc=判定器の概念, f=評価者の処方, d=評価者の診断)。戻り値: 辞書"""
    F = weighted(items, lambda v: v["f"])
    FD = weighted(items, lambda v: v["f"] * v["d"] if v["d"] is not None else 0)
    Fd = weighted(items, lambda v: v["f"] if v["d"] is not None else 0)
    out = {"gap": 1 - FD / Fd if Fd else float("nan"), "formula_total": F}
    tp = weighted(items, lambda v: v["cf"] * v["f"])
    fp = weighted(items, lambda v: v["cf"] * (1 - v["f"]))
    fn = weighted(items, lambda v: (1 - v["cf"]) * v["f"])
    tn = weighted(items, lambda v: (1 - v["cf"]) * (1 - v["f"]))
    out.update(f_ppv=tp / (tp + fp) if tp + fp else float("nan"), f_npv=tn / (tn + fn) if tn + fn else float("nan"),
               f_sens=tp / (tp + fn) if tp + fn else float("nan"), f_spec=tn / (tn + fp) if tn + fp else float("nan"))
    dd = [(k, p, v) for k, p, v in items if v["f"] == 1 and v["d"] is not None]
    tp = weighted(dd, lambda v: v["cc"] * v["d"])
    fp = weighted(dd, lambda v: v["cc"] * (1 - v["d"]))
    fn = weighted(dd, lambda v: (1 - v["cc"]) * v["d"])
    tn = weighted(dd, lambda v: (1 - v["cc"]) * (1 - v["d"]))
    out.update(c_ppv=tp / (tp + fp) if tp + fp else float("nan"), c_npv=tn / (tn + fn) if tn + fn else float("nan"),
               c_sens=tp / (tp + fn) if tp + fn else float("nan"), c_spec=tn / (tn + fp) if tn + fp else float("nan"))
    return out


def bootstrap(items, keys, B=2000, seed=1):
    rng = random.Random(seed)
    by = defaultdict(list)
    for it in items:
        by[it[0]].append(it)
    res = {k: [] for k in keys}
    for _ in range(B):
        sample = []
        for k, lst in by.items():
            sample += [rng.choice(lst) for _ in lst]
        e = estimates(sample)
        for k in keys:
            if not math.isnan(e[k]):
                res[k].append(e[k])
    ci = {}
    for k, v in res.items():
        v.sort()
        ci[k] = (v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]) if len(v) > 20 else (float("nan"), float("nan"))
    return ci


def observed_gap(key, set_name):
    q = defaultdict(int)
    seen = {}
    for r in key.values():
        if r["set"] == set_name:
            seen[r["stratum"]] = r["population"]
    q1, q3 = seen.get("Q1", 0), seen.get("Q3", 0)
    return q3 / (q1 + q3) if q1 + q3 else float("nan")


def report(key, raters, strict=True):
    lines = []
    names = list(raters)
    label = "厳密（『有』のみ）" if strict else "寛容（『有』『背景のみ』）"
    lines.append(f"## 漢方診断の定義: {label}\n")
    # 評価者間の一致
    if len(names) >= 2:
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = raters[names[i]], raters[names[j]]
                pf = [(to_formula(a[k][0]), to_formula(b[k][0])) for k in key if k in a and k in b and to_formula(a[k][0]) is not None and to_formula(b[k][0]) is not None]
                pd = [(to_diag(a[k][1], strict), to_diag(b[k][1], strict)) for k in key if k in a and k in b and to_diag(a[k][1], strict) is not None and to_diag(b[k][1], strict) is not None]
                kf, nf = kappa(pf)
                kd, nd = kappa(pd)
                lines.append(f"- {names[i]} と {names[j]}: 処方名の κ = {kf:.2f}（n={nf}）、漢方診断の κ = {kd:.2f}（n={nd}）")
        lines.append("")
    views = {n: raters[n] for n in names}
    if len(names) >= 2:   # 合意: すべての評価者が処方名・診断の両方で同じ判定をした記録
        agree = {}
        for k in key:
            if all(k in raters[n] for n in names):
                fs = {to_formula(raters[n][k][0]) for n in names}
                ds = {to_diag(raters[n][k][1], strict) for n in names}
                if len(fs) == 1 and len(ds) == 1 and None not in fs and None not in ds:
                    agree[k] = (next(iter(fs)), next(iter(ds)))
        views["合意"] = {k: ("有" if f else "無", "有" if d else "無") for k, (f, d) in agree.items()}
        lines.append(f"- 合意した記録: {len(agree)} / {len(key)}\n")
    for nm, rv in views.items():
        lines.append(f"### 評価者: {nm}\n")
        lines.append("| セット | 判定器のギャップ | 補正後のギャップ（95%CI） | 処方名 PPV | 処方名 感度 | 診断語 PPV | 診断語 NPV | 診断語 感度 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for sn, sl in (("jp", "日本語"), ("pm", "PubMed")):
            items = []
            for k, r in key.items():
                if r["set"] != sn or k not in rv:
                    continue
                f, d = to_formula(rv[k][0]), to_diag(rv[k][1], strict)
                if f is None:
                    continue
                items.append(((sn, r["stratum"]), r["population"], dict(cf=r["formula"], cc=r["concept"], f=f, d=d)))
            if not items:
                continue
            e = estimates(items)
            ci = bootstrap(items, ["gap"])
            lines.append(f"| {sl} | {observed_gap(key, sn) * 100:.1f}% | {e['gap'] * 100:.1f}%（{ci['gap'][0] * 100:.1f}–{ci['gap'][1] * 100:.1f}） | "
                         f"{e['f_ppv'] * 100:.0f}% | {e['f_sens'] * 100:.0f}% | {e['c_ppv'] * 100:.0f}% | {e['c_npv'] * 100:.0f}% | {e['c_sens'] * 100:.0f}% |")
        lines.append("")
    return lines


def main():
    ap = argparse.ArgumentParser(description="第2評価者の検証結果を集計する")
    ap.add_argument("--key", required=True)
    ap.add_argument("--rater", action="append", required=True, metavar="名前=ファイル")
    ap.add_argument("--out")
    args = ap.parse_args()
    key = load_key(args.key)
    raters = {}
    for spec in args.rater:
        name, path = spec.split("=", 1)
        raters[name] = load_rater(path)
    lines = ["# 検証の集計\n", "重み: 層（セット×象限）の母集団 / 標本。『不明』は欠測として除く。補正後のギャップ = 1 − (処方名有かつ診断有) / (処方名有)。\n"]
    lines += report(key, raters, strict=True) + report(key, raters, strict=False)
    text = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
