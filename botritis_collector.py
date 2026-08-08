import pandas as pd
import numpy as np
import os
from datetime import datetime

import meteo_utils as mu

CSV_HISTORIAL = "data/historial.csv"

# Decaïment del risc quan la fulla s'asseca, per hora real.
# El model de Broome descriu un episodi d'humectació complet; el decaïment
# posterior no forma part del model original i és una aproximació nostra.
DECAIMENT_PER_HORA = 0.90

def model_broome(lwd: float, t_mitj: float) -> float:
    """Model empíric de Broome (1995) per Botritis."""
    if lwd < 2: return 0.0
    # Equació logística
    W = -4.268 + (0.0901 * lwd * t_mitj) - (0.0016 * lwd * (t_mitj**2)) - (0.0353 * lwd) - (0.4192 * t_mitj) + (0.0152 * (t_mitj**2))
    # Risc de 0 a 100%
    return (np.exp(W) / (1 + np.exp(W))) * 100.0

def calcular_botritis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analitza els períodes d'humectació i aplica el model de Broome.

    La durada de la humectació es mesura en hores reals: si hi ha un forat
    de dades, l'episodi es talla, perquè no podem afirmar que la fulla
    hagi seguit molla durant el buit.
    """
    df    = mu.ordenar_per_ts(df)
    dur   = mu.durades(df["ts"])
    fulla = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce")
    temps = pd.to_numeric(df["temperatura_c"], errors="coerce")

    risc_arr = np.zeros(len(df))
    lwd_h, t_pond = 0.0, 0.0

    for i in range(len(df)):
        h = dur.iloc[i]
        if fulla.iloc[i] == 1 and pd.notna(h):
            lwd_h  += float(h)
            t_pond += (float(temps.iloc[i]) if pd.notna(temps.iloc[i]) else 0.0) * float(h)
            t_mitj  = t_pond / lwd_h if lwd_h > 0 else 0.0
            risc_arr[i] = model_broome(lwd_h, t_mitj)
        else:
            # La fulla s'asseca (o hi ha un forat): l'episodi es tanca i el
            # risc decau de forma proporcional al temps transcorregut.
            lwd_h, t_pond = 0.0, 0.0
            hores = float(h) if pd.notna(h) else 0.5
            risc_arr[i] = risc_arr[i-1] * (DECAIMENT_PER_HORA ** hores) if i > 0 else 0.0

    df = df.drop(columns=["ts"])
    df["risc_botritis_pct"] = np.round(risc_arr, 1)
    
    def eval_risc(x):
        if x < 20: return "baix"
        elif x < 50: return "moderat"
        else: return "alt"
        
    df["risc_botritis"] = df["risc_botritis_pct"].apply(eval_risc)
    return df

def main():
    if not os.path.exists(CSV_HISTORIAL):
        print("[WARNING] No s'ha trobat historial.csv")
        return
        
    df = pd.read_csv(CSV_HISTORIAL)
    df = calcular_botritis(df)
    
    df = df.drop(columns=["ts"], errors="ignore")
    df.to_csv(CSV_HISTORIAL, index=False)
    
    print(f"  OK Model Botritis (Broome) processat: {len(df)} registres.")

if __name__ == "__main__":
    main()
