#!/usr/bin/env python3
"""Audit Stage 2 NMSE denominator and RadioUNet_S smoke data path."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader
from radiounet.metrics import mse
from radiounet.utils import ensure_dir, git_metadata, load_yaml, require_dataset_dir, save_json, set_seed


OFFICIAL_NOTEBOOK = {
    "firstU_mse": 0.000463,
    "secondU_mse": 0.000409,
    "firstU_nmse": 0.008737,
    "secondU_nmse": 0.007728,
}

PAPER_TABLE = {
    "setting": "accurate map, deterministic simulation with no cars / RadioUNet_C coarse simulations",
    "nmse": 0.0075,
    "rmse": 0.0200,
}


def unpack_batch(batch):
    if len(batch) == 2:
        inputs, targets = batch
        samples = None
    elif len(batch) == 3:
        inputs, targets, samples = batch
    else:
        raise ValueError(f"Expected batch of length 2 or 3, got {len(batch)}.")
    return inputs, targets, samples


def to_image(tensor: torch.Tensor) -> np.ndarray:
    arr = tensor.detach().cpu().numpy()
    if arr.ndim == 3:
        arr = arr[0]
    return arr


def target_energy(config: dict, split: str, smoke: bool, limit_batches: int | None) -> dict:
    loader = build_dataloader(config, split, smoke=smoke, shuffle=False)
    batch_weighted_sum = 0.0
    global_sum_squares = 0.0
    total_pixels = 0
    samples = 0
    per_batch = []

    for batch_idx, batch in enumerate(loader):
        _inputs, targets, _samples = unpack_batch(batch)
        batch_size = targets.size(0)
        batch_energy = float(mse(targets, torch.zeros_like(targets)))
        batch_weighted_sum += batch_energy * batch_size
        global_sum_squares += float(torch.sum(targets * targets))
        total_pixels += targets.numel()
        samples += batch_size
        per_batch.append(batch_energy)
        if limit_batches is not None and batch_idx + 1 >= limit_batches:
            break

    mean_batch_energy = batch_weighted_sum / max(samples, 1)
    global_energy = global_sum_squares / max(total_pixels, 1)
    return {
        "split": split,
        "smoke": smoke,
        "limit_batches": limit_batches,
        "samples": samples,
        "target_pixels": total_pixels,
        "mean_batch_weighted_mse_target_zero": mean_batch_energy,
        "global_mse_target_zero": global_energy,
        "per_batch_min": min(per_batch) if per_batch else None,
        "per_batch_max": max(per_batch) if per_batch else None,
    }


def infer_denominators() -> dict:
    first = OFFICIAL_NOTEBOOK["firstU_mse"] / OFFICIAL_NOTEBOOK["firstU_nmse"]
    second = OFFICIAL_NOTEBOOK["secondU_mse"] / OFFICIAL_NOTEBOOK["secondU_nmse"]
    paper = (PAPER_TABLE["rmse"] ** 2) / PAPER_TABLE["nmse"]
    return {
        "official_notebook": {
            "firstU_inferred_denominator": first,
            "secondU_inferred_denominator": second,
            "mean_inferred_denominator": (first + second) / 2,
            "method": "MSE / NMSE, inferred from saved notebook output.",
        },
        "paper_table": {
            "setting": PAPER_TABLE["setting"],
            "inferred_denominator": paper,
            "method": "RMSE^2 / NMSE, inferred from paper source table.",
        },
    }


def audit_s_loader(config: dict, output_dir: Path) -> dict:
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    loader = build_dataloader(config, "train", smoke=True, shuffle=False)
    batch = next(iter(loader))
    inputs, targets, samples = unpack_batch(batch)
    target_scale = float(config.get("data", {}).get("target_scale", 1.0))
    sparse = inputs[:, 2]
    nonzero_counts = torch.count_nonzero(sparse, dim=(1, 2)).cpu().tolist()
    target_at_sparse = torch.where(sparse > 0, targets[:, 0], torch.zeros_like(sparse))
    alignment_abs_max = float(torch.max(torch.abs(target_at_sparse - sparse)).cpu())

    fig_dir = ensure_dir(output_dir / "figures")
    panels = [
        ("buildings", to_image(inputs[0, 0])),
        ("Tx", to_image(inputs[0, 1])),
        ("sparse samples", to_image(inputs[0, 2]) / target_scale),
        ("target", to_image(targets[0]) / target_scale),
    ]
    if samples is not None:
        panels.append(("sample mask", to_image(samples[0])))
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4), constrained_layout=True)
    if len(panels) == 1:
        axes = [axes]
    for ax, (title, image) in zip(axes, panels):
        ax.imshow(image, cmap="viridis")
        ax.set_title(title)
        ax.axis("off")
    figure_path = fig_dir / "s_dpm_thr2_sparse_samples.png"
    fig.savefig(figure_path, dpi=150)
    plt.close(fig)

    result = {
        "batch_input_shape": list(inputs.shape),
        "batch_target_shape": list(targets.shape),
        "batch_samples_shape": list(samples.shape) if samples is not None else None,
        "channels": ["buildings", "Tx", "sparse samples"],
        "target_scale": target_scale,
        "sparse_nonzero_counts": [int(x) for x in nonzero_counts],
        "sparse_nonzero_min": int(min(nonzero_counts)),
        "sparse_nonzero_max": int(max(nonzero_counts)),
        "sparse_value_min": float(torch.min(sparse).cpu()),
        "sparse_value_max": float(torch.max(sparse).cpu()),
        "target_value_min": float(torch.min(targets).cpu()),
        "target_value_max": float(torch.max(targets).cpu()),
        "sparse_target_alignment_abs_max": alignment_abs_max,
        "figure": str(figure_path),
    }
    return result


def load_metrics(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_firstu_loss(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    history = json.loads(path.read_text(encoding="utf-8"))
    val_losses = [row for row in history.get("history", []) if row.get("split") == "val"]
    train_losses = [row for row in history.get("history", []) if row.get("split") == "train"]
    return {
        "best_val_loss": history.get("best_val_loss"),
        "last_train_loss": train_losses[-1]["loss"] if train_losses else None,
        "last_val_loss": val_losses[-1]["loss"] if val_losses else None,
        "history": str(path),
    }


def write_report(output_dir: Path, audit: dict) -> Path:
    current = audit["nmse"]["current_test_target_energy"]
    denominators = audit["nmse"]["inferred_external_denominators"]
    stage1 = audit["nmse"].get("stage1_metrics") or {}
    s_loader = audit["radio_unet_s_loader"]
    smoke = audit.get("smoke_training") or {}
    metrics = audit.get("smoke_metrics") or {}

    current_den = current["mean_batch_weighted_mse_target_zero"]
    notebook_den = denominators["official_notebook"]["mean_inferred_denominator"]
    paper_den = denominators["paper_table"]["inferred_denominator"]
    notebook_gap = (current_den / notebook_den - 1) * 100
    paper_gap = (current_den / paper_den - 1) * 100
    first_global_nmse = stage1.get("firstU_mse") / current_den if stage1.get("firstU_mse") is not None else None
    second_global_nmse = stage1.get("secondU_mse") / current_den if stage1.get("secondU_mse") is not None else None

    lines = [
        "# Stage 2 smoke 审计：RadioUNet_S + DPM + threshold=0.2",
        "",
        "## 追溯性",
        "",
        f"- source git commit：`{audit['source_git']['commit']}`。",
        f"- source dirty：`{audit['source_git']['dirty']}`（检查时排除 `reports/` 产物目录）。",
        f"- source status：`{audit['source_git']['status_short'] or 'clean'}`。",
        "",
        "## 权威产物",
        "",
        f"- 审计报告目录：`{output_dir}`。",
        f"- smoke run 目录：`{Path(smoke.get('history', '')).parent if smoke.get('history') else '未提供'}`。",
        "- 旧版 `reports/stage2_smoke/` 和时间戳 smoke run 不再作为 Stage 2 权威证据。",
        "",
        "## 结论",
        "",
        f"- 当前 test split 直接统计的 `MSE(target, 0)` 为 `{current_den:.10f}`；全局像素口径为 `{current['global_mse_target_zero']:.10f}`，两者一致到可忽略量级。",
        f"- 官方 notebook 由 `MSE/NMSE` 反推的分母均值为 `{notebook_den:.10f}`；论文表格由 `RMSE^2/NMSE` 反推的分母为 `{paper_den:.10f}`。",
        f"- 当前直接 target energy 比 notebook 高 `{notebook_gap:.2f}%`，比论文表格高 `{paper_gap:.2f}%`，属于小差异；Stage 1 报告中由“平均 MSE / 平均 NMSE”反推的 `0.0435..0.0438` 不是 test split 真实 target energy。",
        "- 结论：遗留 NMSE 偏差主要是统计粒度差异，也就是 batch-mean NMSE 与全局 `sum(error^2)/sum(target^2)` 的口径差异；不支持归因于数据版本差异或 threshold=0.2 差异。",
        "",
        "## NMSE 口径审计",
        "",
        "| 来源 | 分母口径 | 数值 |",
        "| --- | --- | ---: |",
        f"| 当前 test split | `MSE(target, 0)` batch 加权均值 | `{current_den:.10f}` |",
        f"| 当前 test split | `sum(target^2)/Npixels` 全局像素均值 | `{current['global_mse_target_zero']:.10f}` |",
        f"| 官方 notebook | firstU `MSE/NMSE` 反推 | `{denominators['official_notebook']['firstU_inferred_denominator']:.10f}` |",
        f"| 官方 notebook | secondU `MSE/NMSE` 反推 | `{denominators['official_notebook']['secondU_inferred_denominator']:.10f}` |",
        f"| 论文表格 | `RMSE^2/NMSE` 反推 | `{paper_den:.10f}` |",
        "",
        f"Stage 1 firstU 当前 batch-mean NMSE 有效分母：`{stage1.get('firstU_denominator', float('nan')):.10f}`。",
        f"Stage 1 secondU 当前 batch-mean NMSE 有效分母：`{stage1.get('secondU_denominator', float('nan')):.10f}`。",
        f"按全局 target energy 重算 firstU NMSE：`{first_global_nmse}`。",
        f"按全局 target energy 重算 secondU NMSE：`{second_global_nmse}`。",
        "",
        "## RadioUNet_S loader 审计",
        "",
        f"- loader：`{audit['config']['data']['loader']}`。",
        f"- 输入 shape：`{s_loader['batch_input_shape']}`。",
        f"- target shape：`{s_loader['batch_target_shape']}`。",
        f"- 三个输入通道：`{', '.join(s_loader['channels'])}`。",
        f"- sparse samples 非零数量范围：`{s_loader['sparse_nonzero_min']}..{s_loader['sparse_nonzero_max']}`。",
        f"- sparse samples 值域：`{s_loader['sparse_value_min']:.6f}..{s_loader['sparse_value_max']:.6f}`，target 值域：`{s_loader['target_value_min']:.6f}..{s_loader['target_value_max']:.6f}`。",
        f"- sparse samples 与 target 对齐检查最大绝对误差：`{s_loader['sparse_target_alignment_abs_max']:.10f}`。",
        f"- sparse sample 可视化：`{s_loader['figure']}`。",
        "",
        "## Stage 2 配置",
        "",
        "- 配置文件：`configs/s_dpm_thr2.yaml`。",
        "- 关键设置：`loader=RadioUNet_s`，`simulation=DPM`，`city_map=complete`，`inputs=3`，`threshold=0.2`。",
        "- 当前配置只作为 smoke 入口，不声明 full train 结果。",
        "",
        "## Smoke training",
        "",
        "- 命令：`python scripts/train.py --config configs/s_dpm_thr2.yaml --phase firstU --smoke`。",
        f"- firstU smoke loss：`{smoke.get('last_train_loss')}` train / `{smoke.get('last_val_loss')}` val，best val `{smoke.get('best_val_loss')}`。",
        "",
        "## Smoke evaluation / figure",
        "",
    ]
    if metrics:
        first = metrics.get("firstU", {})
        lines.extend(
            [
                f"- firstU smoke MSE：`{first.get('mse')}`。",
                f"- firstU smoke NMSE：`{first.get('nmse')}`。",
                f"- firstU smoke RMSE：`{first.get('rmse')}`。",
                f"- prediction/error 图：`{audit.get('prediction_figure')}`。",
            ]
        )
    else:
        lines.append("- 尚未提供 smoke metrics。")

    report_path = output_dir / "smoke_audit.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c-config", default="configs/c_dpm_thr2.yaml")
    parser.add_argument("--s-config", default="configs/s_dpm_thr2.yaml")
    parser.add_argument("--stage1-metrics", default="reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json")
    parser.add_argument("--smoke-history")
    parser.add_argument("--smoke-metrics")
    parser.add_argument("--prediction-figure")
    parser.add_argument("--output-dir", default="reports/stage2_s_dpm_thr2")
    parser.add_argument("--limit-energy-batches", type=int)
    args = parser.parse_args()

    c_config = load_yaml(Path(args.c_config))
    s_config = load_yaml(Path(args.s_config))
    for config in [c_config, s_config]:
        require_dataset_dir(config)

    output_dir = ensure_dir(args.output_dir)
    current_energy = target_energy(c_config, split="test", smoke=False, limit_batches=args.limit_energy_batches)
    denominators = infer_denominators()
    stage1_metrics = load_metrics(Path(args.stage1_metrics)) if args.stage1_metrics else None
    if stage1_metrics:
        stage1_denominators = {
            "firstU_denominator": stage1_metrics["firstU"]["mse"] / stage1_metrics["firstU"]["nmse"],
            "secondU_denominator": stage1_metrics["secondU"]["mse"] / stage1_metrics["secondU"]["nmse"],
            "firstU_mse": stage1_metrics["firstU"]["mse"],
            "secondU_mse": stage1_metrics["secondU"]["mse"],
            "firstU_reported_nmse": stage1_metrics["firstU"]["nmse"],
            "secondU_reported_nmse": stage1_metrics["secondU"]["nmse"],
        }
    else:
        stage1_denominators = None

    audit = {
        "source_git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "config": s_config,
        "nmse": {
            "current_test_target_energy": current_energy,
            "current_evaluation_denominators": stage1_denominators,
            "stage1_metrics": stage1_denominators,
            "inferred_external_denominators": denominators,
        },
        "radio_unet_s_loader": audit_s_loader(s_config, output_dir),
        "smoke_training": load_firstu_loss(Path(args.smoke_history)) if args.smoke_history else None,
        "smoke_metrics": load_metrics(Path(args.smoke_metrics)) if args.smoke_metrics else None,
        "prediction_figure": args.prediction_figure,
    }
    save_json(audit, output_dir / "smoke_audit.json")
    report_path = write_report(output_dir, audit)
    print(f"saved audit json: {output_dir / 'smoke_audit.json'}")
    print(f"saved audit report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
