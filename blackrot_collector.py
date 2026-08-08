import pandas as pd
import numpy as np
import os
from datetime import datetime

import meteo_utils as mu

CSV_HISTORIAL = "data/historial.csv"

def model_spotts(lwd: float, t_mitj: float) -> str:
    """Model de Spotts (1977) per Black Rot. Retorna baix, moderat o alt."""
    if lwd < 6: return "baix"
    
    # Hores mínimes per infecció segons T (Spotts)
    if 20 <= t_mitj <= 26:
        h_infeccio = 6
    elif 15 <= t_mitj < 20 or 26 < t_mitj <= 29:
        h_infeccio = 9
    elif 10 <= t_mitj < 15:
        h_infeccio = 24
    else:
        return "baix"
        
    if lwd >= h_infeccio * 1.5: return "alt"
    if lwd >= h_infeccio: return "moderat"
    return "baix"

def calcular_blackrot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analitza els períodes d'humectació i aplica el model de Spotts.

    La durada de la humectació es mesura en hores reals: un forat de dades
    tanca l'episodi, perquè no sabem si la fulla va seguir molla.
    """
    df    = mu.ordenar_per_ts(df)
    dur   = mu.durades(df["ts"])
    fulla = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce")
    temps = pd.to_numeric(df["temperatura_c"], errors="coerce")

    risc_arr = ["baix"] * len(df)
    lwd_h, t_pond = 0.0, 0.0

    for i in range(len(df)):
        h = dur.iloc[i]
        if fulla.iloc[i] == 1 and pd.notna(h):
            lwd_h  += float(h)
            t_pond += (float(temps.iloc[i]) if pd.notna(temps.iloc[i]) else 0.0) * float(h)
            t_mitj  = t_pond / lwd_h if lwd_h > 0 else 0.0
            risc_arr[i] = model_spotts(lwd_h, t_mitj)
        else:
            # Sense aigua lliure el black rot no pot infectar: l'episodi s'atura.
            lwd_h, t_pond = 0.0, 0.0
            risc_arr[i] = "baix"

    df = df.drop(columns=["ts"])
    df["risc_blackrot"] = risc_arr
    return df

def main():
    if not os.path.exists(CSV_HISTORIAL):
        print("[WARNING] No s'ha trobat historial.csv")
        return
        
    df = pd.read_csv(CSV_HISTORIAL)
    df = calcular_blackrot(df)
    
    df = df.drop(columns=["ts"], errors="ignore")
    df.to_csv(CSV_HISTORIAL, index=False)
    
    print(f"  OK Model Black Rot (Spotts) processat: {len(df)} registres.")

if __name__ == "__main__":
    main()
