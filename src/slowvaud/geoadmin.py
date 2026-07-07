"""Acces aux couches GeoAdmin utiles pour les agglomerations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from .paths import ensure_data_tree, load_config

FIND_URL = "https://api3.geo.admin.ch/rest/services/ech/MapServer/find"


def find_features(
    layer: str,
    search_field: str,
    search_text: str,
    *,
    contains: bool = False,
    return_geometry: bool = True,
    sr: int = 2056,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """Interroger l'endpoint GeoAdmin find pour une couche et un attribut."""
    params = {
        "layer": layer,
        "searchText": search_text,
        "searchField": search_field,
        "contains": str(contains).lower(),
        "geometryFormat": "geojson",
        "returnGeometry": str(return_geometry).lower(),
        "sr": sr,
        "lang": "fr",
    }
    response = requests.get(FIND_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    return payload.get("results", [])


def feature_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Convertir les resultats GeoAdmin en FeatureCollection GeoJSON."""
    return {"type": "FeatureCollection", "features": features}


def save_json(payload: dict[str, Any], output_path: str | Path) -> Path:
    """Ecrire un JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)
    return output


def save_feature_collection(
    features: list[dict[str, Any]],
    output_path: str | Path,
    *,
    crs: str = "EPSG:2056",
) -> Path:
    """Ecrire une FeatureCollection en fixant explicitement son CRS."""
    import geopandas as gpd

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.GeoDataFrame.from_features(features).set_crs(crs, allow_override=True)
    gdf.to_file(output, driver="GeoJSON")
    return output


def download_agglomeration_communes(
    agglo_key: str,
    source: str = "vaco",
    *,
    swiss_only: bool = True,
    config: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Telecharger les communes d'une agglomeration depuis GeoAdmin.

    Le resultat est un ensemble de communes. La dissolution en polygone unique est
    faite dans le notebook si geopandas est installe.
    """
    cfg = config or load_config()
    layer_cfg = cfg["geoadmin_layers"][source]
    agglo_cfg = cfg["agglomerations"][agglo_key]
    source_name_key = f"{source}_name"
    requested_name = agglo_cfg["geoadmin"][source_name_key]

    features = find_features(
        layer_cfg["layer"],
        layer_cfg["name_field"],
        requested_name,
        contains=False,
        return_geometry=True,
        sr=2056,
    )
    if not features:
        raise ValueError(
            f"Aucune entite GeoAdmin pour {agglo_key}: "
            f"{layer_cfg['layer']}.{layer_cfg['name_field']} = {requested_name!r}"
        )

    if swiss_only:
        allowed = set(agglo_cfg.get("country_filter", ["CH"]))
        features = [
            feature
            for feature in features
            if feature.get("properties", {}).get("land", "CH") in allowed
        ]

    paths = ensure_data_tree()
    output = paths["raw_agglomerations"] / source / f"{agglo_key}_communes.geojson"
    metadata = {
        "agglomeration": agglo_key,
        "source": source,
        "layer": layer_cfg["layer"],
        "name_field": layer_cfg["name_field"],
        "search_text": requested_name,
        "feature_count": len(features),
        "swiss_only": swiss_only,
        "source_label": layer_cfg["source_label"],
        "download_url": layer_cfg["download_url"],
        "notes": layer_cfg["notes"],
        "crs": "EPSG:2056",
        "output": str(output),
    }
    save_feature_collection(features, output, crs="EPSG:2056")
    save_json(metadata, output.with_suffix(".metadata.json"))
    return output, metadata


def download_all_agglomerations(source: str = "vaco", swiss_only: bool = True) -> list[dict[str, Any]]:
    """Telecharger les cinq agglomerations configurees."""
    cfg = load_config()
    summaries = []
    for agglo_key in cfg["agglomerations"]:
        _, metadata = download_agglomeration_communes(
            agglo_key,
            source=source,
            swiss_only=swiss_only,
            config=cfg,
        )
        summaries.append(metadata)
    return summaries
