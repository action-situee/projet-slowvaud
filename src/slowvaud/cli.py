"""Interface en ligne de commande pour les donnees SlowVaud."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context import fetch_context_source, write_context_registry
from .geoadmin import download_all_agglomerations
from .orthophotos import (
    add_content_lengths,
    build_stac_manifest_records,
    download_stac_records,
    estimate_content_lengths,
    read_manifest,
    write_manifest,
)
from .paths import data_paths, ensure_data_tree, load_config


def _split_values(values: list[str] | None) -> list[str] | None:
    return values if values else None


def cmd_init(_: argparse.Namespace) -> None:
    paths = ensure_data_tree()
    for name in [
        "data",
        "raw",
        "raw_agglomerations",
        "raw_osm",
        "raw_orthophotos",
        "raw_swisstlm3d",
        "context",
        "processed",
    ]:
        path = paths[name]
        print(f"{name}: {path}")


def cmd_agglomerations(args: argparse.Namespace) -> None:
    summaries = download_all_agglomerations(source=args.source, swiss_only=not args.include_foreign)
    print(json.dumps(summaries, indent=2, ensure_ascii=False))


def _float_values(values: list[str] | None) -> list[float] | None:
    return [float(value) for value in values] if values else None


def cmd_orthophoto_manifest(args: argparse.Namespace) -> None:
    ensure_data_tree()
    records = build_stac_manifest_records(
        agglomerations=_split_values(args.agglomerations),
        boundary_source=args.boundary_source,
        gsds=_float_values(args.gsds) or [2.0, 0.1],
    )
    if args.exact_sizes:
        records = add_content_lengths(records)
    output = Path(args.output) if args.output else data_paths()["manifests"] / "orthophoto_stac_manifest.csv"
    write_manifest(records, output)
    print(f"{len(records)} assets listes: {output}")
    if args.estimate_sizes:
        estimate = estimate_content_lengths(records, sample_per_gsd=args.sample_per_gsd)
        estimate_output = data_paths()["manifests"] / "orthophoto_stac_size_estimate.json"
        estimate_output.write_text(json.dumps(estimate, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Estimation tailles: {estimate_output}")


def cmd_orthophoto_download(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest) if args.manifest else data_paths()["manifests"] / "orthophoto_stac_manifest.csv"
    records = read_manifest(manifest)
    stats = download_stac_records(
        records,
        gsds=_float_values(args.gsds),
        overwrite=args.overwrite,
    )
    output = data_paths()["manifests"] / "orthophoto_stac_download_stats.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(stats)} assets traites. Statistiques: {output}")


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

    manifest = subparsers.add_parser("orthophoto-manifest", help="Creer un manifeste STAC SWISSIMAGE")
    manifest.add_argument("--gsds", nargs="+", default=["2.0", "0.1"])
    manifest.add_argument("--agglomerations", nargs="+")
    manifest.add_argument("--boundary-source", default="vaco")
    manifest.add_argument("--estimate-sizes", action="store_true")
    manifest.add_argument("--exact-sizes", action="store_true")
    manifest.add_argument("--sample-per-gsd", type=int, default=30)
    manifest.add_argument("--output")
    manifest.set_defaults(func=cmd_orthophoto_manifest)

    download = subparsers.add_parser("orthophoto-download", help="Telecharger des assets STAC SWISSIMAGE")
    download.add_argument("--manifest")
    download.add_argument("--gsds", nargs="+")
    download.add_argument("--overwrite", action="store_true")
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
