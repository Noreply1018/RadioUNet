#!/usr/bin/env python3
"""Generate a no-repeat command plan for remaining full-matrix runs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports/full_matrix"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def path_exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> int:
    commands: list[dict] = []

    cars = load_json(OUT_DIR / "cars_audit.json")
    for row in cars.get("runs", []):
        if row.get("gate") is not True:
            commands.append(
                {
                    "group": "cars",
                    "name": row["name"],
                    "reason": "missing cars full-run gate",
                    "command": f"python scripts/run_full_matrix_cars.py --run {row['name']} --device auto",
                    "skip_guard": "run_full_matrix_cars.py skips completed manifest unless --force is supplied",
                }
            )

    missing = load_json(OUT_DIR / "missing_buildings_matrix.json")
    for row in missing.get("fixed_receiver_rows", []):
        if row.get("run_exists") is not True:
            config = row["config"]
            run_dir = row["run_dir"]
            commands.append(
                {
                    "group": "missing_fixed_receiver",
                    "name": f"{row['model']}_{row['source']}_missing{row['missing']}",
                    "reason": row["blocking_gap"],
                    "command": f"python scripts/run_stage4_experiment.py --config {config} --run-dir {run_dir} --device auto",
                    "skip_guard": "run_stage4_experiment.py skips completed manifest unless --force is supplied",
                }
            )

    wnet = load_json(OUT_DIR / "wnet_size_threshold_audit.json")
    for row in wnet.get("model_size", []):
        config = row["config"]
        run_dir = f"reports/full_matrix/{Path(config).stem}_50ep"
        if not path_exists(f"{run_dir}/secondU_test_metrics.json"):
            commands.append(
                {
                    "group": "wnet_size",
                    "name": row["label"],
                    "reason": "missing model-size full run metrics/rerun/figures",
                    "command": f"python scripts/run_wnet_matrix_experiment.py --config {config} --run-dir {run_dir} --device auto",
                    "skip_guard": "run_wnet_matrix_experiment.py skips completed manifest unless --force is supplied",
                }
            )
    for row in wnet.get("thresholds", []):
        config = row["config"]
        run_dir = f"reports/full_matrix/{Path(config).stem}_50ep"
        if not path_exists(f"{run_dir}/secondU_test_metrics.json"):
            commands.append(
                {
                    "group": "threshold",
                    "name": str(row["threshold"]),
                    "reason": "missing threshold full run metrics/rerun/figures",
                    "command": f"python scripts/run_wnet_matrix_experiment.py --config {config} --run-dir {run_dir} --device auto",
                    "skip_guard": "run_wnet_matrix_experiment.py skips completed manifest unless --force is supplied",
                }
            )
    split = wnet.get("split", {})
    config = split.get("config")
    if config:
        run_dir = f"reports/full_matrix/{Path(config).stem}_50ep"
        if not path_exists(f"{run_dir}/secondU_test_metrics.json"):
            commands.append(
                {
                    "group": "split",
                    "name": "400_100_200",
                    "reason": "missing split full run metrics/rerun/figures",
                    "command": f"python scripts/run_wnet_matrix_experiment.py --config {config} --run-dir {run_dir} --device auto",
                    "skip_guard": "run_wnet_matrix_experiment.py skips completed manifest unless --force is supplied",
                }
            )

    audit = {
        "command_count": len(commands),
        "commands": commands,
        "gate": {
            "pass": len(commands) == 0,
            "reason": "No remaining full-run commands are needed." if not commands else "Full-run gaps remain; commands are generated with no-repeat guards where available.",
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "remaining_full_run_commands.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Remaining Full-run Commands",
        "",
        f"- command count：`{len(commands)}`",
        f"- gate：`{audit['gate']['pass']}`",
        "",
        "| group | name | reason | command | skip guard |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in commands:
        lines.append(f"| {row['group']} | `{row['name']}` | {row['reason']} | `{row['command']}` | {row['skip_guard']} |")
    (OUT_DIR / "remaining_full_run_commands.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"remaining commands: {len(commands)}")
    return 0 if not commands else 2


if __name__ == "__main__":
    raise SystemExit(main())
