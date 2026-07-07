"""Extraction OSM des infrastructures cyclables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import data_paths, ensure_data_tree, load_config


def read_vector_with_crs(path: str | Path, crs: str):
    """Lire un vecteur en appliquant le CRS attendu par le contrat de donnees."""
    import geopandas as gpd

    gdf = gpd.read_file(path)
    return gdf.set_crs(crs, allow_override=True)


def cycling_tag_queries(config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Retourner les requetes de tags OSM configurees."""
    cfg = config or load_config()
    return cfg["osm"]["tags"]


def normalize_osm_class(properties: dict[str, Any]) -> str:
    """Classifier grossierement un objet OSM cyclable pour les labels faibles."""
    highway = properties.get("highway")
    bicycle = properties.get("bicycle")
    cycleway_values = [
        properties.get("cycleway"),
        properties.get("cycleway:left"),
        properties.get("cycleway:right"),
        properties.get("cycleway:both"),
    ]

    if highway == "cycleway":
        return "piste_cyclable_dediee"
    if any(value in {"track", "opposite_track"} for value in cycleway_values):
        return "piste_cyclable_associee_chaussee"
    if any(value in {"lane", "opposite_lane"} for value in cycleway_values):
        return "bande_cyclable"
    if any(value in {"shared_lane", "share_busway"} for value in cycleway_values):
        return "voie_partagee_marquee"
    if bicycle == "designated":
        return "itineraire_ou_acces_velo_designe"
    return "contexte_cyclable_osm"


def extract_osm_for_agglomeration(
    agglo_key: str,
    boundary_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    boundary_crs: str = "EPSG:2056",
    tags: dict[str, Any] | None = None,
) -> Path:
    """Extraire les objets OSM cyclables dans une emprise d'agglomeration.

    Cette fonction requiert geopandas et osmnx. Elle reste importable sans ces
    dependances pour que les notebooks de cadrage puissent tourner partiellement.
    """
    try:
        import osmnx as ox
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise ImportError(
            "Installer les dependances geospatiales: pip install -e . ou "
            "pip install geopandas osmnx shapely pyproj"
        ) from exc

    cfg = load_config()
    query_tags = tags or {}
    if not query_tags:
        query_tags = {}
        for tag_group in cfg["osm"]["tags"].values():
            query_tags.update(tag_group)

    boundary = read_vector_with_crs(boundary_path, boundary_crs)
    polygon_wgs84 = boundary.to_crs(4326).geometry.union_all()
    features = ox.features_from_polygon(polygon_wgs84, tags=query_tags)
    if features.empty:
        raise ValueError(f"Aucun objet OSM cyclable trouve pour {agglo_key}.")

    features = features.reset_index()
    features["agglo_key"] = agglo_key
    features["osm_cycle_class"] = [
        normalize_osm_class(row.drop(labels=["geometry"], errors="ignore").to_dict())
        for _, row in features.iterrows()
    ]

    paths = ensure_data_tree()
    out_root = Path(output_dir) if output_dir else paths["raw_osm"]
    out_root.mkdir(parents=True, exist_ok=True)
    output = out_root / f"osm_cycle_context_{agglo_key}.geojson"
    features.to_file(output, driver="GeoJSON")
    return output


def dissolve_agglomeration_communes(input_path: str | Path, output_path: str | Path) -> Path:
    """Dissoudre les communes d'agglomeration en une geometrie unique."""
    gdf = read_vector_with_crs(input_path, "EPSG:2056")
    if gdf.empty:
        raise ValueError(f"Fichier vide: {input_path}")
    group_field = "agglo_name" if "agglo_name" in gdf.columns else "aname"
    dissolved = gdf.dissolve(by=group_field, as_index=False)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dissolved.to_file(output, driver="GeoJSON")
    return output
