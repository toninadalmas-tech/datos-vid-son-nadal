import pandas as pd
import numpy as np
from datetime import datetime
import os, json

CSV_HISTORIAL = "data/historial.csv"

def carregar_tractaments():
    try:
        with open("tractaments.json", "r", encoding="utf-8") as f:
            return json.load(f).get("tractaments", [])
    except Exception:
        return []

def obtenir_periodes_proteccio(tractaments, malaltia, dies_efecte):
    periodes = []
    for t in tractaments:
        if malaltia in t.get("malalties", []):
            try:
                data_inici = datetime.strptime(t["data"], "%Y-%m-%d")
                data_fi = data_inici + pd.Timedelta(days=dies_efecte)
                periodes.append((data_inici, data_fi))
            except Exception:
                pass
    return periodes

def ui_horaria(t: float, hr: float, uv: float, rad: float) -> float:
    """
    Calcula les Unitats d'Infecció per a una hora donada.
    S'hi afegeix la penalització per Radiació Solar / Índex UV.
    """
    if pd.isna(t) or pd.isna(hr): return 0.0
    if t < 15 or t > 35 or hr < 40: return 0.0

    # Factor HR
    if hr >= 90: f_hr = 3
    elif hr >= 70: f_hr = 2
    elif hr >= 50: f_hr = 1
    else: f_hr = 0
    
    base = [1.0, 2.0, 3.0, 4.0][f_hr]
    if 20 <= t <= 27: base *= 2.0
    
    # Penalització UV (Austin & Wilcox, 2012)
    if pd.notna(uv) and uv >= 6:
        base *= 0.2  # 80% reducció per UV extrem
    elif pd.notna(rad) and rad > 600:
        base *= 0.5  # 50% reducció per insolació forta
        
    return base

def calcular_gubler(df: pd.DataFrame) -> pd.DataFrame:
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = df.sort_values("ts").reset_index(drop=True)

    t_col  = pd.to_numeric(df["temperatura_c"],   errors="coerce")
    hr_col = pd.to_numeric(df["humitat_pct"],      errors="coerce")
    p_col  = pd.to_numeric(df["precipitacio_mm"],  errors="coerce").fillna(0)
    uv_col = pd.to_numeric(df.get("index_uv", np.nan), errors="coerce")
    rad_col = pd.to_numeric(df.get("radiacio_solar_wm2", np.nan), errors="coerce")

    ui_h    = np.zeros(len(df))
    ui_acc  = np.zeros(len(df))
    reinici = np.zeros(len(df), dtype=int)

    acumulat = 0.0
    calor_cnt = 0
    
    tractaments = carregar_tractaments()
    periodes_proteccio = obtenir_periodes_proteccio(tractaments, "oidio", 10)

    for i in range(len(df)):
        t  = t_col.iloc[i]
        hr = hr_col.iloc[i]
        p  = p_col.iloc[i]
        uv = uv_col.iloc[i]
        rad = rad_col.iloc[i]
        ts = df["ts"].iloc[i]

        es_protegit = False
        for inici, fi in periodes_proteccio:
            if inici <= ts <= fi:
                es_protegit = True
                break
                
        if es_protegit:
            acumulat = 0.0
            reinici[i] = 1
            calor_cnt = 0
            ui_h[i] = 0.0
            ui_acc[i] = acumulat
            continue

        reset = False
        if p >= 2.0:
            reset = True
        
        if pd.notna(t) and t > 35:
            calor_cnt += 1
        else:
            calor_cnt = 0
            
        if calor_cnt >= 3:
            reset = True

        if reset:
            acumulat = 0.0
            reinici[i] = 1
        else:
            ui = ui_horaria(t, hr, uv, rad)
            # Normalitzar a 30 min (fórmula original assumia hores)
            ui_h[i] = ui / 2.0
            acumulat += ui_h[i]
            
        ui_acc[i] = acumulat

    df["ui_horaria"] = np.round(ui_h, 2)
    df["ui_acumulades"] = np.round(ui_acc, 2)
    df["reinici_ui"] = reinici

    def risc_f(x):
        if x < 50: return "baix"
        elif x < 100: return "moderat"
        elif x < 150: return "alt"
        else: return "molt alt"
    
    df["risc_gubler"] = df["ui_acumulades"].apply(risc_f)
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
