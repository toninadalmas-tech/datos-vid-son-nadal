import re

with open("generate_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

# Lògica JS per Botritis
js_botritis = """
let chartModel;
function buildCharts(start, end) {
  let L = ALL.labels.slice(start, end);
  let R = ALL.risc_botritis_pct.slice(start, end);
  
  if (chartModel) chartModel.destroy();
  
  const ctx = document.getElementById('chartModel');
  if(!ctx) return;
  
  chartModel = new Chart(ctx, {
    type: 'line',
    data: {
      labels: L,
      datasets: [{
        label: 'Risc Botritis (%)',
        data: R,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245,158,11,0.2)',
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 100 }
      }
    }
  });
}
"""

js_blackrot = """
let chartModel;
function buildCharts(start, end) {
  let L = ALL.labels.slice(start, end);
  // Spotts model returns string: 'baix', 'moderat', 'alt'
  // We map it to numeric values to plot
  let R_num = ALL.risc_blackrot.slice(start, end).map(r => r === 'alt' ? 3 : r === 'moderat' ? 2 : 1);
  let colors = R_num.map(r => r === 3 ? 'rgba(239,68,68,0.8)' : r === 2 ? 'rgba(245,158,11,0.8)' : 'rgba(34,197,94,0.5)');
  
  if (chartModel) chartModel.destroy();
  
  const ctx = document.getElementById('chartModel');
  if(!ctx) return;
  
  chartModel = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: L,
      datasets: [{
        label: 'Risc Black Rot',
        data: R_num,
        backgroundColor: colors
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { 
          min: 0, 
          max: 3, 
          ticks: { callback: v => ['', 'Baix', 'Moderat', 'Alt'][v] || v }
        }
      }
    }
  });
}
"""

# Replace in botritis
def repl_botritis(m):
    return m.group(0).replace("if (typeof setFilter !== 'undefined') { setFilter('7d'); }", js_botritis + "\n    if (typeof setFilter !== 'undefined') { setFilter('7d'); }")

text = re.sub(r'def generar_botritis.*?return "\\n"\.join\(parts\)', repl_botritis, text, flags=re.DOTALL)

# Replace in blackrot
def repl_blackrot(m):
    return m.group(0).replace("if (typeof setFilter !== 'undefined') { setFilter('7d'); }", js_blackrot + "\n    if (typeof setFilter !== 'undefined') { setFilter('7d'); }")

text = re.sub(r'def generar_blackrot.*?return "\\n"\.join\(parts\)', repl_blackrot, text, flags=re.DOTALL)

with open("generate_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)

print("JS charts injected.")
