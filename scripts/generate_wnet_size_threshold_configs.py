#!/usr/bin/env python3
"""Generate audit configs for WNet size, threshold, and split matrix."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"
BASE = ROOT / "configs/c_dpm_thr2.yaml"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_config(name: str, cfg: dict) -> None:
    path = CONFIG_DIR / f"{name}.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def main() -> int:
    base = load_yaml(BASE)
    for label, width_scale in [("small", 0.5), ("base", 1.0), ("large", 1.5)]:
        cfg = copy.deepcopy(base)
        name = f"c_dpm_thr2_size_{label}"
        cfg["experiment"]["name"] = name
        cfg["experiment"]["description"] = f"RadioUNet_C DPM threshold 0.2 model-size audit config: {label}."
        cfg["model"]["width_scale"] = width_scale
        cfg.setdefault("evaluation", {})["matrix_axis"] = "model_size"
        write_config(name, cfg)

    for threshold in [0.0, 0.1, 0.2, 0.3, 0.4]:
        cfg = copy.deepcopy(base)
        tag = str(threshold).replace(".", "p")
        name = f"c_dpm_thr{tag}"
        cfg["experiment"]["name"] = name
        cfg["experiment"]["description"] = f"RadioUNet_C DPM threshold audit config: threshold={threshold}."
        cfg["data"]["threshold"] = threshold
        cfg.setdefault("evaluation", {})["matrix_axis"] = "threshold"
        write_config(name, cfg)

    cfg = copy.deepcopy(base)
    cfg["experiment"]["name"] = "c_dpm_thr2_split400_100_200"
    cfg["experiment"]["description"] = "RadioUNet_C DPM split sanity config for 400/100/200 map split audit."
    cfg["data"]["split_policy"] = "400_100_200"
    cfg["data"]["train_maps"] = 400
    cfg["data"]["val_maps"] = 100
    cfg["data"]["test_maps"] = 200
    cfg.setdefault("evaluation", {})["matrix_axis"] = "split"
    write_config("c_dpm_thr2_split400_100_200", cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
