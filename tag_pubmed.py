"""
PubMedクリーンデータに疾患カテゴリをタグ付け

日本語誌と同じカテゴリ体系 (categories_v2.json) を使用し、
英語キーワード + MeSH用語でマッチング。

Usage:
    python tag_pubmed.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import DATA_DIR

# ─── 疾患カテゴリ → 英語キーワード + MeSH マッピング ───
# 日本語カテゴリ名 → { "en_keywords": [...], "mesh_terms": [...] }
CATEGORY_EN_MAP = {
    # === I 感染症 ===
    "感冒": {
        "en_keywords": ["common cold", "upper respiratory infection",
                        "influenza", "pharyngitis", "acute nasopharyngitis"],
        "mesh": ["Common Cold", "Influenza, Human"],
    },
    "帯状疱疹": {
        "en_keywords": ["herpes zoster", "shingles", "postherpetic neuralgia"],
        "mesh": ["Herpes Zoster"],
    },

    # === II 悪性腫瘍 ===
    "化学療法支持": {
        "en_keywords": ["chemotherapy", "chemotherapy-induced", "supportive care",
                        "CINV", "anticancer", "anti-cancer", "chemo-"],
        "mesh": ["Antineoplastic Agents", "Drug Therapy"],
    },
    "消化器癌": {
        "en_keywords": ["gastric cancer", "colorectal cancer", "colon cancer",
                        "hepatocellular carcinoma", "pancreatic cancer",
                        "esophageal cancer", "liver cancer"],
        "mesh": ["Stomach Neoplasms", "Colorectal Neoplasms", "Liver Neoplasms",
                 "Pancreatic Neoplasms"],
    },
    "その他腫瘍": {
        "en_keywords": ["cancer", "tumor", "tumour", "carcinoma", "neoplasm",
                        "leukemia", "lymphoma", "sarcoma", "malignant",
                        "oncolog", "antitumor", "anti-tumor"],
        "mesh": ["Neoplasms"],
    },

    # === IV 内分泌・代謝 ===
    "糖尿病": {
        "en_keywords": ["diabetes", "diabetic", "hyperglycemia", "insulin resistance",
                        "blood glucose", "HbA1c", "type 2 diabetes"],
        "mesh": ["Diabetes Mellitus", "Diabetes Mellitus, Type 2"],
    },
    "甲状腺": {
        "en_keywords": ["thyroid", "graves", "hyperthyroidism", "hypothyroidism"],
        "mesh": ["Thyroid Diseases", "Graves Disease"],
    },

    # === V 精神・神経 ===
    "うつ": {
        "en_keywords": ["depression", "depressive", "antidepressant", "major depressive"],
        "mesh": ["Depression", "Depressive Disorder"],
    },
    "不安障害": {
        "en_keywords": ["anxiety", "panic disorder", "anxiolytic", "generalized anxiety"],
        "mesh": ["Anxiety Disorders", "Panic Disorder"],
    },
    "認知症": {
        "en_keywords": ["dementia", "alzheimer", "cognitive impairment", "BPSD",
                        "delirium", "cognitive decline", "neurodegener"],
        "mesh": ["Dementia", "Alzheimer Disease"],
    },

    # === 耳鼻科 ===
    "耳鳴・難聴": {
        "en_keywords": ["tinnitus", "hearing loss", "sudden deafness", "sensorineural"],
        "mesh": ["Tinnitus", "Hearing Loss"],
    },
    "アレルギー性鼻炎": {
        "en_keywords": ["allergic rhinitis", "hay fever", "pollinosis", "nasal allergy"],
        "mesh": ["Rhinitis, Allergic"],
    },
    "咽喉頭": {
        "en_keywords": ["pharynx", "larynx", "globus", "throat", "pharyngeal"],
        "mesh": ["Pharyngeal Diseases"],
    },

    # === 呼吸器 ===
    "喘息": {
        "en_keywords": ["asthma", "bronchial asthma", "wheezing"],
        "mesh": ["Asthma"],
    },
    "咳嗽": {
        "en_keywords": ["cough", "chronic cough", "sputum", "antitussive"],
        "mesh": ["Cough"],
    },
    "間質性肺炎": {
        "en_keywords": ["interstitial pneumonia", "interstitial lung", "pulmonary fibrosis",
                        "drug-induced pneumonitis"],
        "mesh": ["Lung Diseases, Interstitial"],
    },
    "COPD": {
        "en_keywords": ["COPD", "chronic obstructive", "bronchitis", "emphysema"],
        "mesh": ["Pulmonary Disease, Chronic Obstructive"],
    },

    # === 消化器 ===
    "胃炎・FD": {
        "en_keywords": ["gastritis", "functional dyspepsia", "dyspepsia", "epigastric",
                        "gastroparesis", "stomach"],
        "mesh": ["Gastritis", "Dyspepsia"],
    },
    "逆流性食道炎": {
        "en_keywords": ["GERD", "gastroesophageal reflux", "heartburn", "reflux esophagitis"],
        "mesh": ["Gastroesophageal Reflux"],
    },
    "肝疾患": {
        "en_keywords": ["hepatitis", "liver cirrhosis", "liver disease", "liver injury",
                        "hepatic", "hepatoprotect", "liver fibrosis", "fatty liver",
                        "NAFLD", "NASH"],
        "mesh": ["Liver Diseases", "Hepatitis"],
    },
    "IBD": {
        "en_keywords": ["crohn", "ulcerative colitis", "inflammatory bowel",
                        "IBD", "colitis"],
        "mesh": ["Inflammatory Bowel Diseases", "Colitis, Ulcerative", "Crohn Disease"],
    },
    "IBS": {
        "en_keywords": ["irritable bowel", "IBS"],
        "mesh": ["Irritable Bowel Syndrome"],
    },
    "イレウス": {
        "en_keywords": ["ileus", "bowel obstruction", "intestinal obstruction",
                        "postoperative ileus", "paralytic ileus"],
        "mesh": ["Ileus", "Intestinal Obstruction"],
    },

    # === 皮膚 ===
    "アトピー": {
        "en_keywords": ["atopic dermatitis", "atopic eczema", "eczema"],
        "mesh": ["Dermatitis, Atopic"],
    },
    "蕁麻疹": {
        "en_keywords": ["urticaria", "hives"],
        "mesh": ["Urticaria"],
    },
    "乾癬": {
        "en_keywords": ["psoriasis"],
        "mesh": ["Psoriasis"],
    },
    "掻痒症": {
        "en_keywords": ["pruritus", "itch", "itching"],
        "mesh": ["Pruritus"],
    },

    # === 筋骨格 ===
    "関節リウマチ": {
        "en_keywords": ["rheumatoid arthritis", "rheumatoid"],
        "mesh": ["Arthritis, Rheumatoid"],
    },
    "変形性関節症": {
        "en_keywords": ["osteoarthritis", "knee osteoarthritis", "degenerative joint"],
        "mesh": ["Osteoarthritis"],
    },
    "腰痛": {
        "en_keywords": ["low back pain", "lumbago", "lumbar pain", "back pain"],
        "mesh": ["Low Back Pain"],
    },
    "線維筋痛症": {
        "en_keywords": ["fibromyalgia"],
        "mesh": ["Fibromyalgia"],
    },

    # === 腎泌尿器 ===
    "腎疾患": {
        "en_keywords": ["nephritis", "nephrotic", "CKD", "chronic kidney", "renal failure",
                        "renal disease", "kidney disease", "glomerulonephritis"],
        "mesh": ["Kidney Diseases", "Renal Insufficiency"],
    },
    "膀胱炎": {
        "en_keywords": ["cystitis", "urinary tract infection"],
        "mesh": ["Cystitis", "Urinary Tract Infections"],
    },
    "前立腺": {
        "en_keywords": ["prostate", "prostatic", "BPH", "benign prostatic"],
        "mesh": ["Prostatic Diseases", "Prostatic Hyperplasia"],
    },

    # === 産婦人科 ===
    "不妊": {
        "en_keywords": ["infertility", "subfertility", "IVF", "in vitro fertilization",
                        "reproductive"],
        "mesh": ["Infertility"],
    },
    "妊娠": {
        "en_keywords": ["pregnancy", "pregnant", "morning sickness", "hyperemesis",
                        "gestational", "prenatal", "nausea of pregnancy"],
        "mesh": ["Pregnancy", "Pregnancy Complications"],
    },
    "産後": {
        "en_keywords": ["postpartum", "postnatal", "lactation", "breastfeeding",
                        "puerperal", "breast milk"],
        "mesh": ["Postpartum Period", "Lactation"],
    },

    # === 症状 ===
    "頭痛": {
        "en_keywords": ["headache", "migraine", "cephalalgia", "tension-type headache"],
        "mesh": ["Headache", "Migraine Disorders"],
    },
    "腹痛": {
        "en_keywords": ["abdominal pain", "stomachache", "visceral pain"],
        "mesh": ["Abdominal Pain"],
    },
    "神経痛": {
        "en_keywords": ["neuralgia", "trigeminal neuralgia", "neuropathic pain",
                        "neuropathy", "peripheral neuropathy"],
        "mesh": ["Neuralgia"],
    },
    "その他疼痛": {
        "en_keywords": ["chronic pain", "musculoskeletal pain", "shoulder pain",
                        "neck pain", "pain management", "pain relief",
                        "analgesic effect", "antinociceptive", "knee pain"],
        "mesh": ["Chronic Pain", "Musculoskeletal Pain"],
    },
    "冷え": {
        "en_keywords": ["cold hypersensitivity", "cold intolerance", "cold sensation",
                        "peripheral circulation", "chilliness", "hiesho",
                        "sensitivity to cold"],
        "mesh": [],
    },
    "倦怠感": {
        "en_keywords": ["fatigue", "malaise", "lassitude", "tiredness", "exhaustion",
                        "chronic fatigue"],
        "mesh": ["Fatigue"],
    },
    "浮腫": {
        "en_keywords": ["edema", "oedema", "swelling", "water retention", "lymphedema"],
        "mesh": ["Edema"],
    },
    "食欲不振": {
        "en_keywords": ["anorexia", "appetite loss", "loss of appetite", "poor appetite",
                        "cachexia"],
        "mesh": ["Anorexia", "Cachexia"],
    },
    "めまい": {
        "en_keywords": ["dizziness", "vertigo", "lightheadedness", "disequilibrium"],
        "mesh": ["Dizziness", "Vertigo"],
    },
    "不眠": {
        "en_keywords": ["insomnia", "sleep disorder", "sleep disturbance",
                        "sleep quality"],
        "mesh": ["Sleep Initiation and Maintenance Disorders"],
    },
    "更年期": {
        "en_keywords": ["menopause", "menopausal", "climacteric", "hot flash",
                        "hot flush", "postmenopausal"],
        "mesh": ["Menopause", "Hot Flashes"],
    },
    "動悸": {
        "en_keywords": ["palpitation", "autonomic dysfunction", "dysautonomia"],
        "mesh": [],
    },
    "便秘": {
        "en_keywords": ["constipation", "laxative"],
        "mesh": ["Constipation"],
    },
    "下痢": {
        "en_keywords": ["diarrhea", "diarrhoea", "loose stool"],
        "mesh": ["Diarrhea"],
    },
    "頻尿": {
        "en_keywords": ["urinary frequency", "nocturia", "overactive bladder",
                        "OAB", "lower urinary tract", "LUTS"],
        "mesh": ["Urinary Bladder, Overactive", "Nocturia"],
    },
    "月経関連": {
        "en_keywords": ["dysmenorrhea", "menstrual", "premenstrual", "PMS", "PMDD",
                        "menstrual irregularity", "amenorrhea"],
        "mesh": ["Dysmenorrhea", "Premenstrual Syndrome"],
    },
    "こむら返り": {
        "en_keywords": ["muscle cramp", "leg cramp", "calf cramp", "muscle spasm"],
        "mesh": ["Muscle Cramp"],
    },
    "口腔・舌": {
        "en_keywords": ["stomatitis", "oral mucositis", "oral ulcer", "dysphagia",
                        "xerostomia", "dry mouth", "glossodynia", "glossalgia",
                        "mouth ulcer", "oral candidiasis"],
        "mesh": ["Stomatitis", "Deglutition Disorders", "Xerostomia"],
    },
    "咳・痰": {
        "en_keywords": ["cough", "sputum", "expectoration", "antitussive", "phlegm"],
        "mesh": ["Cough"],
    },

    # === 鍼灸カテゴリ ===
    "鍼治療": {
        "en_keywords": ["acupuncture treatment", "acupuncture therapy",
                        "needle", "needling"],
        "mesh": ["Acupuncture Therapy"],
    },
    "灸治療": {
        "en_keywords": ["moxibustion", "moxa", "mugwort"],
        "mesh": ["Moxibustion"],
    },
    "電気鍼": {
        "en_keywords": ["electroacupuncture", "electro-acupuncture"],
        "mesh": ["Electroacupuncture"],
    },
    "あん摩・指圧": {
        "en_keywords": ["massage", "shiatsu", "acupressure", "tuina"],
        "mesh": ["Massage", "Acupressure"],
    },
    "経穴": {
        "en_keywords": ["acupuncture point", "acupoint", "ST36", "LI4", "BL23",
                        "Zusanli", "Hegu"],
        "mesh": ["Acupuncture Points"],
    },
    "経絡": {
        "en_keywords": ["meridian", "channel theory"],
        "mesh": ["Meridians"],
    },
    "有害事象": {
        "en_keywords": ["adverse event", "pneumothorax", "needle breakage",
                        "acupuncture safety", "acupuncture complication"],
        "mesh": [],
    },
    "感染管理": {
        "en_keywords": ["infection control", "sterilization", "disinfection",
                        "needle hygiene"],
        "mesh": ["Infection Control"],
    },
    "鍼灸教育": {
        "en_keywords": ["acupuncture education", "training", "curriculum",
                        "competency"],
        "mesh": [],
    },
    "スポーツ": {
        "en_keywords": ["sports medicine", "athlete", "athletic performance",
                        "sports injury"],
        "mesh": ["Sports Medicine", "Athletic Performance"],
    },
    "美容鍼": {
        "en_keywords": ["cosmetic acupuncture", "facial acupuncture", "aesthetic"],
        "mesh": [],
    },
    "メカニズム": {
        "en_keywords": ["mechanism of action", "analgesic mechanism", "fMRI",
                        "brain imaging", "electromyograph", "neural pathway",
                        "action mechanism"],
        "mesh": [],
    },

    # === 漢方理論 ===
    "傷寒論": {
        "en_keywords": ["Shang Han Lun", "Shanghan", "treatise on cold damage"],
        "mesh": [],
    },
    "金匱要略": {
        "en_keywords": ["Jin Gui", "Jingui", "essential prescriptions"],
        "mesh": [],
    },
    "弁証論治": {
        "en_keywords": ["pattern identification", "qi-blood-water",
                        "yin-yang", "deficiency-excess", "Kampo diagnosis",
                        "pattern diagnosis", "TCM pattern", "sho diagnosis",
                        "kampo pattern", "zheng classification"],
        "mesh": [],
    },
    "腹証": {
        "en_keywords": ["abdominal diagnosis", "Fukushin", "abdominal palpation",
                        "abdominal examination"],
        "mesh": [],
    },
    "漢方教育": {
        "en_keywords": ["Kampo education", "Kampo training", "Kampo curriculum",
                        "medical education"],
        "mesh": [],
    },

    # === 安全性 ===
    "副作用": {
        "en_keywords": ["adverse drug reaction", "side effect of herbal",
                        "pseudoaldosteronism", "rhabdomyolysis", "drug eruption",
                        "drug-induced liver injury", "hepatotoxicity",
                        "herbal toxicity", "kampo adverse"],
        "mesh": ["Drug-Related Side Effects and Adverse Reactions"],
    },
    "相互作用": {
        "en_keywords": ["drug interaction", "herb-drug interaction", "drug combination",
                        "concomitant", "co-administration", "CYP", "cytochrome"],
        "mesh": ["Drug Interactions", "Herb-Drug Interactions"],
    },

    # === 臨床セッティング ===
    "術後": {
        "en_keywords": ["postoperative", "perioperative", "after surgery", "surgical"],
        "mesh": ["Postoperative Complications", "Perioperative Care"],
    },
    "透析": {
        "en_keywords": ["dialysis", "hemodialysis", "haemodialysis"],
        "mesh": ["Renal Dialysis"],
    },
    "緩和": {
        "en_keywords": ["palliative care", "end-of-life", "terminal care",
                        "hospice", "cancer supportive care"],
        "mesh": ["Palliative Care", "Terminal Care", "Hospice Care"],
    },

    # === 研究方法論 ===
    "RCT": {
        "en_keywords": ["randomized controlled trial", "randomised controlled trial",
                        "RCT", "randomization"],
        "mesh": [],
    },
    "SR・メタ": {
        "en_keywords": ["systematic review", "meta-analysis", "meta analysis"],
        "mesh": [],
    },
    "ガイドライン": {
        "en_keywords": ["guideline", "clinical practice guideline", "recommendation",
                        "consensus statement"],
        "mesh": ["Practice Guidelines as Topic"],
    },
}


def tag_article(art):
    """1論文に疾患カテゴリをタグ付け"""
    title = (art.get("title", "") or "").lower()
    abstract = (art.get("abstract", "") or "").lower()
    text = title + " " + abstract
    mesh_set = set(m.lower() for m in art.get("mesh_terms", []))

    matched = []
    for cat_name, mapping in CATEGORY_EN_MAP.items():
        # キーワードマッチ
        kw_match = any(kw.lower() in text for kw in mapping["en_keywords"])
        # MeSHマッチ
        mesh_match = any(m.lower() in mesh_set for m in mapping.get("mesh", []))

        if kw_match or mesh_match:
            matched.append(cat_name)

    return matched


def main():
    pubmed_dir = DATA_DIR / "pubmed"
    input_path = pubmed_dir / "pubmed_cleaned.json"

    with open(input_path, encoding="utf-8") as f:
        arts = json.load(f)

    print(f"入力: {len(arts)} 件")

    # タグ付け
    cat_counts = Counter()
    tagged_count = 0
    multi_count = 0

    for art in arts:
        tags = tag_article(art)
        art["disease_categories"] = tags

        if tags:
            tagged_count += 1
            cat_counts.update(tags)
        if len(tags) > 1:
            multi_count += 1

    # 保存
    out_path = pubmed_dir / "pubmed_tagged.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=2)

    print(f"\n=== タグ付け結果 ===")
    print(f"タグ付き: {tagged_count}/{len(arts)} ({100*tagged_count/len(arts):.1f}%)")
    print(f"複数カテゴリ: {multi_count}")
    print(f"タグなし: {len(arts) - tagged_count}")
    print(f"保存: {out_path.name}")

    # カテゴリ別件数
    print(f"\n=== カテゴリ別件数 (上位30) ===")
    for cat, count in cat_counts.most_common(30):
        print(f"  {count:5d}  {cat}")

    # カテゴリ別件数（全件）
    print(f"\n=== 全カテゴリ ===")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:5d}  {cat}")

    # タグなし論文のサンプル
    untagged = [a for a in arts if not a["disease_categories"]]
    print(f"\n=== タグなしサンプル (10件) ===")
    import random
    random.seed(42)
    for a in random.sample(untagged, min(10, len(untagged))):
        mesh = ", ".join(a.get("mesh_terms", [])[:3])
        print(f"  [{a['year']}] {a['title'][:90]}")
        print(f"         MeSH: {mesh}")


if __name__ == "__main__":
    main()
