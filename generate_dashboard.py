"""
Generador del dashboard HTML - Vinya Son Nadal
===============================================
Llegeix data/historial.csv i data/mildiu_historial.csv
i genera les pàgines HTML del dashboard:
  - docs/index.html      (hub principal)
  - docs/oidi.html       (oïdi - model Gubler)
  - docs/mildiu.html     (mildiu - model EPI)
  - docs/botritis.html   (botritis - base sense model)
  - docs/blackrot.html   (black rot - base sense model)

S'executa automàticament al final del workflow de GitHub Actions.
"""

import pandas as pd
import numpy as np
import json
import os
import math
from datetime import datetime

# ── Configuració ─────────────────────────────────────────────────────────────
CSV_HISTORIAL = "data/historial.csv"
CSV_MILDIU    = "data/mildiu_historial.csv"
OUTPUT_DIR    = "docs"

# ═════════════════════════════════════════════════════════════════════════════
#  CSS COMÚ
# ═════════════════════════════════════════════════════════════════════════════

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f5f1eb;--surface:#ffffff;--surface2:#ece7df;
  --border:#ddd6cc;--text:#2d2926;--muted:#7a7269;
  --heading:#1a1714;
  --accent:#6b4c8a;--verd:#2e7d32;--ambre:#c77d00;
  --taronja:#d45e0a;--vermell:#c62828;--violeta:#6a1b9a;
  --radius:12px;
  --shadow:0 2px 8px rgba(0,0,0,.06);
  --shadow-lg:0 8px 24px rgba(0,0,0,.08);
  --navbar-bg:rgba(255,255,255,0.82);
  --chart-grid:rgba(0,0,0,.06);
  --chart-tick:#7a7269;
  --input-bg:#f5f1eb;
  --toast-bg:#ffffff;
}
[data-theme="dark"]{
  --bg:#1c1917;--surface:#292524;--surface2:#3a3530;
  --border:#4a453e;--text:#e7e1d8;--muted:#a09888;
  --heading:#f5f1eb;
  --accent:#a78bfa;--verd:#4ade80;--ambre:#fbbf24;
  --taronja:#fb923c;--vermell:#f87171;--violeta:#c084fc;
  --shadow:0 2px 8px rgba(0,0,0,.25);
  --shadow-lg:0 8px 24px rgba(0,0,0,.35);
  --navbar-bg:rgba(28,25,23,0.88);
  --chart-grid:rgba(255,255,255,.06);
  --chart-tick:#a09888;
  --input-bg:#3a3530;
  --toast-bg:#292524;
}
body{background:var(--bg);color:var(--text);
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  font-size:14px;line-height:1.5;margin:0;padding:0;
  transition:background .3s,color .3s}

/* Navbar */
.navbar{position:sticky;top:0;z-index:100;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;height:56px;
  background:var(--navbar-bg);
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);
  box-shadow:var(--shadow);transition:background .3s}
.nav-brand{font-size:16px;font-weight:600;color:var(--heading);
  text-decoration:none;display:flex;align-items:center;gap:8px}
.nav-links{display:flex;gap:4px;flex-wrap:wrap;align-items:center}
.nav-link{padding:6px 14px;border-radius:8px;font-size:13px;font-weight:500;
  color:var(--muted);text-decoration:none;white-space:nowrap;transition:all .2s}
.nav-link:hover{color:var(--text);background:var(--surface2)}
.nav-link.active{color:var(--heading);background:var(--surface2);font-weight:600}

/* Theme toggle */
.theme-toggle{background:none;border:1px solid var(--border);border-radius:8px;
  cursor:pointer;padding:5px 10px;font-size:16px;line-height:1;
  color:var(--muted);transition:all .2s;margin-left:8px}
.theme-toggle:hover{border-color:var(--accent);color:var(--accent)}

/* Navbar dropdown */
.nav-dropdown{position:relative}
.nav-dropdown-toggle{padding:6px 14px;border-radius:8px;font-size:13px;font-weight:500;
  color:var(--muted);text-decoration:none;white-space:nowrap;transition:all .2s;
  cursor:pointer;display:flex;align-items:center;gap:4px;background:none;border:none;
  font-family:inherit}
.nav-dropdown-toggle:hover{color:var(--text);background:var(--surface2)}
.nav-dropdown-toggle.active{color:var(--heading);background:var(--surface2);font-weight:600}
.nav-dropdown-toggle .chevron{font-size:10px;transition:transform .2s;opacity:.6}
.nav-dropdown:hover .chevron{transform:rotate(180deg)}
.nav-dropdown-menu{display:none;position:absolute;top:100%;left:0;
  min-width:180px;padding:6px;margin-top:4px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:10px;box-shadow:var(--shadow-lg);z-index:200}
.nav-dropdown:hover .nav-dropdown-menu, .nav-dropdown.open .nav-dropdown-menu{display:block}
.nav-dropdown-menu a{display:block;padding:7px 14px;border-radius:6px;
  font-size:13px;font-weight:500;color:var(--muted);text-decoration:none;
  transition:all .15s}
.nav-dropdown-menu a:hover{color:var(--text);background:var(--surface2)}
.nav-dropdown-menu a.active{color:var(--accent);font-weight:600}
.nav-dropdown-menu .menu-sep{height:1px;background:var(--border);margin:4px 8px}

/* Crop summary cards (index) */
.crop-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:16px;margin-bottom:28px}
.crop-card{background:var(--surface);border:1px solid var(--border);
  border-radius:14px;padding:22px;text-decoration:none;color:inherit;
  transition:all .25s ease;position:relative;overflow:hidden;display:block;
  box-shadow:var(--shadow)}
.crop-card:hover{border-color:var(--accent);transform:translateY(-3px);
  box-shadow:var(--shadow-lg)}
.crop-card .crop-icon{font-size:32px;margin-bottom:8px;display:block}
.crop-card .crop-name{font-size:18px;font-weight:700;color:var(--heading);margin-bottom:4px}
.crop-card .crop-sub{font-size:12px;color:var(--muted);margin-bottom:12px}
.crop-card .crop-stats{display:flex;flex-direction:column;gap:6px}
.crop-card .crop-stat{display:flex;align-items:center;justify-content:space-between;
  font-size:13px;color:var(--text)}
.crop-card .crop-stat .dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.crop-card .crop-coming{color:var(--muted);font-size:13px;font-style:italic;padding:8px 0}
.crop-card .arrow{position:absolute;right:18px;bottom:18px;
  color:var(--muted);font-size:18px;transition:transform .2s}
.crop-card:hover .arrow{transform:translateX(3px);color:var(--accent)}

/* Main */
main{max-width:1100px;margin:0 auto;padding:24px 16px}

/* Page header */
.page-header{display:flex;justify-content:space-between;align-items:flex-start;
  margin-bottom:24px;flex-wrap:wrap;gap:12px}
.page-header h1{font-size:22px;font-weight:700;color:var(--heading);letter-spacing:-.3px}
.page-header .sub{color:var(--muted);font-size:12px;margin-top:2px}
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;
  border-radius:20px;font-size:12px;font-weight:600;
  border:1px solid currentColor;letter-spacing:.3px}

/* KPI cards */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:12px;margin-bottom:24px}
.kpi{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:16px 18px;transition:all .2s;
  box-shadow:var(--shadow)}
.kpi:hover{border-color:var(--accent);box-shadow:var(--shadow-lg)}
.kpi-label{font-size:11px;color:var(--muted);text-transform:uppercase;
  letter-spacing:.5px;margin-bottom:6px}
.kpi-val{font-size:28px;font-weight:700;color:var(--heading);line-height:1}
.kpi-unit{font-size:13px;color:var(--muted);margin-left:2px}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:4px}
.ui-bar-outer{background:var(--border);border-radius:4px;height:6px;
  margin-top:8px;overflow:hidden}
.ui-bar-inner{height:100%;border-radius:4px;transition:width .5s}

/* Filter bar */
.filter-bar{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap;align-items:center}
.filter-btn{padding:6px 16px;border-radius:8px;border:1px solid var(--border);
  background:var(--surface);color:var(--muted);cursor:pointer;
  font-size:12px;font-weight:500;font-family:inherit;transition:all .2s;
  box-shadow:var(--shadow)}
.filter-btn:hover{color:var(--text);border-color:var(--accent)}
.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);
  box-shadow:0 2px 8px rgba(107,76,138,.25)}
.filter-sep{width:1px;height:24px;background:var(--border);margin:0 6px}
.filter-date{padding:5px 10px;border-radius:8px;border:1px solid var(--border);
  background:var(--surface);color:var(--text);font-size:12px;font-family:inherit;
  width:auto;cursor:pointer}
.filter-date:focus{border-color:var(--accent);outline:none}
.filter-apply{padding:6px 14px;border-radius:8px;border:none;
  background:var(--accent);color:#fff;cursor:pointer;
  font-size:12px;font-weight:600;font-family:inherit;transition:all .2s}
.filter-apply:hover{opacity:.85}

/* Chart cards */
.chart-card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px;margin-bottom:16px;
  box-shadow:var(--shadow);transition:box-shadow .2s}
.chart-card:hover{box-shadow:var(--shadow-lg)}
.chart-title{font-size:13px;font-weight:600;color:var(--muted);
  text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;
  display:flex;align-items:center;justify-content:space-between}
.chart-info-btn{background:var(--surface2);border:1px solid var(--border);
  border-radius:50%;width:22px;height:22px;display:flex;align-items:center;
  justify-content:center;font-size:12px;cursor:pointer;color:var(--muted);
  transition:all .2s;flex-shrink:0;line-height:1}
.chart-info-btn:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.chart-desc{display:none;font-size:12px;line-height:1.6;color:var(--muted);
  background:var(--surface2);border-radius:8px;padding:10px 14px;
  margin-bottom:12px;border-left:3px solid var(--accent)}
.chart-desc.show{display:block}
canvas{max-height:200px}
.llindars{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;font-size:11px}
.ll{padding:2px 8px;border-radius:4px;border:1px solid}

/* Disease cards (index) */
.disease-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:16px;margin-bottom:28px}
.disease-card{background:var(--surface);border:1px solid var(--border);
  border-radius:14px;padding:22px;text-decoration:none;color:inherit;
  transition:all .25s ease;position:relative;overflow:hidden;display:block;
  box-shadow:var(--shadow)}
.disease-card:hover{border-color:var(--accent);transform:translateY(-3px);
  box-shadow:var(--shadow-lg)}
.disease-card .icon{font-size:28px;margin-bottom:10px;display:block}
.disease-card .name{font-size:16px;font-weight:700;color:var(--heading);margin-bottom:2px}
.disease-card .agent{font-size:12px;color:var(--muted);font-style:italic;margin-bottom:12px}
.disease-card .risk-line{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.disease-card .risk-badge{display:inline-flex;align-items:center;gap:5px;
  padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600}
.disease-card .desc{font-size:12px;color:var(--muted);line-height:1.5}
.disease-card .arrow{position:absolute;right:18px;bottom:18px;
  color:var(--muted);font-size:18px;transition:transform .2s}
.disease-card:hover .arrow{transform:translateX(3px);color:var(--accent)}

/* Info cards */
.info-card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;margin-bottom:16px;
  box-shadow:var(--shadow)}
.info-card h3{font-size:14px;font-weight:600;color:var(--heading);margin-bottom:8px}
.info-card p{color:var(--muted);font-size:13px;line-height:1.6}
.info-card ul{color:var(--muted);font-size:13px;margin-left:16px;margin-top:6px;line-height:1.8}
.notice{background:rgba(107,76,138,.06);border:1px solid rgba(107,76,138,.2);
  border-radius:var(--radius);padding:16px 20px;margin-bottom:20px;
  font-size:13px;color:var(--accent);display:flex;align-items:center;gap:10px}

/* Recommendation Box */
.recom-box{background:rgba(46,125,50,.06);border:1px solid rgba(46,125,50,.2);
  border-radius:var(--radius);padding:16px 20px;margin-bottom:20px;
  font-size:13px;color:var(--verd);display:flex;align-items:flex-start;gap:12px}
.recom-box.warning{background:rgba(198,40,40,.06);border-color:rgba(198,40,40,.2);color:var(--vermell)}
.recom-box.info{background:rgba(107,76,138,.06);border-color:rgba(107,76,138,.2);color:var(--accent)}
.recom-icon{font-size:18px;line-height:1}
.recom-content h4{font-size:14px;font-weight:600;margin-bottom:4px;color:currentColor}
.recom-content p{color:var(--text);opacity:0.85;margin-bottom:4px;line-height:1.5}
.recom-content ul{color:var(--text);opacity:0.85;margin-left:16px;margin-top:4px;line-height:1.6}

