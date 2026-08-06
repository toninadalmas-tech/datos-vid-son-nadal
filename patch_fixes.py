import re

# 1. Fix JS in app.js
with open("docs/assets/app.js", "r", encoding="utf-8") as f:
    app_text = f.read()

fix_llegir = """    let contingut = JSON.parse(txt);
    if (typeof contingut !== 'object' || contingut === null) {
       contingut = { varietats: {}, activa_oidi: typeof contingut === 'string' ? contingut : 'auto_moscatell' };
    } else if (contingut.fase !== undefined) {
       contingut = { varietats: {}, activa_oidi: contingut.fase || 'auto_moscatell' };
    }
    return contingut;"""
app_text = re.sub(r"const contingut = JSON\.parse\(txt\);.*?return contingut;", fix_llegir, app_text, flags=re.DOTALL)

# Remove the old canviFase
app_text = re.sub(r"async function canviFase\(val\) \{\s*updateKastRisk\(val\);\s*await guardarFaseRepo\(val\);\s*\}", "", app_text)

with open("docs/assets/app.js", "w", encoding="utf-8") as f:
    f.write(app_text)


# 2. Fix timeline in generate_dashboard.py
with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    py_text = f.read()

# Remove the empty block I left by accident
py_text = py_text.replace("    # Condicions i Timeline\n\n    # Tractaments", "    # Tractaments")

# Insert timeline for Oïdi under KPIs
oidi_kpi_end = '  </div>\n</div>\n""")\n\n    # Filtre + gràfiques'
py_text = py_text.replace(oidi_kpi_end, '  </div>\n</div>\n""")\n\n    parts.append(generar_condicions("oidi"))\n    parts.append(generar_timeline("oidi"))\n\n    # Filtre + gràfiques')

# Insert timeline for Mildiu under KPIs
mildiu_kpi_end = '  </div>\n</div>\n""")\n\n    # Targetes recomanació'
py_text = py_text.replace(mildiu_kpi_end, '  </div>\n</div>\n""")\n\n    parts.append(generar_condicions("mildiu"))\n    parts.append(generar_timeline("mildiu"))\n\n    # Targetes recomanació')

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(py_text)
