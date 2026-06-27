"""
Model predictiu de mildiu - Estació Son Nadal (Felanitx, CAIB)
==============================================================
Plasmopara viticola - Model EPI + regla dels 3x10

Els sensors es llegeixen del mateix historial.csv generat pel
son_nadal_collector.py. Aquest script NO descarrega dades noves,
simplement llegeix l'historial i calcula el risc de mildiu.

Models implementats:
  1. Infecció primària  → regla dels 3x10 (Goidanich)
  2. Infecció secundària → T + HR + hores humides (model EPI simplificat)
  3. Període d'incubació → graus-dia acumulats des de la infecció

Columnes afegides a mildiu_historial.csv:
  pluja_10d_mm       → precipitació acumulada últims 10 dies
  t_mitjana_10d      → temperatura mitjana últims 10 dies
  condicio_primaria  → 1 si es compleix la regla 3x10
  hores_hr95         → hores consecutives amb HR >= 95%
  condicio_secundaria→ 1 si T 18-30°C i hores_hr95 >= 4
  graus_dia_inc      → graus-dia acumulats des de l'última infecció (base 10°C)
  dies_incubacio_est → dies estimats fins a l'aparició de símptomes
  risc_mildiu        → inactiu / vigilancia / primari / secundari / alt
  reinici_mildiu     → 1 si s'ha reiniciat el comptador
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

CSV_HISTORIAL       = "data/historial.csv"
CSV_MILDIU          = "data/mildiu_historial.csv"

# ── Paràmetres del model ──────────────────────────────────────────────────────
T_MIN_INFECCIO      = 10.0   # °C mínim per a infecció primària
PLUJA_10D_MIN       = 10.0   # mm acumulats en 10 dies (regla 3x10)
T_OPT_MIN           = 18.0   # °C rang òptim infecció secundària
T_OPT_MAX           = 30.0   # °C rang òptim infecció secundària
HR_MIN_SEC          = 95.0   # % HR mínim per a infecció secundària
HORES_HR_MIN        = 4      # hores consecutives HR >= 95% (intervals 30min → 8)
T_BASE_INCUBACIO    = 10.0   # °C base per a càlcul de graus-dia
GD_INCUBACIO        = 60.0   # graus-dia fins a aparició de símptomes


# ── Càlcul de variables meteorològiques derivades ────────────────────────────
def calcular_pluja_10d(df: pd.DataFrame) -> pd.Series:
    """Precipitació acumulada en finestra mòbil de 10 dies (480 intervals de 30min)."""
    p = pd.to_numeric(df["precipitacio_mm"], errors="coerce").fillna(0)
    return p.rolling(window=480, min_periods=1).sum().round(2)


def calcular_t_mitjana_10d(df: pd.DataFrame) -> pd.Series:
    """Temperatura mitjana en finestra mòbil de 10 dies."""
    t = pd.to_numeric(df["temperatura_c"], errors="coerce")
    return t.rolling(window=480, min_periods=1).mean().round(2)


def calcular_hores_hr95(df: pd.DataFrame) -> pd.Series:
    """
    Intervals consecutius de 30 min amb HR >= 95%.
    Reinicia a 0 quan HR baixa del llindar.
    """
    hr = pd.to_numeric(df["humitat_pct"], errors="coerce")
    alta_hr = (hr >= HR_MIN_SEC).astype(int)

    comptador = np.zeros(len(df))
    cnt = 0
    for i in range(len(df)):
        if alta_hr.iloc[i] == 1:
            cnt += 1
        else:
            cnt = 0
        comptador[i] = cnt

    # Converteix intervals de 30min a hores
    return pd.Series(comptador * 0.5, index=df.index).round(1)


# ── Model d'infecció primària (regla 3x10 de Goidanich) ──────────────────────
def condicio_primaria(t_mitj: pd.Series, pluja_10d: pd.Series) -> pd.Series:
    """
    Condició d'infecció primària:
      - T mitjana 10d >= 10°C
      - Pluja acumulada 10d >= 10mm
    (el tercer factor, brots >= 10cm, es gestiona via fenologia.json)
    """
    return ((t_mitj >= T_MIN_INFECCIO) & (pluja_10d >= PLUJA_10D_MIN)).astype(int)


# ── Model d'infecció secundària (EPI simplificat) ────────────────────────────
def condicio_secundaria(t: pd.Series, hores_hr: pd.Series) -> pd.Series:
    """
    Condició d'infecció secundària (conidis):
      - T entre 18-30°C (òptim 22°C)
      - >= 4 hores consecutives amb HR >= 95%
    """
    return (t.between(T_OPT_MIN, T_OPT_MAX) & (hores_hr >= HORES_HR_MIN)).astype(int)


# ── Graus-dia i període d'incubació ──────────────────────────────────────────
def calcular_graus_dia(df: pd.DataFrame,
                       cond_prim: pd.Series,
                       cond_sec: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Acumula graus-dia (base 10°C) des de l'última infecció detectada.
    Retorna:
      - gd_acc:     graus-dia acumulats
      - dies_inc:   dies estimats fins a símptomes
      - reinici:    1 si s'ha reiniciat el comptador
    """
    t = pd.to_numeric(df["temperatura_c"], errors="coerce")

    gd_acc   = np.zeros(len(df))
    dies_inc = np.full(len(df), np.nan)
    reinici  = np.zeros(len(df), dtype=int)

    acumulat     = 0.0
    en_incubacio = False

    for i in range(len(df)):
        t_val = t.iloc[i]

        # Detecta nova infecció → inicia o reinicia l'acumulació
        if cond_prim.iloc[i] == 1 or cond_sec.iloc[i] == 1:
            if not en_incubacio:
                acumulat     = 0.0
                en_incubacio = True
                reinici[i]   = 1

        # Acumula graus-dia si estem en període d'incubació
        if en_incubacio and not pd.isna(t_val):
            gd = max(0.0, (t_val - T_BASE_INCUBACIO) * 0.5)  # interval 30min
            acumulat += gd

        # Estima dies fins a símptomes
        if en_incubacio and acumulat > 0:
            gd_restants = max(0, GD_INCUBACIO - acumulat)
            t_actual    = t_val if not pd.isna(t_val) else 20.0
            t_efectiva  = max(0.1, t_actual - T_BASE_INCUBACIO)
            dies_inc[i] = round(gd_restants / (t_efectiva * 2), 1)  # *2 per 48 intervals/dia

            # Fi del període d'incubació
            if acumulat >= GD_INCUBACIO:
                en_incubacio = False
                acumulat     = 0.0

        gd_acc[i] = round(acumulat, 1)

    return (pd.Series(gd_acc, index=df.index),
            pd.Series(dies_inc, index=df.index),
            pd.Series(reinici, index=df.index))


