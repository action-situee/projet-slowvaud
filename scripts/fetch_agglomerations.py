#!/usr/bin/env python3
"""Telecharger les communes d'agglomeration depuis GeoAdmin."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from slowvaud.geoadmin import download_all_agglomerations  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["vaco", "g1"], default="vaco")
    parser.add_argument("--include-foreign", action="store_true")
    args = parser.parse_args()
    summaries = download_all_agglomerations(source=args.source, swiss_only=not args.include_foreign)
    for summary in summaries:
        print(
            f"{summary['agglomeration']}: {summary['feature_count']} communes "
            f"-> {summary['output']}"
        )


if __name__ == "__main__":
    main()

