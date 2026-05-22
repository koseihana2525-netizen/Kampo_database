"""
Duagnosis Kampo KB - 全論文カテゴリ分類
2,003件の全論文をカテゴリ別に分類し、データベースとして出力

Usage:
    python categorize.py              # 分類レポート表示
    python categorize.py --export     # data/metadata_categorized.json に保存
"""

import argparse
import json
from collections import Counter

from config import DATA_DIR, METADATA_PATH, OUTPUT_DIR


# ── カテゴリ定義（優先度順に判定） ──
CATEGORIES = [
    {
        "id": "exclude_admin",
        "label": "除外：学会運営",
        "keywords": ["プログラム", "日程", "会告", "名簿", "会則", "役員",
                     "目次", "索引", "正誤", "訂正", "編集後記", "投稿規定",
                     "事務局", "会員へ", "お知らせ", "各位に対する"],
        "include_in_analysis": False,
    },
    {
        "id": "exclude_event",
        "label": "除外：学会イベント",
        "keywords": ["学術総会", "セミナー", "シンポジウム", "ワークショップ",
                     "講習会", "研修会", "質疑応答", "パネルディスカッション",
                     "市民公開講座", "教育セッション", "ランチョン"],
        "include_in_analysis": False,
    },
    {
        "id": "exclude_memorial",
        "label": "除外：追悼・記念",
        "keywords": ["追悼", "逝去", "哀悼", "祝辞", "挨拶", "就任"],
        "include_in_analysis": False,
    },
    {
        "id": "clinical_formula",
        "label": "臨床：方剤名あり",
        "keywords": None,  # filter.pyの方剤名検出で判定
        "include_in_analysis": True,
        "note": "方剤名を含む論文（症例報告・臨床研究等）",
    },
    {
        "id": "clinical_kampo",
        "label": "臨床：漢方治療（方剤名なし）",
        "keywords": ["漢方治療", "漢方療法", "漢方薬", "和漢薬", "治験",
                     "治療経験", "治療効果", "漢方的治療", "漢方製剤"],
        "include_in_analysis": True,
        "note": "タイトルに方剤名はないが漢方臨床に関連",
    },
    {
        "id": "sho_study",
        "label": "証・弁証・腹証の研究",
        "keywords": ["証", "弁証", "腹証", "腹診", "舌診", "脈診", "気血水",
                     "陰陽", "虚実", "寒熱", "気血", "随証", "問診"],
        "include_in_analysis": True,
        "note": "証に関する研究",
    },
    {
        "id": "acupuncture",
        "label": "鍼灸・経絡",
        "keywords": ["鍼", "灸", "経絡", "経穴", "ツボ", "鍼灸", "刺鍼",
                     "置鍼", "電気鍼", "温灸"],
        "include_in_analysis": True,
        "note": "鍼灸治療に関する論文",
    },
    {
        "id": "crude_drug",
        "label": "生薬・薬理研究",
        "keywords": ["生薬", "薬理", "成分", "抽出", "含有", "附子", "甘草",
                     "人参", "黄耆", "大黄", "麻黄", "柴胡", "桂皮", "芍薬",
                     "黄芩", "黄連", "黄柏", "当帰", "川芎", "地黄", "茯苓",
                     "薬効", "品質"],
        "include_in_analysis": True,
        "note": "生薬の薬理・品質に関する研究",
    },
    {
        "id": "classic_text",
        "label": "古典・文献研究",
        "keywords": ["傷寒論", "金匱", "古典", "条文", "古方", "後世方",
                     "本草", "万病回春", "医心方", "内経", "素問", "霊枢",
                     "難経", "黄帝内経"],
        "include_in_analysis": True,
        "note": "古典文献の研究",
    },
    {
        "id": "education",
        "label": "漢方教育",
        "keywords": ["漢方教育", "漢方医学教育", "東洋医学教育", "伝統医学教育",
                     "カリキュラム", "医学生", "看護学生", "薬学部",
                     "教育効果", "ゲーミフィケーション"],
        "include_in_analysis": False,
        "note": "漢方教育に関する論文",
    },
    {
        "id": "survey_safety",
        "label": "調査・制度・安全性",
        "keywords": ["意識調査", "実態調査", "アンケート", "処方動向",
                     "副作用情報", "安全性情報", "ヒヤリ", "ポリファーマシー",
                     "薬局方", "医薬品副作用", "リスクマネージメント",
                     "認識度", "処方実態", "処方状況", "医薬品等安全"],
        "include_in_analysis": False,
        "note": "調査・制度・安全性に関する論文",
    },
    {
        "id": "basic_research",
        "label": "基礎研究",
        "keywords": ["マウス", "ラット", "in vitro", "培養細胞",
                     "サイトカイン", "DNA", "遺伝子", "アポトーシス",
                     "肥満マウス"],
        "include_in_analysis": False,
        "note": "動物実験・細胞実験等",
    },
    {
        "id": "disease_only",
        "label": "疾患・症状（方剤名なし）",
        "keywords": None,  # デフォルトの疾患関連
        "include_in_analysis": True,
        "note": "疾患名を含むが方剤名がない論文",
    },
]


