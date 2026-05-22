import json, re, html as H
from collections import Counter

# === Load all data ===
with open('G:/マイドライブ/18_東洋医学雑誌/data/metadata.json','r',encoding='utf-8') as f:
    meta = json.load(f)
with open('G:/マイドライブ/18_東洋医学雑誌/output/extracted_data.json','r',encoding='utf-8') as f:
    ext = json.load(f)
with open('G:/マイドライブ/18_東洋医学雑誌/data/metadata_categorized.json','r',encoding='utf-8') as f:
    cat = json.load(f)

# === Build lookup maps ===
link_to_authors = {m['link']: m.get('authors_ja', []) for m in meta}
title_to_link = {c['title_ja']: c['link'] for c in cat}

link_to_formulas = {}
link_to_symptoms = {}
for e in ext:
    link = title_to_link.get(e['title'])
    if link:
        link_to_formulas[link] = [fm['name'] for fm in e.get('formulas', [])]
        link_to_symptoms[link] = [s['term'] for s in e.get('symptoms', [])]

# === Stats ===
all_authors = []
for m in meta:
    all_authors.extend(m.get('authors_ja', []))
author_counts = Counter(all_authors)
top_authors = list(author_counts.most_common(50))

all_formulas = []
for flist in link_to_formulas.values():
    all_formulas.extend(flist)
formula_counts = Counter(all_formulas)
top_formulas = list(formula_counts.most_common(50))

all_symptoms = []
for slist in link_to_symptoms.values():
    all_symptoms.extend(slist)
symptom_counts = Counter(all_symptoms)
top_symptoms = list(symptom_counts.most_common(44))

# === Build table rows ===
rows = []
for c in cat:
    link = c['link']
    authors = link_to_authors.get(link, [])
    formulas = link_to_formulas.get(link, [])
    symptoms = link_to_symptoms.get(link, [])
    cat_id = c['category_id']
    cat_label = c['category_label']
    year = c['pubyear']
    title = H.escape(c['title_ja'])
    has_analysis = '\u25cb' if c.get('include_in_analysis') else ''

    authors_str = H.escape(', '.join(authors))
    formulas_str = H.escape(', '.join(formulas))
    symptoms_str = H.escape(', '.join(symptoms))

    row = (f'<tr data-cat="{cat_id}">'
           f'<td>{year}</td>'
           f'<td><a href="{H.escape(link)}" target="_blank">{title}</a></td>'
           f'<td class="col-author">{authors_str}</td>'
           f'<td class="col-formula">{formulas_str}</td>'
           f'<td class="col-symptom">{symptoms_str}</td>'
           f'<td>{cat_label}</td>'
           f'<td>{has_analysis}</td>'
           f'</tr>')
    rows.append(row)

tbody = '\n'.join(rows)

# === Build option lists ===
def opts(items):
    return ''.join(f'<option value="{H.escape(n)}">{H.escape(n)} ({c})</option>' for n,c in items)

author_opts = opts(top_authors)
formula_opts = opts(top_formulas)
symptom_opts = opts(top_symptoms)

# === Category filter buttons ===
cat_counter = Counter(c['category_id'] for c in cat)
cat_labels = {}
for c in cat:
    cat_labels[c['category_id']] = c['category_label']

cat_order = ['exclude_admin','exclude_event','clinical_formula','clinical_kampo',
             'sho_study','acupuncture','crude_drug','classic_text','education',
             'survey_safety','basic_research','disease_only','other']
cat_btns = f'<button class="filter-btn active" data-cat="all">\u5168\u3066 ({len(cat)})</button>\n'
for cid in cat_order:
    if cid in cat_counter:
        lbl = cat_labels.get(cid, cid)
        cat_btns += f'<button class="filter-btn" data-cat="{cid}">{lbl} ({cat_counter[cid]})</button>\n'

n_formula = cat_counter.get('clinical_formula', 0)
n_acu = cat_counter.get('acupuncture', 0)
n_sho = cat_counter.get('sho_study', 0)

