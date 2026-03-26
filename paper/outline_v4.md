# Where Is the Evidence? A Comprehensive Map of Japanese Kampo and Acupuncture Research Across Domestic and International Literature

**Target journal**: Journal of General Family Medicine (JGFM)
**Article type**: Original Article
**Date**: 2026-03-26 (v4: PubMed統合版)

---

## Title candidates
1. Where Is the Evidence? A Comprehensive Map of Japanese Kampo and Acupuncture Research Across Domestic and International Literature
2. Mapping Seven Decades of Japanese Traditional Medicine: A Bibliometric Analysis of 10,282 Articles from J-STAGE and PubMed
3. The Translation Gap: How Japan's Kampo and Acupuncture Evidence Is Split Between Japanese and English Literature

---

## Abstract (structured, 250 words)

**Background**: Over 80% of Japanese physicians prescribe Kampo, and acupuncture is widely used. Yet clinical evidence is fragmented across Japanese-language domestic journals and English-language international literature, with no resource integrating both.

**Objective**: To map the complete research landscape of Japan-affiliated Kampo and acupuncture research across both Japanese and English literature, analyze research gaps and translation barriers, and deploy an interactive evidence navigation tool.

**Methods**: Articles were collected from two Japanese journals via J-STAGE (Kampo Medicine 1982–2025, n=2,003; JJSAM 2007–2025, n=650) and from PubMed via E-utilities using a three-layer search strategy (17 sub-queries covering Kampo, acupuncture, pharmacognosy, and pharmacology; 1954–2026; n=7,629 after noise removal and exclusion of non-Japan affiliations). Articles were classified across 5 axes: 88 ICD-11-based disease categories, 30 symptom categories, and study design, intervention, and setting. Author name matching between Japanese and English was performed using co-occurrence analysis (623 matched pairs). An interactive HTML tool was deployed on GitHub Pages.

**Results**: The 10,282 articles revealed fundamental asymmetries. Japanese-language journals contained 38.7% case reports reflecting clinical practice, while PubMed contained 28.2% basic research. Kampo-specific concepts (cold sensitivity, Qi deficiency, blood stasis, water retention) appeared in 6–10% of Japanese case reports but <1% of English literature—the largest translation gap identified. Disease coverage was complementary: 529 RCTs were found in PubMed but zero for conditions like tinnitus, migraine, and facial palsy, which had substantial case report evidence. Kampo dominated internal medicine and cancer supportive care; acupuncture dominated musculoskeletal conditions. The top formula (Yokukansan) mapped to 286 articles, primarily for dementia.

**Conclusions**: This is the first comprehensive bibliometric analysis bridging Japanese and English traditional medicine literature. The translation gap—where Kampo's individualized clinical wisdom exists only in Japanese—represents both a limitation and an opportunity for international evidence synthesis.

---

## 1. Introduction

### 1.1 Kampo and acupuncture in Japanese primary care
- 90% of physicians have Kampo prescribing experience (Uneda 2024)
- 148 Kampo formulas covered by national health insurance
- Acupuncture is a common referral option
- Yet most primary care physicians lack systematic access to the evidence

### 1.2 The fragmentation problem
- **Japanese-language journals**: Domestic clinical wisdom (case reports, clinical experience)
- **PubMed/English literature**: Basic research, RCTs, systematic reviews
- **No overlap**: DOI-based matching found 0 duplicates between J-STAGE and PubMed
- Existing resources (EKAT for RCTs, Yasunaga et al. for RWD) cover narrow slices

### 1.3 Why case reports matter in Kampo
- Kampo treatment is individualized by "Sho" (pattern diagnosis)
- Case reports capture successful treatment of refractory conditions
- These constitute the majority of Japanese Kampo literature (38.7%)
- The audience—family physicians—understands n=1 clinical knowledge

### 1.4 Study objectives
1. Collect all articles from two core Japanese journals (2,653) and Japan-affiliated PubMed articles (7,629) into a unified database of 10,282 articles
2. Analyze the translation gap between Japanese and English literature
3. Identify evidence gaps (conditions with case reports but no RCTs)
4. Deploy an interactive evidence navigation tool for primary care

---

