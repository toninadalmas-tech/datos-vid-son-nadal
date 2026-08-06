import re

with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Variables in generar_index & generar_vinya
text = text.replace(
    'risc_mildiu = str(ultima.get("risc_mildiu", "inactiu"))',
    'risc_mildiu = str(ultima.get("risc_mildiu", "inactiu"))\n    risc_botritis = str(ultima.get("risc_botritis", "baix"))\n    color_botritis = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_botritis, "#7a7269")\n    risc_blackrot = str(ultima.get("risc_blackrot", "baix"))\n    color_blackrot = {"baix":"#2e7d32","moderat":"#c77d00","alt":"#c62828"}.get(risc_blackrot, "#7a7269")'
)

# 2. HTML cards in generar_index & generar_vinya
card_old = """      <div class="crop-stat">
        <span><span class="dot" style="background:#7a7269"></span>Botritis</span>
        <span style="color:#7a7269">Sense model</span>
      </div>
      <div class="crop-stat">
        <span><span class="dot" style="background:#7a7269"></span>Black Rot</span>
        <span style="color:#7a7269">Sense model</span>
      </div>"""

card_new = """      <div class="crop-stat">
        <span><span class="dot" style="background:{color_botritis}"></span>Botritis</span>
        <span style="color:{color_botritis};font-weight:600">{risc_botritis.upper()}</span>
      </div>
      <div class="crop-stat">
        <span><span class="dot" style="background:{color_blackrot}"></span>Black Rot</span>
        <span style="color:{color_blackrot};font-weight:600">{risc_blackrot.upper()}</span>
      </div>"""
text = text.replace(card_old, card_new)

# 3. Replace generar_botritis
botritis_old_start = text.find("def generar_botritis() -> str:")
botritis_old_end = text.find("def generar_blackrot() -> str:")

botritis_new = """def generar_botritis(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")
    risc   = str(ultima.get("risc_botritis", "baix"))
    risc_color = {"baix":"#22c55e","moderat":"#f59e0b","alt":"#ef4444"}.get(risc, "#6b7280")
    
    parts = []
    parts.append("<!DOCTYPE html>\\n<html lang=\\"ca\\">")
    parts.append(generar_head("Botritis · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("botritis"))
    parts.append("<main>")
    
    parts.append(f\"\"\"
<div class="page-header">
  <div>
    <h1>Botritis</h1>
    <div class="sub">Botrytis cinerea · Model Broome (1995) · {ts_act}</div>
  </div>
  <span class="badge" style="color:{risc_color};border-color:{risc_color}">Risc: {risc.upper()}</span>
</div>

<div class="card" style="margin-bottom:24px;">
  {generar_filtre_bar()}
  <div style="height:350px;width:100%;position:relative;">
    <canvas id="chartModel"></canvas>
  </div>
</div>
\"\"\")
    parts.append(generar_recomanacio_tractament("botritis"))
    parts.append(generar_tractaments_section("botritis"))
    parts.append("</main>")
    parts.append(generar_footer())
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append("const MALALTIA_FILTRE = 'botritis';")
    parts.append("if (typeof setFilter !== 'undefined') { setFilter('7d'); }")
    parts.append("</script>")
    parts.append("</body>\\n</html>")
    return "\\n".join(parts)

"""

# 4. Replace generar_blackrot
blackrot_old_start = botritis_old_end
blackrot_old_end = text.find("def _hex_to_rgb(hex_col: str) -> tuple:")

blackrot_new = """def generar_blackrot(df: pd.DataFrame) -> str:
    data_json = preparar_dades_json(df)
    ultima = df.iloc[-1]
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")
    risc   = str(ultima.get("risc_blackrot", "baix"))
    risc_color = {"baix":"#22c55e","moderat":"#f59e0b","alt":"#ef4444"}.get(risc, "#6b7280")
    
    parts = []
    parts.append("<!DOCTYPE html>\\n<html lang=\\"ca\\">")
    parts.append(generar_head("Black Rot · Son Nadal"))
    parts.append("<body>")
    parts.append(generar_navbar("blackrot"))
    parts.append("<main>")
    
    parts.append(f\"\"\"
<div class="page-header">
  <div>
    <h1>Black Rot</h1>
    <div class="sub">Guignardia bidwellii · Model Spotts (1977) · {ts_act}</div>
  </div>
  <span class="badge" style="color:{risc_color};border-color:{risc_color}">Risc: {risc.upper()}</span>
</div>

<div class="card" style="margin-bottom:24px;">
  {generar_filtre_bar()}
  <div style="height:350px;width:100%;position:relative;">
    <canvas id="chartModel"></canvas>
  </div>
</div>
\"\"\")
    parts.append(generar_recomanacio_tractament("blackrot"))
    parts.append(generar_tractaments_section("blackrot"))
    parts.append("</main>")
    parts.append(generar_footer())
    parts.append("<script>")
    parts.append(f"const ALL = {data_json};")
    parts.append("const MALALTIA_FILTRE = 'blackrot';")
    parts.append("if (typeof setFilter !== 'undefined') { setFilter('7d'); }")
    parts.append("</script>")
    parts.append("</body>\\n</html>")
    return "\\n".join(parts)

"""

text = text[:botritis_old_start] + botritis_new + blackrot_new + text[blackrot_old_end:]

# Update the main function to pass df to generar_botritis and generar_blackrot
text = text.replace("generar_botritis()", "generar_botritis(df)")
text = text.replace("generar_blackrot()", "generar_blackrot(df)")

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Dashboard refactored successfully.")
