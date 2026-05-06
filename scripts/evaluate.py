#!/usr/bin/env python3
"""Evaluate RadioUNet checkpoints."""

from __future__ import annotations

import argparse
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader, build_model
from radiounet.metrics import mse, nmse
from radiounet.utils import ensure_dir, get_device, git_metadata, load_yaml, require_dataset_dir, save_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Experiment YAML config.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint to evaluate.")
    parser.add_argument("--split", choices=["train", "val", "test"], default="test")
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N.")
    parser.add_argument("--smoke", action="store_true", help="Use the same tiny custom subset as smoke training.")
    parser.add_argument("--limit-batches", type=int, help="Stop after N batches.")
    parser.add_argument("--output", help="Metrics JSON path.")
    args = parser.parse_args()

    config = load_yaml(args.config)
    try:
        require_dataset_dir(config)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    device = get_device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    phase = checkpoint.get("phase", config.get("model", {}).get("phase", "secondU"))
    model = build_model(config, phase=phase).to(device)
    model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
    model.eval()

    loader = build_dataloader(config, args.split, smoke=args.smoke, shuffle=False)
    sums = defaultdict(float)
    samples = 0
    since = time.time()

    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(loader):
            inputs = inputs.to(device)
            targets = targets.to(device)
            outputs1, outputs2 = model(inputs)
            batch_size = inputs.size(0)
            samples += batch_size
            for name, pred in [("firstU", outputs1), ("secondU", outputs2)]:
                sums[f"{name}_mse"] += float(mse(pred, targets).cpu()) * batch_size
                sums[f"{name}_nmse"] += float(nmse(pred, targets).cpu()) * batch_size
            if args.limit_batches is not None and batch_idx + 1 >= args.limit_batches:
                break

    metrics = {
        "samples": samples,
        "seconds": time.time() - since,
        "checkpoint": args.checkpoint,
        "checkpoint_phase": phase,
        "git": git_metadata(),
    }
    for name in ["firstU", "secondU"]:
        mse_value = sums[f"{name}_mse"] / max(samples, 1)
        nmse_value = sums[f"{name}_nmse"] / max(samples, 1)
        rmse_value = math.sqrt(mse_value)
        metrics[name] = {
            "mse": mse_value,
            "nmse": nmse_value,
            "rmse": rmse_value,
            "rmse_db_80": rmse_value * 80,
        }

    output = Path(args.output) if args.output else Path("reports") / config["experiment"]["name"] / "metrics.json"
    ensure_dir(output.parent)
    save_json(metrics, output)
    print(metrics)
    print(f"saved metrics: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
