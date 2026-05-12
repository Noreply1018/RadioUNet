#!/usr/bin/env python3
"""Run cars-scenario full-matrix experiments."""

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
    "c_dpmcars_thr2": "configs/c_dpmcars_thr2.yaml",
    "c_irt2cars_thr2": "configs/c_irt2cars_thr2.yaml",
    "s_dpmcars_carinput_thr2_rand1_300": "configs/s_dpmcars_carinput_thr2_rand1_300.yaml",
    "s_irt2cars_carinput_thr2_rand1_300": "configs/s_irt2cars_carinput_thr2_rand1_300.yaml",
}


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def completed_manifest(run_dir: Path) -> bool:
    manifest_path = run_dir / "cars_run_manifest.json"
    if not manifest_path.exists():
        return False
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data.get("gate", {}).get("pass") is True


def manifest(run_dir: Path, config_path: Path, smoke: bool) -> None:
    cfg = load_yaml(config_path)
    figures = sorted((run_dir / "figures").glob("*.png"))
    history = {}
    for phase in ["firstU", "secondU"]:
        history_path = run_dir / f"{phase}_history.json"
        if history_path.exists():
            data = json.loads(history_path.read_text(encoding="utf-8"))
            rows = data.get("history", [])
            history[phase] = {
                "best_val_loss": data.get("best_val_loss"),
                "train_entries": sum(1 for row in rows if row.get("split") == "train"),
                "val_entries": sum(1 for row in rows if row.get("split") == "val"),
            }
    checkpoints = {}
    for phase in ["firstU", "secondU"]:
        ckpt = run_dir / "checkpoints" / f"{phase}.pt"
        if ckpt.exists():
            checkpoints[phase] = {"checkpoint": str(ckpt.relative_to(ROOT)), "sha256": file_sha256(ckpt)}
    gate = {
        "cars_simulation_yes": cfg["data"].get("cars_simulation") == "yes",
        "config_present": (run_dir / config_path.name).exists(),
        "firstU_metrics": (run_dir / "firstU_test_metrics.json").exists(),
        "secondU_metrics": (run_dir / "secondU_test_metrics.json").exists(),
        "firstU_rerun": (run_dir / "firstU_test_metrics_rerun.json").exists(),
        "secondU_rerun": (run_dir / "secondU_test_metrics_rerun.json").exists(),
        "history_present": all((run_dir / f"{phase}_history.json").exists() for phase in ["firstU", "secondU"]),
        "checkpoint_manifests_present": all(
            (run_dir / f"{phase}_checkpoint_manifest.json").exists() for phase in ["firstU", "secondU"]
        ),
        "figures_count": len(figures) > 0 if smoke else len(figures) == 8,
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
    save_json(out, run_dir / "cars_run_manifest.json")
    lines = [
        "# Cars run manifest",
        "",
        f"- run_dir：`{out['run_dir']}`",
        f"- config：`{out['config']}`",
        f"- cars_simulation：`{out['cars_simulation']}`",
        f"- cars_input：`{out['cars_input']}`",
        f"- gate：`{gate['pass']}`",
    ]
    (run_dir / "cars_run_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=sorted(RUNS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite/re-run an existing run directory.")
    args = parser.parse_args()
    names = sorted(RUNS) if args.all else [args.run]
    if not names or names == [None]:
        raise SystemExit("Provide --run or --all.")

    for name in names:
        config_path = ROOT / RUNS[name]
        suffix = "smoke" if args.smoke else "50ep"
        run_dir = ROOT / "reports/full_matrix" / f"{name}_{suffix}"
        if completed_manifest(run_dir) and not args.force:
            print(f"skip completed run: {run_dir.relative_to(ROOT)}", flush=True)
            continue
        if run_dir.exists() and any(run_dir.iterdir()) and not args.force:
            raise SystemExit(
                f"Refusing to overwrite non-empty incomplete run dir: {run_dir.relative_to(ROOT)}. "
                "Use --force to rerun intentionally."
            )
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
            "8",
            "--output-dir",
            str((run_dir / "figures").relative_to(ROOT)),
        ]
        if args.smoke:
            figure_cmd.append("--smoke")
        run(figure_cmd)
        manifest(run_dir, config_path, smoke=args.smoke)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
