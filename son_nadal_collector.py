"""
Col·lector diari - Estació Son Nadal (Felanitx, CAIB)
======================================================
Les dades reals estan incrustades a l'HTML de la pàgina de la gràfica
com a JSON de Google Charts. Llegim directament d'aquí, ignorant el
botó CSV que té un bug al servidor.

URL de cada sensor:
  https://www.estacionsclimatiquesiibb.cat/weatherstationlast24chart/117202/temperature/
  https://www.estacionsclimatiquesiibb.cat/weatherstationlast24chart/117202/humidity/
  https://www.estacionsclimatiquesiibb.cat/weatherstationlast24chart/117202/rain/
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os, re, json
import urllib3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def carregar_tractaments():
    try:
        with open("tractaments.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("tractaments", [])
    except Exception:
        return []

def obtenir_periodes_proteccio(tractaments, malaltia="oidio", dies_proteccio=10):
    periodes = []
    for t in tractaments:
        if malaltia in t.get("malalties", []):
            try:
                # La data sol venir com "YYYY-MM-DDTHH:MM"
                inici = pd.to_datetime(t["data"])
                fi = inici + timedelta(days=dies_proteccio)
                periodes.append((inici, fi))
            except Exception:
                pass
    return periodes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Configuració ──────────────────────────────────────────────────────────────
BASE_URL     = "https://www.estacionsclimatiquesiibb.cat"
ESTACIO_ID   = "117202"
CSV_HISTORIAL = "data/historial.csv"

SENSORS = {
    "temperatura_c":   "temperature",
    "humitat_pct":     "humidity",
    "precipitacio_mm": "rain",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ca-ES,ca;q=0.9,es;q=0.8",
}


# ── Descàrrega i parsejat ─────────────────────────────────────────────────────
def descarregar_sensor(nom: str, sensor: str) -> pd.DataFrame | None:
    """
    Descarrega la pàgina HTML del sensor i extreu el JSON de Google Charts
    que conté les dades reals (jsonDataWeatherStationLast24Chart).
    """
    # Primer POST al formulari per establir el sensor actiu
    url_form = f"{BASE_URL}/weatherstationlast24hformview/form"
    url_chart = f"{BASE_URL}/weatherstationlast24chart/{ESTACIO_ID}/{sensor}/"

    s = requests.Session()
    try:
        # POST al formulari (simula seleccionar estació + sensor + Enviar)
        s.post(
            url_form,
            data={"weatherstation_id": ESTACIO_ID, "sensor": sensor},
            headers={**HEADERS, "Referer": f"{BASE_URL}/weatherstationlast24hformview/form"},
            verify=False, timeout=20
        )
        # GET de la pàgina de la gràfica
        r = s.get(url_chart, headers={**HEADERS, "Referer": url_form},
                  verify=False, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] {nom}: error connexió - {e}")
        return None

    # Extreu el JSON de Google Charts de l'HTML
    match = re.search(
        r'var\s+jsonDataWeatherStationLast24Chart\s*=\s*(\{.*?\})\s*\n',
        r.text, re.DOTALL
    )
    if not match:
        print(f"  [ERROR] {nom}: no s'ha trobat jsonDataWeatherStationLast24Chart a l'HTML")
        print(f"     Comprova que la URL retorna la gràfica: {url_chart}")
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"  [ERROR] {nom}: error parsejant JSON - {e}")
        return None

    # Converteix les files del JSON a DataFrame
    # Format: {"rows": [{"c": [{"v": "13:33"}, {"v": 39.2}]}, ...]}
    files = []
    for row in data.get("rows", []):
        try:
            hora  = row["c"][0]["v"]   # ex: "13:33"
            valor = row["c"][1]["v"]   # ex: 39.2
            files.append({"hora": hora, nom: float(valor)})
        except (KeyError, TypeError, ValueError):
            pass

    if not files:
        print(f"  [ERROR] {nom}: JSON buit o format inesperat")
        return None

    df = pd.DataFrame(files)
    print(f"  [OK] {nom}: {len(df)} mesures")
    return df


# ── Construcció del DataFrame combinat ───────────────────────────────────────
def obtenir_dades() -> pd.DataFrame | None:
    """
    Descarrega els tres sensors, assigna timestamps complets
    (les hores del JSON no tenen data), arrodoneix a 30 min i combina.
    """
    ara = datetime.now(ZoneInfo('Europe/Madrid')).replace(tzinfo=None)
    ahir = ara - timedelta(hours=24)

    dfs = {}
    for nom, sensor in SENSORS.items():
        df = descarregar_sensor(nom, sensor)
        if df is None:
            continue

        # Assigna la data correcta a cada hora
        # Hores > hora actual → són d'ahir; hores <= hora actual → avui
        def hora_a_ts(hora_str):
            try:
                h, m = map(int, hora_str.split(":"))
                # Si l'hora és posterior a ara → és d'ahir
                ts_avui = ara.replace(hour=h, minute=m, second=0, microsecond=0)
                ts_ahir = ahir.replace(hour=h, minute=m, second=0, microsecond=0)
                return ts_ahir if ts_avui > ara else ts_avui
            except Exception:
                return None

        df["ts"] = df["hora"].apply(hora_a_ts)
        df = df.dropna(subset=["ts"])

        # Arrodoneix a 30 min
        df["ts30"] = df["ts"].dt.round("30min")

        # Agrupa: suma per pluja, mitjana per la resta
        es_pluja = "precipitacio" in nom
        df_agr = df.groupby("ts30")[nom].sum() if es_pluja else df.groupby("ts30")[nom].mean()
        df_agr = df_agr.reset_index()
        df_agr["timestamp"] = df_agr["ts30"].dt.strftime("%d/%m/%Y %H:%M")
        df_agr = df_agr.drop(columns=["ts30"])

        dfs[nom] = df_agr
        print(f"     -> {len(df_agr)} intervals de 30 min")

    if not dfs:
        return None

    # Merge inner per timestamp
    df_final = None
    for df_s in dfs.values():
        df_final = df_s if df_final is None else pd.merge(df_final, df_s, on="timestamp", how="inner")

    df_final = df_final.sort_values("timestamp").reset_index(drop=True)
    print(f"\n  -> Total: {len(df_final)} registres combinats")
    return df_final


# ── Model de Gubler ──────────────────────────────────────────────────────────
# Taula d'Unitats d'Infecció (UI) horàries segons T i HR
# Font: Gubler (1995), adaptat per a condicions mediterrànies
#
#           HR<40%  40-49%  50-69%  70-89%  >=90%
# <15°C       0       0       0       0       0
# 15-19°C     0       1       2       3       4
# 20-27°C     0       2       4       8      12    ← òptim infecció
# 28-35°C     0       1       2       3       4
# >35°C       0       0       0       0       0

def ui_horaria(t: float, hr: float) -> float:
    """
    Calcula les Unitats d'Infecció per a una hora donada.
    Retorna 0 si les condicions no són favorables.
    """
    if pd.isna(t) or pd.isna(hr):
        return 0.0
    if t < 15 or t > 35 or hr < 40:
        return 0.0

    # Factor HR: zona 0-3
    if hr >= 90:
        f_hr = 3
    elif hr >= 70:
        f_hr = 2
    elif hr >= 50:
        f_hr = 1
    else:
        f_hr = 0  # 40-49%: base

    base = [1, 2, 3, 4][f_hr]  # UI base per HR
    optim = 20 <= t <= 27       # rang òptim → dobla les UI
    return float(base * 2 if optim else base)


def calcular_gubler(df_tot: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula les UI horàries i les acumula sobre tot l'historial.

    Regles de reinici del comptador:
      - Pluja >= 2mm en una finestra de 30 min (els conidis es renten)
      - T > 35°C durant 3 intervals consecutius (6h+ de calor extrema)
      - Inici de cada temporada (1 de març): reinici manual recomanat

    Columnes afegides:
      ui_horaria     → UI d'aquesta hora (0–12)
      ui_acumulades  → UI acumulades des de l'últim reinici
      reinici_ui     → 1 si s'ha reiniciat el comptador en aquesta fila
      risc_gubler    → baix / moderat / alt / molt alt
    """
    df = df_tot.copy()
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = df.sort_values("ts").reset_index(drop=True)

    t_col  = pd.to_numeric(df["temperatura_c"],   errors="coerce")
    hr_col = pd.to_numeric(df["humitat_pct"],      errors="coerce")
    p_col  = pd.to_numeric(df["precipitacio_mm"],  errors="coerce").fillna(0)

    ui_h    = np.zeros(len(df))
    ui_acc  = np.zeros(len(df))
    reinici = np.zeros(len(df), dtype=int)

    acumulat = 0.0
    calor_cnt = 0  # comptador de intervals consecutius T > 35°C
    
    tractaments = carregar_tractaments()
    periodes_proteccio = obtenir_periodes_proteccio(tractaments, "oidio", 10)

    for i in range(len(df)):
        t  = t_col.iloc[i]
        hr = hr_col.iloc[i]
        p  = p_col.iloc[i]
        ts = df["ts"].iloc[i]

        # Comptador de calor extrema
        if not pd.isna(t) and t > 35:
            calor_cnt += 1
        else:
            calor_cnt = 0

        # Reinici per pluja o calor extrema prolongada
        if p >= 2.0 or calor_cnt >= 3:
            acumulat = 0.0
            reinici[i] = 1
            calor_cnt = 0

        ui = ui_horaria(t, hr)
        acumulat += ui
        
        # El model de Gubler té un límit màxim teòric (ex: 150), no s'acumula a l'infinit
        if acumulat > 150.0:
            acumulat = 150.0

        ui_h[i]   = ui
        ui_acc[i] = acumulat

    df["ui_horaria"]    = ui_h
    df["ui_acumulades"] = ui_acc.round(1)
    df["reinici_ui"]    = reinici

    # Nivells de risc basats en UI acumulades
    # Llindars estàndard Gubler per a Uncinula necator
    condicions_risc = [
        ui_acc >= 150,
        ui_acc >= 100,
        ui_acc >= 50,
    ]
    df["risc_gubler"] = np.select(
        condicions_risc,
        ["molt alt", "alt", "moderat"],
        default="baix"
    )

    # Manté compatibilitat amb columnes antigues
    df["hora_favorable_oidio"] = (ui_h > 0).astype(int)
    df["risc_infeccio"] = df["risc_gubler"]  # substitueix el model antic

    df = df.drop(columns=["ts"])
    return df


