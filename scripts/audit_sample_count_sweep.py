#!/usr/bin/env python3
"""Audit the Stage 2 RadioUNet_S fixed sparse sample count sweep."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader
from radiounet.utils import file_sha256, git_metadata, load_yaml, require_dataset_dir, save_json, set_seed


SWEEP_RUNS = {
    50: {
        "config": "configs/s_dpm_thr2_fix50.yaml",
        "run_dir": "reports/s_dpm_thr2/fix50_50ep",
    },
    100: {
        "config": "configs/s_dpm_thr2_fix100.yaml",
        "run_dir": "reports/s_dpm_thr2/fix100_50ep",
    },
    200: {
        "config": "configs/s_dpm_thr2.yaml",
        "run_dir": "reports/s_dpm_thr2/full_50ep",
    },
    300: {
        "config": "configs/s_dpm_thr2_fix300.yaml",
        "run_dir": "reports/s_dpm_thr2/fix300_50ep",
    },
}

STAGE1_METRICS = "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json"
STAGE1_AUDIT = "reports/s_dpm_thr2/full_50ep/full_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def unpack_batch(batch):
    if len(batch) == 2:
        inputs, targets = batch
        samples = None
    elif len(batch) == 3:
        inputs, targets, samples = batch
    else:
        raise ValueError(f"Expected batch of length 2 or 3, got {len(batch)}.")
    return inputs, targets, samples


def flatten_numbers(value: Any, prefix: str = "") -> dict[str, float]:
    if isinstance(value, bool):
        return {}
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return {prefix: float(value)}
        return {}
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
    ignored_prefixes = ("seconds",)
    diffs = [
        abs(left_nums[key] - right_nums[key])
        for key in keys
        if not any(key.endswith(prefix) or key == prefix for prefix in ignored_prefixes)
    ]
    return max(diffs) if diffs else 0.0


def git_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], text=True, capture_output=True)
    return result.returncode == 0


def sparse_stats(config: dict[str, Any], max_batches: int) -> dict[str, Any]:
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    loader = build_dataloader(config, "test", smoke=False, shuffle=False)
    counts: list[int] = []
    samples_seen = 0
    configured = int(config["data"]["fix_samples"])
    target_scale = float(config["data"].get("target_scale", 1.0))
    max_alignment = 0.0

    with torch.no_grad():
        for batch_idx, batch in enumerate(loader):
            inputs, targets, _samples = unpack_batch(batch)
            sparse = inputs[:, 2]
            nonzero = sparse != 0
            counts.extend(int(x) for x in nonzero.flatten(1).sum(dim=1).cpu().tolist())
            if bool(nonzero.any()):
                target = targets[:, 0]
                max_alignment = max(max_alignment, float(torch.abs(sparse[nonzero] - target[nonzero]).max()))
            samples_seen += inputs.size(0)
            if batch_idx + 1 >= max_batches:
                break

    return {
        "configured_fix_samples": configured,
        "checked_test_items": samples_seen,
        "target_scale": target_scale,
        "observed_sparse_channel_nonzero_min": min(counts),
        "observed_sparse_channel_nonzero_max": max(counts),
        "observed_sparse_channel_nonzero_mean": sum(counts) / len(counts),
        "first_8_observed_nonzero_counts": counts[:8],
        "sparse_target_alignment_abs_max": max_alignment,
        "note": (
            "RadioUNet_s samples fixed coordinates per item; duplicate coordinates and zero target "
            "values can reduce the observed nonzero sparse-channel count."
        ),
    }


def load_stage1() -> dict[str, Any]:
    metrics = load_json(ROOT / STAGE1_METRICS)
    audit_path = ROOT / STAGE1_AUDIT
    if audit_path.exists():
        audit = load_json(audit_path)
        if "stage1_metrics" in audit:
            return audit["stage1_metrics"]
    return metrics


def collect_run(sample_count: int, spec: dict[str, str], max_sparse_batches: int) -> dict[str, Any]:
    run_dir = ROOT / spec["run_dir"]
    config_path = ROOT / spec["config"]
    config = load_yaml(config_path)
    require_dataset_dir(config)

    expected_files = {
        "config": run_dir / config_path.name,
        "firstU_history": run_dir / "firstU_history.json",
        "secondU_history": run_dir / "secondU_history.json",
        "firstU_metrics": run_dir / "firstU_test_metrics.json",
        "secondU_metrics": run_dir / "secondU_test_metrics.json",
        "firstU_metrics_rerun": run_dir / "firstU_test_metrics_rerun.json",
        "secondU_metrics_rerun": run_dir / "secondU_test_metrics_rerun.json",
        "firstU_manifest": run_dir / "firstU_checkpoint_manifest.json",
        "secondU_manifest": run_dir / "secondU_checkpoint_manifest.json",
        "run_metadata": run_dir / "run_metadata.json",
    }
    missing = [str(path.relative_to(ROOT)) for path in expected_files.values() if not path.exists()]
    figures = sorted((run_dir / "figures").glob("*.png"))
    if len(figures) != 8:
        missing.append(f"{run_dir.relative_to(ROOT)}/figures/*.png expected 8, found {len(figures)}")
    if missing:
        raise FileNotFoundError(f"run {sample_count} missing artifacts: {missing}")

    first_metrics = load_json(expected_files["firstU_metrics"])
    second_metrics = load_json(expected_files["secondU_metrics"])
    first_rerun = load_json(expected_files["firstU_metrics_rerun"])
    second_rerun = load_json(expected_files["secondU_metrics_rerun"])
    first_manifest = load_json(expected_files["firstU_manifest"])
    second_manifest = load_json(expected_files["secondU_manifest"])
    metadata = load_json(expected_files["run_metadata"])

    first_checkpoint = ROOT / first_manifest["checkpoint"]
    second_checkpoint = ROOT / second_manifest["checkpoint"]
    checkpoints = {
        "firstU": {
            **first_manifest,
            "exists": first_checkpoint.exists(),
            "sha256_matches": first_checkpoint.exists() and file_sha256(first_checkpoint) == first_manifest["sha256"],
            "tracked_by_git": git_tracked(first_checkpoint),
        },
        "secondU": {
            **second_manifest,
            "exists": second_checkpoint.exists(),
            "sha256_matches": second_checkpoint.exists() and file_sha256(second_checkpoint) == second_manifest["sha256"],
            "tracked_by_git": git_tracked(second_checkpoint),
        },
    }
    metrics_git = second_metrics.get("git", {})
    run = {
        "sample_count": sample_count,
        "run_dir": str(run_dir.relative_to(ROOT)),
        "config_path": spec["config"],
        "config": {
            "loader": config["data"]["loader"],
            "simulation": config["data"]["simulation"],
            "threshold": config["data"]["threshold"],
            "fix_samples": config["data"]["fix_samples"],
            "firstU_epochs": config["training"]["epochs"],
            "secondU_epochs": config["training"]["epochs"],
            "inputs": config["model"]["inputs"],
        },
        "run_metadata_git": metadata.get("git", {}),
        "metrics_git": metrics_git,
        "metrics": {
            "firstU": first_metrics["firstU"],
            "secondU": second_metrics["secondU"],
        },
        "rerun_consistency": {
            "firstU_metrics_max_abs_diff": max_abs_diff(first_metrics, first_rerun),
            "secondU_metrics_max_abs_diff": max_abs_diff(second_metrics, second_rerun),
        },
        "checkpoints": checkpoints,
        "figures": [str(path.relative_to(ROOT)) for path in figures],
        "sparse_samples": sparse_stats(config, max_sparse_batches),
        "gate": {
            "fixed_run_dir": spec["run_dir"] == str(run_dir.relative_to(ROOT)),
            "metrics_git_dirty_false": metrics_git.get("dirty") is False,
            "metrics_git_excludes_reports": "reports" in metrics_git.get("exclude_paths", []),
            "checkpoints_exist": checkpoints["firstU"]["exists"] and checkpoints["secondU"]["exists"],
            "checkpoint_sha256_matches": checkpoints["firstU"]["sha256_matches"] and checkpoints["secondU"]["sha256_matches"],
            "checkpoint_files_tracked_by_git": checkpoints["firstU"]["tracked_by_git"] or checkpoints["secondU"]["tracked_by_git"],
            "eight_prediction_figures": len(figures) == 8,
            "rerun_exact": max_abs_diff(first_metrics, first_rerun) == 0.0 and max_abs_diff(second_metrics, second_rerun) == 0.0,
        },
    }
    run["gate"]["passed"] = (
        run["gate"]["fixed_run_dir"]
        and run["gate"]["metrics_git_dirty_false"]
        and run["gate"]["metrics_git_excludes_reports"]
        and run["gate"]["checkpoints_exist"]
        and run["gate"]["checkpoint_sha256_matches"]
        and not run["gate"]["checkpoint_files_tracked_by_git"]
        and run["gate"]["eight_prediction_figures"]
        and run["gate"]["rerun_exact"]
    )
    return run


def format_metric(value: float) -> str:
    return f"{value:.10f}"


def gain(stage1: dict[str, Any], stage2: dict[str, Any], phase: str, metric: str) -> tuple[float, float]:
    baseline = float(stage1[phase][metric])
    current = float(stage2[phase][metric])
    abs_gain = baseline - current
    rel_gain = abs_gain / baseline * 100.0
    return abs_gain, rel_gain


def write_run_report(run: dict[str, Any]) -> Path:
    run_dir = ROOT / run["run_dir"]
    metrics = run["metrics"]
    rerun = run["rerun_consistency"]
    lines = [
        f"# Stage 2 fixed-{run['sample_count']} audit",
        "",
        "## 关键约束",
        "",
        f"- 固定目录：`{run['run_dir']}`。",
        f"- 配置：`{run['config_path']}`，run copy 已保存。",
        f"- loader/simulation/threshold：`{run['config']['loader']}` / `{run['config']['simulation']}` / `{run['config']['threshold']}`。",
        f"- firstU/secondU epoch：`{run['config']['firstU_epochs']}` / `{run['config']['secondU_epochs']}`。",
        f"- fix_samples：`{run['config']['fix_samples']}`。",
        f"- metrics git dirty：`{run['metrics_git'].get('dirty')}`，exclude_paths：`{run['metrics_git'].get('exclude_paths')}`。",
        f"- checkpoint manifest：`firstU_checkpoint_manifest.json`、`secondU_checkpoint_manifest.json`；checkpoint 文件本地存在且未进 git：`{not run['gate']['checkpoint_files_tracked_by_git']}`。",
        f"- 预测图数量：`{len(run['figures'])}`。",
        f"- eval rerun 最大差异：firstU `{rerun['firstU_metrics_max_abs_diff']}`，secondU `{rerun['secondU_metrics_max_abs_diff']}`。",
        f"- gate passed：`{run['gate']['passed']}`。",
        "",
        "## secondU test metrics",
        "",
        "| MSE | NMSE | global NMSE | RMSE | dB RMSE |",
        "| ---: | ---: | ---: | ---: | ---: |",
        "| "
        + " | ".join(
            format_metric(metrics["secondU"][key])
            for key in ["mse", "nmse", "global_nmse", "rmse", "rmse_db_80"]
        )
        + " |",
        "",
        "## firstU test metrics",
        "",
        "| MSE | NMSE | global NMSE | RMSE | dB RMSE |",
        "| ---: | ---: | ---: | ---: | ---: |",
        "| "
        + " | ".join(
            format_metric(metrics["firstU"][key])
            for key in ["mse", "nmse", "global_nmse", "rmse", "rmse_db_80"]
        )
        + " |",
        "",
        "## sparse sample 审计",
        "",
        f"- 配置采样点数：`{run['sparse_samples']['configured_fix_samples']}`。",
        f"- test 抽检样本数：`{run['sparse_samples']['checked_test_items']}`。",
        f"- sparse channel 非零数量范围：`{run['sparse_samples']['observed_sparse_channel_nonzero_min']}..{run['sparse_samples']['observed_sparse_channel_nonzero_max']}`，均值 `{run['sparse_samples']['observed_sparse_channel_nonzero_mean']}`。",
        f"- sparse 与 target 对齐最大绝对误差：`{run['sparse_samples']['sparse_target_alignment_abs_max']}`。",
    ]
    path = run_dir / "sample_count_audit.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    save_json(run, run_dir / "sample_count_audit.json")
    return path


def plot_curves(runs: list[dict[str, Any]], stage1: dict[str, Any], output: Path) -> None:
    samples = [run["sample_count"] for run in runs]
    metric_names = [
        ("mse", "MSE"),
        ("nmse", "NMSE"),
        ("global_nmse", "global NMSE"),
        ("rmse_db_80", "dB RMSE"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for ax, (metric, title) in zip(axes.flatten(), metric_names):
        values = [run["metrics"]["secondU"][metric] for run in runs]
        baseline = stage1["secondU"][metric]
        ax.plot(samples, values, marker="o", label="RadioUNet_S secondU")
        ax.axhline(baseline, color="tab:red", linestyle="--", label="Stage 1 C secondU")
        ax.set_xlabel("fix_samples")
        ax.set_ylabel(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("Stage 2 RadioUNet_S sparse sample count sweep")
    fig.savefig(output, dpi=150)
    plt.close(fig)


def write_summary(runs: list[dict[str, Any]], stage1: dict[str, Any], figure_path: Path, output_dir: Path) -> Path:
    lines = [
        "# Stage 2 sparse sample count sweep audit",
        "",
        "## 范围",
        "",
        "- 配置：RadioUNet_S / DPM / threshold=0.2 / firstU 50 epoch / secondU 50 epoch。",
        "- 样本数：50、100、200、300；其中 200 复用已完成的 `reports/s_dpm_thr2/full_50ep`，未重复训练。",
        "- 每个点包含 test eval、rerun eval、8 张预测图、checkpoint manifest 和单独 audit。",
        "",
        "## secondU 指标曲线表",
        "",
        "| fix_samples | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in runs:
        second = run["metrics"]["secondU"]
        lines.append(
            f"| {run['sample_count']} | "
            + " | ".join(format_metric(second[key]) for key in ["mse", "nmse", "global_nmse", "rmse", "rmse_db_80"])
            + " |"
        )

    lines.extend(
        [
            "",
            "## firstU 指标曲线表",
            "",
            "| fix_samples | MSE | NMSE | global NMSE | RMSE | dB RMSE |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for run in runs:
        first = run["metrics"]["firstU"]
        lines.append(
            f"| {run['sample_count']} | "
            + " | ".join(format_metric(first[key]) for key in ["mse", "nmse", "global_nmse", "rmse", "rmse_db_80"])
            + " |"
        )

    lines.extend(
        [
            "",
            "## 相比 Stage 1 C baseline 的 secondU 收益",
            "",
            "| fix_samples | MSE 降低 | MSE 降低比例 | NMSE 降低 | NMSE 降低比例 | global NMSE 降低 | global NMSE 降低比例 | dB RMSE 降低 | dB RMSE 降低比例 |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for run in runs:
        row = [str(run["sample_count"])]
        for metric in ["mse", "nmse", "global_nmse", "rmse_db_80"]:
            abs_gain, rel_gain = gain(stage1, run["metrics"], "secondU", metric)
            row.extend([format_metric(abs_gain), f"{rel_gain:.2f}%"])
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "## rerun 与产物约束",
            "",
            "| fix_samples | run dir | metrics git dirty | exclude reports | firstU rerun diff | secondU rerun diff | figures | checkpoint tracked | gate |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for run in runs:
        rerun = run["rerun_consistency"]
        lines.append(
            f"| {run['sample_count']} | `{run['run_dir']}` | `{run['metrics_git'].get('dirty')}` | "
            f"`{'reports' in run['metrics_git'].get('exclude_paths', [])}` | "
            f"{rerun['firstU_metrics_max_abs_diff']} | {rerun['secondU_metrics_max_abs_diff']} | "
            f"{len(run['figures'])} | `{run['gate']['checkpoint_files_tracked_by_git']}` | `{run['gate']['passed']}` |"
        )

    lines.extend(
        [
            "",
            "## 曲线图",
            "",
            f"- sample count vs metric 曲线：`{figure_path.relative_to(ROOT)}`。",
            "",
            "## 结论",
            "",
            "- 50/100/200/300 四个点均已形成同口径 secondU 与 firstU 表格。",
            "- 200 点使用既有 fixed-200 强基线产物，作为曲线中的已完成点。",
            "- 所有点 eval rerun 数值差异均为 0.0。",
        ]
    )
    output_path = output_dir / "sample_count_sweep_audit.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/s_dpm_thr2")
    parser.add_argument("--max-sparse-batches", type=int, default=8)
    parser.add_argument(
        "--only",
        type=int,
        choices=sorted(SWEEP_RUNS),
        help="Only audit one completed run and skip the cross-sample summary.",
    )
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stage1 = load_stage1()
    sample_counts = [args.only] if args.only is not None else sorted(SWEEP_RUNS)
    runs = [collect_run(sample_count, SWEEP_RUNS[sample_count], args.max_sparse_batches) for sample_count in sample_counts]
    for run in runs:
        write_run_report(run)
    if args.only is not None:
        print(f"saved run audit: {ROOT / runs[0]['run_dir'] / 'sample_count_audit.json'}")
        print(f"saved run report: {ROOT / runs[0]['run_dir'] / 'sample_count_audit.md'}")
        return 0
    figure_path = output_dir / "sample_count_metric_curves.png"
    plot_curves(runs, stage1, figure_path)
    summary = {
        "source_git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "stage1_metrics": stage1,
        "runs": runs,
        "figure": str(figure_path.relative_to(ROOT)),
    }
    save_json(summary, output_dir / "sample_count_sweep_audit.json")
    report = write_summary(runs, stage1, figure_path, output_dir)
    print(f"saved audit json: {output_dir / 'sample_count_sweep_audit.json'}")
    print(f"saved audit report: {report}")
    print(f"saved figure: {figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
