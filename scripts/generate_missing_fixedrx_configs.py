#!/usr/bin/env python3
"""Generate fixed-receiver missing-building configs for all source/model/count cells."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"
COUNTS = [0, 1, 2, 4]
SOURCES = {
    "dpm": {
        "label": "DPM",
        "c_checkpoint": "reports/c_dpm_thr2/20260506_182311/checkpoints/firstU.pt",
        "s_checkpoint": "reports/s_dpm_thr2/rand1_300_50ep/checkpoints/firstU.pt",
    },
    "irt2": {
        "label": "IRT2",
        "c_checkpoint": "reports/full_matrix/c_irt2_thr2_50ep/checkpoints/firstU.pt",
        "s_checkpoint": "reports/full_matrix/s_irt2_thr2_rand1_300_50ep/checkpoints/firstU.pt",
    },
    "rand": {
        "label": "random coarse simulation",
        "c_checkpoint": "reports/full_matrix/c_rand_thr2_50ep/checkpoints/firstU.pt",
        "s_checkpoint": "reports/full_matrix/s_rand_thr2_rand1_300_50ep/checkpoints/firstU.pt",
    },
}


def write_config(name: str, cfg: dict) -> None:
    path = CONFIG_DIR / f"{name}.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def base(model: str, source: str, count: int) -> dict:
    meta = SOURCES[source]
    is_s = model == "s"
    checkpoint = meta["s_checkpoint"] if is_s else meta["c_checkpoint"]
    name = f"{model}_{source}_irt4_missing{count}_fixedrx_adapt"
    data = {
        "dataset_dir": "RadioMapSeer/",
        "loader": "RadioUNet_s_sprseIRT4" if is_s else "RadioUNet_c_sprseIRT4",
        "simulation": "IRT4",
        "city_map": "complete" if count == 0 else "missing",
        "cars_simulation": "no",
        "cars_input": "no",
        "num_tx": 2,
        "threshold": 0.2,
        "batch_size": 15,
        "num_workers": 1,
        "smoke_num_tx": 2,
        "receiver_seed_policy": "fixed_map",
    }
    if count:
        data["missing"] = count
    if is_s:
        data.update({"target_scale": 256, "data_samples": 600, "fix_samples": 0, "num_samples_low": 1, "num_samples_high": 301})
    else:
        data["num_samples"] = 300
    return {
        "experiment": {
            "name": name,
            "description": f"RadioUNet_{model.upper()} {meta['label']}-source IRT4 missing{count} sparse adaptation with fixed receiver mask.",
            "seed": 42,
        },
        "data": data,
        "model": {"class_name": "RadioWNet", "inputs": 3 if is_s else 2, "phases": ["secondU"]},
        "training": {
            "epochs": 50,
            "optimizer": "Adam",
            "learning_rate": 0.0001,
            "scheduler": "StepLR",
            "step_size": 30,
            "gamma": 0.1,
            "loss": "MSELoss",
            "adaptation_mode": "secondU-only",
            "init_checkpoint": checkpoint,
            "loss_mode": "sparse_mse",
            "num_samples_for_loss": 600 if is_s else 300,
        },
        "evaluation": {
            "metrics": ["mse", "nmse", "rmse"],
            "save_prediction_panels": True,
            "measure_runtime": True,
            "source_checkpoint": checkpoint,
            "source_training_target": meta["label"],
            "target": "IRT4",
            "receiver_policy": "paper-faithful fixed receiver mask",
        },
    }


def main() -> int:
    for source in SOURCES:
        for model in ["c", "s"]:
            for count in COUNTS:
                name = f"{model}_{source}_irt4_missing{count}_fixedrx_adapt"
                write_config(name, base(model, source, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
