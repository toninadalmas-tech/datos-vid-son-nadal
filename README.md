# Model oïdi vid · Estació Son Nadal (Felanitx)

Recollida automàtica de dades meteorològiques horàries de l'estació CAIB
**Son Nadal** (Felanitx, Mallorca) per construir un model predictiu d'oïdi de la vid.

---

## Estructura del repositori

```
├── son_nadal_collector.py        ← script principal
├── .github/workflows/
│   └── recollida_diaria.yml      ← automatització GitHub Actions
├── data/
│   └── historial.csv             ← dades acumulades (es genera sol)
└── README.md
```

---

## Com posar-ho en marxa (15 minuts)

### Pas 1 — Crear el repositori a GitHub

1. Ves a [github.com/new](https://github.com/new)
2. Nom: `oidio-vid-felanitx`  
3. **Privat** (les teves dades, millor privat)
4. Crea el repositori

### Pas 2 — Pujar els fitxers

Tens dues opcions:

**Opció A — Des de la web de GitHub (sense instal·lar res)**
- Ves al teu repositori > "Add file" > "Upload files"
- Puja `son_nadal_collector.py` i `README.md`
- Per crear la carpeta del workflow: "Add file" > "Create new file"  
  → escriu el nom: `.github/workflows/recollida_diaria.yml`  
  → enganxa el contingut del fitxer yml

**Opció B — Amb Git des del terminal**
```bash
git init
git remote add origin https://github.com/EL_TEU_USUARI/oidio-vid-felanitx.git
git add .
git commit -m "primer commit"
git push -u origin main
```

### Pas 3 — Activar les Actions

- Ves a GitHub > el teu repositori > pestanya **Actions**
- Si apareix un avís "Workflows aren't running", clica "Enable workflows"
- Ja està! S'executarà cada dia a les 07:00

### Pas 4 — Provar manualment (recomanat)

- Actions > "Recollida diària Son Nadal" > "Run workflow" > "Run workflow"
- Veuràs el log en temps real
- Si tot va bé, apareixerà `data/historial.csv` al repositori

---

## ⚠ Pas important: trobar l'endpoint CSV real

El script intenta diverses URLs automàticament, però si no en troba cap,
cal fer-ho manualment **una sola vegada**:

1. Obre el navegador i ves a:  
   `https://www.estacionsclimatiquesiibb.cat/weatherstationdataview/117202`
2. Prem **F12** (eines de desenvolupador) → pestanya **Network**
3. Selecciona l'estació "Felanitx - Son Nadal", sensor "Temperatura", prem **Enviar**
4. Quan aparegui la gràfica, clica el **botó CSV** de la pàgina
5. A la llista de peticions de Network, cerca la que acaba en `.csv` o `export`
6. **Copia la URL** d'aquella petició
7. Edita `son_nadal_collector.py` i afegeix-la al principi de `ENDPOINTS_CSV`

---

## Dades generades (`data/historial.csv`)

| Columna | Descripció |
|---|---|
| `timestamp` | Data i hora de la mesura |
| `temperatura_c` | Temperatura (°C) |
| `humitat_pct` | Humitat relativa (%) |
| `precipitacio_mm` | Precipitació (mm) |
| `hora_favorable_oidio` | 1 si les condicions són favorables per a infecció |
| `risc_infeccio` | `baix` / `moderat` / `alt` / `no favorable` |

### Lògica del risc (model Kast & Bleyer simplificat)

| Risc | Temperatura | HR |
|---|---|---|
| **Alt** | 20–27°C | ≥ 70% |
| **Moderat** | 15–35°C | ≥ 50% |
| **Baix** | 15–35°C | ≥ 40% |
| No favorable | fora de rang | — |

---

## Proper pas

Un cop acumulades 4–6 setmanes de dades, podem:
- Calcular unitats d'infecció acumulades (model Gubler complet)
- Comparar amb observacions de camp
- Construir alertes de tractament
