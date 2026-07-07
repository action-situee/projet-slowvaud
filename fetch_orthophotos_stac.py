#!/usr/bin/env python3
"""Construire le manifeste ou telecharger les GeoTIFF SWISSIMAGE via STAC."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from slowvaud.orthophotos import (  # noqa: E402
    add_content_lengths,
    build_stac_manifest_records,
    download_stac_records,
    estimate_content_lengths,
    read_manifest,
    write_manifest,
)
from slowvaud.paths import data_paths, ensure_data_tree, load_config  # noqa: E402


def _parse_gsds(values: list[str]) -> list[float]:
    return [float(value) for value in values]


def _format_gib(bytes_count: int | float) -> str:
    return f"{bytes_count / 1024**3:.1f} GiB"


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser(
        description="Manifeste et telechargement GeoTIFF/COG SWISSIMAGE par STAC."
    )
    parser.add_argument(
        "--agglomerations",
        nargs="+",
        default=list(cfg["agglomerations"].keys()),
        choices=list(cfg["agglomerations"].keys()),
    )
    parser.add_argument("--boundary-source", default="vaco")
    parser.add_argument("--gsds", nargs="+", default=["2.0", "0.1"])
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--estimate-sizes", action="store_true")
    parser.add_argument("--exact-sizes", action="store_true")
    parser.add_argument("--sample-per-gsd", type=int, default=30)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--download-workers", type=int, default=12)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--min-free-gib",
        type=float,
        default=20.0,
        help="Espace libre minimal a conserver si les tailles sont connues.",
    )
    args = parser.parse_args()

    paths = ensure_data_tree()
    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else paths["manifests"] / "orthophoto_stac_manifest.csv"
    )
    gsds = _parse_gsds(args.gsds)

    records = build_stac_manifest_records(
        agglomerations=args.agglomerations,
        boundary_source=args.boundary_source,
        gsds=gsds,
    )
    if args.exact_sizes:
        records = add_content_lengths(records)

    write_manifest(records, manifest_path)
    print(f"Manifeste: {manifest_path}")
    print(f"Assets listes: {len(records)}")

    size_estimate = None
    if args.estimate_sizes:
        size_estimate = estimate_content_lengths(records, sample_per_gsd=args.sample_per_gsd)
        estimate_path = paths["manifests"] / "orthophoto_stac_size_estimate.json"
        estimate_path.write_text(json.dumps(size_estimate, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Estimation tailles: {estimate_path}")
        for row in size_estimate["summary"]:
            print(
                f"  gsd {row['gsd']}: {row['asset_count']} assets, "
                f"estimation {_format_gib(row['estimated_total_bytes'])}"
            )

    if records and "content_length_bytes" in records[0]:
        total = sum(int(record["content_length_bytes"]) for record in records)
        print(f"Taille cumulee par agglomeration: {_format_gib(total)}")
        by_gsd: dict[float, int] = {}
        for record in records:
            by_gsd.setdefault(float(record["gsd"]), 0)
            by_gsd[float(record["gsd"])] += int(record["content_length_bytes"])
        for gsd, bytes_count in sorted(by_gsd.items()):
            print(f"  gsd {gsd}: {_format_gib(bytes_count)}")

    if not args.download:
        return

    records = read_manifest(manifest_path)
    if records and "content_length_bytes" in records[0]:
        total = sum(int(record["content_length_bytes"]) for record in records)
    elif size_estimate:
        total = sum(int(row["estimated_total_bytes"]) for row in size_estimate["summary"])
    else:
        total = None

    if total is not None:
        free = shutil.disk_usage(paths["root"]).free
        reserve = args.min_free_gib * 1024**3
        if total > max(free - reserve, 0):
            raise RuntimeError(
                "Espace disque insuffisant pour le telechargement demande. "
                f"Besoin estime: {_format_gib(total)}, libre: {_format_gib(free)}, "
                f"reserve demandee: {args.min_free_gib:.1f} GiB."
            )

    stats = download_stac_records(
        records,
        gsds=gsds,
        overwrite=args.overwrite,
        max_workers=args.download_workers,
    )
    stats_path = paths["manifests"] / "orthophoto_stac_download_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Statistiques: {stats_path}")


if __name__ == "__main__":
    main()