# ── Historial ─────────────────────────────────────────────────────────────────
def actualitzar_historial(df_nou: pd.DataFrame) -> pd.DataFrame:
    """
    Combina les dades noves amb l'historial existent i recalcula
    les UI acumulades sobre tot l'historial (per continuïtat).
    """
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CSV_HISTORIAL):
        df_old = pd.read_csv(CSV_HISTORIAL)
        # Elimina columnes calculades per recalcular-les netes
        cols_calc = ["ui_horaria", "ui_acumulades", "reinici_ui",
                     "risc_gubler", "hora_favorable_oidio", "risc_infeccio"]
        df_old = df_old.drop(columns=[c for c in cols_calc if c in df_old.columns])
        df_nou_base = df_nou.drop(columns=[c for c in cols_calc if c in df_nou.columns])
        df_tot = pd.concat([df_old, df_nou_base], ignore_index=True)
        df_tot = df_tot.drop_duplicates(subset=["timestamp"], keep="last")
    else:
        cols_calc = ["ui_horaria", "ui_acumulades", "reinici_ui",
                     "risc_gubler", "hora_favorable_oidio", "risc_infeccio"]
        df_tot = df_nou.drop(columns=[c for c in cols_calc if c in df_nou.columns])

    df_tot = df_tot.sort_values("timestamp").reset_index(drop=True)

    # Recalcula Gubler sobre TOT l'historial per mantenir continuïtat
    df_tot = calcular_gubler(df_tot)
    df_tot.to_csv(CSV_HISTORIAL, index=False)

    registres_nous = len(df_nou)
    print(f"  -> {registres_nous} registres nous | {len(df_tot)} totals -> {CSV_HISTORIAL}")
    return df_tot


