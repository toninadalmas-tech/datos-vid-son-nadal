import os

tail = """
def _hex_to_rgb(hex_col: str) -> tuple:
    if not hex_col: return (0,0,0)
    hex_col = hex_col.lstrip('#')
    return tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = carregar_dades()

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(generar_index(df))

    with open(os.path.join(OUTPUT_DIR, "vinya.html"), "w", encoding="utf-8") as f:
        f.write(generar_vinya(df))

    with open(os.path.join(OUTPUT_DIR, "oidi.html"), "w", encoding="utf-8") as f:
        f.write(generar_oidi(df))

    with open(os.path.join(OUTPUT_DIR, "mildiu.html"), "w", encoding="utf-8") as f:
        f.write(generar_mildiu(df))

    with open(os.path.join(OUTPUT_DIR, "botritis.html"), "w", encoding="utf-8") as f:
        f.write(generar_botritis(df))

    with open(os.path.join(OUTPUT_DIR, "blackrot.html"), "w", encoding="utf-8") as f:
        f.write(generar_blackrot(df))

    print(f"  OK Dashboard generat a {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
"""

with open("generate_dashboard.py", "a", encoding="utf-8") as f:
    f.write(tail)

with open("oidi_collector.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('return json.load(f)', 'return json.load(f).get("tractaments", [])')
text = text.replace('if malaltia in t.get("malaltia", []):', 'if malaltia in t.get("malalties", []):')

with open("oidi_collector.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed")
