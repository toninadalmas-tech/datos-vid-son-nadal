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



# ── Historial ─────────────────────────────────────────────────────────────────
def actualitzar_historial(df_nou: pd.DataFrame) -> pd.DataFrame:
    import os
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CSV_HISTORIAL):
        df_old = pd.read_csv(CSV_HISTORIAL)
        df_tot = pd.concat([df_old, df_nou], ignore_index=True)
        df_tot = df_tot.drop_duplicates(subset=["timestamp"], keep="last")
    else:
        df_tot = df_nou

    df_tot = df_tot.sort_values("timestamp").reset_index(drop=True)
    df_tot.to_csv(CSV_HISTORIAL, index=False)

    registres_nous = len(df_nou)
    print(f"  -> {registres_nous} registres nous | {len(df_tot)} totals -> {CSV_HISTORIAL}")
    return df_tot


# ── Resum ─────────────────────────────────────────────────────────────────────
def resum(df: pd.DataFrame):
    print(f"\n{'-'*50}")
    ult24 = df.tail(48)
    print(f"  Últimes 24h  ({len(ult24)} registres)")
    for col, nom, unit in [
        ("temperatura_c",   "Temperatura", "°C"),
        ("humitat_pct",     "Humitat",     "%"),
        ("precipitacio_mm", "Pluja",       "mm"),
    ]:
        if col in ult24.columns:
            s = pd.to_numeric(ult24[col], errors="coerce").dropna()
            if len(s):
                print(f"  {nom:<12}: min={s.min():.1f}{unit}  max={s.max():.1f}{unit}  mitj={s.mean():.1f}{unit}")
    print(f"{'-'*50}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    from datetime import datetime
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
