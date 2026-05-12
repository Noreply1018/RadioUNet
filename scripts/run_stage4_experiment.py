#!/usr/bin/env python3
"""Run a Stage 4 missing-buildings adaptation experiment with required artifacts."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataset
from radiounet.utils import file_sha256, git_metadata, load_yaml, save_json


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def run_command(command: list[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write("$ " + " ".join(command) + "\n")
        handle.flush()
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}. See {log_path}")


def completed_manifest(run_dir: Path) -> bool:
    manifest_path = run_dir / "stage4_run_manifest.json"
    if not manifest_path.exists():
        return False
    data = load_json(manifest_path)
    return data.get("gate", {}).get("pass") is True


def split_counts(config: dict[str, Any]) -> dict[str, int]:
    return {split: len(build_dataset(config, split)) for split in ["train", "val", "test"]}


def figure_audit(figures_dir: Path) -> dict[str, Any]:
    figures = sorted(figures_dir.glob("*.png"))
    return {
        "count": len(figures),
        "files": [str(path) for path in figures],
        "all_nonempty": all(path.stat().st_size > 0 for path in figures),
        "sizes": {path.name: path.stat().st_size for path in figures},
    }


def history_summary(history_path: Path) -> dict[str, Any]:
    history = load_json(history_path)
    rows = history.get("history", [])
    mask_rows = [row for row in rows if "mask_points_mean" in row]
    return {
        "entries": len(rows),
        "train_entries": sum(1 for row in rows if row.get("split") == "train"),
        "val_entries": sum(1 for row in rows if row.get("split") == "val"),
        "best_val_loss": history.get("best_val_loss"),
        "loss_modes": sorted({row.get("loss_mode") for row in rows}),
        "num_samples_for_loss": sorted({row.get("num_samples_for_loss") for row in rows}),
        "mask_points_min": min((row["mask_points_min"] for row in mask_rows), default=None),
        "mask_points_max": max((row["mask_points_max"] for row in mask_rows), default=None),
        "mask_points_mean_min": min((row["mask_points_mean"] for row in mask_rows), default=None),
        "mask_points_mean_max": max((row["mask_points_mean"] for row in mask_rows), default=None),
    }


def write_markdown(manifest: dict[str, Any], output: Path) -> None:
    lines = [
        "# Stage 4 missing-buildings run manifest",
        "",
        f"- 配置：`{manifest['config_path']}`",
        f"- run dir：`{manifest['run_dir']}`",
        f"- missing_buildings：`{manifest['missing_buildings']}`",
        f"- result bucket：`{manifest['result_bucket']}`",
        f"- git commit：`{manifest['git']['commit']}`",
        f"- git dirty：`{manifest['git']['dirty']}`",
        f"- smoke：`{manifest['smoke']}`",
        f"- split 样本数：`{manifest['split_counts']}`",
        f"- rerun 最大差异：`{manifest['rerun_max_abs_diff']}`",
        f"- 图像数量：`{manifest['figures']['count']}`，非空：`{manifest['figures']['all_nonempty']}`",
        f"- checkpoint sha256：`{manifest['checkpoint']['sha256_actual']}`",
        "",
        "## History / mask",
        f"- history entries：`{manifest['history']['entries']}`",
        f"- loss modes：`{manifest['history']['loss_modes']}`",
        f"- num_samples_for_loss：`{manifest['history']['num_samples_for_loss']}`",
        f"- mask 点数范围：`{manifest['history']['mask_points_min']}..{manifest['history']['mask_points_max']}`",
        "",
        "## Gate",
    ]
    for key, value in manifest["gate"].items():
        lines.append(f"- `{key}={value}`")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--figures", type=int, default=8)
    parser.add_argument("--force", action="store_true", help="Overwrite/re-run an existing run directory.")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_yaml(config_path)
    run_dir = Path(args.run_dir)
    if completed_manifest(run_dir) and not args.force:
        print(f"skip completed run: {run_dir}")
        return 0
    if run_dir.exists() and any(run_dir.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to overwrite non-empty incomplete run dir: {run_dir}. Use --force to rerun intentionally.")
    run_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = run_dir / "logs"
    checkpoint = run_dir / "checkpoints" / "secondU.pt"
    metrics = run_dir / "secondU_test_metrics.json"
    metrics_rerun = run_dir / "secondU_test_metrics_rerun.json"
    figures_dir = run_dir / "figures"
    sparse_audit_dir = run_dir / "stage4_sparse_audit"
    missing_audit_dir = run_dir / "stage4_missing_loader_audit"

    init_checkpoint = config["training"]["init_checkpoint"]
    train_cmd = [
        sys.executable,
        "scripts/train.py",
        "--config",
        str(config_path),
        "--phase",
        "secondU",
        "--init-checkpoint",
        init_checkpoint,
        "--device",
        args.device,
        "--run-dir",
        str(run_dir),
    ]
    if args.epochs is not None:
        train_cmd.extend(["--epochs", str(args.epochs)])
    if args.smoke:
        train_cmd.append("--smoke")
    run_command(train_cmd, logs_dir / "secondU_train.log")

    eval_base = [
        sys.executable,
        "scripts/evaluate.py",
        "--config",
        str(config_path),
        "--checkpoint",
        str(checkpoint),
        "--split",
        "test",
        "--device",
        args.device,
    ]
    if args.smoke:
        eval_base.append("--smoke")
    run_command(eval_base + ["--output", str(metrics)], logs_dir / "secondU_eval.log")
    run_command(eval_base + ["--output", str(metrics_rerun)], logs_dir / "secondU_eval_rerun.log")

    figure_cmd = [
        sys.executable,
        "scripts/make_figures.py",
        "--config",
        str(config_path),
        "--checkpoint",
        str(checkpoint),
        "--split",
        "test",
        "--device",
        args.device,
        "--limit",
        str(args.figures),
        "--output-dir",
        str(figures_dir),
    ]
    if args.smoke:
        figure_cmd.append("--smoke")
    run_command(figure_cmd, logs_dir / "make_figures.log")

    run_command(
        [
            sys.executable,
            "scripts/audit_stage3c_sparse.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(sparse_audit_dir),
        ],
        logs_dir / "stage4_sparse_audit.log",
    )
    run_command(
        [
            sys.executable,
            "scripts/audit_missing_buildings_loader.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(missing_audit_dir),
        ],
        logs_dir / "stage4_missing_loader_audit.log",
    )

    checkpoint_manifest = load_json(run_dir / "secondU_checkpoint_manifest.json")
    metrics_data = load_json(metrics)
    metrics_rerun_data = load_json(metrics_rerun)
    data_cfg = config["data"]
    manifest = {
        "config_path": str(config_path),
        "run_dir": str(run_dir),
        "missing_buildings": int(data_cfg.get("missing_buildings", data_cfg.get("missing", 0))),
        "result_bucket": config.get("evaluation", {}).get("result_bucket"),
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "smoke": args.smoke,
        "split_counts": split_counts(config),
        "config_snapshot": str(run_dir / config_path.name),
        "run_metadata": str(run_dir / "run_metadata.json"),
        "checkpoint": {
            **checkpoint_manifest,
            "sha256_actual": file_sha256(checkpoint),
        },
        "history": history_summary(run_dir / "secondU_history.json"),
        "metrics": str(metrics),
        "metrics_rerun": str(metrics_rerun),
        "rerun_max_abs_diff": max_abs_diff(metrics_data, metrics_rerun_data),
        "figures": figure_audit(figures_dir),
        "sparse_audit_dir": str(sparse_audit_dir),
        "missing_loader_audit_dir": str(missing_audit_dir),
    }
    gate = {
        "checkpoint_sha256_matches": manifest["checkpoint"]["sha256"] == manifest["checkpoint"]["sha256_actual"],
        "rerun_diff_zero": manifest["rerun_max_abs_diff"] == 0.0,
        "figures_requested": manifest["figures"]["count"] == args.figures,
        "figures_nonempty": manifest["figures"]["all_nonempty"],
        "sparse_history_recorded": manifest["history"]["loss_modes"] == ["sparse_mse"],
        "mask_distribution_recorded": manifest["history"]["mask_points_min"] is not None,
        "test_samples_198": metrics_data.get("samples") == 198 or args.smoke,
        "sparse_metrics_recorded": "sparse_points" in metrics_data.get("secondU", {}),
    }
    gate["pass"] = all(gate.values())
    manifest["gate"] = gate
    save_json(manifest, run_dir / "stage4_run_manifest.json")
    write_markdown(manifest, run_dir / "stage4_run_manifest.md")
    print(manifest["gate"])
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
