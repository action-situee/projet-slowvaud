"""Interface en ligne de commande pour les donnees SlowVaud."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context import fetch_context_source, write_context_registry
from .geoadmin import download_all_agglomerations
from .orthophotos import download_records, iter_tile_records, write_manifest
from .paths import data_paths, ensure_data_tree, load_config


def _split_values(values: list[str] | None) -> list[str] | None:
    return values if values else None


def cmd_init(_: argparse.Namespace) -> None:
    paths = ensure_data_tree()
    for name, path in paths.items():
        print(f"{name}: {path}")


def cmd_agglomerations(args: argparse.Namespace) -> None:
    summaries = download_all_agglomerations(source=args.source, swiss_only=not args.include_foreign)
    print(json.dumps(summaries, indent=2, ensure_ascii=False))


def cmd_orthophoto_manifest(args: argparse.Namespace) -> None:
    ensure_data_tree()
    records = iter_tile_records(
        agglomerations=_split_values(args.agglomerations),
        profiles=_split_values(args.profiles),
        max_tiles_per_profile=args.max_tiles,
    )
    output = Path(args.output) if args.output else data_paths()["manifests"] / "orthophoto_wmts_manifest.csv"
    write_manifest(records, output)
    print(f"{len(records)} tuiles listees: {output}")


def cmd_orthophoto_download(args: argparse.Namespace) -> None:
    records = iter_tile_records(
        agglomerations=_split_values(args.agglomerations),
        profiles=_split_values(args.profiles),
        max_tiles_per_profile=args.max_tiles,
    )
    stats = download_records(records, dry_run=args.dry_run)
    output = data_paths()["manifests"] / "orthophoto_download_stats.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(stats)} tuiles traitees. Statistiques: {output}")


def cmd_context_registry(_: argparse.Namespace) -> None:
    output = write_context_registry()
    print(output)


def cmd_context_fetch(args: argparse.Namespace) -> None:
    cfg = load_config()
    keys = args.sources or list(cfg["context_sources"].keys())
    for source_key in keys:
        output = fetch_context_source(source_key, config=cfg)
        print(f"{source_key}: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preparation des donnees SlowVaud")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Creer l'arborescence de donnees")
    init.set_defaults(func=cmd_init)

    aggs = subparsers.add_parser("agglomerations", help="Telecharger les communes d'agglomeration")
    aggs.add_argument("--source", choices=["vaco", "g1"], default="vaco")
    aggs.add_argument("--include-foreign", action="store_true")
    aggs.set_defaults(func=cmd_agglomerations)

    manifest = subparsers.add_parser("orthophoto-manifest", help="Creer un manifeste WMTS")
    manifest.add_argument("--profiles", nargs="+")
    manifest.add_argument("--agglomerations", nargs="+")
    manifest.add_argument("--max-tiles", type=int, default=20)
    manifest.add_argument("--output")
    manifest.set_defaults(func=cmd_orthophoto_manifest)

    download = subparsers.add_parser("orthophoto-download", help="Telecharger des tuiles WMTS")
    download.add_argument("--profiles", nargs="+")
    download.add_argument("--agglomerations", nargs="+")
    download.add_argument("--max-tiles", type=int, default=20)
    download.add_argument("--dry-run", action="store_true")
    download.set_defaults(func=cmd_orthophoto_download)

    registry = subparsers.add_parser("context-registry", help="Exporter le registre de contexte")
    registry.set_defaults(func=cmd_context_registry)

    context = subparsers.add_parser("context-fetch", help="Telecharger ou documenter les contextes")
    context.add_argument("--sources", nargs="+")
    context.set_defaults(func=cmd_context_fetch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

