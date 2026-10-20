# 認知ギャップの主解析

論文「漢方関連文献における処方名言及と漢方思考概念言及の乖離」の解析の手順と、実装の構成。
**結果（数値・表）はこのリポジトリに含めない。** 未公開の研究成果のため、出力は `analysis_output/`（`.gitignore` 対象）に出る。

## 構成

| ファイル | 役割 |
|---|---|
| `gap_classifier.py` | 分類の単一の実装。標準ライブラリ + `dictionaries.py` + `romaji.py` だけで動く |
| `run_gap_analysis.py` | 主解析のコマンド。表と全論文の分類CSVを出力する（pandas・scipy・statsmodels が必要） |
| `romaji.py` | 方剤名の読み（ひらがな）→ ヘボン式ローマ字 |
| `tests/test_gap_classifier.py` | 分類のテスト（合成の短文のみ。実データは使わない） |
| `phase3_analysis.py` `pubtype_analysis.py` `run_revision_tasks.py` | 投稿版 v3 の値を作った旧処理の記録（置き換えず、残してある） |

## 分類（4象限）

処方名への言及（辞書A）と、漢方思考概念への言及（辞書B）の組み合わせで、各論文を4象限に分ける。
認知ギャップ = Q3 / (Q1 + Q3)。主解析は Conservative 版の辞書B。

`gap_classifier.classify(article, variant)` の variant は2つ。

- **`legacy`**: 投稿版 v3 の値を作った処理の再現。比較と感度分析のために残す。
- **`primary`**: 主解析。legacy からの修正は次の4点（辞書Bの語の追加・削除はしていない）。
  1. 英語の処方名検出を広げた。空白とハイフンを除いて照合する（`Sho-saiko-to` など）。全ツムラ処方のローマ字名と、0埋めなしのTJコード（`TJ-54`）も検出する。
     旧処理は、テキスト側のハイフンを空白に置換した後、ハイフンなしの名前で照合していたため、ハイフン付きの表記を検出できなかった。
  2. 英語の思考概念語のうち、ハイフン語（`yin-yang`、`kyo-jitsu` など）と末尾空白語（`'sho '`、`'hie '`）の扱いを直した。語境界で照合する。
  3. ラテン文字の発音記号を畳み込む（`shō` → `sho`）。日本語には触れない。
  4. `running piglet`（奔豚の英訳。処方名ではない）を処方名リストから除いた。思考概念語としては残る。

## 実行

入力は `data/integrated_db_japan.json`（投稿版のデータの固定スナップショット。リポジトリには含まれない。著者の手元とDriveにある）。
月次の更新パイプライン（`run_update.py`）は、このファイルを更新しない。論文の解析は固定したデータで行う。

```
python run_gap_analysis.py
python run_gap_analysis.py --db PATH/integrated_db_japan.json --out DIR
```

出力: `analysis_output/gap_primary/tables.md`（表）、`analysis_output/gap_primary/papers_classified.csv`（全論文の分類。legacy と primary の両方）。

表の内容: 4象限と日英OR、感度分析（辞書3段階）、論文タイプ別、Mantel–Haenszel 調整OR、年代別とトレンド、臨床研究に限定した比較、同一処方集合（ツムラ128処方）での比較。
どの表も主解析（primary）を先に、旧処理（legacy）を後に出す。

## 検証

- 旧処理の再現: `python run_gap_analysis.py --verify-legacy PATH/papers_classified_v2.csv` は、legacy が投稿版の分類CSVと全件一致するかを確かめる（不一致があれば終了コード1）。
- テスト: `python -m unittest discover -s tests`

## 著者の判断が必要な点（未決定）

- **症例報告の定義:** コード上に2つある。A（`pubtype_analysis.py`: 「治験」「奏効した」「○例」なども含む）と B（`run_revision_tasks.py`: 題名に「症例」「一例」など、Methodsの記述）。表は両方を出している。
- **英語の思考概念語の追加:** 辞書Bの英語側の語を増やすかどうか。増やす場合は専門家による語の採否が必要（`hiesho` など）。
- 妥当性の再検証（第2評価者、κ）は未実施。

## 注意

- `analysis_output/` と `data/integrated_db_japan.json` はコミットしない（`.gitignore` 済み）。
- 英語の処方名は、ツムラ128処方のローマ字名と、辞書にあるローマ字名のみを検出する。ピンイン表記や辞書にない処方は検出しない。
