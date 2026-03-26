# Search Methodology — Data Collection Protocol

> このドキュメントは論文Methods のドラフトを兼ねる。
> 検索日・件数・除外基準・限界を論文掲載に耐えうる精度で記録する。

**最終更新**: 2026-03-26
**検索実施日**: J-STAGE 2026-03-24 / PubMed 2026-03-26
**Version**: 2.0

---

## 1. Overview

本研究では **日本の東洋医学研究を包括的に地図化する** ため、
日本語文献（J-STAGE 2誌）と英語文献（PubMed）を統合した。
DOIベースの突き合わせで重複は0件であり、2つのソースは完全に相補的である。

### 1.1 Data Sources Summary

| # | Source | Language | API / Method | Period | Articles |
|---|--------|----------|-------------|--------|----------|
| A | 日本東洋医学雑誌 (Kampo Medicine) | Japanese | J-STAGE WebAPI | 1982–2025 | 2,003 |
| B | 全日本鍼灸学会雑誌 (JJSAM) | Japanese | J-STAGE WebAPI | 2007–2025 | 650 |
| C | PubMed / MEDLINE | English (primarily) | NCBI E-utilities | 1954–2026 | 9,193 (cleaned) |
| | **Grand Total** | | | **1954–2026** | **11,846** |

### 1.2 Cross-source Deduplication

DOI-based matching between J-STAGE and PubMed: **0 overlapping DOIs**.
The Japanese-language journals and PubMed datasets are entirely complementary.

---

## 2. Source A & B: J-STAGE（日本語2誌）

### 2.1 Target Journals

| Journal | ISSN | cdjournal | Period | Articles |
|---------|------|-----------|--------|----------|
| 日本東洋医学雑誌 (Kampo Medicine) | 0287-4857 | kampomed | 1982–2025 (44 years) | 2,003 |
| 全日本鍼灸学会雑誌 (Journal of JSAM) | 0285-9955 | jjsam | 2007–2025 (19 years) | 650 |
| **Total** | | | | **2,653** |

### 2.2 Retrieval Method

- **API**: J-STAGE WebAPI (`https://api.jstage.jst.go.jp/searchapi/do`)
- **Script**: `scraper.py` (Python 3, requests library)
- **Parameters**: `service=3`, `issn` or `cdjournal`, pagination with `start` / `count=100`
- **Rate limit**: 1.5 sec interval (robots.txt compliance)
- **Retrieved fields**: title (ja/en), authors (ja/en), DOI, volume, issue,
  pages, publication year, abstract (ja/en), J-STAGE URL

### 2.3 Inclusion / Exclusion

- **Included**: All articles indexed in J-STAGE for the target journals
  within the available date range (complete enumeration).
- **Excluded**: None.

### 2.4 Abstract Availability

| Journal | With Abstract | Without | Rate |
|---------|--------------|---------|------|
| 日本東洋医学雑誌 | 1,666 | 337 | 83.2% |
| 全日本鍼灸学会雑誌 | 354 | 296 | 54.5% |
| **Total** | **2,020** | **633** | **76.1%** |

### 2.5 Rationale for Journal Selection

この2誌を選んだ理由：
- **日本東洋医学雑誌**: 日本東洋医学会（会員約8,000名）の機関誌。
  日本の漢方研究の最大のリポジトリ。保険適用漢方エキス製剤は
  日本独自の制度であり、海外にない臨床知（症例報告）がここに蓄積される。
- **全日本鍼灸学会雑誌**: 全日本鍼灸学会の機関誌。日本の鍼灸研究の
  国内蓄積を代表する。ただし、鍼灸は国際的に普及しているため、
  日本の鍼灸研究者は英文誌への投稿も多く、国内誌の位置づけは
  漢方とは異なる（→ Limitation 5.1.9 参照）。

### 2.6 J-STAGE Coverage Limitations

- 東洋医学雑誌の1982年以前の号はJ-STAGEに未収録（紙媒体のみ）
- 全日本鍼灸学会雑誌の2007年以前の号はJ-STAGEに未収録
- 2誌の収録期間の非対称性（44年 vs 19年）は直接比較を制約する

---

## 3. Source C: PubMed（英語文献）

### 3.1 Search Strategy Overview

