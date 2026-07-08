#!/usr/bin/env python3
"""Controler l'inventaire local des donnees SlowVaud."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402

from slowvaud.paths import data_paths, load_config  # noqa: E402

CRS_LV95 = "EPSG:2056"
CRS_WGS84 = "EPSG:4326"


def _status(path: Path) -> str:
    return "ok" if path.exists() else "missing"


def _vector_row(label: str, path: Path, expected_crs: str) -> dict[str, object]:
    row: dict[str, object] = {
        "dataset": label,
        "path": str(path),
        "status": _status(path),
        "features": None,
        "crs": None,
        "expected_crs": expected_crs,
    }
    if not path.exists():
        return row
    gdf = gpd.read_file(path)
    row["features"] = len(gdf)
    row["crs"] = str(gdf.crs)
    return row


def vector_inventory() -> pd.DataFrame:
    cfg = load_config()
    paths = data_paths()
    rows: list[dict[str, object]] = []
    for agglo_key in cfg["agglomerations"]:
        rows.append(
            _vector_row(
                f"agglomeration_dissolved/{agglo_key}",
                paths["processed"] / "agglomerations" / "vaco" / f"{agglo_key}_dissolved.geojson",
                CRS_LV95,
            )
        )
        rows.append(
            _vector_row(
                f"osm_cycle_context/{agglo_key}",
                paths["raw_osm"] / f"osm_cycle_context_{agglo_key}.geojson",
                CRS_WGS84,
            )
        )
        rows.append(
            _vector_row(
                f"swisstlm3d_roads/{agglo_key}",
                paths["raw_swisstlm3d"] / "roads" / f"swisstlm3d_roads_{agglo_key}.geojson",
                CRS_LV95,
            )
        )
    rows.append(
        _vector_row(
            "context/geneve_sitg_amenagements_2roues",
            paths["context"] / "geneve" / "geneve_sitg_amenagements_2roues.geojson",
            CRS_WGS84,
        )
    )
    rows.append(
        _vector_row(
            "context/lausanne_viageo_velo_amenagement",
            paths["context"] / "lausanne" / "lausanne_viageo_velo_amenagement.geojson",
            CRS_LV95,
        )
    )
    rows.append(
        _vector_row(
            "context/zurich_veloinfrastruktur_radwege",
            paths["context"] / "zurich" / "zurich_veloinfrastruktur_radwege.geojson",
            CRS_LV95,
        )
    )
    rows.append(
        _vector_row(
            "context/zurich_veloinfrastruktur_radstreifen",
            paths["context"] / "zurich" / "zurich_veloinfrastruktur_radstreifen.geojson",
            CRS_LV95,
        )
    )
    return pd.DataFrame(rows)


def orthophoto_inventory() -> pd.DataFrame:
    root = data_paths()["raw_orthophotos"] / "ch.swisstopo.swissimage-dop10"
    rows: list[dict[str, object]] = []
    for gsd_key, expected_res in [("gsd_2_0", 2.0), ("gsd_0_1", 0.1)]:
        folder = root / gsd_key
        files = sorted(folder.glob("*.tif")) if folder.exists() else []
        row: dict[str, object] = {
            "dataset": f"orthophotos/{gsd_key}",
            "path": str(folder),
            "status": "ok" if files else "missing",
            "files": len(files),
            "sample_crs": None,
            "sample_res": None,
            "expected_res": expected_res,
        }
        if files:
            with rasterio.open(files[0]) as src:
                row["sample_crs"] = str(src.crs)
                row["sample_res"] = src.res[0]
        rows.append(row)
    return pd.DataFrame(rows)


def file_inventory() -> pd.DataFrame:
    paths = data_paths()
    rows = [
        {
            "dataset": "swisstlm3d_source_zip",
            "path": str(paths["raw_swisstlm3d"] / "swisstlm3d_2026-02-24_2056_5728.gpkg.zip"),
            "status": _status(paths["raw_swisstlm3d"] / "swisstlm3d_2026-02-24_2056_5728.gpkg.zip"),
        },
        {
            "dataset": "lausanne_viageo_zip",
            "path": str(paths["context"] / "lausanne" / "lausanne_viageo_amenagement_cyclable.zip"),
            "status": _status(paths["context"] / "lausanne" / "lausanne_viageo_amenagement_cyclable.zip"),
        },
    ]
    return pd.DataFrame(rows)


def strict_failures(
    vector_df: pd.DataFrame,
    ortho_df: pd.DataFrame,
    file_df: pd.DataFrame,
) -> list[str]:
    failures: list[str] = []
    for row in vector_df.to_dict("records"):
        if row["status"] != "ok":
            failures.append(f"manquant: {row['dataset']}")
        elif row["crs"] != row["expected_crs"]:
            failures.append(f"CRS inattendu: {row['dataset']} = {row['crs']}")
    for row in file_df.to_dict("records"):
        if row["status"] != "ok":
            failures.append(f"manquant: {row['dataset']}")
    gsd_2 = ortho_df[ortho_df["dataset"] == "orthophotos/gsd_2_0"].iloc[0]
    if int(gsd_2["files"]) == 0:
        failures.append("manquant: orthophotos/gsd_2_0")
    gsd_01 = ortho_df[ortho_df["dataset"] == "orthophotos/gsd_0_1"].iloc[0]
    if int(gsd_01["files"]) == 0:
        failures.append("manquant: orthophotos/gsd_0_1_sample")
    return failures


def print_summary(
    vector_df: pd.DataFrame,
    ortho_df: pd.DataFrame,
    file_df: pd.DataFrame,
) -> None:
    vector_ok = int((vector_df["status"] == "ok").sum())
    vector_total = len(vector_df)
    file_ok = int((file_df["status"] == "ok").sum())
    file_total = len(file_df)

    gsd_2 = ortho_df[ortho_df["dataset"] == "orthophotos/gsd_2_0"].iloc[0]
    gsd_01 = ortho_df[ortho_df["dataset"] == "orthophotos/gsd_0_1"].iloc[0]

    print("\nInventaire SlowVaud")
    print(f"- Vecteurs: {vector_ok}/{vector_total} jeux présents")
    print(f"- Fichiers sources: {file_ok}/{file_total} présents")
    print(f"- Orthophotos 2.0 m: {gsd_2['status']} ({int(gsd_2['files'])} fichiers)")
    print(f"- Orthophotos 0.1 m: sample local ({int(gsd_01['files'])} fichiers)")
    print("\nNote: la couverture 0.1 m complète n'est pas attendue dans le paquet transmis.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    vector_df = vector_inventory()
    ortho_df = orthophoto_inventory()
    file_df = file_inventory()

    if args.verbose:
        print("\nVecteurs")
        print(vector_df.to_string(index=False))
        print("\nFichiers sources")
        print(file_df.to_string(index=False))
        print("\nOrthophotos")
        print(ortho_df.to_string(index=False))
    else:
        print_summary(vector_df, ortho_df, file_df)

    if args.strict:
        failures = strict_failures(vector_df, ortho_df, file_df)
        if failures:
            print("\nEchecs stricts")
            for failure in failures:
                print(f"- {failure}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
