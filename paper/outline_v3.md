# Where Is the Evidence? Mapping 43 Years of Kampo and Acupuncture Research for Primary Care

**Target journal**: Journal of General Family Medicine (JGFM)
**Article type**: Original Article
**Date**: 2025-03-25 (v3: バタフライチャート中心、過剰解釈を削除)

---

## Title candidates
1. Where Is the Evidence? Mapping 43 Years of Kampo and Acupuncture Research for Primary Care
2. Mapping 43 Years of Traditional Japanese Medicine: A Bibliometric Analysis and Interactive Evidence Tool for Primary Care
3. Where Is the Evidence? An Interactive Map of 2,653 Kampo and Acupuncture Articles for Primary Care Physicians

---

## Abstract (structured, 250 words)

**Background**: Over 80% of Japanese physicians prescribe Kampo, and acupuncture is widely used. Yet clinical evidence is scattered across specialty journals in Japanese, making it inaccessible to primary care physicians. No resource integrates Kampo and acupuncture evidence into a single searchable system.

**Objective**: To map the research landscape of Kampo and acupuncture across common primary care conditions, analyze research trends and gaps, and develop an interactive evidence navigation tool.

**Methods**: All articles from the Journal of Kampo Medicine (1982-2024; n=2,003) and the Journal of the Japan Society of Acupuncture and Moxibustion (2007-2024; n=650) were extracted from J-STAGE. Articles were classified by 246 Kampo formulas and 59 disease categories (ICD-11-based). An interactive HTML tool was deployed on GitHub Pages.

**Results**: Research was highly concentrated: the top 10 formulas accounted for 25% of all mentions, while 42% of formulas had only 1-2 articles. Kampo and acupuncture research showed striking separation—gastrointestinal conditions were studied almost exclusively in Kampo, while sports medicine was acupuncture-only. Only 44 authors published in both journals. A single adverse event (Shosaikoto-induced interstitial pneumonia, 1994) reshaped the Kampo research landscape for a decade. The interactive tool enables primary care physicians to search across both fields simultaneously for the first time.

**Conclusions**: This bibliometric analysis reveals the concentration, separation, and hidden breadth of traditional Japanese medicine research. The interactive tool, combined with existing resources (EKAT for RCTs, Yasunaga et al. for real-world data), enables triangulation of the full evidence landscape.

---

## 1. Introduction

### 1.1 Kampo and acupuncture in Japanese primary care
- 90% of physicians have Kampo prescribing experience (Uneda 2024)
- 148 Kampo formulas covered by national health insurance
- Acupuncture is a common referral option
- Yet most primary care physicians lack systematic access to the evidence

### 1.2 Existing evidence resources and their limitations
- **EKAT** (Evidence Reports of Kampo Treatment): 512 structured RCT abstracts → RCTs only
- **Yasunaga et al.**: 37 studies using DPC/NDB databases (millions of patients) → individual formula-disease pairs only
- **Gap**: No resource captures the full spectrum of clinical evidence (especially case reports), and none integrates Kampo with acupuncture

### 1.3 The value of case reports in Kampo
- Kampo treatment is individualized by "Sho" (pattern diagnosis)
- Case reports capture successful treatment of conditions refractory to Western medicine
- These constitute the majority of Kampo literature and represent 43 years of accumulated clinical wisdom
- The audience—family physicians—understands the value of n=1 clinical knowledge

### 1.4 Study objectives
1. Map all articles from two core traditional medicine journals (2,653 articles, 43 years)
2. Analyze research concentration, temporal trends, and the Kampo-acupuncture divide
3. Develop and deploy an interactive evidence navigation tool for primary care

---

## 2. Methods

### 2.1 Study design
- Scoping review following PRISMA-ScR guidelines (Tricco 2018)

### 2.2 Data sources
- Journal of Kampo Medicine (日本東洋医学雑誌, 1982-2024): 2,003 articles
- Journal of the Japan Society of Acupuncture and Moxibustion (全日本鍼灸学会雑誌, 2007-2024): 650 articles

### 2.3 Data extraction
- J-STAGE API + web scraping for metadata (title, authors, year, DOI)
- Abstracts retrieved individually (Kampo: 1,666/2,003 obtained)

### 2.4 Kampo formula identification
- Dictionary of 246 formulas (kanji, hiragana, formula number, classical origin)
- Regex matching against title + abstract
- Validation: 234 manually reviewed articles, Precision = 100%

