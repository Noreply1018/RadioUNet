from __future__ import annotations

import json
import random
import shutil
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device(requested: str = "auto") -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false.")
    return device


def timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def copy_config(config_path: str | Path, output_dir: str | Path) -> Path:
    output_dir = ensure_dir(output_dir)
    dst = output_dir / Path(config_path).name
    shutil.copy2(config_path, dst)
    return dst


def git_commit() -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def require_dataset_dir(config: dict[str, Any]) -> Path:
    dataset_dir = Path(config.get("data", {}).get("dataset_dir", "RadioMapSeer/"))
    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"RadioMapSeer 数据集目录不存在: {dataset_dir}\n"
            f"请先运行: python scripts/prepare_dataset.py --dataset-dir {dataset_dir}"
        )
    return dataset_dir
