"""
Col·lector diari - Estació Son Nadal (Felanitx, CAIB)
======================================================
S'executa cada matí via GitHub Actions.
Descarrega el CSV de les últimes 24h de la web i l'afegeix a l'historial.

Estratègia (per ordre de preferència):
  1. Endpoint CSV directe (el que usa el botó de la web)
  2. Endpoint JSON
  3. Scraping HTML + dades Chart.js embegudes
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os, io, re
import numpy as np

# ── Configuració ─────────────────────────────────────────────────────────────
ESTACIO_ID    = "117202"
BASE_URL      = "https://www.estacionsclimatiquesiibb.cat"
CSV_HISTORIAL = "data/historial.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ca-ES,ca;q=0.9,es;q=0.8",
    "Referer": f"{BASE_URL}/weatherstationdataview/{ESTACIO_ID}",
}

# Endpoints candidats per al CSV directe (el botó de la web fa una d'aquestes)
ENDPOINTS_CSV = [
    f"{BASE_URL}/weatherstationlast24hourscsv/{ESTACIO_ID}",
    f"{BASE_URL}/weatherstationlast24hourscsv/export/{ESTACIO_ID}",
    f"{BASE_URL}/export/csv/{ESTACIO_ID}/last24",
    f"{BASE_URL}/api/weatherstation/{ESTACIO_ID}/last24hours/csv",
]

# Sensors de la web (T, HR, Pluja) - IDs del desplegable
SENSORS = {
    "temperatura": {"sensor_id": 1, "columna": "temperatura_c"},
    "humitat":     {"sensor_id": 2, "columna": "humitat_pct"},
    "pluja":       {"sensor_id": 3, "columna": "precipitacio_mm"},
}


# ─────────────────────────────────────────────────────────────────────────────
def prova_csv_directe(s: requests.Session) -> pd.DataFrame | None:
    for url in ENDPOINTS_CSV:
        try:
            r = s.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.text) > 100 and (";" in r.text[:300] or "," in r.text[:300]):
                sep = ";" if r.text.count(";") > r.text.count(",") else ","
                df = pd.read_csv(io.StringIO(r.text), sep=sep)
                if not df.empty:
                    print(f"  ✓ CSV directe: {url}")
                    return df
        except Exception:
            pass
    return None


def scraping_sensor(s: requests.Session, nom: str, info: dict) -> pd.DataFrame | None:
    """Descarrega les dades d'un sensor via el formulari de gràfica 24h."""
    URL_FORM = f"{BASE_URL}/weatherstationlast24hoursgraph"

    for metode, kwargs in [
        ("POST", {"data": {"weatherstation_id": ESTACIO_ID, "sensor_id": info["sensor_id"]}}),
        ("GET",  {"params": {"weatherstation_id": ESTACIO_ID, "sensor_id": info["sensor_id"]}}),
        ("GET",  {}),  # URL directa
    ]:
        url = URL_FORM if metode == "POST" or "params" in kwargs else f"{URL_FORM}/{ESTACIO_ID}/{info['sensor_id']}"
        try:
            r = s.request(metode, url, headers=HEADERS, timeout=20, **kwargs)
            if r.status_code != 200:
                continue
            html = r.text

            # Intenta extreure dades de Chart.js (labels + data)
            lbls = re.findall(r'labels\s*[=:]\s*\[([^\]]+)\]', html)
            vals = re.findall(r'["\']data["\']\s*:\s*\[([^\]]+)\]', html)
            if lbls and vals:
                hores  = [h.strip().strip('"\'') for h in lbls[0].split(",")]
                valors = [float(v.strip()) for v in vals[0].split(",") if v.strip()]
                if len(hores) == len(valors) and len(hores) > 0:
                    ts = _hores_a_timestamps(hores)
                    df = pd.DataFrame({"timestamp": ts, info["columna"]: valors})
                    print(f"  ✓ {nom} via Chart.js ({len(df)} punts, {metode})")
                    return df

            # Alternativa: taula HTML
            soup = BeautifulSoup(html, "html.parser")
            taula = soup.find("table")
            if taula:
                files = []
                for tr in taula.find_all("tr")[1:]:
                    cel = tr.find_all("td")
                    if len(cel) >= 2:
                        try:
                            files.append({
                                "timestamp": cel[0].get_text(strip=True),
                                info["columna"]: float(cel[1].get_text(strip=True).replace(",", "."))
                            })
                        except Exception:
                            pass
                if files:
                    print(f"  ✓ {nom} via taula HTML ({len(files)} punts, {metode})")
                    return pd.DataFrame(files)

        except Exception as e:
            print(f"    ! {nom} {metode}: {e}")

    return None


