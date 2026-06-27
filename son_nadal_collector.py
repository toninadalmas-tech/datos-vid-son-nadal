"""
Col·lector diari - Estació Son Nadal (Felanitx, CAIB)
======================================================
Descarrega les últimes 24h de temperatura, humitat i pluja
des dels endpoints CSV oficials de la web, calcula el risc
d'oïdi i afegeix les dades a data/historial.csv.

Execució:
  python son_nadal_collector.py
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import os, io
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Endpoints CSV confirmats ──────────────────────────────────────────────────
URLS = {
    "temperatura_c":   "https://www.estacionsclimatiquesiibb.cat/weatherstationlast24chart/117202/temperature/exportcsv",
    "humitat_pct":     "https://www.estacionsclimatiquesiibb.cat/weatherstationlast24chart/117202/humidity/exportcsv",
    "precipitacio_mm": "https://www.estacionsclimatiquesiibb.cat/weatherstationlast24chart/117202/rain/exportcsv",
}

CSV_HISTORIAL = "data/historial.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ca-ES,ca;q=0.9,es;q=0.8",
    "Referer": "https://www.estacionsclimatiquesiibb.cat/weatherstationdataview/117202",
}


# ── Descàrrega ────────────────────────────────────────────────────────────────
def descarregar_sensor(sessio: requests.Session, nom: str, url: str) -> pd.DataFrame | None:
    """Descarrega el CSV d'un sensor i retorna un DataFrame amb [timestamp, valor]."""
    try:
        r = sessio.get(url, headers=HEADERS, timeout=20, verify=False)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✗ {nom}: error de connexió — {e}")
        return None

    text = r.text.strip()
    if not text:
        print(f"  ✗ {nom}: resposta buida")
        return None

    # Detecta separador (punt i coma o coma)
    sep = ";" if text.count(";") > text.count(",") else ","

    try:
        df = pd.read_csv(io.StringIO(text), sep=sep)
    except Exception as e:
        print(f"  ✗ {nom}: no s'ha pogut llegir el CSV — {e}")
        print(f"     Primers 200 caràcters: {text[:200]}")
        return None

    print(f"  ✓ {nom}: {len(df)} files | columnes: {list(df.columns)}")
    print(f"     Primeres 2 files:\n{df.head(2).to_string()}")

    # Estructura real del CSV de la CAIB:
    # Codi | Nom | Data i Hora | Valor
    # La columna de valor és sempre l'última (índex -1),
    # la de temps és la tercera (índex 2)
    if df.shape[1] < 4:
        print(f"  ✗ {nom}: s'esperaven ≥4 columnes, hi ha {df.shape[1]}")
        return None

    col_temps = df.columns[2]
    col_valor = df.columns[-1]  # sempre l'última, independentment del nom

    print(f"     Usant: temps='{col_temps}' | valor='{col_valor}'")

    serie_valor = df[col_valor].astype(str).str.strip().str.replace(",", ".", regex=False)
    print(f"     Primers valors raw: {serie_valor.head(3).tolist()}")

    df_net = pd.DataFrame({
        "timestamp": df[col_temps].astype(str).str.strip(),
        nom:         pd.to_numeric(serie_valor, errors="coerce"),
    })
    nans = df_net[nom].isna().sum()
    if nans > 0:
        print(f"     ⚠ {nans} valors no numèrics ignorats")
    return df_net.dropna(subset=["timestamp"])