# ── Resum ─────────────────────────────────────────────────────────────────────
def resum(df: pd.DataFrame):
    print(f"\n{'-'*50}")
    ult24 = df.tail(48)  # últimes 24h (registres de 30 min)
    print(f"  Últimes 24h  ({len(ult24)} registres)")
    for col, nom, unit in [
        ("temperatura_c",   "Temperatura", "°C"),
        ("humitat_pct",     "Humitat",     "%"),
        ("precipitacio_mm", "Pluja",       "mm"),
    ]:
        if col in ult24.columns:
            s = pd.to_numeric(ult24[col], errors="coerce").dropna()
            if len(s):
                print(f"  {nom:<12}: min={s.min():.1f}{unit}  "
                      f"max={s.max():.1f}{unit}  mitj={s.mean():.1f}{unit}")

    if "ui_acumulades" in df.columns:
        ui_actual = df["ui_acumulades"].iloc[-1]
        ui_24h    = ult24["ui_horaria"].sum() if "ui_horaria" in ult24.columns else 0
        risc      = df["risc_gubler"].iloc[-1] if "risc_gubler" in df.columns else "?"
        reinicios = int(df["reinici_ui"].sum()) if "reinici_ui" in df.columns else 0
        print(f"\n  -- Model Gubler --------------------------")
        print(f"  UI acumulades total : {ui_actual:.0f}")
        print(f"  UI últimes 24h      : {ui_24h:.0f}")
        print(f"  Risc actual         : {risc.upper()}")
        print(f"  Reinicios (pluja/T) : {reinicios}")
        print(f"  Llindars -> moderat>=50  alt>=100  molt alt>=150")
    print(f"{'-'*50}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Col·lector Son Nadal iniciat")
    print("-" * 50)
    print("-> Descarregant sensors des de Google Charts JSON...")

    df_nou = obtenir_dades()

    if df_nou is None or df_nou.empty:
        print("\n[WARNING] No s'han pogut obtenir dades.")
        raise SystemExit(1)

    df_historial = actualitzar_historial(df_nou)
    resum(df_historial)


if __name__ == "__main__":
    main()
