#!/usr/bin/env python3
"""Run a Stage 4 missing-buildings zero-shot evaluation with required artifacts."""

from __future__ import annotations

import argparse
import json
import math
import shutil
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


def write_markdown(manifest: dict[str, Any], output: Path) -> None:
    lines = [
        "# Stage 4 missing-buildings zero-shot manifest",
        "",
        f"- 配置：`{manifest['config_path']}`",
        f"- run dir：`{manifest['run_dir']}`",
        f"- missing_buildings：`{manifest['missing_buildings']}`",
        f"- result bucket：`{manifest['result_bucket']}`",
        f"- source checkpoint：`{manifest['source_checkpoint']['path']}`",
        f"- source checkpoint sha256：`{manifest['source_checkpoint']['sha256']}`",
        f"- split 样本数：`{manifest['split_counts']}`",
        f"- rerun 最大差异：`{manifest['rerun_max_abs_diff']}`",
        f"- 图像数量：`{manifest['figures']['count']}`，非空：`{manifest['figures']['all_nonempty']}`",
        "",
        "## Gate",
    ]
    for key, value in manifest["gate"].items():
        lines.append(f"- `{key}={value}`")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--figures", type=int, default=8)
    args = parser.parse_args()

    config_path = Path(args.config)
    checkpoint = Path(args.checkpoint)
    config = load_yaml(config_path)
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = run_dir / "logs"
    figures_dir = run_dir / "figures"
    missing_audit_dir = run_dir / "stage4_missing_loader_audit"
    metrics = run_dir / "zeroshot_test_metrics.json"
    metrics_rerun = run_dir / "zeroshot_test_metrics_rerun.json"
    shutil.copy2(config_path, run_dir / config_path.name)

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
    run_command(eval_base + ["--output", str(metrics)], logs_dir / "zeroshot_eval.log")
    run_command(eval_base + ["--output", str(metrics_rerun)], logs_dir / "zeroshot_eval_rerun.log")
    run_command(
        [
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
        ],
        logs_dir / "make_figures.log",
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

    metrics_data = load_json(metrics)
    metrics_rerun_data = load_json(metrics_rerun)
    data_cfg = config["data"]
    manifest = {
        "config_path": str(config_path),
        "run_dir": str(run_dir),
        "missing_buildings": int(data_cfg.get("missing_buildings", data_cfg.get("missing", 0))),
        "result_bucket": "zero-shot missing-building degradation",
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "split_counts": split_counts(config),
        "config_snapshot": str(run_dir / config_path.name),
        "source_checkpoint": {"path": str(checkpoint), "sha256": file_sha256(checkpoint)},
        "metrics": str(metrics),
        "metrics_rerun": str(metrics_rerun),
        "rerun_max_abs_diff": max_abs_diff(metrics_data, metrics_rerun_data),
        "figures": figure_audit(figures_dir),
        "missing_loader_audit_dir": str(missing_audit_dir),
    }
    gate = {
        "source_checkpoint_exists": checkpoint.exists(),
        "rerun_diff_zero": manifest["rerun_max_abs_diff"] == 0.0,
        "figures_requested": manifest["figures"]["count"] == args.figures,
        "figures_nonempty": manifest["figures"]["all_nonempty"],
        "test_samples_198": metrics_data.get("samples") == 198,
        "sparse_metrics_recorded": "sparse_points" in metrics_data.get("secondU", {}),
    }
    gate["pass"] = all(gate.values())
    manifest["gate"] = gate
    save_json(manifest, run_dir / "stage4_zeroshot_manifest.json")
    write_markdown(manifest, run_dir / "stage4_zeroshot_manifest.md")
    print(manifest["gate"])
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
