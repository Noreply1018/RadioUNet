#!/usr/bin/env python3
"""Run WNet size/threshold/split matrix experiments with no-repeat manifests."""

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

from radiounet.factory import build_model
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
            out.update(flatten_numbers(child, f"{prefix}.{key}" if prefix else str(key)))
        return out
    return {}


def max_abs_diff(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_nums = flatten_numbers(left)
    right_nums = flatten_numbers(right)
    return max(
        (
            abs(left_nums[key] - right_nums[key])
            for key in set(left_nums) & set(right_nums)
            if key != "seconds" and not key.endswith(".seconds")
        ),
        default=0.0,
    )


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def completed_manifest(run_dir: Path) -> bool:
    manifest_path = run_dir / "wnet_matrix_manifest.json"
    if not manifest_path.exists():
        return False
    return load_json(manifest_path).get("gate", {}).get("pass") is True


def history_summary(run_dir: Path) -> dict[str, Any]:
    out = {}
    for phase in ["firstU", "secondU"]:
        path = run_dir / f"{phase}_history.json"
        if path.exists():
            history = load_json(path).get("history", [])
            out[phase] = {
                "train_entries": sum(1 for row in history if row.get("split") == "train"),
                "val_entries": sum(1 for row in history if row.get("split") == "val"),
            }
    return out


def manifest(run_dir: Path, config_path: Path, smoke: bool, figures: int) -> None:
    cfg = load_yaml(config_path)
    model = build_model(cfg, phase="firstU")
    params = sum(param.numel() for param in model.parameters())
    first = load_json(run_dir / "firstU_test_metrics.json")
    first_rerun = load_json(run_dir / "firstU_test_metrics_rerun.json")
    second = load_json(run_dir / "secondU_test_metrics.json")
    second_rerun = load_json(run_dir / "secondU_test_metrics_rerun.json")
    figure_files = sorted((run_dir / "figures").glob("*.png"))
    history = history_summary(run_dir)
    gate = {
        "firstU_rerun_exact": max_abs_diff(first, first_rerun) == 0.0,
        "secondU_rerun_exact": max_abs_diff(second, second_rerun) == 0.0,
        "figures_count": len(figure_files) == figures,
        "figures_nonempty": all(path.stat().st_size > 0 for path in figure_files),
        "history_present": all(phase in history for phase in ["firstU", "secondU"]),
        "epochs_50_or_smoke": smoke
        or all(history[phase]["train_entries"] == 50 and history[phase]["val_entries"] == 50 for phase in ["firstU", "secondU"]),
    }
    gate["pass"] = all(gate.values())
    out = {
        "config": str(config_path.relative_to(ROOT)),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "smoke": smoke,
        "width_scale": cfg.get("model", {}).get("width_scale", 1.0),
        "threshold": cfg.get("data", {}).get("threshold"),
        "split_policy": cfg.get("data", {}).get("split_policy", "legacy"),
        "parameters": params,
        "checkpoint_sha256": {
            phase: file_sha256(run_dir / "checkpoints" / f"{phase}.pt")
            for phase in ["firstU", "secondU"]
            if (run_dir / "checkpoints" / f"{phase}.pt").exists()
        },
        "history": history,
        "metrics": {
            "firstU": str((run_dir / "firstU_test_metrics.json").relative_to(ROOT)),
            "secondU": str((run_dir / "secondU_test_metrics.json").relative_to(ROOT)),
        },
        "figures": [str(path.relative_to(ROOT)) for path in figure_files],
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "gate": gate,
    }
    save_json(out, run_dir / "wnet_matrix_manifest.json")
    lines = [
        "# WNet matrix manifest",
        "",
        f"- config：`{out['config']}`",
        f"- run_dir：`{out['run_dir']}`",
        f"- smoke：`{out['smoke']}`",
        f"- width_scale：`{out['width_scale']}`",
        f"- threshold：`{out['threshold']}`",
        f"- split_policy：`{out['split_policy']}`",
        f"- parameters：`{out['parameters']}`",
        f"- gate：`{gate['pass']}`",
    ]
    (run_dir / "wnet_matrix_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--figures", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config_path = ROOT / args.config
    run_dir = ROOT / args.run_dir
    if completed_manifest(run_dir) and not args.force:
        print(f"skip completed run: {run_dir.relative_to(ROOT)}")
        return 0
    if run_dir.exists() and any(run_dir.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to overwrite non-empty incomplete run dir: {run_dir.relative_to(ROOT)}. Use --force to rerun intentionally.")
    run_dir.mkdir(parents=True, exist_ok=True)

    train_cmd = [
        sys.executable,
        "scripts/train.py",
        "--config",
        str(config_path.relative_to(ROOT)),
        "--phase",
        "both",
        "--device",
        args.device,
        "--run-dir",
        str(run_dir.relative_to(ROOT)),
    ]
    if args.smoke:
        train_cmd.append("--smoke")
    run(train_cmd)
    for phase in ["firstU", "secondU"]:
        checkpoint = run_dir / "checkpoints" / f"{phase}.pt"
        for rerun in [False, True]:
            output = run_dir / f"{phase}_test_metrics{'_rerun' if rerun else ''}.json"
            eval_cmd = [
                sys.executable,
                "scripts/evaluate.py",
                "--config",
                str(config_path.relative_to(ROOT)),
                "--checkpoint",
                str(checkpoint.relative_to(ROOT)),
                "--split",
                "test",
                "--device",
                args.device,
                "--output",
                str(output.relative_to(ROOT)),
            ]
            if args.smoke:
                eval_cmd.append("--smoke")
            run(eval_cmd)
    figure_cmd = [
        sys.executable,
        "scripts/make_figures.py",
        "--config",
        str(config_path.relative_to(ROOT)),
        "--checkpoint",
        str((run_dir / "checkpoints/secondU.pt").relative_to(ROOT)),
        "--split",
        "test",
        "--device",
        args.device,
        "--limit",
        str(args.figures),
        "--output-dir",
        str((run_dir / "figures").relative_to(ROOT)),
    ]
    if args.smoke:
        figure_cmd.append("--smoke")
    run(figure_cmd)
    manifest(run_dir, config_path, smoke=args.smoke, figures=args.figures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