PubMed was searched via NCBI E-utilities API on 2026-03-26 using a
three-layer strategy designed to capture the full breadth of
Japan-affiliated traditional medicine research.

- **API**: NCBI E-utilities (`esearch.fcgi` + `efetch.fcgi`)
- **Script**: `scrape_pubmed.py` (Python 3, requests library)
- **Protocol**: esearch with `usehistory=y` → efetch in batches of 200 (XML format)
- **Rate limit**: 0.4 sec interval (NCBI guideline: 3 req/sec without API key)
- **Retrieved fields**: PMID, title, authors, journal, year, DOI, PMC ID,
  abstract (structured), MeSH terms, publication types, first author affiliation
- **No date restriction**: All years retrieved (earliest hit: 1954)

### 3.2 Layer 1: Core Kampo/Traditional Japanese Medicine (5 sub-queries)

**L1-1: Kampo Keywords + MeSH** (n = 3,537)
```
(Kampo OR Kanpo OR "Japanese Kampo"
 OR "traditional Japanese medicine"
 OR "Japanese herbal medicine"
 OR "Japanese oriental medicine"
 OR "medicine, Kampo"[MeSH]
 OR "medicine, East Asian traditional"[MeSH])
AND Japan
```

**L1-2: Wakan (和漢)** (n = 283)
```
(Wakan OR "Wakan-yaku" OR "Sino-Japanese medicine"
 OR "Japanese-Chinese medicine")
AND Japan
```

**L1-3: Major Formula Names (Top 30)** (n = 2,860)
```
(Rikkunshito OR Daikenchuto OR Yokukansan OR Hochuekkito
 OR Shosaikoto OR Juzentaihoto OR Shakuyakukanzoto
 OR Bakumondoto OR Goshajinkigan OR Hangeshashinto
 OR Kakkonto OR Maoto OR Keishibukuryogan OR Kamishoyosan
 OR Tokishakuyakusan OR Saireito OR Ninjinyoeito
 OR Choreito OR Goreisan OR Bofutsushosan
 OR Daisaikoto OR Saikokeishito OR Orengedokuto
 OR Shoseiryuto OR Boiogito OR Yokukansankachinpihange
 OR Mashiningan OR Jumihaidokuto OR Unseiin
 OR Hachimijiogan)
```

**L1-4: Additional Formula Names** (n = 557)
```
(Shimotsuto OR Keishikajutsubuto OR Bukuryoingohangekobokuto
 OR Saikokaruyukotsuboreito OR Hangekobokuto OR Inchinkoto
 OR Daiokanzoto OR Tokikenchuto OR Shinbuto
 OR Goshuyuto OR Anchusan OR Chotosan
 OR Sansoninto OR Seishinrenshiin OR Kamikihito
 OR Kososan OR Shigyakusan OR Byakkokaninjinto
 OR Ninjinto OR Saikokeshikankyoto
 OR Tsudosan OR Yokuininto OR Keishito)
```

**L1-5: TJ Numbers (Tsumura product codes)** (n = 307)
```
("TJ-1" OR "TJ-9" OR "TJ-14" OR "TJ-16" OR "TJ-17"
 OR "TJ-19" OR "TJ-23" OR "TJ-24" OR "TJ-25" OR "TJ-27"
 OR "TJ-29" OR "TJ-41" OR "TJ-43" OR "TJ-48" OR "TJ-54"
 OR "TJ-68" OR "TJ-83" OR "TJ-100" OR "TJ-107" OR "TJ-108"
 OR "TJ-114" OR "TJ-128" OR "TJ-135" OR "TJ-137")
AND Japan
```

**Layer 1 subtotal**: 7,543 → **5,544 unique** (after PMID deduplication)

### 3.3 Layer 2: Acupuncture and Related Therapies (1 sub-query)

**L2-1: Acupuncture Comprehensive** (n = 1,495)
```
(acupuncture OR moxibustion OR electroacupuncture
 OR "electro-acupuncture" OR "dry needling"
 OR acupressure OR "auricular acupuncture"
 OR moxa OR shiatsu OR anma
 OR "acupuncture therapy"[MeSH]
 OR "acupuncture points"[MeSH]
 OR "meridians"[MeSH]
 OR "acupuncture analgesia"[MeSH]
 OR "electroacupuncture"[MeSH])
AND (Japan[Affiliation] OR Japanese[Title/Abstract])
```

