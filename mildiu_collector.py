"""
Model predictiu de mildiu - Estació Son Nadal (Felanitx, CAIB)
==============================================================
Plasmopara viticola - infecció primària (regla 3-10) + esporulació
secundària mecanística.

Els sensors es llegeixen de l'historial.csv generat pel son_nadal_collector.
Aquest script NO descarrega dades noves.

Estructura del cicle (i per què importa)
----------------------------------------
Les infeccions secundàries les causen esporangis produïts per lesions ja
establertes. Sense infecció primària no hi ha lesió, sense lesió no hi ha
esporangis i no pot haver-hi secundària. El model manté, doncs, una PORTA:
el risc secundari no s'avalua fins que s'ha registrat una primària i n'ha
passat el període d'incubació.

La porta també s'obre manualment via observacions.json, perquè els
esporangis poden arribar de vinyes veïnes: en aquest cas la parcel·la pot
tenir secundàries sense haver tingut primària pròpia.

Columnes afegides a mildiu_historial.csv:
  pluja_48h_mm           -> precipitació acumulada en 48 h (regla 3-10)
  pluja_10d_mm           -> acumulat de 10 dies (informatiu)
  t_mitjana_24h          -> temperatura mitjana de 24 h
  condicio_primaria      -> 1 si es compleix la regla 3-10
  cicle_obert            -> 1 si el cicle secundari està actiu
  graus_hora_esporulacio -> °C·h acumulats cap a l'esporulació (llindar 50)
  hores_fulla_molla      -> hores contínues amb fulla molla
  condicio_secundaria    -> 1 si s'ha completat un episodi d'esporulació
  graus_dia_inc          -> graus-dia acumulats des de la infecció (base 10 °C)
  dies_incubacio_est     -> dies estimats fins a l'aparició de símptomes
  risc_mildiu            -> inactiu / vigilancia / primari / secundari / alt
  reinici_mildiu         -> 1 si s'ha reiniciat el comptador
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os, json

import meteo_utils as mu

CSV_HISTORIAL = "data/historial.csv"
CSV_MILDIU    = "data/mildiu_historial.csv"
OBSERVACIONS  = "observacions.json"

# ── Infecció primària: regla dels tres deus (Baldacci 1947 / Goidanich) ──────
# La regla exigeix un EPISODI de pluja, no un acumulat dispers: 10 mm en 24-48 h.
# Amb finestra de 10 dies, una plugim d'1 mm/dia comptava igual que una tempesta
# de 10 mm, i epidemiològicament no s'assemblen gens.
PLUJA_EVENT_MM    = 10.0    # mm dins la finestra
FINESTRA_PLUJA    = "48h"
T_MIN_PRIMARIA    = 10.0    # °C de mitjana

# ── Esporulació secundària (model mecanístic tipus METOS) ────────────────────
# Els esporangiòfors només emergeixen de nit (la radiació atura la morfogènesi),
# amb aigua lliure i T > 12 °C. El procés es completa en acumular ~50 °C·h.
HR_ESPORULACIO    = 95.0    # % HR mínima (o fulla molla)
T_MIN_ESPORULACIO = 12.0    # °C
T_MAX_ESPORULACIO = 29.0    # °C, per sobre s'atura
GRAUS_HORA_ESPOR  = 50.0    # °C·h per completar l'esporulació
HORES_FOSCOR_MIN  = 4.0     # h mínimes de foscor

# ── Incubació ────────────────────────────────────────────────────────────────
T_BASE_INCUBACIO  = 10.0    # °C base per a graus-dia
GD_INCUBACIO      = 60.0    # graus-dia fins a símptomes


# ── Observacions de camp ─────────────────────────────────────────────────────
def carregar_observacions(malaltia: str = "mildiu"):
    """
    Dates en què s'ha observat la malaltia al camp.

    Serveixen per obrir la porta del cicle secundari quan l'inòcul ve de fora
    i el model no ha detectat cap primària pròpia.

    Les observacions amb incidència "cap" NO obren res: són controls negatius
    ("he mirat i no hi ha res"), útils per calibrar però no per declarar inòcul.
    """
    if not os.path.exists(OBSERVACIONS):
        return []
    try:
        with open(OBSERVACIONS, "r", encoding="utf-8") as f:
            obs = json.load(f).get("observacions", [])
    except Exception as e:
        print(f"  [!] No s'ha pogut llegir {OBSERVACIONS}: {e}")
        return []

    dates = []
    for o in obs:
        if o.get("malaltia") != malaltia:
            continue
        if str(o.get("incidencia", "")).lower() in ("cap", "", "none"):
            continue
        try:
            d = pd.to_datetime(o.get("data"))
        except (ValueError, TypeError):
            continue
        if pd.notna(d):
            dates.append(d.tz_localize(None) if d.tzinfo else d)
    return sorted(dates)


# ── Variables derivades ──────────────────────────────────────────────────────
def acumulat_mobil(df: pd.DataFrame, col: str, finestra: str, com: str = "sum") -> pd.Series:
    """Finestra mòbil sobre l'eix temporal real (no sobre nombre de registres)."""
    s = pd.Series(pd.to_numeric(df[col], errors="coerce").values, index=df["ts"])
    if com == "sum":
        res = s.fillna(0).rolling(finestra, min_periods=1).sum()
    else:
        res = s.rolling(finestra, min_periods=1).mean()
    return pd.Series(res.round(2).values, index=df.index)


