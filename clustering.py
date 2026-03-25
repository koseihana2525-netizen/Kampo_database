"""
Duagnosis Kampo KB - クラスタリング分析
共起データからHDBSCANクラスタリングを行い、古典的弁証体系との重なりを分析

Usage:
    python clustering.py                    # サンプルデータ
    python clustering.py --source jstage    # J-STAGEデータ
    python clustering.py --method kmeans --n-clusters 6  # k-means指定
"""

import argparse
import json
import numpy as np
from collections import Counter, defaultdict

from config import EXTRACTED_DATA_PATH, CLUSTERS_HTML_PATH
from dictionaries import PATTERN_TERMS, get_formula_info


def load_extracted_data(path=None):
    """抽出済みデータを読み込む"""
    path = path or str(EXTRACTED_DATA_PATH)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_entity_matrix(extracted_cases):
    """症例×エンティティの出現行列を構築"""
    # 全エンティティを収集
    all_entities = set()
    for case in extracted_cases:
        for f in case["formulas"]:
            all_entities.add(f"方_{f['name']}")
        for p in case["patterns"]:
            all_entities.add(f"証_{p['term']}")
        for s in case["symptoms"]:
            all_entities.add(f"症_{s['term']}")

    entity_list = sorted(all_entities)
    entity_idx = {e: i for i, e in enumerate(entity_list)}

    # 行列構築
    matrix = np.zeros((len(extracted_cases), len(entity_list)), dtype=float)
    for i, case in enumerate(extracted_cases):
        for f in case["formulas"]:
            matrix[i, entity_idx[f"方_{f['name']}"]] = 1
        for p in case["patterns"]:
            matrix[i, entity_idx[f"証_{p['term']}"]] = 1
        for s in case["symptoms"]:
            matrix[i, entity_idx[f"症_{s['term']}"]] = 1

    return matrix, entity_list


def build_entity_cooccurrence_matrix(extracted_cases):
    """エンティティ間の共起行列を構築（エンティティをクラスタリング対象に）"""
    all_entities = set()
    for case in extracted_cases:
        for f in case["formulas"]:
            all_entities.add(f"方_{f['name']}")
        for p in case["patterns"]:
            all_entities.add(f"証_{p['term']}")
        for s in case["symptoms"]:
            all_entities.add(f"症_{s['term']}")

    entity_list = sorted(all_entities)
    entity_idx = {e: i for i, e in enumerate(entity_list)}
    n = len(entity_list)

    cooc = np.zeros((n, n), dtype=float)
    for case in extracted_cases:
        entities_in_case = set()
        for f in case["formulas"]:
            entities_in_case.add(f"方_{f['name']}")
        for p in case["patterns"]:
            entities_in_case.add(f"証_{p['term']}")
        for s in case["symptoms"]:
            entities_in_case.add(f"症_{s['term']}")

        for e in entities_in_case:
            idx = entity_idx[e]
            cooc[idx, idx] += 1  # 自己出現
            for e2 in entities_in_case:
                if e != e2:
                    cooc[entity_idx[e], entity_idx[e2]] += 1

    return cooc, entity_list


def cluster_entities(cooc_matrix, entity_list, method="hdbscan", n_clusters=6):
    """エンティティをクラスタリング"""
    if method == "hdbscan":
        try:
            from sklearn.cluster import HDBSCAN
            clusterer = HDBSCAN(min_cluster_size=3, min_samples=2, metric="cosine")
            labels = clusterer.fit_predict(cooc_matrix)
        except ImportError:
            print("  HDBSCAN not available, falling back to k-means")
            method = "kmeans"

    if method == "kmeans":
        from sklearn.cluster import KMeans
        # 正規化
        from sklearn.preprocessing import normalize
        normed = normalize(cooc_matrix, axis=1)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(normed)

    return labels


