"""
Generador del dashboard HTML - Model oïdi Son Nadal
====================================================
Llegeix data/historial.csv i genera docs/index.html
amb gràfiques interactives de T, HR, pluja i UI acumulades.

S'executa automàticament al final del workflow de GitHub Actions.
El fitxer resultant es publica via GitHub Pages.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

CSV_HISTORIAL  = "data/historial.csv"
HTML_SORTIDA   = "docs/index.html"

def carregar_dades() -> pd.DataFrame:
    df = pd.read_csv(CSV_HISTORIAL)
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    # Últims 14 dies per al dashboard
    limit = df["ts"].max() - pd.Timedelta(days=14)
    return df[df["ts"] >= limit].copy()

def generar_html(df: pd.DataFrame) -> str:
    # Prepara les sèries per a les gràfiques
    labels     = df["ts"].dt.strftime("%d/%m %H:%M").tolist()
    temps      = pd.to_numeric(df["temperatura_c"],  errors="coerce").round(1).tolist()
    humitat    = pd.to_numeric(df["humitat_pct"],    errors="coerce").round(1).tolist()
    pluja      = pd.to_numeric(df["precipitacio_mm"],errors="coerce").round(1).tolist()
    ui_hora    = pd.to_numeric(df.get("ui_horaria",    pd.Series([0]*len(df))), errors="coerce").round(1).tolist()
    ui_acc     = pd.to_numeric(df.get("ui_acumulades", pd.Series([0]*len(df))), errors="coerce").round(1).tolist()
    risc_col   = df.get("risc_gubler", pd.Series(["baix"]*len(df))).tolist()
    reinicis   = pd.to_numeric(df.get("reinici_ui", pd.Series([0]*len(df))), errors="coerce").tolist()

    # KPIs actuals
    ultima = df.iloc[-1]
    t_act  = pd.to_numeric(ultima.get("temperatura_c"), errors="coerce")
    hr_act = pd.to_numeric(ultima.get("humitat_pct"),   errors="coerce")
    ui_act = pd.to_numeric(ultima.get("ui_acumulades"), errors="coerce")
    risc   = ultima.get("risc_gubler", "baix")
    ts_act = ultima["ts"].strftime("%d/%m/%Y %H:%M")

    risc_color = {
        "baix":     "#22c55e",
        "moderat":  "#f59e0b",
        "alt":      "#ef4444",
        "molt alt": "#7c3aed",
    }.get(risc, "#6b7280")

    ui_pct = min(100, (ui_act / 150) * 100) if not pd.isna(ui_act) else 0

    # Colors per als punts de la gràfica de risc
    risc_colors = []
    for r in risc_col:
        risc_colors.append({
            "baix":     "rgba(34,197,94,0.8)",
            "moderat":  "rgba(245,158,11,0.8)",
            "alt":      "rgba(239,68,68,0.8)",
            "molt alt": "rgba(124,58,237,0.8)",
        }.get(r, "rgba(107,114,128,0.5)"))

    # Reinicis per marcar a la gràfica
    reinici_points = [{"x": labels[i], "y": ui_acc[i]} for i, r in enumerate(reinicis) if r == 1]

    data_js = json.dumps({
        "labels":        labels,
        "temps":         temps,
        "humitat":       humitat,
        "pluja":         pluja,
        "ui_hora":       ui_hora,
        "ui_acc":        ui_acc,
        "risc_colors":   risc_colors,
        "reinici_points": reinici_points,
    })

    return f"""<!DOCTYPE html>
<html lang="ca">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Oïdi Vid · Son Nadal</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    :root{{
      --verd:#16a34a; --ambre:#d97706; --vermell:#dc2626; --violeta:#7c3aed;
      --bg:#0f1117; --surface:#1a1d27; --border:#2a2d3a;
      --text:#e8eaf0; --muted:#6b7280; --accent:#3b82f6;
    }}
    body{{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;
          font-size:14px;line-height:1.5;padding:16px;max-width:1100px;margin:0 auto}}
    h1{{font-size:20px;font-weight:600;letter-spacing:-.3px;color:#fff}}
    .sub{{color:var(--muted);font-size:12px;margin-top:2px}}
    header{{display:flex;justify-content:space-between;align-items:flex-start;
            padding-bottom:20px;border-bottom:1px solid var(--border);margin-bottom:20px}}
    .badge{{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
            border-radius:20px;font-size:12px;font-weight:500;border:1px solid currentColor}}
    .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}}
    .kpi{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px}}
    .kpi-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}}
    .kpi-val{{font-size:26px;font-weight:600;color:#fff;line-height:1}}
    .kpi-unit{{font-size:13px;color:var(--muted);margin-left:2px}}
    .ui-bar-outer{{background:var(--border);border-radius:4px;height:6px;margin-top:8px;overflow:hidden}}
    .ui-bar-inner{{height:100%;border-radius:4px;transition:width .5s}}
    .chart-card{{background:var(--surface);border:1px solid var(--border);
                 border-radius:10px;padding:16px;margin-bottom:16px}}
    .chart-title{{font-size:13px;font-weight:500;color:var(--muted);
                  text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}}
    canvas{{max-height:200px}}
    .legend{{display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;font-size:11px;color:var(--muted)}}
    .legend-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}}
    .llindars{{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;font-size:11px}}
    .ll{{padding:2px 8px;border-radius:4px;border:1px solid}}
    footer{{color:var(--muted);font-size:11px;text-align:center;
            margin-top:24px;padding-top:16px;border-top:1px solid var(--border)}}
    @media(max-width:600px){{canvas{{max-height:160px}}}}
  </style>
