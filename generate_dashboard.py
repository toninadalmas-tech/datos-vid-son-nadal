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
  --bg:#0f1117;--surface:#1a1d27;--surface2:#232635;
  --border:#2a2d3a;--text:#e8eaf0;--muted:#6b7280;
  --accent:#3b82f6;--verd:#22c55e;--ambre:#f59e0b;
  --taronja:#f97316;--vermell:#ef4444;--violeta:#7c3aed;
  --radius:10px;
}
body{background:var(--bg);color:var(--text);
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  font-size:14px;line-height:1.5;margin:0;padding:0}

/* Navbar */
.navbar{position:sticky;top:0;z-index:100;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;height:56px;
  background:rgba(15,17,23,0.88);
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border)}
.nav-brand{font-size:16px;font-weight:600;color:#fff;
  text-decoration:none;display:flex;align-items:center;gap:8px}
.nav-links{display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch}
.nav-link{padding:6px 14px;border-radius:8px;font-size:13px;font-weight:500;
  color:var(--muted);text-decoration:none;white-space:nowrap;transition:all .2s}
.nav-link:hover{color:var(--text);background:var(--surface)}
.nav-link.active{color:#fff;background:var(--surface2)}

/* Main */
main{max-width:1100px;margin:0 auto;padding:24px 16px}

/* Page header */
.page-header{display:flex;justify-content:space-between;align-items:flex-start;
  margin-bottom:24px;flex-wrap:wrap;gap:12px}
.page-header h1{font-size:22px;font-weight:600;color:#fff;letter-spacing:-.3px}
.page-header .sub{color:var(--muted);font-size:12px;margin-top:2px}
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;
  border-radius:20px;font-size:12px;font-weight:600;
  border:1px solid currentColor;letter-spacing:.3px}

/* KPI cards */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:12px;margin-bottom:24px}
.kpi{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:16px 18px;transition:border-color .2s}
.kpi:hover{border-color:#3a3d4a}
.kpi-label{font-size:11px;color:var(--muted);text-transform:uppercase;
  letter-spacing:.5px;margin-bottom:6px}
.kpi-val{font-size:28px;font-weight:600;color:#fff;line-height:1}
.kpi-unit{font-size:13px;color:var(--muted);margin-left:2px}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:4px}
.ui-bar-outer{background:var(--border);border-radius:4px;height:6px;
  margin-top:8px;overflow:hidden}
.ui-bar-inner{height:100%;border-radius:4px;transition:width .5s}

/* Filter bar */
.filter-bar{display:flex;gap:4px;margin-bottom:16px}
.filter-btn{padding:5px 14px;border-radius:7px;border:1px solid var(--border);
  background:transparent;color:var(--muted);cursor:pointer;
  font-size:12px;font-weight:500;font-family:inherit;transition:all .2s}
.filter-btn:hover{color:var(--text);border-color:#3a3d4a}
.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}

/* Chart cards */
.chart-card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px;margin-bottom:16px}
.chart-title{font-size:13px;font-weight:500;color:var(--muted);
  text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
canvas{max-height:200px}
.llindars{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;font-size:11px}
.ll{padding:2px 8px;border-radius:4px;border:1px solid}

/* Disease cards (index) */
.disease-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:16px;margin-bottom:28px}
.disease-card{background:var(--surface);border:1px solid var(--border);
  border-radius:12px;padding:22px;text-decoration:none;color:inherit;
  transition:all .25s ease;position:relative;overflow:hidden;display:block}
.disease-card:hover{border-color:#3a3d4a;transform:translateY(-2px);
  box-shadow:0 8px 25px rgba(0,0,0,.3)}
.disease-card .icon{font-size:28px;margin-bottom:10px;display:block}
.disease-card .name{font-size:16px;font-weight:600;color:#fff;margin-bottom:2px}
.disease-card .agent{font-size:12px;color:var(--muted);font-style:italic;margin-bottom:12px}
.disease-card .risk-line{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.disease-card .risk-badge{display:inline-flex;align-items:center;gap:5px;
  padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600}
.disease-card .desc{font-size:12px;color:var(--muted);line-height:1.5}
.disease-card .arrow{position:absolute;right:18px;bottom:18px;
  color:var(--muted);font-size:18px;transition:transform .2s}
.disease-card:hover .arrow{transform:translateX(3px);color:var(--text)}

/* Info cards */
.info-card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;margin-bottom:16px}
.info-card h3{font-size:14px;font-weight:600;color:#fff;margin-bottom:8px}
.info-card p{color:var(--muted);font-size:13px;line-height:1.6}
.info-card ul{color:var(--muted);font-size:13px;margin-left:16px;margin-top:6px;line-height:1.8}
.notice{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.2);
  border-radius:var(--radius);padding:16px 20px;margin-bottom:20px;
  font-size:13px;color:var(--accent);display:flex;align-items:center;gap:10px}

/* Recommendation Box */
.recom-box{background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
  border-radius:var(--radius);padding:16px 20px;margin-bottom:20px;
  font-size:13px;color:var(--verd);display:flex;align-items:flex-start;gap:12px}
.recom-box.warning{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.2);color:var(--vermell)}
.recom-box.info{background:rgba(59,130,246,.08);border-color:rgba(59,130,246,.2);color:var(--accent)}
.recom-icon{font-size:18px;line-height:1}
.recom-content h4{font-size:14px;font-weight:600;margin-bottom:4px;color:currentColor}
.recom-content p{color:var(--text);opacity:0.9;margin-bottom:4px;line-height:1.5}
.recom-content ul{color:var(--text);opacity:0.9;margin-left:16px;margin-top:4px;line-height:1.6}