def has_formula_in_title(title):
    """タイトルに方剤名を含むか（filter.pyのロジック簡易版）"""
    import re
    from dictionaries import FORMULAS, EXTRA_FORMULAS
    for info in FORMULAS.values():
        if info["name"] in title:
            return True
        for alias in info.get("aliases", []):
            if alias in title:
                return True
    for info in EXTRA_FORMULAS.values():
        if info["name"] in title:
            return True
        for alias in info.get("aliases", []):
            if alias in title:
                return True
    pattern = re.compile(r'[\u4e00-\u9fff]{2,8}(?:湯|散|丸|飲|膏)')
    from dictionaries import FORMULA_EXCLUDE
    for m in pattern.finditer(title):
        if m.group() not in FORMULA_EXCLUDE:
            return True
    return False


def categorize_article(title):
    """論文をカテゴリに分類"""
    # 1. 除外カテゴリ（学会運営・イベント・追悼）
    for cat in CATEGORIES:
        if cat["id"].startswith("exclude_") and cat["keywords"]:
            for kw in cat["keywords"]:
                if kw in title:
                    return cat["id"]

    # 2. 方剤名あり → clinical_formula
    if has_formula_in_title(title):
        return "clinical_formula"

    # 3. キーワードベースのカテゴリ判定
    for cat in CATEGORIES:
        if cat["id"] in ("exclude_admin", "exclude_event", "exclude_memorial",
                         "clinical_formula", "disease_only"):
            continue
        if cat["keywords"]:
            for kw in cat["keywords"]:
                if kw in title:
                    return cat["id"]

    # 4. 疾患関連キーワード
    disease_kw = ["症", "炎", "痛", "病", "障害", "不全", "癌", "腫瘍",
                  "感染", "糖尿", "高血圧", "アレルギー", "アトピー",
                  "喘息", "潰瘍", "肝", "腎", "出血", "不妊"]
    for kw in disease_kw:
        if kw in title:
            return "disease_only"

    return "other"


def categorize_all(articles):
    """全論文を分類"""
    results = []
    for art in articles:
        title = art.get("title_ja", "")
        cat_id = categorize_article(title)
        cat_info = next((c for c in CATEGORIES if c["id"] == cat_id), None)
        results.append({
            **art,
            "category_id": cat_id,
            "category_label": cat_info["label"] if cat_info else "その他",
            "include_in_analysis": cat_info["include_in_analysis"] if cat_info else False,
        })
    return results


def print_report(categorized):
    """カテゴリ分類レポート"""
    total = len(categorized)
    cat_counts = Counter(a["category_id"] for a in categorized)

    print("=" * 60)
    print("全論文カテゴリ分類レポート")
    print("=" * 60)
    print(f"\n総論文数: {total}")

    # カテゴリ別の表
    print(f"\n{'カテゴリ':<30} {'件数':>5} {'割合':>6} {'分析対象':>8}")
    print("-" * 55)
    analysis_total = 0
    for cat in CATEGORIES:
        cnt = cat_counts.get(cat["id"], 0)
        pct = cnt / total * 100
        flag = "○" if cat.get("include_in_analysis") else "×"
        if cat.get("include_in_analysis"):
            analysis_total += cnt
        print(f"{cat['label']:<28} {cnt:>5} {pct:>5.1f}% {flag:>8}")

    other_cnt = cat_counts.get("other", 0)
    print(f"{'その他':<28} {other_cnt:>5} {other_cnt/total*100:>5.1f}%        ?")
    print("-" * 55)
    print(f"{'分析対象合計':<28} {analysis_total:>5} {analysis_total/total*100:>5.1f}%")


