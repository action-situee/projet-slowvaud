"""Sources cantonales et communales de contexte cyclable."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from .paths import data_paths, ensure_data_tree, load_config


def context_sources(config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Lister les sources de contexte configurees."""
    cfg = config or load_config()
    return cfg["context_sources"]


def download_arcgis_feature_server(
    service_url: str,
    layer_id: int = 0,
    *,
    where: str = "1=1",
    page_size: int = 2000,
    timeout: int = 60,
) -> dict[str, Any]:
    """Telecharger une couche ArcGIS FeatureServer en GeoJSON avec pagination."""
    query_url = f"{service_url.rstrip('/')}/{layer_id}/query"
    features: list[dict[str, Any]] = []
    offset = 0

    while True:
        params = {
            "where": where,
            "outFields": "*",
            "f": "geojson",
            "outSR": 4326,
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "returnGeometry": "true",
        }
        response = requests.get(query_url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("features", [])
        features.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    return {"type": "FeatureCollection", "features": features}


def fetch_context_source(source_key: str, *, config: dict[str, Any] | None = None) -> Path:
    """Telecharger ou documenter une source de contexte selon son type."""
    cfg = config or load_config()
    source = cfg["context_sources"][source_key]
    paths = ensure_data_tree()
    output_dir = paths["context"] / source["agglomeration"]
    output_dir.mkdir(parents=True, exist_ok=True)

    if source["type"] == "arcgis_feature_server":
        payload = download_arcgis_feature_server(source["service_url"], int(source.get("layer_id", 0)))
        output = output_dir / f"{source_key}.geojson"
        with output.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False)
        metadata_output = output.with_suffix(".metadata.json")
        with metadata_output.open("w", encoding="utf-8") as file:
            json.dump(source, file, indent=2, ensure_ascii=False)
        return output

    output = output_dir / f"{source_key}.todo.json"
    with output.open("w", encoding="utf-8") as file:
        json.dump(source, file, indent=2, ensure_ascii=False)
    return output


def write_context_registry(output_path: str | Path | None = None) -> Path:
    """Exporter le registre des sources de contexte en JSON."""
    paths = ensure_data_tree()
    output = Path(output_path) if output_path else paths["manifests"] / "context_sources_registry.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(context_sources(), file, indent=2, ensure_ascii=False)
    return output
