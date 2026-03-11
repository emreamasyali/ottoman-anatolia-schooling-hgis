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

    # Supplement with CSV for kazas absent from the Stata file (e.g. Edirne Vilayet)
    unmatched_mask = merged["ChristianShare"].isna() & merged["RTENO"].notna()
    if unmatched_mask.any():
        csv_path = census_path.parent.parent.parent.parent / "AllKazas_OttomanCensus_April2020.csv"
        if csv_path.exists():
            csv = pd.read_csv(csv_path, encoding="latin1")
            csv = csv[csv["RTENO"].notna()].copy()
            csv["GrandTotal"] = csv["TotalMuslim"] + csv["TotalNonMuslim"]
            csv["Vilayet"] = csv["vilayet"].str.replace(r"\s*Vilayet.*", "", regex=True).str.strip()
            csv["Sanjak"]  = csv["sanjak"].str.replace(r"\s*Sanjak.*",  "", regex=True).str.strip()
            csv_rename = {
                "kaza":               "KazaName",
                "kazcode":            "kazcode",
                "ChristianShare":     "ChristianShare",
                "ArmenianShare":      "ArmenianShare",
                "TotalMuslim":        "Total_Muslim",
                "TotalChristian":     "Total_Christian",
                "TotalArmenian":      "Total_Armenian",
                "MuslimFemale":       "Muslims_Female",
                "MuslimMale":         "Muslims_Male",
                "ArmenianFemale":     "Armenians_Total",
                "GreekFemale":        "Greeks_Female",
                "GreekMale":          "Greeks_Male",
                "ChristianMuslimRatio": "Christian_Muslim_Ratio",
                "ArmenianMuslimRatio":  "Armenian_Muslim_Ratio",
            }
            csv = csv.rename(columns=csv_rename)
            csv_sub = csv[["RTENO"] + [c for c in keep if c in csv.columns and c != "RTENO"]].drop_duplicates("RTENO")
            fill_cols = [c for c in keep if c in csv_sub.columns and c != "RTENO"]
            # Build patch indexed like merged's unmatched rows, then update() in-place
            unmatched_rtenos = merged.loc[unmatched_mask, "RTENO"].values
            patch = pd.DataFrame({"RTENO": unmatched_rtenos}).merge(
                csv_sub[["RTENO"] + fill_cols], on="RTENO", how="left"
            )
            patch.index = merged.index[unmatched_mask]
            merged.update(patch[fill_cols])
            supplemented = (merged["ChristianShare"].notna().sum() - matched)
            print(f"(+{supplemented} from CSV)", end=" ", flush=True)

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
        "census_1881.dta",
        "census_1881.csv",
        "1881/82–1893 Ottoman census (Nüfus-i Umumi) tabulated at the kaza "
        "level. Population counts by sex and ethno-religious community "
        "(Muslims, Greeks, Armenians, Bulgarians, Catholics, Jews, "
        "Protestants, Latins, Monophysites, Non-Muslim Gypsies, "
        "Foreign Citizens). Source: Karpat (1985).",
    ),
    (
        "schools.dta",
        "schools.csv",
        "Ottoman school census data c. 1876 and 1902–1908, from the "
        "Maarif Salnamesi (Education Yearbooks). Counts of male/female "
        "ibtidai (primary) and rüşdiye (secondary) schools per kaza.",
    ),
]


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
    index = {"geojson": [], "csv": []}

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

    # --- Stata → CSV ---
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