# ── Nivell de risc final ──────────────────────────────────────────────────────
def calcular_risc_mildiu(cond_prim: pd.Series,
                          cond_sec: pd.Series,
                          pluja_10d: pd.Series,
                          t_mitj: pd.Series) -> pd.Series:
    """
    Nivells de risc:
      alt        → infecció primària I secundària simultànies
      secundari  → condicions d'infecció secundària actives
      primari    → condicions d'infecció primària actives
      vigilancia → pluja 5-10mm o T propera al llindar
      inactiu    → cap condició
    """
    condicions = [
        (cond_prim == 1) & (cond_sec == 1),
        cond_sec == 1,
        cond_prim == 1,
        (pluja_10d >= 5) | (t_mitj >= 8),
    ]
    return pd.Series(
        np.select(condicions,
                  ["alt", "secundari", "primari", "vigilancia"],
                  default="inactiu"),
        index=cond_prim.index
    )


# ── Pipeline principal ────────────────────────────────────────────────────────
def calcular_model_mildiu(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica tot el model de mildiu sobre l'historial complet."""
    df = df.copy()
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = df.sort_values("ts").reset_index(drop=True)

    t    = pd.to_numeric(df["temperatura_c"], errors="coerce")

    pluja_10d  = calcular_pluja_10d(df)
    t_mitj_10d = calcular_t_mitjana_10d(df)
    hores_hr   = calcular_hores_hr95(df)
    cond_prim  = condicio_primaria(t_mitj_10d, pluja_10d)
    cond_sec   = condicio_secundaria(t, hores_hr)
    gd_acc, dies_inc, reinici = calcular_graus_dia(df, cond_prim, cond_sec)

    df["pluja_10d_mm"]        = pluja_10d
    df["t_mitjana_10d"]       = t_mitj_10d
    df["hores_hr95"]          = hores_hr
    df["condicio_primaria"]   = cond_prim
    df["condicio_secundaria"] = cond_sec
    df["graus_dia_inc"]       = gd_acc
    df["dies_incubacio_est"]  = dies_inc.round(1)
    df["reinici_mildiu"]      = reinici
    df["risc_mildiu"]         = calcular_risc_mildiu(cond_prim, cond_sec, pluja_10d, t_mitj_10d)

    df = df.drop(columns=["ts"])
    return df


# ── Historial mildiu ──────────────────────────────────────────────────────────
def actualitzar_historial_mildiu(df: pd.DataFrame) -> pd.DataFrame:
    """Guarda l'historial de mildiu (recalculat complet cada vegada)."""
    os.makedirs("data", exist_ok=True)
    df.to_csv(CSV_MILDIU, index=False)
    print(f"  → {len(df)} registres guardats a {CSV_MILDIU}")
    return df


# ── Resum ─────────────────────────────────────────────────────────────────────
def resum_mildiu(df: pd.DataFrame):
    ult = df.tail(48)  # últimes 24h
    risc_actual   = df["risc_mildiu"].iloc[-1]
    pluja_10d     = df["pluja_10d_mm"].iloc[-1]
    t_mitj        = df["t_mitjana_10d"].iloc[-1]
    dies_inc      = df["dies_incubacio_est"].iloc[-1]
    hores_hr      = df["hores_hr95"].iloc[-1]

    risc_colors = {
        "inactiu":   "──",
        "vigilancia":"⚡",
        "primari":   "⚠",
        "secundari": "⚠⚠",
        "alt":       "🔴",
    }

    print(f"\n{'─'*50}")
    print(f"  Model mildiu (Plasmopara viticola)")
    print(f"  Risc actual       : {risc_colors.get(risc_actual,'')} {risc_actual.upper()}")
    print(f"  Pluja 10 dies     : {pluja_10d:.1f} mm (mínim: {PLUJA_10D_MIN} mm)")
    print(f"  T mitjana 10 dies : {t_mitj:.1f}°C (mínim: {T_MIN_INFECCIO}°C)")
    print(f"  Hores HR≥95%      : {hores_hr:.1f}h (mínim: {HORES_HR_MIN}h)")
    if not pd.isna(dies_inc):
        print(f"  Dies fins símptomes: {dies_inc:.0f} dies (estimat)")
    inf_prim = int(ult["condicio_primaria"].sum())
    inf_sec  = int(ult["condicio_secundaria"].sum())
    print(f"  Infeccions primàries (24h): {inf_prim} intervals")
    print(f"  Infeccions secundàries (24h): {inf_sec} intervals")
    print(f"{'─'*50}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Model mildiu Son Nadal iniciat")
    print("─" * 50)

    if not os.path.exists(CSV_HISTORIAL):
        print("⚠ No s'ha trobat historial.csv — executa primer son_nadal_collector.py")
        raise SystemExit(1)

    df = pd.read_csv(CSV_HISTORIAL)
    print(f"  → {len(df)} registres carregats de {CSV_HISTORIAL}")

    df = calcular_model_mildiu(df)
    actualitzar_historial_mildiu(df)
    resum_mildiu(df)


if __name__ == "__main__":
    main()
