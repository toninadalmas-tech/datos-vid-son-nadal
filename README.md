# Model de Malalties de la Vid · Estació Son Nadal (Felanitx)

Recollida automàtica de dades meteorològiques horàries de l'estació CAIB **Son Nadal** (Felanitx, Mallorca), ampliada amb dades d'**Open-Meteo**, per construir models predictius de les principals malalties de la vinya (Oïdi, Mildiu, Botritis, Black Rot).

---

## Estructura del repositori

El sistema consta de 4 etapes automatitzades mitjançant GitHub Actions, orquestrades per `main.py`:

```
├── main.py                       ← Orquestrador principal
├── son_nadal_collector.py        ← (1) Scraping dades de l'estació CAIB
├── fetch_openmeteo.py            ← (2) Dades complementàries (Radiació, UV, ET0)
├── oidi_collector.py             ← (3) Índex Gubler-Thomas
├── mildiu_collector.py           ← (4) Regla 3-10 + esporulació secundària
├── botritis_collector.py         ← (5) Model de Broome
├── blackrot_collector.py         ← (6) Model de Spotts
├── generate_dashboard.py         ← (7) Generació del Dashboard HTML (estàtic)
├── meteo_utils.py                ← Durades reals i ratxes (compartit pels models)
├── .github/workflows/
│   └── recollida_diaria.yml      ← Automatització GitHub Actions
├── data/
│   ├── historial.csv             ← Historial climàtic i models d'oïdi/botritis/black rot
│   └── mildiu_historial.csv      ← Dades ampliades del model de mildiu
├── tractaments.json              ← Tractaments aplicats (editable des del dashboard)
├── observacions.json             ← Observacions de camp (obren el cicle secundari)
├── fase_fenologica.json          ← Fase per varietat, amb overrides manuals
├── parceles.json                 ← Geometria de les parcel·les per al mapa
├── docs/                         ← Dashboard i fitxers web
│   ├── assets/                   ← Estils CSS i scripts JS
│   └── *.html                    ← Pàgines generades del dashboard
└── README.md
```

> Els comptadors d'hores (fulla molla, ratxes tèrmiques, graus-dia) treballen amb
> **durades reals** via `meteo_utils.py`: si hi ha un forat a les dades, la ratxa
> es talla en comptes d'unir dos episodis separats.

---

## Models Predictius Implementats

*   **Oïdi (*Erysiphe necator*):** Índex de risc de **Gubler-Thomas (UC Davis)**, escala 0-100, dirigit només per temperatura: +20 punts per cada dia amb ≥6 h contínues entre 21,1 i 29,4 °C, −10 si no s'assoleix el bloc i −10 si es toquen els 35 °C durant 15 min. L'epidèmia no arrenca fins a 3 dies favorables consecutius. La humitat relativa no hi intervé: el fong és xeròfit i no necessita aigua lliure.

    Les ratxes tèrmiques es compten de forma **contínua i no per dia natural**. És una desviació deliberada del model original: a Mallorca la finestra favorable és nocturna (la majoria de ratxes van de les ~21 h a les ~9 h) i tallar-les a mitjanit les partiria pel mig.

    Al damunt s'hi aplica la **resistència ontogènica** del raïm (Gadoury *et al.*, 2003): a partir de baies de 3-4 mm (BBCH 75) el gra és pràcticament immune. Per això el dashboard separa **risc de raïm** i **risc de fulla** — les fulles joves són susceptibles tota la campanya i és on es formen els cleistotecis que hivernen.

*   **Mildiu (*Plasmopara viticola*):** Infecció primària per la **regla dels tres deus** (Baldacci, 1947): brots >10 cm, T mitjana >10 °C i un episodi de pluja ≥10 mm en 24-48 h. La infecció secundària segueix un model mecanístic d'esporulació: foscor, aigua lliure i T entre 12 i 29 °C fins a acumular 50 °C·h.

    El model manté una **porta**: sense infecció primària incubada no es declaren secundàries, perquè els esporangis els produeixen lesions ja establertes. La porta també s'obre registrant una observació de camp, ja que l'inòcul pot arribar de vinyes veïnes.

*   **Botritis:** model de **Broome (1995)**, equació logística sobre durada d'humectació i temperatura mitjana de l'episodi.
*   **Black Rot:** model de **Spotts (1977)**: hores de fulla molla necessàries segons la temperatura (6 h a 20-26 °C, 24 h a 10-15 °C).

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