def condicio_primaria(t_mitj: pd.Series, pluja_event: pd.Series) -> pd.Series:
    """
    Regla 3-10: brots > 10 cm, T mitjana > 10 °C i pluja >= 10 mm en 24-48 h.
    El requisit fenològic dels brots es gestiona des de la fenologia global.
    """
    return ((t_mitj >= T_MIN_PRIMARIA) & (pluja_event >= PLUJA_EVENT_MM)).astype(int)


def esporulacio_secundaria(df: pd.DataFrame, dur: pd.Series):
    """
    Episodis d'esporulació segons el model mecanístic.

    Acumula °C·h mentre es mantenen alhora foscor, aigua lliure i T entre 12 i
    29 °C. En arribar a 50 °C·h amb almenys 4 h de foscor, l'episodi es dona
    per completat (p. ex. 4 h a 13 °C, o 3 h a 17 °C). Si es trenca qualsevol
    condició —surt el sol, baixa la HR, cau la temperatura— l'episodi s'avorta.

    Retorna (graus_hora_acumulats, episodi_completat).
    """
    t     = pd.to_numeric(df["temperatura_c"], errors="coerce")
    hr    = pd.to_numeric(df["humitat_pct"],   errors="coerce")
    fulla = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce").fillna(0)
    nit   = mu.es_nit(df)

    humit = (hr >= HR_ESPORULACIO) | (fulla == 1)
    apte  = nit & humit & t.between(T_MIN_ESPORULACIO, T_MAX_ESPORULACIO)

    gh, fet    = np.zeros(len(df)), np.zeros(len(df), dtype=int)
    acc, hores = 0.0, 0.0

    for i in range(len(df)):
        h = dur.iloc[i]
        if bool(apte.iloc[i]) and pd.notna(h) and pd.notna(t.iloc[i]):
            acc   += float(t.iloc[i]) * float(h)
            hores += float(h)
            if acc >= GRAUS_HORA_ESPOR and hores >= HORES_FOSCOR_MIN:
                fet[i] = 1
                acc, hores = 0.0, 0.0   # episodi consumit
        else:
            acc, hores = 0.0, 0.0       # condicions trencades: s'avorta
        gh[i] = acc

    return pd.Series(gh.round(1), index=df.index), pd.Series(fet, index=df.index)


