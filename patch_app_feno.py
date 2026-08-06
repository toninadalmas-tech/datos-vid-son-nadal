import re

with open("docs/assets/app.js", "r", encoding="utf-8") as f:
    app_text = f.read()

# Replace llegirFase and guardarFaseRepo
js_new_logic = """
async function llegirFase() {
  if (!token() || !repo()) return { varietats: {}, activa_oidi: 'auto_moscatell' };
  try {
    const r = await fetch(`https://api.github.com/repos/${repo()}/contents/${FASE_FILE}`,
      { headers: { Authorization: `Bearer ${token()}`, Accept: 'application/vnd.github+json' } });
    if (!r.ok) throw new Error('No trobat');
    const d = await r.json();
    const txt = decodeURIComponent(escape(atob(d.content)));
    const contingut = JSON.parse(txt);
    if (contingut.fase !== undefined) {
       // Migrate old format
       return { varietats: {}, activa_oidi: contingut.fase || 'auto_moscatell' };
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
"""

app_text = re.sub(r"async function llegirFase\(\) \{.*?(?=const VARIETATS_GDD)", js_new_logic, app_text, flags=re.DOTALL)

# Update DOMContentLoaded Init
# Find:
# document.addEventListener('DOMContentLoaded', async () => {
#   const sel = document.getElementById('sel-fase');
#   if(sel) {
#      const f = await llegirFase();
#      sel.value = f;
#      updateKastRisk(f);
#   }
# });
init_logic = """document.addEventListener('DOMContentLoaded', async () => {
  const sel = document.getElementById('sel-fase');
  if(sel) {
     const st = await llegirFase();
     sel.value = st.activa_oidi || 'auto_moscatell';
     updateKastRisk(sel.value, st.varietats || {});
  }
  await initPhenologyIndex();
});"""

app_text = re.sub(r"document\.addEventListener\('DOMContentLoaded', async \(\) => \{\n  const sel = document\.getElementById\('sel-fase'\);.*?\}\);\n", init_logic + '\n', app_text, flags=re.DOTALL)

# Update updateKastRisk to accept manual states
# function updateKastRisk(faseVal) -> function updateKastRisk(faseVal, varietatsOverrides)
app_text = app_text.replace("function updateKastRisk(faseVal) {", "function updateKastRisk(faseVal, varietatsOverrides = {}) {")

# In updateKastRisk:
# if (typeof faseVal === 'string' && faseVal.startsWith('auto_')) {
#    currentFase = getFaseFromGDD(faseVal);
# Replace with logic that checks varietatsOverrides
new_kast_logic = """  if (typeof faseVal === 'string' && faseVal.startsWith('auto_')) {
     const isManual = varietatsOverrides[faseVal] !== undefined && varietatsOverrides[faseVal] !== null;
     currentFase = isManual ? varietatsOverrides[faseVal] : getFaseFromGDD(faseVal);
     
     if (lbl) {
        const noms = ['N/A','Brotació a Pre-floració','Floració i Quallat','Creixement del gra','Tancament del raïm','Envero i Maduració'];
        lbl.innerText = isManual ? `🖐️ Fase forçada manualment: ${noms[currentFase]}` : `🤖 Fase detectada automàticament: ${noms[currentFase]} (GDD acumulat: ${ALL.gdd_anual})`;
        lbl.style.display = 'block';
     }
  } else {"""

app_text = re.sub(r"  if \(typeof faseVal === 'string' && faseVal\.startsWith\('auto_'\)\) \{.*?  \} else \{", new_kast_logic, app_text, flags=re.DOTALL)

# Also remove canviFase from the bottom if I added it in js_new_logic
# wait, there's already an async function canviFase(val) below?
# Let's remove the old canviFase.
app_text = re.sub(r"async function canviFase\(faseVal\) \{.*?\}", "", app_text, flags=re.DOTALL)


with open("docs/assets/app.js", "w", encoding="utf-8") as f:
    f.write(app_text)

print("app.js patched")
