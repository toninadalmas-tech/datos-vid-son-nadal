# Model de Malalties de la Vid · Estació Son Nadal (Felanitx)

Recollida automàtica de dades meteorològiques horàries de l'estació CAIB **Son Nadal** (Felanitx, Mallorca), ampliada amb dades d'**Open-Meteo**, per construir models predictius de les principals malalties de la vinya (Oïdi, Mildiu, Botritis, Black Rot).

---

## Estructura del repositori

El sistema consta de 4 etapes automatitzades mitjançant GitHub Actions, orquestrades per `main.py`:

```
├── main.py                       ← Orquestrador principal
├── son_nadal_collector.py        ← (1) Scraping dades de l'estació CAIB
├── fetch_openmeteo.py            ← (2) Dades complementàries (Radiació, UV, Evapotranspiració)
├── mildiu_collector.py           ← (3) Càlcul del model predictiu Mildiu
├── generate_dashboard.py         ← (4) Generació del Dashboard HTML (estàtic)
├── .github/workflows/
│   └── recollida_diaria.yml      ← Automatització GitHub Actions
├── data/
│   ├── historial.csv             ← Historial climàtic complet i model Oïdi
│   └── mildiu_historial.csv      ← Dades ampliades del model Mildiu
├── docs/                         ← Dashboard i fitxers web
│   ├── assets/                   ← Estils CSS i scripts JS
│   └── *.html                    ← Pàgines generades del dashboard
└── README.md
```

---

## Models Predictius Implementats

*   **Oïdi (*Uncinula necator*):** S'utilitza el model de **Gubler (1995)** adaptat, calculant Unitats d'Infecció (UI) basades en la temperatura i humitat, amb reinicis per pluja (>2mm) o onades de calor (>35°C). Incorpora ajustos de resistència ontogènica segons la fase fenològica (Kast).
*   **Mildiu (*Plasmopara viticola*):** Es combina el model de regles **3x10 de Goidanich** (infecció primària) i un model **EPI** basat en temperatura, humitat alta perllongada i pluja (infecció secundària i període d'incubació basat en Graus-Dia).
*   **Botritis i Black Rot:** Seguiment actiu d'indicadors meteorològics, hores de fred i recomanacions basades en llindars bàsics i fenologia.

---

## Com posar-ho en marxa en el teu propi repositori

1. **Clona o Copia** aquest repositori al teu propi espai de GitHub.
2. Comprova que a la pestanya **Actions**, els Workflows estiguin activats (et pot demanar autorització si has fet un fork).
3. L'acció "Recollida diària Son Nadal" s'executarà **cada dia a les 07:00 del matí** i penjarà els canvis al directori `docs/` i `data/` automàticament.
4. **Habilitar GitHub Pages:**
   * Ves a "Settings" > "Pages".
   * A "Source", selecciona la branca `main` i la carpeta `/docs`.
   * Guarda i el teu dashboard estarà publicat web gratuïtament.
5. **Configurar registres manuals (Tractaments):** Al dashboard web, pots inserir tractaments manuals si configures un "Personal Access Token" de Github (amb permisos de contingut) directament a la configuració del navegador.
