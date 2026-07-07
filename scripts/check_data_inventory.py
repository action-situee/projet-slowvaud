#!/usr/bin/env python3
"""Controler l'inventaire local des donnees SlowVaud."""

from __future__ import annotations

import argparse
import json
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


def _gib(bytes_count: int | float) -> str:
    return f"{bytes_count / 1024**3:.1f} GiB"


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
            "context/geneve_sitg_amenagements_2roues",
            paths["context"] / "geneve" / "geneve_sitg_amenagements_2roues.geojson",
            CRS_WGS84,
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


def manifest_inventory() -> pd.DataFrame:
    paths = data_paths()
    manifest = paths["manifests"] / "orthophoto_stac_manifest.csv"
    rows: list[dict[str, object]] = [
        {
            "dataset": "orthophoto_stac_manifest",
            "path": str(manifest),
            "status": _status(manifest),
            "rows": None,
            "detail": None,
        }
    ]
    if manifest.exists():
        df = pd.read_csv(manifest)
        detail = [
            f"{gsd}: {count}"
            for gsd, count in sorted(df.groupby("gsd")["href"].nunique().to_dict().items())
        ]
        rows[0]["rows"] = len(df)
        rows[0]["detail"] = ", ".join(detail)

    estimate = paths["manifests"] / "orthophoto_stac_size_estimate.json"
    rows.append(
        {
            "dataset": "orthophoto_stac_size_estimate",
            "path": str(estimate),
            "status": _status(estimate),
            "rows": None,
            "detail": None,
        }
    )
    if estimate.exists():
        payload = json.loads(estimate.read_text(encoding="utf-8"))
        detail = [
            f"{row['gsd']}: {_gib(row['estimated_total_bytes'])}"
            for row in payload.get("summary", [])
        ]
        rows[-1]["rows"] = len(payload.get("summary", []))
        rows[-1]["detail"] = ", ".join(detail)
    return pd.DataFrame(rows)


def strict_failures(
    vector_df: pd.DataFrame,
    ortho_df: pd.DataFrame,
    manifest_df: pd.DataFrame,
) -> list[str]:
    failures: list[str] = []
    for row in vector_df.to_dict("records"):
        if row["status"] != "ok":
            failures.append(f"manquant: {row['dataset']}")
        elif row["crs"] != row["expected_crs"]:
            failures.append(f"CRS inattendu: {row['dataset']} = {row['crs']}")
    manifest_status = dict(zip(manifest_df["dataset"], manifest_df["status"], strict=False))
    if manifest_status.get("orthophoto_stac_manifest") != "ok":
        failures.append("manquant: orthophoto_stac_manifest")
    gsd_2 = ortho_df[ortho_df["dataset"] == "orthophotos/gsd_2_0"].iloc[0]
    if int(gsd_2["files"]) == 0:
        failures.append("manquant: orthophotos/gsd_2_0")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    vector_df = vector_inventory()
    ortho_df = orthophoto_inventory()
    manifest_df = manifest_inventory()

    print("\nVecteurs")
    print(vector_df.to_string(index=False))
    print("\nOrthophotos")
    print(ortho_df.to_string(index=False))
    print("\nManifestes")
    print(manifest_df.to_string(index=False))

    if args.strict:
        failures = strict_failures(vector_df, ortho_df, manifest_df)
        if failures:
            print("\nEchecs stricts")
            for failure in failures:
                print(f"- {failure}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
