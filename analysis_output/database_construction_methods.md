# データベース構築方法の文書化

> **目的**: `integrated_db.json`（11,846件）の構築過程を論文Methods節に記載できる水準で文書化する。
>
> **生成日**: 2026-03-29
> **参照**: `paper/search_methodology.md` (v2.0, 2026-03-26)

---

## 1. データソース

### 1.1 J-STAGE（日本語2誌）

| 項目 | 日本東洋医学雑誌 | 全日本鍼灸学会雑誌 |
|------|-----------------|-------------------|
| ISSN | 0287-4857 | 0285-9955 |
| cdjournal | kampomed | jjsam |
| 収録期間 | 1982–2025（44年間） | 2007–2025（19年間） |
| 取得件数 | 2,003 | 650 |
| 抄録あり | 1,666（83.2%） | 354（54.5%） |
| 取得日 | 2026-03-24 | 2026-03-24 |

**取得方法**:
- API: J-STAGE WebAPI (`https://api.jstage.jst.go.jp/searchapi/do`)
- スクリプト: `scraper.py`（漢方）、`scrape_jjsam.py`（鍼灸）
- パラメータ: `service=3`, ISSN/cdjournal指定, `count=100`でページネーション
- リクエスト間隔: 1.5秒（robots.txt準拠）
- 取得フィールド: タイトル（日英）、著者（日英）、DOI、巻号頁、出版年、抄録（日英）、J-STAGE URL

**抄録取得**: J-STAGE APIのレスポンスに抄録が含まれない場合、`scrape_abstracts.py`により個別記事ページのHTMLをパースして取得（`<meta name="abstract">` → `<meta name="citation_abstract">` → `<div id="article-overiew-abstract-wrap">` の順でフォールバック）。

**包含基準**: 対象2誌のJ-STAGE収録全記事（完全列挙）。除外なし。

**統合**: `merge_data.py` により2誌のメタデータを結合 → `data/merged_metadata.json`（2,653件）

### 1.2 PubMed（英語文献）

**検索日**: 2026-03-26
**API**: NCBI E-utilities (`esearch.fcgi` + `efetch.fcgi`)
**スクリプト**: `scrape_pubmed.py`
**プロトコル**: `usehistory=y` → XML形式で200件ずつバッチ取得
**リクエスト間隔**: 0.4秒（NCBI推奨: APIキーなしで3 req/sec）
**期間制限**: なし（最古のヒット: 1954年）

#### 3層検索戦略（17サブクエリ）

**Layer 1: Core Kampo（5サブクエリ）**

| サブクエリ | 検索式の要旨 | ヒット数 |
|-----------|-------------|---------|
| L1-1: Kampo Keywords + MeSH | (Kampo OR "traditional Japanese medicine" OR "medicine, Kampo"[MeSH] ...) AND Japan | 3,537 |
| L1-2: Wakan | (Wakan OR "Sino-Japanese medicine") AND Japan | 283 |
| L1-3: Major Formulas (Top 30) | (Rikkunshito OR Daikenchuto OR Yokukansan ...) | 2,860 |
| L1-4: Additional Formulas | (Shimotsuto OR Keishikajutsubuto ...) | 557 |
| L1-5: TJ Numbers | ("TJ-1" OR "TJ-9" ...) AND Japan | 307 |
| **Layer 1 小計** | | **7,543 → 5,544 unique** |

**Layer 2: Acupuncture（1サブクエリ）**

| サブクエリ | 検索式の要旨 | ヒット数 |
|-----------|-------------|---------|
| L2-1: Acupuncture | (acupuncture OR moxibustion OR electroacupuncture OR "acupuncture therapy"[MeSH] ...) AND (Japan[Affiliation] OR Japanese[Title/Abstract]) | 1,495 |
| **Layer 2 小計** | | **1,495 unique** |

**Layer 3: Pharmacognosy/Pharmacology（11サブクエリ）**

