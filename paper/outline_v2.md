# Where Is the Evidence? A Three-Layer Evidence Map of Kampo, Acupuncture, and Western Medicine for Primary Care

**Target journal**: Journal of General Family Medicine (JGFM)
**Article type**: Original Article
**Date**: 2025-03-25 (v2: 今日の議論を全反映)

---

## Title candidates
1. Where Is the Evidence? A Three-Layer Evidence Map of Kampo, Acupuncture, and Western Medicine for Primary Care
2. Mapping 43 Years of Traditional Japanese Medicine: An Interactive Evidence Map Comparing Kampo, Acupuncture, and Western Medicine
3. Bridging Three Worlds: An Evidence Map of 2,653 Kampo and Acupuncture Articles Against Western Medicine for Primary Care Physicians

---

## Abstract (structured, 250 words)

**Background**: Over 80% of Japanese physicians prescribe Kampo, and acupuncture is widely used. Yet clinical evidence is scattered across specialty journals in Japanese, making it inaccessible to primary care physicians. No resource integrates Kampo and acupuncture evidence or positions it relative to Western medicine.

**Objective**: To construct a three-layer evidence map comparing Kampo, acupuncture, and Western medicine across common primary care conditions, and to develop an interactive tool for evidence navigation.

**Methods**: All articles from the Journal of Kampo Medicine (1982-2024; n=2,003) and the Journal of the Japan Society of Acupuncture and Moxibustion (2007-2024; n=650) were extracted from J-STAGE. Articles were classified by 246 Kampo formulas and 59 disease categories (ICD-11-based). Western medicine evidence strength for each condition was rated as Strong/Moderate/Weak based on guideline and RCT availability. An interactive HTML tool was deployed on GitHub Pages.

**Results**: The three-layer map revealed conditions where traditional medicine uniquely fills Western medicine gaps (e.g., cold sensitivity, chronic fatigue, muscle cramps, tinnitus). Research was highly concentrated: the top 10 formulas accounted for 25% of all mentions, while 42% of formulas had only 1-2 articles. Kampo and acupuncture research showed striking separation—back pain was dominated by acupuncture (K=4 vs A=13) while gastrointestinal conditions were Kampo-only. Only 44 authors published in both journals. A single adverse event (Shosaikoto-induced interstitial pneumonia, 1994) reshaped the research landscape for a decade.

**Conclusions**: The three-layer evidence map reveals where traditional Japanese medicine offers unique clinical value for primary care. The interactive tool, combined with existing resources (EKAT for RCTs, Yasunaga et al. for real-world data), enables triangulation of the full Kampo evidence landscape.

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
- (2-3 sentences; the audience—family physicians—understands the value of n=1 clinical knowledge)

### 1.4 Study objectives
1. Map all articles from two core traditional medicine journals (2,653 articles, 43 years)
2. Construct a three-layer evidence map: Western medicine × Kampo × Acupuncture
3. Analyze research trends, concentration, and gaps
4. Develop and deploy an interactive evidence navigation tool for primary care

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
- Keyword matching
- Limitation: keyword-based (acknowledged; 234-article manual review for validation)

### 2.6 Western medicine evidence rating
- For each of 59 conditions, evidence strength classified as:
  - **A (Strong)**: Multiple RCTs, established guidelines, clear treatment algorithms
  - **M (Moderate)**: Guidelines exist but effect sizes small or refractory cases common
  - **B (Weak)**: Few/no high-quality RCTs, limited treatment options
- Rated by the lead author (primary care physician) based on literature review

### 2.7 Analyses
- Descriptive statistics: frequencies, proportions, temporal trends
- Fragmentation index: (unique formulas / articles) per disease category
- Three-layer evidence map: 59 conditions × 3 modalities
- Author analysis: publication counts, cross-journal overlap

### 2.8 Interactive tool
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

### 3.2 Three-Layer Evidence Map (Figure 2 = KEY FIGURE)
59 conditions × Western medicine × Kampo × Acupuncture

**Quadrant 1: Western WEAK × Traditional STRONG — unique value of TJM**
| Condition | Western | Kampo | Acupuncture | Clinical implication |
|-----------|---------|-------|-------------|---------------------|
| Cold sensitivity (冷え) | No concept | 19 | 3 | TJM fills a conceptual void |
| Chronic fatigue | Few RCTs | 21 | 4 | TJM as primary option |
| Muscle cramps | Quinine restricted | 14 | 0 | Shakuyakukanzoto widely studied |
| Tinnitus (chronic) | No effective drug | 10 | 2 | TJM for symptom management |
| BPSD | High-risk drugs | 4 | 5 | Acupuncture > Kampo here |
| Post-viral anosmia | No established tx | 8 | 1 | COVID-era relevance |

**Quadrant 2: Both STRONG — complementary evidence**
- Headache, insomnia, atopic dermatitis, asthma, cancer supportive care

**Quadrant 3: Both WEAK — true evidence gaps**
- Post-viral anosmia (emerging)

**Quadrant 4: Western STRONG, TJM WEAK — Western medicine sufficient**
- Cystitis, influenza, diabetes, COPD, hypertension

### 3.3 Research concentration paradox
- Top 10 formulas = 25% of all formula mentions
- 103 formulas (42%) have ≤2 articles → half the pharmacopoeia is unstudied
- **Fragmentation index**: IBS = 2.18 (24 formulas in 11 articles; no consensus) vs Pain = 0.54 (concentrated)
- **Diarrhea paradox**: 76 articles, 79 formulas — more formulas than articles

