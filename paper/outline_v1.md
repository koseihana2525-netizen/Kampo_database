# Kampo and Acupuncture Evidence Map: Paper Outline (JGFM)

## Working Title
**Mapping 43 Years of Kampo and Acupuncture Evidence: An Interactive Evidence Map from Two Major Japanese Traditional Medicine Journals**

## Target Journal
Journal of General Family Medicine (JGFM) — Original Article

---

## Abstract (structured, 250 words)

- **Background**: Kampo and acupuncture are widely used in Japanese primary care, but the clinical evidence—scattered across decades of Japanese-language journals—remains inaccessible to most practitioners.
- **Methods**: Scoping review and evidence mapping of all articles published in the Journal of Kampo Medicine (1979–2023, 43 volumes) and the Journal of the Japan Society of Acupuncture and Moxibustion (19XX–2023). Metadata were extracted via J-STAGE API. Articles were classified by Kampo formula/acupuncture technique and disease category using a keyword-based taxonomy aligned with ICD-10 chapters. An interactive web-based Evidence Map was developed.
- **Results**: 2,653 articles were identified (2,003 Kampo; 650 acupuncture). XX Kampo formulas and XX disease categories were mapped. The most studied formulas were [top 5]. Evidence gaps were identified in [areas]. The interactive tool enables bidirectional search: disease-to-formula and formula-to-disease.
- **Conclusions**: This is the first comprehensive, interactive evidence map integrating Kampo and acupuncture literature. Unlike EKAT, which focuses exclusively on RCTs, this map captures the full spectrum of clinical evidence including case reports—a critical repository of clinical wisdom in traditional medicine. The tool is freely available at [URL].

---

## 1. Introduction (600 words)

### 1.1 Kampo and acupuncture in Japanese primary care
- Over 80% of Japanese physicians prescribe Kampo medicines
- Acupuncture is a common referral option in primary care
- Yet most primary care physicians lack systematic access to the evidence base

### 1.2 The evidence accessibility problem
- Clinical knowledge is concentrated in two specialty journals, both in Japanese
- Articles span 4+ decades → difficult to search manually
- No existing tool allows disease-based reverse lookup

### 1.3 Existing resources and their limitations
- EKAT: 577 RCTs only, PDF format, organized by formula only
- KCPG: clinical guideline survey, not a search tool
- KampoDB: pharmacological, not clinical
- Bibliometric analyses (Onoda 2023): publication trends, not clinical navigation
- **Gap: No interactive evidence map covering all study types**

### 1.4 The value of case reports in Kampo
- Kampo treatment is individualized by "Sho" (pattern diagnosis) → RCT averaging may obscure efficacy
- Case reports capture successful treatment of conditions refractory to conventional medicine
- These constitute the majority of Kampo literature and represent accumulated clinical wisdom
- (2-3 sentences, not belabored)

### 1.5 Study aim
- To create a comprehensive, interactive evidence map of Kampo and acupuncture clinical literature
- To enable primary care physicians to navigate this evidence by disease, formula, or free-text query

---

## 2. Methods (800 words)

### 2.1 Study design
- Scoping review following PRISMA-ScR guidelines
- Evidence mapping methodology (ref: Miake-Lye et al., 2016)

### 2.2 Data sources
- Journal of Kampo Medicine (日本東洋医学雑誌), Volumes 1–74 (1979–2023)
- Journal of the Japan Society of Acupuncture and Moxibustion (全日本鍼灸学会雑誌), Volumes XX–XX (XXXX–2023)
- All articles retrieved via J-STAGE API (metadata + abstracts where available)

### 2.3 Data extraction
- Automated extraction: title, authors, year, volume, pages, DOI, abstract
- Abstract availability: XX% (Kampo), XX% (acupuncture)

### 2.4 Classification
- **Kampo formulas**: Identified using a dictionary of 246 approved formulas + variants (kanji, hiragana, romaji)
  - Validation: 234 articles manually reviewed, formula identification precision = 100%
- **Acupuncture techniques**: [classification method]
- **Disease categories**: Three-level taxonomy aligned with ICD-10
  - Level 1: ICD-10 chapters (e.g., "I Infectious diseases")
  - Level 2: Disease subcategories (e.g., "Common cold", "Hepatitis")
  - Level 3: Specific conditions
  - Additional non-ICD categories: Kampo-specific concepts (classical texts, education, safety/adverse effects, drug interactions)
- Classification method: keyword matching against title and abstract
- Limitations acknowledged: keyword-based, not manual coding of all articles

