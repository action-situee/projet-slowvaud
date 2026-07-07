"""Manifestes et telechargement WMTS SWISSIMAGE."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import requests

from .crs import buffer_bbox_wgs84, tile_range_for_bbox, wmts_pixel_size_m
from .paths import data_paths, ensure_data_tree, load_config

WMTS_TEMPLATE = "https://wmts.geo.admin.ch/1.0.0/{layer}/default/current/3857/{z}/{x}/{y}.{ext}"


def wmts_url(layer: str, zoom: int, x: int, y: int, extension: str = "jpeg") -> str:
    """Construire une URL WMTS GeoAdmin."""
    return WMTS_TEMPLATE.format(layer=layer, z=zoom, x=x, y=y, ext=extension)


def iter_tile_records(
    config: dict[str, Any] | None = None,
    agglomerations: Iterable[str] | None = None,
    profiles: Iterable[str] | None = None,
    max_tiles_per_profile: int | None = None,
) -> list[dict[str, Any]]:
    """Generer un manifeste de tuiles WMTS sans telecharger les images."""
    cfg = config or load_config()
    agglo_keys = list(agglomerations or cfg["agglomerations"].keys())
    profile_keys = list(profiles or cfg["orthophoto_profiles"].keys())
    records: list[dict[str, Any]] = []

    for agglo_key in agglo_keys:
        agglo = cfg["agglomerations"][agglo_key]
        lon = float(agglo["center_wgs84"]["lon"])
        lat = float(agglo["center_wgs84"]["lat"])
        buffer_m = float(agglo["ortho_buffer_m"])
        bbox = buffer_bbox_wgs84(lon, lat, buffer_m)

        for profile_key in profile_keys:
            profile = cfg["orthophoto_profiles"][profile_key]
            zoom = int(profile["zoom"])
            x_min, x_max, y_min, y_max = tile_range_for_bbox(bbox, zoom)
            all_tiles = [(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)]
            tiles = all_tiles[:max_tiles_per_profile] if max_tiles_per_profile else all_tiles
            ground_resolution_m = wmts_pixel_size_m(lat, zoom)

            for x, y in tiles:
                records.append(
                    {
                        "agglomeration": agglo_key,
                        "agglomeration_label": agglo["label"],
                        "profile": profile_key,
                        "profile_label": profile["label"],
                        "layer": profile["layer"],
                        "zoom": zoom,
                        "tile_x": x,
                        "tile_y": y,
                        "extension": profile.get("extension", "jpeg"),
                        "url": wmts_url(
                            profile["layer"],
                            zoom,
                            x,
                            y,
                            profile.get("extension", "jpeg"),
                        ),
                        "center_lon": lon,
                        "center_lat": lat,
                        "buffer_m": buffer_m,
                        "bbox_wgs84": json.dumps(bbox),
                        "bbox_crs": "EPSG:4326",
                        "wmts_crs": "EPSG:3857",
                        "estimated_pixel_size_m": round(ground_resolution_m, 4),
                        "tiles_in_full_bbox": len(all_tiles),
                        "manifest_limited": max_tiles_per_profile is not None,
                    }
                )

    return records


def write_manifest(records: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Ecrire un manifeste CSV de tuiles."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError("Aucun enregistrement de manifeste a ecrire.")
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    return output


def download_records(
    records: list[dict[str, Any]],
    output_root: str | Path | None = None,
    dry_run: bool = True,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """Telecharger les tuiles listees dans un manifeste."""
    root = Path(output_root) if output_root else data_paths()["raw_orthophotos"]
    stats: list[dict[str, Any]] = []

    for record in records:
        out_dir = root / record["profile"] / record["agglomeration"]
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"z{record['zoom']}_x{record['tile_x']}_y{record['tile_y']}.{record['extension']}"
        out_file = out_dir / filename
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "agglomeration": record["agglomeration"],
            "profile": record["profile"],
            "url": record["url"],
            "output": str(out_file),
            "status": "dry_run",
            "bytes": 0,
        }
        if dry_run:
            stats.append(entry)
            continue
        if out_file.exists():
            entry["status"] = "exists"
            entry["bytes"] = out_file.stat().st_size
            stats.append(entry)
            continue
        response = requests.get(record["url"], timeout=timeout)
        response.raise_for_status()
        out_file.write_bytes(response.content)
        entry["status"] = "downloaded"
        entry["bytes"] = len(response.content)
        stats.append(entry)

    return stats


def build_default_manifest(
    profiles: Iterable[str] | None = None,
    agglomerations: Iterable[str] | None = None,
    max_tiles_per_profile: int | None = 20,
    output_name: str = "orthophoto_wmts_manifest.csv",
) -> Path:
    """Creer un manifeste limite, utilisable depuis un notebook de cadrage."""
    ensure_data_tree()
    records = iter_tile_records(
        agglomerations=agglomerations,
        profiles=profiles,
        max_tiles_per_profile=max_tiles_per_profile,
    )
    return write_manifest(records, data_paths()["manifests"] / output_name)
