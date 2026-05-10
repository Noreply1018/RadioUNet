#!/usr/bin/env python3
"""Run coarse-simulation full-matrix experiments."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import file_sha256, git_metadata, load_yaml, save_json

RUNS = {
    "c_dpm_thr2": "configs/c_dpm_thr2.yaml",
    "s_dpm_thr2_rand1_300": "configs/s_dpm_thr2_rand1_300.yaml",
    "c_irt2_thr2": "configs/c_irt2_thr2.yaml",
    "s_irt2_thr2_rand1_300": "configs/s_irt2_thr2_rand1_300.yaml",
    "c_rand_thr2": "configs/c_rand_thr2.yaml",
    "s_rand_thr2_rand1_300": "configs/s_rand_thr2_rand1_300.yaml",
}


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def manifest(run_dir: Path, config_path: Path, smoke: bool) -> None:
    cfg = load_yaml(config_path)
    figures = sorted((run_dir / "figures").glob("*.png"))
    history = {}
    for phase in ["firstU", "secondU"]:
        history_path = run_dir / f"{phase}_history.json"
        if history_path.exists():
            data = json.loads(history_path.read_text(encoding="utf-8"))
            history[phase] = {
                "best_val_loss": data.get("best_val_loss"),
                "train_entries": sum(1 for row in data.get("history", []) if row.get("split") == "train"),
                "val_entries": sum(1 for row in data.get("history", []) if row.get("split") == "val"),
            }
    checkpoints = {}
    for phase in ["firstU", "secondU"]:
        ckpt = run_dir / "checkpoints" / f"{phase}.pt"
        if ckpt.exists():
            checkpoints[phase] = {"checkpoint": str(ckpt.relative_to(ROOT)), "sha256": file_sha256(ckpt)}
    gate = {
        "config_present": (run_dir / config_path.name).exists(),
        "firstU_metrics": (run_dir / "firstU_test_metrics.json").exists(),
        "secondU_metrics": (run_dir / "secondU_test_metrics.json").exists(),
        "firstU_rerun": (run_dir / "firstU_test_metrics_rerun.json").exists(),
        "secondU_rerun": (run_dir / "secondU_test_metrics_rerun.json").exists(),
        "history_present": all((run_dir / f"{phase}_history.json").exists() for phase in ["firstU", "secondU"]),
        "checkpoint_manifests_present": all(
            (run_dir / f"{phase}_checkpoint_manifest.json").exists() for phase in ["firstU", "secondU"]
        ),
        "figures_count_8": (len(figures) > 0 if smoke else len(figures) == 8),
        "figures_nonempty": all(path.stat().st_size > 0 for path in figures),
        "epochs_50_or_smoke": smoke or all(
            history.get(phase, {}).get("train_entries") == 50 and history.get(phase, {}).get("val_entries") == 50
            for phase in ["firstU", "secondU"]
        ),
    }
    gate["pass"] = all(gate.values())
    out = {
        "config": str(config_path.relative_to(ROOT)),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "smoke": smoke,
        "simulation": cfg["data"]["simulation"],
        "model": "S" if cfg["data"]["loader"] == "RadioUNet_s" else "C",
        "cars_simulation": cfg["data"].get("cars_simulation"),
        "cars_input": cfg["data"].get("cars_input"),
        "sample_policy": {
            "fix_samples": cfg["data"].get("fix_samples"),
            "num_samples_low": cfg["data"].get("num_samples_low"),
            "num_samples_high": cfg["data"].get("num_samples_high"),
        },
        "history": history,
        "checkpoints": checkpoints,
        "figures": [str(path.relative_to(ROOT)) for path in figures],
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "gate": gate,
    }
    save_json(out, run_dir / "coarse_run_manifest.json")
    lines = [
        "# Coarse simulation run manifest",
        "",
        f"- run_dir：`{out['run_dir']}`",
        f"- config：`{out['config']}`",
        f"- smoke：`{smoke}`",
        f"- gate：`{gate['pass']}`",
    ]
    (run_dir / "coarse_run_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=sorted(RUNS), required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run-dir")
    args = parser.parse_args()

    config_path = ROOT / RUNS[args.run]
    suffix = "smoke" if args.smoke else "50ep"
    run_dir = Path(args.run_dir) if args.run_dir else ROOT / "reports/full_matrix" / f"{args.run}_{suffix}"
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
    run(
        [
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
            "8",
            "--output-dir",
            str((run_dir / "figures").relative_to(ROOT)),
        ]
        + (["--smoke"] if args.smoke else [])
    )
    manifest(run_dir, config_path, smoke=args.smoke)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
