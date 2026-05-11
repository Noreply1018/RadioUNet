#!/usr/bin/env python3
"""Run full-matrix IRT4 zero-shot and sparse-adaptation experiments."""

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

SOURCES = {
    "dpm": "DPM",
    "irt2": "IRT2",
    "rand": "random coarse simulation",
}
MODELS = ("c", "s")
SETTINGS = ("zeroshot", "adapt")


def config_path(model: str, source: str, setting: str) -> Path:
    return ROOT / "configs" / f"{model}_{source}_irt4_{setting}.yaml"


def run_dir(model: str, source: str, setting: str, smoke: bool = False) -> Path:
    suffix = "smoke" if smoke else ("zeroshot" if setting == "zeroshot" else "50ep")
    return ROOT / "reports/full_matrix" / f"{model}_{source}_irt4_{setting}_{suffix}"


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


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
    diffs = [
        abs(left_nums[key] - right_nums[key])
        for key in set(left_nums) & set(right_nums)
        if key != "seconds" and not key.endswith(".seconds")
    ]
    return max(diffs) if diffs else 0.0


def split_counts(config: dict[str, Any]) -> dict[str, int]:
    return {split: len(build_dataset(config, split)) for split in ["train", "val", "test"]}


def write_zero_manifest(run_dir_path: Path, cfg_path: Path, checkpoint: Path, smoke: bool, figures_requested: int) -> None:
    metrics = load_json(run_dir_path / "zeroshot_test_metrics.json")
    rerun = load_json(run_dir_path / "zeroshot_test_metrics_rerun.json")
    figures = sorted((run_dir_path / "figures").glob("*.png"))
    cfg = load_yaml(cfg_path)
    manifest = {
        "config_path": str(cfg_path.relative_to(ROOT)),
        "run_dir": str(run_dir_path.relative_to(ROOT)),
        "setting": "zero-shot IRT4",
        "smoke": smoke,
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "split_counts": split_counts(cfg),
        "source_checkpoint": str(checkpoint.relative_to(ROOT)),
        "source_checkpoint_sha256": file_sha256(checkpoint),
        "source_training_target": cfg["evaluation"]["source_training_target"],
        "metrics": str((run_dir_path / "zeroshot_test_metrics.json").relative_to(ROOT)),
        "metrics_rerun": str((run_dir_path / "zeroshot_test_metrics_rerun.json").relative_to(ROOT)),
        "rerun_max_abs_diff": max_abs_diff(metrics, rerun),
        "figures": [str(path.relative_to(ROOT)) for path in figures],
        "figure_count": len(figures),
        "gate": {},
    }
    gate = {
        "config_num_tx_2": cfg["data"].get("num_tx") == 2,
        "checkpoint_exists": checkpoint.exists(),
        "test_samples_198_or_smoke": smoke or metrics.get("samples") == 198,
        "rerun_diff_zero": manifest["rerun_max_abs_diff"] == 0.0,
        "figures_requested": len(figures) == figures_requested,
        "figures_nonempty": all(path.stat().st_size > 0 for path in figures),
    }
    gate["pass"] = all(gate.values())
    manifest["gate"] = gate
    save_json(manifest, run_dir_path / "irt4_zeroshot_manifest.json")
    lines = [
        "# IRT4 zero-shot manifest",
        "",
        f"- config：`{manifest['config_path']}`",
        f"- run dir：`{manifest['run_dir']}`",
        f"- source checkpoint：`{manifest['source_checkpoint']}`",
        f"- rerun max abs diff：`{manifest['rerun_max_abs_diff']}`",
        f"- figure count：`{manifest['figure_count']}`",
        f"- gate：`{gate['pass']}`",
    ]
    (run_dir_path / "irt4_zeroshot_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_zero(model: str, source: str, device: str, smoke: bool, figures: int) -> None:
    cfg_path = config_path(model, source, "zeroshot")
    cfg = load_yaml(cfg_path)
    out_dir = run_dir(model, source, "zeroshot", smoke=smoke)
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = ROOT / cfg["evaluation"]["source_checkpoint"]
    for rerun in (False, True):
        output = out_dir / f"zeroshot_test_metrics{'_rerun' if rerun else ''}.json"
        cmd = [
            sys.executable,
            "scripts/evaluate.py",
            "--config",
            str(cfg_path.relative_to(ROOT)),
            "--checkpoint",
            str(checkpoint.relative_to(ROOT)),
            "--split",
            "test",
            "--device",
            device,
            "--output",
            str(output.relative_to(ROOT)),
        ]
        if smoke:
            cmd.append("--smoke")
        run(cmd)
    figure_cmd = [
        sys.executable,
        "scripts/make_figures.py",
        "--config",
        str(cfg_path.relative_to(ROOT)),
        "--checkpoint",
        str(checkpoint.relative_to(ROOT)),
        "--split",
        "test",
        "--device",
        device,
        "--limit",
        str(figures),
        "--output-dir",
        str((out_dir / "figures").relative_to(ROOT)),
    ]
    if smoke:
        figure_cmd.append("--smoke")
    run(figure_cmd)
    write_zero_manifest(out_dir, cfg_path, checkpoint, smoke=smoke, figures_requested=figures)


def run_adapt(model: str, source: str, device: str, smoke: bool, figures: int) -> None:
    cfg_path = config_path(model, source, "adapt")
    out_dir = run_dir(model, source, "adapt", smoke=smoke)
    cmd = [
        sys.executable,
        "scripts/run_stage3c_experiment.py",
        "--config",
        str(cfg_path.relative_to(ROOT)),
        "--run-dir",
        str(out_dir.relative_to(ROOT)),
        "--device",
        device,
        "--figures",
        str(figures),
    ]
    if smoke:
        cmd.append("--smoke")
    run(cmd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", help="Run name like c_dpm_irt4_zeroshot, or omit with --all.")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--figures", type=int, default=8)
    args = parser.parse_args()

    selected: list[tuple[str, str, str]] = []
    if args.all:
        selected = [(model, source, setting) for source in SOURCES for model in MODELS for setting in SETTINGS]
    elif args.run:
        parts = args.run.split("_")
        if len(parts) != 4 or parts[2] != "irt4" or parts[3] not in SETTINGS:
            raise SystemExit("--run must look like c_dpm_irt4_zeroshot or s_rand_irt4_adapt")
        model, source, _irt4, setting = parts
        if model not in MODELS or source not in SOURCES:
            raise SystemExit(f"Unsupported run: {args.run}")
        selected = [(model, source, setting)]
    else:
        raise SystemExit("Provide --run or --all.")

    for model, source, setting in selected:
        if setting == "zeroshot":
            run_zero(model, source, args.device, args.smoke, args.figures)
        else:
            run_adapt(model, source, args.device, args.smoke, args.figures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