### 2.5 Disease classification
- ICD-11-based two-level taxonomy (14 major categories → 59 subcategories)
- Keyword matching against title + abstract
- Limitation: keyword-based (acknowledged; 234-article manual review for validation)

### 2.6 Analyses
- Descriptive statistics: frequencies, proportions, temporal trends
- Fragmentation index: (unique formulas / articles) per disease category
- Kampo vs. acupuncture disease coverage comparison
- Author analysis: publication counts, cross-journal overlap

### 2.7 Interactive tool
- Single-file HTML/JavaScript/CSS application
- Features: category browsing, formula lookup, author search, free-text search
- Deployed on GitHub Pages

---

## 3. Results

### 3.1 Overview (Figure 1: temporal trends)
- 2,653 articles total (Kampo 2,003 + Acupuncture 650)
- 246 unique Kampo formulas identified in 1,124 articles (56%)
- 2,653 unique authors; **62% published only 1 article**
- Top author: Terasawa K. with 219 articles (11% of Kampo journal)

### 3.2 Kampo vs. Acupuncture disease coverage (Figure 2 = KEY FIGURE: butterfly chart)
Comparison of disease-category research volume between the two journals:

**Kampo-dominant conditions** (studied almost exclusively via Kampo):
- Gastrointestinal diseases: Kampo dominant, acupuncture near zero
- Psychiatric/neurological: Kampo dominant (Yokukansan for BPSD, etc.)
- Cold sensitivity (冷え): 19 Kampo articles, 3 acupuncture

**Acupuncture-dominant conditions**:
- Sports medicine/musculoskeletal: A=23 vs K=0
- Back pain: A=13 vs K=4
- Infertility research: acupuncture surging in 2020s

**Shared conditions** (studied in both):
- Cancer supportive care: both journals active
- Pain: both contribute, different approaches

**Key observations** (all factual):
- The two journals cover largely non-overlapping disease areas
- RCTs: Kampo 4 (0.2%) vs Acupuncture 13 (2.0%)
- Cross-journal authors: only 44 individuals out of 2,653 total

### 3.3 Research concentration paradox
- Top 10 formulas = 25% of all formula mentions
- 103 formulas (42%) have ≤2 articles → half the pharmacopoeia is understudied
- **Fragmentation index**: IBS = 2.18 (24 formulas in 11 articles; no consensus) vs Pain = 0.54 (concentrated)
- **Diarrhea paradox**: 76 articles, 79 formulas — more formulas than articles

### 3.4 Clinical events reshape research (Figure 3: time series)
- **Shosaikoto collapse**: 1994 interstitial pneumonia deaths → research dropped to 0.3×
- **Yokukansan rise**: 2005 Iwasaki BPSD paper → research surged 4.5×
- Safety research peaked in 1990s (82 articles) → declining since (2020s: 33)

### 3.5 Hidden breadth: conditions primary care physicians may not expect
(All factual findings — no quality judgments)
- Cancer palliative care: acupuncture 16 articles, Kampo active
- Parkinson's disease: 5 articles (acupuncture)
- Post-viral anosmia: 8 Kampo articles (COVID-era relevance)
- Cold sensitivity (冷え): 19+3 articles — a condition with no Western medicine concept
- Chronic fatigue: 21+4 articles
- Muscle cramps: 14 Kampo articles (Shakuyakukanzoto)