def calcular_graus_dia(df: pd.DataFrame, dur: pd.Series, infeccions: pd.Series):
    """
    Graus-dia (base 10 °C) des de l'última infecció, i dies fins a símptomes.
    Retorna (gd_acumulats, dies_estimats, reinicis, incubacio_completada).
    """
    t = pd.to_numeric(df["temperatura_c"], errors="coerce")

    gd_acc   = np.zeros(len(df))
    dies_inc = np.full(len(df), np.nan)
    reinici  = np.zeros(len(df), dtype=int)
    completa = np.zeros(len(df), dtype=int)

    acumulat, en_incubacio = 0.0, False

    for i in range(len(df)):
        t_val, h = t.iloc[i], dur.iloc[i]

        if infeccions.iloc[i] == 1 and not en_incubacio:
            acumulat, en_incubacio, reinici[i] = 0.0, True, 1

        if en_incubacio and pd.notna(t_val) and pd.notna(h):
            acumulat += max(0.0, (float(t_val) - T_BASE_INCUBACIO) * float(h) / 24.0)

        if en_incubacio:
            restants   = max(0.0, GD_INCUBACIO - acumulat)
            t_efectiva = max(0.1, (float(t_val) if pd.notna(t_val) else 20.0) - T_BASE_INCUBACIO)
            dies_inc[i] = round(restants / t_efectiva, 1)
            if acumulat >= GD_INCUBACIO:
                en_incubacio, completa[i], acumulat = False, 1, 0.0

        gd_acc[i] = round(acumulat, 1)

    return (pd.Series(gd_acc, index=df.index), pd.Series(dies_inc, index=df.index),
            pd.Series(reinici, index=df.index), pd.Series(completa, index=df.index))


def obrir_cicle(df: pd.DataFrame, incub_completa: pd.Series, observacions) -> pd.Series:
    """
    Porta del cicle secundari: 1 a partir del moment en què hi pot haver
    esporangis a la parcel·la. S'obre quan una primària completa la incubació,
    o quan s'ha observat la malaltia al camp. Un cop oberta no es tanca.
    """
    obert = np.zeros(len(df), dtype=int)
    primera_obs = min(observacions) if observacions else None
    actiu = False
    for i in range(len(df)):
        if incub_completa.iloc[i] == 1:
            actiu = True
        elif primera_obs is not None and df["ts"].iloc[i] >= primera_obs:
            actiu = True
        obert[i] = int(actiu)
    return pd.Series(obert, index=df.index)


def calcular_risc_mildiu(cond_prim, cond_sec, pluja_event, t_mitj) -> pd.Series:
    """
    alt        -> primària i secundària alhora
    secundari  -> esporulació completada amb el cicle obert
    primari    -> condicions d'infecció primària
    vigilancia -> pluja i temperatura s'acosten al llindar
    inactiu    -> cap condició
    """
    condicions = [
        (cond_prim == 1) & (cond_sec == 1),
        cond_sec == 1,
        cond_prim == 1,
        (pluja_event >= PLUJA_EVENT_MM / 2) & (t_mitj >= T_MIN_PRIMARIA),
    ]
    return pd.Series(
        np.select(condicions, ["alt", "secundari", "primari", "vigilancia"], default="inactiu"),
        index=cond_prim.index,
    )


