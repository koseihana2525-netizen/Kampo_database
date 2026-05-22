# -*- coding: utf-8 -*-
"""
build_html_v3.py - Generate standalone Kampo Evidence Map v3 HTML
3-layer category navigation + author search + formula browser
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "output/kampo_db_v3.json"), "r", encoding="utf-8") as f:
    db = json.load(f)

db_json = json.dumps(db, ensure_ascii=False, separators=(',', ':'))

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kampo Evidence Map v3</title>
<style>
:root {
  --primary: #2c3e50; --accent: #e67e22; --blue: #3498db;
  --green: #27ae60; --red: #e74c3c; --bg: #f7f7f3;
  --card: #fff; --text: #333; --muted: #888;
  --radius: 8px; --shadow: 0 1px 4px rgba(0,0,0,0.06);
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Helvetica Neue','Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }

/* Header */
.header { background:linear-gradient(135deg,#1a2a3a 0%,#2c3e50 100%); color:#fff; padding:20px 28px; }
.header h1 { font-size:22px; font-weight:300; letter-spacing:2px; }
.header h1 b { font-weight:700; }
.header .sub { font-size:12px; opacity:.6; margin-top:2px; }
.stats-bar { display:flex; gap:16px; margin-top:10px; flex-wrap:wrap; }
.stat-chip { background:rgba(255,255,255,.1); padding:4px 12px; border-radius:16px; font-size:12px; }
.stat-chip b { color:var(--accent); }

/* Nav */
.nav-bar { background:#fff; padding:12px 28px; box-shadow:0 2px 8px rgba(0,0,0,.06); position:sticky; top:0; z-index:100; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.nav-tabs { display:flex; gap:4px; flex-wrap:wrap; }
.nav-tab { padding:7px 14px; border-radius:6px; cursor:pointer; font-size:13px; background:#f0f0f0; border:none; transition:all .15s; white-space:nowrap; }
.nav-tab:hover { background:#e0e0e0; }
.nav-tab.active { background:var(--primary); color:#fff; }
.search-wrap { margin-left:auto; position:relative; }
.search-wrap input { padding:8px 14px 8px 32px; border:2px solid #e0e0e0; border-radius:6px; font-size:14px; width:280px; outline:none; transition:border .2s; }
.search-wrap input:focus { border-color:var(--blue); }
.search-wrap::before { content:'\1F50D'; position:absolute; left:8px; top:50%; transform:translateY(-50%); font-size:14px; }

/* Main */
.main { max-width:1200px; margin:0 auto; padding:20px 28px; }
.breadcrumb { font-size:13px; color:var(--muted); margin-bottom:12px; }
.breadcrumb span { cursor:pointer; color:var(--blue); }
.breadcrumb span:hover { text-decoration:underline; }
.section-title { font-size:17px; font-weight:600; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
.section-title .count { font-size:13px; color:var(--muted); font-weight:400; }

/* Category cards (level 1 & 2) */
.cat-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }
.cat-card { background:var(--card); border-radius:var(--radius); padding:16px; box-shadow:var(--shadow); cursor:pointer; transition:all .15s; border-left:4px solid #ccc; }
.cat-card:hover { box-shadow:0 4px 12px rgba(0,0,0,.1); transform:translateY(-1px); }
.cat-card .name { font-size:15px; font-weight:600; }
.cat-card .cnt { font-size:13px; color:var(--muted); margin-top:2px; }
.cat-card .children-preview { margin-top:8px; display:flex; flex-wrap:wrap; gap:4px; }
.cat-card .children-preview span { font-size:11px; background:#f5f5f5; padding:2px 8px; border-radius:10px; }
.lv1-icd { border-left-color:#3498db; }
.lv1-symptom { border-left-color:#27ae60; }
.lv1-kampo { border-left-color:#9b59b6; }
.lv1-other { border-left-color:#95a5a6; }

/* Tag cloud for lv3 */
.tag-cloud { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0; }
.tag-pill { padding:6px 14px; border-radius:20px; font-size:13px; cursor:pointer; border:1px solid #ddd; background:#fff; transition:all .15s; }
.tag-pill:hover { border-color:var(--blue); background:#ebf5fb; }
.tag-pill .cnt { font-size:11px; opacity:.7; margin-left:4px; }

/* Formula cards */
.formula-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; }
.formula-card { background:var(--card); border-radius:var(--radius); padding:16px; box-shadow:var(--shadow); cursor:pointer; transition:all .15s; border-left:4px solid #ccc; }
.formula-card:hover { box-shadow:0 4px 12px rgba(0,0,0,.1); transform:translateY(-1px); }
.formula-card.keipo { border-left-color:var(--red); }
.formula-card.gosei { border-left-color:var(--blue); }
.formula-card .fname { font-size:16px; font-weight:600; }
.formula-card .fmeta { font-size:12px; color:var(--muted); margin-top:2px; }
.formula-card .fmeta .origin-badge { display:inline-block; padding:1px 7px; border-radius:8px; font-size:10px; }
.formula-card .fmeta .origin-badge.keipo { background:#fde8e8; color:#c0392b; }
.formula-card .fmeta .origin-badge.gosei { background:#e8f0fe; color:#2980b9; }
.formula-card .ftags { margin-top:6px; display:flex; flex-wrap:wrap; gap:3px; }
.formula-card .ftags span { font-size:10px; background:#f0f0f0; padding:2px 6px; border-radius:8px; }
.formula-card .fcount { font-size:13px; margin-top:6px; }
.formula-card .fcount b { color:var(--accent); }

/* Article list */
.article-list { margin-top:12px; }
.article-item { background:var(--card); border-radius:var(--radius); padding:14px 18px; margin-bottom:8px; box-shadow:var(--shadow); }
.article-item .atitle { font-size:14px; font-weight:500; }
.article-item .atitle a { color:var(--primary); text-decoration:none; }
.article-item .atitle a:hover { color:var(--blue); text-decoration:underline; }
.article-item .ainfo { font-size:12px; color:var(--muted); margin-top:3px; }
.article-item .atags { margin-top:5px; display:flex; flex-wrap:wrap; gap:3px; }
.article-item .atags .ftag { font-size:11px; background:#fff3e0; color:#e65100; padding:2px 7px; border-radius:8px; }
.article-item .atags .ctag { font-size:11px; background:#e8f5e9; color:#2e7d32; padding:2px 7px; border-radius:8px; }
.article-item .abstract-text { font-size:13px; color:#555; margin-top:6px; line-height:1.6; display:none; }
.article-item.expanded .abstract-text { display:block; }
.toggle-ab { font-size:12px; color:var(--blue); cursor:pointer; margin-top:4px; display:inline-block; }

/* Author list */
.author-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:8px; }
.author-card { background:var(--card); border-radius:var(--radius); padding:10px 14px; box-shadow:var(--shadow); cursor:pointer; transition:all .15s; }
.author-card:hover { background:#ebf5fb; }
.author-card .aname { font-size:14px; font-weight:500; }
.author-card .acnt { font-size:12px; color:var(--muted); }

/* Timeline mini chart */
.timeline-bar { display:flex; align-items:flex-end; gap:1px; height:80px; margin:12px 0; }
.timeline-bar .bar { background:var(--blue); border-radius:2px 2px 0 0; min-width:4px; flex:1; transition:all .15s; position:relative; cursor:pointer; }
.timeline-bar .bar:hover { background:var(--accent); }
.timeline-bar .bar .tip { display:none; position:absolute; bottom:100%; left:50%; transform:translateX(-50%); background:#333; color:#fff; padding:2px 6px; border-radius:4px; font-size:10px; white-space:nowrap; }
.timeline-bar .bar:hover .tip { display:block; }

.result-info { font-size:14px; color:var(--muted); margin-bottom:12px; }
.empty-state { text-align:center; padding:60px 20px; color:var(--muted); }
.empty-state .icon { font-size:40px; margin-bottom:8px; }
.footer { text-align:center; padding:28px; font-size:11px; color:var(--muted); }

@media (max-width:768px) {
  .header { padding:14px 16px; }
  .nav-bar { padding:10px 16px; }
  .main { padding:12px 16px; }
  .search-wrap input { width:180px; }
  .cat-grid,.formula-grid { grid-template-columns:1fr; }
}
</style>
</head>
<body>

<div class="header">
  <h1><b>Kampo</b> Evidence Map</h1>
  <div class="sub">Japanese Journal of Oriental Medicine + Journal of JSAM (1982-2025)</div>
  <div class="stats-bar">
    <span class="stat-chip"><b id="s-total">-</b> articles</span>
    <span class="stat-chip"><b id="s-formula">-</b> formulas</span>
    <span class="stat-chip"><b id="s-cat">-</b> categories</span>
    <span class="stat-chip"><b id="s-abs">-</b> with abstracts</span>
  </div>
</div>

<div class="nav-bar">
  <div class="nav-tabs" id="nav-tabs"></div>
  <div class="search-wrap">
    <input type="text" id="search-input" placeholder="Search formula, disease, author...">
  </div>
</div>

<div class="main" id="main-content"></div>

<div class="footer">
  Kampo Evidence Map v3 &mdash; Data source: J-STAGE / Japanese Journal of Oriental Medicine
</div>

<script>
const DB = %%DB_JSON%%;

const LV1_CLASSES = {'ICD疾患分類':'lv1-icd','症候から探す':'lv1-symptom','漢方医学':'lv1-kampo','その他':'lv1-other'};
const LV1_ICONS = {'ICD疾患分類':'\uD83C\uDFE5','症候から探す':'\uD83E\uDE7A','漢方医学':'\uD83D\uDCDA','その他':'\uD83D\uDD2C'};
let viewStack = [];

// ── Init ──
function init() {
  document.getElementById('s-total').textContent = DB.stats.total.toLocaleString();
  document.getElementById('s-formula').textContent = DB.stats.formulas;
  document.getElementById('s-cat').textContent = DB.stats.categories;
  document.getElementById('s-abs').textContent = DB.stats.withAbstract.toLocaleString();

  // Build nav tabs
  const tabs = document.getElementById('nav-tabs');
  const tabDefs = [
    {id:'home',label:'Home'},
    {id:'categories',label:'Categories'},
    {id:'formulas',label:'Formulas'},
    {id:'authors',label:'Authors'},
    {id:'timeline',label:'Timeline'},
  ];
  tabDefs.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'nav-tab';
    btn.dataset.id = t.id;
    btn.textContent = t.label;
    btn.onclick = () => navigate(t.id);
    tabs.appendChild(btn);
  });

  // Search
  document.getElementById('search-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim();
      if (!q) { navigate('home'); return; }
      doSearch(q);
    }
  });

  navigate('home');
}

function setActiveTab(id) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.id === id));
}

function navigate(view, data) {
  viewStack = [];
  switch(view) {
    case 'home': showHome(); setActiveTab('home'); break;
    case 'categories': showLv1List(); setActiveTab('categories'); break;
    case 'formulas': showFormulaList(); setActiveTab('formulas'); break;
    case 'authors': showAuthorList(); setActiveTab('authors'); break;
    case 'timeline': showTimeline(); setActiveTab('timeline'); break;
  }
}

// ── Home ──
function showHome() {
  const mc = document.getElementById('main-content');
  let h = '';

  // Timeline mini
  h += '<div class="section-title">Publication Timeline</div>';
  h += renderTimeline(true);

  // Category overview
  h += '<div class="section-title" style="margin-top:24px;">Browse by Category</div>';
  h += '<div class="cat-grid">';
  DB.ct.forEach(lv1 => {
    const cls = LV1_CLASSES[lv1.name] || '';
    const icon = LV1_ICONS[lv1.name] || '';
    h += '<div class="cat-card ' + cls + '" onclick="showLv2(\'' + esc(lv1.name) + '\')">';
    h += '<div class="name">' + icon + ' ' + lv1.name + '</div>';
    h += '<div class="cnt">' + lv1.count + ' articles / ' + lv1.children.length + ' subcategories</div>';
    h += '<div class="children-preview">';
    lv1.children.slice(0, 6).forEach(lv2 => {
      h += '<span>' + lv2.name + ' (' + lv2.count + ')</span>';
    });
    if (lv1.children.length > 6) h += '<span>...</span>';
    h += '</div></div>';
  });
  h += '</div>';

  // Top formulas
  h += '<div class="section-title" style="margin-top:24px;">Top 20 Formulas</div>';
  h += '<div class="formula-grid">';
  const topF = Object.entries(DB.fs).slice(0, 20);
  topF.forEach(([fname, info]) => {
    h += renderFormulaCard(fname, info);
  });
  h += '</div>';

  mc.innerHTML = h;
}

// ── Categories ──
function showLv1List() {
  const mc = document.getElementById('main-content');
  let h = '<div class="section-title">All Categories</div>';
  h += '<div class="cat-grid">';
  DB.ct.forEach(lv1 => {
    const cls = LV1_CLASSES[lv1.name] || '';
    const icon = LV1_ICONS[lv1.name] || '';
    h += '<div class="cat-card ' + cls + '" onclick="showLv2(\'' + esc(lv1.name) + '\')">';
    h += '<div class="name">' + icon + ' ' + lv1.name + '</div>';
    h += '<div class="cnt">' + lv1.count + ' articles</div>';
    h += '<div class="children-preview">';
    lv1.children.forEach(lv2 => {
      h += '<span>' + lv2.name + ' (' + lv2.count + ')</span>';
    });
    h += '</div></div>';
  });
  h += '</div>';
  mc.innerHTML = h;
}

function showLv2(lv1Name) {
  const lv1 = DB.ct.find(x => x.name === lv1Name);
  if (!lv1) return;
  const mc = document.getElementById('main-content');
  const icon = LV1_ICONS[lv1Name] || '';
  let h = '<div class="breadcrumb"><span onclick="showLv1List()">Categories</span> &gt; ' + icon + ' ' + lv1Name + '</div>';
  h += '<div class="section-title">' + lv1Name + ' <span class="count">' + lv1.count + ' articles</span></div>';
  h += '<div class="cat-grid">';
  lv1.children.forEach(lv2 => {
    const cls = LV1_CLASSES[lv1Name] || '';
    h += '<div class="cat-card ' + cls + '" onclick="showLv3(\'' + esc(lv1Name) + '\',\'' + esc(lv2.name) + '\')">';
    h += '<div class="name">' + lv2.name + '</div>';
    h += '<div class="cnt">' + lv2.count + ' articles</div>';
    h += '<div class="children-preview">';
    lv2.children.forEach(lv3 => {
      h += '<span>' + lv3.name + ' (' + lv3.count + ')</span>';
    });
    h += '</div></div>';
  });
  h += '</div>';
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

function showLv3(lv1Name, lv2Name) {
  const lv1 = DB.ct.find(x => x.name === lv1Name);
  if (!lv1) return;
  const lv2 = lv1.children.find(x => x.name === lv2Name);
  if (!lv2) return;
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showLv1List()">Categories</span> &gt; <span onclick="showLv2(\'' + esc(lv1Name) + '\')">' + lv1Name + '</span> &gt; ' + lv2Name + '</div>';
  h += '<div class="section-title">' + lv2Name + ' <span class="count">' + lv2.count + ' articles</span></div>';

  // Show lv3 tags
  h += '<div class="tag-cloud">';
  lv2.children.forEach(lv3 => {
    h += '<span class="tag-pill" onclick="showCategoryArticles(\'' + esc(lv3.name) + '\',\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + lv3.name + '<span class="cnt">' + lv3.count + '</span></span>';
  });
  h += '</div>';

  // Collect indices per lv3 and count formulas within this lv2
  const lv3Indices = {};
  const allIndices = new Set();
  lv2.children.forEach(lv3 => {
    const idxs = DB.ci[lv3.name] || [];
    lv3Indices[lv3.name] = new Set(idxs);
    idxs.forEach(i => allIndices.add(i));
  });
  const formulaCounts = {};
  allIndices.forEach(i => {
    DB.articles[i].f.forEach(f => {
      formulaCounts[f] = (formulaCounts[f] || 0) + 1;
    });
  });
  const sortedFormulas = Object.entries(formulaCounts).sort((a, b) => b[1] - a[1]).slice(0, 15);

  // Matrix table: lv3 × top formulas
  if (sortedFormulas.length > 0 && lv2.children.length > 1) {
    h += '<div class="section-title" style="margin-top:20px;">Evidence Matrix</div>';
    h += '<div style="overflow-x:auto;"><table style="border-collapse:collapse;width:100%;font-size:12px;background:#fff;border-radius:8px;box-shadow:var(--shadow);">';
    h += '<thead><tr><th style="padding:8px 12px;text-align:left;border-bottom:2px solid #eee;position:sticky;left:0;background:#fff;min-width:100px;"></th>';
    sortedFormulas.forEach(([fname]) => {
      h += '<th style="padding:8px 6px;text-align:center;border-bottom:2px solid #eee;white-space:nowrap;cursor:pointer;color:var(--blue);" onclick="showFormulaInCategory(\'' + esc(fname) + '\',\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + fname + '</th>';
    });
    h += '</tr></thead><tbody>';
    lv2.children.forEach(lv3 => {
      h += '<tr>';
      h += '<td style="padding:6px 12px;font-weight:500;border-bottom:1px solid #f0f0f0;position:sticky;left:0;background:#fff;cursor:pointer;color:var(--blue);" onclick="showCategoryArticles(\'' + esc(lv3.name) + '\',\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + lv3.name + ' <span style="color:var(--muted);font-weight:400;">(' + lv3.count + ')</span></td>';
      sortedFormulas.forEach(([fname]) => {
        // Count articles in intersection of lv3 and formula
        const fIndices = DB.fi[fname] || [];
        let cnt = 0;
        fIndices.forEach(fi => { if (lv3Indices[lv3.name] && lv3Indices[lv3.name].has(fi)) cnt++; });
        if (cnt > 0) {
          h += '<td style="padding:6px;text-align:center;border-bottom:1px solid #f0f0f0;cursor:pointer;color:var(--primary);font-weight:600;" onclick="showCrossArticles(\'' + esc(fname) + '\',\'' + esc(lv3.name) + '\',\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + cnt + '</td>';
        } else {
          h += '<td style="padding:6px;text-align:center;border-bottom:1px solid #f0f0f0;color:#ddd;">-</td>';
        }
      });
      h += '</tr>';
    });
    h += '</tbody></table></div>';
  }

  // Formula cards with LOCAL counts
  if (sortedFormulas.length > 0) {
    h += '<div class="section-title" style="margin-top:20px;">Top Formulas in ' + lv2Name + '</div>';
    h += '<div class="formula-grid">';
    sortedFormulas.forEach(([fname, cnt]) => {
      const info = DB.fs[fname];
      if (info) h += renderFormulaCardLocal(fname, info, cnt, lv1Name, lv2Name);
    });
    h += '</div>';
  }

  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

// Show articles at intersection of formula × lv3 category
function showCrossArticles(fname, lv3Name, lv1Name, lv2Name) {
  const fIndices = new Set(DB.fi[fname] || []);
  const cIndices = DB.ci[lv3Name] || [];
  const cross = cIndices.filter(i => fIndices.has(i));
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showLv1List()">Categories</span> &gt; <span onclick="showLv2(\'' + esc(lv1Name) + '\')">' + lv1Name + '</span> &gt; <span onclick="showLv3(\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + lv2Name + '</span> &gt; ' + lv3Name + ' × ' + fname + '</div>';
  h += '<div class="section-title">' + lv3Name + ' × ' + fname + ' <span class="count">' + cross.length + ' articles</span></div>';
  h += renderArticleList(cross);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

// Show articles of a formula filtered to a lv2 category
function showFormulaInCategory(fname, lv1Name, lv2Name) {
  const lv1 = DB.ct.find(x => x.name === lv1Name);
  if (!lv1) return;
  const lv2 = lv1.children.find(x => x.name === lv2Name);
  if (!lv2) return;
  const catIndices = new Set();
  lv2.children.forEach(lv3 => { (DB.ci[lv3.name] || []).forEach(i => catIndices.add(i)); });
  const fIndices = DB.fi[fname] || [];
  const cross = fIndices.filter(i => catIndices.has(i));
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showLv1List()">Categories</span> &gt; <span onclick="showLv2(\'' + esc(lv1Name) + '\')">' + lv1Name + '</span> &gt; <span onclick="showLv3(\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + lv2Name + '</span> &gt; ' + fname + '</div>';
  h += '<div class="section-title">' + lv2Name + ' × ' + fname + ' <span class="count">' + cross.length + ' articles</span></div>';
  h += renderArticleList(cross);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

function showCategoryArticles(lv3Name, lv1Name, lv2Name) {
  const indices = DB.ci[lv3Name] || [];
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showLv1List()">Categories</span> &gt; <span onclick="showLv2(\'' + esc(lv1Name) + '\')">' + lv1Name + '</span> &gt; <span onclick="showLv3(\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">' + lv2Name + '</span> &gt; ' + lv3Name + '</div>';
  h += '<div class="section-title">' + lv3Name + ' <span class="count">' + indices.length + ' articles</span></div>';
  h += renderArticleList(indices);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

// ── Formulas ──
function showFormulaList() {
  const mc = document.getElementById('main-content');
  let h = '<div class="section-title">All Formulas <span class="count">' + DB.stats.formulas + '</span></div>';
  h += '<div class="formula-grid">';
  Object.entries(DB.fs).forEach(([fname, info]) => {
    h += renderFormulaCard(fname, info);
  });
  h += '</div>';
  mc.innerHTML = h;
}

function showFormulaDetail(fname) {
  const info = DB.fs[fname];
  const indices = DB.fi[fname] || [];
  if (!info) return;
  const mc = document.getElementById('main-content');
  const originCls = info.o === '経方' ? 'keipo' : 'gosei';
  let h = '<div class="breadcrumb"><span onclick="showFormulaList()">Formulas</span> &gt; ' + fname + '</div>';
  h += '<div class="section-title">' + fname;
  if (info.y) h += ' <span class="count">(' + info.y + ')</span>';
  h += '</div>';
  h += '<div style="margin-bottom:16px;">';
  if (info.num) h += '<span style="font-size:13px;color:var(--muted);">No.' + info.num + '</span> ';
  h += '<span class="origin-badge ' + originCls + '" style="display:inline-block;padding:2px 8px;border-radius:8px;font-size:12px;' + (info.o === '経方' ? 'background:#fde8e8;color:#c0392b' : 'background:#e8f0fe;color:#2980b9') + '">' + (info.o || '不明') + '</span>';
  h += ' <span style="font-size:14px;margin-left:8px;"><b style="color:var(--accent)">' + info.n + '</b> articles</span>';
  h += '</div>';

  // Top categories - clickable to filter
  if (info.top && info.top.length > 0) {
    h += '<div style="margin-bottom:16px;"><b style="font-size:14px;">Related categories:</b> <span style="font-size:12px;color:var(--muted);">(click to filter)</span><div class="tag-cloud" style="margin-top:6px;">';
    info.top.forEach(([cat, cnt]) => {
      h += '<span class="tag-pill" onclick="showFormulaCategoryArticles(\'' + esc(fname) + '\',\'' + esc(cat) + '\')">' + cat + ' <span class="cnt">' + cnt + '</span></span>';
    });
    h += '</div></div>';
  }

  // All categories for this formula (beyond top 5)
  const allCats = {};
  indices.forEach(idx => {
    DB.articles[idx].c.forEach(c => { allCats[c] = (allCats[c] || 0) + 1; });
  });
  const extraCats = Object.entries(allCats).sort((a,b) => b[1]-a[1]).filter(([c]) => !info.top.some(t => t[0]===c));
  if (extraCats.length > 0) {
    h += '<div style="margin-bottom:16px;"><div class="tag-cloud">';
    extraCats.slice(0,15).forEach(([cat, cnt]) => {
      h += '<span class="tag-pill" style="font-size:12px;padding:4px 10px;" onclick="showFormulaCategoryArticles(\'' + esc(fname) + '\',\'' + esc(cat) + '\')">' + cat + ' <span class="cnt">' + cnt + '</span></span>';
    });
    h += '</div></div>';
  }

  h += '<div class="section-title">All Articles <span class="count">' + indices.length + '</span></div>';
  h += renderArticleList(indices);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

// ── Authors ──
function showAuthorList() {
  const mc = document.getElementById('main-content');
  let h = '<div class="section-title">Top Authors <span class="count">' + Object.keys(DB.au).length + '</span></div>';
  h += '<div class="author-grid">';
  Object.entries(DB.au).forEach(([name, indices]) => {
    h += '<div class="author-card" onclick="showAuthorArticles(\'' + esc(name) + '\')">';
    h += '<div class="aname">' + name + '</div>';
    h += '<div class="acnt">' + indices.length + ' articles</div>';
    h += '</div>';
  });
  h += '</div>';
  mc.innerHTML = h;
}

function showAuthorArticles(authorName) {
  const indices = DB.au[authorName] || [];
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showAuthorList()">Authors</span> &gt; ' + authorName + '</div>';
  h += '<div class="section-title">' + authorName + ' <span class="count">' + indices.length + ' articles</span></div>';
  h += renderArticleList(indices);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

// ── Timeline ──
function showTimeline() {
  const mc = document.getElementById('main-content');
  let h = '<div class="section-title">Publication Timeline</div>';
  h += renderTimeline(false);

  // Year clickable list
  h += '<div style="margin-top:20px;">';
  const years = Object.entries(DB.yd).sort((a,b) => b[0].localeCompare(a[0]));
  years.forEach(([y, cnt]) => {
    h += '<div style="display:inline-block;margin:4px;padding:6px 12px;background:#fff;border-radius:6px;cursor:pointer;box-shadow:var(--shadow);font-size:13px;" onclick="showYearArticles(\'' + y + '\')">';
    h += '<b>' + y + '</b> <span style="color:var(--muted);">' + cnt + '</span></div>';
  });
  h += '</div>';
  mc.innerHTML = h;
}

function showYearArticles(year) {
  const indices = [];
  DB.articles.forEach((a, i) => { if (a.y === year) indices.push(i); });
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showTimeline()">Timeline</span> &gt; ' + year + '</div>';
  h += '<div class="section-title">' + year + '年 <span class="count">' + indices.length + ' articles</span></div>';
  h += renderArticleList(indices);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

function renderTimeline(mini) {
  const years = Object.entries(DB.yd).sort((a,b) => a[0].localeCompare(b[0]));
  const maxCnt = Math.max(...years.map(x => x[1]));
  let h = '<div class="timeline-bar" style="' + (mini ? 'height:60px;' : 'height:120px;') + '">';
  years.forEach(([y, cnt]) => {
    const pct = (cnt / maxCnt * 100).toFixed(0);
    h += '<div class="bar" style="height:' + pct + '%;" onclick="showYearArticles(\'' + y + '\')">';
    h += '<span class="tip">' + y + ': ' + cnt + '</span></div>';
  });
  h += '</div>';
  if (!mini) {
    h += '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);">';
    h += '<span>' + years[0][0] + '</span><span>' + years[years.length-1][0] + '</span></div>';
  }
  return h;
}

// ── Search ──
function doSearch(query) {
  setActiveTab('');
  const mc = document.getElementById('main-content');
  const q = query.toLowerCase();

  // 1. Exact formula match
  if (DB.fi[query]) { showFormulaDetail(query); return; }

  // 2. Check author match
  if (DB.au[query]) { showAuthorArticles(query); return; }

  // 3. Full text search
  const scored = [];
  for (let i = 0; i < DB.articles.length; i++) {
    const a = DB.articles[i];
    const text = (a.t + ' ' + a.ab + ' ' + a.a).toLowerCase();
    if (text.includes(q)) {
      let score = 0;
      if (a.t.toLowerCase().includes(q)) score += 3;
      if (a.a.toLowerCase().includes(q)) score += 2;
      if (a.ab.toLowerCase().includes(q)) score += 1;
      if (a.f.length > 0) score += 0.5;
      scored.push({idx: i, score});
    }
  }
  scored.sort((a, b) => b.score - a.score);

  // Also check partial formula/author/category matches
  const formulaMatches = Object.keys(DB.fi).filter(f => f.includes(query));
  const authorMatches = Object.keys(DB.au).filter(a => a.includes(query));
  const categoryMatches = Object.keys(DB.ci).filter(c => c.includes(query));

  let h = '<div class="section-title">Search: "' + escHtml(query) + '"</div>';

  if (formulaMatches.length > 0) {
    h += '<div style="margin-bottom:16px;"><b>Formulas:</b> ';
    formulaMatches.slice(0, 10).forEach(f => {
      h += '<span class="tag-pill" onclick="showFormulaDetail(\'' + esc(f) + '\')" style="margin:2px;">' + f + '</span> ';
    });
    h += '</div>';
  }
  if (authorMatches.length > 0) {
    h += '<div style="margin-bottom:16px;"><b>Authors:</b> ';
    authorMatches.slice(0, 10).forEach(a => {
      h += '<span class="tag-pill" onclick="showAuthorArticles(\'' + esc(a) + '\')" style="margin:2px;">' + a + '</span> ';
    });
    h += '</div>';
  }
  if (categoryMatches.length > 0) {
    h += '<div style="margin-bottom:16px;"><b>Categories:</b> ';
    categoryMatches.slice(0, 10).forEach(c => {
      h += '<span class="tag-pill" style="margin:2px;cursor:default;">' + c + ' (' + (DB.ci[c]||[]).length + ')</span> ';
    });
    h += '</div>';
  }

  h += '<div class="result-info">' + scored.length + ' articles found</div>';
  h += renderArticleList(scored.slice(0, 50).map(s => s.idx));
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

// ── Renderers ──
function renderFormulaCard(fname, info) {
  const originCls = info.o === '経方' ? 'keipo' : 'gosei';
  let h = '<div class="formula-card ' + originCls + '" onclick="showFormulaDetail(\'' + esc(fname) + '\')">';
  h += '<div class="fname">' + fname + '</div>';
  h += '<div class="fmeta">';
  if (info.num) h += 'No.' + info.num + ' ';
  if (info.y) h += info.y + ' ';
  h += '<span class="origin-badge ' + originCls + '">' + (info.o || '') + '</span>';
  h += '</div>';
  if (info.top && info.top.length > 0) {
    h += '<div class="ftags">';
    info.top.slice(0, 3).forEach(([cat]) => { h += '<span>' + cat + '</span>'; });
    h += '</div>';
  }
  h += '<div class="fcount"><b>' + info.n + '</b> articles</div>';
  h += '</div>';
  return h;
}

// Formula card showing LOCAL count within a category
function renderFormulaCardLocal(fname, info, localCount, lv1Name, lv2Name) {
  const originCls = info.o === '経方' ? 'keipo' : 'gosei';
  let h = '<div class="formula-card ' + originCls + '" onclick="showFormulaInCategory(\'' + esc(fname) + '\',\'' + esc(lv1Name) + '\',\'' + esc(lv2Name) + '\')">';
  h += '<div class="fname">' + fname + '</div>';
  h += '<div class="fmeta">';
  if (info.num) h += 'No.' + info.num + ' ';
  if (info.y) h += info.y + ' ';
  h += '<span class="origin-badge ' + originCls + '">' + (info.o || '') + '</span>';
  h += '</div>';
  h += '<div class="fcount"><b style="color:var(--accent);">' + localCount + '</b> articles in this category <span style="color:var(--muted);font-size:11px;">(' + info.n + ' total)</span></div>';
  h += '</div>';
  return h;
}

// Show articles of a formula filtered to a specific lv3 category
function showFormulaCategoryArticles(fname, catName) {
  const fIndices = new Set(DB.fi[fname] || []);
  const cIndices = DB.ci[catName] || [];
  const cross = cIndices.filter(i => fIndices.has(i));
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showFormulaList()">Formulas</span> &gt; <span onclick="showFormulaDetail(\'' + esc(fname) + '\')">' + fname + '</span> &gt; ' + catName + '</div>';
  h += '<div class="section-title">' + fname + ' × ' + catName + ' <span class="count">' + cross.length + ' articles</span></div>';
  h += renderArticleList(cross);
  mc.innerHTML = h;
  window.scrollTo(0, 0);
}

function renderArticleList(indices) {
  if (indices.length === 0) {
    return '<div class="empty-state"><div class="icon">&#x1F4C4;</div><p>No articles found.</p></div>';
  }
  let h = '<div class="article-list">';
  indices.forEach((idx, pos) => {
    const a = DB.articles[idx];
    if (!a) return;
    const cleanTitle = a.t.replace(/<[^>]*>/g, '');
    h += '<div class="article-item" id="art-' + idx + '">';
    h += '<div class="atitle">';
    if (a.l) h += '<a href="' + a.l + '" target="_blank">' + cleanTitle + '</a>';
    else h += cleanTitle;
    h += '</div>';
    const jBadge = a.j === '鍼灸' ? '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:10px;background:#e8f5e9;color:#2e7d32;margin-right:4px;">鍼灸</span>' : '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:10px;background:#e3f2fd;color:#1565c0;margin-right:4px;">漢方</span>';
    h += '<div class="ainfo">' + jBadge + a.y + '年';
    if (a.a) h += ' | ' + a.a;
    h += '</div>';
    h += '<div class="atags">';
    a.f.forEach(f => { h += '<span class="ftag" onclick="event.stopPropagation();showFormulaDetail(\'' + esc(f) + '\')" style="cursor:pointer;">' + f + '</span>'; });
    a.c.slice(0, 3).forEach(c => { h += '<span class="ctag">' + c + '</span>'; });
    h += '</div>';
    if (a.ab) {
      h += '<span class="toggle-ab" onclick="this.parentElement.classList.toggle(\'expanded\');this.textContent=this.parentElement.classList.contains(\'expanded\')?\'▲ Close\':\'▼ Abstract\';">▼ Abstract</span>';
      h += '<div class="abstract-text">' + escHtml(a.ab) + '</div>';
    }
    h += '</div>';
  });
  h += '</div>';
  return h;
}

// ── Utils ──
function esc(s) { return s.replace(/'/g, "\\'").replace(/"/g, '&quot;'); }
function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

init();
</script>
</body>
</html>"""

# Embed DB
html = HTML_TEMPLATE.replace('%%DB_JSON%%', db_json)

out_path = os.path.join(BASE_DIR, "output/kampo_evidence_map_v3.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"HTML saved: {out_path} ({size_mb:.1f} MB)")
