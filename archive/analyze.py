"""
Duagnosis Kampo KB - Entity Extraction & Co-occurrence Analysis
Phase 0 パイロット：方剤名・証・症状の自動抽出と共起ネットワーク構築

Usage:
    python analyze.py                    # サンプルデータで分析
    python analyze.py --source jstage    # J-STAGEメタデータ（抄録）で分析
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from itertools import combinations

from dictionaries import (
    FORMULAS, EXTRA_FORMULAS, FORMULA_EXCLUDE,
    PATTERN_TERMS, ABDOMINAL_TERMS, SYMPTOM_TERMS,
    get_all_formula_names, get_all_pattern_terms, get_all_symptom_terms,
    get_formula_info,
)
from config import METADATA_PATH, NETWORK_HTML_PATH, EXTRACTED_DATA_PATH


# ═══════════════════════════════════════════
# 1. ENTITY EXTRACTION
# ═══════════════════════════════════════════

def extract_formulas(text):
    """方剤名を抽出（最長一致優先 + 辞書マッチング + パターンマッチ）

    最長一致ロジック:
      「当帰四逆加呉茱萸生姜湯」があるとき、部分文字列の
      「四逆加呉茱萸生姜湯」「四逆湯」は抽出しない。
      テキスト中の各出現位置を記録し、より長い方剤名に
      完全に包含される短い方剤名を除外する。
    """
    # Step 1: 全候補を位置情報付きで収集
    candidates = []  # (start, end, name, tsumura_no, origin)

    # ツムラ方剤
    for num, info in FORMULAS.items():
        name = info["name"]
        for m in re.finditer(re.escape(name), text):
            candidates.append((m.start(), m.end(), name, num, info["origin"]))
        for alias in info.get("aliases", []):
            for m in re.finditer(re.escape(alias), text):
                candidates.append((m.start(), m.end(), name, num, info["origin"]))

    # 非ツムラ方剤
    for key, info in EXTRA_FORMULAS.items():
        name = info["name"]
        for m in re.finditer(re.escape(name), text):
            candidates.append((m.start(), m.end(), name, None, info["origin"]))
        for alias in info.get("aliases", []):
            for m in re.finditer(re.escape(alias), text):
                candidates.append((m.start(), m.end(), name, None, info["origin"]))

    # パターンマッチ（辞書にない方剤）
    pattern = r'[\u4e00-\u9fff]{2,8}(?:湯|散|丸|飲|膏)'
    for m in re.finditer(pattern, text):
        matched = m.group()
        # 既に辞書で候補に入っている名前は追加しない
        if not any(c[2] == matched for c in candidates):
            candidates.append((m.start(), m.end(), matched, None, "不明"))

    # Step 2: 最長一致フィルタ
    # 長い順にソートし、短い候補が長い候補に完全に包含されていたら除外
    candidates.sort(key=lambda c: -(c[1] - c[0]))  # 長い順
    kept = []
    for cand in candidates:
        s, e = cand[0], cand[1]
        # 既にkeptにある候補のスパンに完全包含されていないか確認
        subsumed = False
        for k in kept:
            if s >= k[0] and e <= k[1]:
                subsumed = True
                break
        if not subsumed:
            kept.append(cand)

    # Step 3: 重複名を除去 + 除外リスト適用
    found = []
    seen_names = set()
    for s, e, name, tsumura_no, origin in kept:
        if name not in seen_names and name not in FORMULA_EXCLUDE:
            found.append({"name": name, "tsumura_no": tsumura_no, "origin": origin})
            seen_names.add(name)

    return found


def extract_patterns(text):
    """証関連用語を抽出"""
    found = []
    for category, subcats in PATTERN_TERMS.items():
        for subcat, terms in subcats.items():
            for term in terms:
                if term in text:
                    found.append({"term": term, "category": category, "subcategory": subcat})
    for term in ABDOMINAL_TERMS:
        if term in text:
            found.append({"term": term, "category": "腹証", "subcategory": "腹証"})
    return found


def extract_symptoms(text):
    """症状用語を抽出"""
    found = []
    for category, terms in SYMPTOM_TERMS.items():
        for term in terms:
            if term in text:
                found.append({"term": term, "category": category})
    return found


def extract_all_entities(case):
    """1症例/論文から全エンティティを抽出"""
    text = case.get("title", "") + " " + case.get("text", "")
    return {
        "id": case.get("id", ""),
        "title": case.get("title", ""),
        "year": case.get("year", ""),
        "formulas": extract_formulas(text),
        "patterns": extract_patterns(text),
        "symptoms": extract_symptoms(text),
        "western_dx": case.get("dx", ""),
    }


def load_jstage_cases(filtered=True):
    """J-STAGEメタデータを分析用のcaseフォーマットに変換"""
    from config import DATA_DIR
    if filtered:
        fpath = DATA_DIR / "metadata_filtered.json"
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                articles = json.load(f)
        else:
            print("  metadata_filtered.json が見つかりません。filter.py --export を先に実行してください。")
            print("  フィルタなしのメタデータを使用します。")
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
    else:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)

    cases = []
    for i, art in enumerate(articles):
        title = art.get("title_ja", "") or art.get("title_en", "")
        abstract = art.get("abstract_ja", "") or art.get("abstract_en", "")
        if not title and not abstract:
            continue
        year = art.get("pubyear", "")
        if year and len(year) >= 4:
            year = int(year[:4])
        cases.append({
            "id": f"J{i+1:04d}",
            "title": title,
            "text": abstract,
            "year": year,
            "dx": "",
            "doi": art.get("doi", ""),
        })
    return cases


# ═══════════════════════════════════════════
# 2. CO-OCCURRENCE ANALYSIS
# ═══════════════════════════════════════════

def build_cooccurrence(extracted_cases):
    """共起マトリクスの構築"""
    cooccurrence = defaultdict(lambda: defaultdict(int))
    node_types = {}
    node_counts = Counter()
    node_origins = {}  # 方剤の経方/後世方フラグ

    for case in extracted_cases:
        entities = []
        for f in case["formulas"]:
            name = f"方_{f['name']}"
            entities.append(name)
            node_types[name] = "formula"
            node_counts[name] += 1
            node_origins[name] = f.get("origin", "不明")
        for p in case["patterns"]:
            name = f"証_{p['term']}"
            entities.append(name)
            node_types[name] = "pattern"
            node_counts[name] += 1
        for s in case["symptoms"]:
            name = f"症_{s['term']}"
            entities.append(name)
            node_types[name] = "symptom"
            node_counts[name] += 1

        for a, b in combinations(set(entities), 2):
            pair = tuple(sorted([a, b]))
            cooccurrence[pair[0]][pair[1]] += 1
            cooccurrence[pair[1]][pair[0]] += 1

    return cooccurrence, node_types, node_counts, node_origins


# ═══════════════════════════════════════════
# 3. NETWORK DATA GENERATION
# ═══════════════════════════════════════════

def generate_network_data(cooccurrence, node_types, node_counts, node_origins,
                          min_count=1, min_cooccurrence=1):
    """D3.js用のネットワークデータを生成"""
    valid_nodes = {n for n, c in node_counts.items() if c >= min_count}

    nodes = []
    for name in valid_nodes:
        display = name.split("_", 1)[1]
        ntype = node_types[name]
        node = {
            "id": name,
            "label": display,
            "type": ntype,
            "count": node_counts[name],
        }
        if ntype == "formula":
            node["origin"] = node_origins.get(name, "不明")
        nodes.append(node)

    links = []
    seen = set()
    for source in cooccurrence:
        if source not in valid_nodes:
            continue
        for target, weight in cooccurrence[source].items():
            if target not in valid_nodes or weight < min_cooccurrence:
                continue
            pair = tuple(sorted([source, target]))
            if pair not in seen:
                seen.add(pair)
                links.append({"source": source, "target": target, "weight": weight})

    return {"nodes": nodes, "links": links}


# ═══════════════════════════════════════════
# 4. VISUALIZATION (Interactive HTML)
# ═══════════════════════════════════════════

def generate_html(network_data, extracted_cases, source_label="サンプル"):
    """インタラクティブな共起ネットワーク可視化HTMLを生成"""

    n_cases = len(extracted_cases)
    n_formulas = len(set(f["name"] for c in extracted_cases for f in c["formulas"]))
    n_patterns = len(set(p["term"] for c in extracted_cases for p in c["patterns"]))
    n_symptoms = len(set(s["term"] for c in extracted_cases for s in c["symptoms"]))

    extraction_rows = ""
    for c in extracted_cases:
        fs = ", ".join(f["name"] for f in c["formulas"])
        ps = ", ".join(p["term"] for p in c["patterns"])
        ss = ", ".join(s["term"] for s in c["symptoms"])
        title_short = c["title"][:40] + "..." if len(c["title"]) > 40 else c["title"]
        extraction_rows += f"""
        <tr>
            <td>{c['id']}</td>
            <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{c['title']}">{title_short}</td>
            <td><span class="tag formula">{fs}</span></td>
            <td><span class="tag pattern">{ps}</span></td>
            <td><span class="tag symptom">{ss}</span></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Duagnosis Kampo KB - Phase 0 Pilot Demo</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; color: #333; }}
  .header {{ background: #1B3A5C; color: white; padding: 24px 32px; }}
  .header h1 {{ font-size: 24px; font-weight: 500; }}
  .header p {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
  .stat-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .stat-card .number {{ font-size: 32px; font-weight: 700; color: #1B3A5C; }}
  .stat-card .label {{ font-size: 13px; color: #666; margin-top: 4px; }}
  .section {{ background: white; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .section h2 {{ font-size: 18px; color: #1B3A5C; margin-bottom: 16px; border-bottom: 2px solid #E8F0F8; padding-bottom: 8px; }}
  #network {{ width: 100%; height: 600px; border: 1px solid #eee; border-radius: 4px; }}
  .legend {{ display: flex; gap: 20px; margin-bottom: 12px; font-size: 13px; flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ background: #1B3A5C; color: white; padding: 8px 12px; text-align: left; position: sticky; top: 0; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #eee; }}
  tr:hover {{ background: #f8f9fa; }}
  .tag {{ display: inline-block; padding: 2px 6px; border-radius: 3px; margin: 1px; font-size: 11px; }}
  .tag.formula {{ background: #E6F1FB; color: #0C447C; }}
  .tag.pattern {{ background: #EEEDFE; color: #3C3489; }}
  .tag.symptom {{ background: #E1F5EE; color: #085041; }}
  .node-label {{ font-size: 10px; pointer-events: none; }}
  .tooltip {{ position: absolute; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px 12px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); pointer-events: none; z-index: 100; }}
  .table-container {{ max-height: 500px; overflow-y: auto; }}
</style>
</head>
<body>
<div class="header">
  <h1>Duagnosis Kampo Knowledge Base - Phase 0 Pilot</h1>
  <p>漢方臨床知の教師なし再構造化 | {source_label} {n_cases}件による共起ネットワーク分析</p>
</div>
<div class="container">
  <div class="stats">
    <div class="stat-card"><div class="number">{n_cases}</div><div class="label">分析対象数</div></div>
    <div class="stat-card"><div class="number">{n_formulas}</div><div class="label">抽出方剤数</div></div>
    <div class="stat-card"><div class="number">{n_patterns}</div><div class="label">抽出証関連用語数</div></div>
    <div class="stat-card"><div class="number">{n_symptoms}</div><div class="label">抽出症状数</div></div>
  </div>
  <div class="section">
    <h2>共起ネットワーク</h2>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#2563EB"></div> 方剤（経方）</div>
      <div class="legend-item"><div class="legend-dot" style="background:#EA580C"></div> 方剤（後世方）</div>
      <div class="legend-item"><div class="legend-dot" style="background:#9CA3AF"></div> 方剤（分類不明）</div>
      <div class="legend-item"><div class="legend-dot" style="background:#7C3AED"></div> 証関連用語</div>
      <div class="legend-item"><div class="legend-dot" style="background:#059669"></div> 症状</div>
    </div>
    <p style="font-size:12px;color:#888;margin-bottom:8px">ノードをドラッグして動かせます。ホバーで詳細表示。スクロールでズーム。</p>
    <div id="network"></div>
  </div>
  <div class="section">
    <h2>エンティティ抽出結果</h2>
    <div class="table-container">
    <table>
      <thead><tr><th>ID</th><th>タイトル</th><th>方剤</th><th>証</th><th>症状</th></tr></thead>
      <tbody>{extraction_rows}</tbody>
    </table>
    </div>
  </div>
</div>
<div id="tooltip" class="tooltip" style="display:none"></div>
<script>
const data = {json.dumps(network_data, ensure_ascii=False)};

const container = document.getElementById('network');
const width = container.clientWidth;
const height = 600;

const svg = d3.select('#network').append('svg')
  .attr('width', width).attr('height', height);

const g = svg.append('g');

// ズーム機能
svg.call(d3.zoom()
  .scaleExtent([0.2, 5])
  .on('zoom', (e) => g.attr('transform', e.transform)));

// 色マップ: 方剤は経方/後世方で色分け
function nodeColor(d) {{
  if (d.type === 'pattern') return '#7C3AED';
  if (d.type === 'symptom') return '#059669';
  if (d.origin === '経方') return '#2563EB';
  if (d.origin === '後世方') return '#EA580C';
  return '#9CA3AF';
}}

const tooltip = d3.select('#tooltip');

const simulation = d3.forceSimulation(data.nodes)
  .force('link', d3.forceLink(data.links).id(d => d.id).distance(80))
  .force('charge', d3.forceManyBody().strength(-150))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.count) * 6 + 8));

const link = g.append('g')
  .selectAll('line').data(data.links).enter().append('line')
  .attr('stroke', '#ddd').attr('stroke-width', d => Math.sqrt(d.weight) * 1.5)
  .attr('stroke-opacity', 0.5);

const node = g.append('g')
  .selectAll('circle').data(data.nodes).enter().append('circle')
  .attr('r', d => Math.sqrt(d.count) * 5 + 4)
  .attr('fill', nodeColor)
  .attr('stroke', '#fff').attr('stroke-width', 1.5)
  .attr('opacity', 0.85)
  .call(d3.drag()
    .on('start', (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on('drag', (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on('end', (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}))
  .on('mouseover', (e, d) => {{
    const typeLabel = d.type === 'formula' ? '方剤' : d.type === 'pattern' ? '証' : '症状';
    const originLabel = d.origin ? ` (${{d.origin}})` : '';
    tooltip.style('display', 'block')
      .html(`<strong>${{d.label}}</strong><br>タイプ: ${{typeLabel}}${{originLabel}}<br>出現: ${{d.count}}件`)
      .style('left', (e.pageX + 10) + 'px').style('top', (e.pageY - 10) + 'px');
  }})
  .on('mouseout', () => tooltip.style('display', 'none'));

const label = g.append('g')
  .selectAll('text').data(data.nodes).enter().append('text')
  .attr('class', 'node-label').attr('dx', 12).attr('dy', 4)
  .text(d => d.label).attr('fill', '#555');

simulation.on('tick', () => {{
  link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  node.attr('cx', d => d.x).attr('cy', d => d.y);
  label.attr('x', d => d.x).attr('y', d => d.y);
}});
</script>
</body>
</html>"""
    return html


# ═══════════════════════════════════════════
# 5. MAIN EXECUTION
# ═══════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Duagnosis Kampo KB - 共起ネットワーク分析")
    parser.add_argument("--source", choices=["sample", "jstage"], default="sample",
                        help="データソース: sample=サンプルデータ, jstage=J-STAGEメタデータ")
    parser.add_argument("--min-count", type=int, default=1,
                        help="ノードの最小出現回数 (default: 1)")
    parser.add_argument("--min-cooccurrence", type=int, default=1,
                        help="エッジの最小共起回数 (default: 1)")
    args = parser.parse_args()

    print("=" * 60)
    print("Duagnosis Kampo KB - Phase 0 Pilot Analysis")
    print("=" * 60)

    # データソース選択
    if args.source == "jstage":
        print(f"\n[0/4] J-STAGEメタデータ読み込み: {METADATA_PATH}")
        cases = load_jstage_cases()
        source_label = "J-STAGE論文"
        if not cases:
            print("メタデータが見つかりません。先に scraper.py を実行してください。")
            exit(1)
    else:
        from sample_data import SAMPLE_CASES
        cases = SAMPLE_CASES
        source_label = "サンプル症例"

    # Step 1: Extract entities
    print(f"\n[1/4] エンティティ抽出中... ({len(cases)}件)")
    extracted = [extract_all_entities(case) for case in cases]

    # 抽出サマリー
    total_f = sum(len(e["formulas"]) for e in extracted)
    total_p = sum(len(e["patterns"]) for e in extracted)
    total_s = sum(len(e["symptoms"]) for e in extracted)
    print(f"  方剤: {total_f}件, 証: {total_p}件, 症状: {total_s}件")

    # 方剤頻度トップ10
    formula_counter = Counter()
    for e in extracted:
        for f in e["formulas"]:
            formula_counter[f["name"]] += 1
    print("\n  ── 方剤出現頻度トップ10 ──")
    for name, cnt in formula_counter.most_common(10):
        info = get_formula_info(name)
        origin = info["origin"] if info else "不明"
        print(f"    {name} ({origin}): {cnt}件")

    # Step 2: Build co-occurrence
    print(f"\n[2/4] 共起マトリクス構築中...")
    cooccurrence, node_types, node_counts, node_origins = build_cooccurrence(extracted)
    print(f"  ノード数: {len(node_counts)}")
    print(f"  エッジ数: {sum(len(v) for v in cooccurrence.values()) // 2}")

    # Step 3: Generate network data
    print(f"\n[3/4] ネットワークデータ生成中...")
    network_data = generate_network_data(
        cooccurrence, node_types, node_counts, node_origins,
        min_count=args.min_count, min_cooccurrence=args.min_cooccurrence
    )
    print(f"  フィルタ後ノード: {len(network_data['nodes'])}")
    print(f"  フィルタ後エッジ: {len(network_data['links'])}")

    # Top co-occurrences
    print("\n  ── 上位共起ペア ──")
    all_pairs = []
    seen = set()
    for s in cooccurrence:
        for t, w in cooccurrence[s].items():
            pair = tuple(sorted([s, t]))
            if pair not in seen:
                seen.add(pair)
                all_pairs.append((s.split("_", 1)[1], t.split("_", 1)[1], w))
    all_pairs.sort(key=lambda x: -x[2])
    for a, b, w in all_pairs[:15]:
        print(f"    {a} ── {b}: {w}")

    # Step 4: Generate visualization
    print(f"\n[4/4] 可視化HTML生成中...")
    html = generate_html(network_data, extracted, source_label)

    with open(NETWORK_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  出力: {NETWORK_HTML_PATH}")

    with open(EXTRACTED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)
    print(f"  構造化データ: {EXTRACTED_DATA_PATH}")

    print("\n" + "=" * 60)
    print(f"完了！ {NETWORK_HTML_PATH} をブラウザで開いてください。")
    print("=" * 60)