def _hores_a_timestamps(hores: list) -> list:
    """Converteix ['11:33','12:33',...,'01:33',...] a timestamps complets."""
    avui = datetime.now()
    ahir = avui - timedelta(days=1)
    ts, dia_canviat = [], False
    for h in hores:
        try:
            hora_int = int(h.split(":")[0])
            if hora_int < 6 and not dia_canviat:
                dia_canviat = True
            data = avui if dia_canviat else ahir
            ts.append(f"{data.strftime('%Y-%m-%d')} {h}:00")
        except Exception:
            ts.append(h)
    return ts


def obtenir_dades(s: requests.Session) -> pd.DataFrame | None:
    # 1. CSV directe
    df = prova_csv_directe(s)
    if df is not None:
        return df

    # 2. Scraping per sensor i combinació
    print("→ Scraping per sensor...")
    dfs = {}
    for nom, info in SENSORS.items():
        df_s = scraping_sensor(s, nom, info)
        if df_s is not None:
            dfs[nom] = df_s

    if not dfs:
        return None

    # Combina per timestamp
    df_final = None
    for df_s in dfs.values():
        df_final = df_s if df_final is None else pd.merge(df_final, df_s, on="timestamp", how="outer")

    return df_final.sort_values("timestamp").reset_index(drop=True) if df_final is not None else None


def afegir_risc_oidio(df: pd.DataFrame) -> pd.DataFrame:
    """Model Kast & Bleyer simplificat: T i HR → risc d'infecció oïdi."""
    if "temperatura_c" not in df.columns or "humitat_pct" not in df.columns:
        df["hora_favorable_oidio"] = None
        df["risc_infeccio"] = "sense dades suficients"
        return df

    t  = pd.to_numeric(df["temperatura_c"],  errors="coerce")
    hr = pd.to_numeric(df["humitat_pct"],     errors="coerce")

    condicions = [
        t.between(20, 27) & (hr >= 70),
        t.between(15, 35) & (hr >= 50),
        t.between(15, 35) & (hr >= 40),
    ]
    df["risc_infeccio"]       = np.select(condicions, ["alt", "moderat", "baix"], default="no favorable")
    df["hora_favorable_oidio"] = (t.between(15, 35) & (hr >= 40)).astype(int)
    return df


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
    print(f"\n  → Historial: {len(df_tot)} registres totals guardats a {CSV_HISTORIAL}")
    return df_tot


def resum(df: pd.DataFrame):
    avui = datetime.now().strftime("%Y-%m-%d")
    d = df[df["timestamp"].str.startswith(avui)] if "timestamp" in df.columns else df
    print(f"\n{'─'*48}\n  Resum {avui}  ({len(d)} registres)")
    for col, nom in [("temperatura_c", "Temperatura"), ("humitat_pct", "Humitat"), ("precipitacio_mm", "Pluja")]:
        if col in d.columns:
            s = pd.to_numeric(d[col], errors="coerce").dropna()
            if len(s):
                print(f"  {nom:<12}: min={s.min():.1f}  max={s.max():.1f}  mitj={s.mean():.1f}")
    if "risc_infeccio" in d.columns:
        h = (d["risc_infeccio"] != "no favorable").sum()
        print(f"  Hores favorables oïdi: {h}/{len(d)}")
        print(d["risc_infeccio"].value_counts().to_string())
    print(f"{'─'*48}\n")


def main():
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Col·lector Son Nadal iniciat")
    s = requests.Session()
    # Visita prèvia per obtenir cookies
    try:
        s.get(f"{BASE_URL}/weatherstationdataview/{ESTACIO_ID}", headers=HEADERS, timeout=15)
    except Exception:
        pass

    print("→ Intentant obtenir dades...")
    df = obtenir_dades(s)

    if df is None or df.empty:
        print("\n⚠ No s'han pogut obtenir dades.")
        print("  ACCIÓ NECESSÀRIA: Obre el navegador, ves a la pàgina de l'estació,")
        print("  prem F12 → Network, clica el botó CSV i copia la URL de la petició.")
        print(f"  URL estació: {BASE_URL}/weatherstationdataview/{ESTACIO_ID}")
        raise SystemExit(1)

    print(f"  {len(df)} registres obtinguts")
    df = afegir_risc_oidio(df)
    actualitzar_historial(df)
    resum(df)


if __name__ == "__main__":
    main()
