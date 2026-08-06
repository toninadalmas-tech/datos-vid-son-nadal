import generate_dashboard as gd
import os

with open('docs/assets/style.css', 'w', encoding='utf-8') as f:
    f.write(gd.CSS)

with open('docs/assets/app.js', 'w', encoding='utf-8') as f:
    f.write(gd.JS_THEME + "\n" + gd.JS_FILTER + "\n" + gd.JS_CHART_BASE + "\n" + gd.JS_TRACTAMENTS + "\n" + gd.JS_FASE_KAST)

with open('generate_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("CSS = ") or line.startswith("JS_THEME = ") or line.startswith("JS_FILTER = ") or line.startswith("JS_CHART_BASE = ") or line.startswith("JS_TRACTAMENTS = ") or line.startswith("JS_FASE_KAST = "):
        skip = True
    
    if skip and '"""' in line and (line.startswith('"""') or line.strip() == '"""'):
        skip = False
        continue
    
    if not skip:
        # Remove parts.append for JS components
        if any(v in line for v in ["parts.append(JS_CHART_BASE)", "parts.append(JS_FILTER)", "parts.append(JS_TRACTAMENTS)", "parts.append(JS_FASE_KAST)", "parts.append(JS_THEME)"]):
            continue
        
        # Replace <style>{CSS}</style> with <link...> and add <script src=app.js>
        if "<style>{CSS}</style>" in line:
            line = line.replace("<style>{CSS}</style>", '<link rel="stylesheet" href="assets/style.css">\n  <script src="assets/app.js"></script>')
        
        new_lines.append(line)

with open('generate_dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Refactorització completada amb èxit!")
