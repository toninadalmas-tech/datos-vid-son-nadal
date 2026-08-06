import re

with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Move Timeline for Oidi and Mildiu
text = text.replace('    parts.append(generar_condicions("oidi"))\n    parts.append(generar_timeline("oidi"))\n', '')
text = text.replace('    parts.append(generar_condicions("mildiu"))\n    parts.append(generar_timeline("mildiu"))\n', '')

# Insert for Oïdi
text = text.replace("""<div class="kpi-val">{ui_act:.0f}<span class="kpi-unit">UI</span></div>
  </div>
</div>
\"\"\" )""", """<div class="kpi-val">{ui_act:.0f}<span class="kpi-unit">UI</span></div>
  </div>
</div>
\"\"\" )
    parts.append(generar_condicions("oidi"))
    parts.append(generar_timeline("oidi"))""")

# Insert for Mildiu
text = text.replace("""<div class="kpi-val">{hr_act:.0f}<span class="kpi-unit">%</span></div>
  </div>
</div>
\"\"\" )""", """<div class="kpi-val">{hr_act:.0f}<span class="kpi-unit">%</span></div>
  </div>
</div>
\"\"\" )
    parts.append(generar_condicions("mildiu"))
    parts.append(generar_timeline("mildiu"))""")

# 2. Add Phenology Cards to Index
phenology_html = """
    parts.append('<div class="card" style="margin-bottom:24px;">')
    parts.append('  <div class="card-title">🍇 Estats Fenològics (Predicció GDD i Control)</div>')
    parts.append('  <div style="font-size:12px;color:var(--muted);margin-bottom:16px;">El sistema calcula automàticament la fase fenològica segons la integral tèrmica (GDD) des de març. Pots forçar l\\'estat manualment si l\\'observació al camp és diferent.</div>')
    parts.append('  <div class="kpi-grid" id="feno-grid">')
    parts.append('    <div style="font-size:13px; color:var(--muted);">Carregant estat des del servidor...</div>')
    parts.append('  </div>')
    parts.append('</div>')

"""
text = text.replace('    # Mapa\n    parts.append(\'<div class="section-title" style="display:flex; justify-content:space-between; align-items:center;">\')', phenology_html + '    # Mapa\n    parts.append(\'<div class="section-title" style="display:flex; justify-content:space-between; align-items:center;">\')')

# 3. Simplify Oïdi selector
old_select = """<select id="sel-fase" onchange="canviFase(this.value)" style="margin-bottom:8px">
    <optgroup label="🤖 Automàtic (Predicció per GDD)">
        <option value="auto_moscatell">⚙️ Moscatell (Primerenca)</option>
        <option value="auto_prensal">⚙️ Premsal Blanc</option>
        <option value="auto_callet">⚙️ Callet</option>
        <option value="auto_manto_negro">⚙️ Manto Negro</option>
        <option value="auto_cabernet">⚙️ Cabernet (Tardana)</option>
    </optgroup>
    <optgroup label="🖐️ Manual (Forçar Estat)">
        <option value="1">🌱 Fase 1: Brotació a Pre-floració</option>
        <option value="2">🌼 Fase 2: Floració i Quallat</option>
        <option value="3">🍇 Fase 3: Creixement del gra</option>
        <option value="4">🟢 Fase 4: Tancament del raïm</option>
        <option value="5">🟣 Fase 5: Envero i Maduració</option>
    </optgroup>
  </select>
  <div id="auto-fase-lbl" style="display:none; font-size:13px; font-weight:600; color:#3b82f6; margin-bottom:8px; padding:6px 10px; background:rgba(59,130,246,0.1); border-radius:4px;"></div>
  <div style="font-size:12px;color:var(--muted);">
    L'edat del raïm modifica el risc real d'infecció. Pots deixar que el sistema ho calculi automàticament o forçar-ho a mà.
  </div>"""

new_select = """<label style="margin-top:0">Tria la varietat a avaluar per l'Oïdi (les dades s'agafen de la pàgina principal):</label>
  <select id="sel-fase" onchange="canviFase(this.value)" style="margin-bottom:8px">
        <option value="auto_moscatell">🍇 Moscatell (Primerenca)</option>
        <option value="auto_prensal">🍇 Premsal Blanc</option>
        <option value="auto_callet">🍇 Callet</option>
        <option value="auto_manto_negro">🍇 Manto Negro</option>
        <option value="auto_cabernet">🍇 Cabernet (Tardana)</option>
  </select>
  <div id="auto-fase-lbl" style="display:none; font-size:13px; font-weight:600; color:#3b82f6; margin-bottom:8px; padding:6px 10px; background:rgba(59,130,246,0.1); border-radius:4px;"></div>"""

text = text.replace(old_select, new_select)
text = text.replace('Gestió de l\'Estat Fenològic:', '')

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)

print("generate_dashboard.py patched")
