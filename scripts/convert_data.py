#!/usr/bin/env python3
"""
convert_data.py
===============
Converts the raw spatial and tabular data for the Ottoman Anatolia
Schooling HGIS project into web-ready formats:

  - Shapefiles (EPSG:3857 or EPSG:4326)  → GeoJSON (EPSG:4326 / WGS-84)
  - Stata .dta files                      → CSV

Outputs are written to data/derived/geojson/ and data/derived/csv/.
Original source files in data/raw/ are never modified.

Usage:
    python3 scripts/convert_data.py [--repo-root PATH]

Dependencies:
    pip install geopandas pyreadstat pandas
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import geopandas as gpd
    import pandas as pd
    import pyreadstat
except ImportError as e:
    sys.exit(f"Missing dependency: {e}\nRun: pip install geopandas pyreadstat pandas")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def resolve_root(arg_root) -> Path:
    if arg_root:
        return Path(arg_root).resolve()
    # Default: parent of the scripts/ directory
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Shapefile → GeoJSON
# ---------------------------------------------------------------------------

SHAPEFILE_JOBS = [
    # (source relative to raw/shapefiles, output stem, layer_description)
    (
        "boundaries/AllKazas_December2019.shp",
        "kazas_boundaries",
        "Ottoman kaza (district) boundaries, manually traced from 1:200,000 "
        "Ottoman cadastral maps (c. 1899–1914). Each polygon represents one "
        "administrative kaza. 1881 census demographics joined on RTENO.",
    ),
    (
        "points/Missionary Locations Jeff 20190131.shp",
        "missionary_locations",
        "All Protestant missionary locations in Ottoman Anatolia (492 points), "
        "compiled from ABC-FM Annual Reports, 1870–1914. Includes date founded, "
        "dependent station, and station type (main vs outstation).",
    ),
    (
        "points/AllStations_Missionary.shp",
        "missionary_stations",
        "Protestant missionary stations and outstations in Ottoman Anatolia, "
        "compiled from ABC-FM (American Board of Commissioners for Foreign "
        "Missions) Annual Reports, 1870–1914. Includes main stations, "
        "outstations, and dependent congregations. Column 'Out-Statio'==1 "
        "denotes an outstation; 'Main Stati'==1 a main station.",
    ),
    (
        "points/ArmenianSchools.shp",
        "armenian_schools",
        "Armenian community schools geocoded from the 1901 Ottoman school "
        "census (Maarif Salnamesi). Point locations derived by matching "
        "school names to the Ottoman Gazetteer (ver. 9).",
    ),
    (
        "points/AllChristianBuildings.shp",
        "christian_buildings",
        "Christian religious buildings (churches, chapels, baptisteries) "
        "geocoded from OpenStreetMap and historical sources.",
    ),
    (
        "points/Main Stations.shp",
        "main_missionary_stations",
        "The ten principal ABC-FM mission stations in Anatolia, "
        "used as the primary administrative hubs of the mission network.",
    ),
    (
        "points/Commercial Centers.shp",
        "commercial_centers",
        "Major commercial centers identified from Ottoman trade directories "
        "and Cuinet's La Turquie d'Asie (1890–1894).",
    ),
]

# Relative path from repo root to the canonical census source
CENSUSNEW_REL = Path("data/raw/CensusNew.xlsx")

# Mapping: shapefile RTENO (for 5 Edirne polygons not in census_1881.dta)
# → "Name of Kaza" value in CensusNew.xlsx.
# The AllKazas_OttomanCensus_April2020.csv had misaligned labels for Edirne;
# CensusNew carries the correct names and figures.
EDIRNE_RTENO_TO_CN_KAZA = {
    "Edirne_Edirne_Kirkkilise Kaza": "Kirkkilise (Korklareli) Kaza",
    "Edirne_Edirne_Tekirdag Kaza":   "Tekirdağı (Tekfurdağı)",
    "Edirne_Edirne_Gelibolu Kaza":   "Gelibolu Kaza",
    "Edirne_Edirne_Edirne Kaza":     "Edirne Central Sanjak",
    "Edirne_Edirne_Dedeagac Kaza":   "Dedeağaç Kaza",
}

# CensusNew column → GeoJSON keep-list column name
CENSUSNEW_TO_KEEP = {
    "Name of Kaza":          "KazaName",
    "Name of Vilayet":       "Vilayet",         # strip "Vilayet" suffix below
    "Name of Sanjak":        "Sanjak",           # strip "Sanjak" suffix below
    "kazcode":               "kazcode",
    "Christian Share":       "ChristianShare",
    "Armenian Share":        "ArmenianShare",
    "Grand Total":           "GrandTotal",
    "Total_Muslim":          "Total_Muslim",
    "Total_Christian":       "Total_Christian",
    "Total_Armenian":        "Total_Armenian",
    "Muslims_Female":        "Muslims_Female",
    "Muslims_Male":          "Muslims_Male",
    "Armenians_Female":      "Armenians_Total",  # field name kept for back-compat
    "Greeks_Female":         "Greeks_Female",
    "Greeks_Male":           "Greeks_Male",
    "Christian_Muslim_Ratio": "Christian_Muslim_Ratio",
    "Armenian_Muslim_Ratio":  "Armenian_Muslim_Ratio",
}

# CensusNew column renames for the clean CSV / Stata export
CENSUSNEW_COL_RENAME = {
    "Name of Kaza":                  "KazaName",
    "Name of Sanjak":                "Sanjak",
    "Name of Vilayet":               "Vilayet",
    "Non-Muslim Gypsies_Female":     "NonMuslimGypsies_Female",
    "Non-Muslim Gypsies_Male":       "NonMuslimGypsies_Male",
    "Foreign Citizens_Female":       "ForeignCitizens_Female",
    "Foreign Citizens_Male":         "ForeignCitizens_Male",
    "Armenian Share":                "ArmenianShare",
    "Christian Share":               "ChristianShare",
    "Grand Total":                   "GrandTotal",
    "Sanjak Center":                 "SanjakCenter",
}

# Human-readable variable labels for the Stata .dta output
CENSUSNEW_VAR_LABELS = {
    "KazaName":                  "Name of kaza (sub-district)",
    "kazcode":                   "Kaza code (vilayet-sanjak-kaza)",
    "Sanjak":                    "Name of sanjak (province subdivision)",
    "sancode":                   "Sanjak code",
    "Vilayet":                   "Name of vilayet (province)",
    "vilcode":                   "Vilayet code",
    "Muslims_Female":            "Muslim female population",
    "Muslims_Male":              "Muslim male population",
    "Greeks_Female":             "Greek Orthodox female population",
    "Greeks_Male":               "Greek Orthodox male population",
    "Armenians_Female":          "Armenian female population",
    "Armenians_Male":            "Armenian male population",
    "Bulgarians_Female":         "Bulgarian female population",
    "Bulgarians_Male":           "Bulgarian male population",
    "Catholics_Female":          "Catholic female population",
    "Catholics_Male":            "Catholic male population",
    "Jews_Female":               "Jewish female population",
    "Jews_Male":                 "Jewish male population",
    "Protestants_Female":        "Protestant female population",
    "Protestants_Male":          "Protestant male population",
    "Latins_Female":             "Latin female population",
    "Latins_Male":               "Latin male population",
    "Monophysites_Female":       "Monophysite female population",
    "Monophysites_Male":         "Monophysite male population",
    "NonMuslimGypsies_Female":   "Non-Muslim Gypsy female population",
    "NonMuslimGypsies_Male":     "Non-Muslim Gypsy male population",
    "ForeignCitizens_Female":    "Foreign citizen female population",
    "ForeignCitizens_Male":      "Foreign citizen male population",
    "Total_Muslim":              "Total Muslim population",
    "Total_Christian":           "Total Christian population",
    "Total_NonMuslim":           "Total non-Muslim population",
    "Total_Armenian":            "Total Armenian population",
    "Christian_Muslim_Ratio":    "Ratio of Christians to Muslims",
    "Armenian_Muslim_Ratio":     "Ratio of Armenians to Muslims",
    "ArmenianShare":             "Armenian share of total population",
    "ChristianShare":            "Christian share of total population",
    "Total_Female":              "Total female population",
    "Total_Male":                "Total male population",
    "GrandTotal":                "Grand total population",
    "Source":                    "Data source reference",
    "SanjakCenter":              "Sanjak center dummy (1=central kaza)",
}

# Census columns to join into kaza boundaries (prefixed by ArcGIS join)
CENSUS_COL_RENAME = {
    "census_gis_merged_csv_ChristianS": "ChristianShare",
    "census_gis_merged_csv_ArmenianSh": "ArmenianShare",
    "census_gis_merged_csv_GrandTotal": "GrandTotal",
    "census_gis_merged_csv_Total_Musl": "Total_Muslim",
    "census_gis_merged_csv_Total_Chri": "Total_Christian",
    "census_gis_merged_csv_Total_Arme": "Total_Armenian",
    "census_gis_merged_csv_Muslims_Fe": "Muslims_Female",
    "census_gis_merged_csv_Muslims_Ma": "Muslims_Male",
    "census_gis_merged_csv_Armenians_": "Armenians_Total",
    "census_gis_merged_csv_Greeks_Fem": "Greeks_Female",
    "census_gis_merged_csv_Greeks_Mal": "Greeks_Male",
    "census_gis_merged_csv_Vilayet":    "Vilayet",
    "census_gis_merged_csv_Sanjak":     "Sanjak",
    "census_gis_merged_csv_kaza":       "KazaName",
    "census_gis_merged_csv_kazcode":    "kazcode",
    "census_gis_merged_csv_Christian_": "Christian_Muslim_Ratio",
    "census_gis_merged_csv_Armenian_M": "Armenian_Muslim_Ratio",
}

# Columns to rename for clarity (shapefile truncation artefacts)
RENAME_MAP = {
    "missionary_locations": {
        "Main Stati": "MainStation",
        "Out-Statio": "OutStation",
        "Date Found": "DateFounded",
    },
    "missionary_stations": {
        "Modern Nam": "ModernName",
        "Main Stati": "MainStation",
        "Out-Statio": "OutStation",
    },
    "christian_buildings": {
        "geometry/t": "geom_type_orig",
        "geometry/c": "geom_coords_orig",
        "properti_1": "name",
        "properti_2": "denomination",
        "properti_3": "country",
        "properti_4": "city",
        "properti_5": "source",
        "properti_6": "notes",
    },
    "armenian_schools": {
        "properti_1": "name",
        "properti_2": "type_detail",
        "properti_3": "location",
        "properti_4": "kaza",
        "properti_5": "vilayet",
        "properti_6": "notes",
    },
}

# Columns to drop before export (redundant / empty / internal)
DROP_COLS = {
    "missionary_stations": [
        "field_13","field_14","field_15","field_16","field_17",
        "field_18","field_19","field_20","field_21","field_22",
        "field_23","field_24",
    ],
    "christian_buildings": ["geom_type_orig", "geom_coords_orig", "geometry_1"],
    "armenian_schools":    ["geometry_1"],
}


def join_census(gdf: "gpd.GeoDataFrame", census_path: Path) -> "gpd.GeoDataFrame":
    """Join 1881 census attributes into the kaza boundary GeoDataFrame on RTENO."""
    census, _ = pyreadstat.read_dta(census_path)
    # Drop raw kazcode before renaming to avoid duplicate after rename
    if "kazcode" in census.columns and "census_gis_merged_csv_kazcode" in census.columns:
        census = census.drop(columns=["kazcode"])
    census = census.rename(columns=CENSUS_COL_RENAME)
    keep = ["RTENO", "KazaName", "Vilayet", "Sanjak", "kazcode",
            "ChristianShare", "ArmenianShare", "GrandTotal",
            "Total_Muslim", "Total_Christian", "Total_Armenian",
            "Muslims_Female", "Muslims_Male",
            "Greeks_Female", "Greeks_Male", "Armenians_Total",
            "Christian_Muslim_Ratio", "Armenian_Muslim_Ratio"]
    census_sub = census[[c for c in keep if c in census.columns]].drop_duplicates("RTENO")
    merged = gdf.merge(census_sub, on="RTENO", how="left")
    matched = merged["ChristianShare"].notna().sum()
    print(f"  Census join: {matched}/{len(merged)} kazas matched", end=" ", flush=True)

    # Supplement Edirne Vilayet kazas absent from census_1881.dta using CensusNew.xlsx
    unmatched_mask = merged["ChristianShare"].isna() & merged["RTENO"].notna()
    if unmatched_mask.any():
        cn_path = census_path.parent.parent.parent / CENSUSNEW_REL.name
        # Also try the canonical location relative to repo root
        if not cn_path.exists():
            cn_path = census_path.parent.parent.parent.parent / CENSUSNEW_REL
        if cn_path.exists():
            cn = pd.read_excel(cn_path)
            cn["Vilayet"] = cn["Name of Vilayet"].str.replace(
                r"\s*Vilayet.*|\s*Province.*", "", regex=True).str.strip()
            cn["Sanjak"]  = cn["Name of Sanjak"].str.replace(
                r"\s*Sanjak.*", "", regex=True).str.strip()
            # Build kaza-name → row lookup (using CensusNew "Name of Kaza")
            cn_lookup = cn.set_index("Name of Kaza")
            fill_cols = [c for c in keep if c != "RTENO"]
            patch_rows = {}
            for rteno in merged.loc[unmatched_mask, "RTENO"].values:
                cn_kaza = EDIRNE_RTENO_TO_CN_KAZA.get(rteno)
                if cn_kaza and cn_kaza in cn_lookup.index:
                    row = cn_lookup.loc[cn_kaza]
                    patch_row = {}
                    for cn_col, keep_col in CENSUSNEW_TO_KEEP.items():
                        if keep_col in fill_cols:
                            if keep_col in ("Vilayet", "Sanjak"):
                                patch_row[keep_col] = cn.loc[
                                    cn["Name of Kaza"] == cn_kaza,
                                    keep_col].iloc[0]
                            elif cn_col in row.index:
                                patch_row[keep_col] = row[cn_col]
                    patch_rows[rteno] = patch_row
            if patch_rows:
                for col in fill_cols:
                    if col not in merged.columns:
                        merged[col] = None
                patch_df = pd.DataFrame(patch_rows).T   # RTENOs as index
                patch_df.index.name = "RTENO"
                patch_df = patch_df.reset_index()
                patch_df.index = merged.index[
                    merged["RTENO"].isin(patch_rows.keys()) & unmatched_mask]
                merged.update(patch_df[[c for c in fill_cols if c in patch_df.columns]])
            supplemented = (merged["ChristianShare"].notna().sum() - matched)
            print(f"(+{supplemented} from CensusNew)", end=" ", flush=True)

    return merged


def shp_to_geojson(src: Path, dst: Path, stem: str, census_path: Path = None) -> None:
    print(f"  Converting {src.name} → {dst.name} ...", end=" ", flush=True)
    gdf = gpd.read_file(src)

    # Re-project to WGS-84 if needed
    if gdf.crs is None:
        print("WARNING: no CRS; assuming EPSG:4326", end=" ")
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    # Join census data for kaza boundaries
    if stem == "kazas_boundaries" and census_path and census_path.exists():
        gdf = join_census(gdf, census_path)

    # Rename columns
    if stem in RENAME_MAP:
        gdf = gdf.rename(columns=RENAME_MAP[stem])

    # Drop unnecessary columns
    if stem in DROP_COLS:
        drop = [c for c in DROP_COLS[stem] if c in gdf.columns]
        gdf = gdf.drop(columns=drop)

    # Simplify polygons to reduce file size
    gdf["geometry"] = gdf["geometry"].simplify(0.0001, preserve_topology=True) \
        if gdf.geometry.geom_type.iloc[0] == "Polygon" else gdf["geometry"]

    # Write GeoJSON
    dst.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(dst, driver="GeoJSON")
    size_kb = dst.stat().st_size / 1024
    print(f"done ({len(gdf)} features, {size_kb:.0f} KB)")


# ---------------------------------------------------------------------------
# Stata → CSV
# ---------------------------------------------------------------------------

STATA_JOBS = [
    (
        "master_dataset.dta",
        "master_dataset.csv",
        "Master merged dataset: 1881 Ottoman census demographics joined to "
        "kaza geometries. Unit of observation is the kaza. Key variables "
        "include population by ethno-religious group, schooling counts, and "
        "geographic controls.",
    ),
    (
        "schools.dta",
        "schools.csv",
        "Ottoman school census data c. 1876 and 1902–1908, from the "
        "Maarif Salnamesi (Education Yearbooks). Counts of male/female "
        "ibtidai (primary) and rüşdiye (secondary) schools per kaza.",
    ),
]

CENSUSNEW_DESC = (
    "1881/82–1893 Ottoman census (Nüfus-i Umumi) tabulated at the kaza level. "
    "Population counts by sex and ethno-religious community (Muslims, Greeks, "
    "Armenians, Bulgarians, Catholics, Jews, Protestants, Latins, Monophysites, "
    "Non-Muslim Gypsies, Foreign Citizens). Includes all 16 vilayets + Edirne "
    "Vilayet (European Turkey). Source: Karpat (1985). Clean labels from "
    "CensusNew.xlsx."
)


def censusnew_export(cn_path: Path, out_csv: Path, out_dta: Path) -> None:
    """Export CensusNew.xlsx → clean CSV and labelled Stata .dta."""
    print(f"  Exporting CensusNew.xlsx → {out_csv.name} + {out_dta.name} ...",
          end=" ", flush=True)
    df = pd.read_excel(cn_path)
    df = df.rename(columns=CENSUSNEW_COL_RENAME)

    # Strip "Vilayet"/"Province" and "Sanjak" suffixes for the full-name columns
    if "Vilayet" in df.columns:
        df["Vilayet"] = df["Vilayet"].str.replace(
            r"\s*Vilayet.*|\s*Province.*", "", regex=True).str.strip()
    if "Sanjak" in df.columns:
        df["Sanjak"] = df["Sanjak"].str.replace(
            r"\s*Sanjak.*", "", regex=True).str.strip()

    # CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # Stata .dta with variable labels
    out_dta.parent.mkdir(parents=True, exist_ok=True)
    labels = {col: CENSUSNEW_VAR_LABELS[col]
              for col in df.columns if col in CENSUSNEW_VAR_LABELS}
    pyreadstat.write_dta(df, str(out_dta), column_labels=labels)

    print(f"done ({len(df)} rows × {len(df.columns)} cols)")


def dta_to_csv(src: Path, dst: Path) -> None:
    print(f"  Converting {src.name} → {dst.name} ...", end=" ", flush=True)
    df, meta = pyreadstat.read_dta(src)

    # Decode any remaining bytes columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(
            lambda x: x.decode("utf-8", errors="replace") if isinstance(x, bytes) else x
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False, encoding="utf-8-sig")
    print(f"done ({len(df)} rows × {len(df.columns)} cols)")




# ---------------------------------------------------------------------------
# Codebook helpers
# ---------------------------------------------------------------------------

def write_layer_metadata(root: Path, shp_jobs, stata_jobs) -> None:
    """Write a machine-readable JSON index of all derived files."""
    index = {"geojson": [], "csv": [], "stata": []}

    for src_rel, stem, desc in shp_jobs:
        src = Path(src_rel)
        index["geojson"].append({
            "file": f"data/derived/geojson/{stem}.geojson",
            "source_shapefile": f"data/raw/shapefiles/{src_rel}",
            "description": desc,
            "crs": "EPSG:4326 (WGS-84)",
        })

    for src_name, dst_name, desc in stata_jobs:
        index["csv"].append({
            "file": f"data/derived/csv/{dst_name}",
            "source_stata": f"data/raw/stata/{src_name}",
            "description": desc,
        })

    # CensusNew-derived files
    index["csv"].append({
        "file": "data/derived/csv/census_1881.csv",
        "source": str(CENSUSNEW_REL),
        "description": CENSUSNEW_DESC,
    })
    index["stata"].append({
        "file": "data/derived/stata/census_1881.dta",
        "source": str(CENSUSNEW_REL),
        "description": CENSUSNEW_DESC,
    })

    out = root / "data" / "derived" / "layer_index.json"
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    print(f"  Layer index written → {out.relative_to(root)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Path to repository root (default: parent of scripts/)")
    args = parser.parse_args()

    root = resolve_root(args.repo_root)
    raw_shp  = root / "data" / "raw" / "shapefiles"
    raw_dta  = root / "data" / "raw" / "stata"
    out_geoj = root / "data" / "derived" / "geojson"
    out_csv  = root / "data" / "derived" / "csv"

    print(f"\n{'='*60}")
    print(f"Ottoman Anatolia HGIS — Data Conversion")
    print(f"Repository root: {root}")
    print(f"{'='*60}\n")

    census_path = raw_dta / "census_1881.dta"

    # --- Shapefiles → GeoJSON ---
    print("[ Shapefiles → GeoJSON ]\n")
    for src_rel, stem, _ in SHAPEFILE_JOBS:
        src = raw_shp / src_rel
        dst = out_geoj / f"{stem}.geojson"
        if not src.exists():
            print(f"  SKIP {src.name} (not found at {src})")
            continue
        shp_to_geojson(src, dst, stem, census_path=census_path)

    # --- CensusNew → census_1881.csv + census_1881.dta ---
    cn_path = root / CENSUSNEW_REL
    out_dta_dir = root / "data" / "derived" / "stata"
    print("\n[ CensusNew → census CSV + Stata ]\n")
    if cn_path.exists():
        censusnew_export(cn_path,
                         out_csv / "census_1881.csv",
                         out_dta_dir / "census_1881.dta")
    else:
        print(f"  SKIP CensusNew.xlsx (not found at {cn_path})")

    # --- Stata → CSV (master_dataset, schools) ---
    print("\n[ Stata .dta → CSV ]\n")
    for src_name, dst_name, _ in STATA_JOBS:
        src = raw_dta / src_name
        dst = out_csv / dst_name
        if not src.exists():
            print(f"  SKIP {src_name} (not found at {src})")
            continue
        dta_to_csv(src, dst)

    # --- Layer index ---
    print("\n[ Writing layer index ]\n")
    write_layer_metadata(root, SHAPEFILE_JOBS, STATA_JOBS)

    print(f"\n{'='*60}")
    print("Conversion complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
