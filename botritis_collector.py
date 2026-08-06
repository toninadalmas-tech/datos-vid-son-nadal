import pandas as pd
import numpy as np
import os
from datetime import datetime

CSV_HISTORIAL = "data/historial.csv"

def model_broome(lwd: float, t_mitj: float) -> float:
    """Model empíric de Broome (1995) per Botritis."""
    if lwd < 2: return 0.0
    # Equació logística
    W = -4.268 + (0.0901 * lwd * t_mitj) - (0.0016 * lwd * (t_mitj**2)) - (0.0353 * lwd) - (0.4192 * t_mitj) + (0.0152 * (t_mitj**2))
    # Risc de 0 a 100%
    return (np.exp(W) / (1 + np.exp(W))) * 100.0

def calcular_botritis(df: pd.DataFrame) -> pd.DataFrame:
    """Analitza els períodes d'humectació i aplica el model de Broome."""
    fulla = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce")
    temps = pd.to_numeric(df["temperatura_c"], errors="coerce")
    
    risc_arr = np.zeros(len(df))
    
    lwd_h = 0.0
    t_sum = 0.0
    for i in range(len(df)):
        if fulla.iloc[i] == 1:
            lwd_h += 0.5
            t_sum += temps.iloc[i] if pd.notna(temps.iloc[i]) else 0.0
            t_mitj = t_sum / (lwd_h / 0.5)
            risc_arr[i] = model_broome(lwd_h, t_mitj)
        else:
            # S'asseca, mantenim el risc del darrer període d'humectació fins 24h o decreixem?
            # Botritis pot incubar-se. Mantindrem el darrer pic de risc alt o baixem ràpid.
            lwd_h = 0.0
            t_sum = 0.0
            risc_arr[i] = risc_arr[i-1] * 0.95 if i > 0 else 0.0

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
