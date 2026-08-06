import pandas as pd
import numpy as np
import os
from datetime import datetime

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
    """Analitza els períodes d'humectació i aplica el model de Spotts."""
    fulla = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce")
    temps = pd.to_numeric(df["temperatura_c"], errors="coerce")
    
    risc_arr = ["baix"] * len(df)
    
    lwd_h = 0.0
    t_sum = 0.0
    for i in range(len(df)):
        if fulla.iloc[i] == 1:
            lwd_h += 0.5
            t_sum += temps.iloc[i] if pd.notna(temps.iloc[i]) else 0.0
            t_mitj = t_sum / (lwd_h / 0.5)
            risc_arr[i] = model_spotts(lwd_h, t_mitj)
        else:
            lwd_h = 0.0
            t_sum = 0.0
            risc_arr[i] = "baix" # Blackrot requereix fulla molla per infectar, assecat atura.

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