### 2.5 Evidence Map tool development
- Single-page web application (HTML/CSS/JavaScript)
- Features: category browsing, formula lookup, author search, free-text search, evidence matrix visualization
- Deployed on GitHub Pages (freely accessible)

---

## 3. Results (1000 words)

### 3.1 Overview of included articles
- Total: 2,653 articles (2,003 Kampo journal; 650 acupuncture journal)
- Publication timeline: Figure 1 (temporal trends)
- Abstract availability

### 3.2 Kampo formula landscape
- XX unique formulas identified across XX articles
- Top 20 formulas: Figure 2 (bar chart)
- Most-studied: 補中益気湯, 小柴胡湯, 桂枝茯苓丸, 五苓散, 葛根湯...
- Distribution: highly skewed (top 20 formulas account for XX% of articles)

### 3.3 Disease category landscape
- Distribution across ICD-10 chapters: Figure 3 (treemap or bar chart)
- Most-studied disease areas: [list]
- Least-studied (evidence gaps): [list]

### 3.4 Evidence matrix: Formula × Disease
- Figure 4: Bubble chart / heatmap (evidence gap map)
- Dense cells (well-studied combinations)
- Empty cells (evidence gaps)

### 3.5 Acupuncture-specific findings
- Most common conditions treated
- Most common techniques/points studied
- Comparison with Kampo coverage

### 3.6 The interactive Evidence Map tool
- Figure 5: Screenshots of key features
  - (a) Home / search interface
  - (b) Category browsing (3-layer)
  - (c) Formula detail page
  - (d) Evidence matrix view
- URL provided

---

## 4. Discussion (800 words)

### 4.1 Principal findings
- First comprehensive evidence map of Japanese traditional medicine literature
- Reveals both the breadth (246 formulas, XX diseases) and concentration (top 20 = XX%) of evidence
- Identifies specific evidence gaps for future research

### 4.2 Comparison with existing resources
- vs. EKAT: Complementary, not competing
  - EKAT = curated RCTs with quality assessment (depth)
  - This map = all evidence types with navigability (breadth)
  - Case reports excluded from EKAT represent XX% of our dataset
- vs. Bibliometric studies: Our tool is interactive and clinically navigable

### 4.3 Implications for primary care
- Primary care physicians can now:
  - Check what Kampo evidence exists for a specific condition
  - Discover formulas they may not have considered
  - Find case reports of successful treatment for refractory conditions
- Bridges the gap between traditional medicine specialists and generalists

### 4.4 The role of case reports in Kampo evidence
- Not a limitation but a feature of the evidence base
- Individualized "Sho"-based treatment makes large RCTs challenging
- Case reports capture clinical scenarios where conventional treatment failed
- Future: structured case report registries could further strengthen this evidence base

### 4.5 Limitations
- Keyword-based classification (not manual expert coding for all articles)
- Two journals only (other journals may contain Kampo/acupuncture articles)
- Japanese-language articles (abstracts translated where available, but full text remains in Japanese)
- Static dataset (requires periodic updates)
- No formal quality assessment of individual studies (unlike EKAT)

### 4.6 Future directions
- Claude API integration for AI-assisted case consultation
- Integration with EKAT (link RCTs to our broader evidence base)
- Addition of other journals (e.g., primary care journals)
- Community-driven annotation and quality tagging

---

## 5. Conclusions (100 words)
- 43 years of Kampo and acupuncture evidence mapped and made navigable
- Freely available interactive tool for primary care physicians
- Complements EKAT by capturing the full spectrum of clinical evidence
- Aims to improve the quality of primary care by making traditional medicine evidence accessible

---

## Figures and Tables

| # | Type | Content |
|---|------|---------|
| Fig 1 | Line chart | Publication trends over time (both journals) |
| Fig 2 | Bar chart | Top 20 Kampo formulas by article count |
| Fig 3 | Treemap/Bar | Disease category distribution (ICD-10 chapters) |
| Fig 4 | Bubble chart | Evidence Gap Map: Formula × Disease matrix |
| Fig 5 | Screenshots | Interactive tool features (4 panels) |
| Table 1 | Table | Summary of included articles by journal |
| Table 2 | Table | Comparison with existing resources (EKAT, KampoDB, etc.) |

## Supplementary Materials
- Interactive Evidence Map tool (URL)
- Complete dataset (CSV/JSON)
- Category classification dictionary

---

## Notes for co-authors
- [ ] Confirm acupuncture journal year range
- [ ] Fill in XX placeholders with actual numbers from data
- [ ] Decide on PRISMA-ScR registration (OSF?)
- [ ] Ethical approval: likely not needed (published literature analysis)
- [ ] Author contributions (CRediT)
- [ ] COI declarations
