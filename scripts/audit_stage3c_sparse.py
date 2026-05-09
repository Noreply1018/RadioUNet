#!/usr/bin/env python3
"""Audit Stage 3C sparse IRT4 adaptation semantics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader, build_dataset
from radiounet.metrics import mse
from radiounet.utils import git_metadata, load_yaml, require_dataset_dir, save_json, set_seed
from scripts.train import compute_loss, validate_training_config


def unpack_batch(batch):
    if len(batch) == 2:
        return batch[0], batch[1], None, None
    if len(batch) == 3:
        return batch[0], batch[1], batch[2], None
    if len(batch) == 4:
        return batch
    raise ValueError(f"Expected batch of length 2, 3, or 4, got {len(batch)}.")


def split_counts(config: dict[str, Any]) -> dict[str, int]:
    return {split: len(build_dataset(config, split)) for split in ["train", "val", "test"]}


def audit_split(config: dict[str, Any], split: str, max_batches: int | None) -> dict[str, Any]:
    loader = build_dataloader(config, split, smoke=False, shuffle=False)
    input_counts: list[int] = []
    mask_counts: list[int] = []
    subset_violations = 0
    target_alignment_abs_max = 0.0
    first_sparse_signature: list[float] | None = None

    for batch_idx, batch in enumerate(loader):
        inputs, targets, samples, input_samples_mask = unpack_batch(batch)
        if samples is None:
            raise ValueError("Stage 3C sparse audit requires the loader to return samples mask.")
        sparse_input = inputs[:, 2] if inputs.shape[1] >= 3 else torch.zeros_like(samples[:, 0])
        if input_samples_mask is not None:
            input_mask = input_samples_mask[:, 0] != 0
        else:
            input_mask = sparse_input != 0
        loss_mask = samples[:, 0] != 0
        input_counts.extend(int(x) for x in input_mask.flatten(1).sum(dim=1).tolist())
        mask_counts.extend(int(x) for x in loss_mask.flatten(1).sum(dim=1).tolist())
        subset_violations += int((input_mask & ~loss_mask).sum().item())
        if bool(input_mask.any()):
            target_alignment_abs_max = max(
                target_alignment_abs_max,
                float(torch.abs(sparse_input[input_mask] - targets[:, 0][input_mask]).max().item()),
            )
        if first_sparse_signature is None:
            first_sparse_signature = sparse_input.flatten()[:32].tolist()
        if max_batches is not None and batch_idx + 1 >= max_batches:
            break

    return {
        "checked_samples": len(input_counts),
        "input_points_min": min(input_counts) if input_counts else None,
        "input_points_max": max(input_counts) if input_counts else None,
        "input_points_mean": sum(input_counts) / len(input_counts) if input_counts else None,
        "loss_mask_points_min": min(mask_counts) if mask_counts else None,
        "loss_mask_points_max": max(mask_counts) if mask_counts else None,
        "loss_mask_points_mean": sum(mask_counts) / len(mask_counts) if mask_counts else None,
        "input_subset_of_loss_mask": subset_violations == 0,
        "input_subset_violation_pixels": subset_violations,
        "input_target_alignment_abs_max": target_alignment_abs_max,
        "first_sparse_signature": first_sparse_signature,
    }


def rng_replay(config: dict[str, Any], split: str) -> dict[str, Any]:
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    first = audit_split(config, split, max_batches=1)["first_sparse_signature"]
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    second = audit_split(config, split, max_batches=1)["first_sparse_signature"]
    return {"split": split, "first_batch_sparse_signature_matches": first == second}


def loss_audit(config: dict[str, Any]) -> dict[str, Any]:
    loader = build_dataloader(config, "train", smoke=False, shuffle=False)
    inputs, targets, samples, _input_samples_mask = unpack_batch(next(iter(loader)))
    if samples is None:
        raise ValueError("sparse_mse loss audit requires samples mask.")
    pred = torch.zeros_like(targets)
    dense_value = float(mse(pred, targets).item())
    configured_value = float(compute_loss(pred, targets, samples, config).item())
    masked_value = float((((pred - targets) ** 2) * samples).sum().item())
    denominator = inputs.shape[0] * int(config["training"]["num_samples_for_loss"])
    expected_sparse = masked_value / denominator
    abs_diff = abs(configured_value - expected_sparse)
    rel_diff = abs_diff / max(abs(expected_sparse), 1.0)
    return {
        "loss_mode": config["training"].get("loss_mode", "dense_mse"),
        "num_samples_for_loss": int(config["training"]["num_samples_for_loss"]),
        "dense_mse_on_same_batch": dense_value,
        "configured_loss_on_same_batch": configured_value,
        "manual_sparse_loss_on_same_batch": expected_sparse,
        "configured_manual_abs_diff": abs_diff,
        "configured_manual_rel_diff": rel_diff,
        "configured_equals_manual_sparse": rel_diff < 1e-6,
        "configured_differs_from_dense": abs(configured_value - dense_value) > 1e-12,
    }


def write_markdown(audit: dict[str, Any], output: Path) -> None:
    lines = [
        "# Stage 3C sparse IRT4 adaptation 审计",
        "",
        f"- 配置：`{audit['config_path']}`",
        f"- loader：`{audit['loader']}`",
        f"- sparse pool 配置：`{audit['data_samples']}`",
        f"- 输入随机点数配置：`low={audit['num_samples_low']}, high={audit['num_samples_high']}`（上界为 numpy randint exclusive）",
        f"- loss mode：`{audit['loss']['loss_mode']}`",
        f"- loss 分母：`num_samples_for_loss={audit['loss']['num_samples_for_loss']}`",
        f"- split 样本数：`{audit['split_counts']}`",
        "",
        "## Loss 语义",
        f"- 训练入口计算值等于手算 sparse loss：`{audit['loss']['configured_equals_manual_sparse']}`",
        f"- 训练入口计算值不同于 dense full-map MSE：`{audit['loss']['configured_differs_from_dense']}`",
        "",
        "## Loader / mask 对齐",
    ]
    for split, data in audit["splits"].items():
        lines.append(
            f"- `{split}` 输入点数 `{data['input_points_min']}..{data['input_points_max']}`，"
            f"loss mask 非零点数 `{data['loss_mask_points_min']}..{data['loss_mask_points_max']}`，"
            f"输入点属于 loss mask 子集 `{data['input_subset_of_loss_mask']}`，"
            f"输入 sparse 值与 target 最大误差 `{data['input_target_alignment_abs_max']}`"
        )
    lines.extend(
        [
            "",
            "## Gate",
        ]
    )
    for key, value in audit["gate"].items():
        lines.append(f"- `{key}={value}`")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default="reports/irt4_transfer/stage3c_audits")
    parser.add_argument("--max-batches", type=int, default=None)
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_yaml(config_path)
    validate_training_config(config)
    require_dataset_dir(config)
    set_seed(int(config.get("experiment", {}).get("seed", 42)))

    splits = {split: audit_split(config, split, max_batches=args.max_batches) for split in ["train", "val", "test"]}
    loss = loss_audit(config)
    replay = rng_replay(config, "train")
    data_cfg = config["data"]
    is_s_loader = data_cfg["loader"] == "RadioUNet_s_sprseIRT4"
    expected_pool = data_cfg.get("data_samples", data_cfg.get("num_samples"))
    gate = {
        "sparse_loss_configured": loss["loss_mode"] == "sparse_mse",
        "pool_matches_loss_denominator": expected_pool == loss["num_samples_for_loss"],
        "s_input_range_configured_1_to_300": (not is_s_loader)
        or (data_cfg.get("num_samples_low") == 1 and data_cfg.get("num_samples_high") == 301),
        "loss_matches_manual_sparse": loss["configured_equals_manual_sparse"],
        "loss_not_dense_mse": loss["configured_differs_from_dense"],
        "all_inputs_subset_of_loss_mask": all(item["input_subset_of_loss_mask"] for item in splits.values()),
        "target_alignment_exact": all(item["input_target_alignment_abs_max"] == 0.0 for item in splits.values()),
        "rng_replay_first_batch": replay["first_batch_sparse_signature_matches"],
    }
    gate["pass"] = all(gate.values())
    audit = {
        "scope": "Stage 3C sparse IRT4 adaptation semantic audit",
        "config_path": str(config_path),
        "git": git_metadata(exclude_paths=["reports"]),
        "loader": data_cfg["loader"],
        "simulation": data_cfg["simulation"],
        "data_samples": expected_pool,
        "num_samples_low": data_cfg.get("num_samples_low"),
        "num_samples_high": data_cfg.get("num_samples_high"),
        "split_counts": split_counts(config),
        "loss": loss,
        "splits": splits,
        "rng_replay": replay,
        "gate": gate,
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = config_path.stem
    save_json(audit, output_dir / f"{stem}_audit.json")
    write_markdown(audit, output_dir / f"{stem}_audit.md")
    print(audit["gate"])
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
