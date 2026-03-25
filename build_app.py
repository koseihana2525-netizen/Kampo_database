# -*- coding: utf-8 -*-
"""Build single-file Kampo Evidence Map HTML with embedded data and smart search"""
import json

# Load data
with open('output/kampo_db.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

with open('output/kampo_synonyms.json', 'r', encoding='utf-8') as f:
    syns = json.load(f)

db_json = json.dumps(db, ensure_ascii=False)
syns_json = json.dumps(syns, ensure_ascii=False)

with open('output/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace fetch-based loadDB with embedded data
html = html.replace(
    "async function loadDB() {\n  const res = await fetch('kampo_db.json');\n  DB = await res.json();",
    f"const SYNONYMS = {syns_json};\n\nasync function loadDB() {{\n  DB = {db_json};"
)

# 2. Replace search handler with smart search
old_search = """// Search
document.getElementById('search-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const q = e.target.value.trim();
    if (!q) { showDiseases(); return; }

    viewStack = [];

    // Check if it matches a formula name
    if (DB.formula_index[q]) {
      showFormula(q);
      return;
    }

    // Check if it matches a disease
    if (DB.disease_index[q]) {
      showDisease(q);
      return;
    }

    // Full text search
    showArticles(q);
  }
});"""

new_search = r"""// Smart search with synonym expansion and scoring
function smartSearch(query) {
  const ageMatch = query.match(/(\d+)歳/);
  const age = ageMatch ? parseInt(ageMatch[1]) : null;
  const isFemale = /女性|女|婦人/.test(query);
  const isElderly = /高齢|老人/.test(query) || (age && age >= 65);

  let searchTerms = [query];
  const cleanQuery = query.replace(/\d+歳|女性|男性|女|男|の|が|で|に|を|は|困|って|いる|ている|した|ます/g, '').trim();

  for (const [category, terms] of Object.entries(SYNONYMS.synonyms)) {
    let matched = false;
    for (const term of terms) {
      if (query.includes(term) || cleanQuery.includes(term) || term.includes(cleanQuery)) {
        matched = true;
        break;
      }
    }
    if (matched) searchTerms = searchTerms.concat(terms);
  }

  if (isFemale && age && age >= 40 && age <= 59) {
    searchTerms = searchTerms.concat(['更年期', 'のぼせ', 'ホットフラッシュ']);
  }
  if (isElderly) {
    searchTerms = searchTerms.concat(['認知症', '頻尿', 'こむら返り', '食欲不振']);
  }
  searchTerms = [...new Set(searchTerms)];

  const scored = [];
  for (let i = 0; i < DB.articles.length; i++) {
    const a = DB.articles[i];
    const text = (a.title + ' ' + a.abstract).toLowerCase();
    let score = 0;
    let matchedTerms = [];

    for (const term of searchTerms) {
      const tl = term.toLowerCase();
      if (text.includes(tl)) {
        score += a.title.toLowerCase().includes(tl) ? 3 : 1;
        matchedTerms.push(term);
      }
    }
    if (a.formulas.length > 0) score += 0.5;
    if (a.abstract) score += 0.3;
    const year = parseInt(a.year) || 2000;
    score += (year - 1980) * 0.02;

    if (score > 0) scored.push({ idx: i, score, matchedTerms: [...new Set(matchedTerms)] });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored;
}

function showSmartResults(query, results) {
  const content = document.getElementById('content');
  document.getElementById('back-btn').style.display = 'inline-block';
  viewStack.push({type: currentView});

  let html = '<div class="section-title">おすすめ論文</div>';
  html += '<p class="result-info">' + query + ' → ' + results.length + '件ヒット</p>';

  if (results.length === 0) {
    html += '<div class="empty-state"><div class="icon">&#x1F50D;</div><p>該当する論文が見つかりませんでした。</p></div>';
    content.innerHTML = html;
    return;
  }

  const top3 = results.slice(0, 3);
  html += '<div style="margin:16px 0;">';
  for (let r = 0; r < top3.length; r++) {
    const a = DB.articles[top3[r].idx];
    const cleanTitle = a.title.replace(/<[^>]*>/g, '');
    const stars = '\u2605'.repeat(Math.min(5, Math.ceil(top3[r].score / 2)));
    html += '<div style="background:white;border-radius:10px;padding:20px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #f39c12;">';
    html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">';
    html += '<span style="background:#f39c12;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:14px;">' + (r+1) + '</span>';
    html += '<span style="font-size:12px;color:#888;">関連度: ' + stars + '</span>';
    html += '</div>';
    html += '<div style="font-size:16px;font-weight:600;">';
    if (a.link) html += '<a href="' + a.link + '" target="_blank" style="color:#2c3e50;text-decoration:none;">' + cleanTitle + '</a>';
    else html += cleanTitle;
    html += '</div>';
    html += '<div style="font-size:12px;color:#888;margin-top:4px;">' + a.year + '\u5E74' + (a.authors ? ' | ' + a.authors : '') + '</div>';
    html += '<div class="tags" style="margin-top:8px;">';
    for (const f of a.formulas) {
      html += '<span class="formula-tag">' + f + '</span>';
    }
    html += '</div>';
    html += '<div style="font-size:11px;color:#3498db;margin-top:6px;">マッチ: ' + top3[r].matchedTerms.slice(0,5).join(', ') + '</div>';
    if (a.abstract) {
      html += '<div style="font-size:13px;color:#555;margin-top:8px;line-height:1.6;">' + a.abstract.substring(0, 200) + (a.abstract.length > 200 ? '...' : '') + '</div>';
    }
    html += '</div>';
  }
  html += '</div>';

  if (results.length > 3) {
    html += '<div class="section-title" style="font-size:15px;">その他の関連論文（' + (results.length - 3) + '件）</div>';
    html += renderArticleList(results.slice(3, 23).map(r => r.idx));
  }
  content.innerHTML = html;
  window.scrollTo(0, 0);
}

// Search
document.getElementById('search-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const q = e.target.value.trim();
    if (!q) { showDiseases(); return; }
    viewStack = [];
    if (DB.formula_index[q]) { showFormula(q); return; }
    if (DB.disease_index[q]) { showDisease(q); return; }
    const results = smartSearch(q);
    showSmartResults(q, results);
  }
});"""

html = html.replace(old_search, new_search)

with open('output/kampo_evidence_map.html', 'w', encoding='utf-8') as f:
    f.write(html)

size_mb = len(html.encode('utf-8')) / 1024 / 1024
print(f"Done: output/kampo_evidence_map.html ({size_mb:.1f}MB)")
print("Open this file in your browser - it works standalone!")