## 2. Methods

### 2.1 Study design
- Bibliometric analysis with systematic search (PRISMA-ScR as reporting guide)

### 2.2 Data sources

**Japanese literature (J-STAGE)**:
- Journal of Kampo Medicine (日本東洋医学雑誌, 1982–2025): 2,003 articles
- JJSAM (全日本鍼灸学会雑誌, 2007–2025): 650 articles

**English literature (PubMed)**:
- Three-layer search strategy via NCBI E-utilities (2026-03-26)
  - Layer 1: Core Kampo (keywords, MeSH, formula names, TJ numbers) — 5 sub-queries
  - Layer 2: Acupuncture/moxibustion comprehensive — 1 sub-query
  - Layer 3: Pharmacognosy, pharmacology, safety, RWD — 11 sub-queries
- Noise removal: articles in Layer 3 only required relevance keyword match
- Affiliation filter: China/Korea-affiliated articles excluded (n=1,564); Japan/Other/Unknown retained
- Final: 7,629 PubMed articles (1954–2026)

### 2.3 Disease and symptom classification
- **5-axis system**: disease (88 ICD-11-based leaves across 17 chapters), symptom (30 leaves including Kampo-specific concepts), intervention (6), study design (8), setting (12)
- **Total: 144 categories**
- Keyword + MeSH matching against title/abstract
- Disease tagging rate: PubMed 64.9%, J-STAGE 47.1%

### 2.4 Kampo formula identification
- Dictionary of 257 formulas (kanji, hiragana, romanized names, formula numbers)
- Regex matching against title + abstract

### 2.5 Author name matching
- Japanese↔English author name pairs identified by co-occurrence analysis on J-STAGE articles (which contain both Japanese and romanized author names)
- Jaccard similarity ≥ 0.7 and 1:1 best-match constraint
- **623 author pairs** automatically matched

### 2.6 Analyses
- Descriptive statistics: frequencies, proportions, temporal trends
- Japanese vs. English literature comparison by disease, symptom, and study design
- Evidence gap analysis: conditions with case reports but no RCTs
- Kampo vs. acupuncture disease coverage comparison
- Translation gap analysis: concepts present in Japanese but absent in English literature

### 2.7 Interactive tool
- Single-file HTML/JavaScript application (vanilla JS, no dependencies)
- Features: 5-axis category browsing, formula lookup, author search (bilingual), free-text search, timeline
- Deployed on GitHub Pages

---

## 3. Results

### 3.1 Overview
- **10,282 articles** total (J-STAGE 2,653 + PubMed 7,629)
- Spanning **1954–2026** (72 years)
- 257 Kampo formulas, 17 ICD chapters, 144 categories
- 4,989 indexed authors (623 with Japanese↔English name matching)
- Abstracts available for 94.7% (PubMed) and 76.1% (J-STAGE)

### 3.2 The translation gap: Japanese vs. English literature (KEY FINDING)

**Study design asymmetry** (Table 1):

| Design | J-STAGE | PubMed |
|--------|---------|--------|
| Case reports | **38.7%** | 6.8% |
| Basic research | 2.8% | **28.2%** |
| RCT | 1.8% | 6.0% |
| SR/Meta-analysis | 0.3% | 1.4% |

→ Japanese journals = clinical practice voice; PubMed = basic science. Completely complementary.

**Symptom concepts that exist only in Japanese** (Figure 2):

| Kampo concept | JP case reports | PM case reports |
|---|---|---|
| Cold sensitivity (冷え症) | **9.5%** | 0.2% |
| Water retention (水毒) | **7.4%** | 0.4% |
| Qi deficiency (気虚) | **6.8%** | 0.4% |
| Blood stasis (瘀血) | **6.7%** | 0.8% |
| Palpitation (動悸) | **6.4%** | 0.2% |

→ Sho-based clinical knowledge is essentially invisible in English literature

**Disease coverage gaps**:
- Conditions reported only/mainly in Japanese: facial palsy (JP 21 vs PM 9), herpes zoster (JP 10 vs PM 4), fibromyalgia (JP 10 vs PM 6)
- Conditions reported only/mainly in PubMed: antitumor basic research (PM 713 vs JP 3), fungal infections (PM 214 vs JP 5), dementia (PM 349 vs JP 18)

