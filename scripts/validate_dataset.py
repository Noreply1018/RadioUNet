#!/usr/bin/env python3
"""Validate the expected RadioMapSeer directory layout."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_PATHS = [
    "png/buildings_complete",
    "png/antennas",
    "gain/DPM",
    "gain/IRT2",
    "gain/IRT4",
]

OPTIONAL_PATHS = [
    "png/cars",
    "gain/carsDPM",
    "gain/carsIRT2",
    "gain/carsIRT4",
    "png/buildings_missing1",
    "png/buildings_missing2",
    "png/buildings_missing3",
    "png/buildings_missing4",
]


def count_pngs(path: Path) -> int:
    return sum(1 for _ in path.glob("*.png"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="RadioMapSeer/", help="Path to the RadioMapSeer dataset.")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.exists():
        print(f"Dataset directory does not exist: {dataset_dir}")
        return 1

    missing = []
    print(f"Dataset: {dataset_dir.resolve()}")
    print("\nRequired paths:")
    for rel in REQUIRED_PATHS:
        path = dataset_dir / rel
        if path.exists():
            print(f"  OK      {rel} ({count_pngs(path)} png files)")
        else:
            print(f"  MISSING {rel}")
            missing.append(rel)

    print("\nOptional paths:")
    for rel in OPTIONAL_PATHS:
        path = dataset_dir / rel
        if path.exists():
            print(f"  OK      {rel}")
        else:
            print(f"  absent  {rel}")

    if missing:
        print("\nDataset validation failed.")
        return 1

    print("\nDataset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