/* Treatment section */
.section-title{font-size:16px;font-weight:700;color:var(--heading);margin:32px 0 16px;
  padding-top:20px;border-top:1px solid var(--border)}
.card{background:var(--surface);border:1px solid var(--border);
  border-radius:14px;padding:20px;margin-bottom:16px;box-shadow:var(--shadow)}
.card-title{font-size:13px;font-weight:600;color:var(--muted);
  text-transform:uppercase;letter-spacing:.5px;margin-bottom:16px}
label{display:block;font-size:12px;color:var(--muted);margin-bottom:4px;margin-top:12px}
label:first-of-type{margin-top:0}
input,select,textarea{width:100%;background:var(--input-bg);border:1px solid var(--border);
  border-radius:8px;color:var(--text);font-size:14px;
  padding:8px 12px;outline:none;font-family:inherit;transition:border-color .2s}
input:focus,textarea:focus,select:focus{border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(107,76,138,.1)}
textarea{resize:vertical;min-height:60px}
.checkbox-group{display:flex;gap:12px;margin-top:4px;flex-wrap:wrap}
.checkbox-label{display:flex;align-items:center;gap:6px;cursor:pointer;
  font-size:13px;color:var(--text)}
input[type=checkbox]{width:16px;height:16px;cursor:pointer;accent-color:var(--accent)}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;
  border-radius:8px;font-size:14px;font-weight:500;
  cursor:pointer;border:none;transition:all .15s;font-family:inherit}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{opacity:.85}
.btn-danger{background:transparent;border:1px solid var(--vermell);
  color:var(--vermell);padding:4px 10px;font-size:12px}
.btn-danger:hover{background:rgba(198,40,40,.08)}
.actions{display:flex;justify-content:flex-end;margin-top:20px}
.tractament-item{display:grid;grid-template-columns:1fr auto;
  gap:8px;align-items:start;padding:12px 0;
  border-bottom:1px solid var(--border)}
.tractament-item:last-child{border-bottom:none}
.t-data{font-size:13px;font-weight:500}
.t-producte{font-size:12px;color:var(--muted);margin-top:2px}
.t-badges{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}
.t-badge{font-size:11px;padding:2px 8px;border-radius:20px;font-weight:500}
.t-badge-oidio{background:rgba(199,125,0,.12);color:var(--ambre)}
.t-badge-mildiu{background:rgba(107,76,138,.12);color:var(--accent)}
.t-badge-botritis{background:rgba(139,92,246,.12);color:#7c3aed}
.t-badge-blackrot{background:rgba(198,40,40,.12);color:var(--vermell)}
.empty{color:var(--muted);font-size:13px;padding:16px 0;text-align:center}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  background:var(--toast-bg);border:1px solid var(--border);border-radius:8px;
  padding:10px 20px;font-size:13px;display:none;z-index:999;
  box-shadow:var(--shadow-lg)}
.toast.ok{border-color:var(--verd);color:var(--verd)}
.toast.err{border-color:var(--vermell);color:var(--vermell)}
.config-box{background:var(--surface2);border:1px solid var(--border);
  border-radius:8px;padding:14px;margin-bottom:16px;
  font-size:12px;color:var(--muted);line-height:1.6}
.config-box input{margin-top:6px;font-size:12px;font-family:monospace}
code{background:var(--surface2);padding:2px 6px;border-radius:4px;
  font-family:monospace;font-size:11px;color:var(--accent)}

/* Footer */
footer{color:var(--muted);font-size:11px;text-align:center;
  margin-top:32px;padding-top:16px;border-top:1px solid var(--border);line-height:1.8}

/* Responsive */
@media(max-width:600px){
  canvas{max-height:160px}
  .navbar{padding:0 12px}
  .nav-link{padding:6px 10px;font-size:12px}
  main{padding:16px 12px}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .disease-grid{grid-template-columns:1fr}
  .checkbox-group{flex-direction:column;gap:8px}
  .page-header h1{font-size:18px}
  .filter-bar{gap:4px}
  .filter-date{font-size:11px;padding:4px 6px}
}
"""

# ═════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT COMÚ
# ═════════════════════════════════════════════════════════════════════════════

JS_THEME = """
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? '' : 'dark');
  localStorage.setItem('sn-theme', isDark ? 'light' : 'dark');
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = isDark ? '🌙' : '☀️';
}
(function(){
  const saved = localStorage.getItem('sn-theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = saved === 'dark' ? '☀️' : '🌙';
})();
"""

JS_FILTER = """
const FILTER_SIZES = {'24h':48,'3d':144,'7d':336,'14d':999999};
let activeFilter = '7d';
let customStart = null, customEnd = null;

function toggleChartInfo(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('show');
}

function setFilter(range) {
  activeFilter = range;
  customStart = null;
  customEnd = null;
  const n = Math.min(FILTER_SIZES[range], ALL.labels.length);
  const start = Math.max(0, ALL.labels.length - n);
  buildCharts(start);
  document.querySelectorAll('.filter-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.range === range));
}

function setCustomRange() {
  const dIni = document.getElementById('filter-date-ini');
  const dFi  = document.getElementById('filter-date-fi');
  if (!dIni || !dFi || !dIni.value || !dFi.value) return;
  
  const ini = new Date(dIni.value);
  const fi  = new Date(dFi.value);
  fi.setHours(23,59,59);
  
  let startIdx = -1, endIdx = -1;
  for (let i = 0; i < ALL.ts_raw.length; i++) {
    const d = new Date(ALL.ts_raw[i]);
    if (startIdx === -1 && d >= ini) startIdx = i;
    if (d <= fi) endIdx = i;
  }
  
  if (startIdx === -1 || endIdx === -1 || startIdx > endIdx) return;
  
  customStart = startIdx;
  customEnd = endIdx + 1;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  buildCharts(startIdx, customEnd);
}

// Theme toggle
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? '' : 'dark');
  localStorage.setItem('sn-theme', isDark ? 'light' : 'dark');
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = isDark ? '🌙' : '☀️';
  // Rebuild charts with new theme colors
  if (typeof rebuildCurrentView === 'function') rebuildCurrentView();
}
(function(){
  const saved = localStorage.getItem('sn-theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = saved === 'dark' ? '☀️' : '🌙';
})();

function getChartColors() {
  const style = getComputedStyle(document.documentElement);
  return {
    grid: style.getPropertyValue('--chart-grid').trim() || 'rgba(0,0,0,.06)',
    tick: style.getPropertyValue('--chart-tick').trim() || '#7a7269'
  };
}
"""

JS_CHART_BASE = """
function cfgBase() {
  const cc = getChartColors();
  return {
    responsive:true, maintainAspectRatio:true,
    plugins:{legend:{display:false}},
    scales:{
      x:{ticks:{color:cc.tick,maxTicksLimit:8,font:{size:10}},
         grid:{color:cc.grid}},
      y:{ticks:{color:cc.tick,font:{size:10}},
         grid:{color:cc.grid}}
    }
  };
}
function createTHChart(L, T, H) {
  const cc = getChartColors();
  return new Chart(document.getElementById('chart-th'), {
    type:'line',
    data:{labels:L, datasets:[
      {label:'T (°C)', data:T, borderColor:'#f97316',
       backgroundColor:'rgba(249,115,22,.1)', borderWidth:1.5,
       pointRadius:0, fill:true, tension:.3, yAxisID:'yT'},
      {label:'HR (%)', data:H, borderColor:'#38bdf8',
       backgroundColor:'rgba(56,189,248,.08)', borderWidth:1.5,
       pointRadius:0, fill:false, tension:.3, yAxisID:'yHR'}
    ]},
    options:{...cfgBase(),
      plugins:{...cfgBase().plugins,
        legend:{display:true, labels:{color:'#9ca3af',font:{size:11}}},
        annotation:{annotations:{
          hr40:{type:'line',yScaleID:'yHR',yMin:40,yMax:40,
                borderColor:'rgba(56,189,248,.3)',borderWidth:1,borderDash:[4,4],
                label:{content:'HR 40%',display:true,color:'rgba(56,189,248,.5)',font:{size:9}}},
          hr70:{type:'line',yScaleID:'yHR',yMin:70,yMax:70,
                borderColor:'rgba(56,189,248,.5)',borderWidth:1,borderDash:[4,4],
                label:{content:'HR 70%',display:true,color:'rgba(56,189,248,.7)',font:{size:9}}}
        }}
      },
      scales:{
        x:cfgBase().scales.x,
        yT:{...cfgBase().scales.y, position:'left',
            title:{display:true,text:'°C',color:'#f97316',font:{size:10}}},
        yHR:{...cfgBase().scales.y, position:'right', min:0, max:100,
             title:{display:true,text:'%',color:'#38bdf8',font:{size:10}},
             grid:{drawOnChartArea:false}}
      }
    }
  });
}
function createPlujaChart(L, P) {
  return new Chart(document.getElementById('chart-pluja'), {
    type:'bar',
    data:{labels:L, datasets:[{
      label:'Pluja (mm)', data:P,
      backgroundColor:'rgba(56,189,248,.5)',
      borderColor:'rgba(56,189,248,.8)', borderWidth:1
    }]},
    options:{...cfgBase(),
      scales:{x:cfgBase().scales.x,
        y:{...cfgBase().scales.y, min:0,
           title:{display:true,text:'mm',color:'#38bdf8',font:{size:10}}}}
    }
  });
}

function createRadUVChart(L, Rad, UV) {
  return new Chart(document.getElementById('chart-raduv'), {
    type: 'line',
    data: {
      labels: L,
      datasets: [
        {
          label: 'Radiació Solar (W/m²)',
          data: Rad,
          borderColor: '#eab308',
          backgroundColor: 'rgba(234,179,8,0.1)',
          borderWidth: 1.5,
          pointRadius: 0,
          fill: true,
          tension: 0.3,
          yAxisID: 'yRad'
        },
        {
          label: 'Índex UV',
          data: UV,
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139,92,246,0.1)',
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          tension: 0.3,
          yAxisID: 'yUV'
        }
      ]
    },
    options: {
      ...cfgBase(),
      plugins: {
        ...cfgBase().plugins,
        legend: { display: true, labels: { color: '#9ca3af', font: { size: 11 } } }
      },
      scales: {
        x: cfgBase().scales.x,
        yRad: { ...cfgBase().scales.y, position: 'left', min: 0, title: { display: true, text: 'W/m²', color: '#eab308', font: { size: 10 } } },
        yUV: { ...cfgBase().scales.y, position: 'right', min: 0, title: { display: true, text: 'UVI', color: '#8b5cf6', font: { size: 10 } }, grid: { drawOnChartArea: false } }
      }
    }
  });
}

function createET0Chart(L, ET0, P, B) {
  return new Chart(document.getElementById('chart-et0'), {
    type: 'bar',
    data: {
      labels: L,
      datasets: [
        {
          type: 'line',
          label: 'ET0 (mm)',
          data: ET0,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239,68,68,0.1)',
          borderWidth: 2,
          pointRadius: 2,
          fill: true,
          tension: 0.3,
          yAxisID: 'y'
        },
        {
          type: 'bar',
          label: 'Pluja (mm)',
          data: P,
          backgroundColor: '#3b82f6',
          borderRadius: 2,
          yAxisID: 'y'
        }
      ]
    },
    options: {
      ...cfgBase(),
      plugins: {
        ...cfgBase().plugins,
        legend: { display: true, labels: { color: '#9ca3af', font: { size: 11 } } },
        tooltip: {
          callbacks: {
            afterBody: function(ctx) {
              const idx = ctx[0].dataIndex;
              return 'Balanc acum.: ' + B[idx] + ' mm';
            }
          }
        }
      },
      scales: {
        x: cfgBase().scales.x,
        y: { ...cfgBase().scales.y, min: 0, title: { display: true, text: 'mm', color: '#9ca3af', font: { size: 10 } } }
      }
    }
  });
}

