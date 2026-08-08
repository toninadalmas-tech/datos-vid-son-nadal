
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

// ── Mapa de parcel·les ──────────────────────────────────────────────────────
let map;
let polygons = [];
let capaActiva = 'cultiu';

const COLOR_GRIS = '#7a7269';
const COLORS_RISC = { baix: '#2e7d32', moderat: '#c77d00', alt: '#c62828' };

/** Superfície del polígon en hectàrees (fórmula de l'àrea esfèrica). */
function superficieHa(coords) {
  const R = 6378137;
  const rad = x => x * Math.PI / 180;
  let area = 0;
  for (let i = 0, n = coords.length; i < n; i++) {
    const [lat1, lon1] = coords[i];
    const [lat2, lon2] = coords[(i + 1) % n];
    area += rad(lon2 - lon1) * (2 + Math.sin(rad(lat1)) + Math.sin(rad(lat2)));
  }
  return Math.abs(area * R * R / 2) / 10000;
}

/** Dies transcorreguts des de l'últim tractament que cobreix la parcel·la. */
function diesDesTractament(cultiu) {
  if (cultiu !== 'vinya' || !ALL.tractaments || !ALL.tractaments.length) return null;
  const dates = ALL.tractaments.map(t => new Date(t.data)).filter(d => !isNaN(d));
  if (!dates.length) return null;
  const ultim = new Date(Math.max(...dates));
  return Math.floor((new Date() - ultim) / 86400000);
}

/** Estat sanitari i fenològic d'una parcel·la de vinya. */
function estatParcela(p) {
  if (p.cultiu !== 'vinya') {
    return { color: COLOR_GRIS, estat: 'Properament', detall: null };
  }
  const varietat = p.varietat || 'auto_callet';
  const fase = (typeof getFaseFromGDD === 'function' && VARIETATS_GDD[varietat])
    ? getFaseFromGDD(varietat) : 1;

  const idxClima = (ALL.index_gt && ALL.index_gt.length)
    ? ALL.index_gt[ALL.index_gt.length - 1] : 0;
  const mult = MULTIPLIERS[fase] !== undefined ? MULTIPLIERS[fase] : 1;
  const idxRaim = idxClima * mult;

  const nivell = v => v > 60 ? 'alt' : v > 30 ? 'moderat' : 'baix';
  const noms = ['—', 'Brotació a pre-floració', 'Floració i quallat',
                'Creixement del gra', 'Tancament del raïm', 'Envero i maduració'];

  return {
    color: COLORS_RISC[nivell(idxRaim)],
    estat: 'Monitoratge actiu',
    detall: {
      varietat: varietat.replace('auto_', ''),
      fase: noms[fase],
      riscRaim: nivell(idxRaim), idxRaim: Math.round(idxRaim),
      riscFulla: nivell(idxClima), idxFulla: Math.round(idxClima)
    }
  };
}

/** Color del polígon segons la capa seleccionada. */
function colorParcela(p) {
  const est = estatParcela(p);
  if (capaActiva === 'cultiu') {
    return p.cultiu === 'vinya' ? '#7c3aed' : COLOR_GRIS;
  }
  if (capaActiva === 'tractament') {
    const d = diesDesTractament(p.cultiu);
    if (d === null) return COLOR_GRIS;
    return d > 14 ? COLORS_RISC.alt : d > 10 ? COLORS_RISC.moderat : COLORS_RISC.baix;
  }
  if (capaActiva === 'fulla' && est.detall) return COLORS_RISC[est.detall.riscFulla];
  return est.color;   // 'raim' i per defecte
}

