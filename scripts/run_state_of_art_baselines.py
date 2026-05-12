#!/usr/bin/env python3
"""Run reproducible state-of-the-art comparison baselines on RadioUNet_S samples."""

from __future__ import annotations

import argparse
import copy
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.baselines import BASELINES
from radiounet.factory import build_dataset
from radiounet.utils import git_metadata, load_yaml, require_dataset_dir, save_json, set_seed

OUT_DIR = ROOT / "reports/full_matrix/state_of_art_comparison"
DEFAULT_SAMPLE_COUNTS = [10, 20, 50, 100, 200, 300]


def config_for_samples(base_config: dict[str, Any], sample_count: int) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    config["data"]["loader"] = "RadioUNet_s"
    config["data"]["fix_samples"] = sample_count
    config["data"]["num_samples_low"] = sample_count
    config["data"]["num_samples_high"] = sample_count + 1
    config["data"]["cars_simulation"] = "no"
    config["data"]["cars_input"] = "no"
    config["model"]["inputs"] = 3
    return config


def unpack(item: Any) -> tuple[torch.Tensor, torch.Tensor]:
    if len(item) < 2:
        raise ValueError(f"Expected dataset item with at least 2 tensors, got {len(item)}.")
    return item[0], item[1]


def evaluate_baseline(name: str, config: dict[str, Any], max_samples: int | None) -> dict[str, Any]:
    dataset = build_dataset(config, "test", smoke=False)
    limit = min(len(dataset), max_samples) if max_samples else len(dataset)
    sums = defaultdict(float)
    start = time.time()
    for idx in range(limit):
        inputs, target = unpack(dataset[idx])
        buildings = inputs[0]
        tx = inputs[1]
        samples = inputs[2]
        if name in {"tomography", "one_step_mlp"}:
            result = BASELINES[name](samples, tx, buildings)
        else:
            result = BASELINES[name](samples)
        pred = torch.from_numpy(result.prediction).view_as(target).to(dtype=target.dtype)
        err = pred - target
        sums["sse"] += float(torch.sum(err**2).item())
        sums["target_energy"] += float(torch.sum(target**2).item())
        sums["mse_sum"] += float(torch.mean(err**2).item())
        sums["seconds_inner"] += result.seconds
        sums["used_building_postprocessing"] += 1.0 if result.used_building_postprocessing else 0.0
        sums["per_map_optimized"] += 1.0 if result.per_map_optimized else 0.0
        if idx == 0:
            sums["first_sample_points"] = float(torch.count_nonzero(samples).item())
            implementation = result.implementation
    raw_mse = sums["mse_sum"] / max(limit, 1)
    target_scale = float(config.get("data", {}).get("target_scale", 256.0))
    mse = raw_mse / (target_scale**2)
    rmse = math.sqrt(mse)
    return {
        "baseline": name,
        "samples": limit,
        "sample_count": int(config["data"]["fix_samples"]),
        "input_information": "sparse radio measurements + Tx + buildings",
        "building_postprocessing": bool(sums["used_building_postprocessing"]),
        "per_map_optimized": bool(sums["per_map_optimized"]),
        "implementation": implementation if limit else BASELINES[name].__name__,
        "seconds": time.time() - start,
        "baseline_inner_seconds": sums["seconds_inner"],
        "target_scale": target_scale,
        "first_sample_nonzero_points": int(sums["first_sample_points"]) if limit else None,
        "mse": mse,
        "raw_mse": raw_mse,
        "global_nmse": sums["sse"] / sums["target_energy"] if sums["target_energy"] else None,
        "rmse": rmse,
        "rmse_db_80": rmse * 80.0,
    }


