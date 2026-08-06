import re

with open("docs/assets/app.js", "r", encoding="utf-8") as f:
    app_text = f.read()

# Wrap updateKastRisk body in try-catch to print error
new_body = """
  try {
     const origFunc = function() {
        {BODY}
     };
     origFunc();
  } catch (e) {
     const recomBox = document.getElementById('oidi-recom-box');
     if (recomBox) {
        recomBox.innerHTML = '<div style="color:red; background:#fee2e2; padding:10px; border-radius:8px;">' + e.toString() + '<br>' + e.stack + '</div>';
     }
  }
"""

# Extract the body of updateKastRisk
start_idx = app_text.find("function updateKastRisk(faseVal, varietatsOverrides = {}) {")
if start_idx != -1:
    body_start = app_text.find("{", start_idx) + 1
    # Count braces to find the end
    braces = 1
    body_end = body_start
    while braces > 0 and body_end < len(app_text):
        if app_text[body_end] == '{': braces += 1
        elif app_text[body_end] == '}': braces -= 1
        body_end += 1
    
    body = app_text[body_start:body_end-1]
    
    wrapped = new_body.replace("{BODY}", body)
    
    app_text = app_text[:body_start] + wrapped + app_text[body_end-1:]
    
    with open("docs/assets/app.js", "w", encoding="utf-8") as f:
        f.write(app_text)
    print("Injected try-catch")
else:
    print("Function not found")