### 3.3 Evidence gaps: case reports without RCTs

| Condition | Case reports | RCTs | Evidence gap |
|-----------|-------------|------|-------------|
| Tinnitus/Hearing loss | 29 | 0 | ⚠️ |
| Migraine | 24 | 0 | ⚠️ |
| Thyroid diseases | 16 | 0 | ⚠️ |
| Facial palsy | 14 | 0 | ⚠️ |
| Herpes zoster | 11 | 0 | ⚠️ |
| Sinusitis | 6 | 0 | ⚠️ |

Contrast with RCT-rich conditions: other neoplasms (94 RCTs), influenza (64), GI cancer (41), dementia (38)

### 3.4 Kampo vs. Acupuncture: complementary coverage (Figure 3)

**Acupuncture-dominant** (musculoskeletal/pain):
- Low back pain: acu 58 vs kampo 28
- Facial palsy: acu 22 vs kampo 3
- Shoulder: acu 10 vs kampo 4

**Kampo-dominant** (internal medicine/supportive care):
- Dementia: kampo 143 vs acu 9
- CIPN: kampo 81 vs acu 16
- Cancer anorexia-cachexia: kampo 74 vs acu 10
- Schizophrenia: kampo 35 vs acu 2

### 3.5 Temporal dynamics

**Rapid growth (2020s vs 2010s)**:
- Smell/taste disorders: +73% (COVID-related)
- Heart failure: +67%
- Facial palsy: +100%
- Infertility: +33%

