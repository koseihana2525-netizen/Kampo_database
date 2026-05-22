# -*- coding: utf-8 -*-
"""
build_integrated_html.py — 統合エビデンスマップ HTML 生成

日本語誌 2,653本 + PubMed 9,193本 = 11,846本の
インタラクティブ可視化ダッシュボード
"""
import json, os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "data/integrated_db.json"), "r", encoding="utf-8") as f:
    db = json.load(f)

# HTMLに埋め込む用の軽量版を作る（abstractを50文字に）
for a in db["articles"]:
    if a.get("abstract"):
        a["abstract"] = a["abstract"][:100]
    # 不要フィールド除去
    a.pop("mesh", None)
    a.pop("pub_types", None)

db_json = json.dumps(db, ensure_ascii=False, separators=(',', ':'))

HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Japan Kampo & Acupuncture Evidence Map</title>
<style>
:root {
  --primary:#1a2a3a; --accent:#e67e22; --blue:#3498db;
  --green:#27ae60; --red:#e74c3c; --purple:#9b59b6;
  --bg:#f5f6fa; --card:#fff; --text:#333; --muted:#888;
  --kampo:#e67e22; --acup:#3498db; --pharma:#27ae60;
  --jp:#e74c3c; --en:#3498db;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Helvetica Neue','Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif;background:var(--bg);color:var(--text);line-height:1.5;}

.header{background:linear-gradient(135deg,#0f1923 0%,#1a2a3a 50%,#2c3e50 100%);color:#fff;padding:24px 28px;}
.header h1{font-size:20px;font-weight:300;letter-spacing:2px;}
.header h1 b{font-weight:700;color:var(--accent);}
.header .sub{font-size:12px;opacity:.6;margin-top:4px;}
.stats-row{display:flex;gap:12px;margin-top:14px;flex-wrap:wrap;}
.stat-chip{padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;}
.stat-chip.jp{background:rgba(231,76,60,.2);color:#ff8a80;}
.stat-chip.en{background:rgba(52,152,219,.2);color:#82b1ff;}
.stat-chip.total{background:rgba(255,255,255,.15);color:#fff;}

.nav-bar{background:#fff;padding:10px 28px;box-shadow:0 2px 8px rgba(0,0,0,.06);position:sticky;top:0;z-index:100;display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
.nav-tab{padding:7px 14px;border-radius:6px;cursor:pointer;font-size:13px;background:#f0f0f0;border:none;transition:all .15s;white-space:nowrap;}
.nav-tab:hover{background:#e0e0e0;}
.nav-tab.active{background:var(--primary);color:#fff;}
.search-wrap{margin-left:auto;position:relative;}
.search-wrap input{padding:8px 14px 8px 32px;border:2px solid #e0e0e0;border-radius:6px;font-size:14px;width:260px;outline:none;}
.search-wrap input:focus{border-color:var(--blue);}
.search-wrap::before{content:'\1F50D';position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:14px;}

.main{max-width:1300px;margin:0 auto;padding:20px 28px;}
.section-title{font-size:17px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:8px;}
.section-title .count{font-size:13px;color:var(--muted);font-weight:400;}

/* Dashboard */
.dash-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}
@media(max-width:768px){.dash-grid{grid-template-columns:1fr;}}
.dash-card{background:var(--card);border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);}
.dash-card h3{font-size:14px;color:var(--muted);margin-bottom:12px;font-weight:500;}

/* Chart containers */
.chart-container{position:relative;width:100%;height:300px;}
.bar-row{display:flex;align-items:center;gap:8px;margin-bottom:4px;font-size:12px;}
.bar-label{width:130px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;}
.bar-track{flex:1;height:20px;background:#f0f0f0;border-radius:3px;position:relative;display:flex;}
.bar-seg{height:100%;transition:width .3s;}
.bar-seg.jp-kampo{background:var(--kampo);border-radius:3px 0 0 3px;}
.bar-seg.jp-acup{background:var(--acup);}
.bar-seg.pm-kampo{background:rgba(230,126,34,.4);}
.bar-seg.pm-acup{background:rgba(52,152,219,.4);}
.bar-seg.pm-pharma{background:var(--pharma);}
.bar-count{width:50px;text-align:right;font-size:11px;color:var(--muted);flex-shrink:0;}

/* Timeline */
.tl-chart{display:flex;align-items:flex-end;gap:2px;height:200px;padding-top:10px;}
.tl-bar{flex:1;display:flex;flex-direction:column;justify-content:flex-end;position:relative;min-width:3px;}
.tl-bar .seg{width:100%;transition:height .3s;}
.tl-bar .seg.s-kampo{background:var(--kampo);}
.tl-bar .seg.s-acup{background:var(--acup);}
.tl-bar .seg.s-pm-kampo{background:rgba(230,126,34,.4);}
.tl-bar .seg.s-pm-acup{background:rgba(52,152,219,.4);}
.tl-bar .seg.s-pm-pharma{background:var(--green);}
.tl-bar:hover .seg{opacity:.8;}
.tl-bar .tip{display:none;position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:4px 8px;border-radius:4px;font-size:11px;white-space:nowrap;z-index:10;}
.tl-bar:hover .tip{display:block;}
.tl-axis{display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-top:4px;}

/* Legend */
.legend{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0;font-size:12px;}
.legend-item{display:flex;align-items:center;gap:4px;}
.legend-dot{width:12px;height:12px;border-radius:2px;flex-shrink:0;}

/* Category table */
.cat-table{width:100%;border-collapse:collapse;font-size:13px;}
.cat-table th{text-align:left;padding:8px 10px;background:#f8f8f8;border-bottom:2px solid #e0e0e0;position:sticky;top:44px;z-index:10;cursor:pointer;}
.cat-table th:hover{background:#e8e8e8;}
.cat-table td{padding:6px 10px;border-bottom:1px solid #f0f0f0;}
.cat-table tr:hover{background:#fafafa;}
.cat-table .num{text-align:right;font-variant-numeric:tabular-nums;}
.cat-table .bar-mini{display:inline-block;height:12px;border-radius:2px;vertical-align:middle;}

/* Article cards */
.art-list{display:flex;flex-direction:column;gap:8px;max-height:600px;overflow-y:auto;}
.art-card{background:var(--card);border-radius:8px;padding:12px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);border-left:3px solid var(--muted);}
.art-card.src-kampo{border-left-color:var(--kampo);}
.art-card.src-acupuncture{border-left-color:var(--acup);}
.art-card.src-pubmed_kampo{border-left-color:rgba(230,126,34,.5);}
.art-card.src-pubmed_acupuncture{border-left-color:rgba(52,152,219,.5);}
.art-card.src-pubmed_pharma{border-left-color:var(--green);}
.art-title{font-size:14px;font-weight:600;}
.art-title a{color:var(--text);text-decoration:none;}
.art-title a:hover{color:var(--blue);}
.art-meta{font-size:12px;color:var(--muted);margin-top:2px;}
.art-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px;}
.art-tag{font-size:10px;padding:2px 8px;border-radius:10px;background:#f0f0f0;}
.art-tag.src{background:var(--kampo);color:#fff;}

.hidden{display:none;}

/* Tooltip */
[data-tooltip]{position:relative;}
[data-tooltip]:hover::after{content:attr(data-tooltip);position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:4px 8px;border-radius:4px;font-size:11px;white-space:nowrap;z-index:999;}
</style>
</head>
<body>

<div class="header">
  <h1><b>Japan Kampo & Acupuncture</b> Evidence Map</h1>
  <div class="sub">Japanese Journals + PubMed — Integrated Database</div>
  <div class="stats-row" id="statsRow"></div>
</div>

<div class="nav-bar">
  <button class="nav-tab active" onclick="showView('dashboard')">📊 Dashboard</button>
  <button class="nav-tab" onclick="showView('categories')">🏷️ Categories</button>
  <button class="nav-tab" onclick="showView('timeline')">📈 Timeline</button>
  <button class="nav-tab" onclick="showView('articles')">📄 Articles</button>
  <div class="search-wrap">
    <input type="text" id="searchInput" placeholder="Search articles..." oninput="onSearch(this.value)">
  </div>
</div>

<div class="main">
  <div id="viewDashboard"></div>
  <div id="viewCategories" class="hidden"></div>
  <div id="viewTimeline" class="hidden"></div>
  <div id="viewArticles" class="hidden"></div>
</div>

<script>
const DB = __DB_JSON__;

// ─── Utility ───
function $(id){return document.getElementById(id);}
function showView(name){
  ['dashboard','categories','timeline','articles'].forEach(v=>{
    $('view'+v.charAt(0).toUpperCase()+v.slice(1)).classList.toggle('hidden',v!==name);
  });
  document.querySelectorAll('.nav-tab').forEach((t,i)=>{
    t.classList.toggle('active',['dashboard','categories','timeline','articles'][i]===name);
  });
  if(name==='timeline'&&!window._tlRendered){renderTimeline();window._tlRendered=true;}
  if(name==='categories'&&!window._catRendered){renderCategories();window._catRendered=true;}
}

// ─── Stats Row ───
function renderStats(){
  const s=DB.stats;
  $('statsRow').innerHTML=`
    <span class="stat-chip total"><b>${s.total.toLocaleString()}</b> articles</span>
    <span class="stat-chip jp">🇯🇵 JP: <b>${s.jp_total.toLocaleString()}</b></span>
    <span class="stat-chip en">🌐 PubMed: <b>${s.pm_total.toLocaleString()}</b></span>
    <span class="stat-chip total">${s.year_min}–${s.year_max}</span>
    <span class="stat-chip total"><b>${s.categories}</b> categories</span>
    <span class="stat-chip total"><b>${s.journals.toLocaleString()}</b> journals</span>
  `;
}

// ─── Dashboard ───
function renderDashboard(){
  const cats=DB.categories;
  const top20=Object.entries(cats).sort((a,b)=>b[1].total-a[1].total).slice(0,20);
  const maxTotal=Math.max(...top20.map(([,v])=>v.total));

  let barsHtml=top20.map(([cat,v])=>{
    const pcts={
      'jp-kampo':v.kampo/maxTotal*100,
      'jp-acup':v.acupuncture/maxTotal*100,
      'pm-kampo':v.pubmed_kampo/maxTotal*100,
      'pm-acup':v.pubmed_acupuncture/maxTotal*100,
      'pm-pharma':v.pubmed_pharma/maxTotal*100,
    };
    const segs=Object.entries(pcts).filter(([,p])=>p>0).map(([cls,p])=>`<div class="bar-seg ${cls}" style="width:${p}%"></div>`).join('');
    return `<div class="bar-row">
      <div class="bar-label" title="${cat}">${cat}</div>
      <div class="bar-track">${segs}</div>
      <div class="bar-count">${v.total.toLocaleString()}</div>
    </div>`;
  }).join('');

  // Design breakdown
  const designHtml=Object.entries(DB.design).slice(0,8).map(([k,v])=>`<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;"><span>${k}</span><b>${v.toLocaleString()}</b></div>`).join('');

  // Top journals
  const journalHtml=Object.entries(DB.top_journals).slice(0,15).map(([k,v])=>`<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:12px;"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:250px;">${k}</span><b>${v}</b></div>`).join('');

  $('viewDashboard').innerHTML=`
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--kampo)"></div>JP 漢方</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--acup)"></div>JP 鍼灸</div>
      <div class="legend-item"><div class="legend-dot" style="background:rgba(230,126,34,.4)"></div>PubMed 漢方</div>
      <div class="legend-item"><div class="legend-dot" style="background:rgba(52,152,219,.4)"></div>PubMed 鍼灸</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>PubMed 薬学</div>
    </div>
    <div class="section-title">Top 20 Disease Categories <span class="count">(by total articles)</span></div>
    ${barsHtml}
    <div class="dash-grid" style="margin-top:24px;">
      <div class="dash-card"><h3>📋 Study Design (PubMed)</h3>${designHtml}</div>
      <div class="dash-card"><h3>📚 Top Journals</h3>${journalHtml}</div>
    </div>
  `;
}

// ─── Timeline ───
function renderTimeline(){
  const yearly=DB.yearly;
  const years=Object.keys(yearly).filter(y=>parseInt(y)>=1982).sort();
  const sources=['kampo','acupuncture','pubmed_kampo','pubmed_acupuncture','pubmed_pharma'];
  const classes=['s-kampo','s-acup','s-pm-kampo','s-pm-acup','s-pm-pharma'];
  const maxY=Math.max(...years.map(y=>sources.reduce((s,k)=>s+(yearly[y][k]||0),0)));

  let barsHtml=years.map(y=>{
    const vals=sources.map(k=>yearly[y][k]||0);
    const total=vals.reduce((a,b)=>a+b,0);
    const segs=vals.map((v,i)=>v>0?`<div class="seg ${classes[i]}" style="height:${v/maxY*100}%"></div>`:'').join('');
    return `<div class="tl-bar"><div class="tip">${y}: ${total}</div>${segs}</div>`;
  }).join('');

  const axisLabels=years.filter((_,i)=>i%5===0);
  const axisHtml=`<div class="tl-axis">${axisLabels.map(y=>`<span>${y}</span>`).join('')}</div>`;

  $('viewTimeline').innerHTML=`
    <div class="section-title">📈 Publication Timeline <span class="count">(${years[0]}–${years[years.length-1]})</span></div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--kampo)"></div>JP 漢方</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--acup)"></div>JP 鍼灸</div>
      <div class="legend-item"><div class="legend-dot" style="background:rgba(230,126,34,.4)"></div>PM 漢方</div>
      <div class="legend-item"><div class="legend-dot" style="background:rgba(52,152,219,.4)"></div>PM 鍼灸</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>PM 薬学</div>
    </div>
    <div class="dash-card">
      <div class="tl-chart">${barsHtml}</div>
      ${axisHtml}
    </div>
  `;
}

// ─── Categories ───
function renderCategories(){
  const cats=DB.categories;
  const entries=Object.entries(cats).sort((a,b)=>b[1].total-a[1].total);
  const maxT=entries[0][1].total;

  let rows=entries.map(([cat,v])=>{
    const jpTotal=v.kampo+v.acupuncture;
    const pmTotal=v.pubmed_kampo+v.pubmed_acupuncture+v.pubmed_pharma;
    const ratio=jpTotal>0?(pmTotal/jpTotal).toFixed(1)+'x':'—';
    const barW=(v.total/maxT*100).toFixed(1);
    return `<tr onclick="filterArticles('${cat.replace(/'/g,"\\'")}')" style="cursor:pointer;">
      <td><b>${cat}</b></td>
      <td class="num">${v.kampo}</td>
      <td class="num">${v.acupuncture}</td>
      <td class="num">${v.pubmed_kampo}</td>
      <td class="num">${v.pubmed_acupuncture}</td>
      <td class="num">${v.pubmed_pharma}</td>
      <td class="num"><b>${v.total}</b></td>
      <td class="num">${ratio}</td>
      <td><div class="bar-mini" style="width:${barW}%;background:var(--accent);height:12px;border-radius:2px;"></div></td>
    </tr>`;
  }).join('');

  $('viewCategories').innerHTML=`
    <div class="section-title">🏷️ All Categories <span class="count">(${entries.length})</span></div>
    <div style="overflow-x:auto;">
    <table class="cat-table">
      <thead><tr>
        <th>Category</th>
        <th>JP漢方</th><th>JP鍼灸</th>
        <th>PM漢方</th><th>PM鍼灸</th><th>PM薬学</th>
        <th>Total</th><th>PM/JP</th><th style="width:120px;">Bar</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
    </div>
  `;
}

// ─── Articles ───
let currentFilter='';
function filterArticles(cat){
  currentFilter=cat;
  showView('articles');
  renderArticles(DB.articles.filter(a=>a.categories.includes(cat)),cat);
}

function renderArticles(arts,label){
  if(!arts)arts=DB.articles;
  if(!label)label='All';
  const showing=arts.slice(0,200);
  const cards=showing.map(a=>{
    const srcClass='src-'+a.source;
    const srcLabel={kampo:'JP漢方',acupuncture:'JP鍼灸',pubmed_kampo:'PM漢方',pubmed_acupuncture:'PM鍼灸',pubmed_pharma:'PM薬学'}[a.source]||a.source;
    const tags=a.categories.slice(0,5).map(c=>`<span class="art-tag">${c}</span>`).join('');
    const link=a.link?`<a href="${a.link}" target="_blank">${a.title}</a>`:a.title;
    return `<div class="art-card ${srcClass}">
      <div class="art-title">${link}</div>
      <div class="art-meta">${a.authors} — ${a.journal_short||a.journal} (${a.year}) <span class="art-tag src">${srcLabel}</span></div>
      <div class="art-tags">${tags}</div>
    </div>`;
  }).join('');

  $('viewArticles').innerHTML=`
    <div class="section-title">📄 ${label} <span class="count">(${arts.length.toLocaleString()} articles, showing ${showing.length})</span></div>
    <div class="art-list">${cards}</div>
  `;
}

// ─── Search ───
function onSearch(q){
  if(!q||q.length<2){renderArticles();return;}
  q=q.toLowerCase();
  const results=DB.articles.filter(a=>
    a.title.toLowerCase().includes(q)||
    a.authors.toLowerCase().includes(q)||
    a.categories.some(c=>c.toLowerCase().includes(q))
  ).slice(0,200);
  showView('articles');
  renderArticles(results,'Search: "'+q+'"');
}

// ─── Init ───
renderStats();
renderDashboard();
</script>
</body>
</html>"""

# Replace placeholder
html = HTML.replace("__DB_JSON__", db_json)

out_path = os.path.join(BASE_DIR, "evidence_map_integrated.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"Generated: {out_path}")
print(f"Size: {size_mb:.1f} MB")
