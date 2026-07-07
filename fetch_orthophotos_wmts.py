#!/usr/bin/env python3
"""Wrapper historique pour les orthophotos WMTS SlowVaud.

Le code de reference est dans `src/slowvaud/orthophotos.py`. Ce script garde une
commande courte pour les notebooks et les usages directs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from slowvaud.orthophotos import download_records, iter_tile_records, write_manifest  # noqa: E402
from slowvaud.paths import data_paths, ensure_data_tree, load_config  # noqa: E402


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser(
        description="Creer un manifeste ou telecharger des tuiles WMTS SWISSIMAGE."
    )
    parser.add_argument(
        "--profiles",
        "--resolution",
        nargs="+",
        default=["preview"],
        choices=list(cfg["orthophoto_profiles"].keys()),
        help="Profils orthophotos. --resolution est conserve comme alias.",
    )
    parser.add_argument(
        "--cities",
        "--agglomerations",
        nargs="+",
        default=list(cfg["agglomerations"].keys()),
        choices=list(cfg["agglomerations"].keys()),
        help="Agglomerations a traiter.",
    )
    parser.add_argument(
        "--max-tiles",
        type=int,
        default=20,
        help="Limite par agglomeration et profil. Mettre 0 pour tout lister.",
    )
    parser.add_argument("--download", action="store_true", help="Telecharger les tuiles listees.")
    parser.add_argument("--dry-run", action="store_true", help="Ne pas telecharger.")
    parser.add_argument("--output", default=None, help="Chemin du manifeste CSV.")

    args = parser.parse_args()
    ensure_data_tree()
    max_tiles = None if args.max_tiles == 0 else args.max_tiles
    records = iter_tile_records(
        agglomerations=args.cities,
        profiles=args.profiles,
        max_tiles_per_profile=max_tiles,
    )

    output = Path(args.output) if args.output else data_paths()["manifests"] / "orthophoto_wmts_manifest.csv"
    write_manifest(records, output)
    print(f"Manifeste: {output}")
    print(f"Tuiles listees: {len(records)}")
    if records:
        print(f"Premiere URL: {records[0]['url']}")

    if args.download:
        stats = download_records(records, dry_run=args.dry_run)
        stats_output = data_paths()["manifests"] / "orthophoto_download_stats.json"
        stats_output.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Statistiques: {stats_output}")
    elif args.dry_run:
        print("Mode dry-run: aucun telechargement.")
    else:
        print("Aucun telechargement lance. Ajouter --download pour ecrire les images.")


if __name__ == "__main__":
    main()

