#!/usr/bin/env python3
"""Telecharger ou documenter les sources de contexte configurees."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from slowvaud.context import fetch_context_source  # noqa: E402
from slowvaud.paths import load_config  # noqa: E402


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", nargs="+", default=list(cfg["context_sources"].keys()))
    args = parser.parse_args()
    for source_key in args.sources:
        output = fetch_context_source(source_key, config=cfg)
        print(f"{source_key}: {output}")


if __name__ == "__main__":
    main()