### 3.6 Tool walkthrough (Figure 4: screenshots)
- Scenario 1: "Chronic headache + cold sensitivity" → discovers relevant case reports
- Scenario 2: "Back pain" → Kampo 4 + Acupuncture 13 integrated view (tool's unique value)
- Scenario 3: Keyword search across both journals simultaneously

---

## 4. Discussion

### 4.1 What the research landscape reveals
- Research is concentrated in specific areas — this is the first quantitative demonstration
- The Kampo-acupuncture divide is striking: separate diseases, separate researchers, separate journals
- Within this concentrated landscape, there is clinical knowledge that most primary care physicians have never accessed

### 4.2 Triangulation with existing resources
- **This tool**: Research literature map (breadth: 43 years, 2,653 articles)
- **EKAT**: RCT structured reviews (quality: 512 RCTs)
- **Yasunaga et al.**: Real-world data (scale: DPC millions of patients)
- Example — Daikenchuto:
  - This tool: 34 articles across 9 disease categories
  - EKAT: Multiple RCTs for postoperative ileus
  - Yasunaga 2011/2018/2021: DPC validation for ileus, COPD, ICU
- **All three are needed for the complete picture**

### 4.3 The value and limitations of case reports
- RCTs in Kampo journal: only 4 (0.2%) — but this reflects the nature of Sho-based individualization
- Case reports grew from 13 (1980s) to 125 (2010s) — clinical wisdom is accumulating
- This tool makes 43 years of accumulated clinical experience searchable for the first time

### 4.4 Research infrastructure fragility
- One author (Terasawa) = 11% of all Kampo journal output
- 62% of authors published only once
- Kampo-Acupuncture personnel divide: only 44 cross-journal authors
- Generational shift: 2020s show new leading authors (Tahara, Yoshinaga, Inoue)

### 4.5 Implications for primary care
- This tool allows primary care physicians to discover what research exists for conditions they encounter
- Integrated Kampo + acupuncture search reveals the full range of traditional medicine options
- COVID sequelae: Kampo responded rapidly with clinical cases (anosmia, fatigue)

### 4.6 Limitations
1. Keyword-based disease classification (validated on 234 articles)
2. Two journals only (other journals contain Kampo/acupuncture articles)
3. No systematic study design classification
4. English paper but source articles in Japanese
5. Acupuncture journal coverage starts 2007 (vs. Kampo 1982)
6. Research volume ≠ clinical utility. Low article count does not mean a treatment is ineffective; high article count does not guarantee effectiveness.

### 4.7 Future directions
- Intervention study: does tool use change primary care physicians' clinical behavior? (Paper 2)
- Integration with EKAT and Yasunaga RWD for a unified evidence platform
- Expansion to other journals (JGFM, primary care journals)
- Bilingual (EN/JP) tool interface

---

## 5. Conclusion
This bibliometric analysis of 2,653 articles from Japan's two core traditional medicine journals reveals a research landscape marked by concentration, separation, and hidden breadth. Kampo and acupuncture research occupy largely non-overlapping disease areas, with only 44 authors bridging the two fields. By integrating both journals into an interactive tool, and positioning this alongside EKAT (RCTs) and real-world data studies, we provide primary care physicians with a means to discover and navigate the full range of traditional Japanese medicine evidence.

---

## Figures

| Figure | Content | Type |
|--------|---------|------|
| Fig 1 | Publication trends by decade (Kampo/Acupuncture stacked) | Stacked bar chart |
| **Fig 2** | **Kampo vs. Acupuncture disease coverage (butterfly chart)** | **Butterfly chart** |
| Fig 3 | Temporal dynamics: Shosaikoto collapse + Yokukansan rise | Line chart |
| Fig 4 | Tool screenshots (clinical scenarios) | Screenshots |

## Tables

| Table | Content |
|-------|---------|
| Table 1 | Dataset summary (2 journals, key metrics) |
| Table 2 | Comparison with existing resources (EKAT, Yasunaga RWD, this tool) |

## Supplementary
- Table S1: 246 formulas complete list
- Table S2: 59 disease categories with keywords
- Table S3: Disease category × Kampo/Acupuncture article counts (full data behind Fig 2)
- Table S4: Top 30 authors with publication spans
- Online tool: GitHub Pages URL

---

## Key references
- Uneda 2024: Kampo physician survey (Trad Kampo Med)
- Arai 2021: Need for Kampo evidence (J Integr Med)
- EKAT / Motoo: Evidence Reports of Kampo Treatment
- Yasunaga 2020: Outpatient Kampo prescriptions nationwide (Intern Med)
- Yasunaga 2018: Daikenchuto × COPD (Int J COPD)
- Yasunaga 2023: Yokukansan × BPSD (Geriatr Gerontol Int)
- Yasunaga 2025: Kampo in cancer inpatients 14-year trend (Int J Clin Oncol)
- Tricco 2018: PRISMA-ScR guideline

---

## 次のアクションアイテム
- [ ] Fig 1（時系列）作図
- [ ] Fig 2（バタフライチャート）最終版作図
- [ ] Fig 3（小柴胡湯・抑肝散）作図
- [ ] Fig 4 ツールスクリーンショット
- [ ] ツールUI改修（英語化、カテゴリフィルタ修正）
- [ ] GitHub Pages公開準備
- [ ] 共著者候補の検討
- [ ] PRISMA-ScRチェックリスト確認
- [ ] 本文ドラフト着手
