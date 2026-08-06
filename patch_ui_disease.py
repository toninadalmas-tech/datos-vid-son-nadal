import re

with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

helpers = """
def generar_timeline(malaltia: str) -> str:
    timelines = {
        "oidi": [("MAR", 1), ("ABR", 2), ("MAI", 3), ("JUN", 3), ("JUL", 3), ("AGO", 1), ("SET", 0), ("OCT", 0)],
        "mildiu": [("MAR", 1), ("ABR", 3), ("MAI", 3), ("JUN", 2), ("JUL", 0), ("AGO", 0), ("SET", 2), ("OCT", 3)],
        "botritis": [("MAR", 0), ("ABR", 0), ("MAI", 2), ("JUN", 1), ("JUL", 0), ("AGO", 2), ("SET", 3), ("OCT", 3)],
        "blackrot": [("MAR", 0), ("ABR", 2), ("MAI", 3), ("JUN", 3), ("JUL", 1), ("AGO", 0), ("SET", 0), ("OCT", 0)],
    }
    
    tl = timelines.get(malaltia, [])
    if not tl: return ""
    
    colors = {0: "rgba(107,114,128,0.1)", 1: "#fde047", 2: "#f97316", 3: "#ef4444"}
    
    html = '<div class="card" style="margin-bottom:24px;">'
    html += '<div class="card-title">🗓️ Calendari Anual de Risc (Clima Mediterrani / Mallorca)</div>'
    html += '<div style="display:flex; width:100%; height:12px; border-radius:4px; overflow:hidden; margin-top:12px;">'
    for m, r in tl:
        html += f'<div style="flex:1; background-color:{colors[r]};" title="{m}"></div>'
    html += '</div>'
    html += '<div style="display:flex; width:100%; justify-content:space-between; margin-top:4px; font-size:11px; color:var(--muted);">'
    for m, r in tl:
        html += f'<div style="flex:1; text-align:center;">{m}</div>'
    html += '</div>'
    html += '<div style="margin-top:12px; font-size:12px; color:var(--muted); display:flex; gap:16px;">'
    html += '<span><span style="display:inline-block;width:10px;height:10px;background:rgba(107,114,128,0.1);border-radius:2px;"></span> Risc Nul</span>'
    html += '<span><span style="display:inline-block;width:10px;height:10px;background:#fde047;border-radius:2px;"></span> Risc Baix</span>'
    html += '<span><span style="display:inline-block;width:10px;height:10px;background:#f97316;border-radius:2px;"></span> Risc Alt</span>'
    html += '<span><span style="display:inline-block;width:10px;height:10px;background:#ef4444;border-radius:2px;"></span> Risc Màxim</span>'
    html += '</div>'
    html += '</div>'
    return html

def generar_condicions(malaltia: str) -> str:
    conds = {
        "botritis": "<b>Condicions favorables:</b> Necessita aigua lliure (fulla molla) durant un mínim de 15 hores continuades si la temperatura és suau (15-20ºC). La susceptibilitat és màxima durant la maduració del raïm (agost-setembre) i en ferides obertes. No suporta bé la sequera ni la calor extrema.",
        "blackrot": "<b>Condicions favorables:</b> Depèn completament de la combinació temperatura i aigua lliure (Fulla Molla). A 26.5ºC només necessita 6 hores de fulla molla per infectar, mentre que a 10ºC en necessita 24. Afecta sobretot a la primavera i principis d'estiu.",
        "oidi": "<b>Condicions favorables:</b> No necessita aigua líquida, de fet, la pluja forta renta les espores. Es desenvolupa ràpidament entre els 20ºC i els 30ºC amb humitats relatives altes. La llum ultraviolada (>6 UI) i temperatures per sobre dels 35ºC aturen i maten el fong.",
        "mildiu": "<b>Condicions favorables:</b> Necessita pluja o aigua lliure abundant. La infecció primària requereix la <i>Regla dels 3 Deus</i>: Brots de 10cm, Temperatura de 10ºC, i pluges de 10mm. Les infeccions secundàries s'escampen ràpid amb hores de fulla molla i nits càlides."
    }
    
    if malaltia not in conds: return ""
    return f'<div class="card" style="margin-bottom:24px; font-size:14px; line-height:1.6; color:var(--text);">🔬 {conds[malaltia]}</div>'
"""

text = text.replace('def generar_recomanacio_tractament', helpers + '\ndef generar_recomanacio_tractament')

def insert_in_page(page, text):
    call_timeline = f'    parts.append(generar_timeline("{page}"))\n'
    call_conds = f'    parts.append(generar_condicions("{page}"))\n'
    return text.replace(
        f'parts.append(generar_recomanacio_tractament("{page}"))',
        call_conds + call_timeline + f'    parts.append(generar_recomanacio_tractament("{page}"))'
    )

text = insert_in_page("oidi", text)
text = insert_in_page("mildiu", text)
text = insert_in_page("botritis", text)
text = insert_in_page("blackrot", text)

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)
print("UI patched")