### 3.4 Clinical events reshape research (Figure 3: time series)
- **Shosaikoto collapse**: 1994 interstitial pneumonia deaths → research dropped to 0.3×
- **Yokukansan rise**: 2005 Iwasaki BPSD paper → research surged 4.5×
- Safety research peaked in 1990s (82 articles) → declining since (2020s: 33)

### 3.5 The Kampo-Acupuncture divide
- **Back pain**: K=4 vs A=13 (acupuncture dominates)
- **GI diseases**: Kampo only (acupuncture = 0)
- **Sports**: A=23 vs K=0
- **Infertility**: Kampo avg. 2009 → Acupuncture avg. 2022 (13-year lag)
- **COVID-19**: Kampo 17 (clinical cases) vs Acupuncture 6 (only 1 clinical)
- **RCTs**: Kampo 4 (0.2%) vs Acupuncture 13 (2.0%) — acupuncture is 10× more evidence-oriented
- Cross-journal authors: only 44 individuals

### 3.6 Tool walkthrough (Figure 4: screenshots)
- Scenario 1: "Chronic headache + cold sensitivity" → finds Tokishigyakukagoshuyushokyoto case reports
- Scenario 2: "Keishibukuryogan × psychiatric" → discovers unexpected 10 articles
- Scenario 3: "Back pain" → Kampo 4 + Acupuncture 13 integrated view (tool's unique value)

---

## 4. Discussion

### 4.1 The three-layer map as a clinical compass
- First visualization of where TJM uniquely fills Western medicine gaps
- Q1 conditions (cold sensitivity, fatigue, cramps, tinnitus): "when stuck, try Kampo" now has an evidence basis
- Q4 conditions: unnecessary to use TJM where Western medicine is effective

### 4.2 Triangulation with existing resources
- **This tool**: Research literature map (breadth: 43 years, 2,653 articles)
- **EKAT**: RCT structured reviews (quality: 512 RCTs)
- **Yasunaga et al.**: Real-world data (scale: DPC millions of patients)
- Example — Daikenchuto:
  - This tool: 34 articles across 9 disease categories (case reports)
  - EKAT: Multiple RCTs for postoperative ileus
  - Yasunaga 2011/2018/2021: DPC validation for ileus, COPD, ICU
- **All three are needed for the complete picture**

### 4.3 The value and limitations of case reports
- RCTs in Kampo journal: only 4 (0.2%) — but this is not a failure
- Case reports grew from 13 (1980s) to 125 (2010s) — clinical wisdom is accumulating
- Sho-based individualization makes RCT averaging problematic
- This tool makes 43 years of accumulated clinical experience searchable

### 4.4 Research infrastructure fragility
- One author (Terasawa) = 11% of all Kampo journal output
- 62% of authors published only once
- Kampo-Acupuncture personnel divide: only 44 cross-journal authors
- Generational shift needed: 2020s show new leading authors (Tahara, Yoshinaga, Inoue)

### 4.5 Implications for primary care
- Q1 conditions: use this tool to explore Kampo options when Western medicine falls short
- Back pain: consider acupuncture referral (stronger evidence than Kampo)
- COVID sequelae: Kampo responded rapidly with clinical cases (anosmia, fatigue)

### 4.6 Limitations
1. Keyword-based disease classification (validated on 234 articles)
2. Two journals only (other journals contain Kampo/acupuncture articles)
3. Western medicine evidence rating is simplified (A/M/B)
4. English paper but source articles in Japanese
5. No systematic study design classification
6. Acupuncture journal coverage starts 2007 (vs. Kampo 1982)

### 4.7 Future directions
- AI-powered case consultation (Claude API integration)
- Intervention study: does tool use change primary care prescribing behavior? (Paper 2)
- Integration with EKAT and Yasunaga RWD for a unified evidence platform
- Expansion to other journals (JGFM, primary care journals)
- Bilingual (EN/JP) tool interface

---

## 5. Conclusion
The three-layer evidence map reveals that traditional Japanese medicine offers unique clinical value precisely where Western medicine struggles—cold sensitivity, chronic fatigue, muscle cramps, and tinnitus. By integrating 2,653 articles from Japan's two core traditional medicine journals into an interactive tool, and positioning this alongside EKAT (RCTs) and real-world data studies, we provide primary care physicians with a clinical compass for evidence-informed use of Kampo and acupuncture.

---

## Figures

| Figure | Content | Type |
|--------|---------|------|
| Fig 1 | Publication trends by decade (Kampo/Acupuncture stacked) | Bar chart |
| **Fig 2** | **Three-layer evidence map (59 conditions × W/K/A)** | **Heatmap/bubble** |
| Fig 3 | Temporal dynamics: Shosaikoto collapse + Yokukansan rise | Line chart |
| Fig 4 | Tool screenshots (3 clinical scenarios) | Screenshots |

## Tables

| Table | Content |
|-------|---------|
| Table 1 | Dataset summary (2 journals, key metrics) |
| Table 2 | Comparison with existing resources (EKAT, Yasunaga RWD, this tool) |
| Table 3 | Quadrant 1 conditions: TJM evidence where Western medicine is weak |

## Supplementary
- Table S1: 246 formulas complete list
- Table S2: 59 disease categories with keywords
- Table S3: Full three-layer map data (59 × 3)
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
- [ ] Fig 2 (3層マップ) のビジュアル作成
- [ ] Fig 3 (時系列) のデータ確定・作図
- [ ] 臨床シナリオ3例の具体化（ウォークスルー用）
- [ ] ツールのUI改修（カテゴリフィルタ、英語UI）
- [ ] GitHub Pages公開準備
- [ ] 共著者候補の検討
- [ ] PRISMA-ScRチェックリスト確認
