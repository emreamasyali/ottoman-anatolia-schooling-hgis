# Ottoman Anatolia Schooling — Historical GIS Dataset

A kaza-level historical GIS dataset on Protestant missionary activity and
schooling in Ottoman Anatolia, c. 1880–1914, compiled for a doctoral thesis
project at McGill University. The repository bundles boundary shapefiles,
point data for missionary institutions, Armenian schools and Christian
buildings, the 1881 Ottoman census demographics, and an interactive Leaflet
web map — all deployable via GitHub Pages.

**[→ Open interactive map](https://YOUR_USERNAME.github.io/ottoman-anatolia-schooling-hgis/web/](https://emreamasyali.github.io/ottoman-anatolia-schooling-hgis/web/)**

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

The dataset covers **335 kazas** (sub-provincial districts) across the
Anatolian vilayets of the late Ottoman Empire. The unit of observation is
the kaza as it existed c. 1899–1914. The core analytical focus is the
relationship between the presence of Protestant missionary institutions,
the density of existing Christian communities (Armenians, Greeks, and
other denominations), and Ottoman state schooling outcomes.

Key data components:

| Component | Records | Period | Format |
|---|---|---|---|
| Kaza boundary polygons | 332 kazas | c. 1899–1914 | Shapefile, GeoJSON |
| Missionary stations & outstations | 420 locations | 1870–1914 | Shapefile, GeoJSON |
| Armenian community schools | 1,313 locations | c. 1901 | Shapefile, GeoJSON |
| Christian buildings | 9,476 locations | mixed | Shapefile, GeoJSON |
| Main ABC-FM stations | 10 locations | c. 1900 | Shapefile, GeoJSON |
| Commercial centers | 4 locations | c. 1890 | Shapefile, GeoJSON |
| 1881 census demographics | 335 kazas | 1881/82–1893 | Stata, CSV |
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

The kaza polygons were **manually digitised** from a combination of:

- Ottoman cadastral map sheets (1:200,000 scale, c. 1899–1914), accessed via
  the Istanbul Atatürk Library (digital copies).
- Stanford's Ottoman spatial data published through the
  *World Historical Gazetteer* project (cross-referenced for vilayet outlines).
- Cuinet, Vital. *La Turquie d'Asie* (4 vols., 1890–1894), for administrative
  descriptions of individual kazas.

Each polygon was traced in ArcGIS and assigned a unique **RTENO** identifier.
Boundaries reflect the administrative geography c. 1905, the midpoint of the
census and schooling data. Minor boundary disputes between adjacent sources
were resolved in favour of the Ottoman census tabulation geography
(Karpat 1985).

### ABC-FM missionary stations

The American Board of Commissioners for Foreign Missions (ABC-FM) operated
the dominant Protestant missionary network in Anatolia. Station coordinates
were geocoded from:

- ABC-FM *Annual Reports*, 1870–1914 (digitised volumes held by the Houghton
  Library, Harvard University).
- ABC-FM correspondence and field reports (*ABC 16*, Houghton Library archives).
- Smith, Eli and Harrison Gray Otis Dwight. *Missionary Researches in Armenia*
  (1833) — for the 1834 reconnaissance journey encoded as an instrumental
  variable shapefile (`Instrumental Variables/Smith&DwightJourney_1834.shp`).

Each location record includes the station name, Ottoman administrative
hierarchy (vilayet / sanjak / kaza), modern place name, mission name,
and classification (main station vs. outstation vs. dependent congregation).

**Field `Out-Statio` = 1** indicates an outstation (a secondary location
served from a main station but without a resident missionary).
**Field `Main Stati` = 1** indicates a principal station with a resident
missionary household.

### Armenian schools

Armenian community school locations were geocoded from the **1901 Ottoman
education yearbook** (*Maarif Salnamesi*), which tabulated schools by
community and administrative unit. Place names were matched to the
*Ottoman Gazetteer (ver. 9)* to derive latitude/longitude coordinates.
Unmatched records were excluded; matching rates are reported in the
project paper.

### Christian buildings

Point locations for churches, chapels, and baptisteries were derived from:

- OpenStreetMap (queried January 2020, filtered for `amenity=place_of_worship`
  and `religion=christian` within the study region).
- Historical sources cross-referenced against the ABC-FM archive for
  building-level verification of selected sites.

### 1881 Ottoman census (*Nüfus-i Umumi*)

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

- **1876**: Initial survey of Ottoman state schools (Ruşdiye / Rüşdiye
  level, male only).
- **1902–1908**: Expanded enumeration covering male and female ibtidai
  (primary) and ruşdiye (secondary) schools, compiled from the annual
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

The dataset is deliberately **cross-sectional at c. 1900**. The kaza
boundaries, missionary station counts, and census demographics all refer
to the late Hamidian / early Unionist period (roughly 1893–1914). The
school census provides two points (1876 and 1902–08). No attempt has
been made to model boundary changes between censuses; the 1881 and 1914
administrative geographies are treated as equivalent for the purpose of
the analysis.

### Incomplete vilayet coverage

The digitised kaza boundary set covers the core Anatolian vilayets. Several
peripheral regions are partially represented or absent:
- **Halep (Aleppo) Vilayet** — southern kazas only.
- **Edirne Vilayet** — included but treated as outside the Anatolian core
  in the main regression sample.
- **Kars** — included as a special administrative zone.

### Simplification

Kaza boundary polygons exported to GeoJSON are simplified using a tolerance
of 0.0001 degrees (roughly 10 m at the equator) via Shapely's
`simplify(preserve_topology=True)`. This reduces file sizes by ~30% without
affecting visual accuracy at typical web-map zoom levels (z6–z10). The
original unsimplified shapefiles are preserved in `data/raw/`.

### Encoding

All CSV exports use **UTF-8 with BOM** (`utf-8-sig`) to ensure correct
display of Ottoman place names in Excel without manual encoding selection.
The Stata files use Stata's internal string encoding; variable labels and
value labels are preserved in the `.dta` format but stripped in the CSV
export.

### Raw vs. derived data

Files in `data/raw/` are never modified by the conversion pipeline. They
serve as archival copies for download. Files in `data/derived/` are
fully reproducible by running `scripts/convert_data.py`.

---

## Variable descriptions

### `master_dataset.csv` / `master_dataset.dta`
Master merged dataset (335 rows, one per kaza).

| Variable | Description |
|---|---|
| `NameofKaza` | Ottoman kaza name (transliterated) |
| `kazcode` | Unique kaza identifier (join key) |
| `NameofSanjak` | Ottoman sanjak (county) name |
| `NameofVilayet` | Ottoman vilayet (province) name |
| `Muslims_Female` / `Muslims_Male` | Muslim population by sex (1881 census) |
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
| `MaleRusdiyyeSchools1876` | Male ruşdiye (middle) school count, 1876 |
| `MaleRusdiyyeSchools19021908` | Male ruşdiye school count, 1902–08 |
| `FemaleRusdiyyeSchools190219` | Female ruşdiye school count, 1902–08 |

---

## Download links

All data files are available directly from this repository.

### GeoJSON (web map layers)

| Layer | File | Features |
|---|---|---|
| Kaza boundaries (WGS-84) | [`data/derived/geojson/kazas_boundaries.geojson`](data/derived/geojson/kazas_boundaries.geojson) | 332 polygons |
| Missionary stations | [`data/derived/geojson/missionary_stations.geojson`](data/derived/geojson/missionary_stations.geojson) | 420 points |
| Main missionary stations | [`data/derived/geojson/main_missionary_stations.geojson`](data/derived/geojson/main_missionary_stations.geojson) | 10 points |
| Armenian schools | [`data/derived/geojson/armenian_schools.geojson`](data/derived/geojson/armenian_schools.geojson) | 1,313 points |
| Christian buildings | [`data/derived/geojson/christian_buildings.geojson`](data/derived/geojson/christian_buildings.geojson) | 9,476 points |
| Commercial centers | [`data/derived/geojson/commercial_centers.geojson`](data/derived/geojson/commercial_centers.geojson) | 4 points |

### CSV (tabular data)

| Dataset | File | Rows |
|---|---|---|
| Master dataset | [`data/derived/csv/master_dataset.csv`](data/derived/csv/master_dataset.csv) | 335 |
| 1881 census | [`data/derived/csv/census_1881.csv`](data/derived/csv/census_1881.csv) | 335 |
| School census | [`data/derived/csv/schools.csv`](data/derived/csv/schools.csv) | 1,000 |

### Stata / .dta

| Dataset | File |
|---|---|
| Master dataset | [`data/raw/stata/master_dataset.dta`](data/raw/stata/master_dataset.dta) |
| 1881 census | [`data/raw/stata/census_1881.dta`](data/raw/stata/census_1881.dta) |
| School census | [`data/raw/stata/schools.dta`](data/raw/stata/schools.dta) |

### Shapefiles

| Layer | Folder |
|---|---|
| Kaza boundaries | [`data/raw/shapefiles/boundaries/`](data/raw/shapefiles/boundaries/) |
| All missionary stations | [`data/raw/shapefiles/points/AllStations_Missionary.*`](data/raw/shapefiles/points/) |
| Armenian schools | [`data/raw/shapefiles/points/ArmenianSchools.*`](data/raw/shapefiles/points/) |
| Christian buildings | [`data/raw/shapefiles/points/AllChristianBuildings.*`](data/raw/shapefiles/points/) |
| Main stations | [`data/raw/shapefiles/points/Main Stations.*`](data/raw/shapefiles/points/) |
| Commercial centers | [`data/raw/shapefiles/points/Commercial Centers.*`](data/raw/shapefiles/points/) |

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
  (1881 census), from dark blue (< 2%) to pale blue (> 35%).
- **Hover tooltips** — hovering a kaza shows the 1881 population breakdown
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

If you use this dataset in published research, please cite:

> [Author, Year]. *Ottoman Anatolia Schooling HGIS Dataset* [Data set].
> McGill University. https://github.com/YOUR_USERNAME/ottoman-anatolia-schooling-hgis

Primary sources that must also be cited:

- Karpat, Kemal H. *Ottoman Population, 1830–1914: Demographic and Social
  Characteristics*. Madison: University of Wisconsin Press, 1985.
- American Board of Commissioners for Foreign Missions. *Annual Report*.
  Boston: ABCFM, 1870–1914. [Houghton Library, Harvard University]
- Ottoman Ministry of Education. *Maarif Salnamesi* [Education Yearbook].
  Istanbul: Matbaa-i Amire, 1901–1908.

---

## License

**Data**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
You are free to share and adapt the data for any purpose, provided you give
appropriate credit.

**Code** (`scripts/`, `web/`): [MIT License](https://opensource.org/licenses/MIT)

Original boundary digitisation and data compilation by the repository
authors. Census data reproduced under scholarly fair use from Karpat (1985).
OpenStreetMap data © OpenStreetMap contributors (ODbL).

