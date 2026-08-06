import re

with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

def repl(m):
    content = m.group(1)
    return 'parts.append("""' + content + '""")\n    parts.append("if (typeof setFilter !== \'undefined\') { setFilter(\'7d\'); }")'

text = re.sub(r'parts\.append\("\n(let chartModel;.*?)\n    if \(typeof setFilter !== \'undefined\'\) \{ setFilter\(\'7d\'\); \}"\)', repl, text, flags=re.DOTALL)

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed syntax")
