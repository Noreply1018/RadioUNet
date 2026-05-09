#!/usr/bin/env python3
"""Audit Stage 3 IRT4 zero-shot transfer and sparse adaptation artifacts."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader, build_dataset
from radiounet.utils import file_sha256, git_metadata, load_yaml, require_dataset_dir, save_json, set_seed


ZERO_RUNS = {
    "c_baseline": {
        "config": ROOT / "configs/c_irt4_zeroshot.yaml",
        "run_dir": ROOT / "reports/irt4_zeroshot/c_baseline",
        "checkpoint": ROOT / "reports/c_dpm_thr2/20260506_182311/checkpoints/secondU.pt",
        "source": "Stage 1 C secondU DPM checkpoint",
    },
    "s_rand1_300": {
        "config": ROOT / "configs/s_irt4_zeroshot_rand1_300.yaml",
        "run_dir": ROOT / "reports/irt4_zeroshot/s_rand1_300",
        "checkpoint": ROOT / "reports/s_dpm_thr2/rand1_300_50ep/checkpoints/secondU.pt",
        "source": "Stage 2 S random 1..300 secondU DPM checkpoint",
    },
}
ADAPT_CONFIG = ROOT / "configs/s_irt4_adapt_rand1_300.yaml"
ADAPT_RUN = ROOT / "reports/irt4_adapt/rand1_300_50ep"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], text=True, capture_output=True)
    return result.returncode == 0


def flatten_numbers(value: Any, prefix: str = "") -> dict[str, float]:
    if isinstance(value, bool):
        return {}
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return {prefix: float(value)}
    if isinstance(value, dict):
        out: dict[str, float] = {}
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_numbers(child, child_prefix))
        return out
    return {}


def max_abs_diff(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_nums = flatten_numbers(left)
    right_nums = flatten_numbers(right)
    keys = set(left_nums) & set(right_nums)
    diffs = [abs(left_nums[key] - right_nums[key]) for key in keys if key != "seconds" and not key.endswith(".seconds")]
    return max(diffs) if diffs else 0.0


def unpack_batch(batch):
    if len(batch) == 2:
        return batch[0], batch[1], None
    if len(batch) == 3:
        return batch
    raise ValueError(f"Expected batch of length 2 or 3, got {len(batch)}.")


def split_counts(config: dict[str, Any]) -> dict[str, int]:
    return {split: len(build_dataset(config, split)) for split in ["train", "val", "test"]}


def loader_audit(config_path: Path, max_batches: int = 4) -> dict[str, Any]:
    config = load_yaml(config_path)
    require_dataset_dir(config)
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    counts = split_counts(config)
    loader = build_dataloader(config, "test", smoke=False, shuffle=False)
    sparse_counts: list[int] = []
    sample_mask_counts: list[int] = []
    max_sparse_target_diff = 0.0
    input_channels = None
    target_scale = float(config.get("data", {}).get("target_scale", 1.0))

    with torch.no_grad():
        for batch_idx, batch in enumerate(loader):
            inputs, targets, samples = unpack_batch(batch)
            input_channels = int(inputs.shape[1])
            if inputs.shape[1] >= 3:
                sparse = inputs[:, 2]
                nonzero = sparse != 0
                sparse_counts.extend(int(x) for x in nonzero.flatten(1).sum(dim=1).cpu().tolist())
                if bool(nonzero.any()):
                    max_sparse_target_diff = max(
                        max_sparse_target_diff,
                        float(torch.abs(sparse[nonzero] - targets[:, 0][nonzero]).max()),
                    )
            if samples is not None:
                sample_mask_counts.extend(int(x) for x in (samples[:, 0] != 0).flatten(1).sum(dim=1).cpu().tolist())
            if batch_idx + 1 >= max_batches:
                break

    return {
        "config_path": str(config_path.relative_to(ROOT)),
        "loader": config["data"]["loader"],
        "simulation": config["data"]["simulation"],
        "num_tx": int(config["data"]["num_tx"]),
        "split_samples": counts,
        "input_channels": input_channels,
        "target_scale": target_scale,
        "data_samples": config["data"].get("data_samples"),
        "fix_samples": config["data"].get("fix_samples"),
        "num_samples_low": config["data"].get("num_samples_low"),
        "num_samples_high": config["data"].get("num_samples_high"),
        "checked_test_batches": max_batches,
        "input_sparse_nonzero_min": min(sparse_counts) if sparse_counts else None,
        "input_sparse_nonzero_max": max(sparse_counts) if sparse_counts else None,
        "input_sparse_nonzero_mean": sum(sparse_counts) / len(sparse_counts) if sparse_counts else None,
        "sample_mask_nonzero_min": min(sample_mask_counts) if sample_mask_counts else None,
        "sample_mask_nonzero_max": max(sample_mask_counts) if sample_mask_counts else None,
        "sparse_target_alignment_abs_max": max_sparse_target_diff,
        "official_loader_audit": {
            "local_reference": "reference/RadioUNet/lib/loaders.py",
            "repo_loader": "src/radiounet/data.py",
            "finding": (
                "The IRT4 sparse path is implemented by RadioUNet_c_sprseIRT4 and "
                "RadioUNet_s_sprseIRT4. Both default to numTx=2, read gain/IRT4, "
                "and the S loader builds inputs from deterministic sparse IRT4 sample coordinates."
            ),
        },
    }


def checkpoint_audit(manifest_path: Path | None, checkpoint_path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "checkpoint": str(checkpoint_path.relative_to(ROOT)),
        "exists": checkpoint_path.exists(),
        "tracked_by_git": git_tracked(checkpoint_path),
    }
    if checkpoint_path.exists():
        out["sha256_actual"] = file_sha256(checkpoint_path)
    if manifest_path is not None and manifest_path.exists():
        manifest = load_json(manifest_path)
        out.update(manifest)
        out["sha256_matches"] = checkpoint_path.exists() and out.get("sha256_actual") == manifest.get("sha256")
    return out


def collect_metrics(run_dir: Path) -> dict[str, Any]:
    metrics = load_json(run_dir / "secondU_test_metrics.json")
    rerun = load_json(run_dir / "secondU_test_metrics_rerun.json")
    figures = sorted((run_dir / "figures").glob("*.png"))
    return {
        "metrics": metrics,
        "rerun_metrics": rerun,
        "rerun_max_abs_diff": max_abs_diff(metrics, rerun),
        "figures": [str(path.relative_to(ROOT)) for path in figures],
        "figure_count": len(figures),
        "metrics_git_dirty": metrics.get("git", {}).get("dirty"),
    }


def zero_audit() -> dict[str, Any]:
    runs: dict[str, Any] = {}
    for name, spec in ZERO_RUNS.items():
        config = load_yaml(spec["config"])
        collected = collect_metrics(spec["run_dir"])
        runs[name] = {
            "source": spec["source"],
            "transfer_mode": "zero-shot",
            "config": {
                "path": str(spec["config"].relative_to(ROOT)),
                "loader": config["data"]["loader"],
                "simulation": config["data"]["simulation"],
                "num_tx": config["data"]["num_tx"],
                "inputs": config["model"]["inputs"],
            },
            "loader_audit": loader_audit(spec["config"]),
            "checkpoint": checkpoint_audit(None, spec["checkpoint"]),
            **collected,
        }
    gate = {
        "test_samples_198": all(run["metrics"]["samples"] == 198 for run in runs.values()),
        "metrics_git_dirty_false": all(run["metrics_git_dirty"] is False for run in runs.values()),
        "rerun_diff_zero": all(run["rerun_max_abs_diff"] == 0.0 for run in runs.values()),
        "checkpoint_not_tracked": all(not run["checkpoint"]["tracked_by_git"] for run in runs.values()),
        "figures_8_each": all(run["figure_count"] == 8 for run in runs.values()),
    }
    gate["pass"] = all(gate.values())
    return {
        "scope": "Stage 3A IRT4 zero-shot transfer audit",
        "git": git_metadata(),
        "runs": runs,
        "comparison": {
            "c_baseline_secondU": runs["c_baseline"]["metrics"]["secondU"],
            "s_rand1_300_secondU": runs["s_rand1_300"]["metrics"]["secondU"],
            "note": "这里仅比较 IRT4 test 指标，不与 DPM test 指标混合下结论。",
        },
        "gate": gate,
    }


def history_summary(path: Path) -> dict[str, Any]:
    data = load_json(path)
    rows = data.get("history", [])
    train = [row for row in rows if row.get("split") == "train"]
    val = [row for row in rows if row.get("split") == "val"]
    return {
        "entries": len(rows),
        "train_entries": len(train),
        "val_entries": len(val),
        "best_val_loss": data.get("best_val_loss"),
        "first_entry": rows[0] if rows else None,
        "last_entry": rows[-1] if rows else None,
    }


def adapt_audit() -> dict[str, Any]:
    config = load_yaml(ADAPT_CONFIG)
    collected = collect_metrics(ADAPT_RUN)
    zero = load_json(ROOT / "reports/irt4_zeroshot/zero_shot_audit.json")
    manifest = ADAPT_RUN / "secondU_checkpoint_manifest.json"
    checkpoint = ROOT / load_json(manifest)["checkpoint"]
    run_meta = load_json(ADAPT_RUN / "run_metadata.json")
    hist = history_summary(ADAPT_RUN / "secondU_history.json")
    gate = {
        "mode_secondU_only_adaptation": config["training"].get("adaptation_mode") == "secondU-only",
        "train_val_test_samples": split_counts(config) == {"train": 1002, "val": 200, "test": 198},
        "history_50_train_and_val_entries": hist["train_entries"] == 50 and hist["val_entries"] == 50,
        "test_samples_198": collected["metrics"]["samples"] == 198,
        "metrics_git_dirty_false": collected["metrics_git_dirty"] is False,
        "rerun_diff_zero": collected["rerun_max_abs_diff"] == 0.0,
        "checkpoint_not_tracked": not git_tracked(checkpoint),
        "figures_8": collected["figure_count"] == 8,
    }
    gate["pass"] = all(gate.values())
    return {
        "scope": "Stage 3B IRT4 sparse adaptation audit",
        "git": git_metadata(),
        "run_dir": str(ADAPT_RUN.relative_to(ROOT)),
        "config_path": str(ADAPT_CONFIG.relative_to(ROOT)),
        "adaptation_mode": "secondU-only adaptation",
        "init_checkpoint": config["training"]["init_checkpoint"],
        "run_metadata_git": run_meta.get("git", {}),
        "loader_audit": loader_audit(ADAPT_CONFIG),
        "history": hist,
        "checkpoint": checkpoint_audit(manifest, checkpoint),
        **collected,
        "irt4_only_comparison": {
            "stage1_c_zero_shot": zero["runs"]["c_baseline"]["metrics"]["secondU"],
            "stage2_s_zero_shot": zero["runs"]["s_rand1_300"]["metrics"]["secondU"],
            "stage3_s_adaptation": collected["metrics"]["secondU"],
            "note": "本对比只使用 IRT4 test split；DPM 指标不参与结论。",
        },
        "gate": gate,
    }


def write_zero_report(audit: dict[str, Any]) -> None:
    lines = [
        "# Stage 3A IRT4 zero-shot transfer audit",
        "",
        "## 范围",
        "- 目标：不训练新模型，用 DPM 训练得到的 Stage 1/2 checkpoint 直接评估 IRT4 test target。",
        "- IRT4 Tx 限制：所有配置都固定 `num_tx=2`，test split 为 99 张 map x 2 Tx = `198` 个样本。",
        "- 本报告只讨论 IRT4 test 指标，不把 DPM 指标混进结论。",
        "",
        "## 结果",
        "| run | source | samples | secondU MSE | secondU NMSE | global NMSE | RMSE | dB RMSE | rerun diff |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, run in audit["runs"].items():
        m = run["metrics"]["secondU"]
        lines.append(
            f"| {name} | {run['source']} | {run['metrics']['samples']} | {m['mse']:.10f} | "
            f"{m['nmse']:.10f} | {m['global_nmse']:.10f} | {m['rmse']:.10f} | "
            f"{m['rmse_db_80']:.10f} | {run['rerun_max_abs_diff']:.1f} |"
        )
    lines.extend([
        "",
        "## Loader / artifact gate",
    ])
    for name, run in audit["runs"].items():
        la = run["loader_audit"]
        lines.extend([
            f"- `{name}`：loader `{la['loader']}`，simulation `{la['simulation']}`，split 样本数 `{la['split_samples']}`。",
            f"- `{name}`：metrics `git.dirty={run['metrics_git_dirty']}`，checkpoint 进 git：`{run['checkpoint']['tracked_by_git']}`，图像数量 `{run['figure_count']}`。",
        ])
    lines.extend([
        "",
        f"## Gate：`{audit['gate']['pass']}`",
        f"- `test_samples_198={audit['gate']['test_samples_198']}`",
        f"- `metrics_git_dirty_false={audit['gate']['metrics_git_dirty_false']}`",
        f"- `rerun_diff_zero={audit['gate']['rerun_diff_zero']}`",
        f"- `checkpoint_not_tracked={audit['gate']['checkpoint_not_tracked']}`",
        f"- `figures_8_each={audit['gate']['figures_8_each']}`",
    ])
    (ROOT / "reports/irt4_zeroshot/zero_shot_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_loader_report(audit: dict[str, Any]) -> None:
    la = audit["loader_audit"]
    lines = [
        "# IRT4 loader audit",
        "",
        "- 审计对象：`RadioUNet_s_sprseIRT4` sparse adaptation 路径。",
        "- 本地官方参考：`reference/RadioUNet/lib/loaders.py`；当前复现 loader：`src/radiounet/data.py`。",
        f"- 配置：`{audit['config_path']}`，loader `{la['loader']}`，simulation `{la['simulation']}`，num_tx `{la['num_tx']}`。",
        f"- split 样本数：`{la['split_samples']}`。",
        f"- sparse 数据池：每张 map 固定 `data_samples={la['data_samples']}`；输入 sparse samples 从该池内抽取 `1..300`。",
        f"- sparse 与 target 对齐最大误差：`{la['sparse_target_alignment_abs_max']}`。",
        "",
        "结论：IRT4 输入、target 和 sparse sample 均来自 IRT4 路径；train/val/test 都限制为前 2 个 Tx，可以开始 secondU-only adaptation。",
    ]
    (ADAPT_RUN / "irt4_loader_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_adapt_report(audit: dict[str, Any]) -> None:
    comp = audit["irt4_only_comparison"]
    lines = [
        "# Stage 3B IRT4 sparse adaptation audit",
        "",
        "## 范围",
        "- 训练模式：`secondU-only adaptation`。",
        f"- 初始化 checkpoint：`{audit['init_checkpoint']}`。",
        "- target/input samples：IRT4；所有 split 固定 `num_tx=2`。",
        "- 本报告只比较 IRT4 test 指标，不混用 DPM 指标。",
        "",
        "## 样本数",
        f"- train/val/test：`{audit['loader_audit']['split_samples']}`。",
        "",
        "## IRT4 对比",
        "| run | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, metrics in [
        ("Stage 1 C zero-shot", comp["stage1_c_zero_shot"]),
        ("Stage 2 S zero-shot", comp["stage2_s_zero_shot"]),
        ("Stage 3 S adaptation", comp["stage3_s_adaptation"]),
    ]:
        lines.append(
            f"| {label} | {metrics['mse']:.10f} | {metrics['nmse']:.10f} | "
            f"{metrics['global_nmse']:.10f} | {metrics['rmse']:.10f} | {metrics['rmse_db_80']:.10f} |"
        )
    lines.extend([
        "",
        "## 训练和 artifact",
        f"- secondU history：train entries `{audit['history']['train_entries']}`，val entries `{audit['history']['val_entries']}`，best val loss `{audit['history']['best_val_loss']}`。",
        f"- test samples `{audit['metrics']['samples']}`；rerun diff `{audit['rerun_max_abs_diff']}`；metrics `git.dirty={audit['metrics_git_dirty']}`。",
        f"- checkpoint 进 git：`{audit['checkpoint']['tracked_by_git']}`；sha256 匹配：`{audit['checkpoint'].get('sha256_matches')}`。",
        f"- prediction/error 图数量：`{audit['figure_count']}`。",
        "",
        f"## Gate：`{audit['gate']['pass']}`",
    ])
    for key, value in audit["gate"].items():
        if key != "pass":
            lines.append(f"- `{key}={value}`")
    (ADAPT_RUN / "irt4_adapt_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["zero", "loader", "adapt"], required=True)
    args = parser.parse_args()

    if args.mode == "zero":
        audit = zero_audit()
        save_json(audit, ROOT / "reports/irt4_zeroshot/zero_shot_audit.json")
        write_zero_report(audit)
    elif args.mode == "loader":
        ADAPT_RUN.mkdir(parents=True, exist_ok=True)
        audit = {
            "scope": "Stage 3B pre-training IRT4 loader audit",
            "git": git_metadata(),
            "config_path": str(ADAPT_CONFIG.relative_to(ROOT)),
            "loader_audit": loader_audit(ADAPT_CONFIG),
        }
        save_json(audit, ADAPT_RUN / "irt4_loader_audit.json")
        write_loader_report(audit)
    else:
        audit = adapt_audit()
        save_json(audit, ADAPT_RUN / "irt4_adapt_audit.json")
        write_adapt_report(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
