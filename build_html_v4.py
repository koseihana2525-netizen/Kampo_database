# -*- coding: utf-8 -*-
"""
build_html_v4.py - Generate standalone HTML evidence map from integrated_db_v4.json
Outputs index.html for GitHub Pages (~13-15 MB single file).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "integrated_db_v4.json")
OUT_PATH = os.path.join(BASE_DIR, "index.html")

# ── Load DB ──
with open(DB_PATH, "r", encoding="utf-8") as f:
    db = json.load(f)

in_size = os.path.getsize(DB_PATH)
print(f"Input : {DB_PATH} ({in_size/1024/1024:.1f} MB)")
print(f"Articles: {db['stats']['total']}")

db_json = json.dumps(db, ensure_ascii=False, separators=(',', ':'))

# ── HTML Template ──
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日本の東洋医学エビデンスマップ v4</title>
<style>
:root {
  --primary:#2c3e50; --accent:#e67e22; --blue:#3498db;
  --green:#27ae60; --red:#e74c3c; --purple:#8e44ad;
  --bg:#f7f7f3; --card:#fff; --text:#333; --muted:#888;
  --radius:8px; --shadow:0 1px 4px rgba(0,0,0,0.06);
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Helvetica Neue','Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif;background:var(--bg);color:var(--text);line-height:1.5;}

/* Header */
.header{background:linear-gradient(135deg,#1a2a3a 0%,#2c3e50 100%);color:#fff;padding:20px 28px;}
.header h1{font-size:22px;font-weight:300;letter-spacing:2px;}
.header h1 b{font-weight:700;}
.header .sub{font-size:12px;opacity:.6;margin-top:2px;}
.stats-bar{display:flex;gap:12px;margin-top:10px;flex-wrap:wrap;}
.stat-chip{background:rgba(255,255,255,.1);padding:4px 12px;border-radius:16px;font-size:12px;}
.stat-chip b{color:var(--accent);}

/* Nav */
.nav-bar{background:#fff;padding:10px 28px;box-shadow:0 2px 8px rgba(0,0,0,.06);position:sticky;top:0;z-index:100;display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
.nav-tabs{display:flex;gap:3px;flex-wrap:wrap;}
.nav-tab{padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px;background:#f0f0f0;border:none;transition:all .15s;white-space:nowrap;}
.nav-tab:hover{background:#e0e0e0;}
.nav-tab.active{background:var(--primary);color:#fff;}
.search-wrap{margin-left:auto;position:relative;}
.search-wrap input{padding:8px 14px 8px 32px;border:2px solid #e0e0e0;border-radius:6px;font-size:14px;width:260px;outline:none;transition:border .2s;}
.search-wrap input:focus{border-color:var(--blue);}
.search-wrap::before{content:'\1F50D';position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:14px;}

/* Main */
.main{max-width:1200px;margin:0 auto;padding:20px 28px;}
.breadcrumb{font-size:13px;color:var(--muted);margin-bottom:12px;}
.breadcrumb span{cursor:pointer;color:var(--blue);}
.breadcrumb span:hover{text-decoration:underline;}
.section-title{font-size:17px;font-weight:600;margin:18px 0 12px;display:flex;align-items:center;gap:8px;}
.section-title:first-child{margin-top:0;}
.section-title .count{font-size:13px;color:var(--muted);font-weight:400;}

/* Cards grid */
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;}
.cat-card{background:var(--card);border-radius:var(--radius);padding:16px;box-shadow:var(--shadow);cursor:pointer;transition:all .15s;border-left:4px solid #ccc;}
.cat-card:hover{box-shadow:0 4px 12px rgba(0,0,0,.1);transform:translateY(-1px);}
.cat-card .name{font-size:15px;font-weight:600;}
.cat-card .name-en{font-size:12px;color:var(--muted);}
.cat-card .cnt{font-size:13px;color:var(--muted);margin-top:2px;}
.cat-card .children-preview{margin-top:8px;display:flex;flex-wrap:wrap;gap:4px;}
.cat-card .children-preview span{font-size:11px;background:#f5f5f5;padding:2px 8px;border-radius:10px;}
.border-disease{border-left-color:var(--blue);}
.border-symptom{border-left-color:var(--green);}
.border-intervention{border-left-color:var(--purple);}
.border-sd{border-left-color:var(--accent);}
.border-setting{border-left-color:#95a5a6;}

/* Tag cloud */
.tag-cloud{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;}
.tag-pill{padding:6px 14px;border-radius:20px;font-size:13px;cursor:pointer;border:1px solid #ddd;background:#fff;transition:all .15s;}
.tag-pill:hover{border-color:var(--blue);background:#ebf5fb;}
.tag-pill .cnt{font-size:11px;opacity:.7;margin-left:4px;}

/* Tag colors */
.tag-d{font-size:11px;display:inline-block;padding:2px 7px;border-radius:8px;background:#e8f0fe;color:#1a73e8;border:1px solid #c5d9f7;margin:1px;}
.tag-sx{font-size:11px;display:inline-block;padding:2px 7px;border-radius:8px;background:#e8f6ef;color:#1b7d46;border:1px solid #b7e1cd;margin:1px;}
.tag-int{font-size:11px;display:inline-block;padding:2px 7px;border-radius:8px;background:#f0e8fe;color:#7b2cbf;border:1px solid #d4bff0;margin:1px;}
.tag-sd{font-size:11px;display:inline-block;padding:2px 7px;border-radius:8px;background:#fef5e8;color:#b45309;border:1px solid #f5d9a8;margin:1px;}
.tag-set{font-size:11px;display:inline-block;padding:2px 7px;border-radius:8px;background:#f0f0f0;color:#555;border:1px solid #ccc;margin:1px;}
.tag-f{font-size:11px;display:inline-block;padding:2px 7px;border-radius:8px;background:#fff3e0;color:#e65100;border:1px solid #ffcc80;margin:1px;cursor:pointer;}

/* Source badges */
.src-jp{display:inline-block;padding:2px 8px;border-radius:8px;font-size:10px;background:#e8f5e9;color:#2e7d32;font-weight:600;margin-right:4px;}
.src-pm{display:inline-block;padding:2px 8px;border-radius:8px;font-size:10px;background:#e3f2fd;color:#1565c0;font-weight:600;margin-right:4px;}

/* Formula cards */
.formula-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;}
.formula-card{background:var(--card);border-radius:var(--radius);padding:16px;box-shadow:var(--shadow);cursor:pointer;transition:all .15s;border-left:4px solid #ccc;}
.formula-card:hover{box-shadow:0 4px 12px rgba(0,0,0,.1);transform:translateY(-1px);}
.formula-card.keipo{border-left-color:var(--red);}
.formula-card.gosei{border-left-color:var(--blue);}
.formula-card .fname{font-size:16px;font-weight:600;}
.formula-card .fmeta{font-size:12px;color:var(--muted);margin-top:2px;}
.origin-badge{display:inline-block;padding:1px 7px;border-radius:8px;font-size:10px;}
.origin-badge.keipo{background:#fde8e8;color:#c0392b;}
.origin-badge.gosei{background:#e8f0fe;color:#2980b9;}
.formula-card .fcount{font-size:13px;margin-top:6px;}
.formula-card .fcount b{color:var(--accent);}

/* Author */
.author-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;}
.author-card{background:var(--card);border-radius:var(--radius);padding:10px 14px;box-shadow:var(--shadow);cursor:pointer;transition:all .15s;}
.author-card:hover{background:#ebf5fb;}
.author-card .aname{font-size:14px;font-weight:500;}
.author-card .acnt{font-size:12px;color:var(--muted);}

/* Article list */
.article-list{margin-top:12px;}
.article-item{background:var(--card);border-radius:var(--radius);padding:14px 18px;margin-bottom:8px;box-shadow:var(--shadow);}
.article-item .atitle{font-size:14px;font-weight:500;}
.article-item .atitle a{color:var(--primary);text-decoration:none;}
.article-item .atitle a:hover{color:var(--blue);text-decoration:underline;}
.article-item .ameta{font-size:12px;color:var(--muted);margin-top:3px;}
.article-item .atags{margin-top:5px;display:flex;flex-wrap:wrap;gap:3px;}
.article-item .aformula{font-size:12px;margin-top:4px;color:#e65100;}
.toggle-ab{font-size:12px;color:var(--blue);cursor:pointer;margin-top:4px;display:inline-block;}
.abstract-text{font-size:13px;color:#555;margin-top:6px;line-height:1.6;display:none;white-space:pre-wrap;word-break:break-word;}
.article-item.expanded .abstract-text{display:block;}

/* Timeline */
.timeline-chart{display:flex;align-items:flex-end;gap:1px;margin:12px 0;}
.timeline-chart .bar-group{flex:1;display:flex;flex-direction:column;align-items:stretch;cursor:pointer;position:relative;min-width:3px;}
.timeline-chart .bar-jp{background:var(--green);border-radius:2px 2px 0 0;}
.timeline-chart .bar-pm{background:var(--blue);}
.timeline-chart .bar-group:hover .bar-jp{opacity:.8;}
.timeline-chart .bar-group:hover .bar-pm{opacity:.8;}
.timeline-chart .bar-group .tip{display:none;position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;white-space:nowrap;z-index:10;}
.timeline-chart .bar-group:hover .tip{display:block;}

/* Bar chart (CSS) */
.bar-chart{margin:12px 0;}
.bar-row{display:flex;align-items:center;margin-bottom:6px;}
.bar-label{width:180px;font-size:13px;text-align:right;padding-right:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;}
.bar-track{flex:1;display:flex;gap:1px;height:22px;align-items:stretch;}
.bar-seg-jp{background:var(--green);border-radius:3px 0 0 3px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;min-width:0;}
.bar-seg-pm{background:var(--blue);border-radius:0 3px 3px 0;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;min-width:0;}
.bar-total{font-size:12px;color:var(--muted);margin-left:6px;white-space:nowrap;}

/* Source filter */
.source-filter{display:flex;gap:6px;margin-bottom:12px;}
.source-filter button{padding:5px 14px;border-radius:16px;border:1px solid #ddd;background:#fff;cursor:pointer;font-size:12px;transition:all .15s;}
.source-filter button.active{background:var(--primary);color:#fff;border-color:var(--primary);}
.source-filter button:hover{border-color:var(--blue);}

/* Sort controls */
.sort-bar{display:flex;gap:6px;margin-bottom:12px;align-items:center;font-size:13px;color:var(--muted);}
.sort-bar button{padding:4px 12px;border-radius:12px;border:1px solid #ddd;background:#fff;cursor:pointer;font-size:12px;}
.sort-bar button.active{background:var(--accent);color:#fff;border-color:var(--accent);}

.load-more{display:block;margin:16px auto;padding:10px 32px;border:2px solid var(--blue);background:#fff;color:var(--blue);border-radius:8px;font-size:14px;cursor:pointer;transition:all .15s;}
.load-more:hover{background:var(--blue);color:#fff;}

.result-info{font-size:14px;color:var(--muted);margin-bottom:12px;}
.empty-state{text-align:center;padding:60px 20px;color:var(--muted);}
.empty-state .icon{font-size:40px;margin-bottom:8px;}

/* Overview cards */
.overview-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:24px;}
.overview-card{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);text-align:center;}
.overview-card .ov-num{font-size:28px;font-weight:700;color:var(--primary);}
.overview-card .ov-label{font-size:13px;color:var(--muted);margin-top:4px;}

/* Legend */
.legend{display:flex;gap:16px;margin:8px 0;font-size:12px;color:var(--muted);align-items:center;}
.legend-dot{width:12px;height:12px;border-radius:3px;display:inline-block;margin-right:4px;vertical-align:middle;}

.footer{text-align:center;padding:28px;font-size:11px;color:var(--muted);}

/* Inst filter */
.inst-filter{margin-bottom:12px;}
.inst-filter select{padding:6px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px;max-width:300px;}

@media (max-width:768px){
  .header{padding:14px 16px;}
  .nav-bar{padding:8px 12px;}
  .main{padding:12px 16px;}
  .search-wrap input{width:160px;font-size:12px;}
  .cat-grid,.formula-grid{grid-template-columns:1fr;}
  .bar-label{width:120px;font-size:11px;}
  .overview-grid{grid-template-columns:repeat(2,1fr);}
}
</style>
</head>
<body>

<div class="header">
  <h1><b>日本の東洋医学</b>エビデンスマップ v4</h1>
  <div class="sub">Japanese Traditional Medicine Evidence Map &mdash; 11,846 articles from J-STAGE + PubMed</div>
  <div class="stats-bar" id="stats-bar"></div>
</div>

<div class="nav-bar">
  <div class="nav-tabs" id="nav-tabs"></div>
  <div class="search-wrap">
    <input type="text" id="search-input" placeholder="タイトル・著者・抄録を検索...">
  </div>
</div>

<div class="main" id="main-content"></div>

<div class="footer">
  日本の東洋医学エビデンスマップ v4 &mdash; Data: J-STAGE + PubMed &mdash; Generated with Python
</div>

<script>
const DB = %%DB_JSON%%;

/* ── Axis display config ── */
const AXIS_META = {
  disease:       {icon:'\uD83C\uDFE5', label:'疾患', labelEn:'Disease', borderCls:'border-disease', tagCls:'tag-d'},
  symptom:       {icon:'\uD83E\uDE7A', label:'症候', labelEn:'Symptom', borderCls:'border-symptom', tagCls:'tag-sx'},
  intervention:  {icon:'\uD83D\uDC89', label:'介入', labelEn:'Intervention', borderCls:'border-intervention', tagCls:'tag-int'},
  study_design:  {icon:'\uD83D\uDCCA', label:'研究デザイン', labelEn:'Study Design', borderCls:'border-sd', tagCls:'tag-sd'},
  setting:       {icon:'\u2699\uFE0F', label:'セッティング', labelEn:'Setting', borderCls:'border-setting', tagCls:'tag-set'}
};
const TAG_CLS_MAP = {};
Object.entries(AXIS_META).forEach(([ax, m]) => {
  (DB.axis_chapters[ax]||[]).forEach(ch => {
    ch.leaves.forEach(leafId => { TAG_CLS_MAP[leafId] = m.tagCls; });
  });
});

/* ── Tab definitions ── */
const TABS = [
  {id:'home',   label:'\uD83C\uDFE0 ホーム'},
  {id:'disease',label:'\uD83C\uDFE5 疾患'},
  {id:'symptom',label:'\uD83E\uDE7A 症候'},
  {id:'sd',     label:'\uD83D\uDCCA 研究デザイン'},
  {id:'formula',label:'\uD83D\uDC8A 方剤'},
  {id:'author', label:'\uD83D\uDC64 著者'},
  {id:'timeline',label:'\uD83D\uDCC8 タイムライン'}
];

let currentTab = 'home';
let currentSourceFilter = 'all'; // all | jp | pm
let japanOnly = false; // default: show all (China/Korea already removed at DB level)

/* ── Japan-only filter ── */
function isVisible(art) {
  if (!japanOnly) return true;
  if (art.s === 'jp') return true; // J-STAGE is always Japan
  return !art.fgn; // PubMed: exclude foreign-affiliated
}
function filterIndices(indices) {
  if (!japanOnly) return indices;
  return indices.filter(i => isVisible(DB.articles[i]));
}
function toggleJapanOnly() {
  japanOnly = !japanOnly;
  const btn = document.getElementById('japan-toggle');
  if (btn) {
    btn.classList.toggle('active', japanOnly);
    btn.style.cssText = japanOnly ? 'background:#27ae60;color:#fff;margin-left:8px;' : 'background:#e0e0e0;margin-left:8px;';
    btn.textContent = japanOnly ? '\uD83C\uDDEF\uD83C\uDDF5 Japan Only' : '\uD83C\uDF0D All Countries';
  }
  showTab(currentTab); // re-render current tab
}

/* ── Init ── */
function init() {
  // Stats bar
  const s = DB.stats;
  const sb = document.getElementById('stats-bar');
  sb.innerHTML =
    chip('Total', s.total) +
    chip('\uD83C\uDDEF\uD83C\uDDF5 J-STAGE', s.jp) +
    chip('\uD83D\uDD2C PubMed', s.pm) +
    chip('\uD83D\uDC8A 方剤', Object.keys(DB.formulas).length) +
    chip('\uD83C\uDFF7 カテゴリ', Object.keys(DB.axes).length) +
    chip('\uD83D\uDCC5 ' + s.year_range[0] + '-' + s.year_range[1], '');

  // Nav tabs
  const nt = document.getElementById('nav-tabs');
  TABS.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'nav-tab';
    btn.dataset.id = t.id;
    btn.textContent = t.label;
    btn.onclick = () => showTab(t.id);
    nt.appendChild(btn);
  });
  // Japan-only toggle button
  const jtBtn = document.createElement('button');
  jtBtn.id = 'japan-toggle';
  jtBtn.className = 'nav-tab';
  jtBtn.style.cssText = 'background:#e0e0e0;margin-left:8px;';
  jtBtn.textContent = '\uD83C\uDF0D All Countries';
  jtBtn.onclick = toggleJapanOnly;
  nt.appendChild(jtBtn);

  // Search
  document.getElementById('search-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim();
      if (!q) { showTab('home'); return; }
      doSearch(q);
    }
  });

  showTab('home');
}

function chip(label, val) {
  if (val === '') return '<span class="stat-chip">' + label + '</span>';
  return '<span class="stat-chip"><b>' + (typeof val==='number'?val.toLocaleString():val) + '</b> ' + label + '</span>';
}

function setActiveTab(id) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.id === id));
}

function showTab(tabId) {
  currentTab = tabId;
  setActiveTab(tabId);
  const mc = document.getElementById('main-content');
  switch(tabId) {
    case 'home': renderHome(mc); break;
    case 'disease': renderAxisChapters(mc, 'disease'); break;
    case 'symptom': renderAxisChapters(mc, 'symptom'); break;
    case 'sd': renderStudyDesign(mc); break;
    case 'formula': renderFormulas(mc); break;
    case 'author': renderAuthors(mc); break;
    case 'timeline': renderTimeline(mc); break;
  }
  window.scrollTo(0,0);
}

/* ── Utility ── */
function esc(s) { return s.replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/"/g,'&quot;'); }
function escHtml(s) { if(!s)return''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function tagJa(tagId) { const ax=DB.axes[tagId]; return ax?ax.ja:tagId; }
function tagEn(tagId) { const ax=DB.axes[tagId]; return ax?ax.en:''; }
function tagLabel(tagId) { const ax=DB.axes[tagId]; if(!ax) return tagId; return ax.ja + (ax.en?' / '+ax.en:''); }
function tagCls(tagId) { return TAG_CLS_MAP[tagId] || 'tag-set'; }

/* Count articles for a tag, respecting japanOnly filter */
function tagCount(tagId) {
  return filterIndices(DB.ai[tagId]||[]).length;
}

/* Get indices for a tag, applying source + japanOnly filter */
function getFilteredIndices(indices, srcFilter) {
  let result = filterIndices(indices);
  if (srcFilter && srcFilter !== 'all') {
    result = result.filter(i => DB.articles[i].s === srcFilter);
  }
  return result;
}

/* ── HOME TAB ── */
function renderHome(mc) {
  let h = '';

  // Compute visible stats
  let visTotal=0, visJp=0, visPm=0;
  DB.articles.forEach(a => { if(isVisible(a)){visTotal++;if(a.s==='jp')visJp++;else visPm++;} });

  // Overview cards
  h += '<div class="overview-grid">';
  h += '<div class="overview-card"><div class="ov-num">' + visTotal.toLocaleString() + '</div><div class="ov-label">Total Articles</div></div>';
  h += '<div class="overview-card"><div class="ov-num" style="color:var(--green)">' + visJp.toLocaleString() + '</div><div class="ov-label">\uD83C\uDDEF\uD83C\uDDF5 J-STAGE</div></div>';
  h += '<div class="overview-card"><div class="ov-num" style="color:var(--blue)">' + visPm.toLocaleString() + '</div><div class="ov-label">\uD83D\uDD2C PubMed</div></div>';
  h += '<div class="overview-card"><div class="ov-num" style="color:var(--accent)">' + Object.keys(DB.formulas).length + '</div><div class="ov-label">\uD83D\uDC8A Formulas</div></div>';
  h += '</div>';

  // Top 10 diseases bar chart
  h += '<div class="section-title">\uD83C\uDFE5 Top 10 疾患カテゴリ</div>';
  h += '<div class="legend"><span class="legend-dot" style="background:var(--green)"></span>J-STAGE <span class="legend-dot" style="background:var(--blue);margin-left:8px"></span>PubMed</div>';
  const dChapters = DB.axis_chapters.disease || [];
  const dLeafCounts = [];
  dChapters.forEach(ch => {
    ch.leaves.forEach(lid => {
      const idxs = filterIndices(DB.ai[lid]||[]);
      let jp=0,pm=0;
      idxs.forEach(i => { if(DB.articles[i].s==='jp') jp++; else pm++; });
      dLeafCounts.push({id:lid, ja:tagJa(lid), en:tagEn(lid), total:idxs.length, jp, pm});
    });
  });
  dLeafCounts.sort((a,b) => b.total - a.total);
  const top10D = dLeafCounts.slice(0,10);
  const maxD = top10D.length ? top10D[0].total : 1;
  h += '<div class="bar-chart">';
  top10D.forEach(d => {
    const jpW = (d.jp/maxD*100).toFixed(1);
    const pmW = (d.pm/maxD*100).toFixed(1);
    h += '<div class="bar-row" style="cursor:pointer" onclick="showTagArticles(\'' + d.id + '\')">';
    h += '<div class="bar-label" title="' + d.en + '">' + d.ja + '</div>';
    h += '<div class="bar-track">';
    if(d.jp>0) h += '<div class="bar-seg-jp" style="width:' + jpW + '%">' + (d.jp>30?d.jp:'') + '</div>';
    if(d.pm>0) h += '<div class="bar-seg-pm" style="width:' + pmW + '%">' + (d.pm>30?d.pm:'') + '</div>';
    h += '</div><div class="bar-total">' + d.total + '</div></div>';
  });
  h += '</div>';

  // Top 5 study designs
  h += '<div class="section-title">\uD83D\uDCCA Top 研究デザイン</div>';
  const sdCh = (DB.axis_chapters.study_design||[]);
  const sdLeaves = [];
  sdCh.forEach(ch => ch.leaves.forEach(lid => {
    sdLeaves.push({id:lid, ja:tagJa(lid), total:filterIndices(DB.ai[lid]||[]).length});
  }));
  sdLeaves.sort((a,b)=>b.total-a.total);
  const maxSD = sdLeaves.length ? sdLeaves[0].total : 1;
  h += '<div class="bar-chart">';
  sdLeaves.slice(0,8).forEach(d => {
    const w = (d.total/maxSD*100).toFixed(1);
    h += '<div class="bar-row" style="cursor:pointer" onclick="showTagArticles(\'' + d.id + '\')">';
    h += '<div class="bar-label">' + d.ja + '</div>';
    h += '<div class="bar-track"><div class="bar-seg-pm" style="width:' + w + '%;border-radius:3px;">' + (d.total>30?d.total:'') + '</div></div>';
    h += '<div class="bar-total">' + d.total + '</div></div>';
  });
  h += '</div>';

  // Mini timeline
  h += '<div class="section-title">\uD83D\uDCC8 年次推移</div>';
  h += '<div class="legend"><span class="legend-dot" style="background:var(--green)"></span>J-STAGE <span class="legend-dot" style="background:var(--blue);margin-left:8px"></span>PubMed</div>';
  h += renderTimelineChart(80, true);

  mc.innerHTML = h;
}

/* ── AXIS CHAPTERS (Disease / Symptom tabs) ── */
function renderAxisChapters(mc, axisType) {
  const meta = AXIS_META[axisType];
  const chapters = DB.axis_chapters[axisType] || [];
  let h = '<div class="section-title">' + meta.icon + ' ' + meta.label + ' / ' + meta.labelEn + '</div>';
  h += '<div class="cat-grid">';
  chapters.forEach(ch => {
    let total = 0;
    ch.leaves.forEach(lid => { total += filterIndices(DB.ai[lid]||[]).length; });
    h += '<div class="cat-card ' + meta.borderCls + '" onclick="showChapterLeaves(\'' + axisType + '\',\'' + esc(ch.id) + '\')">';
    h += '<div class="name">' + ch.ja + '</div>';
    h += '<div class="name-en">' + ch.en + '</div>';
    h += '<div class="cnt">' + total + ' articles / ' + ch.leaves.length + ' tags</div>';
    h += '<div class="children-preview">';
    ch.leaves.slice(0,6).forEach(lid => {
      h += '<span>' + tagJa(lid) + ' (' + filterIndices(DB.ai[lid]||[]).length + ')</span>';
    });
    if (ch.leaves.length > 6) h += '<span>...</span>';
    h += '</div></div>';
  });
  h += '</div>';
  mc.innerHTML = h;
}

function showChapterLeaves(axisType, chId) {
  const meta = AXIS_META[axisType];
  const chapters = DB.axis_chapters[axisType] || [];
  const ch = chapters.find(c => c.id === chId);
  if (!ch) return;
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showTab(\'' + axisType + '\')">' + meta.icon + ' ' + meta.label + '</span> &gt; ' + ch.ja + ' / ' + ch.en + '</div>';
  h += '<div class="section-title">' + ch.ja + ' <span class="count">' + ch.en + '</span></div>';
  h += '<div class="tag-cloud">';
  const sorted = ch.leaves.map(lid => ({id:lid, ja:tagJa(lid), en:tagEn(lid), cnt:filterIndices(DB.ai[lid]||[]).length}))
    .sort((a,b) => b.cnt - a.cnt);
  sorted.forEach(t => {
    h += '<span class="tag-pill" onclick="showTagArticles(\'' + t.id + '\')">' + t.ja + ' / ' + t.en + '<span class="cnt">' + t.cnt + '</span></span>';
  });
  h += '</div>';
  mc.innerHTML = h;
  window.scrollTo(0,0);
}

function showTagArticles(tagId) {
  const indices = filterIndices(DB.ai[tagId] || []);
  const mc = document.getElementById('main-content');
  const ax = DB.axes[tagId];
  const label = ax ? ax.ja + ' / ' + ax.en : tagId;
  // Find which axis/chapter this tag belongs to
  let parentAxis = null, parentCh = null;
  for (const [axType, chs] of Object.entries(DB.axis_chapters)) {
    for (const ch of chs) {
      if (ch.leaves.includes(tagId)) { parentAxis = axType; parentCh = ch; break; }
    }
    if (parentAxis) break;
  }
  let h = '<div class="breadcrumb">';
  if (parentAxis) {
    const m = AXIS_META[parentAxis];
    h += '<span onclick="showTab(\'' + parentAxis + '\')">' + m.icon + ' ' + m.label + '</span> &gt; ';
    if (parentCh) h += '<span onclick="showChapterLeaves(\'' + parentAxis + '\',\'' + esc(parentCh.id) + '\')">' + parentCh.ja + '</span> &gt; ';
  }
  h += label + '</div>';
  h += '<div class="section-title">' + label + ' <span class="count">' + indices.length + ' articles</span></div>';
  h += renderSourceFilter('showTagArticlesFiltered', "'" + esc(tagId) + "'");
  h += '<div id="article-container"></div>';
  mc.innerHTML = h;
  renderArticlesInto(indices, document.getElementById('article-container'));
  window.scrollTo(0,0);
}

function showTagArticlesFiltered(tagId, src) {
  currentSourceFilter = src;
  const indices = getFilteredIndices(DB.ai[tagId]||[], src);
  document.querySelectorAll('.source-filter button').forEach(b => b.classList.toggle('active', b.dataset.src === src));
  renderArticlesInto(indices, document.getElementById('article-container'));
}

/* ── STUDY DESIGN TAB ── */
function renderStudyDesign(mc) {
  const meta = AXIS_META.study_design;
  const chapters = DB.axis_chapters.study_design || [];
  let allLeaves = [];
  chapters.forEach(ch => ch.leaves.forEach(lid => {
    allLeaves.push({id:lid, ja:tagJa(lid), en:tagEn(lid), cnt:(DB.ai[lid]||[]).length});
  }));
  allLeaves.sort((a,b) => b.cnt - a.cnt);

  let h = '<div class="section-title">' + meta.icon + ' ' + meta.label + ' / ' + meta.labelEn + '</div>';
  h += '<div class="cat-grid">';
  allLeaves.forEach(sd => {
    h += '<div class="cat-card border-sd" onclick="showTagArticles(\'' + sd.id + '\')">';
    h += '<div class="name">' + sd.ja + '</div>';
    h += '<div class="name-en">' + sd.en + '</div>';
    h += '<div class="cnt" style="font-size:20px;font-weight:700;color:var(--accent);margin:8px 0;">' + sd.cnt + '</div>';
    // mini disease breakdown
    const sdIdxs = new Set(DB.ai[sd.id]||[]);
    const dCounts = [];
    (DB.axis_chapters.disease||[]).forEach(ch => {
      ch.leaves.forEach(lid => {
        const cross = (DB.ai[lid]||[]).filter(i => sdIdxs.has(i)).length;
        if (cross > 0) dCounts.push({ja:tagJa(lid), cnt:cross});
      });
    });
    dCounts.sort((a,b)=>b.cnt-a.cnt);
    if (dCounts.length > 0) {
      h += '<div class="children-preview">';
      dCounts.slice(0,5).forEach(d => { h += '<span>' + d.ja + ' ' + d.cnt + '</span>'; });
      if (dCounts.length > 5) h += '<span>...</span>';
      h += '</div>';
    }
    h += '</div>';
  });
  h += '</div>';
  mc.innerHTML = h;
}

/* ── FORMULA TAB ── */
let formulaSort = 'count';
function renderFormulas(mc) {
  let entries = Object.entries(DB.formulas);
  if (formulaSort === 'count') entries.sort((a,b) => b[1].count - a[1].count);
  else if (formulaSort === 'num') entries.sort((a,b) => (a[1].num||999) - (b[1].num||999));
  else entries.sort((a,b) => a[0].localeCompare(b[0],'ja'));

  let h = '<div class="section-title">\uD83D\uDC8A 方剤 / Formulas <span class="count">' + entries.length + '</span></div>';
  h += '<div class="sort-bar">Sort: ';
  h += '<button class="' + (formulaSort==='count'?'active':'') + '" onclick="formulaSort=\'count\';renderFormulas(document.getElementById(\'main-content\'))">件数順</button>';
  h += '<button class="' + (formulaSort==='num'?'active':'') + '" onclick="formulaSort=\'num\';renderFormulas(document.getElementById(\'main-content\'))">TJ番号順</button>';
  h += '<button class="' + (formulaSort==='name'?'active':'') + '" onclick="formulaSort=\'name\';renderFormulas(document.getElementById(\'main-content\'))">名前順</button>';
  h += '</div>';
  h += '<div class="formula-grid">';
  entries.forEach(([fname, info]) => {
    h += renderFormulaCard(fname, info);
  });
  h += '</div>';
  mc.innerHTML = h;
}

function renderFormulaCard(fname, info) {
  const originCls = info.origin === '経方' ? 'keipo' : 'gosei';
  let h = '<div class="formula-card ' + originCls + '" onclick="showFormulaDetail(\'' + esc(fname) + '\')">';
  h += '<div class="fname">' + escHtml(fname) + '</div>';
  h += '<div class="fmeta">';
  if (info.num) h += 'TJ-' + info.num + ' ';
  h += '<span class="origin-badge ' + originCls + '">' + (info.origin || '不明') + '</span>';
  h += '</div>';
  h += '<div class="fcount"><b>' + info.count + '</b> articles</div>';
  h += '</div>';
  return h;
}

function showFormulaDetail(fname) {
  const info = DB.formulas[fname];
  const indices = DB.fi[fname] || [];
  if (!info && !indices.length) return;
  const mc = document.getElementById('main-content');
  const originCls = (info && info.origin === '経方') ? 'keipo' : 'gosei';
  let h = '<div class="breadcrumb"><span onclick="showTab(\'formula\')">\uD83D\uDC8A 方剤</span> &gt; ' + escHtml(fname) + '</div>';
  h += '<div class="section-title">' + escHtml(fname) + '</div>';
  h += '<div style="margin-bottom:16px;">';
  if (info) {
    if (info.num) h += '<span style="font-size:13px;color:var(--muted);">TJ-' + info.num + '</span> ';
    h += '<span class="origin-badge ' + originCls + '">' + (info.origin || '') + '</span> ';
  }
  h += '<span style="font-size:14px;margin-left:8px;"><b style="color:var(--accent)">' + indices.length + '</b> articles</span>';
  h += '</div>';

  // Disease breakdown for this formula
  const tagCounts = {};
  indices.forEach(i => {
    const a = DB.articles[i];
    (a.d||[]).forEach(t => { tagCounts[t] = (tagCounts[t]||0)+1; });
    (a.sx||[]).forEach(t => { tagCounts[t] = (tagCounts[t]||0)+1; });
  });
  const sortedTags = Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]);
  if (sortedTags.length > 0) {
    h += '<div style="margin-bottom:16px;"><b>Related tags:</b><div class="tag-cloud" style="margin-top:6px;">';
    sortedTags.slice(0,15).forEach(([tid, cnt]) => {
      h += '<span class="tag-pill" onclick="showFormulaCrossArticles(\'' + esc(fname) + '\',\'' + esc(tid) + '\')">';
      h += '<span class="' + tagCls(tid) + '" style="border:none;background:none;padding:0;">' + tagJa(tid) + '</span>';
      h += '<span class="cnt">' + cnt + '</span></span>';
    });
    h += '</div></div>';
  }

  h += renderSourceFilter('showFormulaDetailFiltered', "'" + esc(fname) + "'");
  h += '<div id="article-container"></div>';
  mc.innerHTML = h;
  renderArticlesInto(indices, document.getElementById('article-container'));
  window.scrollTo(0,0);
}

function showFormulaDetailFiltered(fname, src) {
  currentSourceFilter = src;
  const indices = getFilteredIndices(DB.fi[fname]||[], src);
  document.querySelectorAll('.source-filter button').forEach(b => b.classList.toggle('active', b.dataset.src === src));
  renderArticlesInto(indices, document.getElementById('article-container'));
}

function showFormulaCrossArticles(fname, tagId) {
  const fSet = new Set(DB.fi[fname]||[]);
  const tIdxs = DB.ai[tagId]||[];
  const cross = tIdxs.filter(i => fSet.has(i));
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showTab(\'formula\')">\uD83D\uDC8A 方剤</span> &gt; <span onclick="showFormulaDetail(\'' + esc(fname) + '\')">' + escHtml(fname) + '</span> &gt; ' + tagJa(tagId) + '</div>';
  h += '<div class="section-title">' + escHtml(fname) + ' \u00D7 ' + tagJa(tagId) + ' <span class="count">' + cross.length + ' articles</span></div>';
  h += '<div id="article-container"></div>';
  mc.innerHTML = h;
  renderArticlesInto(cross, document.getElementById('article-container'));
  window.scrollTo(0,0);
}

/* ── AUTHOR TAB ── */
function renderAuthors(mc) {
  let h = '<div class="section-title">\uD83D\uDC64 著者 / Authors</div>';

  // Search
  h += '<div style="margin-bottom:16px;"><input type="text" id="author-search" placeholder="著者名を検索 / Search author..." style="padding:8px 14px;border:2px solid #e0e0e0;border-radius:6px;font-size:14px;width:100%;max-width:400px;outline:none;" oninput="filterAuthors(this.value)"></div>';

  // Institution filter
  h += '<div class="inst-filter"><select id="inst-select" onchange="filterByInst(this.value)"><option value="">All institutions</option>';
  const instSorted = Object.entries(DB.inst).sort((a,b)=>b[1].length-a[1].length);
  instSorted.forEach(([name, idxs]) => {
    h += '<option value="' + escHtml(name) + '">' + escHtml(name) + ' (' + idxs.length + ')</option>';
  });
  h += '</select></div>';

  // Top 20
  h += '<div id="author-list"></div>';
  mc.innerHTML = h;
  showTopAuthors();
}

function showTopAuthors() {
  const sorted = Object.entries(DB.au).sort((a,b) => b[1].length - a[1].length).slice(0,20);
  let h = '<div class="section-title">Top 20 著者</div>';
  h += '<div class="author-grid">';
  sorted.forEach(([name, idxs]) => {
    h += '<div class="author-card" onclick="showAuthorArticles(\'' + esc(name) + '\')">';
    h += '<div class="aname">' + escHtml(name) + '</div>';
    h += '<div class="acnt">' + idxs.length + ' articles</div></div>';
  });
  h += '</div>';
  document.getElementById('author-list').innerHTML = h;
}

function filterAuthors(q) {
  if (!q || q.length < 2) { showTopAuthors(); return; }
  const ql = q.toLowerCase();
  const matches = Object.entries(DB.au).filter(([name]) => name.toLowerCase().includes(ql) || name.includes(q))
    .sort((a,b) => b[1].length - a[1].length).slice(0,30);
  let h = '<div class="result-info">' + matches.length + ' authors found</div>';
  h += '<div class="author-grid">';
  matches.forEach(([name, idxs]) => {
    h += '<div class="author-card" onclick="showAuthorArticles(\'' + esc(name) + '\')">';
    h += '<div class="aname">' + escHtml(name) + '</div>';
    h += '<div class="acnt">' + idxs.length + ' articles</div></div>';
  });
  h += '</div>';
  document.getElementById('author-list').innerHTML = h;
}

function filterByInst(instName) {
  if (!instName) { showTopAuthors(); return; }
  const instIdxs = new Set(DB.inst[instName]||[]);
  // find authors who have articles in this institution
  const authorCounts = {};
  instIdxs.forEach(i => {
    const a = DB.articles[i];
    if (a.a) {
      a.a.split(/[,、]\s*/).forEach(name => {
        name = name.trim();
        if (name && DB.au[name]) authorCounts[name] = (authorCounts[name]||0) + 1;
      });
    }
  });
  const sorted = Object.entries(authorCounts).sort((a,b)=>b[1]-a[1]).slice(0,30);
  let h = '<div class="section-title">' + escHtml(instName) + ' <span class="count">' + instIdxs.size + ' articles</span></div>';
  h += '<div class="author-grid">';
  sorted.forEach(([name, cnt]) => {
    h += '<div class="author-card" onclick="showAuthorArticles(\'' + esc(name) + '\')">';
    h += '<div class="aname">' + escHtml(name) + '</div>';
    h += '<div class="acnt">' + cnt + ' articles (inst)</div></div>';
  });
  h += '</div>';
  document.getElementById('author-list').innerHTML = h;
}

function showAuthorArticles(authorName) {
  const indices = DB.au[authorName] || [];
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showTab(\'author\')">\uD83D\uDC64 著者</span> &gt; ' + escHtml(authorName) + '</div>';
  h += '<div class="section-title">' + escHtml(authorName) + ' <span class="count">' + indices.length + ' articles</span></div>';
  h += renderSourceFilter('showAuthorArticlesFiltered', "'" + esc(authorName) + "'");
  h += '<div id="article-container"></div>';
  mc.innerHTML = h;
  renderArticlesInto(indices, document.getElementById('article-container'));
  window.scrollTo(0,0);
}

function showAuthorArticlesFiltered(authorName, src) {
  currentSourceFilter = src;
  const indices = getFilteredIndices(DB.au[authorName]||[], src);
  document.querySelectorAll('.source-filter button').forEach(b => b.classList.toggle('active', b.dataset.src === src));
  renderArticlesInto(indices, document.getElementById('article-container'));
}

/* ── TIMELINE TAB ── */
function renderTimeline(mc) {
  let h = '<div class="section-title">\uD83D\uDCC8 年次推移 / Publication Timeline</div>';
  h += '<div class="legend"><span class="legend-dot" style="background:var(--green)"></span>J-STAGE <span class="legend-dot" style="background:var(--blue);margin-left:8px"></span>PubMed</div>';
  h += renderTimelineChart(160, false);

  // Year list (clickable)
  h += '<div class="section-title" style="margin-top:24px;">年別一覧</div>';
  const years = Object.entries(DB.yd).sort((a,b)=>b[0].localeCompare(a[0]));
  h += '<div style="display:flex;flex-wrap:wrap;gap:6px;">';
  years.forEach(([y, d]) => {
    const total = (d.jp||0)+(d.pm||0);
    h += '<div style="display:inline-block;padding:6px 12px;background:#fff;border-radius:6px;cursor:pointer;box-shadow:var(--shadow);font-size:13px;" onclick="showYearArticles(\'' + y + '\')">';
    h += '<b>' + y + '</b> <span style="color:var(--green);">' + (d.jp||0) + '</span>+<span style="color:var(--blue);">' + (d.pm||0) + '</span> = ' + total + '</div>';
  });
  h += '</div>';
  mc.innerHTML = h;
}

function renderTimelineChart(height, mini) {
  const years = Object.entries(DB.yd).sort((a,b)=>a[0].localeCompare(b[0]));
  const maxCnt = Math.max(...years.map(([,d])=>(d.jp||0)+(d.pm||0)));
  let h = '<div class="timeline-chart" style="height:' + height + 'px;">';
  years.forEach(([y, d]) => {
    const jp = d.jp||0, pm = d.pm||0, total = jp+pm;
    const jpH = (jp/maxCnt*height).toFixed(0);
    const pmH = (pm/maxCnt*height).toFixed(0);
    h += '<div class="bar-group" onclick="showYearArticles(\'' + y + '\')">';
    h += '<span class="tip">' + y + ': JP=' + jp + ' PM=' + pm + ' (Total ' + total + ')</span>';
    h += '<div class="bar-jp" style="height:' + jpH + 'px;"></div>';
    h += '<div class="bar-pm" style="height:' + pmH + 'px;"></div>';
    h += '</div>';
  });
  h += '</div>';
  if (!mini) {
    h += '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);">';
    if (years.length > 0) {
      h += '<span>' + years[0][0] + '</span>';
      // decade markers
      const decades = new Set();
      years.forEach(([y]) => decades.add(Math.floor(parseInt(y)/10)*10));
      h += '<span>' + years[years.length-1][0] + '</span>';
    }
    h += '</div>';
  }
  return h;
}

function showYearArticles(year) {
  const indices = [];
  DB.articles.forEach((a, i) => { if (a.y === year) indices.push(i); });
  const mc = document.getElementById('main-content');
  let h = '<div class="breadcrumb"><span onclick="showTab(\'timeline\')">\uD83D\uDCC8 タイムライン</span> &gt; ' + year + '年</div>';
  h += '<div class="section-title">' + year + '年 <span class="count">' + indices.length + ' articles</span></div>';
  h += renderSourceFilter('showYearArticlesFiltered', "'" + year + "'");
  h += '<div id="article-container"></div>';
  mc.innerHTML = h;
  renderArticlesInto(indices, document.getElementById('article-container'));
  window.scrollTo(0,0);
}

function showYearArticlesFiltered(year, src) {
  currentSourceFilter = src;
  const indices = [];
  DB.articles.forEach((a, i) => { if (a.y === year) indices.push(i); });
  const filtered = getFilteredIndices(indices, src);
  document.querySelectorAll('.source-filter button').forEach(b => b.classList.toggle('active', b.dataset.src === src));
  renderArticlesInto(filtered, document.getElementById('article-container'));
}

/* ── SEARCH ── */
function doSearch(query) {
  setActiveTab('');
  const mc = document.getElementById('main-content');
  const q = query.toLowerCase();

  // Exact formula match
  if (DB.fi[query]) { showFormulaDetail(query); return; }
  // Exact author match
  if (DB.au[query]) { showAuthorArticles(query); return; }

  // Full text search
  const scored = [];
  for (let i = 0; i < DB.articles.length; i++) {
    const a = DB.articles[i];
    const title = (a.t||'').toLowerCase();
    const authors = (a.a||'').toLowerCase();
    const abs = (a.ab||'').toLowerCase();
    const titleEn = (a.te||'').toLowerCase();
    const combined = title + ' ' + titleEn + ' ' + authors + ' ' + abs;
    if (combined.includes(q)) {
      let score = 0;
      if (title.includes(q) || titleEn.includes(q)) score += 3;
      if (authors.includes(q)) score += 2;
      if (abs.includes(q)) score += 1;
      scored.push({idx:i, score});
    }
  }
  scored.sort((a,b) => b.score - a.score);

  // Partial matches in formulas, authors, tags
  const formulaMatches = Object.keys(DB.fi).filter(f => f.includes(query));
  const authorMatches = Object.keys(DB.au).filter(a => a.toLowerCase().includes(q)).slice(0,10);
  const tagMatches = Object.keys(DB.ai).filter(t => {
    const ax = DB.axes[t];
    if (!ax) return false;
    return ax.ja.includes(query) || ax.en.toLowerCase().includes(q);
  }).slice(0,10);

  let h = '<div class="section-title">検索: "' + escHtml(query) + '"</div>';

  if (formulaMatches.length > 0) {
    h += '<div style="margin-bottom:12px;"><b>\uD83D\uDC8A 方剤:</b> ';
    formulaMatches.slice(0,10).forEach(f => {
      h += '<span class="tag-pill" onclick="showFormulaDetail(\'' + esc(f) + '\')" style="margin:2px;">' + escHtml(f) + '</span> ';
    });
    h += '</div>';
  }
  if (tagMatches.length > 0) {
    h += '<div style="margin-bottom:12px;"><b>\uD83C\uDFF7 カテゴリ:</b> ';
    tagMatches.forEach(t => {
      h += '<span class="tag-pill" onclick="showTagArticles(\'' + t + '\')" style="margin:2px;">' + tagJa(t) + '</span> ';
    });
    h += '</div>';
  }
  if (authorMatches.length > 0) {
    h += '<div style="margin-bottom:12px;"><b>\uD83D\uDC64 著者:</b> ';
    authorMatches.forEach(a => {
      h += '<span class="tag-pill" onclick="showAuthorArticles(\'' + esc(a) + '\')" style="margin:2px;">' + escHtml(a) + '</span> ';
    });
    h += '</div>';
  }

  h += '<div class="result-info">' + scored.length + ' articles found' + (scored.length>200?' (showing first 200)':'') + '</div>';
  h += renderSourceFilter('doSearchFiltered', "'" + esc(query) + "'");
  h += '<div id="article-container"></div>';
  mc.innerHTML = h;
  renderArticlesInto(scored.slice(0,200).map(s=>s.idx), document.getElementById('article-container'));
  window.scrollTo(0,0);
}

function doSearchFiltered(query, src) {
  currentSourceFilter = src;
  document.querySelectorAll('.source-filter button').forEach(b => b.classList.toggle('active', b.dataset.src === src));
  const q = query.toLowerCase();
  const scored = [];
  for (let i = 0; i < DB.articles.length; i++) {
    const a = DB.articles[i];
    if (src !== 'all' && a.s !== src) continue;
    const title = (a.t||'').toLowerCase();
    const authors = (a.a||'').toLowerCase();
    const abs = (a.ab||'').toLowerCase();
    const titleEn = (a.te||'').toLowerCase();
    const combined = title + ' ' + titleEn + ' ' + authors + ' ' + abs;
    if (combined.includes(q)) {
      let score = 0;
      if (title.includes(q) || titleEn.includes(q)) score += 3;
      if (authors.includes(q)) score += 2;
      if (abs.includes(q)) score += 1;
      scored.push({idx:i, score});
    }
  }
  scored.sort((a,b) => b.score - a.score);
  renderArticlesInto(scored.slice(0,200).map(s=>s.idx), document.getElementById('article-container'));
}

/* ── Source filter buttons ── */
function renderSourceFilter(fnName, fnArgs) {
  return '<div class="source-filter">' +
    '<button class="active" data-src="all" onclick="' + fnName + '(' + fnArgs + ',\'all\')">All</button>' +
    '<button data-src="jp" onclick="' + fnName + '(' + fnArgs + ',\'jp\')">\uD83C\uDDEF\uD83C\uDDF5 J-STAGE</button>' +
    '<button data-src="pm" onclick="' + fnName + '(' + fnArgs + ',\'pm\')">\uD83D\uDD2C PubMed</button>' +
    '</div>';
}

/* ── Article Rendering (with pagination) ── */
function renderArticlesInto(indices, container, startFrom) {
  const PAGE = 50;
  const start = startFrom || 0;
  if (indices.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="icon">&#x1F4C4;</div><p>No articles found.</p></div>';
    return;
  }

  let h = '';
  if (start === 0) {
    h += '<div class="result-info">' + indices.length + ' articles</div>';
    h += '<div class="article-list" id="art-list">';
  }

  const end = Math.min(start + PAGE, indices.length);
  for (let p = start; p < end; p++) {
    const idx = indices[p];
    const a = DB.articles[idx];
    if (!a) continue;
    const cleanTitle = (a.t||'').replace(/<[^>]*>/g, '');
    const srcCls = a.s === 'jp' ? 'src-jp' : 'src-pm';
    const srcLabel = a.s === 'jp' ? '\uD83C\uDDEF\uD83C\uDDF5 J-STAGE' : '\uD83D\uDD2C PubMed';

    h += '<div class="article-item" id="art-' + idx + '">';
    h += '<div><span class="' + srcCls + '">' + srcLabel + '</span></div>';
    h += '<div class="atitle">';
    if (a.l) h += '<a href="' + escHtml(a.l) + '" target="_blank">' + escHtml(cleanTitle) + '</a>';
    else h += escHtml(cleanTitle);
    if (a.te) h += '<div style="font-size:12px;color:var(--muted);margin-top:1px;">' + escHtml(a.te) + '</div>';
    h += '</div>';
    h += '<div class="ameta">' + escHtml(a.a||'') + ' \u00B7 ' + escHtml(a.j||'') + ' \u00B7 ' + (a.y||'') + '</div>';
    h += '<div class="atags">';
    (a.d||[]).forEach(t => { h += '<span class="tag-d" style="cursor:pointer" onclick="event.stopPropagation();showTagArticles(\'' + t + '\')">' + tagJa(t) + '</span>'; });
    (a.sx||[]).forEach(t => { h += '<span class="tag-sx" style="cursor:pointer" onclick="event.stopPropagation();showTagArticles(\'' + t + '\')">' + tagJa(t) + '</span>'; });
    (a.int||[]).forEach(t => { h += '<span class="tag-int" style="cursor:pointer" onclick="event.stopPropagation();showTagArticles(\'' + t + '\')">' + tagJa(t) + '</span>'; });
    (a.sd||[]).forEach(t => { h += '<span class="tag-sd" style="cursor:pointer" onclick="event.stopPropagation();showTagArticles(\'' + t + '\')">' + tagJa(t) + '</span>'; });
    (a.set||[]).forEach(t => { h += '<span class="tag-set" style="cursor:pointer" onclick="event.stopPropagation();showTagArticles(\'' + t + '\')">' + tagJa(t) + '</span>'; });
    h += '</div>';
    if (a.f && a.f.length > 0) {
      h += '<div class="aformula">\uD83D\uDC8A ';
      a.f.forEach((f,fi) => {
        if (fi > 0) h += ', ';
        h += '<span class="tag-f" onclick="event.stopPropagation();showFormulaDetail(\'' + esc(typeof f==='number'?''+f:f) + '\')">' + escHtml(typeof f==='number'?''+f:f) + '</span>';
      });
      h += '</div>';
    }
    if (a.ab) {
      h += '<span class="toggle-ab" onclick="this.parentElement.classList.toggle(\'expanded\');this.textContent=this.parentElement.classList.contains(\'expanded\')?\'\u25B2 \u62B1\u9332\u3092\u9589\u3058\u308B\':\'\u25B6 \u62B1\u9332\u3092\u8868\u793A\';">\u25B6 \u62B1\u9332\u3092\u8868\u793A</span>';
      h += '<div class="abstract-text">' + escHtml(a.ab) + '</div>';
    }
    h += '</div>';
  }

  if (start === 0) {
    h += '</div>';
    if (end < indices.length) {
      h += '<button class="load-more" onclick="loadMoreArticles(this,' + JSON.stringify(indices).replace(/"/g,'&quot;') + ',' + end + ')">More (' + (indices.length - end) + ' remaining)</button>';
    }
    container.innerHTML = h;
  } else {
    // Append to existing list
    const list = document.getElementById('art-list');
    list.insertAdjacentHTML('beforeend', h);
    // Update or remove load-more button
    const btn = container.querySelector('.load-more');
    if (btn) {
      if (end < indices.length) {
        btn.outerHTML = '<button class="load-more" onclick="loadMoreArticles(this,' + JSON.stringify(indices).replace(/"/g,'&quot;') + ',' + end + ')">More (' + (indices.length - end) + ' remaining)</button>';
      } else {
        btn.remove();
      }
    }
  }
}

function loadMoreArticles(btn, indices, startFrom) {
  const container = btn.parentElement;
  renderArticlesInto(indices, container, startFrom);
}

init();
</script>
</body>
</html>"""

# ── Build ──
html = HTML_TEMPLATE.replace('%%DB_JSON%%', db_json)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

out_size = os.path.getsize(OUT_PATH)
print(f"Output: {OUT_PATH} ({out_size/1024/1024:.1f} MB)")
print(f"Articles: {db['stats']['total']}")
print("Done.")
