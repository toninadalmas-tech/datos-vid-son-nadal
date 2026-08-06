import re

with open("mildiu_collector.py", "r", encoding="utf-8") as f:
    text = f.read()

# Substitucions de text
text = text.replace("hores_hr95", "hores_fulla_molla")
text = text.replace("HR >= 95%", "fulla_molla == 1")
text = text.replace("HORES_HR_MIN", "HORES_FULLA_MOLLA_MIN")
text = text.replace("hores_hr", "hores_fm")
text = text.replace("HR_MIN_SEC", "HORES_FULLA_MOLLA_MIN")
text = text.replace("Hores HR>=95%", "Hores Fulla Molla")

# Substituir calcular_hores_fulla_molla manualment ja que la lògica interna canvia
# Abans:
# def calcular_hores_fulla_molla(df: pd.DataFrame) -> pd.Series:
#     hr = pd.to_numeric(df["humitat_pct"], errors="coerce")
#     alta_hr = (hr >= HORES_FULLA_MOLLA_MIN).astype(int)

# Buscar def calcular_hores_fulla_molla i substituir-lo
nova_funcio = """def calcular_hores_fulla_molla(df: pd.DataFrame) -> pd.Series:
    \"\"\"
    Intervals consecutius de 30 min amb fulla_molla == 1.
    Reinicia a 0 quan s'asseca.
    \"\"\"
    fulla = pd.to_numeric(df.get("fulla_molla", 0), errors="coerce")

    comptador = np.zeros(len(df))
    cnt = 0
    for i in range(len(df)):
        if fulla.iloc[i] == 1:
            cnt += 1
        else:
            cnt = 0
        comptador[i] = cnt

    return pd.Series(comptador * 0.5, index=df.index).round(1)"""

import re
text = re.sub(r'def calcular_hores_fulla_molla\(df.*?return pd\.Series\(comptador \* 0\.5, index=df\.index\)\.round\(1\)', nova_funcio, text, flags=re.DOTALL)

with open("mildiu_collector.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Done")
