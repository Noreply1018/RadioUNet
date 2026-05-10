from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

from . import data as data_module
from . import models


def _yes_no(value: object, default: str = "no") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def build_dataset(config: dict[str, Any], phase: str, smoke: bool = False):
    data_cfg = config["data"]
    loader_name = data_cfg.get("loader", "RadioUNet_c")
    loader_cls = getattr(data_module, loader_name)

    kwargs: dict[str, Any] = {
        "phase": phase,
        "dir_dataset": data_cfg.get("dataset_dir", "RadioMapSeer/"),
        "numTx": int(data_cfg.get("num_tx", 80)),
        "thresh": float(data_cfg.get("threshold", 0.2)),
        "simulation": data_cfg.get("simulation", "DPM"),
        "carsSimul": _yes_no(data_cfg.get("cars_simulation"), "no"),
        "carsInput": _yes_no(data_cfg.get("cars_input"), "no"),
        "cityMap": data_cfg.get("city_map", "complete"),
    }
    if "missing" in data_cfg:
        kwargs["missing"] = int(data_cfg["missing"])
    for config_key, loader_key, caster in [
        ("fix_samples", "fix_samples", float),
        ("num_samples_low", "num_samples_low", int),
        ("num_samples_high", "num_samples_high", int),
        ("num_samples", "num_samples", int),
        ("data_samples", "data_samples", int),
        ("IRT2maxW", "IRT2maxW", float),
    ]:
        if config_key in data_cfg:
            kwargs[loader_key] = caster(data_cfg[config_key])
    if "receiver_seed_policy" in data_cfg:
        kwargs["receiver_seed_policy"] = str(data_cfg["receiver_seed_policy"])

    if smoke:
        kwargs.update({"phase": "custom", "ind1": 0, "ind2": 0, "numTx": int(data_cfg.get("smoke_num_tx", 2))})

    return loader_cls(**kwargs)


def build_dataloader(config: dict[str, Any], phase: str, smoke: bool = False, shuffle: bool | None = None) -> DataLoader:
    dataset = build_dataset(config, phase=phase, smoke=smoke)
    data_cfg = config["data"]
    if shuffle is None:
        shuffle = phase == "train"
    seed = int(config.get("experiment", {}).get("seed", 42))
    phase_offsets = {"train": 0, "val": 10_000, "test": 20_000}
    loader_seed = seed + phase_offsets.get(phase, 30_000) + (1_000_000 if smoke else 0)
    generator = torch.Generator()
    generator.manual_seed(loader_seed)

    def seed_worker(worker_id: int) -> None:
        worker_seed = (loader_seed + worker_id) % (2**32)
        random.seed(worker_seed)
        np.random.seed(worker_seed)
        torch.manual_seed(worker_seed)

    return DataLoader(
        dataset,
        batch_size=int(data_cfg.get("batch_size", 15)),
        shuffle=shuffle,
        num_workers=int(data_cfg.get("num_workers", 1)),
        worker_init_fn=seed_worker,
        generator=generator,
    )


def build_model(config: dict[str, Any], phase: str | None = None):
    model_cfg = config["model"]
    class_name = model_cfg.get("class_name", "RadioWNet")
    model_cls = getattr(models, class_name)
    model_phase = phase or model_cfg.get("phase", "firstU")
    return model_cls(inputs=int(model_cfg.get("inputs", 2)), phase=model_phase)
