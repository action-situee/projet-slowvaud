"""Manifestes et telechargement STAC SWISSIMAGE."""

from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import requests
from shapely.geometry import shape

from .paths import data_paths, ensure_data_tree, load_config

STAC_COLLECTION_ID = "ch.swisstopo.swissimage-dop10"
STAC_COLLECTION_URL = (
    "https://data.geo.admin.ch/api/stac/v0.9/collections/"
    "ch.swisstopo.swissimage-dop10"
)
STAC_ITEMS_URL = f"{STAC_COLLECTION_URL}/items"
ORTHOPHOTO_CRS = "EPSG:2056"
STAC_CRS = "EPSG:4326"
DEFAULT_GSDS = (2.0, 0.1)


def _next_link(payload: dict[str, Any]) -> str | None:
    for link in payload.get("links", []):
        if link.get("rel") == "next":
            return link["href"]
    return None


def _bbox_param(bounds: Iterable[float]) -> str:
    return ",".join(str(round(float(value), 7)) for value in bounds)


def stac_items_for_bbox(
    bbox_wgs84: tuple[float, float, float, float],
    *,
    limit: int = 500,
    timeout: int = 60,
) -> list[dict[str, Any]]:
    """Recuperer les items STAC intersectant une emprise WGS84."""
    url: str | None = STAC_ITEMS_URL
    params: dict[str, Any] | None = {
        "bbox": _bbox_param(bbox_wgs84),
        "limit": limit,
    }
    items: list[dict[str, Any]] = []

    while url:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        items.extend(payload.get("features", []))
        url = _next_link(payload)
        params = None

    return items


def _load_boundary_lv95(agglo_key: str, source: str) -> Any:
    import geopandas as gpd

    boundary_path = (
        data_paths()["processed"]
        / "agglomerations"
        / source
        / f"{agglo_key}_dissolved.geojson"
    )
    if not boundary_path.exists():
        raise FileNotFoundError(
            f"Perimetre d'agglomeration manquant: {boundary_path}. "
            "Executer 02_agglomerations_shapes.ipynb avant les orthophotos."
        )

    boundary = gpd.read_file(boundary_path)
    if str(boundary.crs) != ORTHOPHOTO_CRS:
        raise ValueError(f"CRS inattendu pour {boundary_path}: {boundary.crs}")
    return boundary.geometry.union_all()


def _items_intersecting_boundary(
    items: list[dict[str, Any]],
    boundary_lv95: Any,
) -> list[dict[str, Any]]:
    import geopandas as gpd

    rows = [
        {
            "item_id": item["id"],
            "datetime": item.get("properties", {}).get("datetime"),
            "geometry": shape(item["geometry"]),
            "assets": item.get("assets", {}),
        }
        for item in items
    ]
    if not rows:
        return []

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=STAC_CRS).to_crs(ORTHOPHOTO_CRS)
    gdf = gdf[gdf.intersects(boundary_lv95)].copy()
    gdf["intersection_area_m2"] = gdf.geometry.intersection(boundary_lv95).area.round(2)
    return gdf.to_dict("records")


def _asset_output_path(asset_href: str, gsd: float) -> str:
    filename = asset_href.rsplit("/", 1)[-1]
    gsd_key = str(gsd).replace(".", "_")
    return str(Path("data") / "raw" / "orthophotos" / STAC_COLLECTION_ID / f"gsd_{gsd_key}" / filename)