def obtenir_dades(sessio: requests.Session) -> pd.DataFrame | None:
    """
    Descarrega els tres sensors i els combina correctament:
    1. Cada sensor es normalitza a intervals de 30 min (arrodonint el timestamp)
    2. Es combinen per merge sobre el timestamp arrodonit
    Això garanteix que T, HR i pluja sempre queden a la mateixa fila.
    """
    dfs_nets = {}
    for nom, url in URLS.items():
        df = descarregar_sensor(sessio, nom, url)
        if df is None:
            continue

        # Converteix timestamp a datetime
        df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["ts", nom])

        # Arrodoneix cada mesura al interval de 30 min més proper
        # ex: 13:08 → 13:00, 13:18 → 13:30, 13:33 → 13:30
        df["ts30"] = df["ts"].dt.round("30min")

        # Agrupa per interval: mitjana per T i HR, suma per pluja
        es_pluja = any(k in nom for k in ["precipitacio", "pluja", "rain"])
        if es_pluja:
            df_agr = df.groupby("ts30")[nom].sum()
        else:
            df_agr = df.groupby("ts30")[nom].mean()

        df_agr = df_agr.reset_index()
        df_agr["timestamp"] = df_agr["ts30"].dt.strftime("%d/%m/%Y %H:%M")
        df_agr = df_agr.drop(columns=["ts30"])

        dfs_nets[nom] = df_agr
        print(f"  → {nom}: {len(df_agr)} intervals de 30 min")

    if not dfs_nets:
        return None

    # Merge de tots els sensors per timestamp
    df_final = None
    for df_s in dfs_nets.values():
        if df_final is None:
            df_final = df_s
        else:
            df_final = pd.merge(df_final, df_s, on="timestamp", how="inner")

    df_final = df_final.sort_values("timestamp").reset_index(drop=True)
    print(f"  → Total combinat (inner join): {len(df_final)} registres")
    return df_final


# ── Risc oïdi (model Kast & Bleyer simplificat) ───────────────────────────────
def afegir_risc_oidio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Temperatura favorable: 15–35°C (òptim 20–27°C)
    HR mínima: 40% | risc alt: ≥70%
    """
    if "temperatura_c" not in df.columns or "humitat_pct" not in df.columns:
        df["hora_favorable_oidio"] = None
        df["risc_infeccio"] = "sense dades"
        return df

    t  = pd.to_numeric(df["temperatura_c"], errors="coerce")
    hr = pd.to_numeric(df["humitat_pct"],   errors="coerce")

    condicions = [
        t.between(20, 27) & (hr >= 70),
        t.between(15, 35) & (hr >= 50),
        t.between(15, 35) & (hr >= 40),
    ]
    df["risc_infeccio"]        = np.select(condicions, ["alt", "moderat", "baix"], default="no favorable")
    df["hora_favorable_oidio"] = (t.between(15, 35) & (hr >= 40)).astype(int)
    return df


# ── Historial ─────────────────────────────────────────────────────────────────
def actualitzar_historial(df_nou: pd.DataFrame) -> pd.DataFrame:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CSV_HISTORIAL):
        df_old = pd.read_csv(CSV_HISTORIAL)
        df_tot = pd.concat([df_old, df_nou], ignore_index=True)
        df_tot = df_tot.drop_duplicates(subset=["timestamp"], keep="last")
    else:
        df_tot = df_nou
    df_tot = df_tot.sort_values("timestamp").reset_index(drop=True)
    df_tot.to_csv(CSV_HISTORIAL, index=False)
    print(f"\n  → {len(df_nou)} registres nous | {len(df_tot)} totals → {CSV_HISTORIAL}")
    return df_tot


# ── Resum ─────────────────────────────────────────────────────────────────────
def resum(df: pd.DataFrame):
    print(f"\n{'─'*50}")
    print(f"  Últimes 24h  ({len(df)} registres)")
    for col, nom, unit in [
        ("temperatura_c",   "Temperatura", "°C"),
        ("humitat_pct",     "Humitat",     "%"),
        ("precipitacio_mm", "Pluja",       "mm"),
    ]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s):
                print(f"  {nom:<12}: min={s.min():.1f}{unit}  max={s.max():.1f}{unit}  mitj={s.mean():.1f}{unit}")
    if "risc_infeccio" in df.columns:
        h = (df["risc_infeccio"] != "no favorable").sum()
        print(f"\n  Hores favorables oïdi: {h}/{len(df)}")
        print(df["risc_infeccio"].value_counts().to_string())
    print(f"{'─'*50}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Col·lector Son Nadal iniciat")
    print("─" * 50)

    s = requests.Session()

    print("→ Descarregant sensors...")
    df = obtenir_dades(s)

    if df is None or df.empty:
        print("\n⚠ No s'han pogut obtenir dades de cap sensor.")
        raise SystemExit(1)

    df = afegir_risc_oidio(df)
    actualitzar_historial(df)
    resum(df)


if __name__ == "__main__":
    main()