def analyze_clusters(entity_list, labels, extracted_cases):
    """クラスターの特徴を分析"""
    cluster_ids = sorted(set(labels))
    results = []

    # 各クラスターの特徴語
    for cid in cluster_ids:
        members = [entity_list[i] for i in range(len(labels)) if labels[i] == cid]
        if not members:
            continue

        formulas = [m.split("_", 1)[1] for m in members if m.startswith("方_")]
        patterns = [m.split("_", 1)[1] for m in members if m.startswith("証_")]
        symptoms = [m.split("_", 1)[1] for m in members if m.startswith("症_")]

        # 弁証体系との重なりを計算
        overlap = compute_bianzheng_overlap(patterns)

        results.append({
            "cluster_id": int(cid),
            "size": len(members),
            "formulas": formulas,
            "patterns": patterns,
            "symptoms": symptoms,
            "top_terms": (formulas + patterns + symptoms)[:10],
            "bianzheng_overlap": overlap,
        })

    return results


def compute_bianzheng_overlap(pattern_terms):
    """クラスター内の証用語が各弁証体系とどれだけ重なるか"""
    overlap = {}
    for framework, subcats in PATTERN_TERMS.items():
        all_terms = []
        for terms in subcats.values():
            all_terms.extend(terms)
        matched = [t for t in pattern_terms if t in all_terms]
        overlap[framework] = {
            "count": len(matched),
            "total": len(pattern_terms) if pattern_terms else 1,
            "ratio": len(matched) / max(len(pattern_terms), 1),
            "matched_terms": matched,
        }
    return overlap