# === Assemble HTML ===
html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Duagnosis Kampo KB - \u5168\u8ad6\u6587\u30c7\u30fc\u30bf\u30d9\u30fc\u30b9</title>
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
  th {{ background: #1B3A5C; color: white; padding: 8px 12px; text-align: left; position: sticky; top: 0; }}
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

  .search-tabs {{ display: flex; gap: 0; margin-bottom: 0; }}
  .search-tab {{ padding: 8px 20px; border: 1px solid #ddd; border-bottom: none; border-radius: 6px 6px 0 0;
                 background: #f0f0f0; cursor: pointer; font-size: 13px; font-weight: 500; color: #666;
                 transition: background 0.15s; }}
  .search-tab.active {{ background: white; color: #1B3A5C; border-bottom: 1px solid white; margin-bottom: -1px; z-index: 1; }}
  .search-tab:hover:not(.active) {{ background: #e8f0f8; }}
  .search-tab .badge {{ display: inline-block; background: #1B3A5C; color: white; font-size: 10px;
                        padding: 1px 6px; border-radius: 8px; margin-left: 6px; }}
  .search-panels {{ border: 1px solid #ddd; border-radius: 0 8px 8px 8px; background: white;
                    padding: 16px; margin-bottom: 16px; }}
  .search-panel {{ display: none; align-items: center; gap: 8px; flex-wrap: wrap; }}
  .search-panel.active {{ display: flex; }}
  .search-panel input {{ padding: 7px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; width: 280px; }}
  .search-panel input:focus {{ outline: none; border-color: #1B3A5C; box-shadow: 0 0 0 2px rgba(27,58,92,0.15); }}
  .search-panel select {{ padding: 7px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; max-width: 320px; }}
  .search-info {{ font-size: 13px; color: #1B3A5C; font-weight: 500; margin-left: 4px; }}
  .clear-btn {{ padding: 6px 14px; border: 1px solid #ccc; border-radius: 4px; background: #fafafa;
                cursor: pointer; font-size: 12px; }}
  .clear-btn:hover {{ background: #fee; border-color: #c00; color: #c00; }}

  .col-author {{ max-width: 180px; font-size: 11px; color: #555; }}
  .col-formula {{ max-width: 160px; font-size: 11px; color: #2a6e2a; font-weight: 500; }}
  .col-symptom {{ max-width: 140px; font-size: 11px; color: #8b4513; }}
</style>
</head>
<body>
<div class="header">
  <h1>Duagnosis Kampo KB - \u5168\u8ad6\u6587\u30c7\u30fc\u30bf\u30d9\u30fc\u30b9</h1>
  <p>\u65e5\u672c\u6771\u6d0b\u533b\u5b66\u96d1\u8a8c 1982-2025 | \u5168{len(cat)}\u4ef6\u306e\u30ab\u30c6\u30b4\u30ea\u5206\u985e</p>
</div>
<div class="container">
  <div class="stats">
    <div class="stat"><div class="num">{len(cat)}</div><div class="lbl">\u7dcf\u8ad6\u6587\u6570</div></div>
    <div class="stat"><div class="num">{n_formula}</div><div class="lbl">\u65b9\u5264\u540d\u3042\u308a</div></div>
    <div class="stat"><div class="num">{n_acu}</div><div class="lbl">\u92fc\u7078</div></div>
    <div class="stat"><div class="num">{n_sho}</div><div class="lbl">\u8a3c\u306e\u7814\u7a76</div></div>
  </div>
  <div class="section">
    <div class="filters">{cat_btns}</div>

    <div class="search-tabs">
      <div class="search-tab active" data-panel="author">\u8457\u8005 <span class="badge">{len(author_counts)}\u4eba</span></div>
      <div class="search-tab" data-panel="formula">\u65b9\u5264 <span class="badge">{len(formula_counts)}\u7a2e</span></div>
      <div class="search-tab" data-panel="symptom">\u75c7\u5019 <span class="badge">{len(symptom_counts)}\u7a2e</span></div>
    </div>
    <div class="search-panels">
      <div class="search-panel active" id="panel-author">
        <input type="text" id="searchAuthor" placeholder="\u8457\u8005\u540d\u3067\u691c\u7d22\uff08\u4f8b\uff1a\u5bfa\u6fa4\u3001\u82b1\u8f2a\uff09..." />
        <select id="selectAuthor"><option value="">\u4e3b\u8981\u8457\u8005 Top50</option>{author_opts}</select>
        <button class="clear-btn" data-clear="author">\u30af\u30ea\u30a2</button>
        <span class="search-info" id="infoAuthor"></span>
      </div>
      <div class="search-panel" id="panel-formula">
        <input type="text" id="searchFormula" placeholder="\u65b9\u5264\u540d\u3067\u691c\u7d22\uff08\u4f8b\uff1a\u88dc\u4e2d\u76ca\u6c17\u6e6f\u3001\u4e94\u82d3\u6563\uff09..." />
        <select id="selectFormula"><option value="">\u4e3b\u8981\u65b9\u5264 Top50</option>{formula_opts}</select>
        <button class="clear-btn" data-clear="formula">\u30af\u30ea\u30a2</button>
        <span class="search-info" id="infoFormula"></span>
      </div>
      <div class="search-panel" id="panel-symptom">
        <input type="text" id="searchSymptom" placeholder="\u75c7\u5019\u3067\u691c\u7d22\uff08\u4f8b\uff1a\u982d\u75db\u3001\u51b7\u3048\u3001\u4e0d\u7720\uff09..." />
        <select id="selectSymptom"><option value="">\u4e3b\u8981\u75c7\u5019</option>{symptom_opts}</select>
        <button class="clear-btn" data-clear="symptom">\u30af\u30ea\u30a2</button>
        <span class="search-info" id="infoSymptom"></span>
      </div>
    </div>

    <div id="count"></div>
    <div class="table-container">
    <table id="articles">
      <thead><tr><th>\u5e74</th><th>\u30bf\u30a4\u30c8\u30eb</th><th>\u8457\u8005</th><th>\u65b9\u5264</th><th>\u75c7\u5019</th><th>\u30ab\u30c6\u30b4\u30ea</th><th>\u5206\u6790</th></tr></thead>
      <tbody>{tbody}</tbody>
    </table>
    </div>
  </div>
</div>
<script>
const rows = document.querySelectorAll('#articles tbody tr');
const catBtns = document.querySelectorAll('.filter-btn');
const countEl = document.getElementById('count');

let activeCat = 'all';
let queries = {{ author: '', formula: '', symptom: '' }};
const colIdx = {{ author: 2, formula: 3, symptom: 4 }};

document.querySelectorAll('.search-tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.search-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.panel).classList.add('active');
  }});
}});

// Also allow searching across all tabs simultaneously
// (queries persist when switching tabs)

catBtns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    catBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCat = btn.dataset.cat;
    applyFilters();
  }});
}});

['author','formula','symptom'].forEach(key => {{
  const cap = key.charAt(0).toUpperCase() + key.slice(1);
  const input = document.getElementById('search' + cap);
  const select = document.getElementById('select' + cap);
  input.addEventListener('input', () => {{
    queries[key] = input.value.trim();
    select.value = '';
    applyFilters();
  }});
  select.addEventListener('change', () => {{
    queries[key] = select.value;
    input.value = select.value;
    applyFilters();
  }});
}});

document.querySelectorAll('.clear-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const key = btn.dataset.clear;
    const cap = key.charAt(0).toUpperCase() + key.slice(1);
    queries[key] = '';
    document.getElementById('search' + cap).value = '';
    document.getElementById('select' + cap).value = '';
    applyFilters();
  }});
}});

function applyFilters() {{
  let shown = 0;
  rows.forEach(tr => {{
    const catOk = activeCat === 'all' || tr.dataset.cat === activeCat;
    let searchOk = true;
    for (const [key, q] of Object.entries(queries)) {{
      if (q) {{
        const cell = tr.children[colIdx[key]];
        if (!cell || !cell.textContent.includes(q)) {{
          searchOk = false;
          break;
        }}
      }}
    }}
    tr.style.display = (catOk && searchOk) ? '' : 'none';
    if (catOk && searchOk) shown++;
  }});
  countEl.textContent = shown + '\u4ef6\u8868\u793a\u4e2d';
  ['author','formula','symptom'].forEach(key => {{
    const cap = key.charAt(0).toUpperCase() + key.slice(1);
    const info = document.getElementById('info' + cap);
    info.textContent = queries[key] ? '\u300c' + queries[key] + '\u300d ' + shown + '\u4ef6' : '';
  }});
}}

countEl.textContent = rows.length + '\u4ef6\u8868\u793a\u4e2d';
</script>
</body>
</html>'''

with open('G:/マイドライブ/18_東洋医学雑誌/output/database.html','w',encoding='utf-8') as f:
    f.write(html)

print(f'Done! {len(rows)} rows, {len(formula_counts)} formulas, {len(symptom_counts)} symptoms, {len(author_counts)} authors')
