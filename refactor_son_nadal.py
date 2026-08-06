with open("son_nadal_collector.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("# ── Model de Gubler ──────────────────────────────────────────────────────────")
text = text[:idx]

new_tail = """
# ── Historial ─────────────────────────────────────────────────────────────────
def actualitzar_historial(df_nou: pd.DataFrame) -> pd.DataFrame:
    import os
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CSV_HISTORIAL):
        df_old = pd.read_csv(CSV_HISTORIAL)
        df_tot = pd.concat([df_old, df_nou], ignore_index=True)
        df_tot = df_tot.drop_duplicates(subset=["timestamp"], keep="last")
    else:
        df_tot = df_nou

    df_tot = df_tot.sort_values("timestamp").reset_index(drop=True)
    df_tot.to_csv(CSV_HISTORIAL, index=False)

    registres_nous = len(df_nou)
    print(f"  -> {registres_nous} registres nous | {len(df_tot)} totals -> {CSV_HISTORIAL}")
    return df_tot


# ── Resum ─────────────────────────────────────────────────────────────────────
def resum(df: pd.DataFrame):
    print(f"\\n{'-'*50}")
    ult24 = df.tail(48)
    print(f"  Últimes 24h  ({len(ult24)} registres)")
    for col, nom, unit in [
        ("temperatura_c",   "Temperatura", "°C"),
        ("humitat_pct",     "Humitat",     "%"),
        ("precipitacio_mm", "Pluja",       "mm"),
    ]:
        if col in ult24.columns:
            s = pd.to_numeric(ult24[col], errors="coerce").dropna()
            if len(s):
                print(f"  {nom:<12}: min={s.min():.1f}{unit}  max={s.max():.1f}{unit}  mitj={s.mean():.1f}{unit}")
    print(f"{'-'*50}\\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    from datetime import datetime
    print(f"\\n[{datetime.now():%Y-%m-%d %H:%M}] Col·lector Son Nadal iniciat")
    print("-" * 50)
    print("-> Descarregant sensors des de Google Charts JSON...")

    df_nou = obtenir_dades()

    if df_nou is None or df_nou.empty:
        print("\\n[WARNING] No s'han pogut obtenir dades.")
        raise SystemExit(1)

    df_historial = actualitzar_historial(df_nou)
    resum(df_historial)


if __name__ == "__main__":
    main()
"""

with open("son_nadal_collector.py", "w", encoding="utf-8") as f:
    f.write(text + new_tail)

print("Done")