function createPhenologyChart(L, GDD, Fred) {
  const cc = getChartColors();
  return new Chart(document.getElementById('chart-phenology'), {
    type:'line',
    data:{labels:L, datasets:[
      {label:'Graus-Dia Acum.', data:GDD, borderColor:'#f59e0b',
       backgroundColor:'rgba(245,158,11,.1)', borderWidth:2,
       pointRadius:0, fill:true, tension:.3, yAxisID:'yGDD'},
      {label:'Hores Fred Acum.', data:Fred, borderColor:'#60a5fa',
       backgroundColor:'rgba(96,165,250,.1)', borderWidth:2,
       pointRadius:0, fill:true, tension:.3, yAxisID:'yFred'}
    ]},
    options:{...cfgBase(),
      plugins:{...cfgBase().plugins,
        legend:{display:true, labels:{color:'#9ca3af',font:{size:11}}}
      },
      scales:{
        x:cfgBase().scales.x,
        yGDD:{...cfgBase().scales.y, position:'left',
            title:{display:true,text:'°D (Base 10)',color:'#f59e0b',font:{size:10}}},
        yFred:{...cfgBase().scales.y, position:'right',
             title:{display:true,text:'h (<7°C)',color:'#60a5fa',font:{size:10}},
             grid:{drawOnChartArea:false}}
      }
    }
  });
}
function getProtectionInfo(t, tsRaw, pluja, temps) {
  let tDate = new Date(t.data);
  let baseDays = t.dies_proteccio || 10;
  let tEnd = new Date(tDate.getTime() + baseDays * 24 * 60 * 60 * 1000);
  let isDegraded = false;
  let reason = "";

  if (t.ecologic === true) {
    let rainAccum = 0;
    let validDays = baseDays;
    let tMaxDay = -99;
    let currentDayStr = null;
    let didCutByRain = false;

    for (let i = 0; i < tsRaw.length; i++) {
      let currDate = new Date(tsRaw[i]);
      if (currDate < tDate) continue;
      if (currDate > tEnd) break;

      let r = pluja && pluja[i] ? pluja[i] : 0;
      let temp = temps && temps[i] ? temps[i] : 0;

      // Regla A: Rentat per pluja (>12mm)
      if (!didCutByRain) {
        rainAccum += r;
        if (rainAccum >= 12) {
          tEnd = currDate;
          didCutByRain = true;
          isDegraded = true;
          reason = "Pluja >12mm";
          break; // Rentat total, s'acaba aquí la protecció
        }
      }

      // Regla B: Calor > 35ºC (-2 dies)
      let dayStr = currDate.toLocaleDateString();
      if (dayStr !== currentDayStr) {
        if (currentDayStr && tMaxDay >= 35) {
          validDays -= 2;
          isDegraded = true;
          reason = "Calor >35ºC";
          tEnd = new Date(tDate.getTime() + validDays * 24 * 60 * 60 * 1000);
          if (currDate > tEnd) {
            tEnd = currDate;
            break;
          }
        }
        currentDayStr = dayStr;
        tMaxDay = temp;
      } else {
        if (temp > tMaxDay) tMaxDay = temp;
      }
    }
  }

  return { active: true, endDate: tEnd, degraded: isDegraded, reason: reason };
}

function createUIGublerChart(L, uiAcc, uiHora, tsRaw) {
  const uiColors = uiAcc.map(v =>
    v>=150?'rgba(124,58,237,.8)':v>=100?'rgba(239,68,68,.8)':
    v>=50?'rgba(245,158,11,.8)':'rgba(34,197,94,.8)');
    
  let anns = {
    ll50:{type:'line',yMin:50,yMax:50,borderColor:'rgba(245,158,11,.4)',borderWidth:1,borderDash:[4,4]},
    ll100:{type:'line',yMin:100,yMax:100,borderColor:'rgba(239,68,68,.5)',borderWidth:1,borderDash:[4,4]},
    ll150:{type:'line',yMin:150,yMax:150,borderColor:'rgba(124,58,237,.5)',borderWidth:1.5,borderDash:[4,4]}
  };
  
  if (ALL.tractaments && tsRaw) {
    let boxId = 0;
    ALL.tractaments.forEach(t => {
      if (t.malalties && t.malalties.includes('oidio')) {
        let tDate = new Date(t.data);
        let info = getProtectionInfo(t, tsRaw, ALL.pluja, ALL.temps);
        let tEnd = info.endDate;
        
        let startIdx = -1;
        let endIdx = -1;
        
        for (let i = 0; i < tsRaw.length; i++) {
          let currDate = new Date(tsRaw[i]);
          if (startIdx === -1 && currDate >= tDate) startIdx = i;
          if (currDate <= tEnd) endIdx = i;
          else if (currDate > tEnd) break;
        }
        
        if (startIdx !== -1 && endIdx !== -1 && startIdx <= endIdx) {
          let labelText = `Vinya Protegida (${t.dies_proteccio || 10} d)`;
          if (info.degraded) labelText = `Prot. trencada (${info.reason})`;
          
          anns['protBox' + boxId] = {
            type: 'box',
            xMin: L[startIdx],
            xMax: L[endIdx],
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
            borderWidth: 1,
            borderColor: 'rgba(34, 197, 94, 0.8)',
            label: {
              content: labelText,
              display: true,
              position: 'start',
              color: 'rgba(34, 197, 94, 0.9)',
              font: {size: 10, weight: 'bold'}
            }
          };
          boxId++;
        }
      }
    });
  }

  return new Chart(document.getElementById('chart-ui'), {
    type:'line',
    data:{labels:L, datasets:[
      {label:'UI acumulades', data:uiAcc, borderColor:'#a78bfa', borderWidth:2,
       pointRadius:2, pointBackgroundColor:uiColors,
       fill:true, backgroundColor:'rgba(167,139,250,.08)', tension:.2},
      {label:'UI horàries', data:uiHora, type:'bar',
       backgroundColor:'rgba(167,139,250,.25)',
       borderColor:'rgba(167,139,250,.5)', borderWidth:1, yAxisID:'yUH'}
    ]},
    options:{...cfgBase(),
      plugins:{...cfgBase().plugins,
        legend:{display:true, labels:{color:'#9ca3af',font:{size:11}}},
        annotation:{annotations:anns}
      },
      scales:{x:cfgBase().scales.x,
        y:{...cfgBase().scales.y, min:0,
           title:{display:true,text:'UI acum.',color:'#a78bfa',font:{size:10}}},
        yUH:{...cfgBase().scales.y, position:'right', min:0,
             title:{display:true,text:'UI/h',color:'rgba(167,139,250,.6)',font:{size:10}},
             grid:{drawOnChartArea:false}}
      }
    }
  });
}
function createRiscMildiuChart(L, riscData) {
  const colors = riscData.map(v =>
    v>=4?'rgba(124,58,237,.8)':v>=3?'rgba(239,68,68,.8)':
    v>=2?'rgba(249,115,22,.8)':v>=1?'rgba(245,158,11,.8)':'rgba(107,114,128,.4)');
  return new Chart(document.getElementById('chart-mildiu'), {
    type:'bar',
    data:{labels:L, datasets:[{
      label:'Risc mildiu', data:riscData,
      backgroundColor:colors,
      borderColor:colors.map(c=>c.replace(/,\\.8\\)/,',1)').replace(/,\\.4\\)/,',1)')),
      borderWidth:1
    }]},
    options:{...cfgBase(),
      scales:{x:cfgBase().scales.x,
        y:{...cfgBase().scales.y, min:0, max:4,
           ticks:{stepSize:1, callback:v=>['Inact.','Vigil.','Prim.','Sec.','Alt'][v]||v,
                  color:'#6b7280',font:{size:10}},
           title:{display:true,text:'Nivell',color:'#9ca3af',font:{size:10}}}}
    }
  });
}
"""

JS_TRACTAMENTS = r"""
const FITXER = 'tractaments.json';
document.getElementById('gh-token').value = localStorage.getItem('gh_token') || '';
document.getElementById('gh-repo').value  = localStorage.getItem('gh_repo')  || '';
const ara = new Date();
ara.setMinutes(ara.getMinutes() - ara.getTimezoneOffset());
document.getElementById('inp-data').value = ara.toISOString().slice(0,16);
function token() { return localStorage.getItem('gh_token') || ''; }
function repo()  { return localStorage.getItem('gh_repo')  || ''; }
function toast(msg, ok=true) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast ' + (ok ? 'ok' : 'err');
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3000);
}
async function llegirFitxer() {
  if (!token() || !repo()) return { tractaments: [] };
  try {
    const r = await fetch(
      `https://api.github.com/repos/${repo()}/contents/${FITXER}`,
      { headers: { Authorization: `Bearer ${token()}`, Accept: 'application/vnd.github+json' } });
    if (r.status === 404) return { tractaments: [] };
    const data = await r.json();
    const contingut = JSON.parse(atob(data.content.replace(/\n/g,'')));
    contingut._sha = data.sha;
    return contingut;
  } catch(e) {
    toast('Error llegint tractaments.json: ' + e.message, false);
    return { tractaments: [] };
  }
}
async function guardarFitxer(dades) {
  if (!token() || !repo()) { toast('Configura el token i el repositori primer', false); return false; }
  const sha = dades._sha; delete dades._sha;
  dades._instruccions = "Afegeix un registre per cada tractament.";
  const cos = { message: `tractament: ${new Date().toISOString().slice(0,10)}`,
    content: btoa(unescape(encodeURIComponent(JSON.stringify(dades, null, 2)))) };
  if (sha) cos.sha = sha;
  try {
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FITXER}`,
      { method:'PUT', headers:{ Authorization:`Bearer ${token()}`,
        Accept:'application/vnd.github+json','Content-Type':'application/json'},
        body:JSON.stringify(cos) });
    return r.ok;
  } catch(e) { toast('Error guardant: ' + e.message, false); return false; }
}
const PRODUCTES_DB = {
  'sofre_pols': {nom: 'Sofre en pols', eco: true, dies: 7, malalties: ['oidio']},
  'sofre_mullable': {nom: 'Sofre mullable 80%', eco: true, dies: 10, malalties: ['oidio']},
  'triazol': {nom: 'Triazol (ex. Difenoconazol, Miclobutanil)', eco: false, dies: 14, malalties: ['oidio', 'blackrot']},
  'caldo_bordeles': {nom: 'Caldo Bordelès / Sals de coure', eco: true, dies: 10, malalties: ['mildiu', 'blackrot']},
  'metalaxil': {nom: 'Sistèmic (Metalaxil + Mancozeb)', eco: false, dies: 14, malalties: ['mildiu']},
  'cimoxanil': {nom: 'Penetrant (Cimoxanil)', eco: false, dies: 10, malalties: ['mildiu']},
  'bacillus': {nom: 'Bacillus subtilis', eco: true, dies: 7, malalties: ['botritis']},
  'switch': {nom: 'Switch (Ciprodinil + Fludioxonil)', eco: false, dies: 14, malalties: ['botritis']},
  'altre': {nom: 'Altre producte (Introduir a notes)', eco: false, dies: 10, malalties: ['oidio', 'mildiu', 'botritis', 'blackrot']}
};

function actualitzarSelectorProductes() {
  const malaltiesSelec = [];
  ['oidio','mildiu','botritis','blackrot'].forEach(m => {
    const cb = document.getElementById('cb-' + m);
    if (cb && cb.checked) malaltiesSelec.push(m);
  });
  
  const sel = document.getElementById('inp-producte');
  sel.innerHTML = '<option value="">-- Selecciona un producte --</option>';
  
  if (malaltiesSelec.length === 0) {
    sel.innerHTML = '<option value="">-- Selecciona les malalties primer --</option>';
    actualitzarInfoProducte();
    return;
  }
  
  Object.keys(PRODUCTES_DB).forEach(k => {
    const p = PRODUCTES_DB[k];
    const faMatch = malaltiesSelec.some(m => p.malalties.includes(m));
    if (faMatch) {
      const opt = document.createElement('option');
      opt.value = k;
      opt.textContent = p.nom;
      sel.appendChild(opt);
    }
  });
  actualitzarInfoProducte();
}

function actualitzarInfoProducte() {
  const sel = document.getElementById('inp-producte');
  const ecoBadge = document.getElementById('info-eco');
  const noEcoBadge = document.getElementById('info-no-eco');
  const diesLabel = document.getElementById('info-dies');
  const divAltre = document.getElementById('div-altre-eco');
  
  if (!sel.value || sel.value === '') {
    ecoBadge.style.display = 'none';
    noEcoBadge.style.display = 'none';
    diesLabel.style.display = 'none';
    divAltre.style.display = 'none';
    return;
  }
  
  const p = PRODUCTES_DB[sel.value];
  if (p) {
    let isEco = p.eco;
    
    if (sel.value === 'altre') {
      divAltre.style.display = 'block';
      isEco = document.getElementById('inp-altre-eco').checked;
    } else {
      divAltre.style.display = 'none';
    }
    
    if (isEco) {
      ecoBadge.style.display = 'inline';
      noEcoBadge.style.display = 'none';
    } else {
      ecoBadge.style.display = 'none';
      noEcoBadge.style.display = 'inline';
    }
    diesLabel.style.display = 'inline';
    diesLabel.textContent = `Protecció est.: ${p.dies} dies`;
  }
}

async function afegirTractament() {
  const data = document.getElementById('inp-data').value;
  const prodKey = document.getElementById('inp-producte').value;
  const dosi = document.getElementById('inp-dosi').value.trim();
  const notes = document.getElementById('inp-notes').value.trim();
  
  if (!data || !prodKey) { toast('La data i el producte són obligatoris', false); return; }
  
  const p = PRODUCTES_DB[prodKey];
  let isEco = p.eco;
  if (prodKey === 'altre') {
    isEco = document.getElementById('inp-altre-eco').checked;
  }
  
  const malalties = [];
  ['oidio','mildiu','botritis','blackrot'].forEach(m => {
    const cb = document.getElementById('cb-' + m);
    if (cb && cb.checked) malalties.push(m);
  });
  
  if (malalties.length === 0) { toast('Selecciona almenys una malaltia', false); return; }
  
  const nou = { 
    data: data, 
    producte: p.nom, 
    malalties: malalties, 
    dosi: dosi, 
    notes: notes,
    ecologic: isEco,
    dies_proteccio: p.dies
  };
  
  const dades = await llegirFitxer();
  dades.tractaments = dades.tractaments || [];
  dades.tractaments.push(nou);
  dades.tractaments.sort((a,b) => a.data.localeCompare(b.data));
  const ok = await guardarFitxer(dades);
  if (ok) {
    toast("Tractament guardat!");
    document.getElementById('inp-producte').value = '';
    document.getElementById('inp-dosi').value = '';
    document.getElementById('inp-notes').value = '';
    actualitzarInfoProducte();
    renderLlista(dades.tractaments);
    setTimeout(() => window.location.reload(), 800);
  } else { toast("No s'ha pogut guardar. Comprova el token i el repositori.", false); }
}

async function eliminarTractament(idx) {
  if (!confirm('Eliminar aquest tractament?')) return;
  const dades = await llegirFitxer();
  dades.tractaments.splice(idx, 1);
  const ok = await guardarFitxer(dades);
  if (ok) { 
    toast('Tractament eliminat'); 
    renderLlista(dades.tractaments); 
    setTimeout(() => window.location.reload(), 800);
  }
}
function renderLlista(tractaments) {
  const el = document.getElementById('llista-tractaments');
  const filtrats = tractaments.filter(t => t.malalties && t.malalties.includes(MALALTIA_FILTRE));
  if (!filtrats.length) {
    el.innerHTML = '<div class="empty">Cap tractament registrat per a aquesta malaltia</div>'; return;
  }
  const origIndices = [];
  tractaments.forEach((t, i) => {
    if (t.malalties && t.malalties.includes(MALALTIA_FILTRE)) origIndices.push(i);
  });
  const bc = {oidio:'t-badge-oidio',mildiu:'t-badge-mildiu',botritis:'t-badge-botritis',blackrot:'t-badge-blackrot'};
  el.innerHTML = [...filtrats].reverse().map((t, i) => {
    const idxReal = origIndices[filtrats.length - 1 - i];
    const d = new Date(t.data).toLocaleDateString('ca-ES',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
    const badges = (t.malalties||[]).map(m => `<span class="t-badge ${bc[m]||''}">${m}</span>`).join('');
    let ecoBadge = "";
    if (t.ecologic === true) {
      ecoBadge = '<span class="t-badge" style="background:rgba(34,197,94,0.15);color:var(--verd);">🍃 Eco</span>';
    } else if (t.ecologic === false) {
      ecoBadge = '<span class="t-badge" style="background:rgba(239,68,68,0.15);color:var(--vermell);">🧪 Convencional</span>';
    }
    const diesTxt = t.dies_proteccio ? ` (${t.dies_proteccio} dies)` : '';
    return `<div class="tractament-item"><div>
      <div class="t-data">${d} — ${t.producte}${diesTxt} ${ecoBadge}</div>
      <div class="t-producte">${t.dosi||''}${t.notes ? ' · '+t.notes : ''}</div>
      <div class="t-badges">${badges}</div></div>
      <button class="btn btn-danger" onclick="eliminarTractament(${idxReal})">Eliminar</button></div>`;
  }).join('');
}
(async () => {
  const dades = await llegirFitxer();
  renderLlista(dades.tractaments);
  if (token() && repo()) document.getElementById('config-section').style.display = 'none';
})();
"""

JS_FASE_KAST = r"""
const FASE_FILE = 'fase_fenologica.json';
const MULTIPLIERS = {
  1: 1.0,
  2: 1.3,
  3: 1.0,
  4: 0.4,
  5: 0.0
};

async function llegirFase() {
  if (!token() || !repo()) return 1;
  try {
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FASE_FILE}`,
      { headers: { Authorization: `Bearer ${token()}`, Accept: 'application/vnd.github+json' } });
    if (r.status === 404) return 1;
    const data = await r.json();
    const contingut = JSON.parse(atob(data.content.replace(/\n/g,'')));
    window._faseSha = data.sha;
    return contingut.fase || 1;
  } catch(e) { return 1; }
}