| サブクエリ | 検索式の要旨 | ヒット数 |
|-----------|-------------|---------|
| L3-1: Herbal MeSH | ("drugs, Chinese herbal"[MeSH] ...) AND Japan AND Kampoコンテキスト | 2,270 |
| L3-2: Crude Drug | (crude drug OR pharmacognosy ...) AND Japan AND Kampoコンテキスト | 668 |
| L3-3: Active Compounds | (glycyrrhizin OR berberine OR baicalin ...) AND Japan AND 文脈語 | 914 |
| L3-4: Botanical Names | (Glycyrrhiza OR Bupleurum ...) AND Japan AND 文脈語 | 1,187 |
| L3-5: Quality Control | HPLC, standardization, authentication等 | 650 |
| L3-6: Pharmacological Activity | anti-inflammatory, antioxidant等 | 1,480 |
| L3-7: Safety/Toxicity | adverse effects, hepatotoxicity, CYP等 | 407 |
| L3-8: Gut Microbiota | gut microbiota, herbal medicine | 76 |
| L3-9: Real-World Data | DPC database, claims data等 | 182 |
| L3-10: Manufacturer | Tsumura, Kracie, Kotaro, JPS | 3,004 |
| L3-11: Network Pharmacology | network pharmacology, systems biology | 38 |
| **Layer 3 小計** | | **10,876 → 7,460 unique** |

検索式の完全な文字列は `paper/search_methodology.md` §3.2–3.4 および `scrape_pubmed.py` L45–L269 に記録されている。

#### 重複排除とノイズ除去

| ステップ | 件数 |
|---------|------|
| 全Layer合計（延べ） | 19,914 |
| PMID重複排除後 | 11,682 |
| ノイズ除去後 | **9,193** |

**PMID重複排除**: `scrape_pubmed.py` の `deduplicate()` 関数により、PMIDの一意性で統合。複数Layerにヒットした論文は `search_layers` フィールドに全該当Layer/サブクエリを記録。

**ノイズ除去** (`clean_pubmed.py`):
- **Tier 1 (自動通過)**: L1またはL2に該当 → 無条件で保持
- **Tier 2 (文脈判定)**: L3のみの論文 → タイトル・抄録・MeSHに関連性辞書（60+語: Kampo, herbal medicine, acupuncture, 活性化合物名, 植物学名等）のいずれかを含む場合のみ保持
- **Tier 3 (除去)**: 関連性シグナルなし → ノイズとしてラベル付け・除外

**主要ノイズ源**:
- "JPS" → *Journal of Physiological Sciences* 略称との衝突（約412件）
- "Tsumura" → 著者姓との衝突（約723件）
- "Kotaro" → 人名との衝突（約138件）

除去された2,489件は `data/pubmed/pubmed_noise_removed.json` に監査用として保存。

---

## 2. データ統合手順

### 2.1 処理パイプライン

```
[J-STAGE]                               [PubMed]
scraper.py → metadata.json              scrape_pubmed.py → pubmed_all_merged.json
scrape_jjsam.py → jjsam_metadata.json         ↓
scrape_abstracts.py → 抄録付与           clean_pubmed.py → pubmed_cleaned.json
        ↓                                      ↓
merge_data.py → merged_metadata.json     tag_pubmed.py → pubmed_tagged.json
        ↓                                      ↓
build_v3.py → kampo_db_v3.json                 ↓
        ↓                                      ↓
        └──────────┬───────────────────────────┘
                   ↓
      build_integrated_db.py → integrated_db.json (11,846件)
```

### 2.2 ID採番

- **日本語誌**: `jp_{連番}` （例: jp_0, jp_1, ..., jp_2652）
- **PubMed**: `pm_{PMID}` （例: pm_41880126）

### 2.3 ソース分類（`source`フィールド）

- **`kampo`**: J-STAGE 日本東洋医学雑誌（cdjournal = kampomed）
- **`acupuncture`**: J-STAGE 全日本鍼灸学会雑誌（cdjournal = jjsam）
- **`pubmed_kampo`**: PubMed論文でL1に該当するもの（L1 ∩ {L2, L3} も含む）
- **`pubmed_acupuncture`**: PubMed論文でL2に該当しL1に非該当のもの
- **`pubmed_pharma`**: PubMed論文でL3のみに該当するもの

分類ロジック（`build_integrated_db.py` L57–L63）:
```python
layers = set(t[0:2] for t in search_layers if t.startswith("L"))
if "L2" in layers and "L1" not in layers: source = "pubmed_acupuncture"
elif "L1" in layers:                       source = "pubmed_kampo"
else:                                      source = "pubmed_pharma"
```

### 2.4 Cross-source重複排除

J-STAGEとPubMed間のDOIベースの突き合わせ: **重複0件**。
2つのソースは完全に相補的（日本語誌はPubMedに収録されていない）。

---

## 3. フィールド付与

### 3.1 方剤名抽出（`formulas`）

**対象**: J-STAGE記事のみ（PubMed記事は未付与 → 0.0%）