**Layer 2 subtotal**: **1,495 unique**

### 3.4 Layer 3: Pharmacognosy, Pharmacology, and Basic Research (11 sub-queries)

**L3-1: Herbal MeSH in Kampo context** (n = 2,270)
```
("drugs, Chinese herbal"[MeSH] OR "phytotherapy"[MeSH]
 OR "plant extracts"[MeSH])
AND Japan[Affiliation]
AND (Kampo OR "traditional Japanese" OR "Japanese herbal"
 OR "oriental medicine" OR "traditional medicine"
 OR "East Asian" OR "herbal medicine")
```

**L3-2: Crude Drug / Pharmacognosy** (n = 668)
```
("crude drug" OR "crude drugs" OR pharmacognosy
 OR "herbal drug" OR "medicinal plant" OR "medicinal plants"
 OR "medicinal herb")
AND Japan[Affiliation]
AND (Kampo OR "traditional Japanese" OR ...)
```

**L3-3: Active Compounds** (n = 914)
```
(glycyrrhizin OR berberine OR baicalin OR baicalein
 OR paeoniflorin OR ginsenoside OR saikosaponin
 OR atractylodin OR magnolol OR honokiol
 OR coptisine OR palmatine OR wogonin
 OR poricoic OR pachymic OR aucubin
 OR sennoside OR rhein OR emodin
 OR aconitine OR mesaconitine
 OR ephedrine OR pseudoephedrine
 OR shogaol OR gingerol)
AND Japan[Affiliation]
AND ("herbal" OR "crude drug" OR "Kampo" OR ...)
```

**L3-4: Botanical Names (15 key genera)** (n = 1,187)
```
(Glycyrrhiza OR Bupleurum OR Scutellaria OR Coptis
 OR Atractylodes OR Poria OR Rehmannia
 OR Angelica OR Cnidium OR Magnolia
 OR Ephedra OR Paeonia OR Zingiber
 OR Panax OR Cinnamomum)
AND Japan[Affiliation]
AND (Kampo OR "herbal medicine" OR ...)
```

**L3-5: Quality Control / Analytical Chemistry** (n = 650)
**L3-6: Pharmacological Activity** (n = 1,480)
**L3-7: Safety / Toxicity / Drug Interactions** (n = 407)
**L3-8: Gut Microbiota** (n = 76)
**L3-9: Real-World Data / Epidemiology** (n = 182)
**L3-10: Manufacturer-related** (n = 3,004)
**L3-11: Network Pharmacology** (n = 38)

**Layer 3 subtotal**: 10,876 → **7,460 unique**

### 3.5 Deduplication and Noise Removal

| Step | Articles |
|------|----------|
| Total retrieved (all layers) | 19,914 |
| After PMID deduplication | 11,682 |
| After noise removal | **9,193** |

**Noise removal criteria**:
Articles matching Layer 3 only (no Layer 1 or 2 match) were retained only if their title, abstract, or MeSH terms contained at least one term from a curated relevance dictionary (n = 60+ terms covering Kampo, herbal medicine, acupuncture, active compounds, and botanical names).

**Primary noise sources identified and removed**:
- "JPS" → false match with *Journal of Physiological Sciences* abbreviation (n ≈ 412)
- "Tsumura" → false match with author surname (n ≈ 723)
- "Kotaro" → false match with given name (n ≈ 138)

---

## 4. Integrated Dataset Statistics

### 4.1 Final Dataset

| Source | Language | Articles | Period | Abstracts | DOIs |
|--------|---------|---------|--------|-----------|------|
| 日本東洋医学雑誌 | Japanese | 2,003 | 1982–2025 | 1,666 (83.2%) | 2,003 (100%) |
| 全日本鍼灸学会雑誌 | Japanese | 650 | 2007–2025 | 354 (54.5%) | 650 (100%) |
| PubMed (cleaned) | English | 9,193 | 1954–2026 | ~8,747 (95.1%) | ~8,461 (92.0%) |
| **Grand Total** | | **11,846** | **1954–2026** | **~10,767** | **~11,114** |

### 4.2 PubMed — Research Design (Publication Type)