</head>
<body>

<header>
  <div>
    <h1>Oïdi de la vid · Son Nadal</h1>
    <div class="sub">Felanitx, Mallorca · Model Gubler · Últims 14 dies</div>
  </div>
  <div>
    <span class="badge" style="color:{risc_color};border-color:{risc_color}">
      ● {risc.upper()}
    </span>
    <div class="sub" style="text-align:right;margin-top:4px">{ts_act}</div>
  </div>
</header>

<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-label">Temperatura</div>
    <div class="kpi-val">{t_act:.1f}<span class="kpi-unit">°C</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Humitat relativa</div>
    <div class="kpi-val">{hr_act:.0f}<span class="kpi-unit">%</span></div>
  </div>
  <div class="kpi">
    <div class="kpi-label">UI acumulades</div>
    <div class="kpi-val">{ui_act:.0f}<span class="kpi-unit">UI</span></div>
    <div class="ui-bar-outer">
      <div class="ui-bar-inner" style="width:{ui_pct:.0f}%;background:{risc_color}"></div>
    </div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Risc Gubler</div>
    <div class="kpi-val" style="font-size:18px;color:{risc_color}">{risc.upper()}</div>
    <div class="sub" style="margin-top:4px">Llindar alt: 100 UI</div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Temperatura i humitat</div>
  <canvas id="chart-th"></canvas>
</div>

<div class="chart-card">
  <div class="chart-title">UI acumulades (model Gubler)</div>
  <canvas id="chart-ui"></canvas>
  <div class="llindars">
    <span class="ll" style="color:#22c55e;border-color:#22c55e">Baix &lt;50</span>
    <span class="ll" style="color:#f59e0b;border-color:#f59e0b">Moderat ≥50</span>
    <span class="ll" style="color:#ef4444;border-color:#ef4444">Alt ≥100</span>
    <span class="ll" style="color:#7c3aed;border-color:#7c3aed">Molt alt ≥150</span>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Precipitació (mm)</div>
  <canvas id="chart-pluja"></canvas>
</div>

<footer>
  Son Nadal (RC0039468) · 39.5146, 3.15405 · 
  Actualitzat: {datetime.now().strftime("%d/%m/%Y %H:%M")} · 
  Model: Gubler (1995) adaptat per a Uncinula necator
</footer>

<script>
const D = {data_js};

const cfgBase = {{
  responsive:true, maintainAspectRatio:true,
  plugins:{{legend:{{display:false}}}},
  scales:{{
    x:{{ticks:{{color:'#6b7280',maxTicksLimit:8,font:{{size:10}}}},
        grid:{{color:'rgba(255,255,255,.04)'}}}},
    y:{{ticks:{{color:'#6b7280',font:{{size:10}}}},
        grid:{{color:'rgba(255,255,255,.06)'}}}}
  }}
}};

