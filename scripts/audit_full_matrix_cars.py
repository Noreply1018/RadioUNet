#!/usr/bin/env python3
"""Audit cars-scenario full-matrix artifacts."""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataset
from radiounet.utils import git_metadata, load_yaml, require_dataset_dir, save_json

OUT_DIR = ROOT / "reports/full_matrix"
RUNS = {
    "c_dpmcars_thr2": "configs/c_dpmcars_thr2.yaml",
    "c_irt2cars_thr2": "configs/c_irt2cars_thr2.yaml",
    "s_dpmcars_carinput_thr2_rand1_300": "configs/s_dpmcars_carinput_thr2_rand1_300.yaml",
    "s_irt2cars_carinput_thr2_rand1_300": "configs/s_irt2cars_carinput_thr2_rand1_300.yaml",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_numbers(value: Any, prefix: str = "") -> dict[str, float]:
    if isinstance(value, bool):
        return {}
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return {prefix: float(value)}
    if isinstance(value, dict):
        out: dict[str, float] = {}
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_numbers(child, child_prefix))
        return out
    return {}


def max_abs_diff(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_nums = flatten_numbers(left)
    right_nums = flatten_numbers(right)
    diffs = [
        abs(left_nums[key] - right_nums[key])
        for key in set(left_nums) & set(right_nums)
        if key != "seconds" and not key.endswith(".seconds")
    ]
    return max(diffs) if diffs else 0.0


def no_cars_config(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    cfg["data"]["cars_simulation"] = "no"
    cfg["data"]["cars_input"] = "no"
    return cfg


def first_item(config: dict[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
    ds = build_dataset(config, "test", smoke=True)
    item = ds[0]
    return item[0], item[1]


def loader_audit(config_path: Path) -> dict[str, Any]:
    cfg = load_yaml(config_path)
    require_dataset_dir(cfg)
    cars_inputs, cars_target = first_item(cfg)
    clean_inputs, clean_target = first_item(no_cars_config(cfg))
    cars_channel = None
    if cfg["data"].get("cars_input") == "yes":
        cars_channel = cars_inputs[-1]
    ds = build_dataset(cfg, "test", smoke=True)
    dataset_dir = ROOT / cfg["data"]["dataset_dir"]
    evidence = {
        "cars_dpm_dir": str((dataset_dir / "gain/carsDPM").relative_to(ROOT)),
        "cars_irt2_dir": str((dataset_dir / "gain/carsIRT2").relative_to(ROOT)),
        "cars_irt4_dir": str((dataset_dir / "gain/carsIRT4").relative_to(ROOT)),
        "cars_png_dir": str((dataset_dir / "png/cars").relative_to(ROOT)),
        "target_dir_from_loader": getattr(ds, "dir_gain", None),
        "cars_input_dir_from_loader": getattr(ds, "dir_cars", None),
    }
    return {
        "config": str(config_path.relative_to(ROOT)),
        "loader": cfg["data"]["loader"],
        "simulation": cfg["data"]["simulation"],
        "cars_simulation": cfg["data"].get("cars_simulation"),
        "cars_input": cfg["data"].get("cars_input"),
        "input_shape": list(cars_inputs.shape),
        "target_shape": list(cars_target.shape),
        "target_diff_vs_no_cars_max": float(torch.abs(cars_target - clean_target).max().item()),
        "target_diff_vs_no_cars_mean": float(torch.abs(cars_target - clean_target).mean().item()),
        "cars_input_nonzero": None if cars_channel is None else int((cars_channel != 0).sum().item()),
        "cars_input_max": None if cars_channel is None else float(cars_channel.max().item()),
        "evidence": evidence,
    }


def collect(name: str) -> dict[str, Any]:
    config_path = ROOT / RUNS[name]
    cfg = load_yaml(config_path)
    run_dir = OUT_DIR / f"{name}_50ep"
    row: dict[str, Any] = {
        "name": name,
        "config": str(config_path.relative_to(ROOT)),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "exists": run_dir.exists(),
        "model": "S" if cfg["data"]["loader"] == "RadioUNet_s" else "C",
        "simulation": cfg["data"]["simulation"],
        "cars_simulation": cfg["data"].get("cars_simulation"),
        "cars_input": cfg["data"].get("cars_input"),
        "loader_audit": loader_audit(config_path),
    }
    if not run_dir.exists():
        row["gate"] = False
        return row
    for phase in ["firstU", "secondU"]:
        metrics_path = run_dir / f"{phase}_test_metrics.json"
        rerun_path = run_dir / f"{phase}_test_metrics_rerun.json"
        row[f"{phase}_metrics_exists"] = metrics_path.exists()
        row[f"{phase}_rerun_exists"] = rerun_path.exists()
        if metrics_path.exists() and rerun_path.exists():
            metrics = load_json(metrics_path)
            rerun = load_json(rerun_path)
            row[f"{phase}_rerun_max_abs_diff"] = max_abs_diff(metrics, rerun)
            row[f"{phase}_mse"] = metrics[phase]["mse"] if phase in metrics else metrics["secondU"]["mse"]
            row[f"{phase}_metrics_git_dirty"] = metrics.get("git", {}).get("dirty")
    history_ok = {}
    for phase in ["firstU", "secondU"]:
        history_path = run_dir / f"{phase}_history.json"
        if history_path.exists():
            history = load_json(history_path).get("history", [])
            history_ok[phase] = {
                "train_entries": sum(1 for item in history if item.get("split") == "train"),
                "val_entries": sum(1 for item in history if item.get("split") == "val"),
            }
    row["history"] = history_ok
    figures = sorted((run_dir / "figures").glob("*.png"))
    row["figure_count"] = len(figures)
    row["figures_nonempty"] = all(path.stat().st_size > 0 for path in figures)
    row["manifest_exists"] = (run_dir / "cars_run_manifest.json").exists()
    row["secondU_not_worse_than_firstU"] = (
        row.get("firstU_mse") is not None
        and row.get("secondU_mse") is not None
        and row["secondU_mse"] <= row["firstU_mse"]
    )
    la = row["loader_audit"]
    row["gate"] = all(
        [
            row["cars_simulation"] == "yes",
            la["target_diff_vs_no_cars_max"] > 0.0,
            row["cars_input"] != "yes" or (la["cars_input_nonzero"] or 0) > 0,
            row.get("firstU_metrics_exists"),
            row.get("secondU_metrics_exists"),
            row.get("firstU_rerun_exists"),
            row.get("secondU_rerun_exists"),
            row.get("firstU_rerun_max_abs_diff") == 0.0,
            row.get("secondU_rerun_max_abs_diff") == 0.0,
            row.get("firstU_metrics_git_dirty") is False,
            row.get("secondU_metrics_git_dirty") is False,
            row["history"].get("firstU", {}).get("train_entries") == 50,
            row["history"].get("firstU", {}).get("val_entries") == 50,
            row["history"].get("secondU", {}).get("train_entries") == 50,
            row["history"].get("secondU", {}).get("val_entries") == 50,
            row.get("figure_count") == 8,
            row.get("figures_nonempty"),
            row.get("manifest_exists"),
            row.get("secondU_not_worse_than_firstU"),
        ]
    )
    return row


def dataset_availability() -> dict[str, Any]:
    dataset_dir = ROOT / "RadioMapSeer"
    dirs = {
        "carsDPM": dataset_dir / "gain/carsDPM",
        "carsIRT2": dataset_dir / "gain/carsIRT2",
        "carsIRT4": dataset_dir / "gain/carsIRT4",
        "cars_png": dataset_dir / "png/cars",
    }
    return {
        key: {
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "file_count": sum(1 for item in path.glob("*") if item.is_file()) if path.exists() else 0,
        }
        for key, path in dirs.items()
    }


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# Cars 场景全矩阵审计",
        "",
        f"- gate：`{audit['gate']['pass']}`。",
        "- 覆盖：DPM/IRT2 cars simulation；C baseline 无 cars input；S 使用 cars input channel 与随机 1..300 measurement input。",
        f"- IRT4 cars 数据：`{audit['irt4_cars_status']}`。",
        "",
        "| run | model | simulation | cars input | firstU MSE | secondU MSE | target cars diff | cars channel nnz | figures | gate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in audit["runs"]:
        la = row["loader_audit"]
        lines.append(
            f"| `{row['name']}` | {row['model']} | {row['simulation']} | {row['cars_input']} | "
            f"{row.get('firstU_mse', float('nan')):.10f} | {row.get('secondU_mse', float('nan')):.10f} | "
            f"{la['target_diff_vs_no_cars_max']:.6f} | {la['cars_input_nonzero'] or 0} | "
            f"{row.get('figure_count', 0)} | `{row['gate']}` |"
        )
    lines.extend(["", "## 缺口"])
    missing = [row for row in audit["runs"] if not row["gate"]]
    if not missing:
        lines.append("- 无。")
    for row in missing:
        lines.append(f"- `{row['name']}` 未满足 gate；运行 `python scripts/run_full_matrix_cars.py --run {row['name']} --device auto`。")
    (OUT_DIR / "cars_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [collect(name) for name in RUNS]
    availability = dataset_availability()
    irt4_status = "available" if availability["carsIRT4"]["file_count"] > 0 else "dataset-unavailable"
    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "dataset_availability": availability,
        "irt4_cars_status": irt4_status,
        "runs": rows,
        "gate": {"pass": all(row["gate"] for row in rows)},
    }
    save_json(audit, OUT_DIR / "cars_audit.json")
    write_markdown(audit)
    print(f"cars gate: {audit['gate']['pass']}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
