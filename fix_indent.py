import re

with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

# Fix the messy indentation created by the previous replace
text = re.sub(r'[ ]*parts\.append\(generar_condicions\("([^"]+)"\)\)', r'    parts.append(generar_condicions("\1"))', text)
text = re.sub(r'[ ]*parts\.append\(generar_timeline\("([^"]+)"\)\)', r'    parts.append(generar_timeline("\1"))', text)
text = re.sub(r'[ ]*parts\.append\(generar_recomanacio_tractament\("([^"]+)"\)\)', r'    parts.append(generar_recomanacio_tractament("\1"))', text)

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Indentation fixed")
