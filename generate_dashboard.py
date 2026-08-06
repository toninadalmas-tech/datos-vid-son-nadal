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


# ═════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT COMÚ
# ═════════════════════════════════════════════════════════════════════════════






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
  <link rel="stylesheet" href="assets/style.css">
  <script src="assets/app.js"></script>
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
    risc_botritis = str(ultima.get("risc_botritis", "baix"))
    color_botritis = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_botritis, "#7a7269")
    risc_blackrot = str(ultima.get("risc_blackrot", "baix"))
    color_blackrot = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_blackrot, "#7a7269")
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
        <span><span class="dot" style="background:{color_botritis}"></span>Botritis</span>
        <span style="color:{color_botritis};font-weight:600">{risc_botritis.upper()}</span>
      </div>
      <div class="crop-stat">
        <span><span class="dot" style="background:{color_blackrot}"></span>Black Rot</span>
        <span style="color:{color_blackrot};font-weight:600">{risc_blackrot.upper()}</span>
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
    risc_botritis = str(ultima.get("risc_botritis", "baix"))
    color_botritis = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_botritis, "#7a7269")
    risc_blackrot = str(ultima.get("risc_blackrot", "baix"))
    color_blackrot = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_blackrot, "#7a7269")
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
    parts.append("const MALALTIA_FILTRE = 'oidio';")
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
    risc_botritis = str(ultima.get("risc_botritis", "baix"))
    color_botritis = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_botritis, "#7a7269")
    risc_blackrot = str(ultima.get("risc_blackrot", "baix"))
    color_blackrot = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_blackrot, "#7a7269")
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
    parts.append("const MALALTIA_FILTRE = 'mildiu';")
    parts.append("setFilter('7d');")
    parts.append("</script>")
    parts.append("</body>\n</html>")

    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  PÀGINA: BOTRITIS (sense model)
# ═════════════════════════════════════════════════════════════════════════════

def generar_botritis(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")
    risc   = str(ultima.get("risc_botritis", "baix"))
    risc_color = {"baix":"#22c55e","moderat":"#f59e0b","alt":"#ef4444"}.get(risc, "#6b7280")
    
    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Botritis · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("botritis"))
    parts.append("<main>")
    
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>Botritis</h1>
    <div class="sub">Botrytis cinerea · Model Broome (1995) · {ts_act}</div>
  </div>
  <span class="badge" style="color:{risc_color};border-color:{risc_color}">Risc: {risc.upper()}</span>
</div>

<div class="card" style="margin-bottom:24px;">
  {generar_filtre_bar()}
  <div style="height:350px;width:100%;position:relative;">
    <canvas id="chartModel"></canvas>
  </div>
</div>
""")
    parts.append(generar_recomanacio_tractament("botritis"))
    parts.append(generar_tractaments_section("botritis"))
    parts.append("</main>")
    parts.append(generar_footer())
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append("const MALALTIA_FILTRE = 'botritis';")
    parts.append("""let chartModel;
function buildCharts(start, end) {
  let L = ALL.labels.slice(start, end);
  let R = ALL.risc_botritis_pct.slice(start, end);
  
  if (chartModel) chartModel.destroy();
  
  const ctx = document.getElementById('chartModel');
  if(!ctx) return;
  
  chartModel = new Chart(ctx, {
    type: 'line',
    data: {
      labels: L,
      datasets: [{
        label: 'Risc Botritis (%)',
        data: R,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245,158,11,0.2)',
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 100 }
      }
    }
  });
}
""")
    parts.append("if (typeof setFilter !== 'undefined') { setFilter('7d'); }")
    parts.append("</script>")
    parts.append("</body>\n</html>")
    return "\n".join(parts)

def generar_blackrot(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")
    risc   = str(ultima.get("risc_blackrot", "baix"))
    risc_color = {"baix":"#22c55e","moderat":"#f59e0b","alt":"#ef4444"}.get(risc, "#6b7280")
    
    parts = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ca\">")
    parts.append(generar_head("Black Rot · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("blackrot"))
    parts.append("<main>")
    
    parts.append(f"""
<div class="page-header">
  <div>
    <h1>Black Rot</h1>
    <div class="sub">Guignardia bidwellii · Model Spotts (1977) · {ts_act}</div>
  </div>
  <span class="badge" style="color:{risc_color};border-color:{risc_color}">Risc: {risc.upper()}</span>
</div>

<div class="card" style="margin-bottom:24px;">
  {generar_filtre_bar()}
  <div style="height:350px;width:100%;position:relative;">
    <canvas id="chartModel"></canvas>
  </div>
</div>
""")
    parts.append(generar_recomanacio_tractament("blackrot"))
    parts.append(generar_tractaments_section("blackrot"))
    parts.append("</main>")
    parts.append(generar_footer())
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append("const MALALTIA_FILTRE = 'blackrot';")
    parts.append("""let chartModel;
function buildCharts(start, end) {
  let L = ALL.labels.slice(start, end);
  // Spotts model returns string: 'baix', 'moderat', 'alt'
  // We map it to numeric values to plot
  let R_num = ALL.risc_blackrot.slice(start, end).map(r => r === 'alt' ? 3 : r === 'moderat' ? 2 : 1);
  let colors = R_num.map(r => r === 3 ? 'rgba(239,68,68,0.8)' : r === 2 ? 'rgba(245,158,11,0.8)' : 'rgba(34,197,94,0.5)');
  
  if (chartModel) chartModel.destroy();
  
  const ctx = document.getElementById('chartModel');
  if(!ctx) return;
  
  chartModel = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: L,
      datasets: [{
        label: 'Risc Black Rot',
        data: R_num,
        backgroundColor: colors
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { 
          min: 0, 
          max: 3, 
          ticks: { callback: v => ['', 'Baix', 'Moderat', 'Alt'][v] || v }
        }
      }
    }
  });
}
""")
    parts.append("if (typeof setFilter !== 'undefined') { setFilter('7d'); }")
    parts.append("</script>")
    parts.append("</body>\n</html>")
    return "\n".join(parts)



def _hex_to_rgb(hex_col: str) -> tuple:
    if not hex_col: return (0,0,0)
    hex_col = hex_col.lstrip('#')
    return tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = carregar_dades()

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(generar_index(df))

    with open(os.path.join(OUTPUT_DIR, "vinya.html"), "w", encoding="utf-8") as f:
        f.write(generar_vinya(df))

    with open(os.path.join(OUTPUT_DIR, "oidi.html"), "w", encoding="utf-8") as f:
        f.write(generar_oidi(df))

    with open(os.path.join(OUTPUT_DIR, "mildiu.html"), "w", encoding="utf-8") as f:
        f.write(generar_mildiu(df))

    with open(os.path.join(OUTPUT_DIR, "botritis.html"), "w", encoding="utf-8") as f:
        f.write(generar_botritis(df))

    with open(os.path.join(OUTPUT_DIR, "blackrot.html"), "w", encoding="utf-8") as f:
        f.write(generar_blackrot(df))

    print(f"  OK Dashboard generat a {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