| Publication Type | Count |
|-----------------|-------|
| Randomized Controlled Trial | 529 |
| Clinical Trial | 258 |
| Systematic Review | 198 |
| Meta-Analysis | 123 |
| Observational Study | 96 |
| Case Reports | 607 |
| Review | 888 |

### 4.3 PubMed — First Author Affiliation

| Country | Articles | % |
|---------|---------|---|
| Japan | 8,836 | 75.6% |
| China | 983 | 8.4% |
| Korea | 281 | 2.4% |
| USA | 170 | 1.5% |
| Taiwan | 86 | 0.7% |
| Other / Unknown | 1,326 | 11.4% |

> **Note**: China-affiliated articles (8.4%) were retained because many
> involve Japan-China collaborations or study Kampo-origin formulas.
> Sensitivity analyses comparing Japan-only vs. all-country results
> should be reported.

### 4.4 PubMed — Publication Trend by Decade

| Decade | Articles |
|--------|---------|
| 1950–1970s | 56 |
| 1980s | 300 |
| 1990s | 1,678 |
| 2000s | 2,122 |
| 2010s | 3,489 |
| 2020s | 4,037 |

### 4.5 PubMed — Top 15 Journals

| Journal | Articles |
|---------|---------|
| Biol Pharm Bull | 407 |
| J Ethnopharmacol | 332 |
| J Physiol Sci | 330 |
| J Nat Med | 283 |
| Am J Chin Med | 276 |
| Evid Based Complement Alternat Med | 264 |
| Chem Pharm Bull (Tokyo) | 206 |
| Yakugaku Zasshi | 177 |
| Planta Med | 145 |
| PLoS One | 138 |
| Medicine (Baltimore) | 131 |
| Phytomedicine | 129 |
| Sci Rep | 127 |
| Front Pharmacol | 102 |
| Phytother Res | 94 |

### 4.6 Disease Category Tagging (TBD — 次フェーズ)

ICD-11準拠のカテゴリ体系で疾患タグ付けを行う予定。
MeSHからICD-11へのマッピングと、漢方特有の症候分類を併用する。

---

## 5. Known Limitations of the Search Strategy

### 5.1 Recall Limitations（取りこぼしの可能性）

1. **Formula romanization variants**: 漢方方剤名のローマ字化には揺れがある
   (e.g., Shosaikoto vs Sho-saiko-to vs Xiao-chai-hu-tang)。
   本検索は日本式ローマ字の主要パターンをカバーしたが、
   中国語ピンイン表記のみの論文は取りこぼしうる。

2. **Non-indexed Japanese journals**: 以下の日本語誌はJ-STAGE対象外またはPubMed未収録:
   - 漢方と最新治療、漢方医学、Phil漢方
   - 和漢医薬学会誌
   - 生薬学雑誌（→ J Nat Med としてPubMedに283件収録されているが、
     前身の和文誌時代は未カバー）
   - 日本薬学会誌の生薬関連論文

3. **医中誌（ICHUSHI）未検索**: 日本語文献の最大DBである医中誌Webは
   本研究では検索していない。上記2誌以外の日本語論文は捕捉できない。

4. **CINAHL, Cochrane, EMBASE**: 未検索。看護系・リハビリ系の
   鍼灸研究が取りこぼされている可能性がある。

5. **Component herb research without context**: 個々の生薬（例: Glycyrrhiza）を
   対象とした日本の薬学研究で、タイトル/抄録に "Kampo" "herbal medicine" 等の
   文脈語がないものはLayer 3のノイズ除去で除外される。
   推定50–100件が境界領域にある。

6. **Conference proceedings, dissertations, books**: いずれのソースでも未収録。
   特に日本東洋医学会学術総会の抄録は部分的にしか含まれない。

7. **Grey literature**: 厚労省研究班報告書、製薬企業の技術資料、
   PMDA審査報告書等は含まれない。

8. **Pre-2007 acupuncture journal**: 全日本鍼灸学会雑誌の2007年以前の号は
   J-STAGEに未収録。

