#!/usr/bin/env python3
"""
3-Layer Evidence Map Analysis
=============================
Layer 1: Western medicine evidence strength (A/B/M)
Layer 2: Kampo (漢方) article counts from 東洋医学雑誌
Layer 3: Acupuncture (鍼灸) article counts from 東洋医学雑誌

Classifies 59 primary care conditions into 4 quadrants:
  Q1: Western WEAK  + TJM STRONG  -> Traditional medicine fills gaps
  Q2: Western STRONG + TJM STRONG -> Complementary evidence
  Q3: Western WEAK  + TJM WEAK   -> True evidence gap
  Q4: Western STRONG + TJM WEAK  -> Western medicine sufficient
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# ── Data ────────────────────────────────────────────────────────────────────

# Each entry: (condition_name, body_system, kampo_count, acupuncture_count, western_rating)
# western_rating: 'A' = strong, 'B' = weak/difficult, 'M' = middle

CONDITIONS = [
    # 筋骨格系・疼痛
    ("腰痛",               "筋骨格・疼痛",    4, 13, "A"),
    ("頭痛",               "筋骨格・疼痛",   21,  6, "A"),
    ("肩こり肩痛",         "筋骨格・疼痛",    5,  5, "B"),
    ("膝痛変形性関節症",   "筋骨格・疼痛",   11,  4, "A"),
    ("関節リウマチ",       "筋骨格・疼痛",   37,  1, "A"),
    ("線維筋痛症",         "筋骨格・疼痛",    8,  0, "B"),
    ("神経痛",             "筋骨格・疼痛",   17,  4, "M"),
    ("しびれ",             "筋骨格・疼痛",    4,  1, "B"),
    ("筋痙攣こむら返り",   "筋骨格・疼痛",   14,  0, "B"),
    # 精神・神経
    ("うつ抑うつ",         "精神・神経",     11,  4, "A"),
    ("不安障害",           "精神・神経",      7,  2, "A"),
    ("不眠",               "精神・神経",     22,  5, "A"),
    ("認知症BPSD",         "精神・神経",      4,  5, "B"),
    ("めまい",             "精神・神経",      8,  0, "M"),
    ("自律神経失調",       "精神・神経",      9,  2, "B"),
    ("顔面神経麻痺",       "精神・神経",      7,  7, "M"),
    # 消化器
    ("FD",                 "消化器",          6,  0, "M"),
    ("GERD",               "消化器",          3,  0, "A"),
    ("IBS",                "消化器",          7,  1, "M"),
    ("便秘",               "消化器",         10,  0, "A"),
    ("下痢",               "消化器",          9,  0, "M"),
    ("肝疾患",             "消化器",         80,  6, "A"),
    ("イレウス",           "消化器",          9,  0, "A"),
    ("口内炎",             "消化器",          7,  1, "B"),
    # 呼吸器・感染症
    ("感冒",               "呼吸器・感染症",  6,  1, "M"),
    ("インフルエンザ",     "呼吸器・感染症",  7,  0, "A"),
    ("COVID-19",           "呼吸器・感染症", 17,  6, "M"),
    ("咳嗽",               "呼吸器・感染症", 10,  1, "B"),
    ("気管支喘息",         "呼吸器・感染症", 25,  1, "A"),
    ("アレルギー性鼻炎",   "呼吸器・感染症",  7,  3, "A"),
    ("COPD",               "呼吸器・感染症",  7,  0, "A"),
    # 循環器・全身
    ("高血圧",             "循環器・全身",    8,  0, "A"),
    ("動悸不整脈",         "循環器・全身",    5,  0, "A"),
    ("冷え",               "循環器・全身",   19,  3, "B"),
    ("浮腫",               "循環器・全身",    6,  1, "M"),
    # 泌尿器
    ("頻尿過活動膀胱",     "泌尿器",          7,  1, "A"),
    ("膀胱炎",             "泌尿器",          5,  0, "A"),
    ("前立腺",             "泌尿器",          3,  1, "A"),
    ("腎疾患",             "泌尿器",         37,  0, "A"),
    # 婦人科
    ("更年期障害",         "婦人科",         11,  0, "M"),
    ("月経異常PMS",        "婦人科",         15,  4, "A"),
    ("不妊",               "婦人科",          7,  5, "A"),
    ("妊娠関連",           "婦人科",         14,  0, "M"),
    # 皮膚科
    ("アトピー",           "皮膚科",         23,  3, "A"),
    ("湿疹蕁麻疹",         "皮膚科",         37,  4, "A"),
    ("帯状疱疹",           "皮膚科",          6,  2, "A"),
    ("褥瘡創傷",           "皮膚科",         13,  2, "A"),
    # がん・代謝
    ("がん支持療法",       "がん・代謝",     38,  9, "A"),
    ("糖尿病",             "がん・代謝",     21,  0, "A"),
    ("肥満",               "がん・代謝",      8,  0, "A"),
    # その他全身
    ("倦怠感疲労",         "その他",         21,  4, "B"),
    ("耳鳴",               "その他",         10,  2, "B"),
    ("突発性難聴",         "その他",          6,  1, "M"),
    ("嗅覚味覚障害",       "その他",          8,  1, "B"),
    ("眼疾患",             "その他",         10,  2, "A"),
    ("小児疾患",           "その他",         29,  2, "A"),
    ("高齢者",             "その他",         25,  9, "M"),
    ("スポーツ障害",       "その他",          0, 23, "A"),
    ("脳卒中リハビリ",     "その他",          6,  2, "A"),
]


# ── Classification logic ────────────────────────────────────────────────────

def tjm_strength(k, a):
    total = k + a
    if total >= 15:
        return "Strong"
    elif total >= 5:
        return "Moderate"
    elif total >= 1:
        return "Weak"
    else:
        return "None"

def western_is_weak(rating):
    """B or M are considered 'weak/limited' for quadrant assignment."""
    return rating in ("B", "M")

def classify(k, a, w):
    tjm = tjm_strength(k, a)
    tjm_strong = tjm in ("Strong", "Moderate")  # >= 5 articles
    w_weak = western_is_weak(w)

    if w_weak and tjm_strong:
        return "Q1"
    elif (not w_weak) and tjm_strong:
        return "Q2"
    elif w_weak and (not tjm_strong):
        return "Q3"
    else:
        return "Q4"


# ── Build quadrants ─────────────────────────────────────────────────────────

quadrants = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}

for name, system, k, a, w in CONDITIONS:
    q = classify(k, a, w)
    quadrants[q].append((name, system, k, a, w, tjm_strength(k, a)))


# ── Display helpers ─────────────────────────────────────────────────────────

def bar(count, char="█", scale=1):
    return char * (count // scale) if count > 0 else ""

def print_quadrant(qid, title, emoji, items):
    print(f"\n{'='*78}")
    print(f"  {emoji}  {qid}: {title}")
    print(f"{'='*78}")
    print(f"  {'疾患':<20s} {'系統':<14s} {'K':>3s} {'A':>3s} {'計':>3s} {'W':>2s} {'TJM':<8s}  漢方/鍼灸バー")
    print(f"  {'-'*74}")

    # Sort by total descending
    items_sorted = sorted(items, key=lambda x: x[2] + x[3], reverse=True)
    for name, system, k, a, w, tjm_s in items_sorted:
        total = k + a
        k_bar = bar(k, "K")
        a_bar = bar(a, "A")
        print(f"  {name:<20s} {system:<14s} {k:>3d} {a:>3d} {total:>3d}  {w:<2s} {tjm_s:<8s}  {k_bar}{a_bar}")

    print(f"\n  -> {len(items)} conditions")


# ── Main output ─────────────────────────────────────────────────────────────

print()
print("=" * 78)
print("  3-Layer Evidence Map: Western Medicine x Traditional Japanese Medicine (TJM)")
print("  東洋医学雑誌 原著論文 (2014-2024) に基づくエビデンスマップ")
print("=" * 78)
print()
print("  Layers:")
print("    1. Western medicine evidence strength: A(strong) / M(middle) / B(weak)")
print("    2. Kampo (漢方) article count  [K]")
print("    3. Acupuncture (鍼灸) article count  [A]")
print()
print("  TJM Strength: Total(K+A) >= 15 Strong, >= 5 Moderate, >= 1 Weak, 0 None")
print()
print("  Quadrant assignment:")
print("    Western weak  = B or M rating")
print("    TJM strong    = Strong or Moderate (total >= 5)")

QUADRANT_INFO = {
    "Q1": ("Western WEAK + TJM STRONG: TJM fills evidence gaps", "***"),
    "Q2": ("Western STRONG + TJM STRONG: Complementary evidence", "+++"),
    "Q3": ("Western WEAK + TJM WEAK: True evidence gap", "???"),
    "Q4": ("Western STRONG + TJM WEAK: Western medicine sufficient", "---"),
}

for qid in ["Q1", "Q2", "Q3", "Q4"]:
    title, emoji = QUADRANT_INFO[qid]
    print_quadrant(qid, title, emoji, quadrants[qid])


# ── Summary ─────────────────────────────────────────────────────────────────

print()
print("=" * 78)
print("  SUMMARY")
print("=" * 78)

total_k = sum(k for _, _, k, a, w in CONDITIONS)
total_a = sum(a for _, _, k, a, w in CONDITIONS)
total_all = total_k + total_a

print(f"\n  Total conditions analyzed: {len(CONDITIONS)}")
print(f"  Total articles: {total_all}  (Kampo: {total_k}, Acupuncture: {total_a})")

for qid in ["Q1", "Q2", "Q3", "Q4"]:
    items = quadrants[qid]
    n = len(items)
    pct = n / len(CONDITIONS) * 100
    k_sum = sum(x[2] for x in items)
    a_sum = sum(x[3] for x in items)
    title, _ = QUADRANT_INFO[qid]
    print(f"\n  {qid} ({n} conditions, {pct:.0f}%): {title}")
    print(f"      Kampo articles: {k_sum}  |  Acupuncture articles: {a_sum}  |  Total: {k_sum+a_sum}")
    names = [x[0] for x in sorted(items, key=lambda x: x[2]+x[3], reverse=True)]
    # Print top 5
    top = names[:5]
    print(f"      Top: {', '.join(top)}")

# ── Key findings ────────────────────────────────────────────────────────────

print()
print("=" * 78)
print("  KEY FINDINGS")
print("=" * 78)

q1_items = sorted(quadrants["Q1"], key=lambda x: x[2]+x[3], reverse=True)
print("\n  [1] TJM fills Western evidence gaps (Q1) - top conditions:")
for name, system, k, a, w, tjm_s in q1_items[:8]:
    print(f"      {name:<20s}  K={k:>2d}  A={a:>2d}  Total={k+a:>2d}  (Western: {w})")

q3_items = sorted(quadrants["Q3"], key=lambda x: x[2]+x[3], reverse=True)
print("\n  [2] True evidence gaps (Q3) - need more research:")
for name, system, k, a, w, tjm_s in q3_items:
    print(f"      {name:<20s}  K={k:>2d}  A={a:>2d}  Total={k+a:>2d}  (Western: {w})")

# Body system analysis
print("\n  [3] Body system coverage:")
systems = {}
for name, system, k, a, w in CONDITIONS:
    if system not in systems:
        systems[system] = {"count": 0, "k": 0, "a": 0}
    systems[system]["count"] += 1
    systems[system]["k"] += k
    systems[system]["a"] += a

for sys_name, data in sorted(systems.items(), key=lambda x: x[1]["k"]+x[1]["a"], reverse=True):
    total = data["k"] + data["a"]
    print(f"      {sys_name:<16s}  {data['count']:>2d} conditions  K={data['k']:>3d}  A={data['a']:>3d}  Total={total:>3d}")

# Acupuncture vs Kampo dominance
print("\n  [4] Acupuncture-dominant conditions (A > K):")
for name, system, k, a, w in CONDITIONS:
    if a > k:
        print(f"      {name:<20s}  K={k:>2d}  A={a:>2d}  (A leads by {a-k})")

print("\n  [5] Kampo-only conditions (A = 0):")
kampo_only = [(name, k) for name, system, k, a, w in CONDITIONS if a == 0]
kampo_only.sort(key=lambda x: x[1], reverse=True)
for name, k in kampo_only:
    print(f"      {name:<20s}  K={k:>2d}")

print()
print("=" * 78)
print("  Analysis complete.")
print("=" * 78)