// Gràfica T i HR
new Chart(document.getElementById('chart-th'), {{
  type:'line',
  data:{{
    labels: D.labels,
    datasets:[
      {{label:'T (°C)', data:D.temps, borderColor:'#f97316',
        backgroundColor:'rgba(249,115,22,.1)', borderWidth:1.5,
        pointRadius:0, fill:true, tension:.3, yAxisID:'yT'}},
      {{label:'HR (%)', data:D.humitat, borderColor:'#38bdf8',
        backgroundColor:'rgba(56,189,248,.08)', borderWidth:1.5,
        pointRadius:0, fill:false, tension:.3, yAxisID:'yHR'}}
    ]
  }},
  options:{{...cfgBase,
    plugins:{{...cfgBase.plugins,
      legend:{{display:true, labels:{{color:'#9ca3af',font:{{size:11}}}}}},
      annotation:{{annotations:{{
        hr40:{{type:'line',yScaleID:'yHR',yMin:40,yMax:40,
               borderColor:'rgba(56,189,248,.3)',borderWidth:1,
               borderDash:[4,4],label:{{content:'HR 40%',display:true,
               color:'rgba(56,189,248,.5)',font:{{size:9}}}}}},
        hr70:{{type:'line',yScaleID:'yHR',yMin:70,yMax:70,
               borderColor:'rgba(56,189,248,.5)',borderWidth:1,
               borderDash:[4,4],label:{{content:'HR 70%',display:true,
               color:'rgba(56,189,248,.7)',font:{{size:9}}}}}}
      }}}}
    }},
    scales:{{
      x:cfgBase.scales.x,
      yT:{{...cfgBase.scales.y, position:'left',
           title:{{display:true,text:'°C',color:'#f97316',font:{{size:10}}}}}},
      yHR:{{...cfgBase.scales.y, position:'right', min:0, max:100,
            title:{{display:true,text:'%',color:'#38bdf8',font:{{size:10}}}},
            grid:{{drawOnChartArea:false}}}}
    }}
  }}
}});

// Gràfica UI acumulades
const uiColors = D.ui_acc.map(v =>
  v >= 150 ? 'rgba(124,58,237,.8)' :
  v >= 100 ? 'rgba(239,68,68,.8)' :
  v >= 50  ? 'rgba(245,158,11,.8)' :
             'rgba(34,197,94,.8)'
);

new Chart(document.getElementById('chart-ui'), {{
  type:'line',
  data:{{
    labels: D.labels,
    datasets:[
      {{label:'UI acumulades', data:D.ui_acc,
        borderColor:'#a78bfa', borderWidth:2,
        pointRadius:2, pointBackgroundColor:uiColors,
        fill:true, backgroundColor:'rgba(167,139,250,.08)', tension:.2}},
      {{label:'UI horàries', data:D.ui_hora, type:'bar',
        backgroundColor:'rgba(167,139,250,.25)',
        borderColor:'rgba(167,139,250,.5)', borderWidth:1,
        yAxisID:'yUH'}}
    ]
  }},
  options:{{...cfgBase,
    plugins:{{...cfgBase.plugins,
      legend:{{display:true, labels:{{color:'#9ca3af',font:{{size:11}}}}}},
      annotation:{{annotations:{{
        ll50: {{type:'line',yMin:50,yMax:50,borderColor:'rgba(245,158,11,.4)',
                borderWidth:1,borderDash:[4,4]}},
        ll100:{{type:'line',yMin:100,yMax:100,borderColor:'rgba(239,68,68,.5)',
                borderWidth:1,borderDash:[4,4]}},
        ll150:{{type:'line',yMin:150,yMax:150,borderColor:'rgba(124,58,237,.5)',
                borderWidth:1.5,borderDash:[4,4]}}
      }}}}
    }},
    scales:{{
      x:cfgBase.scales.x,
      y:{{...cfgBase.scales.y, min:0,
          title:{{display:true,text:'UI acum.',color:'#a78bfa',font:{{size:10}}}}}},
      yUH:{{...cfgBase.scales.y, position:'right', min:0,
            title:{{display:true,text:'UI/h',color:'rgba(167,139,250,.6)',font:{{size:10}}}},
            grid:{{drawOnChartArea:false}}}}
    }}
  }}
}});

// Gràfica pluja
new Chart(document.getElementById('chart-pluja'), {{
  type:'bar',
  data:{{
    labels: D.labels,
    datasets:[{{
      label:'Pluja (mm)', data:D.pluja,
      backgroundColor:'rgba(56,189,248,.5)',
      borderColor:'rgba(56,189,248,.8)', borderWidth:1
    }}]
  }},
  options:{{...cfgBase,
    scales:{{
      x:cfgBase.scales.x,
      y:{{...cfgBase.scales.y, min:0,
          title:{{display:true,text:'mm',color:'#38bdf8',font:{{size:10}}}}}}
    }}
  }}
}});
</script>
</body>
</html>"""

def main():
    if not os.path.exists(CSV_HISTORIAL):
        print("⚠ No s'ha trobat historial.csv — executa primer el collector")
        raise SystemExit(1)

    df = carregar_dades()
    if df.empty:
        print("⚠ Historial buit")
        raise SystemExit(1)

    os.makedirs("docs", exist_ok=True)
    html = generar_html(df)
    with open(HTML_SORTIDA, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Dashboard generat: {HTML_SORTIDA}")
    print(f"  {len(df)} registres | {df['ts'].min().strftime('%d/%m')} → {df['ts'].max().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
