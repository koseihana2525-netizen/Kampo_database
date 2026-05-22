"""
Duagnosis Kampo KB - 時系列分析
方剤の出現頻度を年別に集計し、インタラクティブなグラフをD3.jsで生成

Usage:
    python timeline.py                    # extracted_data.json を使用
    python timeline.py --source jstage    # J-STAGEメタデータから直接
"""

import argparse
import json
from collections import Counter, defaultdict

from config import EXTRACTED_DATA_PATH, METADATA_PATH, TIMELINE_HTML_PATH
from dictionaries import get_formula_info


def load_extracted_data(path=None):
    """抽出済みデータを読み込む"""
    path = path or str(EXTRACTED_DATA_PATH)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_yearly_stats(extracted_cases):
    """年別の方剤出現頻度を集計"""
    yearly_formula = defaultdict(Counter)  # year -> Counter(formula_name)
    yearly_origin = defaultdict(Counter)   # year -> Counter(origin)
    yearly_total = Counter()               # year -> total articles

    for case in extracted_cases:
        year = case.get("year", "")
        if not year:
            continue
        if isinstance(year, str) and len(year) >= 4:
            year = int(year[:4])
        elif isinstance(year, (int, float)):
            year = int(year)
        else:
            continue

        yearly_total[year] += 1

        for f in case.get("formulas", []):
            name = f["name"]
            origin = f.get("origin", "不明")
            yearly_formula[year][name] += 1
            yearly_origin[year][origin] += 1

    return yearly_formula, yearly_origin, yearly_total