**Decline**:
- GERD: −80%
- H. pylori: −76% (eradication therapy reduced Kampo's role)
- Ileus: −68%

### 3.6 Formula-disease mapping (Top 5)

| Formula | Articles | Primary indication |
|---------|---------|-------------------|
| Yokukansan (抑肝散) | 286 | Dementia/BPSD (134) |
| Goreisan (五苓散) | 145 | Influenza (23), Heart failure (18) |
| Goshajinkigan (牛車腎気丸) | 104 | CIPN (51) |
| Keishibukuryogan (桂枝茯苓丸) | 79 | (broad) |
| Hachimijiogan (八味地黄丸) | 72 | Diabetes (10) |

### 3.7 Tool walkthrough (Figure 4: screenshots)
- Scenario 1: "片頭痛" → discovers 24 case reports + 0 RCTs → evidence gap visible
- Scenario 2: Author search "寺澤" → unified view of 228 articles across JP and PM
- Scenario 3: Disease × study design cross-tabulation

---

## 4. Discussion

### 4.1 The translation gap as the central finding
- This is the first study to quantify the gap between Japanese and English Kampo literature
- Sho-based concepts (冷え, 気虚, 瘀血, 水毒) are virtually absent from English literature
- This is not a deficiency—it reflects the fundamentally different epistemological frameworks
- Implication: international systematic reviews of Kampo that search only English databases miss the majority of clinical experience

### 4.2 Complementary evidence ecosystems
- Japanese literature: clinical practice, case reports, Sho-based individualization
- English literature: basic research, RCTs, pharmacology
- Neither alone gives the full picture
- This tool provides the first integrated view

### 4.3 Evidence gaps as research priorities
- Conditions with substantial case report evidence but zero RCTs (tinnitus, migraine, facial palsy, thyroid) are natural candidates for clinical trials
- The case report corpus provides pilot data for sample size estimation and outcome selection

### 4.4 Divergent publishing cultures
- Acupuncture: internationally practiced → Japanese researchers publish in English → domestic journal declining
- Kampo: uniquely Japanese (148 insured formulas, Sho-based practice) → domestic journal remains vital
- This asymmetry explains the different roles of the two data sources

### 4.5 Triangulation with existing resources
- **This tool**: 10,282 articles (breadth: 72 years, bilingual)
- **EKAT**: 512 structured RCT reviews (quality)
- **Yasunaga et al.**: DPC/NDB real-world data (scale: millions of patients)
- All three needed for the complete picture

### 4.6 Implications for primary care
- First time Kampo + acupuncture + basic research are searchable in one tool
- Bilingual author matching enables following researcher trajectories across languages
- Evidence gap identification helps guide referrals and shared decision-making

### 4.7 Limitations
1. Keyword-based disease classification (validated but Recall not measured)
2. Two Japanese journals only (other journals exist)
3. PubMed noise: ~100 false positives may remain in Layer 3
4. Affiliation-based country assignment uses first author only
5. Asymmetric coverage: Kampo 44y, Acupuncture 19y, PubMed 72y
6. Author matching (623 pairs) covers only J-STAGE authors; PubMed-internal name variants (e.g., "Shimada Y" vs "Shimada Yutaka") not resolved
7. Research volume ≠ clinical utility
8. Non-searched databases: ICHUSHI, CINAHL, Cochrane, EMBASE
9. Case report symptom analysis limited to keyword matching for Kampo concepts
10. China/Korea exclusion may remove valid Japan-collaboration studies

### 4.8 Future directions
- Integration with EKAT and Yasunaga RWD for unified evidence platform
- Sho-based symptom extraction using NLP
- Intervention study: does tool use change clinical behavior? (Paper 2)
- Expansion to ICHUSHI (医中誌) for broader Japanese coverage
- Bilingual tool interface (EN/JP)

---

## 5. Conclusion

This bibliometric analysis of 10,282 articles—bridging Japanese and English literature for the first time—reveals a fundamental translation gap in Kampo evidence. Japanese-language journals preserve four decades of Sho-based clinical wisdom (cold sensitivity, Qi deficiency, blood stasis) that is virtually invisible in English literature. Meanwhile, PubMed contains 529 RCTs and extensive basic research absent from domestic journals. The two literatures are completely complementary, with zero DOI overlap. By integrating both into an interactive tool and identifying evidence gaps (conditions with case reports but no RCTs), we provide primary care physicians with a comprehensive map of traditional Japanese medicine evidence and a roadmap for future research priorities.

---

## Figures

| Figure | Content | Type |
|--------|---------|------|
| Fig 1 | Publication trends: J-STAGE vs PubMed by decade (1954–2026) | Stacked bar chart |
| **Fig 2** | **Translation gap: Kampo concepts in JP vs PM case reports** | **Grouped bar chart** |
| Fig 3 | Kampo vs. Acupuncture disease coverage (butterfly chart) | Butterfly chart |
| Fig 4 | Tool screenshots (3 clinical scenarios) | Screenshots |

## Tables

| Table | Content |
|-------|---------|
| Table 1 | Study design composition: J-STAGE vs PubMed |
| Table 2 | Evidence gap: conditions with case reports but no RCTs |
| Table 3 | Top 10 formulas with primary disease mapping |
| Table 4 | Comparison with existing resources (EKAT, Yasunaga RWD, this tool) |

## Supplementary
- Table S1: 257 formulas complete list
- Table S2: 144 categories (5 axes) with ICD-11 codes
- Table S3: 17 PubMed sub-queries with hit counts
- Table S4: 623 author name pairs (Japanese ↔ English)
- Table S5: Full disease × study design cross-tabulation
- Table S6: Disease × Kampo/Acupuncture article counts
- Online tool: https://koseihana2525-netizen.github.io/Kampo_database/

---

## Key references
- Uneda 2024: Kampo physician survey (Trad Kampo Med)
- Arai 2021: Need for Kampo evidence (J Integr Med)
- EKAT / Motoo: Evidence Reports of Kampo Treatment
- Yasunaga 2020: Outpatient Kampo prescriptions (Intern Med)
- Yasunaga 2025: Kampo in cancer inpatients (Int J Clin Oncol)
- Tricco 2018: PRISMA-ScR guideline

---

## 次のアクションアイテム
- [ ] Fig 1（時系列）作図
- [ ] Fig 2（翻訳ギャップ）作図 ← NEW key figure
- [ ] Fig 3（バタフライチャート）作図
- [ ] Fig 4 ツールスクリーンショット
- [ ] search_methodology.md の数値更新（中韓除外後の7,629件ベース）
- [ ] PRISMA-ScRチェックリスト
- [ ] 共著者候補の検討
- [ ] 本文ドラフト着手
