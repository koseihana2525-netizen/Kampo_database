"""
Duagnosis Kampo KB - プロジェクト設定
パス管理と定数定義
"""

from pathlib import Path

# プロジェクトルート（このファイルの場所を基準）
PROJECT_ROOT = Path(__file__).resolve().parent

# データディレクトリ
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 自動作成
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# J-STAGE設定
JSTAGE_API_URL = "https://api.jstage.jst.go.jp/searchapi/do"
JSTAGE_ISSN = "0287-4857"  # 日本東洋医学雑誌
JSTAGE_REQUEST_INTERVAL = 1.5  # 秒（robots.txt遵守）

# ファイルパス
METADATA_PATH = DATA_DIR / "metadata.json"
EXTRACTED_DATA_PATH = OUTPUT_DIR / "extracted_data.json"
NETWORK_HTML_PATH = OUTPUT_DIR / "pilot_demo.html"
CLUSTERS_HTML_PATH = OUTPUT_DIR / "clusters.html"
TIMELINE_HTML_PATH = OUTPUT_DIR / "timeline.html"
