#!/usr/bin/env python3
"""Audit coarse-simulation matrix artifacts."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import git_metadata, load_yaml, save_json

OUT_DIR = ROOT / "reports/full_matrix"
RUNS = [
    "c_dpm_thr2",
    "s_dpm_thr2_rand1_300",
    "c_irt2_thr2",
    "s_irt2_thr2_rand1_300",
    "c_rand_thr2",
    "s_rand_thr2_rand1_300",
]
LEGACY_RUNS = {
    "c_dpm_thr2": ROOT / "reports/c_dpm_thr2/20260506_182311",
    "s_dpm_thr2_rand1_300": ROOT / "reports/s_dpm_thr2/rand1_300_50ep",
}


def flatten(value: Any, prefix: str = "") -> dict[str, float]:
    if isinstance(value, bool):
        return {}
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return {prefix: float(value)}
    if isinstance(value, dict):
        out: dict[str, float] = {}
        for key, child in value.items():
            out.update(flatten(child, f"{prefix}.{key}" if prefix else str(key)))
        return out
    return {}


def max_abs_diff(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_nums = flatten(left)
    right_nums = flatten(right)
    diffs = [
        abs(left_nums[key] - right_nums[key])
        for key in set(left_nums) & set(right_nums)
        if key != "seconds" and not key.endswith(".seconds")
    ]
    return max(diffs) if diffs else 0.0


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_dir_for(name: str) -> Path:
    full = OUT_DIR / f"{name}_50ep"
    if full.exists():
        return full
    return LEGACY_RUNS.get(name, full)


def collect(name: str) -> dict[str, Any]:
    run_dir = run_dir_for(name)
    config_path = ROOT / "configs" / f"{name}.yaml"
    if name == "s_dpm_thr2_rand1_300":
        config_path = ROOT / "configs/s_dpm_thr2_rand1_300.yaml"
    cfg = load_yaml(config_path)
    row = {
        "name": name,
        "run_dir": str(run_dir.relative_to(ROOT)) if run_dir.exists() else str(run_dir),
        "config": str(config_path.relative_to(ROOT)),
        "exists": run_dir.exists(),
        "simulation": cfg["data"]["simulation"],
        "model": "S" if cfg["data"]["loader"] == "RadioUNet_s" else "C",
        "sample_policy": {
            "fix_samples": cfg["data"].get("fix_samples"),
            "num_samples_low": cfg["data"].get("num_samples_low"),
            "num_samples_high": cfg["data"].get("num_samples_high"),
        },
        "cars_simulation": cfg["data"].get("cars_simulation"),
        "cars_input": cfg["data"].get("cars_input"),
    }
    if not run_dir.exists():
        row["gate"] = False
        return row
    for phase in ["firstU", "secondU"]:
        metrics = run_dir / f"{phase}_test_metrics.json"
        rerun = run_dir / f"{phase}_test_metrics_rerun.json"
        row[f"{phase}_metrics_exists"] = metrics.exists()
        row[f"{phase}_rerun_exists"] = rerun.exists()
        if metrics.exists() and rerun.exists():
            metric_data = load_json(metrics)
            rerun_data = load_json(rerun)
            row[f"{phase}_rerun_max_abs_diff"] = max_abs_diff(metric_data, rerun_data)
            row[f"{phase}_mse"] = metric_data[phase]["mse"] if phase in metric_data else metric_data["secondU"]["mse"]
    manifest = run_dir / "coarse_run_manifest.json"
    row["manifest_exists"] = manifest.exists()
    if manifest.exists():
        row["manifest_gate"] = load_json(manifest).get("gate", {})
    else:
        row["manifest_gate"] = {}
    figures = sorted((run_dir / "figures").glob("*.png"))
    row["figure_count"] = len(figures)
    row["figures_nonempty"] = all(path.stat().st_size > 0 for path in figures)
    row["secondU_not_worse_than_firstU"] = (
        row.get("firstU_mse") is not None
        and row.get("secondU_mse") is not None
        and row["secondU_mse"] <= row["firstU_mse"]
    )
    row["gate"] = all(
        [
            row.get("firstU_metrics_exists"),
            row.get("secondU_metrics_exists"),
            row.get("firstU_rerun_exists"),
            row.get("secondU_rerun_exists"),
            row.get("firstU_rerun_max_abs_diff") == 0.0,
            row.get("secondU_rerun_max_abs_diff") == 0.0,
            row.get("figure_count") == 8,
            row.get("figures_nonempty"),
            row.get("secondU_not_worse_than_firstU"),
        ]
    )
    return row


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# Coarse Simulation 全矩阵审计",
        "",
        f"- gate：`{audit['gate']['pass']}`。",
        "- 覆盖轴：RadioUNet_C/S x DPM/IRT2/random coarse simulation，clean map，no cars。",
        "",
        "| run | model | simulation | run dir | firstU MSE | secondU MSE | figures | gate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in audit["runs"]:
        lines.append(
            f"| `{row['name']}` | {row['model']} | {row['simulation']} | `{row['run_dir']}` | "
            f"{row.get('firstU_mse', float('nan')):.10f} | {row.get('secondU_mse', float('nan')):.10f} | "
            f"{row.get('figure_count', 0)} | `{row['gate']}` |"
        )
    lines.extend(["", "## 缺口"])
    for row in audit["runs"]:
        if not row["gate"]:
            lines.append(f"- `{row['name']}` 未满足 full-run gate；请运行 `python scripts/run_full_matrix_coarse.py --run {row['name']} --device auto`。")
    (OUT_DIR / "coarse_simulation_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [collect(name) for name in RUNS]
    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "runs": rows,
        "gate": {"pass": all(row["gate"] for row in rows)},
    }
    save_json(audit, OUT_DIR / "coarse_simulation_audit.json")
    write_markdown(audit)
    print(f"coarse gate: {audit['gate']['pass']}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
