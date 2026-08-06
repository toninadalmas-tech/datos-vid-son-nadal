"""
fetch_openmeteo.py – Obté dades complementàries d'Open-Meteo
=============================================================
Llegeix data/historial.csv per determinar el rang de dates,
consulta l'API gratuïta d'Open-Meteo i afegeix columnes noves
al CSV si encara no existeixen:

  - radiacio_solar_wm2   (shortwave_radiation, W/m²)
  - radiacio_directa_wm2 (direct_radiation, W/m²)
  - index_uv             (uv_index)
  - humitat_sol_0_7      (soil_moisture_0_to_7cm, m³/m³)
  - et0_openmeteo        (et0_fao_evapotranspiration, mm)

Coordenades: Son Nadal, Felanitx (39.5146°N, 3.15405°E)

Execució:
  python fetch_openmeteo.py
"""

import pandas as pd
import requests
import sys
import os

# ── Configuració ─────────────────────────────────────────────────────────────
LAT = 39.5146
LON = 3.15405
CSV_PATH = "data/historial.csv"
TIMEZONE = "Europe/Madrid"

# Variables horàries a obtenir d'Open-Meteo
HOURLY_VARS = [
    "shortwave_radiation",
    "direct_radiation",
    "uv_index",
    "soil_moisture_0_to_7cm",
    "et0_fao_evapotranspiration",
]

# Mapatge: nom Open-Meteo → nom columna al CSV
COL_MAP = {
    "shortwave_radiation":        "radiacio_solar_wm2",
    "direct_radiation":           "radiacio_directa_wm2",
    "uv_index":                   "index_uv",
    "soil_moisture_0_to_7cm":     "humitat_sol_0_7",
    "et0_fao_evapotranspiration": "et0_openmeteo",
}

def fetch_openmeteo(start_date: str, end_date: str) -> pd.DataFrame:
    """Consulta l'API d'Open-Meteo i retorna un DataFrame amb timestamp + variables."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  LAT,
        "longitude": LON,
        "hourly":    ",".join(HOURLY_VARS),
        "timezone":  TIMEZONE,
        "start_date": start_date,
        "end_date":   end_date,
    }
    
    print(f"  Consultant Open-Meteo: {start_date} -> {end_date} ...")
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    
    hourly = data.get("hourly", {})
    if "time" not in hourly:
        print("  [!] Resposta buida d'Open-Meteo")
        return pd.DataFrame()
    
    df = pd.DataFrame({"timestamp_om": pd.to_datetime(hourly["time"])})
    for var in HOURLY_VARS:
        col = COL_MAP[var]
        df[col] = hourly.get(var, [None] * len(df))
    
    return df


def main():
    if not os.path.exists(CSV_PATH):
        print(f"  [X] No existeix {CSV_PATH}")
        sys.exit(1)
    
    # Llegir CSV existent
    df = pd.read_csv(CSV_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True)
    
    # Rang de dates
    start_date = df["ts"].min().strftime("%Y-%m-%d")
    end_date   = df["ts"].max().strftime("%Y-%m-%d")
    
    # Obtenir dades d'Open-Meteo
    om = fetch_openmeteo(start_date, end_date)
    if om.empty:
        print("  [X] Sense dades d'Open-Meteo")
        sys.exit(0)
    
    # Les dades d'Open-Meteo són horàries (cada 60 min).
    # El nostre CSV és cada 30 min.
    # Estratègia: Per a cada registre del CSV, busquem l'hora 
    # Open-Meteo més propera (forward fill, l'hora anterior).
    
    # Arrodonir el timestamp del CSV a l'hora sencera per fer el merge
    df["ts_hora"] = df["ts"].dt.floor("h")
    
    # Preparar Open-Meteo per merge
    om = om.rename(columns={"timestamp_om": "ts_hora"})
    
    # Eliminar columnes si ja existien (per actualitzar-les)
    for col in COL_MAP.values():
        if col in df.columns:
            df = df.drop(columns=[col])
    
    # Merge
    df = df.merge(om, on="ts_hora", how="left")
    
    # Netejar columnes auxiliars
    df = df.drop(columns=["ts", "ts_hora"])
    
    # Guardar
    df.to_csv(CSV_PATH, index=False)
    
    # Resum
    new_cols = [c for c in COL_MAP.values() if c in df.columns]
    n_valid = df[new_cols].notna().sum().to_dict()
    print(f"  OK {len(new_cols)} columnes afegides a {CSV_PATH}:")
    for col, count in n_valid.items():
        print(f"      {col}: {count}/{len(df)} registres")


if __name__ == "__main__":
    main()
