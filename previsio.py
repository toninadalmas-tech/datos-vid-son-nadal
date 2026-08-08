"""
previsio.py – Projecció del risc als pròxims dies
==================================================
Els models són retrospectius: diuen el risc d'ahir. Però un tractament
preventiu s'aplica ABANS de la infecció, així que el que decideix és el
risc dels pròxims dies.

Aquest mòdul baixa la previsió horària d'Open-Meteo i hi aplica les
mateixes regles que als models observats, partint de l'estat actual:

  - Oïdi: continua l'índex de Gubler-Thomas des del valor d'avui
  - Mildiu: projecta pluja acumulada i condicions d'esporulació

Escriu data/previsio.csv amb una fila per dia previst.

Execució:
  python previsio.py
"""

import pandas as pd
import numpy as np
import requests
import os

import meteo_utils as mu
import oidi_collector as oidi
import mildiu_collector as mildiu

LAT, LON = 39.5146, 3.15405
TIMEZONE = "Europe/Madrid"
DIES_PREVISIO = 5          # Open-Meteo dona fins a 16; 5 ja és poc fiable al final
CSV_HISTORIAL = "data/historial.csv"
CSV_PREVISIO  = "data/previsio.csv"

HOURLY = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "shortwave_radiation",
]


def baixar_previsio(dies: int = DIES_PREVISIO) -> pd.DataFrame:
    """Previsió horària d'Open-Meteo a partir d'ara."""
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LAT, "longitude": LON,
            "hourly": ",".join(HOURLY),
            "timezone": TIMEZONE,
            "forecast_days": dies,
        },
        timeout=30,
    )
    r.raise_for_status()
    h = r.json().get("hourly", {})
    if "time" not in h:
        return pd.DataFrame()

    df = pd.DataFrame({
        "ts":                 pd.to_datetime(h["time"]),
        "temperatura_c":      h.get("temperature_2m"),
        "humitat_pct":        h.get("relative_humidity_2m"),
        "precipitacio_mm":    h.get("precipitation"),
        "radiacio_solar_wm2": h.get("shortwave_radiation"),
    })
    # Només ens interessa el futur
    return df[df["ts"] > pd.Timestamp.now()].reset_index(drop=True)


def projectar_oidi(prev: pd.DataFrame, index_inicial: float) -> pd.DataFrame:
    """
    Continua l'índex de Gubler-Thomas sobre la previsió.

    Aplica les mateixes regles que oidi_collector, partint de l'índex d'avui:
    l'epidèmia ja està declarada, així que no cal tornar a exigir l'arrencada.
    """
    dur = mu.durades(prev["ts"])
    t = pd.to_numeric(prev["temperatura_c"], errors="coerce")
    dins = t.between(oidi.T_OPT_MIN, oidi.T_OPT_MAX)
    ratxa = mu.ratxes(dins, dur)

    files, valor = [], float(index_inicial)
    for dia, g in prev.groupby(prev["ts"].dt.date):
        idx = g.index
        ratxa_max = float(ratxa[idx].max())
        min_calor = sum((dur[i] if pd.notna(dur[i]) else 1.0) * 60
                        for i in idx if pd.notna(t[i]) and t[i] >= oidi.T_CALOR)

        favorable = ratxa_max >= oidi.HORES_CONTINUES_MIN
        calor     = min_calor >= oidi.MINUTS_CALOR_LIMIT

        if favorable and calor:  delta = oidi.PUNTS_FAVORABLE + oidi.PUNTS_CALOR
        elif favorable:          delta = oidi.PUNTS_FAVORABLE
        elif calor:              delta = oidi.PUNTS_DESFAVORABLE + oidi.PUNTS_CALOR
        else:                    delta = oidi.PUNTS_DESFAVORABLE

        valor = max(0.0, min(100.0, valor + delta))
        files.append({
            "dia": dia,
            "hores_rang_optim": round(ratxa_max, 1),
            "min_calor_dia": int(min_calor),
            "index_gubler": round(valor, 1),
            "risc_gubler": oidi.nivell_risc(valor),
            "t_min": round(float(t[idx].min()), 1),
            "t_max": round(float(t[idx].max()), 1),
        })
    return pd.DataFrame(files)


def projectar_mildiu(prev: pd.DataFrame) -> pd.DataFrame:
    """
    Condicions de mildiu previstes: pluja acumulada en 48 h i episodis
    d'esporulació. No projecta el cicle (obert/tancat), que depèn de
    l'històric real; només diu si el temps serà favorable.
    """
    dur = mu.durades(prev["ts"])
    p = pd.to_numeric(prev["precipitacio_mm"], errors="coerce").fillna(0)

    pluja48 = pd.Series(p.values, index=prev["ts"]).rolling("48h", min_periods=1).sum()
    pluja48 = pd.Series(pluja48.values, index=prev.index)

    df = prev.copy()
    df["fulla_molla"] = (pd.to_numeric(df["humitat_pct"], errors="coerce") >= 90).astype(int)
    _, esporulat = mildiu.esporulacio_secundaria(df, dur)

    files = []
    for dia, g in prev.groupby(prev["ts"].dt.date):
        idx = g.index
        files.append({
            "dia": dia,
            "pluja_dia_mm": round(float(p[idx].sum()), 1),
            "pluja_48h_max": round(float(pluja48[idx].max()), 1),
            "episodis_esporulacio": int(esporulat[idx].sum()),
            "condicio_primaria_prev": int(float(pluja48[idx].max()) >= mildiu.PLUJA_EVENT_MM),
        })
    return pd.DataFrame(files)


def main():
    print("  Consultant la previsió d'Open-Meteo...")
    prev = baixar_previsio()
    if prev.empty:
        print("  [X] Sense dades de previsió")
        return

    index_inicial = 0.0
    if os.path.exists(CSV_HISTORIAL):
        h = pd.read_csv(CSV_HISTORIAL)
        if "index_gubler" in h.columns:
            v = pd.to_numeric(h["index_gubler"], errors="coerce").dropna()
            index_inicial = float(v.iloc[-1]) if len(v) else 0.0

    oid = projectar_oidi(prev, index_inicial)
    mil = projectar_mildiu(prev)
    df = oid.merge(mil, on="dia", how="outer").sort_values("dia")

    os.makedirs("data", exist_ok=True)
    df.to_csv(CSV_PREVISIO, index=False)

    print(f"  OK Previsió de {len(df)} dies -> {CSV_PREVISIO}")
    print(f"  Índex d'oïdi actual: {index_inicial:.0f}")
    for _, r in df.iterrows():
        print(f"      {r['dia']}  T {r['t_min']:.0f}-{r['t_max']:.0f}C  "
              f"ratxa {r['hores_rang_optim']:.1f}h  ->  índex {r['index_gubler']:.0f} "
              f"({r['risc_gubler']})  pluja {r['pluja_dia_mm']:.1f}mm")


if __name__ == "__main__":
    main()
