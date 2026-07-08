"""Chemins et configuration du projet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "slowvaud_config.json"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Charger la configuration JSON du projet."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with config_path.open(encoding="utf-8") as file:
        return json.load(file)


def data_paths(root: str | Path | None = None) -> dict[str, Path]:
    """Retourner les dossiers de donnees utilises par les notebooks et scripts."""
    base = Path(root) if root else PROJECT_ROOT
    data = base / "data"
    return {
        "root": base,
        "data": data,
        "raw": data / "raw",
        "raw_agglomerations": data / "raw" / "agglomerations",
        "raw_osm": data / "raw" / "osm",
        "raw_orthophotos": data / "raw" / "orthophotos",
        "raw_swisstlm3d": data / "raw" / "swisstlm3d",
        "context": data / "context",
        "manifests": data / "manifests",
        "processed": data / "processed",
        "exports": base / "exports",
    }


def ensure_data_tree(root: str | Path | None = None) -> dict[str, Path]:
    """Creer les dossiers de travail s'ils n'existent pas."""
    paths = data_paths(root)
    for key, path in paths.items():
        if key not in {"root", "manifests"}:
            path.mkdir(parents=True, exist_ok=True)
    return paths


def agglomeration_items(config: dict[str, Any] | None = None) -> list[tuple[str, dict[str, Any]]]:
    """Lister les agglomerations dans l'ordre de la configuration."""
    cfg = config or load_config()
    return list(cfg["agglomerations"].items())