/* Treatment section */
.section-title{font-size:16px;font-weight:600;color:#fff;margin:32px 0 16px;
  padding-top:20px;border-top:1px solid var(--border)}
.card{background:var(--surface);border:1px solid var(--border);
  border-radius:12px;padding:20px;margin-bottom:16px}
.card-title{font-size:13px;font-weight:500;color:var(--muted);
  text-transform:uppercase;letter-spacing:.5px;margin-bottom:16px}
label{display:block;font-size:12px;color:var(--muted);margin-bottom:4px;margin-top:12px}
label:first-of-type{margin-top:0}
input,select,textarea{width:100%;background:var(--surface2);border:1px solid var(--border);
  border-radius:8px;color:var(--text);font-size:14px;
  padding:8px 12px;outline:none;font-family:inherit}
input:focus,textarea:focus{border-color:var(--accent)}
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
.btn-danger:hover{background:rgba(239,68,68,.1)}
.actions{display:flex;justify-content:flex-end;margin-top:20px}
.tractament-item{display:grid;grid-template-columns:1fr auto;
  gap:8px;align-items:start;padding:12px 0;
  border-bottom:1px solid var(--border)}
.tractament-item:last-child{border-bottom:none}
.t-data{font-size:13px;font-weight:500}
.t-producte{font-size:12px;color:var(--muted);margin-top:2px}
.t-badges{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}
.t-badge{font-size:11px;padding:2px 8px;border-radius:20px;font-weight:500}
.t-badge-oidio{background:rgba(245,158,11,.15);color:var(--ambre)}
.t-badge-mildiu{background:rgba(59,130,246,.15);color:var(--accent)}
.t-badge-botritis{background:rgba(139,92,246,.15);color:#a78bfa}
.t-badge-blackrot{background:rgba(239,68,68,.15);color:var(--vermell)}
.empty{color:var(--muted);font-size:13px;padding:16px 0;text-align:center}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  background:#1a1d27;border:1px solid var(--border);border-radius:8px;
  padding:10px 20px;font-size:13px;display:none;z-index:999}
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
}
"""

# ═════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT COMÚ
# ═════════════════════════════════════════════════════════════════════════════

JS_FILTER = """
const FILTER_SIZES = {'24h':48,'3d':144,'7d':336,'14d':999999};
let activeFilter = '7d';
function setFilter(range) {
  activeFilter = range;
  const n = Math.min(FILTER_SIZES[range], ALL.labels.length);
  const start = Math.max(0, ALL.labels.length - n);
  buildCharts(start);
  document.querySelectorAll('.filter-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.range === range));
}
"""

JS_CHART_BASE = """
const cfgBase = {
  responsive:true, maintainAspectRatio:true,
  plugins:{legend:{display:false}},
  scales:{
    x:{ticks:{color:'#6b7280',maxTicksLimit:8,font:{size:10}},
       grid:{color:'rgba(255,255,255,.04)'}},
    y:{ticks:{color:'#6b7280',font:{size:10}},
       grid:{color:'rgba(255,255,255,.06)'}}
  }
};
function createTHChart(L, T, H) {
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
    options:{...cfgBase,
      plugins:{...cfgBase.plugins,
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
        x:cfgBase.scales.x,
        yT:{...cfgBase.scales.y, position:'left',
            title:{display:true,text:'°C',color:'#f97316',font:{size:10}}},
        yHR:{...cfgBase.scales.y, position:'right', min:0, max:100,
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
    options:{...cfgBase,
      scales:{x:cfgBase.scales.x,
        y:{...cfgBase.scales.y, min:0,
           title:{display:true,text:'mm',color:'#38bdf8',font:{size:10}}}}
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
    options:{...cfgBase,
      plugins:{...cfgBase.plugins,
        legend:{display:true, labels:{color:'#9ca3af',font:{size:11}}},
        annotation:{annotations:anns}
      },
      scales:{x:cfgBase.scales.x,
        y:{...cfgBase.scales.y, min:0,
           title:{display:true,text:'UI acum.',color:'#a78bfa',font:{size:10}}},
        yUH:{...cfgBase.scales.y, position:'right', min:0,
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
    options:{...cfgBase,
      scales:{x:cfgBase.scales.x,
        y:{...cfgBase.scales.y, min:0, max:4,
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

def generar_head(titol: str, amb_charts: bool = True) -> str:
    charts_scripts = ""
    if amb_charts:
        charts_scripts = ('\n  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0'
                          '/dist/chart.umd.min.js"></script>'
                          '\n  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin'
                          '-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>')
    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titol}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">{charts_scripts}
  <style>{CSS}</style>
</head>"""


NAV_ITEMS = [
    ("index",    "index.html",    "Inici"),
    ("oidi",     "oidi.html",     "Oïdi"),
    ("mildiu",   "mildiu.html",   "Mildiu"),
    ("botritis", "botritis.html", "Botritis"),
    ("blackrot", "blackrot.html", "Black Rot"),
]

def generar_navbar(pagina_activa: str) -> str:
    links = []
    for pid, href, label in NAV_ITEMS:
        cls = "nav-link active" if pid == pagina_activa else "nav-link"
        links.append(f'<a href="{href}" class="{cls}">{label}</a>')
    links_html = "\n    ".join(links)
    return f"""<nav class="navbar">
  <a href="index.html" class="nav-brand">🍇 Son Nadal</a>
  <div class="nav-links">
    {links_html}
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

def preparar_dades_json(df: pd.DataFrame) -> str:
    """Prepara totes les sèries de dades com a JSON per a les gràfiques."""
    labels  = df["ts"].dt.strftime("%d/%m %H:%M").tolist()
    ts_raw  = df["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    temps   = pd.to_numeric(df["temperatura_c"],   errors="coerce").round(1).tolist()
    humitat = pd.to_numeric(df["humitat_pct"],     errors="coerce").round(1).tolist()
    pluja   = pd.to_numeric(df["precipitacio_mm"], errors="coerce").round(1).tolist()
    ui_hora = pd.to_numeric(df.get("ui_horaria",    pd.Series([0]*len(df))), errors="coerce").round(1).tolist()
    ui_acc  = pd.to_numeric(df.get("ui_acumulades", pd.Series([0]*len(df))), errors="coerce").round(1).tolist()

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

    return json.dumps({
        "labels":           labels,
        "ts_raw":           ts_raw,
        "temps":            temps,
        "humitat":          humitat,
        "pluja":            pluja,
        "ui_hora":          ui_hora,
        "ui_acc":           ui_acc,
        "risc_mildiu_data": risc_mildiu_data,
        "tractaments":      tractaments_data,
    })


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: INDEX  (hub principal)
# ═════════════════════════════════════════════════════════════════════════════

def generar_index(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")

    # Risc oïdi
    risc_oidi = str(ultima.get("risc_gubler", "baix"))
    color_oidi = {"baix":"#22c55e","moderat":"#f59e0b","alt":"#ef4444","molt alt":"#7c3aed"}.get(risc_oidi, "#6b7280")

    # Risc mildiu
    risc_mildiu = str(ultima.get("risc_mildiu", "inactiu"))
    color_mildiu = {"inactiu":"#6b7280","vigilancia":"#f59e0b","primari":"#f97316",
                    "secundari":"#ef4444","alt":"#7c3aed"}.get(risc_mildiu, "#6b7280")

    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Vinya Son Nadal · Felanitx"))
    parts.append("<body>")
    parts.append(generar_navbar("index"))
    parts.append("<main>")

    # Capçalera
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>Vinya Son Nadal</h1>
    <div class="sub">Felanitx, Mallorca · Monitoratge fitosanitari · Últims 14 dies</div>
  </div>
  <div class="sub" style="text-align:right">{ts_act}</div>
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
      <span class="risk-badge" style="background:rgba(107,114,128,.15);color:#6b7280">— SENSE MODEL</span>
    </div>
    <div class="desc">Podridura gris. Factors: HR alta, pluja a maduració, ferides.</div>
    <span class="arrow">→</span>
  </a>
  <a href="blackrot.html" class="disease-card">
    <span class="icon">⚫</span>
    <div class="name">Black Rot</div>
    <div class="agent">Guignardia bidwellii</div>
    <div class="risk-line">
      <span class="risk-badge" style="background:rgba(107,114,128,.15);color:#6b7280">— SENSE MODEL</span>
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
function buildCharts(start) {
  const L = ALL.labels.slice(start);
  Object.values(window._charts || {}).forEach(c => c.destroy());
  window._charts = {
    th: createTHChart(L, ALL.temps.slice(start), ALL.humitat.slice(start)),
    pluja: createPlujaChart(L, ALL.pluja.slice(start))
  };
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
function buildCharts(start) {
  const L = ALL.labels.slice(start);
  Object.values(window._charts || {}).forEach(c => c.destroy());
  window._charts = {
    th: createTHChart(L, ALL.temps.slice(start), ALL.humitat.slice(start)),
    ui: createUIGublerChart(L, ALL.ui_acc.slice(start), ALL.ui_hora.slice(start), ALL.ts_raw.slice(start)),
    pluja: createPlujaChart(L, ALL.pluja.slice(start))
  };
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
function buildCharts(start) {
  const L = ALL.labels.slice(start);
  Object.values(window._charts || {}).forEach(c => c.destroy());
  window._charts = {
    th: createTHChart(L, ALL.temps.slice(start), ALL.humitat.slice(start)),
    mildiu: createRiscMildiuChart(L, ALL.risc_mildiu_data.slice(start)),
    pluja: createPlujaChart(L, ALL.pluja.slice(start))
  };
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
