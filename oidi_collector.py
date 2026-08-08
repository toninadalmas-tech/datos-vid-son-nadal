"""
Model d'oïdi (Erysiphe necator) – Índex de risc de Gubler-Thomas
================================================================
Implementa l'índex de UC Davis (Gubler & Thomas, anys 90), escala 0-100,
dirigit exclusivament per temperatura: el fong és xeròfit i, un cop
iniciada l'epidèmia conidial, la humitat relativa no hi intervé.

S'hi afegeixen dues extensions documentades:
  - correcció per radiació UV (Austin & Wilcox, 2012)
  - reinici per tractament vigent (veure calcular_fi_proteccio)

Columnes que escriu a historial.csv:
  hores_rang_optim -> hores contínues dins la finestra 21.1-29.4 °C
  min_calor_dia    -> minuts del dia per sobre de 35 °C
  index_gubler     -> índex de risc 0-100 (risc climàtic = risc de FULLA)
  risc_gubler      -> baix / moderat / alt
  reinici_ui       -> 1 si el registre cau dins un període de protecció
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os, json

import meteo_utils as mu

CSV_HISTORIAL = "data/historial.csv"

# ── Paràmetres del model Gubler-Thomas ───────────────────────────────────────
T_OPT_MIN            = 21.1   # °C (70 °F) límit inferior de la finestra òptima
T_OPT_MAX            = 29.4   # °C (85 °F) límit superior
T_CALOR              = 35.0   # °C (95 °F) xoc tèrmic
HORES_CONTINUES_MIN  = 6.0    # h dins la finestra per sumar punts
MINUTS_CALOR_LIMIT   = 15     # min a >= 35 °C per restar punts
DIES_ARRENCADA       = 3      # dies favorables seguits per declarar l'epidèmia
PUNTS_ARRENCADA      = 60     # índex en què arrenca (3 x 20)
PUNTS_FAVORABLE      = 20
PUNTS_DESFAVORABLE   = -10
PUNTS_CALOR          = -10

# Llindars oficials del model
LLINDAR_MODERAT      = 30
LLINDAR_ALT          = 60


def nivell_risc(index: float) -> str:
    """Categoria de risc segons els llindars de UC Davis (0-30 / 40-60 / >60)."""
    if pd.isna(index):     return "baix"
    if index <= LLINDAR_MODERAT: return "baix"
    if index <= LLINDAR_ALT:     return "moderat"
    return "alt"

# ── Degradació de la protecció ────────────────────────────────────────────────
# Aquests paràmetres han de coincidir amb getProtectionInfo() de
# docs/assets/app.js: si es canvien aquí, s'han de canviar allà.
DIES_PROTECCIO_DEFECTE  = 10     # dies si el tractament no porta dies_proteccio
PLUJA_RENTAT_MM         = 12.0   # mm acumulats que renten el producte
T_CALOR_LIMIT           = 35.0   # °C a partir dels quals el dia degrada la protecció
DIES_PENALITZACIO_CALOR = 2      # dies que resta cada jornada de calor

def carregar_tractaments():
    try:
        with open("tractaments.json", "r", encoding="utf-8") as f:
            return json.load(f).get("tractaments", [])
    except Exception:
        return []


def calcular_fi_proteccio(inici, dies_base, ecologic, ts, pluja, temps):
    """
    Data de fi de protecció d'un tractament, amb la degradació pel clima.

    Rèplica de getProtectionInfo() a docs/assets/app.js perquè el model i el
    dashboard diguin el mateix. Només es degraden els productes ecològics:
      - Rentat: pluja acumulada >= 12 mm des del tractament -> s'acaba allà
      - Calor:  cada dia amb T màx >= 35 °C resta 2 dies de protecció
    Els convencionals mantenen els dies nominals del producte.

    Retorna (fi, degradat, motiu).
    """
    fi = inici + pd.Timedelta(days=dies_base)
    if not ecologic:
        return fi, False, ""

    # Només cal recórrer la finestra de protecció nominal: la degradació
    # només pot escurçar-la, mai allargar-la.
    finestra = (ts >= inici) & (ts <= fi)
    ts_f    = ts[finestra].reset_index(drop=True)
    pluja_f = pluja[finestra].reset_index(drop=True).fillna(0.0)
    temps_f = temps[finestra].reset_index(drop=True)

    dies_valids = dies_base
    pluja_acc   = 0.0
    dia_actual  = None
    t_max_dia   = float("-inf")
    degradat    = False
    motiu       = ""

    for i in range(len(ts_f)):
        moment = ts_f.iloc[i]
        if moment > fi:
            break

        # Regla A — rentat per pluja acumulada
        pluja_acc += float(pluja_f.iloc[i])
        if pluja_acc >= PLUJA_RENTAT_MM:
            return moment, True, f"Pluja >{PLUJA_RENTAT_MM:.0f}mm"

        # Regla B — cada dia tancat amb T màx alta escurça la protecció
        t = temps_f.iloc[i]
        dia = moment.date()
        if dia != dia_actual:
            if dia_actual is not None and t_max_dia >= T_CALOR_LIMIT:
                dies_valids -= DIES_PENALITZACIO_CALOR
                degradat = True
                motiu    = f"Calor >{T_CALOR_LIMIT:.0f}ºC"
                fi = inici + pd.Timedelta(days=dies_valids)
                if moment > fi:
                    return moment, True, motiu
            dia_actual = dia
            t_max_dia  = float("-inf") if pd.isna(t) else float(t)
        elif pd.notna(t) and float(t) > t_max_dia:
            t_max_dia = float(t)

    return fi, degradat, motiu


def obtenir_periodes_proteccio(tractaments, malaltia, df):
    """
    Retorna els períodes (inici, fi) de protecció per a una malaltia.

    Els dies de protecció surten del propi tractament (dies_proteccio, que el
    dashboard desa segons el producte) i no d'un valor fix, i es degraden pel
    clima igual que a la gràfica.

    La data ve del formulari del dashboard com a datetime-local
    ("2026-07-01T18:28"), per això es fa servir pd.to_datetime i no
    strptime amb un format fix.
    """
    ts    = df["ts"]
    pluja = pd.to_numeric(df["precipitacio_mm"], errors="coerce")
    temps = pd.to_numeric(df["temperatura_c"],   errors="coerce")

    periodes = []
    for t in tractaments:
        if malaltia not in t.get("malalties", []):
            continue
        try:
            data_inici = pd.to_datetime(t.get("data"))
        except (ValueError, TypeError) as e:
            print(f"  [!] Tractament amb data invàlida, s'ignora: {t.get('data')!r} ({e})")
            continue
        if pd.isna(data_inici):
            print(f"  [!] Tractament amb data buida, s'ignora: {t.get('data')!r}")
            continue
        # L'historial té timestamps sense zona horària: normalitzem per poder comparar
        if data_inici.tzinfo is not None:
            data_inici = data_inici.tz_localize(None)

        dies_base = t.get("dies_proteccio") or DIES_PROTECCIO_DEFECTE
        ecologic  = t.get("ecologic") is True
        data_fi, degradat, motiu = calcular_fi_proteccio(
            data_inici, dies_base, ecologic, ts, pluja, temps
        )

        detall = f" (retallada: {motiu})" if degradat else ""
        print(f"  -> Protecció {t.get('producte', '?')}: "
              f"{data_inici:%d/%m/%Y %H:%M} -> {data_fi:%d/%m/%Y %H:%M} "
              f"[{dies_base}d nominals{', ecològic' if ecologic else ''}]{detall}")
        periodes.append((data_inici, data_fi))
    return periodes

# NOTA sobre la radiació UV
# -------------------------
# El codi anterior reduïa el risc un 80% quan l'índex UV superava 6. La idea
# té base biològica (E. necator és ectoparàsit i la UV degrada miceli i
# conidis; és el mecanisme pel qual el desfullat aporta control físic), però
# aquí no es pot aplicar així:
#   1. A Mallorca els 42 dies de l'històric tenen UV màxim >= 6, o sigui que
#      la penalització seria constant i l'índex no podria pujar mai.
#   2. La finestra tèrmica favorable és NOCTURNA (UV mitjana 0.07 de 21h a 8h)
#      mentre que la UV alta és de migdia (6.63). No coincideixen en el temps.
#   3. El model ja penalitza el xoc tèrmic (-10), que en aquest clima va
#      lligat a la insolació forta: seria comptar dues vegades el mateix.
# La UV es desa com a columna informativa (uv_max_dia) però no entra a
# l'índex. Reincorporar-la exigiria recalibrar el model amb dades de camp.


def calcular_gubler(df: pd.DataFrame) -> pd.DataFrame:
    """
    Índex de risc d'oïdi de Gubler-Thomas (UC Davis), escala 0-100.

    Regles diàries del model canònic:
      +20  si hi ha >= 6 h CONTÍNUES entre 21.1 i 29.4 °C
      -10  si no s'assoleix aquest bloc
      -10  si es toquen els 35 °C durant >= 15 min
      +10  net si es donen les dues coses alhora

    L'epidèmia no arrenca fins que no hi ha 3 dies consecutius favorables;
    llavors l'índex se situa a 60. Abans d'això es manté a 0: són les
    ascòspores les que han d'iniciar el cicle, i el model no dona risc
    conidial sense inòcul establert.

    Desviació deliberada respecte del model original: les ratxes tèrmiques
    es compten de forma contínua i no per dia natural. A Mallorca la
    finestra favorable és nocturna (la majoria de ratxes van de les ~21 h
    a les ~9 h) i tallar-les a mitjanit les partiria pel mig.
    """
    df = mu.ordenar_per_ts(df)

    t   = pd.to_numeric(df["temperatura_c"],       errors="coerce")
    uv  = pd.to_numeric(df.get("index_uv", np.nan), errors="coerce")
    rad = pd.to_numeric(df.get("radiacio_solar_wm2", np.nan), errors="coerce")

    dur = mu.durades(df["ts"])

    # Ratxa contínua dins la finestra tèrmica òptima
    dins_rang  = t.between(T_OPT_MIN, T_OPT_MAX)
    ratxa      = mu.ratxes(dins_rang, dur)
    df["hores_rang_optim"] = ratxa.round(2)

    tractaments        = carregar_tractaments()
    periodes_proteccio = obtenir_periodes_proteccio(tractaments, "oidio", df)

    def protegit(ts_val):
        return any(ini <= ts_val <= fi for ini, fi in periodes_proteccio)

    # ── Agregats diaris ──────────────────────────────────────────────────
    dies = {}
    for dia, g in df.groupby(df["ts"].dt.dayofyear):
        idx = g.index
        min_calor = sum((dur[i] if pd.notna(dur[i]) else 0) * 60
                        for i in idx if pd.notna(t[i]) and t[i] >= T_CALOR)
        dies[dia] = {
            "ratxa_max": float(ratxa[idx].max()),
            "min_calor": min_calor,
            "uv_max":    float(uv[idx].max())  if uv[idx].notna().any()  else np.nan,
            "rad_max":   float(rad[idx].max()) if rad[idx].notna().any() else np.nan,
            "protegit":  all(protegit(x) for x in g["ts"]),
        }

    # ── Índex diari ──────────────────────────────────────────────────────
    index_dia, arrencat, seguits = {}, False, 0
    valor = 0.0
    for dia in sorted(dies):
        d = dies[dia]
        favorable = d["ratxa_max"] >= HORES_CONTINUES_MIN
        calor     = d["min_calor"] >= MINUTS_CALOR_LIMIT

        if d["protegit"]:
            # Tractament vigent: el fong no pot progressar
            valor, arrencat, seguits = 0.0, False, 0
            index_dia[dia] = 0.0
            continue

        if not arrencat:
            # Fase d'arrencada: cal la seqüència de 3 dies favorables seguits
            seguits = seguits + 1 if favorable else 0
            if seguits >= DIES_ARRENCADA:
                arrencat, valor = True, float(PUNTS_ARRENCADA)
            index_dia[dia] = valor
            continue

        if favorable and calor:
            delta = PUNTS_FAVORABLE + PUNTS_CALOR      # +10 net
        elif favorable:
            delta = PUNTS_FAVORABLE
        elif calor:
            delta = PUNTS_DESFAVORABLE + PUNTS_CALOR
        else:
            delta = PUNTS_DESFAVORABLE

        valor = max(0.0, min(100.0, valor + delta))
        index_dia[dia] = valor

    # ── Projecció als registres ──────────────────────────────────────────
    dia_serie = df["ts"].dt.dayofyear
    df["index_gubler"]  = dia_serie.map(index_dia).astype(float).round(1)
    df["risc_gubler"]   = df["index_gubler"].apply(nivell_risc)

    # Mitjana mòbil de 7 dies del risc diari: és la base de l'índex d'OiDiag
    # (VitiMeteo), que en modula el resultat per la sensibilitat del raïm.
    # Evolucionar lentament és intencionat: evita que un sol dia dolent
    # dispari la decisió de tractar.
    risc_diari = pd.Series([index_dia[d] for d in sorted(index_dia)],
                           index=sorted(index_dia))
    mitjana7 = risc_diari.rolling(7, min_periods=1).mean().round(1)
    df["index_oidiag_meteo"] = dia_serie.map(mitjana7.to_dict()).astype(float)
    df["min_calor_dia"] = dia_serie.map({d: v["min_calor"] for d, v in dies.items()})
    df["uv_max_dia"]    = dia_serie.map({d: v["uv_max"] for d, v in dies.items()}).round(1)
    df["reinici_ui"]    = df["ts"].apply(lambda x: int(protegit(x)))

    # Columnes de l'escala antiga (0-150, puntuació per HR): ja no s'hi
    # escriuen valors i el dashboard no les llegeix.
    df = df.drop(columns=["ui_acumulades", "ui_horaria", "hora_favorable_oidio",
                          "risc_infeccio"], errors="ignore")

    return df

def main():
    if not os.path.exists(CSV_HISTORIAL):
        print("[WARNING] No s'ha trobat historial.csv")
        return
        
    df = pd.read_csv(CSV_HISTORIAL)
    df = calcular_gubler(df)
    
    # Aquest collector actualitza l'historial.csv directament
    df = df.drop(columns=["ts"], errors="ignore")
    df.to_csv(CSV_HISTORIAL, index=False)
    
    print(f"  OK Model Oïdi (Gubler+UV) processat: {len(df)} registres.")

if __name__ == "__main__":
    main()