**辞書**: `dictionaries.py`
- FORMULAS: ツムラ医療用漢方製剤128処方（番号体系TJ-001〜TJ-138、欠番10品目）
- EXTRA_FORMULAS: 非ツムラ処方134品目（日本東洋医学雑誌で頻出する古方・後世方）
- 合計: **262方剤**（エイリアス含む）

**抽出アルゴリズム** (`build_v3.py` L36–L43):
1. 全方剤名を文字列長の降順にソート（最長一致優先）
2. タイトル + 抄録の連結テキストに対して、各方剤名の文字列包含を検査
3. マッチした方剤名の箇所をNUL文字で置換し、部分一致の重複を防止

**除外辞書**: `FORMULA_EXCLUDE`（50+語）で漢字の偽陽性マッチ（例: 部分文字列の衝突）を除外。

**結果**: 漢方誌の56.1%（1,124/2,003件）で方剤名を検出。

### 3.2 疾患カテゴリ付与（`categories`）

**2つのカテゴリ体系が並存**:

#### (A) categories_v2 ベース（build_v3.pyおよびtag_pubmed.pyで使用 → integrated_db.jsonに反映）

**J-STAGE記事** (`build_v3.py` L67–L71):
- `categories_v2.json` の3階層構造（lv1 → lv2 → lv3）からleafノードのキーワードリストを平坦化
- タイトル + 抄録の連結テキストに対して、各leafノードの日本語キーワード群の文字列包含を検査
- マッチした全leafノード名を `categories` に格納（複数カテゴリ可）

**PubMed記事** (`tag_pubmed.py` L436–L453):
- `CATEGORY_EN_MAP` 辞書（約60疾患カテゴリ）で英語キーワード + MeSH用語のマッチング
- タイトル + 抄録のテキストに対して英語キーワードの包含チェック
- MeSHフィールドに対してMeSH用語のマッチング
- いずれかにヒットしたカテゴリ名（日本語）を `disease_categories` に格納

#### (B) categories_v3（tagger_v3.pyで使用 → tagged/ディレクトリに別途保存）

- ICD-11準拠の5軸体系（disease, symptom, intervention, study_design, setting）
- 88疾患リーフ + 30症候リーフ + 26その他 = **144カテゴリ**
- 各leafに `keywords_ja`, `keywords_en`, `mesh_terms` を定義
- J-STAGE: 日本語キーワード → 英語キーワードの順でマッチ
- PubMed: 英語キーワード → MeSH → pub_type_matchの順でマッチ

**注**: integrated_db.jsonの`categories`フィールドはcategories_v2ベースの分類結果である。

### 3.3 pub_types / mesh

- **PubMed記事**: MEDLINE XMLのPublicationType/MeSHフィールドをそのまま転記
  - `pub_types`: 全PublicationTypeを配列で格納
  - `mesh`: MeSH用語を最大10件まで格納
- **J-STAGE記事**: いずれも空配列 `[]`

---

## 4. データ品質チェック結果

### 4.1 基本統計

| 指標 | 結果 |
|------|------|
| 総論文数 | 11,846 |
| ID一意性 | 重複0件 |
| 年代範囲 | 1954–2026 |
| 年代異常値 | 0件（<1950 or >2026） |

### 4.2 ソース分布

| source | 件数 | 言語 |
|--------|------|------|
| pubmed_kampo | 5,544 | en |
| pubmed_pharma | 2,265 | en |
| kampo | 2,003 | ja |
| pubmed_acupuncture | 1,384 | en |
| acupuncture | 650 | ja |
| **合計** | **11,846** | ja: 2,653 / en: 9,193 |

### 4.3 フィールド欠損率

| フィールド | null | empty |
|-----------|------|-------|
| id | 0% | 0% |
| title | 0% | 0% |
| year | 0% | 0% |
| source | 0% | 0% |
| abstract | 0% | **9.6%**（1,138件） |
| lang | 0% | 0% |

**abstract空の内訳**:
- kampo: 337件（16.8%） — 1982年代の古い論文で抄録未収録
- acupuncture: 296件（45.5%） — 学会抄録集の目次的エントリ
- pubmed_kampo: 398件（7.2%）
- pubmed_acupuncture: 74件（5.3%）
- pubmed_pharma: 33件（1.5%）

### 4.4 抄録長の統計（source別、非空のみ）

| source | mean | median | min | max |
|--------|------|--------|-----|-----|
| kampo | 351 | 376 | 35 | 500 |
| acupuncture | 448 | 500 | 109 | 500 |
| pubmed_kampo | 496 | 500 | 54 | 500 |
| pubmed_acupuncture | 496 | 500 | 48 | 500 |
| pubmed_pharma | 495 | 500 | 59 | 500 |