# ── Pipeline principal ───────────────────────────────────────────────────────
def calcular_model_mildiu(df: pd.DataFrame) -> pd.DataFrame:
    df  = mu.ordenar_per_ts(df)
    dur = mu.durades(df["ts"])

    pluja_event = acumulat_mobil(df, "precipitacio_mm", FINESTRA_PLUJA)
    pluja_10d   = acumulat_mobil(df, "precipitacio_mm", "10D")
    t_mitj_24h  = acumulat_mobil(df, "temperatura_c", "24h", com="mean")
    t_mitj_10d  = acumulat_mobil(df, "temperatura_c", "10D", com="mean")

    cond_prim     = condicio_primaria(t_mitj_24h, pluja_event)
    gh, esporulat = esporulacio_secundaria(df, dur)

    fulla    = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce").fillna(0)
    hores_fm = mu.ratxes(fulla == 1, dur)

    observacions = carregar_observacions("mildiu")
    if observacions:
        print(f"  -> {len(observacions)} observació(ns) de camp; cicle obert des de "
              f"{min(observacions):%d/%m/%Y}")

    # Primera passada: la incubació de les primàries és qui obre la porta
    _, _, _, incub_completa = calcular_graus_dia(df, dur, cond_prim)
    cicle = obrir_cicle(df, incub_completa, observacions)

    # Les secundàries només compten amb el cicle obert
    cond_sec = (esporulat & (cicle == 1)).astype(int)

    # Segona passada: incubació de totes les infeccions reals
    infeccions = ((cond_prim == 1) | (cond_sec == 1)).astype(int)
    gd_acc, dies_inc, reinici, _ = calcular_graus_dia(df, dur, infeccions)

    df["pluja_48h_mm"]           = pluja_event
    df["pluja_10d_mm"]           = pluja_10d
    df["t_mitjana_24h"]          = t_mitj_24h
    df["t_mitjana_10d"]          = t_mitj_10d
    df["hores_fulla_molla"]      = hores_fm.round(1)
    df["graus_hora_esporulacio"] = gh
    df["condicio_primaria"]      = cond_prim
    df["condicio_secundaria"]    = cond_sec
    df["cicle_obert"]            = cicle
    df["graus_dia_inc"]          = gd_acc
    df["dies_incubacio_est"]     = dies_inc.round(1)
    df["reinici_mildiu"]         = reinici
    df["risc_mildiu"]            = calcular_risc_mildiu(
        cond_prim, cond_sec, pluja_event, t_mitj_24h)

    return df.drop(columns=["ts"])


def actualitzar_historial_mildiu(df: pd.DataFrame) -> pd.DataFrame:
    os.makedirs("data", exist_ok=True)
    df.to_csv(CSV_MILDIU, index=False)
    print(f"  -> {len(df)} registres guardats a {CSV_MILDIU}")
    return df


def resum_mildiu(df: pd.DataFrame):
    ult = df.tail(48)
    print(f"\n{'-'*50}")
    print("  Model mildiu (Plasmopara viticola)")
    print(f"  Risc actual        : {str(df['risc_mildiu'].iloc[-1]).upper()}")
    print(f"  Cicle secundari    : {'OBERT' if df['cicle_obert'].iloc[-1] else 'TANCAT (sense primaria)'}")
    print(f"  Pluja 48 h         : {df['pluja_48h_mm'].iloc[-1]:.1f} mm (llindar: {PLUJA_EVENT_MM} mm)")
    print(f"  T mitjana 24 h     : {df['t_mitjana_24h'].iloc[-1]:.1f} C (minim: {T_MIN_PRIMARIA} C)")
    print(f"  Fulla molla        : {df['hores_fulla_molla'].iloc[-1]:.1f} h")
    print(f"  Graus-hora esporul.: {df['graus_hora_esporulacio'].iloc[-1]:.1f} (llindar: {GRAUS_HORA_ESPOR})")
    dies_inc = df["dies_incubacio_est"].iloc[-1]
    if not pd.isna(dies_inc):
        print(f"  Dies fins simptomes: {dies_inc:.0f}")
    print(f"  Primaries (24 h)   : {int(ult['condicio_primaria'].sum())} intervals")
    print(f"  Secundaries (24 h) : {int(ult['condicio_secundaria'].sum())} intervals")
    print(f"{'-'*50}\n")


def main():
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Model mildiu Son Nadal iniciat")
    print("-" * 50)

    if not os.path.exists(CSV_HISTORIAL):
        print("[WARNING] No s'ha trobat historial.csv — executa primer son_nadal_collector.py")
        raise SystemExit(1)

    df = pd.read_csv(CSV_HISTORIAL)
    print(f"  -> {len(df)} registres carregats de {CSV_HISTORIAL}")

    df = calcular_model_mildiu(df)
    actualitzar_historial_mildiu(df)
    resum_mildiu(df)


if __name__ == "__main__":
    main()
