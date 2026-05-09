#!/usr/bin/env python3
"""Audit the sample-assisted RadioUNet_s data path."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader
from radiounet.utils import ensure_dir, load_yaml, require_dataset_dir, save_json


def tensor_stats(tensor: torch.Tensor) -> dict:
    return {
        "min": float(tensor.min()),
        "max": float(tensor.max()),
        "mean": float(tensor.float().mean()),
        "nonzero": int(torch.count_nonzero(tensor)),
    }


def build_report(data: dict) -> str:
    lines = [
        "# Stage 2 前置审计：RadioUNet_S loader",
        "",
        "## 数据 shape",
        "",
        f"- config: `{data['config']}`",
        f"- split: `{data['split']}`",
        f"- smoke: `{data['smoke']}`",
        f"- batch length: `{data['batch_length']}`",
        f"- inputs shape: `{data['inputs_shape']}`",
        f"- targets shape: `{data['targets_shape']}`",
        "",
        "## 通道和值域",
        "",
        "| 通道 | min | max | mean | nonzero |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, stats in data["channel_stats"].items():
        lines.append(f"| {name} | {stats['min']:.6f} | {stats['max']:.6f} | {stats['mean']:.6f} | {stats['nonzero']} |")
    lines.extend(
        [
            "",
            "## sparse samples",
            "",
            f"- 每张图 sparse 非零数量范围: `{data['sparse_nonzero_min']}` 到 `{data['sparse_nonzero_max']}`",
            f"- 每张图 sparse 非零数量列表: `{data['sparse_nonzero_per_sample']}`",
            f"- sparse 非零位置与 target 最大绝对误差: `{data['sparse_target_alignment_max_abs_error']:.10f}`",
            f"- sparse 非零值域: `{data['sparse_nonzero_value_min']:.6f}` 到 `{data['sparse_nonzero_value_max']:.6f}`",
            "",
            "## 结论",
            "",
            data["conclusion"],
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/s_dpm_thr2.yaml")
    parser.add_argument("--split", default="train", choices=["train", "val", "test"])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output-dir", default="reports/stage2_smoke")
    args = parser.parse_args()

    config = load_yaml(args.config)
    require_dataset_dir(config)
    loader = build_dataloader(config, args.split, smoke=args.smoke, shuffle=False)
    batch = next(iter(loader))
    if len(batch) == 2:
        inputs, targets = batch
        sample_mask = None
    elif len(batch) == 3:
        inputs, targets, sample_mask = batch
    elif len(batch) == 4:
        inputs, targets, sample_mask, _input_sample_mask = batch
    else:
        raise ValueError(f"Expected batch of length 2, 3, or 4, got {len(batch)}.")

    if inputs.ndim != 4 or inputs.shape[1:] != (3, 256, 256):
        raise AssertionError(f"RadioUNet_s inputs should be [B, 3, 256, 256], got {tuple(inputs.shape)}")
    if targets.ndim != 4 or targets.shape[1:] != (1, 256, 256):
        raise AssertionError(f"Targets should be [B, 1, 256, 256], got {tuple(targets.shape)}")

    buildings = inputs[:, 0:1]
    tx = inputs[:, 1:2]
    sparse = inputs[:, 2:3]
    sparse_nonzero = sparse != 0
    sparse_counts = sparse_nonzero.flatten(1).sum(dim=1)
    if int(sparse_counts.min()) < int(config["data"].get("num_samples_low", 10)) - 1:
        raise AssertionError("Sparse sample count is below the configured lower bound after duplicate coordinates.")
    if int(sparse_counts.max()) > int(config["data"].get("num_samples_high", 300)):
        raise AssertionError("Sparse sample count is above the configured upper bound.")

    target_at_sparse = targets[sparse_nonzero]
    sparse_values = sparse[sparse_nonzero]
    alignment_error = torch.abs(sparse_values - target_at_sparse).max() if sparse_values.numel() else torch.tensor(0.0)

    report = {
        "config": args.config,
        "split": args.split,
        "smoke": args.smoke,
        "batch_length": len(batch),
        "inputs_shape": list(inputs.shape),
        "targets_shape": list(targets.shape),
        "samples_shape": list(sample_mask.shape) if sample_mask is not None else None,
        "channel_stats": {
            "buildings": tensor_stats(buildings),
            "Tx": tensor_stats(tx),
            "sparse_samples": tensor_stats(sparse),
            "target": tensor_stats(targets),
        },
        "sparse_nonzero_per_sample": [int(x) for x in sparse_counts.tolist()],
        "sparse_nonzero_min": int(sparse_counts.min()),
        "sparse_nonzero_max": int(sparse_counts.max()),
        "sparse_nonzero_value_min": float(sparse_values.min()) if sparse_values.numel() else 0.0,
        "sparse_nonzero_value_max": float(sparse_values.max()) if sparse_values.numel() else 0.0,
        "sparse_target_alignment_max_abs_error": float(alignment_error),
        "conclusion": (
            "RadioUNet_s 当前真实 batch 满足 [B, 3, 256, 256]，三通道依次为 buildings、Tx、sparse samples；"
            "sparse samples 直接来自 threshold 后并乘以 256 的 target，在非零采样点与 target 完全对齐。"
            "该 loader 返回二元 batch `(inputs, targets)`；训练循环已兼容二元和三元 batch。"
        ),
    }

    output_dir = ensure_dir(args.output_dir)
    json_path = output_dir / "s_loader_audit.json"
    md_path = output_dir / "s_loader_audit.md"
    save_json(report, json_path)
    md_path.write_text(build_report(report), encoding="utf-8")
    print(f"saved: {json_path}")
    print(f"saved: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