**注**: PubMed記事の抄録は`build_integrated_db.py` L73で500文字に切り詰められている。

### 4.5 formulas非空率（source別）

| source | 付与率 |
|--------|-------|
| kampo | 56.1%（1,124/2,003） |
| acupuncture | 0.5%（3/650） |
| pubmed_* | 0.0%（未実装） |

**注**: PubMed記事への方剤名抽出は未実装。英語方剤名（ローマ字表記）のマッチングは`tagger_v3.py`のcategories_v3系で別途実施されているが、integrated_db.jsonの`formulas`フィールドには反映されていない。

### 4.6 categories非空率（source別）

| source | 付与率 |
|--------|-------|
| kampo | 68.0%（1,362/2,003） |
| acupuncture | 58.0%（377/650） |
| pubmed_kampo | 68.8%（3,812/5,544） |
| pubmed_acupuncture | 91.3%（1,264/1,384） |
| pubmed_pharma | 52.8%（1,195/2,265） |

### 4.7 潜在的重複（タイトル完全一致）

タイトル完全一致: **25タイトル**（同一sourceのJP記事のみ）

主な内容は学会運営記事であり、実質的な論文の重複ではない:
- "学会シンポジウム"（22件）、"一般演題抄録"（19件）、"特別演題抄録"（17件）
- "医薬品等安全性情報"（16件）、"訂正"（9件）

PubMed側: "Dysmenorrhoea."（4件）と "Gateways to clinical trials."（4件）は同名の連載記事。

JP-EN間のタイトル重複: なし（言語が異なるため構造的に発生しない）

### 4.8 Cross-source DOI重複

integrated_db.jsonにはDOIフィールドが直接含まれていない（`link`フィールドにJ-STAGE URL/PubMed URLが格納）。`search_methodology.md`で報告されたDOIベースの突き合わせ（0件重複）はスクリプト実行時の検証結果。

### 4.9 pub_types / mesh

- PubMed全9,193件で`pub_types`が付与済み（空率0%）
- MeSH非空率: 84.6%（7,776/9,193件）
- 主要pub_types: Journal Article (9,002), Case Reports (482), RCT (396), Review (717), Systematic Review (162), Meta-Analysis (94)

---

## 5. 既知の限界

### 5.1 Recall Limitations（取りこぼし）

1. **方剤名ローマ字化の揺れ**: 日本式ローマ字の主要パターンはカバーしたが、中国語ピンイン表記のみの論文（例: Xiao-chai-hu-tang）は取りこぼしうる
2. **非収録日本語誌**: 漢方と最新治療、漢方医学、Phil漢方、和漢医薬学会誌等は未検索
3. **医中誌未検索**: 日本語文献の最大DBである医中誌Webは検索していない
4. **CINAHL, Cochrane, EMBASE**: 未検索
5. **文脈語なしの生薬研究**: Layer 3のノイズ除去で推定50–100件が境界領域
6. **学会抄録・学位論文・書籍**: 未収録
7. **灰色文献**: 厚労省研究班報告書、PMDA審査報告書等は未収録
8. **J-STAGE収録の時間的制約**: 東洋医学雑誌1982年以前、鍼灸学会雑誌2007年以前は未収録
9. **鍼灸研究者の英文誌志向**: 国際普及により国内誌のカバレッジだけでは日本の鍼灸研究全体を反映しない

### 5.2 Precision Limitations（残存ノイズ）

1. **中国TCM研究**: PubMed記事の約8.4%が中国所属筆頭著者。大部分は日中共同研究だが、純粋なTCM研究も含まれうる
2. **MeSH粒度**: "Medicine, East Asian Traditional" MeSHは韓中日を区別しない
3. **Layer 3偽陽性**: 推定100件程度の残留ノイズ

### 5.3 データ構造の限界

1. **PubMed記事の`formulas`未付与**: 英語方剤名のマッチングはcategories_v3系で別途実施済みだが、integrated_db.jsonには未反映
2. **抄録500文字切り詰め**: PubMed記事の抄録は500文字で切断
3. **DOIフィールド未格納**: integrated_db.jsonにDOIが直接格納されていない
4. **J-STAGE記事のpub_types未付与**: 日本語誌の研究デザイン分類は未実装

---

## 6. 再現性

全スクリプト・クエリ・設定は以下で公開:
**https://github.com/koseihana2525-netizen/Kampo_database**