function contingutPopup(p) {
  const est = estatParcela(p);
  const ha = superficieHa(p.coordenades);
  let cos = `<div style="font-family:Inter,sans-serif;min-width:190px">
    <h4 style="margin:0 0 2px 0;font-size:14px">${p.nom}</h4>
    <div style="font-size:11px;color:#666;margin-bottom:6px">
      ${p.cultiu} · ${ha.toFixed(2)} ha</div>`;

  if (est.detall) {
    const d = est.detall;
    const dies = diesDesTractament(p.cultiu);
    cos += `
      <div style="font-size:12px;line-height:1.6">
        <div><b>Varietat:</b> ${d.varietat}</div>
        <div><b>Fase:</b> ${d.fase}</div>
        <div style="margin-top:4px">
          🍇 Raïm <b style="color:${COLORS_RISC[d.riscRaim]}">${d.riscRaim.toUpperCase()}</b>
          <span style="color:#888">(${d.idxRaim}/100)</span></div>
        <div>🍃 Fulla <b style="color:${COLORS_RISC[d.riscFulla]}">${d.riscFulla.toUpperCase()}</b>
          <span style="color:#888">(${d.idxFulla}/100)</span></div>
        ${dies !== null ? `<div style="margin-top:4px"><b>Últim tractament:</b> fa ${dies} dies</div>` : ''}
      </div>
      <div style="font-size:11px;color:#888;margin-top:6px">Fes clic per veure el detall</div>`;
  } else {
    cos += `<div style="font-size:12px;color:#666">${est.estat}</div>`;
  }
  return cos + '</div>';
}

function pintarParceles() {
  polygons.forEach(poly => {
    const col = colorParcela(poly.parcelaData);
    poly.setStyle({ color: col, fillColor: col });
    poly.setTooltipContent(contingutPopup(poly.parcelaData));
  });
  const lleg = document.getElementById('map-llegenda');
  if (lleg) lleg.innerHTML = llegendaMapa();
}

function llegendaMapa() {
  const punt = (c, t) => `<span style="margin-right:14px;white-space:nowrap">
    <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${c};margin-right:4px"></span>${t}</span>`;
  if (capaActiva === 'cultiu') {
    return punt('#7c3aed', 'Vinya (monitorada)') + punt(COLOR_GRIS, 'Sense monitoratge');
  }
  if (capaActiva === 'tractament') {
    return punt(COLORS_RISC.baix, '≤10 dies') + punt(COLORS_RISC.moderat, '11-14 dies') +
           punt(COLORS_RISC.alt, '>14 dies') + punt(COLOR_GRIS, 'Sense tractaments');
  }
  return punt(COLORS_RISC.baix, 'Risc baix') + punt(COLORS_RISC.moderat, 'Moderat') +
         punt(COLORS_RISC.alt, 'Alt') + punt(COLOR_GRIS, 'Sense model');
}

function setCapaMapa(capa) {
  capaActiva = capa;
  pintarParceles();
}