def generate_category_html(categorized):
    """カテゴリ一覧のインタラクティブHTML"""
    cat_counts = Counter(a["category_id"] for a in categorized)
    total = len(categorized)

    # カテゴリごとの年別分布
    cat_year = {}
    for a in categorized:
        cid = a["category_id"]
        y = a.get("pubyear", "")[:4] if a.get("pubyear") else ""
        if y:
            cat_year.setdefault(cid, Counter())[y] += 1

    # テーブル行
    rows = ""
    for a in categorized:
        title = a.get("title_ja", "")[:60]
        year = a.get("pubyear", "")[:4] if a.get("pubyear") else ""
        link = a.get("link", "")
        cat_label = a.get("category_label", "")
        cat_id = a.get("category_id", "")
        incl = "○" if a.get("include_in_analysis") else ""
        rows += f'<tr data-cat="{cat_id}"><td>{year}</td><td><a href="{link}" target="_blank">{title}</a></td><td>{cat_label}</td><td>{incl}</td></tr>\n'

    # カテゴリフィルターボタン
    buttons = '<button class="filter-btn active" data-cat="all">全て ({0})</button>\n'.format(total)
    for cat in CATEGORIES:
        cnt = cat_counts.get(cat["id"], 0)
        if cnt > 0:
            buttons += f'<button class="filter-btn" data-cat="{cat["id"]}">{cat["label"]} ({cnt})</button>\n'
    other_cnt = cat_counts.get("other", 0)
    if other_cnt:
        buttons += f'<button class="filter-btn" data-cat="other">その他 ({other_cnt})</button>\n'

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Duagnosis Kampo KB - 全論文データベース</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; color: #333; }}
  .header {{ background: #1B3A5C; color: white; padding: 24px 32px; }}
  .header h1 {{ font-size: 24px; font-weight: 500; }}
  .header p {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
  .filters {{ margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px; }}
  .filter-btn {{ padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; background: white;
                 cursor: pointer; font-size: 12px; }}
  .filter-btn.active {{ background: #1B3A5C; color: white; border-color: #1B3A5C; }}
  .filter-btn:hover {{ background: #e8f0f8; }}
  .filter-btn.active:hover {{ background: #2a4f7a; }}
  .section {{ background: white; border-radius: 8px; padding: 24px; margin-bottom: 24px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ background: #1B3A5C; color: white; padding: 8px 12px; text-align: left; position: sticky; top: 0; cursor: pointer; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #eee; }}
  tr:hover {{ background: #f8f9fa; }}
  a {{ color: #1B3A5C; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .table-container {{ max-height: 70vh; overflow-y: auto; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
  .stat {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .stat .num {{ font-size: 28px; font-weight: 700; color: #1B3A5C; }}
  .stat .lbl {{ font-size: 12px; color: #666; margin-top: 4px; }}
  #count {{ font-size: 14px; color: #666; margin-bottom: 8px; }}
</style>
</head>
<body>
<div class="header">
  <h1>Duagnosis Kampo KB - 全論文データベース</h1>
  <p>日本東洋医学雑誌 1982-2025 | 全{total}件のカテゴリ分類</p>
</div>
<div class="container">
  <div class="stats">
    <div class="stat"><div class="num">{total}</div><div class="lbl">総論文数</div></div>
    <div class="stat"><div class="num">{cat_counts.get('clinical_formula',0)}</div><div class="lbl">方剤名あり</div></div>
    <div class="stat"><div class="num">{cat_counts.get('acupuncture',0)}</div><div class="lbl">鍼灸</div></div>
    <div class="stat"><div class="num">{cat_counts.get('sho_study',0)}</div><div class="lbl">証の研究</div></div>
  </div>
  <div class="section">
    <div class="filters">{buttons}</div>
    <div id="count"></div>
    <div class="table-container">
    <table id="articles">
      <thead><tr><th>年</th><th>タイトル</th><th>カテゴリ</th><th>分析</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
  </div>
</div>
<script>
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const cat = btn.dataset.cat;
    let shown = 0;
    document.querySelectorAll('#articles tbody tr').forEach(tr => {{
      if (cat === 'all' || tr.dataset.cat === cat) {{
        tr.style.display = '';
        shown++;
      }} else {{
        tr.style.display = 'none';
      }}
    }});
    document.getElementById('count').textContent = shown + '件表示中';
  }});
}});
document.getElementById('count').textContent = '{total}件表示中';
</script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="全論文カテゴリ分類")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    categorized = categorize_all(articles)
    print_report(categorized)

    if args.export:
        # JSON保存
        out_path = DATA_DIR / "metadata_categorized.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(categorized, f, ensure_ascii=False, indent=2)
        print(f"\n保存: {out_path}")

        # HTML保存
        html = generate_category_html(categorized)
        html_path = OUTPUT_DIR / "database.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML: {html_path}")


if __name__ == "__main__":
    main()
