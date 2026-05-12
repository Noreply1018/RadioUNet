#!/usr/bin/env python3
"""Audit missing-buildings full-matrix readiness without launching training."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import git_metadata, save_json

OUT_DIR = ROOT / "reports/full_matrix"
COUNTS = [0, 1, 2, 4]
SOURCES = ["dpm", "irt2", "rand"]
MODELS = ["c", "s"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def max_abs_diff(left: dict[str, Any], right: dict[str, Any]) -> float:
    def flatten(value: Any, prefix: str = "") -> dict[str, float]:
        if isinstance(value, bool):
            return {}
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return {prefix: float(value)}
        if isinstance(value, dict):
            out: dict[str, float] = {}
            for key, child in value.items():
                out.update(flatten(child, f"{prefix}.{key}" if prefix else str(key)))
            return out
        return {}

    left_nums = flatten(left)
    right_nums = flatten(right)
    diffs = [
        abs(left_nums[key] - right_nums[key])
        for key in set(left_nums) & set(right_nums)
        if key != "seconds" and not key.endswith(".seconds")
    ]
    return max(diffs) if diffs else 0.0


def metric_gate(metrics_path: Path, rerun_path: Path, manifest_path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "metrics": str(metrics_path.relative_to(ROOT)),
        "rerun": str(rerun_path.relative_to(ROOT)),
        "manifest": str(manifest_path.relative_to(ROOT)),
        "metrics_exists": metrics_path.exists(),
        "rerun_exists": rerun_path.exists(),
        "manifest_exists": manifest_path.exists(),
    }
    if metrics_path.exists() and rerun_path.exists():
        metrics = load_json(metrics_path)
        rerun = load_json(rerun_path)
        second = metrics.get("secondU", metrics.get(metrics.get("checkpoint_phase", "secondU"), {}))
        row.update(
            {
                "samples": metrics.get("samples"),
                "mse": second.get("mse"),
                "global_nmse": second.get("global_nmse"),
                "metrics_git_dirty": metrics.get("git", {}).get("dirty"),
                "rerun_max_abs_diff": max_abs_diff(metrics, rerun),
            }
        )
    row["gate"] = all(
        [
            row["metrics_exists"],
            row["rerun_exists"],
            row["manifest_exists"],
            row.get("metrics_git_dirty") is False,
            row.get("rerun_max_abs_diff") == 0.0,
        ]
    )
    return row


def official_rows() -> list[dict[str, Any]]:
    rows = []
    base = ROOT / "reports/missing_buildings"
    for model in MODELS:
        for count in COUNTS:
            rows.append(
                {
                    "policy": "official_loader",
                    "source": "dpm",
                    "model": model,
                    "transfer": "zeroshot",
                    "missing": count,
                    **metric_gate(
                        base / f"zeroshot_{model}_missing{count}/zeroshot_test_metrics.json",
                        base / f"zeroshot_{model}_missing{count}/zeroshot_test_metrics_rerun.json",
                        base / f"zeroshot_{model}_missing{count}/stage4_zeroshot_manifest.json",
                    ),
                }
            )
        for count in [1, 2, 4]:
            stem = f"s_irt4_missing{count}_pool600_sparse_loss_50ep" if model == "s" else f"c_irt4_missing{count}_sparse_loss_50ep"
            rows.append(
                {
                    "policy": "official_loader",
                    "source": "dpm",
                    "model": model,
                    "transfer": "adapt",
                    "missing": count,
                    **metric_gate(
                        base / f"{stem}/secondU_test_metrics.json",
                        base / f"{stem}/secondU_test_metrics_rerun.json",
                        base / f"{stem}/stage4_run_manifest.json",
                    ),
                }
            )
    return rows


def fixed_receiver_rows() -> list[dict[str, Any]]:
    rows = []
    for source in SOURCES:
        for model in MODELS:
            for count in COUNTS:
                config = ROOT / f"configs/{model}_{source}_irt4_missing{count}_fixedrx_adapt.yaml"
                run_dir = ROOT / "reports/full_matrix" / f"{model}_{source}_irt4_missing{count}_fixedrx_adapt_50ep"
                smoke_dir = ROOT / "reports/full_matrix" / f"{model}_{source}_irt4_missing{count}_fixedrx_adapt_smoke"
                smoke_manifest = smoke_dir / "stage4_run_manifest.json"
                smoke_gate = False
                if smoke_manifest.exists():
                    smoke_gate = load_json(smoke_manifest).get("gate", {}).get("pass") is True
                rows.append(
                    {
                        "policy": "fixed_receiver",
                        "source": source,
                        "model": model,
                        "transfer": "adapt",
                        "missing": count,
                        "config": str(config.relative_to(ROOT)),
                        "config_exists": config.exists(),
                        "run_dir": str(run_dir.relative_to(ROOT)),
                        "run_exists": run_dir.exists(),
                        "smoke_dir": str(smoke_dir.relative_to(ROOT)),
                        "smoke_manifest_exists": smoke_manifest.exists(),
                        "smoke_gate": smoke_gate,
                        "gate": False,
                        "blocking_gap": "missing config" if not config.exists() else "missing fixed receiver full run",
                    }
                )
    return rows


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# Missing Buildings Full Matrix 审计",
        "",
        f"- gate：`{audit['gate']['pass']}`。",
        f"- official-loader DPM run gate：`{audit['gate']['official_loader_dpm_complete']}`。",
        f"- fixed receiver policy hash gate：`{audit['gate']['fixed_receiver_policy_pass']}`。",
        f"- fixed receiver configs complete：`{audit['gate']['fixed_receiver_configs_complete']}`。",
        f"- fixed receiver full runs complete：`{audit['gate']['fixed_receiver_full_runs_complete']}`。",
        f"- fixed receiver smoke cells passed：`{audit['gate']['fixed_receiver_smoke_cells_passed']}`。",
        "",
        "## Official-loader 已有 run",
        "| policy | source | model | transfer | missing | samples | mse | rerun diff | gate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in audit["official_loader_rows"]:
        lines.append(
            f"| {row['policy']} | {row['source']} | {row['model']} | {row['transfer']} | {row['missing']} | "
            f"{row.get('samples', '')} | {row.get('mse', float('nan')):.10f} | "
            f"{row.get('rerun_max_abs_diff', float('nan')):.1f} | `{row['gate']}` |"
        )
    lines.extend(
        [
            "",
            "## Fixed receiver matrix 缺口",
            "| source | model | missing | config | smoke gate | run exists | gap |",
            "| --- | --- | ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in audit["fixed_receiver_rows"]:
        if not row["gate"]:
            lines.append(
                f"| {row['source']} | {row['model']} | {row['missing']} | `{row['config_exists']}` | "
                f"`{row['smoke_gate']}` | `{row['run_exists']}` | {row['blocking_gap']} |"
            )
    (OUT_DIR / "missing_buildings_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    fixed_policy_path = OUT_DIR / "fixed_receiver_policy_audit.json"
    fixed_policy = load_json(fixed_policy_path) if fixed_policy_path.exists() else {"gate": {"pass": False}}
    official = official_rows()
    fixed = fixed_receiver_rows()
    gate = {
        "official_loader_dpm_complete": all(row["gate"] for row in official),
        "fixed_receiver_policy_pass": fixed_policy.get("gate", {}).get("pass") is True,
        "fixed_receiver_configs_complete": all(row["config_exists"] for row in fixed),
        "fixed_receiver_smoke_cells_passed": any(row["smoke_gate"] for row in fixed),
        "fixed_receiver_full_runs_complete": all(row["run_exists"] for row in fixed),
    }
    gate["pass"] = all(gate.values())
    blocking = []
    if not gate["official_loader_dpm_complete"]:
        blocking.append("official-loader DPM rows are archived evidence but do not all satisfy clean full-matrix gate")
    if not gate["fixed_receiver_full_runs_complete"]:
        blocking.append("缺全部 fixed receiver full runs/metrics/rerun/manifest")
    if not gate["fixed_receiver_configs_complete"]:
        blocking.append("缺 fixed receiver configs")
    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "fixed_receiver_policy_audit": str(fixed_policy_path.relative_to(ROOT)),
        "official_loader_rows": official,
        "fixed_receiver_rows": fixed,
        "gate": gate,
        "blocking_gap": "；".join(blocking) if blocking else "无。",
    }
    save_json(audit, OUT_DIR / "missing_buildings_matrix.json")
    write_markdown(audit)
    print(f"missing buildings matrix gate: {gate['pass']}")
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