/** Botons de capa del mapa (no comparteixen estat amb el filtre temporal). */
function triaCapa(btn, capa) {
  document.querySelectorAll('[data-capa]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  setCapaMapa(capa);
}

function initMap() {
  const el = document.getElementById('map');
  if (!el || typeof L === 'undefined') return;

  map = L.map('map').setView([39.5146, 3.15405], 16);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles &copy; Esri' }).addTo(map);

  (ALL.parceles || []).forEach(p => {
    const poly = L.polygon(p.coordenades, { weight: 3, fillOpacity: 0.4, className: 'parcel-polygon' });
    poly.parcelaData = p;
    poly.bindTooltip(contingutPopup(p), { sticky: true, direction: 'top', offset: [0, -10] });

    if (p.link && p.link !== '#') {
      poly.on('click', () => { window.location.href = p.link; });
      poly.on('mouseover', function () { this._path.style.cursor = 'pointer'; });
    }
    poly.addTo(map);
    polygons.push(poly);
  });

  // Estació meteorològica: totes les dades dels models en surten, i la
  // distància a cada parcel·la diu com de representatives hi són.
  if (ALL.estacio && ALL.estacio.coordenades) {
    const [lat, lon] = ALL.estacio.coordenades;
    L.circleMarker([lat, lon], {
      radius: 6, color: '#fff', weight: 2, fillColor: '#3b82f6', fillOpacity: 1
    }).addTo(map).bindTooltip(
      `<b>${ALL.estacio.nom || 'Estació meteorològica'}</b><br>
       <span style="font-size:11px">Origen de totes les dades dels models</span>`,
      { direction: 'top' });
  }

  pintarParceles();
}

function filterMap(cultiu) {
  let bounds = new L.LatLngBounds();
  let found = false;
  polygons.forEach(poly => {
    if (cultiu === 'all' || (poly.parcelaData && poly.parcelaData.cultiu === cultiu)) {
      if (!map.hasLayer(poly)) map.addLayer(poly);
      bounds.extend(poly.getBounds());
      found = true;
    } else if (map.hasLayer(poly)) {
      map.removeLayer(poly);
    }
  });
  if (found) map.fitBounds(bounds, { padding: [20, 20] });
}

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

function createUIGublerChart(L, indexGT, horesRang, tsRaw) {
  // Llindars oficials del model de UC Davis sobre l'escala 0-100
  const uiColors = indexGT.map(v =>
    v>60?'rgba(239,68,68,.8)':v>30?'rgba(245,158,11,.8)':'rgba(34,197,94,.8)');

  let anns = {
    ll30:{type:'line',yMin:30,yMax:30,borderColor:'rgba(245,158,11,.4)',borderWidth:1,borderDash:[4,4],
          label:{content:'Moderat',display:true,position:'start',color:'rgba(245,158,11,.7)',font:{size:9}}},
    ll60:{type:'line',yMin:60,yMax:60,borderColor:'rgba(239,68,68,.5)',borderWidth:1.5,borderDash:[4,4],
          label:{content:'Alt',display:true,position:'start',color:'rgba(239,68,68,.7)',font:{size:9}}}
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
      {label:'Índex Gubler-Thomas', data:indexGT, borderColor:'#a78bfa', borderWidth:2,
       pointRadius:2, pointBackgroundColor:uiColors,
       fill:true, backgroundColor:'rgba(167,139,250,.08)', tension:.2},
      {label:'Ratxa a 21-29 °C (h)', data:horesRang, type:'bar',
       backgroundColor:'rgba(167,139,250,.25)',
       borderColor:'rgba(167,139,250,.5)', borderWidth:1, yAxisID:'yUH'}
    ]},
    options:{...cfgBase(),
      plugins:{...cfgBase().plugins,
        legend:{display:true, labels:{color:'#9ca3af',font:{size:11}}},
        annotation:{annotations:anns}
      },
      scales:{x:cfgBase().scales.x,
        y:{...cfgBase().scales.y, min:0, max:100,
           title:{display:true,text:'Índex (0-100)',color:'#a78bfa',font:{size:10}}},
        yUH:{...cfgBase().scales.y, position:'right', min:0,
             title:{display:true,text:'hores',color:'rgba(167,139,250,.6)',font:{size:10}},
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
const ghTokenEl = document.getElementById('gh-token');
if (ghTokenEl) ghTokenEl.value = localStorage.getItem('gh_token') || '';
const ghRepoEl = document.getElementById('gh-repo');
if (ghRepoEl) ghRepoEl.value = localStorage.getItem('gh_repo') || '';

const inpDataEl = document.getElementById('inp-data');
if (inpDataEl) {
  const ara = new Date();
  ara.setMinutes(ara.getMinutes() - ara.getTimezoneOffset());
  inpDataEl.value = ara.toISOString().slice(0,16);
}
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
// 'tipus' distingeix contacte de penetrant: el model OiDiag/VitiMeteo en fa
// servir per decidir l'interval màxim fins al tractament següent (taula 2 de
// Dubuis et al. 2014). Cap fongicida anti-oïdi és realment sistèmic.
const PRODUCTES_DB = {
  'sofre_pols': {nom: 'Sofre en pols', eco: true, dies: 7, tipus: 'contacte', malalties: ['oidio']},
  'sofre_mullable': {nom: 'Sofre mullable 80%', eco: true, dies: 10, tipus: 'contacte', malalties: ['oidio']},
  'triazol': {nom: 'Triazol (ex. Difenoconazol, Miclobutanil)', eco: false, dies: 14, tipus: 'penetrant', malalties: ['oidio', 'blackrot']},
  'caldo_bordeles': {nom: 'Caldo Bordelès / Sals de coure', eco: true, dies: 10, tipus: 'contacte', malalties: ['mildiu', 'blackrot']},
  'metalaxil': {nom: 'Sistèmic (Metalaxil + Mancozeb)', eco: false, dies: 14, tipus: 'penetrant', malalties: ['mildiu']},
  'cimoxanil': {nom: 'Penetrant (Cimoxanil)', eco: false, dies: 10, tipus: 'penetrant', malalties: ['mildiu']},
  'bacillus': {nom: 'Bacillus subtilis', eco: true, dies: 7, tipus: 'contacte', malalties: ['botritis']},
  'switch': {nom: 'Switch (Ciprodinil + Fludioxonil)', eco: false, dies: 14, tipus: 'penetrant', malalties: ['botritis']},
  'altre': {nom: 'Altre producte (Introduir a notes)', eco: false, dies: 10, tipus: 'contacte', malalties: ['oidio', 'mildiu', 'botritis', 'blackrot']}
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
    dies_proteccio: p.dies,
    tipus: p.tipus
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
  const obsEl = document.getElementById('llista-observacions');
  if (obsEl && typeof MALALTIA_FILTRE !== 'undefined') {
    const obs = await llegirObservacions();
    renderObservacions(obs.observacions, MALALTIA_FILTRE);

    // L'alerta d'OiDiag ha de saber si hi ha símptomes: amb la malaltia
    // instal·lada no s'han d'espaiar els tractaments.
    window.OBSERVACIONS_OIDI = (obs.observacions || []).filter(o => o.malaltia === 'oidio');
    const sel = document.getElementById('sel-fase');
    if (sel && window.OBSERVACIONS_OIDI.length) {
      const st = await llegirFase();
      updateKastRisk(sel.value, st.varietats || {});
    }
  }
  const dataObs = document.getElementById('obs-data');
  if (dataObs && !dataObs.value) dataObs.value = new Date().toISOString().slice(0, 10);

  const conf = document.getElementById('config-section');
  if (conf && token() && repo()) conf.style.display = 'none';
});


// ── Observacions de camp ────────────────────────────────────────────────────
// El model no pot saber si hi ha inòcul que ve de fora (una vinya veïna amb
// mildiu, per exemple). Aquestes observacions obren la porta del cicle
// secundari i, amb els anys, són l'únic contrast per calibrar els llindars.
const FITXER_OBS = 'observacions.json';

async function llegirObservacions() {
  if (!token() || !repo()) return { observacions: [] };
  try {
    const r = await fetch(
      `https://api.github.com/repos/${repo()}/contents/${FITXER_OBS}`,
      { headers: { Authorization: `Bearer ${token()}`, Accept: 'application/vnd.github+json' } });
    if (r.status === 404) return { observacions: [] };
    const data = await r.json();
    const contingut = JSON.parse(decodeURIComponent(escape(atob(data.content.replace(/\n/g, '')))));
    contingut._sha = data.sha;
    return contingut;
  } catch (e) {
    toast('Error llegint observacions: ' + e.message, false);
    return { observacions: [] };
  }
}

async function guardarObservacions(dades) {
  if (!token() || !repo()) { toast('Configura el token i el repositori primer', false); return false; }
  const sha = dades._sha; delete dades._sha;
  const cos = {
    message: `observacio: ${new Date().toISOString().slice(0, 10)}`,
    content: btoa(unescape(encodeURIComponent(JSON.stringify(dades, null, 2))))
  };
  if (sha) cos.sha = sha;
  try {
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FITXER_OBS}`,
      { method: 'PUT', headers: { Authorization: `Bearer ${token()}`,
        Accept: 'application/vnd.github+json', 'Content-Type': 'application/json' },
        body: JSON.stringify(cos) });
    return r.ok;
  } catch (e) { toast('Error guardant: ' + e.message, false); return false; }
}

async function afegirObservacio(malaltia) {
  const data = document.getElementById('obs-data').value;
  if (!data) { toast('La data és obligatòria', false); return; }

  const nova = {
    data: data,
    malaltia: malaltia,
    organ: document.getElementById('obs-organ').value,
    incidencia: document.getElementById('obs-incidencia').value,
    notes: document.getElementById('obs-notes').value.trim()
  };

  const dades = await llegirObservacions();
  dades.observacions = dades.observacions || [];
  dades.observacions.push(nova);
  dades.observacions.sort((a, b) => a.data.localeCompare(b.data));

  if (await guardarObservacions(dades)) {
    toast('Observació guardada');
    document.getElementById('obs-notes').value = '';
    renderObservacions(dades.observacions, malaltia);
    setTimeout(() => window.location.reload(), 800);
  } else {
    toast("No s'ha pogut guardar. Comprova el token i el repositori.", false);
  }
}

async function eliminarObservacio(idx, malaltia) {
  if (!confirm('Eliminar aquesta observació?')) return;
  const dades = await llegirObservacions();
  dades.observacions.splice(idx, 1);
  if (await guardarObservacions(dades)) {
    toast('Observació eliminada');
    renderObservacions(dades.observacions, malaltia);
    setTimeout(() => window.location.reload(), 800);
  }
}

function renderObservacions(observacions, malaltia) {
  const el = document.getElementById('llista-observacions');
  if (!el) return;
  const parells = (observacions || [])
    .map((o, i) => ({ o, i }))
    .filter(x => x.o.malaltia === malaltia);

  if (!parells.length) {
    el.innerHTML = '<div class="empty">Cap observació registrada per a aquesta malaltia</div>';
    return;
  }
  const colors = { cap: 'var(--muted)', baixa: '#fde047', mitjana: '#f97316', alta: '#ef4444' };
  el.innerHTML = parells.reverse().map(({ o, i }) => {
    const d = new Date(o.data).toLocaleDateString('ca-ES',
      { day: '2-digit', month: '2-digit', year: 'numeric' });
    const col = colors[o.incidencia] || 'var(--muted)';
    return `<div class="tractament-item"><div>
      <div class="t-data">${d} — <span style="color:${col}">${o.incidencia}</span> a ${o.organ}</div>
      <div class="t-producte">${o.notes || ''}</div></div>
      <button class="btn btn-danger" onclick="eliminarObservacio(${i}, '${malaltia}')">Eliminar</button></div>`;
  }).join('');
}

const FASE_FILE = 'fase_fenologica.json';

// Resistència ontogènica del RAÏM (Gadoury, Seem, Ficke & Wilcox, 2003).
// Les inflorescències i les baies joves són molt susceptibles fins que el gra
// fa 3-4 mm (BBCH 75); a partir d'aquí són gairebé immunes, i amb el raïm
// tancat (BBCH 77) la resistència és pràcticament total. Només el fruit
// inoculat dins les 2 setmanes posteriors a la floració desenvolupa oïdi greu.
//
// El criteri antic dels °Brix (susceptible fins a 8, esporulació fins a 15) és
// justament el que aquell treball va corregir: la resistència apareix unes 6
// setmanes abans d'arribar als 8 °Brix.
//
// ATENCIÓ: aquests factors valen per al RAÏM. La fulla no té resistència
// ontogènica equivalent i es valora amb l'índex climàtic sense multiplicar.
const MULTIPLIERS = {
  1: 1.0,   // Brotació a pre-floració: inflorescències susceptibles
  2: 1.3,   // Floració i quallat: màxima susceptibilitat
  3: 0.3,   // Creixement del gra: passa BBCH 75, gairebé immune
  4: 0.05,  // Tancament del raïm (BBCH 77): resistència gairebé total
  5: 0.0    // Envero i maduració: immunitat ontogènica
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

// ── Model OiDiag / VitiMeteo-Oidium (Kast) ──────────────────────────────────
// Referència: Dubuis, Bloesch, Fabre, Viret, Mittaz, Bleyer i Krause (2014),
// "Lutte contre l'oïdium à l'aide du modèle VitiMeteo-Oidium", Revue suisse
// Vitic. Arboric. Hortic. 46(6): 368-375, basat en Kast (1997) i Kast & Bleyer.
//
// A diferència de Gubler-Thomas, OiDiag no modela el cicle biològic: calcula
// un índex de risc i, sobretot, en deriva l'INTERVAL MÀXIM fins al tractament
// següent. L'índex és la mitjana del risc diari dels 7 últims dies, modulada
// per la sensibilitat del raïm.
//
// El risc diari meteorològic d'OiDiag no està publicat amb prou detall per
// reproduir-lo; aquí s'hi fa servir l'índex de Gubler-Thomas, que sí que ho
// està. La resta de l'estructura (mitjana de 7 dies, modulació ontogènica,
// sostre residual i taula d'intervals) segueix el model original.

// Sensibilitat del raïm segons la corba d'OiDiag (fig. 1 de la publicació):
// màxima de la floració al quallat i decreixent després.
const SENSIBILITAT_OIDIAG = {
  1: 0.60,  // Brotació a pre-floració: inflorescències en formació
  2: 1.00,  // Floració i quallat: sensibilitat màxima
  3: 0.50,  // Creixement del gra: decreixent
  4: 0.20,  // Tancament del raïm: sensibilitat residual
  5: 0.20   // Envero i maduració: es manté el sostre residual
};
// Després del tancament del raïm l'índex no pot superar aquest sostre.
const SOSTRE_RESIDUAL_OIDIAG = 20;

// Interval màxim recomanat entre dos tractaments (taula 2 de la publicació).
const INTERVALS_OIDIAG = {
  contacte:  { baix: [10, 12], mitja: [8, 10], fort: [6, 8]  },
  penetrant: { baix: [14, 16], mitja: [10, 14], fort: [8, 10] }
};

function nivellOidiag(index) {
  if (index > 66) return 'fort';
  if (index > 33) return 'mitja';
  return 'baix';
}

function calcularIndexOidiag(fase) {
  // Mitjana del risc diari dels 7 últims dies. El col·lector ja la calcula;
  // si no hi és (dades antigues) es fa aquí sobre els registres.
  let mitjana7;
  if (ALL.index_oidiag_meteo && ALL.index_oidiag_meteo.length) {
    mitjana7 = ALL.index_oidiag_meteo[ALL.index_oidiag_meteo.length - 1] || 0;
  } else {
    const n = Math.min(7 * 48, ALL.index_gt.length);
    const tall = ALL.index_gt.slice(-n).filter(v => v !== null && !isNaN(v));
    mitjana7 = tall.length ? tall.reduce((a, b) => a + b, 0) / tall.length : 0;
  }

  const sens = SENSIBILITAT_OIDIAG[fase] !== undefined ? SENSIBILITAT_OIDIAG[fase] : 1.0;
  let index = mitjana7 * sens;
  if (fase >= 4) index = Math.min(index, SOSTRE_RESIDUAL_OIDIAG);
  return { index: Math.round(index), mitjana7: Math.round(mitjana7), sens: sens };
}

function ultimTractamentOidi() {
  if (!ALL.tractaments || !ALL.tractaments.length) return null;
  const dels = ALL.tractaments
    .filter(t => t.malalties && t.malalties.includes('oidio'))
    .map(t => ({ ...t, _d: new Date(t.data) }))
    .sort((a, b) => a._d - b._d);
  return dels.length ? dels[dels.length - 1] : null;
}

function renderAlertaOidiag(fase) {
  const box = document.getElementById('oidiag-box');
  if (!box) return;

  const { index, mitjana7, sens } = calcularIndexOidiag(fase);
  const nivell = nivellOidiag(index);
  const etiqueta = { baix: 'BAIX', mitja: 'MITJÀ', fort: 'FORT' }[nivell];
  const color = { baix: '#22c55e', mitja: '#f59e0b', fort: '#ef4444' }[nivell];

  const ultim = ultimTractamentOidi();
  const tipus = ultim && ultim.tipus === 'penetrant' ? 'penetrant' : 'contacte';
  const [imin, imax] = INTERVALS_OIDIAG[tipus][nivell];

  // El model només val per a parcel·les sanes: amb símptomes visibles no
  // s'ha d'espaiar cap tractament.
  const teSimptomes = (window.OBSERVACIONS_OIDI || [])
    .some(o => o.incidencia && o.incidencia !== 'cap');

  let cos;
  if (!ultim) {
    cos = `<p>Encara no hi ha cap tractament d'oïdi registrat. El model calcula
           l'interval a partir de l'últim tractament, així que registra'n un
           per obtenir la data límit del següent.</p>`;
  } else {
    const dataUltim = new Date(ultim.data);
    const limit = new Date(dataUltim.getTime() + imax * 86400000);
    const recomanat = new Date(dataUltim.getTime() + imin * 86400000);
    const avui = new Date();
    const dies = Math.ceil((limit - avui) / 86400000);

    const fmt = d => d.toLocaleDateString('ca-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
    let estat, colorEstat;
    if (dies < 0)      { estat = `Termini superat fa ${Math.abs(dies)} dies`; colorEstat = '#ef4444'; }
    else if (dies <= 2){ estat = `Queden ${dies} dies`;                        colorEstat = '#f59e0b'; }
    else               { estat = `Queden ${dies} dies`;                        colorEstat = '#22c55e'; }

    cos = `
      <div style="display:flex;flex-wrap:wrap;gap:20px;margin-bottom:10px">
        <div><div style="font-size:11px;color:var(--muted)">ÚLTIM TRACTAMENT</div>
             <b>${fmt(dataUltim)}</b><br>
             <span style="font-size:12px;color:var(--muted)">${ultim.producte} (${tipus})</span></div>
        <div><div style="font-size:11px;color:var(--muted)">INTERVAL RECOMANAT</div>
             <b>${imin}-${imax} dies</b><br>
             <span style="font-size:12px;color:var(--muted)">risc ${etiqueta} · ${tipus}</span></div>
        <div><div style="font-size:11px;color:var(--muted)">RENOVAR ENTRE</div>
             <b>${fmt(recomanat)}</b> i <b>${fmt(limit)}</b><br>
             <span style="font-size:12px;color:${colorEstat};font-weight:600">${estat}</span></div>
      </div>`;
  }

  const avis = teSimptomes ? `
      <div style="margin-top:10px;padding:10px;border-radius:6px;
                  background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3)">
        <b style="color:#ef4444">Hi ha símptomes registrats a la parcel·la.</b>
        El model només dona indicacions per a vinyes sanes: amb la malaltia
        instal·lada no s'han d'espaiar els tractaments en cap cas.
      </div>` : '';

  box.innerHTML = `
    <div class="card" style="margin-bottom:24px;border-left:3px solid ${color}">
      <div class="card-title">Alerta de tractament · model OiDiag (VitiMeteo)</div>
      <div style="display:flex;align-items:baseline;gap:10px;margin:12px 0">
        <span style="font-size:30px;font-weight:700;color:${color}">${index}%</span>
        <span style="font-size:14px;font-weight:600;color:${color}">RISC ${etiqueta}</span>
        <span style="font-size:12px;color:var(--muted)">
          mitjana de 7 dies ${mitjana7}% × sensibilitat del raïm ${sens}
          ${fase >= 4 ? ' · sostre residual 20%' : ''}</span>
      </div>
      ${cos}
      ${avis}
      <div style="font-size:11px;color:var(--muted);margin-top:10px;line-height:1.5">
        L'índex és la mitjana del risc dels 7 últims dies, per això evoluciona a poc a poc.
        L'interval surt de la taula de Dubuis et al. (2014) segons el nivell de risc i si
        l'últim producte era de contacte o penetrant.
      </div>
    </div>`;
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
  const idxClima = ALL.index_gt[ALL.index_gt.length - 1] || 0;   // risc de FULLA
  const idxRaim  = idxClima * mult;                              // risc de RAÏM

  // Llindars oficials de UC Davis sobre l'escala 0-100
  let riscKast = "BAIX";
  let colorKast = "#22c55e";
  if (idxRaim > 60) { riscKast = "ALT"; colorKast = "#ef4444"; }
  else if (idxRaim > 30) { riscKast = "MODERAT"; colorKast = "#f59e0b"; }
  
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
    document.getElementById('kast-ui').innerText =
      `Índex ${idxRaim.toFixed(0)}/100 (clima ${idxClima.toFixed(0)} × ${mult} per fase)`;
  }

  // El marge del KPI segueix el risc del RAÏM, que pot ser molt diferent del
  // risc climàtic: amb resistència ontogènica activa, verd sobre clima vermell.
  const kpiRaim = document.getElementById('kpi-raim');
  if (kpiRaim) kpiRaim.style.borderLeftColor = isProtected ? '#22c55e' : colorKast;

  // Alerta d'interval de tractament segons OiDiag
  renderAlertaOidiag(currentFase);
  
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
  } else if (idxRaim > 60) {
     recomBox.innerHTML = `
<div class="recom-box warning" style="margin-bottom:0">
  <div class="recom-icon">⚠️</div>
  <div class="recom-content">
    <h4>Tractament recomanat — risc al raïm ${riscKast}</h4>
    <p>El raïm és en una fase susceptible i l'índex climàtic és alt (${idxClima.toFixed(0)}/100).
       Es recomana tractar per protegir el fruit.</p>
    <ul>
      <li><strong>Sofre en pols:</strong> 20-30 kg/ha. (Evitar si T &gt; 30°C).</li>
      <li><strong>Sofre mullable:</strong> Dosi al 0.25-0.75%.</li>
      <li><strong>Sistèmics/Penetrants:</strong> Triazols alternant famílies.</li>
    </ul>
  </div>
</div>`;
  } else if (idxClima > 60) {
     // El raïm ja no és susceptible però la vegetació sí: el cas que abans
     // quedava amagat darrere d'un únic indicador.
     const motiu = currentFase === 5
        ? "El raïm és en envero/maduració i ja no admet infeccions noves."
        : "El raïm ha superat la fase susceptible (resistència ontogènica).";
     recomBox.innerHTML = `
<div class="recom-box info" style="margin-bottom:0; background:rgba(245,158,11,0.08); border-color:rgba(245,158,11,0.3)">
  <div class="recom-icon">🍃</div>
  <div class="recom-content">
    <h4>Raïm protegit, però la fulla no</h4>
    <p>${motiu} En canvi l'índex climàtic és <b>${idxClima.toFixed(0)}/100</b>: les condicions
       són molt favorables per a l'oïdi i les fulles joves segueixen sent susceptibles.</p>
    <p>No cal tractar per protegir el fruit, però convé vigilar la vegetació: l'oïdi foliar
       redueix la fotosíntesi i, sobretot, forma els cleistotecis que hivernen a l'escorça i
       engeguen l'epidèmia de la campanya vinent. El desfullat a la zona de raïms hi ajuda,
       perquè exposa miceli i conidis a la radiació UV.</p>
  </div>
</div>`;
  } else {
     recomBox.innerHTML = `
<div class="recom-box" style="margin-bottom:0">
  <div class="recom-icon">✅</div>
  <div class="recom-content">
    <h4>Risc sota control</h4>
    <p>Ni el raïm ni la vegetació presenten risc alt ara mateix
       (índex climàtic ${idxClima.toFixed(0)}/100). Mantingues l'estratègia preventiva habitual.</p>
  </div>
</div>`;
  }
}



// Init
document.addEventListener('DOMContentLoaded', async () => {
  // El mapa necessita ALL (definit al <script> inline de la pàgina) i Leaflet,
  // tots dos ja disponibles quan es dispara DOMContentLoaded amb app.js diferit.
  if (document.getElementById('map')) initMap();

  const sel = document.getElementById('sel-fase');
  if(sel) {
     const st = await llegirFase();
     sel.value = st.activa_oidi || 'auto_moscatell';
     updateKastRisk(sel.value, st.varietats || {});
  }
  await initPhenologyIndex();
});
