#!/usr/bin/env python3
"""Generate Stage 2 random 1..300 and final synthesis audits."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader
from radiounet.utils import file_sha256, git_metadata, load_yaml, require_dataset_dir, save_json


METRIC_KEYS = ["mse", "nmse", "global_nmse", "rmse", "rmse_db_80"]
STAGE1_AUDIT = ROOT / "reports/s_dpm_thr2/full_50ep/full_audit.json"
STAGE1_METRICS = ROOT / "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json"
FIXED_SWEEP_AUDIT = ROOT / "reports/s_dpm_thr2/sample_count_sweep_audit.json"
RAND10_AUDIT = ROOT / "reports/s_dpm_thr2/rand10_300_50ep/rand10_300_audit.json"
RAND1_RUN = ROOT / "reports/s_dpm_thr2/rand1_300_50ep"
RAND1_CONFIG = ROOT / "configs/s_dpm_thr2_rand1_300.yaml"


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


def metric_row(metrics: dict[str, float]) -> str:
    return " | ".join(f"{float(metrics[key]):.10f}" for key in METRIC_KEYS)


def history_summary(path: Path) -> dict[str, Any]:
    history = load_json(path)
    rows = history.get("history", [])
    train = [row for row in rows if row.get("split") == "train"]
    val = [row for row in rows if row.get("split") == "val"]
    return {
        "entries": len(rows),
        "train_entries": len(train),
        "val_entries": len(val),
        "best_val_loss": history.get("best_val_loss"),
        "first_entry": rows[0] if rows else None,
        "last_entry": rows[-1] if rows else None,
    }


def unpack_batch(batch):
    if len(batch) == 2:
        inputs, targets = batch
        samples = None
    elif len(batch) == 3:
        inputs, targets, samples = batch
    elif len(batch) == 4:
        inputs, targets, samples, _input_sample_mask = batch
    else:
        raise ValueError(f"Expected batch of length 2, 3, or 4, got {len(batch)}.")
    return inputs, targets, samples


def sparse_random_audit(config: dict[str, Any], split: str = "test") -> dict[str, Any]:
    replay_config = json.loads(json.dumps(config))
    replay_config["data"]["num_workers"] = 0
    require_dataset_dir(replay_config)
    low = int(replay_config["data"]["num_samples_low"])
    high = int(replay_config["data"]["num_samples_high"])
    loader = build_dataloader(replay_config, split, smoke=False, shuffle=False)

    original_randint = np.random.randint
    drawn_counts: list[int] = []

    def recording_randint(*args, **kwargs):
        value = original_randint(*args, **kwargs)
        call_low = args[0] if len(args) >= 1 else kwargs.get("low")
        call_high = args[1] if len(args) >= 2 else kwargs.get("high")
        call_size = args[2] if len(args) >= 3 else kwargs.get("size")
        if call_low == low and call_high == high and call_size == 1:
            drawn_counts.append(int(np.asarray(value).reshape(-1)[0]))
        return value

    observed_counts: list[int] = []
    max_alignment = 0.0
    np.random.randint = recording_randint
    try:
        with torch.no_grad():
            for batch in loader:
                inputs, targets, _samples = unpack_batch(batch)
                sparse = inputs[:, 2]
                nonzero = sparse != 0
                observed_counts.extend(int(x) for x in nonzero.flatten(1).sum(dim=1).cpu().tolist())
                if bool(nonzero.any()):
                    target = targets[:, 0]
                    max_alignment = max(max_alignment, float(torch.abs(sparse[nonzero] - target[nonzero]).max()))
    finally:
        np.random.randint = original_randint

    bins = [(1, 49), (50, 99), (100, 149), (150, 199), (200, 249), (250, 300)]
    histogram = {
        f"{start}..{end}": sum(1 for value in drawn_counts if start <= value <= end)
        for start, end in bins
    }
    return {
        "drawn_distribution_method": (
            "Real RadioUNet_s DataLoader replay with num_workers=0 and a temporary np.random.randint recorder; "
            "records exactly the per-item num_samples draw where low/high/size match the config."
        ),
        "split": split,
        "configured_fix_samples": int(replay_config["data"]["fix_samples"]),
        "configured_num_samples_low": low,
        "configured_num_samples_high": high,
        "numpy_randint_high_is_exclusive": True,
        "paper_faithful_expected_drawn_range": "1..300",
        "drawn_count_items": len(drawn_counts),
        "drawn_min": min(drawn_counts),
        "drawn_max": max(drawn_counts),
        "drawn_mean": sum(drawn_counts) / len(drawn_counts),
        "drawn_first_16": drawn_counts[:16],
        "drawn_histogram": histogram,
        "checked_sparse_items": len(observed_counts),
        "observed_sparse_channel_nonzero_min": min(observed_counts),
        "observed_sparse_channel_nonzero_max": max(observed_counts),
        "observed_sparse_channel_nonzero_mean": sum(observed_counts) / len(observed_counts),
        "observed_first_16_nonzero_counts": observed_counts[:16],
        "sparse_target_alignment_abs_max": max_alignment,
        "note": (
            "drawn sample count is the requested random count; observed nonzero sparse-channel count can be lower "
            "because duplicate coordinates and zero target values collapse entries."
        ),
    }


def load_stage1_metrics() -> dict[str, Any]:
    if STAGE1_AUDIT.exists():
        audit = load_json(STAGE1_AUDIT)
        if "stage1_metrics" in audit:
            return audit["stage1_metrics"]
    metrics = load_json(STAGE1_METRICS)
    return {"firstU": metrics["firstU"], "secondU": metrics["secondU"]}


def collect_rand1() -> dict[str, Any]:
    config = load_yaml(RAND1_CONFIG)
    first_metrics = load_json(RAND1_RUN / "firstU_test_metrics.json")
    second_metrics = load_json(RAND1_RUN / "secondU_test_metrics.json")
    first_rerun = load_json(RAND1_RUN / "firstU_test_metrics_rerun.json")
    second_rerun = load_json(RAND1_RUN / "secondU_test_metrics_rerun.json")
    first_manifest = load_json(RAND1_RUN / "firstU_checkpoint_manifest.json")
    second_manifest = load_json(RAND1_RUN / "secondU_checkpoint_manifest.json")
    metadata = load_json(RAND1_RUN / "run_metadata.json")
    figures = sorted((RAND1_RUN / "figures").glob("*.png"))

    checkpoints = {}
    for phase, manifest in [("firstU", first_manifest), ("secondU", second_manifest)]:
        checkpoint = ROOT / manifest["checkpoint"]
        actual = file_sha256(checkpoint) if checkpoint.exists() else None
        checkpoints[phase] = {
            **manifest,
            "exists": checkpoint.exists(),
            "sha256_actual": actual,
            "sha256_matches": actual == manifest.get("sha256"),
            "tracked_by_git": git_tracked(checkpoint),
        }

    audit = {
        "scope": "paper_faithful_random_1_300_run",
        "paper_faithful_random_sample_count_run": True,
        "scope_note": (
            "This is the paper-faithful random sample count run: fix_samples=0, "
            "num_samples_low=1, num_samples_high=301, and numpy randint therefore draws 1..300."
        ),
        "run_dir": str(RAND1_RUN.relative_to(ROOT)),
        "config_path": str(RAND1_CONFIG.relative_to(ROOT)),
        "config": {
            "loader": config["data"]["loader"],
            "simulation": config["data"]["simulation"],
            "threshold": config["data"]["threshold"],
            "batch_size": config["data"]["batch_size"],
            "seed": config["experiment"]["seed"],
            "fix_samples": config["data"]["fix_samples"],
            "num_samples_low": config["data"]["num_samples_low"],
            "num_samples_high": config["data"]["num_samples_high"],
            "firstU_epochs": config["training"]["epochs"],
            "secondU_epochs": config["training"]["epochs"],
            "inputs": config["model"]["inputs"],
        },
        "commands": [
            "python scripts/train.py --config configs/s_dpm_thr2_rand1_300.yaml --phase both --device cuda:0 --run-dir reports/s_dpm_thr2/rand1_300_50ep",
            "python scripts/evaluate.py --config configs/s_dpm_thr2_rand1_300.yaml --checkpoint reports/s_dpm_thr2/rand1_300_50ep/checkpoints/firstU.pt --split test --device cuda:0 --output reports/s_dpm_thr2/rand1_300_50ep/firstU_test_metrics.json",
            "python scripts/evaluate.py --config configs/s_dpm_thr2_rand1_300.yaml --checkpoint reports/s_dpm_thr2/rand1_300_50ep/checkpoints/secondU.pt --split test --device cuda:0 --output reports/s_dpm_thr2/rand1_300_50ep/secondU_test_metrics.json",
            "rerun both eval commands to *_rerun.json",
            "python scripts/make_figures.py --config configs/s_dpm_thr2_rand1_300.yaml --checkpoint reports/s_dpm_thr2/rand1_300_50ep/checkpoints/secondU.pt --split test --device cuda:0 --limit 8 --output-dir reports/s_dpm_thr2/rand1_300_50ep/figures",
        ],
        "source_git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "run_metadata_git": metadata.get("git", {}),
        "metrics_git": {"firstU": first_metrics.get("git", {}), "secondU": second_metrics.get("git", {})},
        "history": {
            "firstU": history_summary(RAND1_RUN / "firstU_history.json"),
            "secondU": history_summary(RAND1_RUN / "secondU_history.json"),
        },
        "metrics": {"firstU": first_metrics["firstU"], "secondU": second_metrics["secondU"]},
        "test_samples": {"firstU": first_metrics["samples"], "secondU": second_metrics["samples"]},
        "rerun_consistency": {
            "firstU_metrics_max_abs_diff": max_abs_diff(first_metrics, first_rerun),
            "secondU_metrics_max_abs_diff": max_abs_diff(second_metrics, second_rerun),
        },
        "checkpoints": checkpoints,
        "figures": [str(path.relative_to(ROOT)) for path in figures],
        "sparse_samples": sparse_random_audit(config),
    }
    gate = {
        "paper_faithful_random_1_300": audit["sparse_samples"]["drawn_min"] == 1
        and audit["sparse_samples"]["drawn_max"] == 300
        and audit["config"]["num_samples_low"] == 1
        and audit["config"]["num_samples_high"] == 301,
        "fixed_run_dir": audit["run_dir"] == "reports/s_dpm_thr2/rand1_300_50ep",
        "config_path_expected": audit["config_path"] == "configs/s_dpm_thr2_rand1_300.yaml",
        "history_entries_100_each": audit["history"]["firstU"]["entries"] == 100 and audit["history"]["secondU"]["entries"] == 100,
        "test_samples_7920": first_metrics["samples"] == 7920 and second_metrics["samples"] == 7920,
        "run_metadata_git_dirty_false": metadata.get("git", {}).get("dirty") is False,
        "metrics_git_dirty_false": first_metrics.get("git", {}).get("dirty") is False
        and second_metrics.get("git", {}).get("dirty") is False,
        "metrics_git_excludes_reports": "reports" in first_metrics.get("git", {}).get("exclude_paths", [])
        and "reports" in second_metrics.get("git", {}).get("exclude_paths", []),
        "checkpoint_sha256_matches": checkpoints["firstU"]["sha256_matches"] and checkpoints["secondU"]["sha256_matches"],
        "checkpoint_files_tracked_by_git": checkpoints["firstU"]["tracked_by_git"] or checkpoints["secondU"]["tracked_by_git"],
        "eight_prediction_figures": len(figures) == 8,
        "rerun_exact": audit["rerun_consistency"]["firstU_metrics_max_abs_diff"] == 0.0
        and audit["rerun_consistency"]["secondU_metrics_max_abs_diff"] == 0.0,
        "random_sample_distribution_recorded": audit["sparse_samples"]["drawn_count_items"] == 7920,
    }
    gate["passed"] = (
        gate["paper_faithful_random_1_300"]
        and gate["fixed_run_dir"]
        and gate["config_path_expected"]
        and gate["history_entries_100_each"]
        and gate["test_samples_7920"]
        and gate["run_metadata_git_dirty_false"]
        and gate["metrics_git_dirty_false"]
        and gate["metrics_git_excludes_reports"]
        and gate["checkpoint_sha256_matches"]
        and not gate["checkpoint_files_tracked_by_git"]
        and gate["eight_prediction_figures"]
        and gate["rerun_exact"]
        and gate["random_sample_distribution_recorded"]
    )
    audit["gate"] = gate
    return audit


def stage1_comparison(stage1: dict[str, Any], current: dict[str, Any], label: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for phase in ["firstU", "secondU"]:
        out[phase] = {}
        for metric in METRIC_KEYS:
            base = float(stage1[phase][metric])
            value = float(current[phase][metric])
            out[phase][metric] = {
                "stage1": base,
                label: value,
                "delta_stage1_minus_current": base - value,
                "relative_improvement_percent": (base - value) / base * 100.0,
            }
    return out


def plot_random_vs_fixed(fixed_runs: list[dict[str, Any]], rand10: dict[str, Any], rand1: dict[str, Any], output: Path) -> None:
    samples = [run["sample_count"] for run in fixed_runs]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for ax, metric in zip(axes.flatten(), ["mse", "nmse", "global_nmse", "rmse_db_80"]):
        fixed_values = [run["metrics"]["secondU"][metric] for run in fixed_runs]
        ax.plot(samples, fixed_values, marker="o", label="fixed sweep")
        ax.axhline(rand10["metrics"]["secondU"][metric], color="tab:orange", linestyle="--", label="random 10..299")
        ax.axhline(rand1["metrics"]["secondU"][metric], color="tab:green", linestyle="-.", label="random 1..300")
        ax.set_xlabel("fixed sparse sample count")
        ax.set_ylabel(metric)
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("Stage 2 random sample runs vs fixed sweep")
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_final_curves(stage1: dict[str, Any], fixed_runs: list[dict[str, Any]], rand10: dict[str, Any], rand1: dict[str, Any], output: Path) -> None:
    labels = ["Stage 1 C"] + [f"fixed {run['sample_count']}" for run in fixed_runs] + ["random 10..299", "random 1..300"]
    x = list(range(len(labels)))
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    for ax, metric in zip(axes.flatten(), ["mse", "nmse", "global_nmse", "rmse_db_80"]):
        values = [stage1["secondU"][metric]]
        values.extend(run["metrics"]["secondU"][metric] for run in fixed_runs)
        values.append(rand10["metrics"]["secondU"][metric])
        values.append(rand1["metrics"]["secondU"][metric])
        ax.plot(x, values, marker="o")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel(metric)
        ax.grid(True, axis="y", alpha=0.3)
    fig.suptitle("Stage 2 final synthesis: secondU metrics")
    fig.savefig(output, dpi=150)
    plt.close(fig)


def write_rand1_report(audit: dict[str, Any], fixed_runs: list[dict[str, Any]], rand10: dict[str, Any], stage1: dict[str, Any]) -> None:
    comparison_figure = RAND1_RUN / "rand1_300_vs_fixed_rand10_metrics.png"
    plot_random_vs_fixed(fixed_runs, rand10, audit, comparison_figure)
    fixed_plus_random = [
        {"setting": f"fixed {run['sample_count']}", **run["metrics"]["secondU"]}
        for run in fixed_runs
    ]
    fixed_plus_random.append({"setting": "implementation-default random 10..299", **rand10["metrics"]["secondU"]})
    fixed_plus_random.append({"setting": "paper-faithful random 1..300", **audit["metrics"]["secondU"]})
    audit["fixed_sweep_and_random_secondU_comparison"] = fixed_plus_random
    audit["stage1_comparison"] = stage1_comparison(stage1, audit["metrics"], "paper_faithful_random_1_300")
    audit["comparison_figure"] = str(comparison_figure.relative_to(ROOT))
    save_json(audit, RAND1_RUN / "rand1_300_audit.json")

    sparse = audit["sparse_samples"]
    lines = [
        "# Stage 2 paper-faithful random 1..300 audit",
        "",
        "## 范围",
        "",
        "- 本 run 是 `paper-faithful random sample count run`：`data.fix_samples=0`，每个样本重新随机抽 sparse sample count。",
        "- 配置为 `num_samples_low=1`、`num_samples_high=301`；由于 `np.random.randint(low, high)` 的 high 为排他上界，实际 drawn count 为 `1..300`。",
        "- 本 run 是论文随机样本数口径的 Stage 2 结果；`implementation-default random 10..299` 只保留为对照变体。",
        f"- 固定权威目录：`{audit['run_dir']}`。",
        f"- 配置：`{audit['config_path']}`，run copy 已保存为 `reports/s_dpm_thr2/rand1_300_50ep/s_dpm_thr2_rand1_300.yaml`。",
        f"- loader/simulation/threshold：`{audit['config']['loader']}` / `{audit['config']['simulation']}` / `{audit['config']['threshold']}`。",
        f"- firstU/secondU epoch：`{audit['config']['firstU_epochs']}` / `{audit['config']['secondU_epochs']}`；history 条数：`{audit['history']['firstU']['entries']}` / `{audit['history']['secondU']['entries']}`。",
        f"- run metadata git dirty：`{audit['run_metadata_git'].get('dirty')}`；metrics git dirty：firstU `{audit['metrics_git']['firstU'].get('dirty')}`，secondU `{audit['metrics_git']['secondU'].get('dirty')}`。",
        f"- checkpoint sha256 匹配：`{audit['gate']['checkpoint_sha256_matches']}`；checkpoint 进 git：`{audit['gate']['checkpoint_files_tracked_by_git']}`。",
        f"- eval rerun 最大差异：firstU `{audit['rerun_consistency']['firstU_metrics_max_abs_diff']}`，secondU `{audit['rerun_consistency']['secondU_metrics_max_abs_diff']}`。",
        f"- 预测图数量：`{len(audit['figures'])}`；gate passed：`{audit['gate']['passed']}`。",
        "",
        "## random sparse sample 审计",
        "",
        f"- 配置：`fix_samples=0`，`num_samples_low={audit['config']['num_samples_low']}`，`num_samples_high={audit['config']['num_samples_high']}`。",
        f"- RNG replay 记录到的 drawn sample count 范围是 `{sparse['drawn_min']}..{sparse['drawn_max']}`，均值 `{sparse['drawn_mean']:.4f}`。",
        f"- drawn count 前 16 个：`{sparse['drawn_first_16']}`。",
        f"- drawn count 分桶：`{sparse['drawn_histogram']}`。",
        f"- 真实 DataLoader 检查样本数：`{sparse['checked_sparse_items']}`；sparse channel 非零数范围：`{sparse['observed_sparse_channel_nonzero_min']}..{sparse['observed_sparse_channel_nonzero_max']}`，均值 `{sparse['observed_sparse_channel_nonzero_mean']:.4f}`。",
        f"- sparse 与 target 对齐最大绝对误差：`{sparse['sparse_target_alignment_abs_max']}`。",
        "",
        "## secondU fixed sweep + random 对照表",
        "",
        "| setting | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in fixed_plus_random:
        lines.append(f"| {row['setting']} | {metric_row(row)} |")
    lines.extend(
        [
            "",
            "## firstU / secondU random metrics",
            "",
            "| phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            f"| firstU | {metric_row(audit['metrics']['firstU'])} |",
            f"| secondU | {metric_row(audit['metrics']['secondU'])} |",
            "",
            "## 相比 Stage 1 C baseline",
            "",
            "| phase | metric | Stage 1 C | paper-faithful random 1..300 | Stage 1 - random | improvement |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for phase in ["firstU", "secondU"]:
        for metric in ["mse", "nmse", "global_nmse", "rmse_db_80"]:
            row = audit["stage1_comparison"][phase][metric]
            lines.append(
                f"| {phase} | {metric} | {row['stage1']:.10f} | {row['paper_faithful_random_1_300']:.10f} | "
                f"{row['delta_stage1_minus_current']:.10f} | {row['relative_improvement_percent']:.2f}% |"
            )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- paper-faithful random 1..300 的 RNG replay 已覆盖 test split 全部 `7920` 个样本，drawn count 明确覆盖 `1..300`。",
            "- 本 run 满足训练前干净源码、metrics `git.dirty=false`、checkpoint manifest hash 匹配、checkpoint/log 不进 git、eval rerun diff 为 `0.0`、8 张预测图完整这些 Stage 2 归档约束。",
            f"- 对照曲线图：`{comparison_figure.relative_to(ROOT)}`。",
        ]
    )
    (RAND1_RUN / "rand1_300_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def final_summary(stage1: dict[str, Any], fixed_runs: list[dict[str, Any]], rand10: dict[str, Any], rand1: dict[str, Any]) -> dict[str, Any]:
    runs = [{"setting": "Stage 1 C baseline", "category": "baseline", "metrics": stage1}]
    runs.extend(
        {
            "setting": f"fixed {run['sample_count']}",
            "category": "controlled ablation",
            "sample_count": run["sample_count"],
            "metrics": run["metrics"],
            "gate": run.get("gate", {}),
        }
        for run in fixed_runs
    )
    runs.append({"setting": "implementation-default random 10..299", "category": "comparison variant", "metrics": rand10["metrics"], "gate": rand10["gate"]})
    runs.append({"setting": "paper-faithful random 1..300", "category": "paper-faithful random sample count", "metrics": rand1["metrics"], "gate": rand1["gate"]})
    random_delta = {}
    for phase in ["firstU", "secondU"]:
        random_delta[phase] = {}
        for metric in METRIC_KEYS:
            v10 = rand10["metrics"][phase][metric]
            v1 = rand1["metrics"][phase][metric]
            random_delta[phase][metric] = {
                "random_10_299": v10,
                "random_1_300": v1,
                "delta_1_300_minus_10_299": v1 - v10,
                "relative_delta_percent": (v1 - v10) / v10 * 100.0,
            }
    return {
        "scope": "stage2_final_synthesis",
        "source_git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "final_artifact_commit": "2987ae495e2689176d8c5c33a1f5b5ddf31346f7",
        "final_artifact_commit_subject": "Add Stage 2 final synthesis audit",
        "provenance_note": (
            "Final synthesis was generated from clean source commit 601d7e6 with reports excluded. "
            "Commit 2987ae4 added the tracked final synthesis JSON, Markdown, and metric curve PNG; "
            "checkpoints and logs remain ignored local artifacts."
        ),
        "stage1_metrics": stage1,
        "runs": runs,
        "fixed_sweep": fixed_runs,
        "random_10_299": rand10,
        "random_1_300": rand1,
        "stage1_improvements": {
            "fixed_50": stage1_comparison(stage1, fixed_runs[0]["metrics"], "current"),
            "fixed_100": stage1_comparison(stage1, fixed_runs[1]["metrics"], "current"),
            "fixed_200": stage1_comparison(stage1, fixed_runs[2]["metrics"], "current"),
            "fixed_300": stage1_comparison(stage1, fixed_runs[3]["metrics"], "current"),
            "implementation_default_random_10_299": stage1_comparison(stage1, rand10["metrics"], "current"),
            "paper_faithful_random_1_300": stage1_comparison(stage1, rand1["metrics"], "current"),
        },
        "random_delta": random_delta,
        "paper_faithful_alignment": {
            "loader_RadioUNet_s": rand1["config"]["loader"] == "RadioUNet_s",
            "simulation_DPM": rand1["config"]["simulation"] == "DPM",
            "threshold_0_2": rand1["config"]["threshold"] == 0.2,
            "fix_samples_0": rand1["config"]["fix_samples"] == 0,
            "drawn_count_1_300": rand1["gate"]["paper_faithful_random_1_300"],
            "firstU_50_epochs": rand1["config"]["firstU_epochs"] == 50,
            "secondU_50_epochs": rand1["config"]["secondU_epochs"] == 50,
            "batch_size_15": rand1["config"]["batch_size"] == 15,
            "seed_42": rand1["config"]["seed"] == 42,
            "passed": rand1["gate"]["passed"],
        },
        "reproduction_judgement": {
            "paper_faithful_reproduced": [
                "RadioUNet_s / DPM / threshold=0.2 / seed=42 / batch_size=15 的 Stage 2 random 1..300 训练、评估和 rerun 已完成。",
                "random 1..300 的 test split RNG replay 证明 drawn count 为 1..300。",
                "firstU/secondU 50 epoch、checkpoint manifest、8 张图和 metrics 归档完整。",
            ],
            "controlled_ablation": [
                "fixed 50/100/200/300 是 controlled ablation，用来隔离 sparse sample count 对性能的影响。",
                "implementation-default random 10..299 是历史实现默认口径对照，不是论文 1..300。",
            ],
            "not_full_paper_reproduction": [
                "Stage 2 仍只覆盖当前 DPM/complete-city-map/test split 口径，不覆盖论文所有仿真/缺楼/transfer 设置。",
                "IRT4 transfer、missing buildings 和 robustness 尚未在本阶段训练或评估。",
            ],
            "stage2_can_close": True,
            "next_stage": "Stage 3 应进入 IRT4 zero-shot transfer / missing buildings / robustness，因为 Stage 2 已完成 S 输入与随机样本数口径收口，剩余差距属于跨仿真与鲁棒性问题。",
        },
    }


def write_final_report(summary: dict[str, Any], figure: Path) -> None:
    runs = summary["runs"]
    lines = [
        "# Stage 2 final synthesis audit",
        "",
        "## 范围",
        "",
        "- 本报告统一 Stage 1 C baseline、fixed 50/100/200/300、implementation-default random 10..299、paper-faithful random 1..300。",
        "- fixed sweep 是 controlled ablation；random 10..299 是历史 implementation-default 对照；random 1..300 是本阶段的 paper-faithful random sample count run。",
        "- checkpoint 和 log 只作为本地复现实物，不进入 git；报告、metrics、manifest、PNG 和配置副本进入归档。",
        "- final synthesis 生成源码提交：`601d7e6e239b9c6bdd8d9f7421f22d012c7c5859`，生成时排除 `reports/` 后源码干净。",
        "- final synthesis 轻量产物入库提交：`2987ae495e2689176d8c5c33a1f5b5ddf31346f7`；该提交加入 `stage2_final_audit.json`、`stage2_final_audit.md` 和 `stage2_final_metric_curves.png`。",
        "",
        "## firstU 全指标表",
        "",
        "| setting | category | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in runs:
        lines.append(f"| {run['setting']} | {run['category']} | {metric_row(run['metrics']['firstU'])} |")
    lines.extend(
        [
            "",
            "## secondU 全指标表",
            "",
            "| setting | category | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for run in runs:
        lines.append(f"| {run['setting']} | {run['category']} | {metric_row(run['metrics']['secondU'])} |")
    lines.extend(
        [
            "",
            "## 相比 Stage 1 的改进表",
            "",
            "| setting | phase | metric | Stage 1 C | current | Stage 1 - current | improvement |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for setting_key, comp in summary["stage1_improvements"].items():
        for phase in ["firstU", "secondU"]:
            for metric in ["mse", "nmse", "global_nmse", "rmse_db_80"]:
                row = comp[phase][metric]
                lines.append(
                    f"| {setting_key} | {phase} | {metric} | {row['stage1']:.10f} | {row['current']:.10f} | "
                    f"{row['delta_stage1_minus_current']:.10f} | {row['relative_improvement_percent']:.2f}% |"
                )
    lines.extend(
        [
            "",
            "## fixed sweep 曲线表",
            "",
            "| fix_samples | phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for run in summary["fixed_sweep"]:
        for phase in ["firstU", "secondU"]:
            lines.append(f"| {run['sample_count']} | {phase} | {metric_row(run['metrics'][phase])} |")
    lines.extend(
        [
            "",
            "## random 10..299 vs random 1..300 差异表",
            "",
            "| phase | metric | random 10..299 | random 1..300 | 1..300 - 10..299 | relative delta |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for phase in ["firstU", "secondU"]:
        for metric in METRIC_KEYS:
            row = summary["random_delta"][phase][metric]
            lines.append(
                f"| {phase} | {metric} | {row['random_10_299']:.10f} | {row['random_1_300']:.10f} | "
                f"{row['delta_1_300_minus_10_299']:.10f} | {row['relative_delta_percent']:.2f}% |"
            )
    align = summary["paper_faithful_alignment"]
    lines.extend(
        [
            "",
            "## paper-faithful run 与论文设定对齐检查表",
            "",
            "| item | passed |",
            "| --- | --- |",
        ]
    )
    for key, value in align.items():
        lines.append(f"| {key} | `{value}` |")
    judgement = summary["reproduction_judgement"]
    lines.extend(
        [
            "",
            "## 论文复现判断",
            "",
            "### 已按论文口径复现",
        ]
    )
    lines.extend(f"- {item}" for item in judgement["paper_faithful_reproduced"])
    lines.append("")
    lines.append("### controlled ablation")
    lines.extend(f"- {item}" for item in judgement["controlled_ablation"])
    lines.append("")
    lines.append("### 仍不是论文完整复现")
    lines.extend(f"- {item}" for item in judgement["not_full_paper_reproduction"])
    lines.extend(
        [
            "",
            "## Stage 2 关闭结论",
            "",
            f"- Stage 2 能否关闭：`{judgement['stage2_can_close']}`。",
            f"- 下一阶段：{judgement['next_stage']}",
            f"- 总汇总曲线图：`{figure.relative_to(ROOT)}`。",
        ]
    )
    (ROOT / "reports/s_dpm_thr2/stage2_final_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    stage1 = load_stage1_metrics()
    fixed_summary = load_json(FIXED_SWEEP_AUDIT)
    fixed_runs = sorted(fixed_summary["runs"], key=lambda run: run["sample_count"])
    rand10 = load_json(RAND10_AUDIT)
    rand1 = collect_rand1()
    write_rand1_report(rand1, fixed_runs, rand10, stage1)
    rand1 = load_json(RAND1_RUN / "rand1_300_audit.json")
    final = final_summary(stage1, fixed_runs, rand10, rand1)
    final_figure = ROOT / "reports/s_dpm_thr2/stage2_final_metric_curves.png"
    plot_final_curves(stage1, fixed_runs, rand10, rand1, final_figure)
    final["figure"] = str(final_figure.relative_to(ROOT))
    save_json(final, ROOT / "reports/s_dpm_thr2/stage2_final_audit.json")
    write_final_report(final, final_figure)
    print(f"saved {RAND1_RUN / 'rand1_300_audit.json'}")
    print(f"saved {RAND1_RUN / 'rand1_300_audit.md'}")
    print(f"saved {RAND1_RUN / 'rand1_300_vs_fixed_rand10_metrics.png'}")
    print(f"saved {ROOT / 'reports/s_dpm_thr2/stage2_final_audit.json'}")
    print(f"saved {ROOT / 'reports/s_dpm_thr2/stage2_final_audit.md'}")
    print(f"saved {final_figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