def radio_unet_reference(sample_count: int) -> dict[str, Any] | None:
    mapping = {
        50: ROOT / "reports/s_dpm_thr2/fix50_50ep/secondU_test_metrics.json",
        100: ROOT / "reports/s_dpm_thr2/fix100_50ep/secondU_test_metrics.json",
        300: ROOT / "reports/s_dpm_thr2/fix300_50ep/secondU_test_metrics.json",
    }
    path = mapping.get(sample_count)
    if not path or not path.exists():
        return None
    import json

    metrics = json.loads(path.read_text(encoding="utf-8"))
    second = metrics["secondU"]
    return {
        "baseline": "radiounet_s_secondU",
        "samples": metrics.get("samples"),
        "sample_count": sample_count,
        "input_information": "sparse radio measurements + Tx + buildings, trained RadioUNet_S",
        "building_postprocessing": False,
        "per_map_optimized": False,
        "implementation": "existing trained RadioUNet_S secondU metrics",
        "seconds": metrics.get("seconds"),
        "target_scale": second.get("target_scale"),
        "mse": second.get("mse"),
        "raw_mse": second.get("raw_mse"),
        "global_nmse": second.get("global_nmse"),
        "rmse": second.get("rmse"),
        "rmse_db_80": second.get("rmse_db_80"),
        "source_metrics": str(path.relative_to(ROOT)),
    }


def c_reference() -> dict[str, Any]:
    import json

    path = ROOT / "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json"
    metrics = json.loads(path.read_text(encoding="utf-8"))
    second = metrics["secondU"]
    return {
        "baseline": "radiounet_c_secondU",
        "samples": metrics.get("samples"),
        "sample_count": None,
        "input_information": "Tx + buildings, trained RadioUNet_C",
        "building_postprocessing": False,
        "per_map_optimized": False,
        "implementation": "existing trained RadioUNet_C horizontal baseline",
        "seconds": metrics.get("seconds"),
        "target_scale": second.get("target_scale"),
        "mse": second.get("mse"),
        "raw_mse": second.get("raw_mse"),
        "global_nmse": second.get("global_nmse"),
        "rmse": second.get("rmse"),
        "rmse_db_80": second.get("rmse_db_80"),
        "source_metrics": str(path.relative_to(ROOT)),
    }


def make_figure(rows: list[dict[str, Any]], output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8), constrained_layout=True)
    for baseline in sorted({row["baseline"] for row in rows if row.get("sample_count") is not None}):
        points = sorted((row for row in rows if row["baseline"] == baseline and row.get("sample_count") is not None), key=lambda row: row["sample_count"])
        ax.plot([row["sample_count"] for row in points], [row["mse"] for row in points], marker="o", label=baseline)
    c_rows = [row for row in rows if row["baseline"] == "radiounet_c_secondU"]
    if c_rows:
        ax.axhline(c_rows[0]["mse"], color="black", linestyle="--", linewidth=1.0, label="radiounet_c_secondU")
    ax.set_xlabel("Sparse measurement count")
    ax.set_ylabel("MSE")
    ax.set_title("State-of-the-art comparison baselines")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/s_dpm_thr2_fix50.yaml")
    parser.add_argument("--sample-counts", nargs="+", type=int, default=DEFAULT_SAMPLE_COUNTS)
    parser.add_argument("--baselines", nargs="+", choices=sorted(BASELINES), default=sorted(BASELINES))
    parser.add_argument("--max-samples", type=int, default=198, help="Limit test items for classical baselines; use 0 for full test split.")
    parser.add_argument("--output-dir", default=str(OUT_DIR.relative_to(ROOT)))
    args = parser.parse_args()

    base_config = load_yaml(ROOT / args.config)
    require_dataset_dir(base_config)
    set_seed(int(base_config.get("experiment", {}).get("seed", 42)))
    max_samples = None if args.max_samples == 0 else args.max_samples
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for sample_count in args.sample_counts:
        config = config_for_samples(base_config, sample_count)
        for baseline in args.baselines:
            print(f"running {baseline} sample_count={sample_count}", flush=True)
            rows.append(evaluate_baseline(baseline, config, max_samples=max_samples))
        ref = radio_unet_reference(sample_count)
        if ref is not None:
            rows.append(ref)
    rows.append(c_reference())

    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "config": args.config,
        "sample_counts": args.sample_counts,
        "max_samples": max_samples,
        "baselines": args.baselines,
        "runs": rows,
        "gate": {
            "pass": bool(rows)
            and all(row.get("samples") for row in rows if row["baseline"] != "radiounet_c_secondU")
            and all(row.get("mse") is not None for row in rows),
            "scope": "classical baselines are deterministic implementation-faithful proxies unless official baseline code is provided",
        },
    }
    save_json(audit, output_dir / "state_of_art_comparison.json")
    make_figure(rows, output_dir / "state_of_art_comparison.png")
    print(f"saved: {output_dir / 'state_of_art_comparison.json'}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
