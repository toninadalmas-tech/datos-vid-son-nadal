import re

# 1. Update generate_dashboard.py
with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    dash_text = f.read()

# Add get_annual_gdd function
gdd_func = """
def get_annual_gdd(lat=39.5146, lon=3.2124) -> float:
    import datetime, requests
    try:
        now = datetime.datetime.now()
        start_date = f"{now.year}-03-01"
        end_date = now.strftime("%Y-%m-%d")
        if now.month < 3: return 0.0
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {"latitude": lat, "longitude": lon, "start_date": start_date, "end_date": end_date, "daily": "temperature_2m_mean", "timezone": "Europe/Madrid"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "daily" not in data or "temperature_2m_mean" not in data["daily"]: return -1.0
        
        return round(sum(max(t - 10.0, 0.0) for t in data["daily"]["temperature_2m_mean"] if t is not None), 1)
    except Exception as e:
        return -1.0

"""
dash_text = dash_text.replace('def calc_ET0_hargreaves(tmin, tmax, tmean, doy, lat=39.5146):', gdd_func + 'def calc_ET0_hargreaves(tmin, tmax, tmean, doy, lat=39.5146):')

# Update preparar_dades_json to include gdd_anual
dash_text = dash_text.replace('"risc_blackrot":     risc_blackrot,', '"risc_blackrot":     risc_blackrot,\n        "gdd_anual":        get_annual_gdd(),')

# Update HTML in generar_oidi
old_select = """  <select id="sel-fase" onchange="canviFase(this.value)">
    <option value="1">🌱 Brotació a Pre-floració (Risc climàtic complet - Només fulles)</option>
    <option value="2">🌼 Floració i Quallat (Risc MÀXIM - Raïm molt sensible)</option>
    <option value="3">🍇 Creixement del gra (Risc Alt - Raïm sensible)</option>
    <option value="4">🟢 Tancament del raïm (Risc Moderat - Inici de resistència)</option>
    <option value="5">🟣 Envero i Maduració (Risc NUL pel raïm - Resistència total)</option>
  </select>
  <div style="font-size:12px;color:var(--muted);margin-top:8px;">
    L'edat del raïm modifica el risc real d'infecció calculat pel model Gubler. Selecciona la fase per ajustar la predicció i les recomanacions.
  </div>"""

new_select = """  <select id="sel-fase" onchange="canviFase(this.value)" style="margin-bottom:8px">
    <optgroup label="🤖 Automàtic (Predicció per GDD)">
        <option value="auto_moscatell">⚙️ Moscatell (Primerenca)</option>
        <option value="auto_prensal">⚙️ Premsal Blanc</option>
        <option value="auto_callet">⚙️ Callet</option>
        <option value="auto_manto_negro">⚙️ Manto Negro</option>
        <option value="auto_cabernet">⚙️ Cabernet (Tardana)</option>
    </optgroup>
    <optgroup label="🖐️ Manual (Forçar Estat)">
        <option value="1">🌱 Fase 1: Brotació a Pre-floració</option>
        <option value="2">🌼 Fase 2: Floració i Quallat</option>
        <option value="3">🍇 Fase 3: Creixement del gra</option>
        <option value="4">🟢 Fase 4: Tancament del raïm</option>
        <option value="5">🟣 Fase 5: Envero i Maduració</option>
    </optgroup>
  </select>
  <div id="auto-fase-lbl" style="display:none; font-size:13px; font-weight:600; color:#3b82f6; margin-bottom:8px; padding:6px 10px; background:rgba(59,130,246,0.1); border-radius:4px;"></div>
  <div style="font-size:12px;color:var(--muted);">
    L'edat del raïm modifica el risc real d'infecció. Pots deixar que el sistema ho calculi automàticament o forçar-ho a mà.
  </div>"""

dash_text = dash_text.replace(old_select, new_select)

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(dash_text)


# 2. Update app.js
with open("docs/assets/app.js", "r", encoding="utf-8") as f:
    app_text = f.read()

js_logic = """const VARIETATS_GDD = {
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

function updateKastRisk(faseVal) {
  let currentFase;
  const lbl = document.getElementById('auto-fase-lbl');
  
  if (typeof faseVal === 'string' && faseVal.startsWith('auto_')) {
     currentFase = getFaseFromGDD(faseVal);
     if (lbl) {
        const noms = ['N/A','Brotació a Pre-floració','Floració i Quallat','Creixement del gra','Tancament del raïm','Envero i Maduració'];
        lbl.innerText = `🤖 Fase detectada: ${noms[currentFase]} (GDD acumulat: ${ALL.gdd_anual})`;
        lbl.style.display = 'block';
     }
  } else {
     currentFase = parseInt(faseVal);
     if (lbl) lbl.style.display = 'none';
  }
  
  const mult = MULTIPLIERS[currentFase];"""

app_text = app_text.replace("""function updateKastRisk(faseVal) {
  const currentFase = parseInt(faseVal);
  const mult = MULTIPLIERS[currentFase];""", js_logic)

# Replace 'parseInt(faseVal)' inside guardarFaseRepo
app_text = app_text.replace("fase: parseInt(faseVal)", "fase: faseVal")

with open("docs/assets/app.js", "w", encoding="utf-8") as f:
    f.write(app_text)

print("Patch applied to dashboard and JS")