### コマンドシーケンス

```bash
# 1. J-STAGE取得（完全列挙）
python scraper.py --all                    # 日本東洋医学雑誌
python scrape_jjsam.py                     # 全日本鍼灸学会雑誌
python scrape_abstracts.py                 # 抄録付与

# 2. J-STAGE統合
python merge_data.py                       # 2誌統合

# 3. PubMed取得（3層戦略）
python scrape_pubmed.py --dry-run          # ヒット数確認
python scrape_pubmed.py                    # 全件取得（~10分）

# 4. PubMedクリーニング・タグ付け
python clean_pubmed.py                     # ノイズ除去
python tag_pubmed.py                       # 疾患カテゴリ付与

# 5. 統合DB構築
python build_v3.py                         # JP側DB構築（方剤名・カテゴリ付与）
python build_integrated_db.py              # JP + PubMed統合
```

---

## 7. 論文Methods節への記載案（英文ドラフト）

### Data Sources and Search Strategy

We constructed a comprehensive bibliometric database of Japanese traditional medicine research by integrating Japanese-language domestic journals with English-language PubMed literature.

**Japanese-language sources**: All articles indexed in J-STAGE for two official society journals were retrieved via J-STAGE WebAPI on March 24, 2026: the Journal of Kampo Medicine (Nihon Toyo Igaku Zasshi; ISSN 0287-4857; 2,003 articles, 1982–2025) and the Journal of the Japan Society of Acupuncture and Moxibustion (JJSAM; ISSN 0285-9955; 650 articles, 2007–2025). Complete enumeration was performed with no exclusion criteria.

**PubMed**: A three-layer search strategy was applied via NCBI E-utilities on March 26, 2026, with no date restriction. Layer 1 (5 sub-queries) targeted core Kampo research using formula names, keywords, MeSH terms, and Tsumura product codes. Layer 2 (1 sub-query) targeted acupuncture and related therapies with Japan affiliation. Layer 3 (11 sub-queries) captured pharmacognosy, pharmacology, and basic research with Kampo-context requirements. All queries are documented in the supplementary repository.

**Deduplication and noise removal**: PubMed results were deduplicated by PMID (19,914 → 11,682 unique). Layer 3-only articles were retained only if title, abstract, or MeSH terms contained terms from a curated relevance dictionary (60+ terms). This removed 2,489 false positives, primarily from journal abbreviation collisions (JPS → Journal of Physiological Sciences) and author surname collisions (Tsumura, Kotaro). DOI-based cross-source matching confirmed zero overlap between J-STAGE and PubMed datasets.

**Classification**: Herbal formula names were extracted from Japanese-language articles using a dictionary of 257 Kampo formulas with longest-match-first string matching. Disease categories were assigned using keyword and MeSH-based matching against a taxonomy of 60+ conditions aligned with ICD-11 chapters.

The final integrated database contained **11,846 articles** (2,653 Japanese + 9,193 English), spanning 1954–2026. All scripts, search queries, and raw data are publicly available at the study repository.

---

## 付録: ファイル構成

```
data/
  merged_metadata.json          # J-STAGE 2誌統合 (2,653)
  metadata_with_abstracts.json  # 東洋医学雑誌 (2,003)
  jjsam_with_abstracts.json     # 鍼灸学会雑誌 (650)
  categories_v2.json            # 疾患カテゴリ体系 v2
  categories_v3.json            # ICD-11準拠カテゴリ体系 v3 (144カテゴリ)
  integrated_db.json            # 統合DB (11,846)
  author_aliases.json           # 著者名寄せ (623ペア)
  pubmed/
    pubmed_all_merged.json      # PubMed生データ (11,682)
    pubmed_cleaned.json         # ノイズ除去後 (9,193)
    pubmed_noise_removed.json   # 除去ノイズ (2,489, 監査用)
    pubmed_tagged.json          # カテゴリ付き (9,193)
    pubmed_L{1-3}_*.json        # サブクエリ別結果 (17ファイル)
    pubmed_layer{1-3}.json      # Layer別統合結果

output/
  kampo_db_v3.json              # JP側DB (方剤名・カテゴリ付き)

dictionaries.py                 # 方剤辞書 (262方剤)
scrape_pubmed.py                # PubMed 3層検索 (17サブクエリ)
clean_pubmed.py                 # ノイズ除去
tag_pubmed.py                   # PubMedカテゴリ付与
build_v3.py                     # JP側DB構築
build_integrated_db.py          # 統合DB構築
```
