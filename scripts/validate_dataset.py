#!/usr/bin/env python3
"""Validate the expected RadioMapSeer directory layout and sample integrity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from skimage import io


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


def image_stats(path: Path) -> dict:
    arr = np.asarray(io.imread(path))
    return {
        "path": str(path),
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "unique_count": int(np.unique(arr).size),
    }


def expected_file(dataset_dir: Path, rel_dir: str, name: str) -> Path:
    return dataset_dir / rel_dir / name


def validate_sample(dataset_dir: Path, map_id: int, tx_id: int) -> tuple[list[str], dict]:
    errors: list[str] = []
    map_name = f"{map_id}.png"
    tx_name = f"{map_id}_{tx_id}.png"
    files = {
        "buildings": expected_file(dataset_dir, "png/buildings_complete", map_name),
        "antenna": expected_file(dataset_dir, "png/antennas", tx_name),
        "dpm": expected_file(dataset_dir, "gain/DPM", tx_name),
        "irt2": expected_file(dataset_dir, "gain/IRT2", tx_name),
    }
    irt4 = expected_file(dataset_dir, "gain/IRT4", tx_name)
    if irt4.exists():
        files["irt4"] = irt4

    stats = {"map_id": map_id, "tx_id": tx_id, "files": {}}
    for key, path in files.items():
        if not path.exists():
            errors.append(f"missing sample file: {path}")
            continue
        try:
            file_stats = image_stats(path)
            stats["files"][key] = file_stats
            shape = file_stats["shape"]
            if shape[:2] != [256, 256]:
                errors.append(f"unexpected shape for {path}: {shape}")
        except Exception as exc:
            errors.append(f"failed to read {path}: {exc}")

    return errors, stats


def write_reports(report: dict, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "dataset_validation.json"
    md_path = report_dir / "dataset_validation.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# RadioMapSeer 数据集校验报告",
        "",
        f"- dataset_dir: `{report['dataset_dir']}`",
        f"- passed: `{report['passed']}`",
        "",
        "## 必要目录",
    ]
    for item in report["required_paths"]:
        lines.append(f"- {item['status']}: `{item['path']}`，png={item.get('png_count', 0)}")
    lines.extend(["", "## 可选目录"])
    for item in report["optional_paths"]:
        lines.append(f"- {item['status']}: `{item['path']}`")
    lines.extend(["", "## 样本检查", "```json", json.dumps(report["sample"], ensure_ascii=False, indent=2), "```"])
    if report["errors"]:
        lines.extend(["", "## 错误"])
        lines.extend(f"- {err}" for err in report["errors"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n已写入报告: {json_path}")
    print(f"已写入报告: {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="RadioMapSeer/", help="Path to the RadioMapSeer dataset.")
    parser.add_argument("--sample-map", type=int, default=1, help="Map id to validate, using dataset file naming.")
    parser.add_argument("--sample-tx", type=int, default=0, help="Tx id to validate.")
    parser.add_argument("--report-dir", default="reports/dataset_validation", help="Directory for JSON/Markdown reports.")
    parser.add_argument("--no-report", action="store_true", help="Do not write reports.")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    report = {
        "dataset_dir": str(dataset_dir.resolve()),
        "required_paths": [],
        "optional_paths": [],
        "sample": {},
        "errors": [],
        "passed": False,
    }
    if not dataset_dir.exists():
        print(f"Dataset directory does not exist: {dataset_dir}")
        report["errors"].append(f"dataset directory does not exist: {dataset_dir}")
        if not args.no_report:
            write_reports(report, Path(args.report_dir))
        return 1

    missing = []
    print(f"Dataset: {dataset_dir.resolve()}")
    print("\nRequired paths:")
    for rel in REQUIRED_PATHS:
        path = dataset_dir / rel
        if path.exists():
            png_count = count_pngs(path)
            print(f"  OK      {rel} ({png_count} png files)")
            report["required_paths"].append({"path": rel, "status": "OK", "png_count": png_count})
        else:
            print(f"  MISSING {rel}")
            report["required_paths"].append({"path": rel, "status": "MISSING", "png_count": 0})
            missing.append(rel)

    print("\nOptional paths:")
    for rel in OPTIONAL_PATHS:
        path = dataset_dir / rel
        if path.exists():
            print(f"  OK      {rel}")
            report["optional_paths"].append({"path": rel, "status": "OK"})
        else:
            print(f"  absent  {rel}")
            report["optional_paths"].append({"path": rel, "status": "absent"})

    sample_errors, sample_stats = validate_sample(dataset_dir, args.sample_map, args.sample_tx)
    report["sample"] = sample_stats
    report["errors"].extend(sample_errors)

    if sample_errors:
        print("\nSample validation errors:")
        for err in sample_errors:
            print(f"  {err}")
    else:
        print(f"\nSample validation passed for map={args.sample_map}, tx={args.sample_tx}.")

    if missing:
        report["errors"].extend(f"missing required directory: {rel}" for rel in missing)
        print("\nDataset validation failed.")
        if not args.no_report:
            write_reports(report, Path(args.report_dir))
        return 1

    if sample_errors:
        print("\nDataset validation failed.")
        if not args.no_report:
            write_reports(report, Path(args.report_dir))
        return 1

    report["passed"] = True
    print("\nDataset validation passed.")
    if not args.no_report:
        write_reports(report, Path(args.report_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
