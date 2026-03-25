#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_categories_v2.py
3層カテゴリ構造を定義し、metadata_with_abstracts.json の各記事を
キーワードマッチでカウントして categories_v2.json に保存する。
"""

import json
import os
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_FILE = os.path.join(DATA_DIR, "merged_metadata.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "categories_v2.json")

# ============================================================
# 3層カテゴリ定義
# Level 1 > Level 2 > Level 3: (表示名, [検索キーワード])
# ============================================================
CATEGORY_TREE = OrderedDict([
    ("ICD疾患分類", OrderedDict([
        ("I 感染症", OrderedDict([
            ("感冒",        ["感冒", "風邪", "上気道炎", "インフルエンザ"]),
            ("帯状疱疹",    ["帯状疱疹"]),
        ])),
        ("II 悪性腫瘍", OrderedDict([
            ("化学療法支持", ["化学療法", "抗がん剤"]),
            ("消化器癌",    ["胃癌", "大腸癌", "肝癌"]),
            ("その他腫瘍",  ["癌", "がん", "腫瘍", "白血病"]),
        ])),
        ("IV 内分泌・代謝", OrderedDict([
            ("糖尿病",      ["糖尿病"]),
            ("甲状腺",      ["甲状腺", "バセドウ"]),
        ])),
        ("V 精神・行動", OrderedDict([
            ("うつ",        ["うつ", "抑うつ"]),
            ("不安障害",    ["不安障害", "パニック障害"]),
            ("認知症",      ["認知症", "BPSD", "アルツハイマー", "せん妄"]),
        ])),
        ("VIII 耳鼻咽喉", OrderedDict([
            ("耳鳴・難聴",      ["耳鳴", "難聴", "突発性難聴"]),
            ("アレルギー性鼻炎", ["アレルギー性鼻炎", "花粉症"]),
            ("咽喉頭",          ["咽頭", "梅核気"]),
        ])),
        ("X 呼吸器", OrderedDict([
            ("喘息",        ["喘息", "気管支喘息"]),
            ("咳嗽",        ["咳嗽", "喀痰", "慢性咳嗽"]),
            ("間質性肺炎",  ["間質性肺炎"]),
            ("COPD",        ["COPD", "気管支炎"]),
        ])),
        ("XI 消化器", OrderedDict([
            ("胃炎・FD",        ["胃炎", "FD", "胃もたれ", "心窩部"]),
            ("逆流性食道炎",    ["GERD", "胸やけ"]),
            ("肝疾患",          ["肝炎", "肝硬変", "肝障害", "肝機能"]),
            ("IBD",             ["クローン", "潰瘍性大腸炎"]),
            ("IBS",             ["過敏性腸", "IBS"]),
            ("イレウス",        ["イレウス", "腸閉塞"]),
        ])),
        ("XII 皮膚", OrderedDict([
            ("アトピー",    ["アトピー"]),
            ("蕁麻疹",      ["蕁麻疹"]),
            ("乾癬",        ["乾癬"]),
            ("掻痒症",      ["掻痒", "かゆみ"]),
        ])),
        ("XIII 筋骨格", OrderedDict([
            ("関節リウマチ",    ["関節リウマチ", "リウマチ"]),
            ("変形性関節症",    ["変形性膝"]),
            ("腰痛",            ["腰痛"]),
            ("線維筋痛症",      ["線維筋痛"]),
        ])),
        ("XIV 泌尿・生殖器", OrderedDict([
            ("腎疾患",      ["腎炎", "ネフローゼ", "CKD", "腎不全"]),
            ("膀胱炎",      ["膀胱炎", "尿路感染"]),
            ("前立腺",      ["前立腺"]),
            ("不妊",        ["不妊"]),
        ])),
        ("XV 産科", OrderedDict([
            ("妊娠",        ["妊娠", "つわり"]),
            ("産後",        ["産後", "産褥", "母乳"]),
        ])),
    ])),
    ("症候から探す", OrderedDict([
        ("痛み", OrderedDict([
            ("頭痛",        ["頭痛", "片頭痛"]),
            ("腹痛",        ["腹痛"]),
            ("神経痛",      ["神経痛", "三叉神経痛"]),
            ("その他疼痛",  ["疼痛", "しびれ"]),
        ])),
        ("全身症状", OrderedDict([
            ("冷え",        ["冷え", "冷え症"]),
            ("倦怠感",      ["倦怠", "疲労", "易疲労"]),
            ("浮腫",        ["浮腫", "むくみ"]),
            ("食欲不振",    ["食欲不振", "食欲低下"]),
        ])),
        ("自律神経・精神", OrderedDict([
            ("めまい",      ["めまい", "眩暈", "ふらつき"]),
            ("不眠",        ["不眠", "睡眠障害"]),
            ("更年期",      ["不定愁訴", "更年期", "のぼせ"]),
            ("動悸",        ["動悸", "自律神経"]),
        ])),
        ("消化器症状", OrderedDict([
            ("便秘",        ["便秘"]),
            ("下痢",        ["下痢", "軟便"]),
        ])),
        ("泌尿器症状", OrderedDict([
            ("頻尿",        ["頻尿", "夜間頻尿", "排尿障害", "過活動膀胱"]),
        ])),
        ("婦人科", OrderedDict([
            ("月経関連",    ["月経痛", "月経不順", "月経困難", "生理痛", "PMS"]),
        ])),
        ("その他", OrderedDict([
            ("こむら返り",  ["こむら返り", "筋痙攣", "腓腹筋"]),
            ("口腔・舌",    ["口内炎", "口腔", "嚥下", "口渇", "舌痛"]),
            ("咳・痰",      ["咳嗽", "喀痰", "咳", "痰"]),
        ])),
    ])),
    ("鍼灸", OrderedDict([
        ("手技・技法", OrderedDict([
            ("鍼治療",      ["鍼治療", "刺鍼", "置鍼", "円皮鍼", "皮内鍼"]),
            ("灸治療",      ["灸治療", "施灸", "温灸", "艾", "お灸"]),
            ("電気鍼",      ["電気鍼", "低周波", "TENS", "SSP", "パルス鍼"]),
            ("あん摩・指圧",["あん摩", "マッサージ", "指圧", "推拿"]),
        ])),
        ("経穴・経絡", OrderedDict([
            ("経穴",        ["経穴", "ツボ", "足三里", "合谷", "百会"]),
            ("経絡",        ["経絡", "奇経", "十二経"]),
        ])),
        ("安全性・管理", OrderedDict([
            ("有害事象",    ["有害事象", "気胸", "折鍼", "鍼事故"]),
            ("感染管理",    ["感染管理", "消毒", "鍼感染"]),
        ])),
        ("教育・制度", OrderedDict([
            ("鍼灸教育",    ["鍼灸教育", "養成", "鍼灸師", "国家試験"]),
        ])),
        ("スポーツ鍼灸", OrderedDict([
            ("スポーツ",    ["スポーツ", "アスリート", "運動器", "コンディショニング"]),
        ])),
        ("美容鍼灸", OrderedDict([
            ("美容鍼",      ["美容鍼", "美容", "顔面鍼"]),
        ])),
        ("基礎研究", OrderedDict([
            ("メカニズム",  ["作用機序", "鎮痛機序", "fMRI", "脳画像", "筋電", "EMG", "サーモグラフ"]),
        ])),
    ])),
    ("漢方医学", OrderedDict([
        ("古典・理論", OrderedDict([
            ("傷寒論",      ["傷寒論"]),
            ("金匱要略",    ["金匱"]),
            ("弁証論治",    ["弁証", "八綱", "気血水", "陰陽", "虚実"]),
            ("腹証",        ["腹証", "腹診"]),
        ])),
        ("教育", OrderedDict([
            ("漢方教育",    ["漢方教育", "カリキュラム", "研修"]),
        ])),
        ("安全性", OrderedDict([
            ("副作用",      ["副作用", "偽アルドステロン", "横紋筋融解", "薬疹"]),
            ("相互作用",    ["相互作用", "併用"]),
        ])),
    ])),
    ("その他", OrderedDict([
        ("周術期", OrderedDict([
            ("術後",        ["術後", "手術後", "周術期"]),
        ])),
        ("透析", OrderedDict([
            ("透析",        ["透析", "血液透析"]),
        ])),
        ("緩和ケア", OrderedDict([
            ("緩和",        ["緩和", "終末期", "QOL"]),
        ])),
        ("エビデンス・研究手法", OrderedDict([
            ("RCT",         ["RCT", "ランダム化", "無作為化比較"]),
            ("SR・メタ",    ["システマティック", "メタアナリシス", "メタ解析"]),
            ("ガイドライン", ["ガイドライン", "診療指針"]),
        ])),
    ])),
])


def load_articles(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_matches(articles, category_tree):
    """
    各記事の title_ja + abstract_ja を結合したテキストに対して
    キーワードマッチを行い、カウントを返す。
    戻り値は category_tree と同じ構造で count を持つ dict。
    """
    # 事前に全記事のテキストを結合しておく
    texts = []
    for a in articles:
        t = (a.get("title_ja") or "") + " " + (a.get("abstract_ja") or "")
        texts.append(t)

    result = OrderedDict()
    for lv1_name, lv2_dict in category_tree.items():
        result[lv1_name] = OrderedDict()
        for lv2_name, lv3_dict in lv2_dict.items():
            result[lv1_name][lv2_name] = OrderedDict()
            for lv3_name, keywords in lv3_dict.items():
                count = 0
                for text in texts:
                    if any(kw in text for kw in keywords):
                        count += 1
                result[lv1_name][lv2_name][lv3_name] = {
                    "keywords": keywords,
                    "count": count,
                }
    return result


def build_output(result):
    """categories_v2.json 用の構造を組み立てる"""
    output = []
    for lv1_name, lv2_dict in result.items():
        lv1_obj = {
            "name": lv1_name,
            "children": [],
        }
        lv1_total = 0
        for lv2_name, lv3_dict in lv2_dict.items():
            lv2_obj = {
                "name": lv2_name,
                "children": [],
            }
            lv2_total = 0
            for lv3_name, info in lv3_dict.items():
                lv3_obj = {
                    "name": lv3_name,
                    "keywords": info["keywords"],
                    "count": info["count"],
                }
                lv2_total += info["count"]
                lv2_obj["children"].append(lv3_obj)
            lv2_obj["count"] = lv2_total
            lv1_total += lv2_total
            lv1_obj["children"].append(lv2_obj)
        lv1_obj["count"] = lv1_total
        output.append(lv1_obj)
    return output


def print_summary(result):
    """コンソールに集計結果を表示"""
    grand_total = 0
    for lv1_name, lv2_dict in result.items():
        lv1_total = 0
        print(f"\n{'='*60}")
        print(f"【{lv1_name}】")
        print(f"{'='*60}")
        for lv2_name, lv3_dict in lv2_dict.items():
            lv2_total = sum(v["count"] for v in lv3_dict.values())
            lv1_total += lv2_total
            print(f"\n  ■ {lv2_name}  (小計: {lv2_total})")
            for lv3_name, info in lv3_dict.items():
                print(f"      {lv3_name:　<12s}  {info['count']:>4d}  {info['keywords']}")
        print(f"\n  >>> {lv1_name} 合計: {lv1_total}")
        grand_total += lv1_total
    print(f"\n{'='*60}")
    print(f"全カテゴリ延べ合計: {grand_total}  (重複含む)")
    print(f"{'='*60}")


def main():
    print(f"Loading articles from {INPUT_FILE} ...")
    articles = load_articles(INPUT_FILE)
    print(f"Loaded {len(articles)} articles.")

    print("Counting keyword matches ...")
    result = count_matches(articles, CATEGORY_TREE)

    print_summary(result)

    output = build_output(result)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