async function guardarFaseRepo(faseVal) {
  if (!token() || !repo()) { toast('Configura el token a Tractaments primer', false); return; }
  const cos = { 
    message: `fase fenologica: ${faseVal}`,
    content: btoa(JSON.stringify({fase: parseInt(faseVal), data: new Date().toISOString()}))
  };
  if (window._faseSha) cos.sha = window._faseSha;
  try {
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FASE_FILE}`,
      { method:'PUT', headers:{ Authorization:`Bearer ${token()}`,
        Accept:'application/vnd.github+json','Content-Type':'application/json'},
        body:JSON.stringify(cos) });
    if (r.ok) {
       const data = await r.json();
       window._faseSha = data.content.sha;
       toast("Fase fenològica actualitzada");
    } else {
       toast("Error guardant fase", false);
    }
  } catch(e) { toast('Error guardant fase', false); }
}

function updateKastRisk(faseVal) {
  const currentFase = parseInt(faseVal);
  const mult = MULTIPLIERS[currentFase];
  const uiAct = ALL.ui_acc[ALL.ui_acc.length - 1] || 0;
  const uiKast = uiAct * mult;
  
  let riscKast = "BAIX";
  let colorKast = "#22c55e";
  if (uiKast >= 150) { riscKast = "MOLT ALT"; colorKast = "#7c3aed"; }
  else if (uiKast >= 100) { riscKast = "ALT"; colorKast = "#ef4444"; }
  else if (uiKast >= 50) { riscKast = "MODERAT"; colorKast = "#f59e0b"; }
  
  // Check if protected by a recent treatment
  let isProtected = false;
  let strDataFi = "";
  let recBoxText = "";
  if (ALL.tractaments && ALL.ts_raw && ALL.ts_raw.length > 0) {
    const lastDate = new Date(ALL.ts_raw[ALL.ts_raw.length - 1]);
    ALL.tractaments.forEach(t => {
      if (t.malalties && t.malalties.includes('oidio')) {
        let tDate = new Date(t.data);
        let info = getProtectionInfo(t, ALL.ts_raw, ALL.pluja, ALL.temps);
        let tEnd = info.endDate;
        if (lastDate >= tDate && lastDate <= tEnd) {
           isProtected = true;
           strDataFi = tEnd.toLocaleDateString('ca-ES', {day:'2-digit', month:'2-digit', year:'numeric'});
           if (info.degraded) {
              recBoxText = `Protecció degradada per clima (${info.reason})`;
           }
        }
      }
    });
  }

  if (isProtected) {
    document.getElementById('kast-val').innerText = "PROTEGIT";
    document.getElementById('kast-val').style.color = "#22c55e";
    document.getElementById('kast-ui').innerText = "Fins al " + strDataFi;
  } else {
    document.getElementById('kast-val').innerText = riscKast;
    document.getElementById('kast-val').style.color = colorKast;
    document.getElementById('kast-ui').innerText = uiKast.toFixed(0) + " UI (Ajustat per edat)";
  }
  
  const recomBox = document.getElementById('oidi-recom-box');
  
  if (isProtected) {
     let warnHtml = recBoxText ? `<p style="color:#f59e0b; margin-top:4px;"><b>Atenció:</b> ${recBoxText}</p>` : "";
     recomBox.innerHTML = `
<div class="recom-box info" style="margin-bottom:0; background: rgba(34, 197, 94, 0.1); border-color: rgba(34, 197, 94, 0.3);">
  <div class="recom-icon" style="color: #22c55e">🛡️</div>
  <div class="recom-content">
    <h4 style="color: #22c55e">Vinya Protegida (Fins al ${strDataFi})</h4>
    <p>Has registrat un tractament recent d'oïdi. Durant els pròxims dies, la vinya està blindada i s'ignora l'índex climàtic.</p>
    ${warnHtml}
  </div>
</div>`;
  } else if (currentFase === 5) {
     recomBox.innerHTML = `
<div class="recom-box info" style="margin-bottom:0">
  <div class="recom-icon">🛡️</div>
  <div class="recom-content">
    <h4>Resistència Ontogènica Activa (Model Kast)</h4>
    <p>La vinya està en Envero/Maduració. Els raïms ja tenen suficient sucre i són pràcticament immunes a noves infeccions d'oïdi. El risc pel fruit és NUL, tot i el risc climàtic.</p>
  </div>
</div>`;
  } else if (uiKast >= 100) {
     recomBox.innerHTML = `
<div class="recom-box warning" style="margin-bottom:0">
  <div class="recom-icon">⚠️</div>
  <div class="recom-content">
    <h4>Tractament recomanat (Risc Kast ${riscKast})</h4>
    <p>El risc ajustat per edat indica perill greu d'infecció al raïm. Es recomana un tractament immediat.</p>
    <ul>
      <li><strong>Sofre en pols:</strong> 20-30 kg/ha. (Evitar si T > 30°C).</li>
      <li><strong>Sofre mullable:</strong> Dosi al 0.25-0.75%.</li>
      <li><strong>Sistèmics/Penetrants:</strong> Triazols alternant famílies.</li>
    </ul>
  </div>
</div>`;
  } else {
     recomBox.innerHTML = `
<div class="recom-box" style="margin-bottom:0">
  <div class="recom-icon">✅</div>
  <div class="recom-content">
    <h4>Risc sota control</h4>
    <p>Un tractament recent, l'edat de la planta o el clima mantenen el risc d'oïdi a ratlla. L'índex de risc es mantindrà a 0 durant el període de protecció.</p>
  </div>
</div>`;
  }
}

async function canviFase(val) {
  updateKastRisk(val);
  await guardarFaseRepo(val);
}

// Init
(async () => {
  const sel = document.getElementById('sel-fase');
  if(sel) {
     const f = await llegirFase();
     sel.value = f;
     updateKastRisk(f);
  }
})();
"""

# ═════════════════════════════════════════════════════════════════════════════
#  CÀRREGA DE DADES
# ═════════════════════════════════════════════════════════════════════════════

def carregar_dades() -> pd.DataFrame:
    """Llegeix historial.csv i fusiona dades de mildiu si existeixen."""
    df = pd.read_csv(CSV_HISTORIAL)
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    limit = df["ts"].max() - pd.Timedelta(days=14)
    df = df[df["ts"] >= limit].copy()

    if os.path.exists(CSV_MILDIU):
        dm = pd.read_csv(CSV_MILDIU)
        cols_mildiu = ["timestamp", "pluja_10d_mm", "t_mitjana_10d",
                       "hores_hr95", "condicio_primaria", "condicio_secundaria",
                       "graus_dia_inc", "dies_incubacio_est", "risc_mildiu"]
        cols_ok = [c for c in cols_mildiu if c in dm.columns]
        df = pd.merge(df, dm[cols_ok], on="timestamp", how="left")

    return df


# ═════════════════════════════════════════════════════════════════════════════
#  COMPONENTS HTML REUTILITZABLES
# ═════════════════════════════════════════════════════════════════════════════

def generar_head(titol: str, amb_charts: bool = True, amb_mapa: bool = False) -> str:
    charts_scripts = ""
    if amb_charts:
        charts_scripts = ('\n  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0'
                          '/dist/chart.umd.min.js"></script>'
                          '\n  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin'
                          '-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>')
    map_scripts = ""
    if amb_mapa:
        map_scripts = ('\n  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>'
                       '\n  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')

    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titol}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">{charts_scripts}{map_scripts}
  <style>{CSS}</style>
</head>"""

# Estructura de navegació multi-cultiu
# Cada element pot ser:
#   ("id", "href", "label")                          → link simple
#   ("id", "href", "label", [sublinks...])           → desplegable
NAV_ITEMS = [
    ("index", "index.html", "Inici"),
    ("vinya", "vinya.html", "Vinya", [
        ("vinya",    "vinya.html",    "Resum"),
        ("oidi",     "oidi.html",     "Oïdi"),
        ("mildiu",   "mildiu.html",   "Mildiu"),
        ("botritis", "botritis.html", "Botritis"),
        ("blackrot", "blackrot.html", "Black Rot"),
    ]),
    ("cirerers",  None, "Cirerers"),
    ("pistatxo",  None, "Pistatxo"),
]

# Tots els IDs que pertanyen al grup "vinya"
VINYA_GROUP = {"vinya", "oidi", "mildiu", "botritis", "blackrot"}

def generar_navbar(pagina_activa: str) -> str:
    links = []
    for item in NAV_ITEMS:
        pid, href, label = item[0], item[1], item[2]
        children = item[3] if len(item) > 3 else None

        if children:
            # Dropdown
            is_group_active = pagina_activa in {c[0] for c in children}
            toggle_cls = "nav-dropdown-toggle active" if is_group_active else "nav-dropdown-toggle"
            sub_links = []
            for cid, chref, clabel in children:
                ccls = "active" if cid == pagina_activa else ""
                sub_links.append(f'<a href="{chref}" class="{ccls}">{clabel}</a>')
            sub_html = "\n        ".join(sub_links)
            links.append(f"""<div class="nav-dropdown" onclick="this.classList.toggle('open')">
      <button class="{toggle_cls}">{label} <span class="chevron">▼</span></button>
      <div class="nav-dropdown-menu">
        {sub_html}
      </div>
    </div>""")
        elif href:
            cls = "nav-link active" if pid == pagina_activa else "nav-link"
            links.append(f'<a href="{href}" class="{cls}">{label}</a>')
        else:
            # Placeholder (sense pàgina encara)
            links.append(f'<span class="nav-link" style="opacity:.45;cursor:default" title="Properament">{label}</span>')

    links_html = "\n    ".join(links)
    return f"""<nav class="navbar">
  <a href="index.html" class="nav-brand">🌿 Son Nadal</a>
  <div class="nav-links">
    {links_html}
    <button id="theme-btn" class="theme-toggle" onclick="toggleTheme()" title="Canviar tema">🌙</button>
  </div>
</nav>"""


def generar_footer() -> str:
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<footer>
  Son Nadal (RC0039468) · 39.5146, 3.15405 ·
  Actualitzat: {ts} ·
  Oïdi: Gubler (1995) · Mildiu: Model EPI + regla 3×10 (Goidanich)
</footer>"""


def generar_filtre_bar() -> str:
    return """<div class="filter-bar">
  <button class="filter-btn" data-range="24h" onclick="setFilter('24h')">24h</button>
  <button class="filter-btn" data-range="3d" onclick="setFilter('3d')">3 dies</button>
  <button class="filter-btn active" data-range="7d" onclick="setFilter('7d')">7 dies</button>
  <button class="filter-btn" data-range="14d" onclick="setFilter('14d')">14 dies</button>
  <div class="filter-sep"></div>
  <input type="date" id="filter-date-ini" class="filter-date" title="Data inici">
  <span style="color:var(--muted);font-size:12px;">→</span>
  <input type="date" id="filter-date-fi" class="filter-date" title="Data fi">
  <button class="filter-apply" onclick="setCustomRange()">Aplicar</button>
</div>"""

def generar_chart_card(canvas_id: str, titol: str, descripcio: str, style: str = "") -> str:
    """Genera una targeta de gràfic estàndard amb botó d'informació i descripció."""
    return f"""<div class="chart-card" {style}>
  <div class="chart-title">
    <span>{titol}</span>
    <button class="chart-info-btn" onclick="toggleChartInfo('desc-{canvas_id}')" title="Més informació">i</button>
  </div>
  <div id="desc-{canvas_id}" class="chart-desc">{descripcio}</div>
  <canvas id="{canvas_id}"></canvas>
</div>"""
ALL_MALALTIES = [
    ("oidio",    "Oïdi"),
    ("mildiu",   "Mildiu"),
    ("botritis", "Botritis"),
    ("blackrot", "Black Rot"),
]

def generar_tractaments_section(malaltia_id: str) -> str:
    """Genera l'HTML de la secció de tractaments amb formulari i historial."""
    checkboxes = []
    for mid, mnom in ALL_MALALTIES:
        checked = " checked" if mid == malaltia_id else ""
        disabled = " disabled" if mid == malaltia_id else ""
        checkboxes.append(
            f'<label class="checkbox-label">'
            f'<input type="checkbox" id="cb-{mid}" onchange="actualitzarSelectorProductes()"{checked}{disabled}> {mnom}</label>'
        )
    cbs = "\n      ".join(checkboxes)

    return f"""
<div class="section-title">Tractaments</div>

<div class="config-box" id="config-section">
  <strong style="color:var(--text)">Configuració GitHub (una sola vegada)</strong><br>
  Per guardar els tractaments al repositori necessites un token d'accés.<br><br>
  Token GitHub (permís <code>contents:write</code>):
  <input type="password" id="gh-token" placeholder="ghp_..."
         oninput="localStorage.setItem('gh_token',this.value)">
  Repositori (usuari/nom):
  <input type="text" id="gh-repo" placeholder="usuari/repo"
         oninput="localStorage.setItem('gh_repo',this.value)">
  <div style="margin-top:8px;font-size:11px">
    El token es guarda localment al navegador.
    GitHub → Settings → Developer settings → Personal access tokens → Fine-grained →
    <code>Contents: Read and write</code>.
  </div>
</div>

<div class="card" style="margin-bottom:20px;">
  <div class="card-title">Registrar tractament</div>
  <div style="margin-top:16px;">
    <label>Data i hora del tractament</label>
    <input type="datetime-local" id="inp-data">
    
    <label style="margin-top:12px;">Malalties tractades</label>
    <div class="checkbox-group">
        {cbs}
    </div>

    <label style="margin-top:12px; display:flex; align-items:center; flex-wrap:wrap;">
      Producte aplicat
      <span id="info-eco" style="display:none; color:var(--verd); font-size:12px; font-weight:bold; margin-left:8px; background:rgba(34,197,94,0.1); padding:2px 6px; border-radius:4px;">🍃 Ecològic</span>
      <span id="info-no-eco" style="display:none; color:var(--vermell); font-size:12px; font-weight:bold; margin-left:8px; background:rgba(239,68,68,0.1); padding:2px 6px; border-radius:4px;">🧪 Convencional</span>
      <span id="info-dies" style="display:none; color:var(--muted); font-size:12px; margin-left:8px;"></span>
    </label>
    <select id="inp-producte" onchange="actualitzarInfoProducte()">
       <option value="">-- Selecciona les malalties primer --</option>
    </select>
    
    <div id="div-altre-eco" style="display:none; margin-top:8px;">
       <label class="checkbox-label" style="font-size:13px; color:var(--text);">
         <input type="checkbox" id="inp-altre-eco" onchange="actualitzarInfoProducte()"> Aquest producte és ecològic?
       </label>
    </div>

    <label style="margin-top:12px;">Dosi</label>
    <input type="text" id="inp-dosi" placeholder="3 kg/ha, 2 L/ha...">

    <label style="margin-top:12px;">Notes (opcional)</label>
    <textarea id="inp-notes" placeholder="Condicions, observacions..."></textarea>
    <div class="actions">
      <button class="btn btn-primary" onclick="afegirTractament()">Guardar tractament</button>
    </div>
  </div>
</div>

<div class="card">
  <div class="card-title">Historial de tractaments</div>
  <div id="llista-tractaments"><div class="empty">Carregant...</div></div>
</div>

<div class="toast" id="toast"></div>
"""


def generar_recomanacio_tractament(malaltia: str, risc: str = None) -> str:
    """Genera la caixa de recomanació de tractament segons la malaltia i el nivell de risc."""
    
    if malaltia == "oidi":
        if risc in ["alt", "molt alt"]:
            return """
<div class="recom-box warning">
  <div class="recom-icon">⚠️</div>
  <div class="recom-content">
    <h4>Tractament recomanat (Risc Alt/Molt Alt)</h4>
    <p>El risc d'infecció per oïdi és elevat. Es recomana un tractament immediat per protegir els òrgans verds i especialment els raïms (des de floració a envero).</p>
    <ul>
      <li><strong>Sofre en pols:</strong> 20-30 kg/ha. Efectiu si les temperatures són suaus (ull amb cremades si T > 30°C).</li>
      <li><strong>Sofre mullable:</strong> Dosi al 0.25-0.75%. Bona cobertura.</li>
      <li><strong>Sistèmics/Penetrants:</strong> Triazols (ex: Tetraconazol, Difenoconazol) o estrobilurines si la pressió és molt alta. (Recordar alternar famílies).</li>
    </ul>
  </div>
</div>"""
        else:
            return """
<div class="recom-box">
  <div class="recom-icon">🛡️</div>
  <div class="recom-content">
    <h4>Risc sota control</h4>
    <p>Actualment les condicions no són altament favorables per a l'oïdi segons el model Gubler. Mantingues l'estratègia preventiva habitual, especialment si t'apropes a la floració o al quallat.</p>
  </div>
</div>"""

    elif malaltia == "mildiu":
        if risc in ["primari", "secundari", "alt"]:
            return """
<div class="recom-box warning">
  <div class="recom-icon">⚠️</div>
  <div class="recom-content">
    <h4>Tractament recomanat (Risc d'infecció)</h4>
    <p>S'han complert les condicions per a infeccions de mildiu. Si no hi ha protecció prèvia vigent, es recomana tractar.</p>
    <ul>
      <li><strong>Fungicides de contacte:</strong> Productes cúprics (ex. Caldo Bordelès) actuen com a barrera. Es renten si plou > 15-20 mm.</li>
      <li><strong>Fungicides penetrants/sistèmics:</strong> Recomanats si l'infecció ja ha començat (1-2 dies d'incubació). Màxim 2-3 aplicacions per campanya per evitar resistències.</li>
      <li><em>Nota:</em> Consultar registres actualitzats per Mancozeb / Folpet / Cimoxanilo segons la normativa vigent.</li>
    </ul>
  </div>
</div>"""
        else:
             return """
<div class="recom-box">
  <div class="recom-icon">🛡️</div>
  <div class="recom-content">
    <h4>Risc baix / en vigilància</h4>
    <p>Les condicions actuals no presenten un risc immediat d'infecció de mildiu. Vigila l'evolució de les previsions de pluja (>10mm) i temperatura (>10°C).</p>
  </div>
</div>"""

    elif malaltia == "botritis":
        return """
<div class="recom-box info">
  <div class="recom-icon">ℹ️</div>
  <div class="recom-content">
    <h4>Estratègia de tractament (Botritis)</h4>
    <p>L'estratègia clau és preventiva en moments crítics: final de floració, tancament del raïm i inici de l'envero.</p>
    <ul>
      <li><strong>Matèries actives:</strong> Fenhexamid (1.2-1.5 kg/ha), Ciprodinil + Fludioxonil (Switch 60-100 g/hl).</li>
      <li>Alternar productes per evitar resistències.</li>
      <li>Controlar focus d'oïdi i corc del raïm (Lobesia), ja que les ferides afavoreixen la botritis.</li>
    </ul>
  </div>
</div>"""

    elif malaltia == "blackrot":
        return """
<div class="recom-box info">
  <div class="recom-icon">ℹ️</div>
  <div class="recom-content">
    <h4>Estratègia de tractament (Black Rot)</h4>
    <p>Control principalment preventiu des que es fan visibles les inflorescències fins al tancament del raïm.</p>
    <ul>
      <li><strong>Tractaments:</strong> Triazols (ex: Miclobutanil) o ditiocarbamats (consultar estat del registre de Mancozeb/Metiram).</li>
      <li>Són vitals les pràctiques culturals: eliminar i cremar raïms momificats i sarments infectats de l'any anterior on hiverna el fong.</li>
    </ul>
  </div>
</div>"""
    
    return ""


# ═════════════════════════════════════════════════════════════════════════════
#  PREPARACIÓ DE DADES PER A GRÀFIQUES
# ═════════════════════════════════════════════════════════════════════════════

def calc_Ra(day_of_year: int, lat_deg: float) -> float:
    lat_rad = math.radians(lat_deg)
    delta = 0.409 * math.sin((2 * math.pi * day_of_year / 365.0) - 1.39)
    ws = math.acos(-math.tan(lat_rad) * math.tan(delta))
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365.0)
    Ra_MJ = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(lat_rad) * math.sin(delta) +
        math.cos(lat_rad) * math.cos(delta) * math.sin(ws)
    )
    return Ra_MJ / 2.45

def calc_ET0_hargreaves(tmin, tmax, tmean, doy, lat=39.5146):
    Ra = calc_Ra(doy, lat)
    tdiff = max(tmax - tmin, 0)
    et0 = 0.0023 * (tmean + 17.8) * math.sqrt(tdiff) * Ra
    return max(et0, 0)


def preparar_dades_json(df: pd.DataFrame) -> str:
    """Prepara totes les sèries de dades com a JSON per a les gràfiques."""
    labels  = df["ts"].dt.strftime("%d/%m %H:%M").tolist()
    ts_raw  = df["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    temps   = pd.to_numeric(df["temperatura_c"],   errors="coerce").round(1).tolist()
    humitat = pd.to_numeric(df["humitat_pct"],     errors="coerce").round(1).tolist()
    pluja   = pd.to_numeric(df["precipitacio_mm"], errors="coerce").round(1).tolist()
    ui_hora = pd.to_numeric(df.get("ui_horaria",    pd.Series([0]*len(df))), errors="coerce").round(1).tolist()
    ui_acc  = pd.to_numeric(df.get("ui_acumulades", pd.Series([0]*len(df))), errors="coerce").round(1).tolist()
    
    rad_solar = pd.to_numeric(df.get("radiacio_solar_wm2", pd.Series([None]*len(df))), errors="coerce").round(1).tolist()
    uv_index  = pd.to_numeric(df.get("index_uv", pd.Series([None]*len(df))), errors="coerce").round(1).tolist()

    risc_mildiu_data = pd.to_numeric(
        df.get("risc_mildiu", pd.Series(dtype=str)).map(
            {"inactiu":0, "vigilancia":1, "primari":2, "secundari":3, "alt":4}
        ).fillna(0), errors="coerce"
    ).tolist() if "risc_mildiu" in df.columns else [0]*len(labels)

    tractaments_data = []
    import os
    if os.path.exists("tractaments.json"):
        import json as j
        try:
            with open("tractaments.json", "r", encoding="utf-8") as f:
                t_json = j.load(f)
                tractaments_data = t_json.get("tractaments", [])
        except Exception:
            pass

    parceles_data = []
    if os.path.exists("parceles.json"):
        import json as j
        try:
            with open("parceles.json", "r", encoding="utf-8") as f:
                p_json = j.load(f)
                parceles_data = p_json.get("parceles", [])
        except Exception:
            pass

    # Daily aggregation for ET0 and Water Balance
    df_daily = df.copy()
    df_daily['date'] = df_daily['ts'].dt.date
    df_daily['doy'] = df_daily['ts'].dt.dayofyear
    
    daily_data = {"labels": [], "et0": [], "pluja": [], "balanc": [], "gdd": [], "gdd_acc": [], "fred": [], "fred_acc": []}
    balanc_acumulat = 0.0
    gdd_acumulat = 0.0
    fred_acumulat = 0.0
    
    for date, group in df_daily.groupby('date'):
        tmin = group['temperatura_c'].min()
        tmax = group['temperatura_c'].max()
        tmean = group['temperatura_c'].mean()
        pluja_dia = group['precipitacio_mm'].sum()
        doy = group['doy'].iloc[0]
        
        # ET0 & Balanç
        et0 = calc_ET0_hargreaves(tmin, tmax, tmean, doy)
        balanc_acumulat += (pluja_dia - et0)
        
        # GDD (Base 10)
        gdd = max(tmean - 10.0, 0)
        gdd_acumulat += gdd
        
        # Hores de fred (< 7ºC, 30 min per registre)
        hores_fred_dia = (group['temperatura_c'] < 7.0).sum() * 0.5
        fred_acumulat += hores_fred_dia
        
        daily_data["labels"].append(date.strftime("%d/%m"))
        daily_data["et0"].append(round(et0, 2))
        daily_data["pluja"].append(round(pluja_dia, 2))
        daily_data["balanc"].append(round(balanc_acumulat, 2))
        daily_data["gdd"].append(round(gdd, 1))
        daily_data["gdd_acc"].append(round(gdd_acumulat, 1))
        daily_data["fred"].append(round(hores_fred_dia, 1))
        daily_data["fred_acc"].append(round(fred_acumulat, 1))

    return json.dumps({
        "labels":           labels,
        "ts_raw":           ts_raw,
        "temps":            temps,
        "humitat":          humitat,
        "pluja":            pluja,
        "ui_hora":          ui_hora,
        "ui_acc":           ui_acc,
        "rad_solar":        rad_solar,
        "uv_index":         uv_index,
        "risc_mildiu_data": risc_mildiu_data,
        "tractaments":      tractaments_data,
        "parceles":         parceles_data,
        "daily":            daily_data,
    })


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: INDEX  (dashboard global de finca)
# ═════════════════════════════════════════════════════════════════════════════

def calcular_hores_fred(df: pd.DataFrame, llindar: float = 7.0) -> float:
    """Calcula les hores de fred (T < llindar) a partir de registres cada 30 min."""
    temps = pd.to_numeric(df["temperatura_c"], errors="coerce")
    registres_freds = (temps < llindar).sum()
    # Cada registre = 30 min → dividir per 2 per obtenir hores
    return registres_freds * 0.5

def generar_index(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")

    # KPIs globals
    t_act  = pd.to_numeric(ultima.get("temperatura_c"), errors="coerce")
    hr_act = pd.to_numeric(ultima.get("humitat_pct"),   errors="coerce")
    pluja_total = pd.to_numeric(df["precipitacio_mm"], errors="coerce").sum()
    hores_fred = calcular_hores_fred(df)
    t_min = pd.to_numeric(df["temperatura_c"], errors="coerce").min()
    t_max = pd.to_numeric(df["temperatura_c"], errors="coerce").max()

    # Risc oïdi i mildiu (per a la targeta de vinya)
    risc_oidi = str(ultima.get("risc_gubler", "baix"))
    color_oidi = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828","molt alt":"#6a1b9a"}.get(risc_oidi, "#7a7269")
    risc_mildiu = str(ultima.get("risc_mildiu", "inactiu"))
    color_mildiu = {"inactiu":"#7a7269","vigilancia":"#c77d00","primari":"#d45e0a",
                    "secundari":"#c62828","alt":"#6a1b9a"}.get(risc_mildiu, "#7a7269")

    # Rang de dates
    data_ini = df["ts"].min().strftime("%d/%m/%Y")
    data_fi  = df["ts"].max().strftime("%d/%m/%Y")

    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Son Nadal · Finca", amb_mapa=True))
    parts.append("<body>")
    parts.append(generar_navbar("index"))
    parts.append("<main>")

    # Capçalera
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>Finca Son Nadal</h1>
    <div class="sub">Felanitx, Mallorca · Dades del {data_ini} al {data_fi}</div>
  </div>
  <div class="sub" style="text-align:right">{ts_act}</div>
</div>
""")

    # KPIs globals
    parts.append(f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-label">Estació Meteorològica</div>
    <div class="kpi-val" style="font-size:22px">Son Nadal</div>
    <div class="kpi-sub">ID: 117202 · Activa</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Temperatura</div>
    <div class="kpi-val">{t_act:.1f}<span class="kpi-unit">°C</span></div>
    <div class="kpi-sub">Min {t_min:.1f}° · Max {t_max:.1f}°</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Humitat relativa</div>
    <div class="kpi-val">{hr_act:.0f}<span class="kpi-unit">%</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Precipitació acumulada</div>
    <div class="kpi-val">{pluja_total:.1f}<span class="kpi-unit">mm</span></div>
    <div class="kpi-sub">Últims 14 dies</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Hores de fred</div>
    <div class="kpi-val">{hores_fred:.0f}<span class="kpi-unit">h</span></div>
    <div class="kpi-sub">T &lt; 7°C · Període disponible</div>
  </div>
</div>
""")

    # Targetes de cultiu
    parts.append(f"""
<div class="section-title" style="border-top:none;padding-top:0;margin-top:8px">Cultius</div>
<div class="crop-grid">
  <a href="vinya.html" class="crop-card">
    <span class="crop-icon">🍇</span>
    <div class="crop-name">Vinya</div>
    <div class="crop-sub">4 malalties monitorades · Models Gubler + Kast + EPI</div>
    <div class="crop-stats">
      <div class="crop-stat">
        <span><span class="dot" style="background:{color_oidi}"></span>Oïdi</span>
        <span style="color:{color_oidi};font-weight:600">{risc_oidi.upper()}</span>
      </div>
      <div class="crop-stat">
        <span><span class="dot" style="background:{color_mildiu}"></span>Mildiu</span>
        <span style="color:{color_mildiu};font-weight:600">{risc_mildiu.upper()}</span>
      </div>
      <div class="crop-stat">
        <span><span class="dot" style="background:#7a7269"></span>Botritis</span>
        <span style="color:#7a7269">Sense model</span>
      </div>
      <div class="crop-stat">
        <span><span class="dot" style="background:#7a7269"></span>Black Rot</span>
        <span style="color:#7a7269">Sense model</span>
      </div>
    </div>
    <span class="arrow">→</span>
  </a>
  <div class="crop-card" style="cursor:default">
    <span class="crop-icon">🍒</span>
    <div class="crop-name">Cirerers</div>
    <div class="crop-sub">Properament</div>
    <div class="crop-coming">El monitoratge de cirerers s'activarà quan es configurin les dades del cultiu.</div>
  </div>
  <div class="crop-card" style="cursor:default">
    <span class="crop-icon">🌰</span>
    <div class="crop-name">Pistatxo</div>
    <div class="crop-sub">Properament</div>
    <div class="crop-coming">El monitoratge de pistatxo s'activarà quan es configurin les dades del cultiu.</div>
  </div>
</div>
""")

    # Mapa
    parts.append('<div class="section-title" style="display:flex; justify-content:space-between; align-items:center;">')
    parts.append('<span>Mapa de Parcel·les</span>')
    parts.append('<select id="map-filter" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text); font-size:14px; outline:none; cursor:pointer;" onchange="filterMap(this.value)">')
    parts.append('  <option value="all">Tots els cultius</option>')
    parts.append('  <option value="vinya">🍇 Vinya</option>')
    parts.append('  <option value="cirerers">🍒 Cirerers</option>')
    parts.append('  <option value="pistatxo">🌰 Pistatxo</option>')
    parts.append('</select>')
    parts.append('</div>')
    parts.append('<div id="map" style="height: 400px; border-radius: 14px; margin-bottom: 24px; z-index: 1;"></div>')

    # Filtre + gràfiques meteo globals
    parts.append('<div class="section-title">Dades meteorològiques globals</div>')
    parts.append(generar_filtre_bar())
    parts.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:24px">')
    parts.append(generar_chart_card(
        "chart-et0", 
        "Balanç Hídric (ET0 vs Pluja)", 
        "Aquesta gràfica mostra l'Evapotranspiració de referència (ET0) comparada amb la precipitació diària. Permet avaluar les pèrdues d'aigua per evaporació del sòl i transpiració de les plantes, i saber si l'aportació d'aigua (pluja o reg) és suficient per mantenir el balanç hídric.",
        'style="margin-bottom:0"'
    ))
    parts.append(generar_chart_card(
        "chart-phenology", 
        "Evolució Fenològica", 
        "Mostra l'acumulació de Graus-Dia (integral tèrmica base 10°C) i Hores de Fred (temperatures < 7°C). Aquestes mètriques són essencials per predir les fases de desenvolupament de la vinya i assegurar que arbres com els cirerers i pistatxos han cobert les seves necessitats de fred hivernal.",
        'style="margin-bottom:0"'
    ))
    parts.append('</div>')
    
    parts.append(generar_chart_card(
        "chart-th", 
        "Temperatura i humitat", 
        "Evolució horària de la temperatura (°C) i la humitat relativa (%). Les línies discontínues marquen els llindars d'humitat del 40% i 70%, crítics per al desenvolupament de certes malalties fúngiques."
    ))

    parts.append(generar_chart_card(
        "chart-raduv", 
        "Radiació Solar i Índex UV", 
        "Dades obtingudes via satèl·lit (Open-Meteo). La radiació solar (W/m²) afecta directament a la fotosíntesi i l'evapotranspiració. L'Índex UV ens permet modelar de forma més precisa l'estrès de la planta i el creixement d'alguns patògens (com l'oïdi, que és sensible a l'alta radiació UV)."
    ))

    parts.append('<div class="section-title">Previsió Meteorològica (7 dies)</div>')
    parts.append("""
<div class="chart-card" style="padding:0; overflow:hidden">
  <iframe width="100%" height="450" src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=%C2%B0C&metricWind=km%2Fh&zoom=10&overlay=wind&product=ecmwf&level=surface&lat=39.5146&lon=3.1540" frameborder="0"></iframe>
</div>
""")

    parts.append("</main>")
    parts.append(generar_footer())

    # Script
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append(JS_CHART_BASE)
    parts.append(f"""
let map;
let polygons = [];

// Inicialització del Mapa (Leaflet)
function initMap() {{
  map = L.map('map').setView([39.5146, 3.15405], 16);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
    attribution: 'Tiles &copy; Esri'
  }}).addTo(map);

  // Colors segons risc (simplificat, en el futur cada parcel·la tindrà la seva lògica de color completa)
  const colorVinya = '{color_oidi}'; 
  const colorGris = '#7a7269';

  if (ALL.parceles && ALL.parceles.length > 0) {{
    ALL.parceles.forEach(p => {{
      let color = colorGris;
      let status = "Properament";
      if (p.cultiu === "vinya") {{
        color = colorVinya;
        status = "Monitoratge Actiu";
      }}
      
      const poly = L.polygon(p.coordenades, {{
        color: color, 
        weight: 3, 
        fillOpacity: 0.4,
        className: 'parcel-polygon'
      }});
      poly.parcelaData = p; // Guardem dades per filtrar
      
      const tooltipHTML = `
        <div style="font-family:Inter,sans-serif; text-align:center">
          <h4 style="margin:0 0 4px 0; font-size:14px">${{p.nom}}</h4>
          <span style="font-size:12px; color:#666">${{status}}</span><br>
          <span style="font-size:12px; color:${{color}}">&#9679; Fes clic per veure detalls</span>
        </div>
      `;
      
      poly.bindTooltip(tooltipHTML, {{sticky: true, direction: 'top', offset: [0, -10]}});
      
      if (p.link && p.link !== "#") {{
        poly.on('click', () => {{
          window.location.href = p.link;
        }});
        poly.on('mouseover', function () {{
          this._path.style.cursor = 'pointer';
        }});
      }}
      
      poly.addTo(map);
      polygons.push(poly);
    }});
  }} else {{
    // Fallback if parceles.json doesn't exist
    const vinyaCoords = [[39.5150, 3.1535], [39.5150, 3.1545], [39.5140, 3.1545], [39.5140, 3.1535]];
    const poly = L.polygon(vinyaCoords, {{color: colorVinya, weight: 3, fillOpacity: 0.4}}).addTo(map).bindPopup("<b>Vinya</b><br>Monitoratge Actiu");
    polygons.push(poly);
  }}
}}

function filterMap(cultiu) {{
  let bounds = new L.LatLngBounds();
  let found = false;
  
  polygons.forEach(poly => {{
    if (cultiu === 'all' || (poly.parcelaData && poly.parcelaData.cultiu === cultiu)) {{
      if (!map.hasLayer(poly)) map.addLayer(poly);
      bounds.extend(poly.getBounds());
      found = true;
    }} else {{
      if (map.hasLayer(poly)) map.removeLayer(poly);
    }}
  }});
  
  if (found) {{
    map.fitBounds(bounds, {{padding: [20, 20]}});
  }}
}}

window.addEventListener('load', initMap);

function buildCharts(start, end) {{
  if (end === undefined) end = ALL.labels.length;
  const L_th = ALL.labels.slice(start, end);
  
  // Determinar rang de dates per filtrar les dades diàries
  const startDate = ALL.ts_raw[start] ? ALL.ts_raw[start].substring(0, 10) : null;
  const endDate = ALL.ts_raw[Math.min(end - 1, ALL.ts_raw.length - 1)] ? ALL.ts_raw[Math.min(end - 1, ALL.ts_raw.length - 1)].substring(0, 10) : null;
  
  const daily = ALL.daily;
  let dStart = 0, dEnd = daily.labels.length;
  
  if (startDate && endDate) {{
    // daily.labels format: "dd/mm" — convertim a comparable
    const sD = new Date(startDate);
    const eD = new Date(endDate);
    
    for (let i = 0; i < daily.labels.length; i++) {{
      // Reconstruir data del label "dd/mm" amb l'any actual
      const parts = daily.labels[i].split('/');
      const d = new Date(sD.getFullYear(), parseInt(parts[1]) - 1, parseInt(parts[0]));
      if (d < sD) {{ dStart = i + 1; }}
      if (d <= eD) {{ dEnd = i + 1; }}
    }}
  }}
  
  const dL = daily.labels.slice(dStart, dEnd);
  const dET0 = daily.et0.slice(dStart, dEnd);
  const dP = daily.pluja.slice(dStart, dEnd);
  const dB = daily.balanc.slice(dStart, dEnd);
  const dGDD = daily.gdd_acc.slice(dStart, dEnd);
  const dFred = daily.fred_acc.slice(dStart, dEnd);

  Object.values(window._charts || {{}}).forEach(c => c.destroy());
  window._charts = {{
    th: createTHChart(L_th, ALL.temps.slice(start, end), ALL.humitat.slice(start, end)),
    et0: createET0Chart(dL, dET0, dP, dB),
    pheno: createPhenologyChart(dL, dGDD, dFred),
    raduv: createRadUVChart(L_th, ALL.rad_solar.slice(start, end), ALL.uv_index.slice(start, end))
  }};
}}
function rebuildCurrentView() {{
  if (customStart !== null && customEnd !== null) {{ buildCharts(customStart, customEnd); }}
  else {{ setFilter(activeFilter); }}
}}
""")
    parts.append(JS_FILTER)
    parts.append("setFilter('7d');")
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: VINYA  (resum del cultiu)
# ═════════════════════════════════════════════════════════════════════════════

def generar_vinya(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")

    # Risc oïdi
    risc_oidi = str(ultima.get("risc_gubler", "baix"))
    color_oidi = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828","molt alt":"#6a1b9a"}.get(risc_oidi, "#7a7269")

    # Risc mildiu
    risc_mildiu = str(ultima.get("risc_mildiu", "inactiu"))
    color_mildiu = {"inactiu":"#7a7269","vigilancia":"#c77d00","primari":"#d45e0a",
                    "secundari":"#c62828","alt":"#6a1b9a"}.get(risc_mildiu, "#7a7269")

    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Vinya · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("vinya"))
    parts.append("<main>")

    # Capçalera
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>🍇 Vinya</h1>
    <div class="sub">Monitoratge fitosanitari · Últimes dades: {ts_act}</div>
  </div>
</div>
""")

    # Targetes de malalties
    parts.append(f"""
<div class="disease-grid">
  <a href="oidi.html" class="disease-card">
    <span class="icon">🍂</span>
    <div class="name">Oïdi</div>
    <div class="agent">Erysiphe necator</div>
    <div class="risk-line">
      <span class="risk-badge" style="background:rgba({_hex_to_rgb(color_oidi)},.15);color:{color_oidi}">● {risc_oidi.upper()}</span>
    </div>
    <div class="desc">Models Gubler + Kast — Risc climàtic ajustat per fase fenològica (resistència ontogènica).</div>
    <span class="arrow">→</span>
  </a>
  <a href="mildiu.html" class="disease-card">
    <span class="icon">💧</span>
    <div class="name">Mildiu</div>
    <div class="agent">Plasmopara viticola</div>
    <div class="risk-line">
      <span class="risk-badge" style="background:rgba({_hex_to_rgb(color_mildiu)},.15);color:{color_mildiu}">● {risc_mildiu.upper()}</span>
    </div>
    <div class="desc">Model EPI + regla 3×10 de Goidanich. Graus-dia d'incubació.</div>
    <span class="arrow">→</span>
  </a>
  <a href="botritis.html" class="disease-card">
    <span class="icon">🍇</span>
    <div class="name">Botritis</div>
    <div class="agent">Botrytis cinerea</div>
    <div class="risk-line">
      <span class="risk-badge" style="background:rgba(107,114,128,.15);color:#7a7269">— SENSE MODEL</span>
    </div>
    <div class="desc">Podridura gris. Factors: HR alta, pluja a maduració, ferides.</div>
    <span class="arrow">→</span>
  </a>
  <a href="blackrot.html" class="disease-card">
    <span class="icon">⚫</span>
    <div class="name">Black Rot</div>
    <div class="agent">Guignardia bidwellii</div>
    <div class="risk-line">
      <span class="risk-badge" style="background:rgba(107,114,128,.15);color:#7a7269">— SENSE MODEL</span>
    </div>
    <div class="desc">Podridura negra. Factors: pluja + T 20-30°C, fulles infectades.</div>
    <span class="arrow">→</span>
  </a>
</div>
""")

    # Filtre + gràfiques meteo
    parts.append(generar_filtre_bar())
    parts.append("""
<div class="chart-card">
  <div class="chart-title">Temperatura i humitat</div>
  <canvas id="chart-th"></canvas>
</div>
<div class="chart-card">
  <div class="chart-title">Precipitació (mm)</div>
  <canvas id="chart-pluja"></canvas>
</div>
""")

    parts.append("</main>")
    parts.append(generar_footer())

    # Script
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append(JS_CHART_BASE)
    parts.append("""
function buildCharts(start, end) {
  const L = ALL.labels.slice(start, end);
  Object.values(window._charts || {}).forEach(c => c.destroy());
  window._charts = {
    th: createTHChart(L, ALL.temps.slice(start, end), ALL.humitat.slice(start, end)),
    pluja: createPlujaChart(L, ALL.pluja.slice(start, end))
  };
}
function rebuildCurrentView() {
  if (customStart !== null && customEnd !== null) { buildCharts(customStart, customEnd); }
  else { setFilter(activeFilter); }
}
""")
    parts.append(JS_FILTER)
    parts.append("setFilter('7d');")
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: OÏDI
# ═════════════════════════════════════════════════════════════════════════════

def generar_oidi(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]

    t_act  = pd.to_numeric(ultima.get("temperatura_c"), errors="coerce")
    hr_act = pd.to_numeric(ultima.get("humitat_pct"),   errors="coerce")
    ui_act = pd.to_numeric(ultima.get("ui_acumulades"), errors="coerce")
    risc   = str(ultima.get("risc_gubler", "baix"))
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")
    risc_color = {"baix":"#22c55e","moderat":"#f59e0b","alt":"#ef4444","molt alt":"#7c3aed"}.get(risc, "#6b7280")
    ui_pct = min(100, (ui_act / 150) * 100) if not pd.isna(ui_act) else 0

    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Oïdi · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("oidi"))
    parts.append("<main>")

    # Capçalera
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>Oïdi</h1>
    <div class="sub">Erysiphe necator · Model Gubler (1995) + Kast (OiDiag) · {ts_act}</div>
  </div>
  <span class="badge" style="color:{risc_color};border-color:{risc_color}">Clima: {risc.upper()}</span>
</div>

<div class="card" style="margin-bottom:24px;">
  <div class="card-title">Resistència Ontogènica (Model Kast)</div>
  <label style="margin-top:0">Fase fenològica actual de la vinya:</label>
  <select id="sel-fase" onchange="canviFase(this.value)">
    <option value="1">🌱 Brotació a Pre-floració (Risc climàtic complet - Només fulles)</option>
    <option value="2">🌼 Floració i Quallat (Risc MÀXIM - Raïm molt sensible)</option>
    <option value="3">🍇 Creixement del gra (Risc Alt - Raïm sensible)</option>
    <option value="4">🟢 Tancament del raïm (Risc Moderat - Inici de resistència)</option>
    <option value="5">🟣 Envero i Maduració (Risc NUL pel raïm - Resistència total)</option>
  </select>
  <div style="font-size:12px;color:var(--muted);margin-top:8px;">
    L'edat del raïm modifica el risc real d'infecció calculat pel model Gubler. Selecciona la fase per ajustar la predicció i les recomanacions.
  </div>
</div>

<div id="oidi-recom-box" style="margin-bottom:20px;">
  <div class="recom-box"><div class="empty" style="padding:0">Carregant avaluació Kast...</div></div>
</div>
""")

    # KPIs
    parts.append(f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-label">Risc Kast (Raïm)</div>
    <div class="kpi-val" id="kast-val" style="font-size:18px;">--</div>
    <div class="kpi-sub" id="kast-ui">-- UI (Ajustat)</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Risc Gubler (Clima)</div>
    <div class="kpi-val" style="font-size:18px;color:{risc_color}">{risc.upper()}</div>
    <div class="kpi-sub">Llindar alt: 100 UI</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Temperatura</div>
    <div class="kpi-val">{t_act:.1f}<span class="kpi-unit">°C</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Humitat relativa</div>
    <div class="kpi-val">{hr_act:.0f}<span class="kpi-unit">%</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">UI acumulades</div>
    <div class="kpi-val">{ui_act:.0f}<span class="kpi-unit">UI</span></div>
    <div class="ui-bar-outer">
      <div class="ui-bar-inner" style="width:{ui_pct:.0f}%;background:{risc_color}"></div>
    </div>
  </div>
</div>
""")

    # Filtre + gràfiques
    parts.append(generar_filtre_bar())
    parts.append("""
<div class="chart-card">
  <div class="chart-title">Temperatura i humitat</div>
  <canvas id="chart-th"></canvas>
</div>
<div class="chart-card">
  <div class="chart-title">UI acumulades (model Gubler)</div>
  <canvas id="chart-ui"></canvas>
  <div class="llindars">
    <span class="ll" style="color:#22c55e;border-color:#22c55e">Baix &lt;50</span>
    <span class="ll" style="color:#f59e0b;border-color:#f59e0b">Moderat ≥50</span>
    <span class="ll" style="color:#ef4444;border-color:#ef4444">Alt ≥100</span>
    <span class="ll" style="color:#7c3aed;border-color:#7c3aed">Molt alt ≥150</span>
  </div>
</div>
<div class="chart-card">
  <div class="chart-title">Precipitació (mm)</div>
  <canvas id="chart-pluja"></canvas>
</div>
""")

    # Tractaments
    parts.append(generar_tractaments_section("oidio"))

    parts.append("</main>")
    parts.append(generar_footer())

    # Script
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append(JS_CHART_BASE)
    parts.append("""
function buildCharts(start, end) {
  const L = ALL.labels.slice(start, end);
  Object.values(window._charts || {}).forEach(c => c.destroy());
  window._charts = {
    th: createTHChart(L, ALL.temps.slice(start, end), ALL.humitat.slice(start, end)),
    ui: createUIGublerChart(L, ALL.ui_acc.slice(start, end), ALL.ui_hora.slice(start, end), ALL.ts_raw.slice(start, end)),
    pluja: createPlujaChart(L, ALL.pluja.slice(start, end))
  };
}
function rebuildCurrentView() {
  if (customStart !== null && customEnd !== null) { buildCharts(customStart, customEnd); }
  else { setFilter(activeFilter); }
}
""")
    parts.append(JS_FILTER)
    parts.append("const MALALTIA_FILTRE = 'oidio';")
    parts.append(JS_TRACTAMENTS)
    parts.append(JS_FASE_KAST)
    parts.append("setFilter('7d');")
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: MILDIU
# ═════════════════════════════════════════════════════════════════════════════

def generar_mildiu(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]

    risc_mildiu = str(ultima.get("risc_mildiu", "inactiu"))
    pluja_10d   = pd.to_numeric(ultima.get("pluja_10d_mm"), errors="coerce")
    dies_inc    = pd.to_numeric(ultima.get("dies_incubacio_est"), errors="coerce")
    ts_act      = ultima["ts"].strftime("%d/%m/%Y %H:%M")
    t_act       = pd.to_numeric(ultima.get("temperatura_c"), errors="coerce")
    hr_act      = pd.to_numeric(ultima.get("humitat_pct"),   errors="coerce")

    risc_color = {"inactiu":"#6b7280","vigilancia":"#f59e0b","primari":"#f97316",
                  "secundari":"#ef4444","alt":"#7c3aed"}.get(risc_mildiu, "#6b7280")
    dies_str = f"{dies_inc:.0f}d" if not pd.isna(dies_inc) else "—"
    pluja_10d_val = f"{pluja_10d:.1f}" if not pd.isna(pluja_10d) else "0.0"

    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Mildiu · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("mildiu"))
    parts.append("<main>")

    # Capçalera
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>Mildiu</h1>
    <div class="sub">Plasmopara viticola · Model EPI + regla 3×10 · {ts_act}</div>
  </div>
  <span class="badge" style="color:{risc_color};border-color:{risc_color}">● {risc_mildiu.upper()}</span>
</div>
""")

    parts.append(generar_recomanacio_tractament("mildiu", risc_mildiu))

    # KPIs
    parts.append(f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-label">Risc mildiu</div>
    <div class="kpi-val" style="font-size:18px;color:{risc_color}">{risc_mildiu.upper()}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Pluja acumulada 10d</div>
    <div class="kpi-val">{pluja_10d_val}<span class="kpi-unit">mm</span></div>
    <div class="kpi-sub">Llindar: 10 mm</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Dies fins a símptomes</div>
    <div class="kpi-val">{dies_str}</div>
    <div class="kpi-sub">Si hi ha infecció activa</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Temperatura</div>
    <div class="kpi-val">{t_act:.1f}<span class="kpi-unit">°C</span></div>
  </div>
</div>
""")

    # Filtre + gràfiques
    parts.append(generar_filtre_bar())
    parts.append("""
<div class="chart-card">
  <div class="chart-title">Temperatura i humitat</div>
  <canvas id="chart-th"></canvas>
</div>
<div class="chart-card">
  <div class="chart-title">Risc mildiu (0=inactiu → 4=alt)</div>
  <canvas id="chart-mildiu"></canvas>
  <div class="llindars" style="margin-top:8px">
    <span class="ll" style="color:#6b7280;border-color:#6b7280">Inactiu</span>
    <span class="ll" style="color:#f59e0b;border-color:#f59e0b">Vigilància</span>
    <span class="ll" style="color:#f97316;border-color:#f97316">Primari</span>
    <span class="ll" style="color:#ef4444;border-color:#ef4444">Secundari</span>
    <span class="ll" style="color:#7c3aed;border-color:#7c3aed">Alt</span>
  </div>
</div>
<div class="chart-card">
  <div class="chart-title">Precipitació (mm)</div>
  <canvas id="chart-pluja"></canvas>
</div>
""")

    # Tractaments
    parts.append(generar_tractaments_section("mildiu"))

    parts.append("</main>")
    parts.append(generar_footer())

    # Script
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append(JS_CHART_BASE)
    parts.append("""
function buildCharts(start, end) {
  const L = ALL.labels.slice(start, end);
  Object.values(window._charts || {}).forEach(c => c.destroy());
  window._charts = {
    th: createTHChart(L, ALL.temps.slice(start, end), ALL.humitat.slice(start, end)),
    mildiu: createRiscMildiuChart(L, ALL.risc_mildiu_data.slice(start, end)),
    pluja: createPlujaChart(L, ALL.pluja.slice(start, end))
  };
}
function rebuildCurrentView() {
  if (customStart !== null && customEnd !== null) { buildCharts(customStart, customEnd); }
  else { setFilter(activeFilter); }
}
""")
    parts.append(JS_FILTER)
    parts.append("const MALALTIA_FILTRE = 'mildiu';")
    parts.append(JS_TRACTAMENTS)
    parts.append("setFilter('7d');")
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: BOTRITIS (sense model)
# ═════════════════════════════════════════════════════════════════════════════

def generar_botritis() -> str:
    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Botritis · Son Nadal", amb_charts=False))
    parts.append("<body>")
    parts.append(generar_navbar("botritis"))
    parts.append("<main>")

    parts.append("""
<div class="page-header">
  <div>
    <h1>Botritis</h1>
    <div class="sub">Botrytis cinerea · Podridura gris</div>
  </div>
  <span class="badge" style="color:#6b7280;border-color:#6b7280">SENSE MODEL</span>
</div>

<div class="notice">
  ℹ️ Model predictiu en desenvolupament. Aquesta pàgina permet registrar tractaments
  i consultar els factors de risc principals.
</div>
""")

    parts.append(generar_recomanacio_tractament("botritis"))

    parts.append("""
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:20px">
  <div class="info-card">
    <h3>Descripció</h3>
    <p>La botritis o podridura gris és causada pel fong <em>Botrytis cinerea</em>.
    Ataca principalment els raïms madurs, provocant la seva descomposició.
    Pot afectar també flors, brots i fulles en condicions favorables.</p>
  </div>
  <div class="info-card">
    <h3>Factors de risc</h3>
    <ul>
      <li>Humitat relativa &gt; 90% durant períodes prolongats</li>
      <li>Temperatura entre 15°C i 25°C</li>
      <li>Pluja durant la maduració del raïm</li>
      <li>Ferides per insectes (polilla del raïm) o pedregada</li>
      <li>Varietats de raïm compactes amb poca ventilació</li>
    </ul>
  </div>
  <div class="info-card">
    <h3>Prevenció</h3>
    <ul>
      <li>Desfullat per millorar la ventilació dels raïms</li>
      <li>Tractament preventiu al tancament del raïm i a l'envero</li>
      <li>Productes: Fenhexamid, Ciprodinil, Pirimetanil</li>
      <li>Control de la polilla del raïm (vector de ferides)</li>
    </ul>
  </div>
  <div class="info-card">
    <h3>Símptomes</h3>
    <ul>
      <li>Vel grisenc (esporulació) sobre els raïms</li>
      <li>Grans que es tornen marrons i s'estoven</li>
      <li>Olor a podrit dolç en casos avançats</li>
      <li>Taques necròtiques a fulles i brots joves</li>
    </ul>
  </div>
</div>
""")

    # Tractaments
    parts.append(generar_tractaments_section("botritis"))

    parts.append("</main>")
    parts.append(generar_footer())

    # Script (només tractaments, sense gràfiques)
    parts.append("<script>")
    parts.append(JS_THEME)
    parts.append("const MALALTIA_FILTRE = 'botritis';")
    parts.append(JS_TRACTAMENTS)
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: BLACK ROT (sense model)
# ═════════════════════════════════════════════════════════════════════════════

def generar_blackrot() -> str:
    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Black Rot · Son Nadal", amb_charts=False))
    parts.append("<body>")
    parts.append(generar_navbar("blackrot"))
    parts.append("<main>")

    parts.append("""
<div class="page-header">
  <div>
    <h1>Black Rot</h1>
    <div class="sub">Guignardia bidwellii · Podridura negra</div>
  </div>
  <span class="badge" style="color:#6b7280;border-color:#6b7280">SENSE MODEL</span>
</div>

<div class="notice">
  ℹ️ Model predictiu en desenvolupament. Aquesta pàgina permet registrar tractaments
  i consultar els factors de risc principals.
</div>
""")

    parts.append(generar_recomanacio_tractament("blackrot"))

    parts.append("""
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:20px">
  <div class="info-card">
    <h3>Descripció</h3>
    <p>El black rot o podridura negra és causat pel fong <em>Guignardia bidwellii</em>.
    És una malaltia molt destructiva que pot afectar fulles, brots i especialment els raïms,
    que acaben momificats i negres a la planta.</p>
  </div>
  <div class="info-card">
    <h3>Factors de risc</h3>
    <ul>
      <li>Temperatura entre 20°C i 30°C (òptim ~26°C)</li>
      <li>Pluja o mullat foliar durant &gt; 6 hores</li>
      <li>Raïms infectats momificats de l'any anterior</li>
      <li>Fulles mortes amb picnidis al terra</li>
      <li>Període crític: floració fins a tancament del raïm</li>
    </ul>
  </div>
  <div class="info-card">
    <h3>Prevenció</h3>
    <ul>
      <li>Eliminar raïms momificats de la vinya i del terra</li>
      <li>Tractaments preventius des de brotació</li>
      <li>Productes: Mancozeb, Metiram, Myclobutanil</li>
      <li>Millorar la ventilació amb poda adequada</li>
    </ul>
  </div>
  <div class="info-card">
    <h3>Símptomes</h3>
    <ul>
      <li>Lesions marrons circulars a fulles amb vora fosca</li>
      <li>Petits punts negres (picnidis) sobre les lesions</li>
      <li>Raïms que es tornen negres i es momifiquen</li>
      <li>Lesions allargades a sarments joves</li>
    </ul>
  </div>
</div>
""")

    # Tractaments
    parts.append(generar_tractaments_section("blackrot"))

    parts.append("</main>")
    parts.append(generar_footer())

    # Script (només tractaments, sense gràfiques)
    parts.append("<script>")
    parts.append(JS_THEME)
    parts.append("const MALALTIA_FILTRE = 'blackrot';")
    parts.append(JS_TRACTAMENTS)
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  UTILITATS
# ═════════════════════════════════════════════════════════════════════════════

def _hex_to_rgb(hex_color: str) -> str:
    """Converteix #rrggbb a 'r,g,b' per usar en rgba()."""
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    if not os.path.exists(CSV_HISTORIAL):
        print("[!] No s'ha trobat historial.csv")
        raise SystemExit(1)

    df = carregar_dades()
    if df.empty:
        print("[!] Historial buit")
        raise SystemExit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pages = {
        "index.html":    generar_index(df),
        "vinya.html":    generar_vinya(df),
        "oidi.html":     generar_oidi(df),
        "mildiu.html":   generar_mildiu(df),
        "botritis.html": generar_botritis(),
        "blackrot.html": generar_blackrot(),
    }

    for filename, html in pages.items():
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  OK {path}")

    print(f"\nDashboard generat: {len(pages)} pagines")
    print(f"  {len(df)} registres | "
          f"{df['ts'].min().strftime('%d/%m')} -> "
          f"{df['ts'].max().strftime('%d/%m/%Y %H:%M')}")


if __name__ == "__main__":
    main()