def build_stac_manifest_records(
    *,
    agglomerations: Iterable[str] | None = None,
    boundary_source: str = "vaco",
    gsds: Iterable[float] = DEFAULT_GSDS,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Construire le manifeste des GeoTIFF SWISSIMAGE couvrant les agglomerations."""
    import geopandas as gpd

    cfg = config or load_config()
    requested_agglos = list(agglomerations or cfg["agglomerations"].keys())
    requested_gsds = {round(float(gsd), 3) for gsd in gsds}
    records: list[dict[str, Any]] = []

    for agglo_key in requested_agglos:
        boundary_lv95 = _load_boundary_lv95(agglo_key, boundary_source)
        boundary_wgs84 = gpd.GeoSeries([boundary_lv95], crs=ORTHOPHOTO_CRS).to_crs(STAC_CRS)
        bbox_wgs84 = tuple(float(value) for value in boundary_wgs84.total_bounds)
        items = stac_items_for_bbox(bbox_wgs84)
        intersecting_items = _items_intersecting_boundary(items, boundary_lv95)

        for item in intersecting_items:
            minx, miny, maxx, maxy = item["geometry"].bounds
            for asset_key, asset in item["assets"].items():
                gsd = round(float(asset.get("eo:gsd", -1)), 3)
                if gsd not in requested_gsds:
                    continue
                href = asset["href"]
                records.append(
                    {
                        "agglomeration": agglo_key,
                        "agglomeration_label": cfg["agglomerations"][agglo_key]["label"],
                        "collection": STAC_COLLECTION_ID,
                        "source": STAC_COLLECTION_URL,
                        "item_id": item["item_id"],
                        "datetime": item["datetime"],
                        "asset_key": asset_key,
                        "gsd": gsd,
                        "proj_epsg": asset.get("proj:epsg"),
                        "asset_type": asset.get("type"),
                        "checksum_multihash": asset.get("checksum:multihash"),
                        "href": href,
                        "output_path": _asset_output_path(href, gsd),
                        "item_bounds_lv95": json.dumps([minx, miny, maxx, maxy]),
                        "intersection_area_m2": item["intersection_area_m2"],
                    }
                )

    records.sort(key=lambda row: (row["agglomeration"], row["gsd"], row["item_id"]))
    return records


def write_manifest(records: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Ecrire un manifeste CSV."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError("Aucun enregistrement de manifeste a ecrire.")
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    return output


def read_manifest(path: str | Path) -> list[dict[str, Any]]:
    """Lire un manifeste CSV."""
    with Path(path).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _head_size(record: dict[str, Any], timeout: int) -> dict[str, Any]:
    result = dict(record)
    response = requests.head(record["href"], allow_redirects=True, timeout=timeout)
    response.raise_for_status()
    result["content_length_bytes"] = int(response.headers["content-length"])
    return result


def add_content_lengths(
    records: list[dict[str, Any]],
    *,
    timeout: int = 30,
    max_workers: int = 12,
) -> list[dict[str, Any]]:
    """Ajouter les tailles HTTP Content-Length au manifeste."""
    by_href = {record["href"]: record for record in records}
    sizes: dict[str, int] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_head_size, record, timeout): href
            for href, record in by_href.items()
        }
        for future in as_completed(futures):
            href = futures[future]
            sizes[href] = int(future.result()["content_length_bytes"])

    output: list[dict[str, Any]] = []
    for record in records:
        enriched = dict(record)
        enriched["content_length_bytes"] = sizes[record["href"]]
        output.append(enriched)
    return output


def estimate_content_lengths(
    records: list[dict[str, Any]],
    *,
    sample_per_gsd: int = 30,
    timeout: int = 20,
    max_workers: int = 8,
) -> dict[str, Any]:
    """Estimer les volumes par resolution a partir d'un echantillon HEAD."""
    unique: dict[str, dict[str, Any]] = {}
    for record in records:
        unique.setdefault(record["href"], record)

    by_gsd: dict[float, list[dict[str, Any]]] = {}
    for record in unique.values():
        by_gsd.setdefault(round(float(record["gsd"]), 3), []).append(record)

    summary: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    for gsd, gsd_records in sorted(by_gsd.items()):
        ordered = sorted(gsd_records, key=lambda record: record["href"])
        if len(ordered) <= sample_per_gsd:
            sample = ordered
        else:
            step = (len(ordered) - 1) / (sample_per_gsd - 1)
            indexes = sorted({round(index * step) for index in range(sample_per_gsd)})
            sample = [ordered[index] for index in indexes]

        sample_with_sizes = add_content_lengths(
            sample,
            timeout=timeout,
            max_workers=max_workers,
        )
        sizes = [int(record["content_length_bytes"]) for record in sample_with_sizes]
        mean_size = sum(sizes) / len(sizes)
        estimated_total = mean_size * len(ordered)
        summary.append(
            {
                "gsd": gsd,
                "asset_count": len(ordered),
                "sample_count": len(sizes),
                "sample_min_bytes": min(sizes),
                "sample_mean_bytes": round(mean_size),
                "sample_max_bytes": max(sizes),
                "estimated_total_bytes": round(estimated_total),
            }
        )
        samples.extend(sample_with_sizes)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "method": "deterministic_head_sample_by_gsd",
        "sample_per_gsd": sample_per_gsd,
        "summary": summary,
        "samples": samples,
    }


def _download_one_stac_record(
    record: dict[str, Any],
    *,
    root: Path,
    timeout: int,
    overwrite: bool,
) -> dict[str, Any]:
    gsd = round(float(record["gsd"]), 3)
    output = root / record["output_path"]
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_suffix(output.suffix + ".part")
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "collection": record["collection"],
        "item_id": record["item_id"],
        "gsd": gsd,
        "href": record["href"],
        "output": str(output),
        "status": "pending",
        "bytes": 0,
    }

    if output.exists() and not overwrite:
        entry["status"] = "exists"
        entry["bytes"] = output.stat().st_size
        return entry

    response = requests.get(record["href"], stream=True, timeout=timeout)
    response.raise_for_status()
    bytes_written = 0
    with part.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)
                bytes_written += len(chunk)
    part.replace(output)
    entry["status"] = "downloaded"
    entry["bytes"] = bytes_written
    return entry


def download_stac_records(
    records: list[dict[str, Any]],
    *,
    gsds: Iterable[float] | None = None,
    output_root: str | Path | None = None,
    timeout: int = 120,
    overwrite: bool = False,
    max_workers: int = 12,
) -> list[dict[str, Any]]:
    """Telecharger les assets STAC references dans un manifeste."""
    root = Path(output_root) if output_root else data_paths()["root"]
    requested_gsds = {round(float(gsd), 3) for gsd in gsds} if gsds else None
    unique_records: dict[Path, dict[str, Any]] = {}

    for record in records:
        gsd = round(float(record["gsd"]), 3)
        if requested_gsds is not None and gsd not in requested_gsds:
            continue
        output = root / record["output_path"]
        unique_records.setdefault(output, record)

    stats: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                _download_one_stac_record,
                record,
                root=root,
                timeout=timeout,
                overwrite=overwrite,
            )
            for record in unique_records.values()
        ]
        for future in as_completed(futures):
            stats.append(future.result())

    return sorted(stats, key=lambda row: row["output"])
