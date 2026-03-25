
import json

with open("data/metadata_with_abstracts.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

from dictionaries import FORMULAS, EXTRA_FORMULAS

formula_info = {}
for k, v in FORMULAS.items():
    formula_info[v["name"]] = {"origin": v.get("origin",""), "number": k, "yomi": v.get("yomi","")}
for k, v in EXTRA_FORMULAS.items():
    formula_info[v["name"]] = {"origin": v.get("origin",""), "number": v.get("number",""), "yomi": v.get("yomi","")}

all_names = sorted(formula_info.keys(), key=len, reverse=True)

def extract_formulas(text):
    found = []
    remaining = text
    for name in all_names:
        if name in remaining:
            found.append(name)
            remaining = remaining.replace(name, chr(0) * len(name))
    return found

categories = {
    "ICD疾患分類": {
        "I 感染症": ["感染","結核","肝炎","ウイルス","帯状疱疹"],
        "II 悪性腫瘍": ["癌","がん","腫瘍","悪性","化学療法","抗がん剤","白血病"],
        "IV 内分泌・代謝": ["糖尿病","甲状腺","脂質異常","痛風"],
        "V 精神・行動": ["うつ","抑うつ","統合失調","パニック障害","PTSD"],
        "VIII 耳": ["耳鳴","難聴","突発性難聴","メニエール"],
        "X 呼吸器": ["感冒","風邪","上気道炎","インフルエンザ","肺炎","喘息","気管支炎","COPD","間質性肺炎"],
        "XI 消化器": ["胃炎","胃潰瘍","十二指腸","逆流性食道炎","GERD","肝硬変","肝障害","膵炎","胆石","クローン","潰瘍性大腸炎","過敏性腸","IBS"],
        "XII 皮膚": ["湿疹","アトピー","皮膚炎","蕁麻疹","乾癬","掻痒"],
        "XIII 筋骨格": ["関節痛","関節リウマチ","リウマチ","変形性膝","腰痛","五十肩","骨粗鬆","線維筋痛"],
        "XIV 泌尿・生殖器": ["膀胱炎","尿路感染","腎炎","ネフローゼ","CKD","腎不全","前立腺","不妊","子宮内膜症"],
        "XV 産科": ["妊娠","つわり","産後","分娩","母乳"],
    },
    "症候から探す": {
        "疼痛": ["疼痛","痛み","神経痛","頭痛","片頭痛","腹痛","三叉神経痛"],
        "冷え": ["冷え","冷え症","冷え性"],
        "倦怠感・疲労": ["倦怠","疲労","だるさ","全身倦怠"],
        "めまい・ふらつき": ["めまい","眩暈","ふらつき"],
        "不眠": ["不眠","睡眠障害","入眠困難"],
        "不定愁訴・更年期": ["不定愁訴","更年期","ホットフラッシュ","のぼせ"],
        "自律神経症状": ["自律神経","動悸","発汗"],
        "浮腫・むくみ": ["浮腫","むくみ","水腫"],
        "食欲不振": ["食欲不振","食欲低下","食思不振"],
        "便秘": ["便秘"],
        "下痢": ["下痢","軟便"],
        "咳・痰": ["咳嗽","喀痰","咳","痰"],
        "こむら返り": ["こむら返り","筋痙攣","腓腹筋"],
        "月経関連症状": ["月経痛","月経不順","月経困難","生理痛","PMS"],
        "排尿症状": ["頻尿","夜間頻尿","排尿障害","過活動膀胱"],
        "口腔・咽頭症状": ["口内炎","口腔","咽頭","嚥下","口渇","舌痛","梅核気"],
        "鼻症状": ["アレルギー性鼻炎","花粉症","鼻閉"],
    },
    "その他": {
        "術後・周術期": ["術後","手術後","周術期","イレウス","腸閉塞"],
        "透析関連": ["透析","血液透析"],
        "緩和ケア": ["緩和","終末期","QOL"],
    }
}

flat_disease_map = {}
disease_to_category = {}
for cat_group, subcats in categories.items():
    for subcat, kws in subcats.items():
        flat_disease_map[subcat] = kws
        disease_to_category[subcat] = cat_group

structured = []
for a in articles:
    title = a.get("title_ja","")
    abstract = a.get("abstract_ja","")
    combined = title + " " + abstract
    year = str(a.get("pubyear",""))[:4]
    formulas = extract_formulas(combined)
    diseases = [d for d, kws in flat_disease_map.items() if any(kw in combined for kw in kws)]
    structured.append({
        "title": title, "year": year, "authors": a.get("authors_ja",""),
        "link": a.get("link",""), "abstract": abstract[:500] if abstract else "",
        "formulas": formulas, "diseases": diseases,
    })

formula_index = {}
for i, s in enumerate(structured):
    for f in s["formulas"]:
        formula_index.setdefault(f, []).append(i)

disease_index = {}
for i, s in enumerate(structured):
    for d in s["diseases"]:
        disease_index.setdefault(d, []).append(i)

formula_summary = {}
for fname in sorted(formula_index.keys(), key=lambda x: -len(formula_index[x])):
    indices = formula_index[fname]
    info = formula_info.get(fname, {})
    d_counter = {}
    for idx in indices:
        for d in structured[idx]["diseases"]:
            d_counter[d] = d_counter.get(d, 0) + 1
    formula_summary[fname] = {
        "count": len(indices), "origin": info.get("origin",""),
        "yomi": info.get("yomi",""), "number": info.get("number",""),
        "top_diseases": sorted(d_counter.items(), key=lambda x: -x[1])[:5],
    }

category_structure = {}
for cat_group, subcats in categories.items():
    category_structure[cat_group] = {}
    for subcat in subcats:
        count = len(disease_index.get(subcat, []))
        if count > 0:
            category_structure[cat_group][subcat] = count

db = {
    "articles": structured,
    "formula_index": {k: v for k, v in sorted(formula_index.items(), key=lambda x: -len(x[1]))},
    "disease_index": {k: v for k, v in sorted(disease_index.items(), key=lambda x: -len(x[1]))},
    "formula_summary": formula_summary,
    "category_structure": category_structure,
    "disease_to_category": disease_to_category,
    "total_articles": len(articles),
    "total_with_formula": sum(1 for s in structured if s["formulas"]),
    "total_with_abstract": sum(1 for s in structured if s["abstract"]),
}

with open("output/kampo_db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False)

print("DB rebuilt")
for cg, sc in category_structure.items():
    total = sum(sc.values())
    print(f"\n{cg} ({total})")
    for s, c in sorted(sc.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")