9. **Acupuncture researchers' preference for English journals**:
   鍼灸は国際的に普及しており、日本の鍼灸研究者も英文誌への投稿を
   志向する傾向がある。このため全日本鍼灸学会雑誌（日本語）の
   カバレッジだけでは日本の鍼灸研究の全体像を反映しない。
   一方、漢方は日本の保険制度に根ざした固有の臨床体系であり、
   東洋医学雑誌は日本独自の臨床知の蓄積場所として機能している。
   この非対称性はデータ解釈上重要である。

10. **Pre-1982 Kampo journal**: 日本東洋医学雑誌は1950年創刊だが、
    1982年以前はJ-STAGEに未収録。

### 5.2 Precision Limitations（残存ノイズの可能性）

1. **Chinese TCM research**: PubMed記事の~8.4%が中国所属の筆頭著者。
   日中共同研究や共通方剤の研究が多いが、純粋なTCM研究で
   日本との接点がないものも含まれうる。

2. **MeSH term granularity**: "Medicine, East Asian Traditional" MeSH は
   韓・中・日の伝統医学を区別しない。

3. **Layer 3 false positives**: ノイズ除去で2,489件を除去したが、
   残留するfalse positive（広義の薬理学で漢方と無関係な論文）は
   推定100件程度。

### 5.3 Systematic Biases

1. **Publication bias**: 陽性結果が出版されやすい。
2. **Language bias**: 日本語論文と英語論文では、同じ研究グループでも
   報告内容が異なりうる。
3. **Temporal asymmetry**: 東洋医学雑誌（44年）vs 鍼灸学会雑誌（19年）。
   PubMed（72年）との期間差も考慮が必要。
4. **研究量 ≠ 臨床的有用性**: 論文数はエビデンスの質を反映しない。
5. **Affiliation bias**: Japan[Affiliation] フィルタは共著者の所属を
   見ていない。日本人研究者が海外所属の場合、捕捉漏れが生じうる。

---

## 6. Reproducibility

All scripts, queries, and configuration are publicly available at:
**https://github.com/koseihana2525-netizen/Kampo_database**

### 6.1 Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `config.py` | Project configuration, paths | — | — |
| `scraper.py` | J-STAGE metadata retrieval | ISSN / cdjournal | `data/metadata.json` |
| `scrape_pubmed.py` | PubMed 3-layer search (17 sub-queries) | Built-in queries | `data/pubmed/pubmed_all_merged.json` |
| `dictionaries.py` | Kampo formula dictionary (257 formulas) | — | Used by analysis scripts |
| `build_v3.py` | Integrated database construction | metadata + dictionaries | `output/kampo_db_v3.json` |
| `build_html_v3.py` | Interactive HTML visualization | JSON database | `index.html` |

### 6.2 Command Sequence

```bash
# 1. J-STAGE retrieval (complete enumeration)
python scraper.py --all                    # 日本東洋医学雑誌
python scraper.py --cdjournal jjsam --all  # 全日本鍼灸学会雑誌

# 2. PubMed retrieval (3-layer strategy)
python scrape_pubmed.py --dry-run          # Verify hit counts
python scrape_pubmed.py                    # Full retrieval (~10 min)

# 3. Database construction & visualization
python build_v3.py
python build_html_v3.py
```

### 6.3 Data Files

```
data/
  merged_metadata.json         # J-STAGE 2誌統合 (2,653 articles)
  metadata_with_abstracts.json # 東洋医学雑誌のみ (2,003)
  categories_v2.json           # 疾患カテゴリ分類体系
  pubmed/
    pubmed_all_merged.json     # PubMed生データ (11,682)
    pubmed_cleaned.json        # ノイズ除去後 (9,193)
    pubmed_noise_removed.json  # 除去されたノイズ（監査用, 2,489）
    pubmed_L1_*.json           # Layer 1 サブクエリ別結果 (5 files)
    pubmed_L2_*.json           # Layer 2 サブクエリ別結果 (1 file)
    pubmed_L3_*.json           # Layer 3 サブクエリ別結果 (11 files)
    pubmed_layer[1-3].json     # Layer別統合結果
```

### 6.4 PRISMA-ScR Compliance Note

本研究は従来のscoping reviewではなく、**bibliometric analysis with
systematic search elements** である。PRISMA-ScR チェックリストを
reporting guide として参考にしたが、2名独立スクリーニング等の
scoping review必須要件は満たしていない。
検索の再現性はスクリプトの公開により担保される。