def generate_clusters_html(cluster_results, entity_list, labels):
    """クラスター分析結果のHTML可視化"""

    cluster_cards = ""
    for cr in cluster_results:
        cid = cr["cluster_id"]
        label = f"Cluster {cid}" if cid >= 0 else "Noise"

        # 弁証重なりバー
        overlap_bars = ""
        for fw, ov in cr["bianzheng_overlap"].items():
            pct = int(ov["ratio"] * 100)
            overlap_bars += f"""
            <div style="margin:4px 0">
              <div style="font-size:11px;color:#666">{fw} ({ov['count']}/{ov['total']})</div>
              <div style="background:#eee;border-radius:3px;height:16px;width:200px">
                <div style="background:#2563EB;height:16px;border-radius:3px;width:{min(pct,100)}%;font-size:10px;color:white;line-height:16px;padding-left:4px">{pct}%</div>
              </div>
            </div>"""

        formulas_html = " ".join(f'<span class="tag formula">{f}</span>' for f in cr["formulas"][:15])
        patterns_html = " ".join(f'<span class="tag pattern">{p}</span>' for p in cr["patterns"][:15])
        symptoms_html = " ".join(f'<span class="tag symptom">{s}</span>' for s in cr["symptoms"][:15])

        cluster_cards += f"""
        <div class="cluster-card">
          <h3>{label} <span style="font-size:13px;color:#888">({cr['size']}要素)</span></h3>
          <div style="margin:8px 0">
            <strong>方剤:</strong> {formulas_html or '<span style="color:#aaa">なし</span>'}
          </div>
          <div style="margin:8px 0">
            <strong>証:</strong> {patterns_html or '<span style="color:#aaa">なし</span>'}
          </div>
          <div style="margin:8px 0">
            <strong>症状:</strong> {symptoms_html or '<span style="color:#aaa">なし</span>'}
          </div>
          <div style="margin:12px 0">
            <strong>弁証体系との重なり:</strong>
            {overlap_bars}
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Duagnosis Kampo KB - クラスタリング分析</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; color: #333; }}
  .header {{ background: #1B3A5C; color: white; padding: 24px 32px; }}
  .header h1 {{ font-size: 24px; font-weight: 500; }}
  .header p {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
  .cluster-card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .cluster-card h3 {{ color: #1B3A5C; margin-bottom: 8px; font-size: 16px; }}
  .tag {{ display: inline-block; padding: 2px 6px; border-radius: 3px; margin: 2px; font-size: 11px; }}
  .tag.formula {{ background: #E6F1FB; color: #0C447C; }}
  .tag.pattern {{ background: #EEEDFE; color: #3C3489; }}
  .tag.symptom {{ background: #E1F5EE; color: #085041; }}
  .summary {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
</style>
</head>
<body>
<div class="header">
  <h1>Duagnosis Kampo KB - クラスタリング分析</h1>
  <p>教師なしクラスタリングによる漢方臨床知の再構造化 | {len(cluster_results)}クラスター検出</p>
</div>
<div class="container">
  <div class="summary">
    <h2 style="color:#1B3A5C;margin-bottom:12px">分析サマリー</h2>
    <p>総エンティティ数: {len(entity_list)} | クラスター数: {len([c for c in cluster_results if c['cluster_id'] >= 0])}</p>
    <p style="margin-top:8px;font-size:13px;color:#666">
      核心の問い: データ駆動型クラスターは、六経弁証・八綱弁証・気血津液弁証・臓腑弁証のどれとどの程度重なるか？
    </p>
  </div>
  {cluster_cards}
</div>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Duagnosis Kampo KB - クラスタリング分析")
    parser.add_argument("--source", choices=["sample", "jstage"], default="sample")
    parser.add_argument("--method", choices=["hdbscan", "kmeans"], default="kmeans")
    parser.add_argument("--n-clusters", type=int, default=6)
    parser.add_argument("--input", type=str, default=None, help="extracted_data.json のパス")
    args = parser.parse_args()

    print("=" * 60)
    print("Duagnosis Kampo KB - クラスタリング分析")
    print("=" * 60)

    # データ読み込み
    if args.input:
        extracted = load_extracted_data(args.input)
    else:
        # analyze.py を先に実行して extracted_data.json を生成しておく必要がある
        try:
            extracted = load_extracted_data()
        except FileNotFoundError:
            print("extracted_data.json が見つかりません。先に analyze.py を実行してください。")
            # サンプルデータで直接実行
            from sample_data import SAMPLE_CASES
            from analyze import extract_all_entities
            extracted = [extract_all_entities(case) for case in SAMPLE_CASES]

    print(f"\n対象データ: {len(extracted)}件")

    # 共起行列構築
    print("\n[1/3] 共起行列構築中...")
    cooc_matrix, entity_list = build_entity_cooccurrence_matrix(extracted)
    print(f"  エンティティ数: {len(entity_list)}")

    if len(entity_list) < 4:
        print("エンティティが少なすぎます。クラスタリングをスキップします。")
        return

    # クラスタリング
    print(f"\n[2/3] クラスタリング中... (method={args.method})")
    n_clusters = min(args.n_clusters, len(entity_list) // 2)
    labels = cluster_entities(cooc_matrix, entity_list, args.method, n_clusters)

    cluster_ids = sorted(set(labels))
    print(f"  検出クラスター数: {len([c for c in cluster_ids if c >= 0])}")
    if -1 in cluster_ids:
        noise_count = sum(1 for l in labels if l == -1)
        print(f"  ノイズ（未分類）: {noise_count}エンティティ")

    # クラスター分析
    print("\n[3/3] クラスター特徴分析中...")
    cluster_results = analyze_clusters(entity_list, labels, extracted)

    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    for cr in cluster_results:
        cid = cr["cluster_id"]
        label = f"Cluster {cid}" if cid >= 0 else "Noise"
        print(f"\n  {label} ({cr['size']}要素)")
        top_terms_str = ', '.join(cr['top_terms'])
        print(f"    特徴語トップ10: {top_terms_str}")
        for fw, ov in cr["bianzheng_overlap"].items():
            if ov["count"] > 0:
                print(f"    {fw}: {ov['count']}/{ov['total']} ({int(ov['ratio']*100)}%)")

    # HTML出力
    html = generate_clusters_html(cluster_results, entity_list, labels)
    with open(CLUSTERS_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n出力: {CLUSTERS_HTML_PATH}")

    print("\n" + "=" * 60)
    print("完了！")
    print("=" * 60)


if __name__ == "__main__":
    main()
