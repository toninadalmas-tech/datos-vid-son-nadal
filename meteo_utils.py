"""
meteo_utils.py – Utilitats compartides pels models epidemiològics
==================================================================
Els col·lectors compten "hores consecutives" (fulla molla, ratxes tèrmiques,
graus-dia). Fins ara multiplicaven el nombre de registres per 0.5 assumint
intervals regulars de 30 min, però l'historial té forats: un salt de 6 h
comptava com 0.5 h, i una ratxa partida per un forat es comptava com contínua.

Aquestes funcions treballen amb durades reals i tallen les ratxes quan el
salt entre registres supera un llindar.
"""

import pandas as pd
import numpy as np

# Salt màxim entre dos registres perquè es considerin consecutius.
# Els registres són cada 30 min; per sobre d'1 h assumim que hi ha un forat.
FORAT_MAX_H = 1.0


def durades(ts: pd.Series, forat_max_h: float = FORAT_MAX_H) -> pd.Series:
    """
    Durada en hores que representa cada registre (fins al següent).

    Retorna NaN quan el salt cap al registre següent supera forat_max_h:
    aquell tram no es pot comptabilitzar perquè no en tenim dades.
    L'últim registre hereta la durada del penúltim.
    """
    d = ts.diff().shift(-1).dt.total_seconds() / 3600.0
    d = d.where(d <= forat_max_h, np.nan)
    if len(d) > 1:
        d.iloc[-1] = d.iloc[-2]
    return d


def ratxes(condicio: pd.Series, dur: pd.Series) -> pd.Series:
    """
    Hores acumulades de la ratxa contínua en curs, per a cada registre.

    La ratxa es reinicia quan la condició deixa de complir-se o quan hi ha
    un forat de dades (durada NaN), perquè no podem afirmar que la condició
    s'hagi mantingut durant el buit.
    """
    out = np.zeros(len(condicio))
    acc = 0.0
    for i in range(len(condicio)):
        h = dur.iloc[i]
        if bool(condicio.iloc[i]) and pd.notna(h):
            acc += float(h)
        else:
            acc = 0.0
        out[i] = acc
    return pd.Series(out, index=condicio.index)


def hores_condicio(condicio: pd.Series, dur: pd.Series) -> float:
    """Total d'hores reals en què es compleix la condició (ignorant forats)."""
    m = condicio.astype(bool) & dur.notna()
    return float(dur[m].sum())


def es_nit(df: pd.DataFrame) -> pd.Series:
    """
    Foscor, a partir de la radiació solar d'Open-Meteo.

    P. viticola només esporula de nit: la radiació solar atura l'elongació
    de l'esporangiòfor. Si no hi ha dades de radiació, s'aproxima per hora
    solar (21h-06h), que és una franja conservadora per a Mallorca.
    """
    rad = pd.to_numeric(df.get("radiacio_solar_wm2", np.nan), errors="coerce")
    if rad.notna().any():
        return rad.fillna(0) <= 1.0
    hora = df["ts"].dt.hour
    return (hora >= 21) | (hora <= 6)


def ordenar_per_ts(df: pd.DataFrame) -> pd.DataFrame:
    """Afegeix la columna 'ts' i ordena cronològicament (no pel text del timestamp)."""
    df = df.copy()
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
