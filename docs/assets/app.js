
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
      borderColor:colors.map(c=>c.replace(/,\.8\)/,',1)').replace(/,\.4\)/,',1)')),
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
document.addEventListener('DOMContentLoaded', async () => {
  const el = document.getElementById('llista-tractaments');
  if (el) {
    const dades = await llegirFitxer();
    renderLlista(dades.tractaments);
  }
  const conf = document.getElementById('config-section');
  if (conf && token() && repo()) conf.style.display = 'none';
});


const FASE_FILE = 'fase_fenologica.json';
const MULTIPLIERS = {
  1: 1.0,
  2: 1.3,
  3: 1.0,
  4: 0.4,
  5: 0.0
};


async function llegirFase() {
  if (!token() || !repo()) return { varietats: {}, activa_oidi: 'auto_moscatell' };
  try {
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FASE_FILE}`,
      { headers: { Authorization: `Bearer ${token()}`, Accept: 'application/vnd.github+json' } });
    if (!r.ok) throw new Error('No trobat');
    const d = await r.json();
    const txt = decodeURIComponent(escape(atob(d.content)));
        let contingut = JSON.parse(txt);
    if (typeof contingut !== 'object' || contingut === null) {
       contingut = { varietats: {}, activa_oidi: typeof contingut === 'string' ? contingut : 'auto_moscatell' };
    } else if (contingut.fase !== undefined) {
       contingut = { varietats: {}, activa_oidi: contingut.fase || 'auto_moscatell' };
    }
    return contingut;
  } catch(e) {
    return { varietats: {}, activa_oidi: 'auto_moscatell' };
  }
}

async function guardarFaseRepo(faseData) {
  if (!token() || !repo()) return;
  try {
    let sha = null;
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FASE_FILE}`,
      { headers: { Authorization: `Bearer ${token()}`, Accept: 'application/vnd.github+json' } });
    if (r.ok) { const d = await r.json(); sha = d.sha; }
    
    faseData.data = new Date().toISOString();
    const b = {
      message: 'Actualització estat fenològic manual',
      content: btoa(unescape(encodeURIComponent(JSON.stringify(faseData)))),
    };
    if (sha) b.sha = sha;
    
    await fetch(`https://api.github.com/repos/${repo()}/contents/${FASE_FILE}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(b)
    });
  } catch(e) { console.error('Error guardant fase:', e); }
}

async function forceVarietat(varId, val) {
  const current = await llegirFase();
  if (!current.varietats) current.varietats = {};
  if (val === 'auto') {
      current.varietats[varId] = null;
  } else {
      current.varietats[varId] = parseInt(val);
  }
  await guardarFaseRepo(current);
  await initPhenologyIndex(); // Re-render
}

async function canviFase(val) {
  const current = await llegirFase();
  current.activa_oidi = val;
  await guardarFaseRepo(current);
  updateKastRisk(val, current.varietats || {});
}

async function initPhenologyIndex() {
  const grid = document.getElementById('feno-grid');
  if (!grid) return;
  
  const current = await llegirFase();
  const manualStates = current.varietats || {};
  
  const varietats = [
    { id: 'auto_moscatell', nom: 'Moscatell', tipus: 'Primerenca' },
    { id: 'auto_prensal', nom: 'Premsal Blanc', tipus: 'Mitjana' },
    { id: 'auto_callet', nom: 'Callet', tipus: 'Tardana' },
    { id: 'auto_manto_negro', nom: 'Manto Negro', tipus: 'Tardana' },
    { id: 'auto_cabernet', nom: 'Cabernet', tipus: 'Tardana' }
  ];
  
  const noms = ['N/A', '1. Brotació a Pre-floració', '2. Floració i Quallat', '3. Creixement del gra', '4. Tancament del raïm', '5. Envero i Maduració'];
  
  let html = '';
  varietats.forEach(v => {
     let isManual = manualStates[v.id] !== undefined && manualStates[v.id] !== null;
     let faseComputed = isManual ? manualStates[v.id] : getFaseFromGDD(v.id);
     
     let options = `<option value="auto" ${!isManual ? 'selected' : ''}>🤖 Auto-GDD (Calculat)</option>`;
     for(let i=1; i<=5; i++) {
        options += `<option value="${i}" ${isManual && manualStates[v.id] === i ? 'selected' : ''}>Forçar Fase ${i}</option>`;
     }
     
     html += `
     <div class="kpi" style="border: 1px solid ${isManual ? '#f59e0b' : 'var(--border)'};">
       <div class="kpi-label">${v.nom} (${v.tipus})</div>
       <div class="kpi-val" style="font-size:16px; margin-bottom:12px;">${noms[faseComputed]}</div>
       <select style="width:100%; font-size:12px; padding:4px; border-radius:4px; border:1px solid var(--border); outline:none; background:var(--bg); color:var(--text);" onchange="forceVarietat('${v.id}', this.value)">
         ${options}
       </select>
     </div>`;
  });
  grid.innerHTML = html;
}
const VARIETATS_GDD = {
  'auto_moscatell':   {2: 250, 3: 500, 4: 900,  5: 1400},
  'auto_prensal':     {2: 300, 3: 600, 4: 1000, 5: 1600},
  'auto_callet':      {2: 320, 3: 650, 4: 1100, 5: 1750},
  'auto_manto_negro': {2: 320, 3: 650, 4: 1100, 5: 1750},
  'auto_cabernet':    {2: 350, 3: 700, 4: 1150, 5: 1800}
};

function getFaseFromGDD(varietat) {
  const limits = VARIETATS_GDD[varietat];
  const gdd = ALL.gdd_anual || 0;
  if (gdd >= limits[5]) return 5;
  if (gdd >= limits[4]) return 4;
  if (gdd >= limits[3]) return 3;
  if (gdd >= limits[2]) return 2;
  return 1;
}

function updateKastRisk(faseVal, varietatsOverrides = {}) {
  let currentFase;
  const lbl = document.getElementById('auto-fase-lbl');
  
  if (typeof faseVal === 'string' && faseVal.startsWith('auto_')) {
     const isManual = varietatsOverrides[faseVal] !== undefined && varietatsOverrides[faseVal] !== null;
     currentFase = isManual ? varietatsOverrides[faseVal] : getFaseFromGDD(faseVal);
     
     if (lbl) {
        const noms = ['N/A','Brotació a Pre-floració','Floració i Quallat','Creixement del gra','Tancament del raïm','Envero i Maduració'];
        lbl.innerText = isManual ? `🖐️ Fase forçada manualment: ${noms[currentFase]}` : `🤖 Fase detectada automàticament: ${noms[currentFase]} (GDD acumulat: ${ALL.gdd_anual})`;
        lbl.style.display = 'block';
     }
  } else {
     currentFase = parseInt(faseVal);
     if (lbl) lbl.style.display = 'none';
  }
  
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



// Init
document.addEventListener('DOMContentLoaded', async () => {
  const sel = document.getElementById('sel-fase');
  if(sel) {
     const st = await llegirFase();
     sel.value = st.activa_oidi || 'auto_moscatell';
     updateKastRisk(sel.value, st.varietats || {});
  }
  await initPhenologyIndex();
});