def generate_timeline_html(yearly_formula, yearly_origin, yearly_total):
    """D3.jsによるインタラクティブ時系列グラフHTML"""

    years = sorted(yearly_total.keys())
    if not years:
        return "<html><body><p>データがありません。</p></body></html>"

    # 年別の経方/後世方カウント
    origin_data = []
    for y in years:
        origin_data.append({
            "year": y,
            "total": yearly_total[y],
            "経方": yearly_origin[y].get("経方", 0),
            "後世方": yearly_origin[y].get("後世方", 0),
            "不明": yearly_origin[y].get("不明", 0),
        })

    # トップ方剤（全期間）
    total_formula = Counter()
    for y in years:
        total_formula.update(yearly_formula[y])
    top_formulas = [name for name, _ in total_formula.most_common(20)]

    # 方剤別年次データ
    formula_yearly = {}
    for name in top_formulas:
        info = get_formula_info(name)
        origin = info["origin"] if info else "不明"
        series = []
        for y in years:
            series.append({"year": y, "count": yearly_formula[y].get(name, 0)})
        formula_yearly[name] = {"data": series, "origin": origin}

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Duagnosis Kampo KB - 時系列分析</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; color: #333; }}
  .header {{ background: #1B3A5C; color: white; padding: 24px 32px; }}
  .header h1 {{ font-size: 24px; font-weight: 500; }}
  .header p {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
  .section {{ background: white; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .section h2 {{ font-size: 18px; color: #1B3A5C; margin-bottom: 16px; border-bottom: 2px solid #E8F0F8; padding-bottom: 8px; }}
  .chart {{ width: 100%; }}
  .legend {{ display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px; flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 2px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #1B3A5C; color: white; padding: 8px 12px; text-align: left; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #eee; }}
  tr:hover {{ background: #f8f9fa; }}
  .bar-cell {{ position: relative; }}
  .bar {{ height: 20px; border-radius: 3px; display: inline-block; }}
  .tooltip {{ position: absolute; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px 12px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); pointer-events: none; z-index: 100; }}
</style>
</head>
<body>
<div class="header">
  <h1>Duagnosis Kampo KB - 時系列分析</h1>
  <p>方剤出現頻度の年次推移 | {years[0]}-{years[-1]}年 | {sum(yearly_total.values())}件</p>
</div>
<div class="container">
  <div class="section">
    <h2>経方 vs 後世方 年別出現数</h2>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#2563EB"></div> 経方</div>
      <div class="legend-item"><div class="legend-dot" style="background:#EA580C"></div> 後世方</div>
      <div class="legend-item"><div class="legend-dot" style="background:#9CA3AF"></div> 分類不明</div>
    </div>
    <div id="origin-chart" class="chart"></div>
  </div>

  <div class="section">
    <h2>方剤別出現頻度トップ20</h2>
    <div id="formula-chart" class="chart"></div>
  </div>

  <div class="section">
    <h2>方剤別年次推移（トップ20）</h2>
    <table>
      <thead>
        <tr>
          <th>方剤名</th>
          <th>分類</th>
          <th>合計</th>
          {"".join(f'<th>{y}</th>' for y in years)}
        </tr>
      </thead>
      <tbody>
        {"".join(
          f'''<tr>
            <td>{name}</td>
            <td style="color:{'#2563EB' if formula_yearly[name]['origin']=='経方' else '#EA580C' if formula_yearly[name]['origin']=='後世方' else '#9CA3AF'}">{formula_yearly[name]['origin']}</td>
            <td><strong>{total_formula[name]}</strong></td>
            {"".join(f'<td>{yearly_formula[y].get(name,0) or "-"}</td>' for y in years)}
          </tr>'''
          for name in top_formulas
        )}
      </tbody>
    </table>
  </div>
</div>
<div id="tooltip" class="tooltip" style="display:none"></div>
<script>
const originData = {json.dumps(origin_data, ensure_ascii=False)};
const tooltip = d3.select('#tooltip');

// 経方/後世方のスタックバーチャート
(function() {{
  const container = document.getElementById('origin-chart');
  const margin = {{top: 20, right: 30, bottom: 40, left: 50}};
  const width = container.clientWidth - margin.left - margin.right;
  const height = 300 - margin.top - margin.bottom;

  const svg = d3.select('#origin-chart').append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  const x = d3.scaleBand().domain(originData.map(d => d.year)).range([0, width]).padding(0.3);
  const maxY = d3.max(originData, d => d['経方'] + d['後世方'] + d['不明']);
  const y = d3.scaleLinear().domain([0, maxY]).nice().range([height, 0]);

  svg.append('g').attr('transform', `translate(0,${{height}})`).call(d3.axisBottom(x));
  svg.append('g').call(d3.axisLeft(y));

  const keys = ['経方', '後世方', '不明'];
  const colors = {{'経方': '#2563EB', '後世方': '#EA580C', '不明': '#9CA3AF'}};

  const stack = d3.stack().keys(keys)(originData);

  svg.selectAll('.layer')
    .data(stack).enter().append('g')
    .attr('fill', (d, i) => colors[keys[i]])
    .selectAll('rect').data(d => d).enter().append('rect')
    .attr('x', d => x(d.data.year))
    .attr('y', d => y(d[1]))
    .attr('height', d => y(d[0]) - y(d[1]))
    .attr('width', x.bandwidth())
    .attr('rx', 2)
    .on('mouseover', (e, d) => {{
      tooltip.style('display', 'block')
        .html(`${{d.data.year}}年<br>経方: ${{d.data['経方']}}<br>後世方: ${{d.data['後世方']}}<br>論文数: ${{d.data.total}}`)
        .style('left', (e.pageX + 10) + 'px').style('top', (e.pageY - 10) + 'px');
    }})
    .on('mouseout', () => tooltip.style('display', 'none'));
}})();

// 方剤別出現頻度の横棒グラフ
(function() {{
  const formulaData = {json.dumps([{"name": n, "count": total_formula[n], "origin": formula_yearly[n]["origin"]} for n in top_formulas], ensure_ascii=False)};

  const container = document.getElementById('formula-chart');
  const margin = {{top: 10, right: 30, bottom: 30, left: 180}};
  const width = container.clientWidth - margin.left - margin.right;
  const height = formulaData.length * 28;

  const svg = d3.select('#formula-chart').append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  const x = d3.scaleLinear().domain([0, d3.max(formulaData, d => d.count)]).nice().range([0, width]);
  const y = d3.scaleBand().domain(formulaData.map(d => d.name)).range([0, height]).padding(0.2);

  svg.append('g').attr('transform', `translate(0,${{height}})`).call(d3.axisBottom(x).ticks(5));
  svg.append('g').call(d3.axisLeft(y));

  const colors = {{'経方': '#2563EB', '後世方': '#EA580C', '不明': '#9CA3AF'}};

  svg.selectAll('rect').data(formulaData).enter().append('rect')
    .attr('x', 0).attr('y', d => y(d.name))
    .attr('width', d => x(d.count)).attr('height', y.bandwidth())
    .attr('fill', d => colors[d.origin] || '#9CA3AF')
    .attr('rx', 3);

  svg.selectAll('.count-label').data(formulaData).enter().append('text')
    .attr('x', d => x(d.count) + 5).attr('y', d => y(d.name) + y.bandwidth() / 2)
    .attr('dy', '0.35em').attr('font-size', '11px').attr('fill', '#666')
    .text(d => d.count);
}})();
</script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Duagnosis Kampo KB - 時系列分析")
    parser.add_argument("--input", type=str, default=None, help="extracted_data.json のパス")
    args = parser.parse_args()

    print("=" * 60)
    print("Duagnosis Kampo KB - 時系列分析")
    print("=" * 60)

    # データ読み込み
    if args.input:
        extracted = load_extracted_data(args.input)
    else:
        try:
            extracted = load_extracted_data()
        except FileNotFoundError:
            print("extracted_data.json が見つかりません。先に analyze.py を実行してください。")
            from sample_data import SAMPLE_CASES
            from analyze import extract_all_entities
            extracted = [extract_all_entities(case) for case in SAMPLE_CASES]

    print(f"\n対象データ: {len(extracted)}件")

    # 年別集計
    print("\n[1/2] 年別集計中...")
    yearly_formula, yearly_origin, yearly_total = compute_yearly_stats(extracted)

    years = sorted(yearly_total.keys())
    print(f"  年範囲: {years[0]}-{years[-1]}" if years else "  年データなし")
    for y in years:
        keiho = yearly_origin[y].get("経方", 0)
        gosei = yearly_origin[y].get("後世方", 0)
        print(f"  {y}: {yearly_total[y]}件 (経方={keiho}, 後世方={gosei})")

    # HTML生成
    print("\n[2/2] HTML生成中...")
    html = generate_timeline_html(yearly_formula, yearly_origin, yearly_total)
    with open(TIMELINE_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  出力: {TIMELINE_HTML_PATH}")

    print("\n" + "=" * 60)
    print("完了！")
    print("=" * 60)


if __name__ == "__main__":
    main()
