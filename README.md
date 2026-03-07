# Ottoman Anatolia Schooling — Historical GIS Dataset

A kaza-level historical GIS dataset on Protestant missionary activity and
Ottoman state education in Ottoman Turkey (Eastern Thrace and Anatolia),
c. 1880–1914. Compiled for a doctoral dissertation at McGill University
(Amasyalı 2020), the repository bundles boundary shapefiles, point data
for missionary institutions, the 1881/93 Ottoman census demographics,
Ottoman school censuses, and an interactive Leaflet web map — all
deployable via GitHub Pages.

**[→ Open interactive map](https://emreamasyali.github.io/ottoman-anatolia-schooling-hgis/web/)**

---

## Table of Contents

1. [Overview](#overview)
2. [Repository structure](#repository-structure)
3. [Data sources](#data-sources)
4. [Coding decisions](#coding-decisions)
5. [Variable descriptions](#variable-descriptions)
6. [Download links](#download-links)
7. [Interactive map](#interactive-map)
8. [Replication](#replication)
9. [Citation](#citation)
10. [License](#license)

---

## Overview

This dataset was constructed for *The Fight for Eden: A Mixed-Methods Analysis
of Historical Educational Competition and its Legacies* (Amasyalı 2020), a
doctoral dissertation at McGill University. Two published articles draw on
the data: Amasyalı (2022a) in *European Journal of Sociology* and Amasyalı
(2022b) in *Social Science History*.

The dataset covers **335 kazas** (sub-provincial districts) across the
Anatolian vilayets and Eastern Thrace of the late Ottoman Empire. The unit
of observation is the kaza as it existed c. 1899–1914. It combines three
categories of information:

- **Administrative boundaries and census demographics.** Manually digitised
  kaza polygons linked to the 1881/93 Ottoman population census, which
  records population by sex and ethno-religious community (millet) at the
  district level.
- **Protestant missionary institutions.** Geocoded locations of 420 ABCFM
  main stations and outstations operational in Ottoman Turkey between 1870
  and 1914, compiled from archival sources at Houghton Library (Harvard)
  and ARIT (Istanbul).
- **Ottoman state schooling.** School counts from Ottoman education
  yearbooks (*Maarif Salnamesi*) for two cross-sections: 1876 (male
  rüşdiye only) and 1902–08 (male and female ibtidai and rüşdiye).

Key data components:

| Component | Records | Period | Format |
|---|---|---|---|
| Kaza boundary polygons | 332 kazas | c. 1899–1914 | Shapefile, GeoJSON |
| Missionary stations & outstations | 420 locations | 1870–1914 | Shapefile, GeoJSON |
| Main ABCFM stations | 10 locations | c. 1900 | Shapefile, GeoJSON |
| 1881/93 census demographics | 335 kazas | 1881/82–1893 | Stata, CSV |
| Ottoman school census | 1,000 kaza-years | 1876, 1902–08 | Stata, CSV |

---

## Repository structure

```
ottoman-anatolia-schooling-hgis/
│
├── data/
│   ├── raw/
│   │   ├── shapefiles/
│   │   │   ├── boundaries/      Original kaza boundary shapefiles (.shp/.dbf/.prj/…)
│   │   │   └── points/          Original point shapefiles for all location data
│   │   ├── stata/               Original Stata .dta files (master, census, schools)
│   │   └── missionary_locations_raw.csv   Raw, unmatched missionary location list
│   │
│   └── derived/
│       ├── geojson/             Web-ready GeoJSON (WGS-84, EPSG:4326)
│       ├── csv/                 UTF-8 CSV exports of all Stata files
│       └── layer_index.json     Machine-readable index of all derived files
│
├── docs/
│   └── codebook.md              Full variable-level codebook (generated separately)
│
├── scripts/
│   └── convert_data.py          SHP → GeoJSON and DTA → CSV conversion script
│
├── web/
│   ├── index.html               Interactive Leaflet map (GitHub Pages entry point)
│   ├── js/map.js                Map application logic
│   └── css/style.css            Map styling
│
└── README.md
```

---

## Data sources

### Kaza boundaries

The Ottoman census of 1881/93 recorded population at three spatial levels:
vilayet (province), sanjak (sub-province), and kaza (district). Because the
first two are too expansive to produce meaningful subnational variation, the
kaza is adopted as the unit of observation.

To map the kazas captured in the 1893 census onto a spatial framework, the
**1899 administrative and political map of the Ottoman Empire by R. Huber**
was georeferenced and fitted to a modified TUREF / LAEA Europe projection.
Based on this map, the administrative boundaries of all kazas within the 1893
census were **manually traced in ArcGIS**, producing 332 boundary polygons.
Each polygon was assigned a unique **RTENO** identifier. Between 1893 and
1899, some kazas were disaggregated or merged into other units; for these
cases, provincial yearbooks (*vilayet salnameleri*) were consulted to
reconstruct boundaries as they appeared in 1893.

To link historical kazas to modern Turkish districts (*ilçe*, ~957 units),
the **historical gazetteer of the Ottoman Empire compiled by Sezen (2017)**
was used. This gazetteer indexes approximately 120,000 localities from
the reign of Suleiman the Magnificent onward and documents their changing
administrative affiliations. Because Ottoman kazas were generally larger
than modern Turkish districts, most cases involve multiple modern districts
mapping to a single historical kaza. For modern districts that post-date
the Ottoman period and therefore lack a gazetteer entry, the geographic
coordinates of the district capital were used as an approximation.

Additional sources cross-referenced for boundary verification include:

- Cuinet, Vital. *La Turquie d'Asie* (4 vols., 1890–1894), for
  administrative descriptions of individual kazas.
- Stanford's Ottoman spatial data published through the *World Historical
  Gazetteer* project (cross-referenced for vilayet outlines).

### ABCFM missionary stations

The American Board of Commissioners for Foreign Missions (ABCFM) operated
the dominant Protestant missionary network in Ottoman Turkey from 1820
onward. The dataset contains the geocoded locations of **420 mission main
stations and outstations** within the borders of modern Turkey, covering
the period 1870–1914. Coordinates were determined by matching station names
from archival publications to modern or historical localities, achieving a
97 percent match rate. Where place names had changed or disappeared — a
common outcome of post-Ottoman toponymical engineering — multiple gazetteers
and reference works were triangulated (Hewsen and Salvatico 2001; Kévorkian
and Paboudjian 2012; Nişanyan 2010).

Station coordinates were geocoded from:

- ABCFM *Annual Reports*, 1860–1914 (digitised volumes held by the Houghton
  Library, Harvard University).
- ABCFM correspondence and field reports (*ABC 16*, Houghton Library
  archives).
- The private library and archive of the Amerikan Bord Heyeti at the
  American Research Institute in Turkey (ARIT), Beylerbeyi, Istanbul.
- Data on Protestant missionary schools drawn from Alan (2015).

Each location record includes the station name, Ottoman administrative
hierarchy (vilayet / sanjak / kaza), modern place name, mission name,
and classification (main station vs. outstation vs. dependent congregation).

**Field `Out-Station` = 1** indicates an outstation (a secondary location
served from a main station but without a resident missionary).
**Field `Main Station` = 1** indicates a principal station with a resident
missionary household.

### 1881/93 Ottoman census (*Nüfus-i Umumi*)

Population counts by ethno-religious community were digitised from:

- **Karpat, Kemal H.** *Ottoman Population, 1830–1914: Demographic and
  Social Characteristics*. University of Wisconsin Press, 1985.

The census was conducted 1881/82–1893 and published in 1893. It tabulates
population by sex and by the Ottoman millet categories: Muslims, Greeks,
Armenians, Bulgarians, Catholics, Jews, Protestants, Latins, Monophysites,
Non-Muslim Gypsies, and Foreign Citizens. **These categories reflect Ottoman
administrative classification, not ethnic self-identification**, and the
census is known to undercount non-Muslim populations (see Karpat 1985,
ch. 2 for a methodological discussion).

### Ottoman school census (*Maarif Salnamesi*)

School counts were digitised from the Ottoman education yearbooks for two
cross-sections:

- **1876**: Initial survey of Ottoman state schools (rüşdiye level, male
  only).
- **1902–1908**: Expanded enumeration covering male and female ibtidai
  (primary) and rüşdiye (secondary) schools, compiled from the annual
  editions held at the Bibliothèque nationale de France and the ISAM
  library, Istanbul.

---

## Coding decisions

### Projection

All boundary and point data were originally digitised in **EPSG:3857**
(Web Mercator / Pseudo-Mercator) inside ArcGIS. The conversion script
reprojects all layers to **EPSG:4326 (WGS-84)** before GeoJSON export,
which is the standard coordinate system for web mapping.

### Kaza identifier (`RTENO` / `kazcode`)

Each kaza is assigned a unique numeric identifier. Two codes appear across
the dataset:
- **RTENO** — the internal ArcGIS identifier assigned during digitisation.
- **kazcode** — a harmonised join key used in the tabular datasets. The
  `census_gis_merged` table links census data to boundaries via `kazcode`.

The `.do` files in `Statistical Analysis/Data/GIS Data/` document the
manual merging process for the ~30 kazas where name-based matching required
hand-inspection (`manual_merge.dta`).

### Temporal scope

The kaza boundaries, missionary station counts, and census demographics all
refer to the late Hamidian / early Unionist period (roughly 1893–1914). The
school census provides two cross-sections (1876 and 1902–08), enabling
before-and-after comparisons of state schooling expansion. No attempt has
been made to model boundary changes between censuses; the 1881/93 and 1914
administrative geographies are treated as equivalent for the purpose of
analysis.

### Incomplete vilayet coverage

The digitised kaza boundary set covers the core Anatolian vilayets and
Eastern Thrace. Several peripheral regions are partially represented
or absent:
- **Halep (Aleppo) Vilayet** — southern kazas only.
- **Edirne Vilayet** — included but treated as outside the Anatolian core
  in the main regression sample.
- **Kars** — included as a special administrative zone but excluded from
  the main analytical sample as it was under Russian jurisdiction
  (1878–1918) during the relevant period.

---

## Variable descriptions

### `master_dataset.csv` / `master_dataset.dta`
Master merged dataset (335 rows, one per kaza).

| Variable | Description |
|---|---|
| `NameofKaza` | Ottoman kaza name (transliterated) |
| `kazcode` | Unique kaza identifier (join key) |
| `NameofSanjak` | Ottoman sanjak (sub-province) name |
| `NameofVilayet` | Ottoman vilayet (province) name |
| `Muslims_Female` / `Muslims_Male` | Muslim population by sex (1881/93 census) |
| `Greeks_Female` / `Greeks_Male` | Greek Orthodox population by sex |
| `Armenians_Female` / `Armenians_Male` | Armenian population by sex |
| `Bulgarians_Female` / `Bulgarians_Male` | Bulgarian Orthodox population by sex |
| `Catholics_Female` / `Catholics_Male` | Catholic population by sex |
| `Jews_Female` / `Jews_Male` | Jewish population by sex |
| `Protestants_Female` / `Protestants_Male` | Protestant population by sex |
| `Latins_Female` / `Latins_Male` | Latin Catholic population by sex |
| `Monophysites_Female` / `Monophysites_Male` | Monophysite (Syriac/Assyrian) population by sex |
| `NonMuslimGypsies_Female` / `NonMuslimGypsies_Male` | Non-Muslim Roma population by sex |
| `ForeignCitizens_Female` / `ForeignCitizens_Male` | Foreign nationals by sex |
| `Total_Muslim` | Total Muslim population |
| `Total_Christian` | Total Christian population (all denominations) |
| `Total_NonMuslim` | Total non-Muslim population |
| `Total_Armenian` | Total Armenian population |
| `Christian_Muslim_Ratio` | Ratio of Christians to Muslims |
| `Armenian_Muslim_Ratio` | Ratio of Armenians to Muslims |
| `ArmenianShare` | Armenians / Grand Total |
| `ChristianShare` | Total Christians / Grand Total |
| `Total_Female` / `Total_Male` | Total population by sex |
| `GrandTotal` | Total population all groups |
| `Source` | Source note for census tabulation |
| `CentralKazaDummy` | 1 if kaza contains the vilayet capital |

### `census_1881.csv` / `census_1881.dta`
Census table with full spatial join (335 rows). Contains all columns from
`master_dataset` plus spatial join metadata (`OBJECTID`, `Join_Count`,
`TARGET_FID`) and the raw kaza name from the GIS join (`kaza`).

### `schools.csv` / `schools.dta`
Ottoman school census (1,000 rows, kaza × year structure).

| Variable | Description |
|---|---|
| `NameofKaza` | Kaza name |
| `kazcode` | Join key |
| `MaleIptidaiSchoolsDistributio` | Male ibtidai (primary) school count |
| `FemaleIbtidaiSchools1902190` | Female ibtidai school count (1902–08) |
| `MaleRusdiyyeSchools1876` | Male rüşdiye (secondary) school count, 1876 |
| `MaleRusdiyyeSchools19021908` | Male rüşdiye school count, 1902–08 |
| `FemaleRusdiyyeSchools190219` | Female rüşdiye school count, 1902–08 |

---

## Download links

All data files are available directly from this repository.

### GeoJSON (web map layers)

| Layer | File | Features |
|---|---|---|
| Kaza boundaries (WGS-84) | [`data/derived/geojson/kazas_boundaries.geojson`](data/derived/geojson/kazas_boundaries.geojson) | 332 polygons |
| Missionary stations | [`data/derived/geojson/missionary_stations.geojson`](data/derived/geojson/missionary_stations.geojson) | 420 points |
| Main missionary stations | [`data/derived/geojson/main_missionary_stations.geojson`](data/derived/geojson/main_missionary_stations.geojson) | 10 points |

### CSV (tabular data)

| Dataset | File | Rows |
|---|---|---|
| Master dataset | [`data/derived/csv/master_dataset.csv`](data/derived/csv/master_dataset.csv) | 335 |
| 1881/93 census | [`data/derived/csv/census_1881.csv`](data/derived/csv/census_1881.csv) | 335 |
| School census | [`data/derived/csv/schools.csv`](data/derived/csv/schools.csv) | 1,000 |

### Stata / .dta

| Dataset | File |
|---|---|
| Master dataset | [`data/raw/stata/master_dataset.dta`](data/raw/stata/master_dataset.dta) |
| 1881/93 census | [`data/raw/stata/census_1881.dta`](data/raw/stata/census_1881.dta) |
| School census | [`data/raw/stata/schools.dta`](data/raw/stata/schools.dta) |

### Shapefiles

| Layer | Folder |
|---|---|
| Kaza boundaries | [`data/raw/shapefiles/boundaries/`](data/raw/shapefiles/boundaries/) |
| All missionary stations | [`data/raw/shapefiles/points/AllStations_Missionary.*`](data/raw/shapefiles/points/) |
| Main stations | [`data/raw/shapefiles/points/Main Stations.*`](data/raw/shapefiles/points/) |

---

## Interactive map

The web map lives in `web/index.html` and is deployable as a static site via
**GitHub Pages**. No server-side code is required; all data files are loaded
client-side via `fetch()`.

### Local preview

```bash
# From the repository root, serve the web/ folder over HTTP
# (required because fetch() needs a server, not file://)
python3 -m http.server 8000
# then open http://localhost:8000/web/
```

### GitHub Pages deployment

1. Push the repository to GitHub.
2. Go to **Settings → Pages → Source** and select the `main` branch, root `/`.
3. The map will be live at
   `https://YOUR_USERNAME.github.io/ottoman-anatolia-schooling-hgis/web/`.

### Map features

- **Choropleth layer** — kaza polygons shaded by Christian population share
  (1881/93 census), from dark blue (< 2%) to pale blue (> 35%).
- **Hover tooltips** — hovering a kaza shows the 1881/93 population breakdown
  in the sidebar stats panel.
- **Click-to-zoom** — clicking a kaza polygon fits the map to that district.
- **Pop-up cards** — clicking any point or polygon opens a detail card.
- **Layer toggles** — each data layer can be independently shown/hidden.
- **Download buttons** — header links to the master CSV and Stata downloads.

---

## Replication

To regenerate all derived files from the raw data:

```bash
# 1. Install dependencies
pip install geopandas pyreadstat pandas

# 2. Run conversion
python3 scripts/convert_data.py

# Outputs written to:
#   data/derived/geojson/*.geojson
#   data/derived/csv/*.csv
#   data/derived/layer_index.json
```

The script is idempotent — running it multiple times produces identical output.

---

## Citation

If you use this dataset in published research, please cite the dataset and
at least one of the publications that use it:

> Amasyalı, Emre. 2020. *Ottoman Anatolia Schooling HGIS Dataset* [Data set].
> McGill University. https://github.com/emreamasyali/ottoman-anatolia-schooling-hgis

### Published articles using this dataset

> Amasyalı, Emre. 2022. "Indigenous Responses to Protestant Missionaries:
> Educational Competition and Economic Development in Ottoman Turkey."
> *European Journal of Sociology / Archives Européennes de Sociologie*
> 63 (1): 39–86.

> Amasyalı, Emre. 2022. "Protestant Missionary Education and the Diffusion
> of Women's Education in Ottoman Turkey: A Historical GIS Analysis."
> *Social Science History* 46 (1): 173–222.

### Dissertation

> Amasyalı, Emre. 2020. *The Fight for Eden: A Mixed-Methods Analysis of
> Historical Educational Competition and its Legacies.* PhD dissertation,
> McGill University.

Primary sources that must also be cited:

- Karpat, Kemal H. *Ottoman Population, 1830–1914: Demographic and Social
  Characteristics*. Madison: University of Wisconsin Press, 1985.
- American Board of Commissioners for Foreign Missions. *Annual Report*.
  Boston: ABCFM, 1860–1914. [Houghton Library, Harvard University]
- Ottoman Ministry of Education. *Maarif Salnamesi* [Education Yearbook].
  Istanbul: Matbaa-i Amire, 1901–1908.

---

## License

**Data**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
You are free to share and adapt the data for any purpose, provided you give
appropriate credit.

**Code** (`scripts/`, `web/`): [MIT License](https://opensource.org/licenses/MIT)

Original boundary digitisation and data compilation by the repository
author. Census data reproduced under scholarly fair use from Karpat (1985).
