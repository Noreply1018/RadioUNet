#!/usr/bin/env python3
"""Audit full-matrix IRT4 zero-shot and sparse-adaptation artifacts."""

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

from radiounet.factory import build_dataset
from radiounet.utils import file_sha256, git_metadata, load_yaml, save_json

OUT_DIR = ROOT / "reports/full_matrix"
SOURCES = {
    "dpm": "DPM",
    "irt2": "IRT2",
    "rand": "random coarse simulation",
}
MODELS = ("c", "s")
SETTINGS = ("zeroshot", "adapt")


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


def config_path(model: str, source: str, setting: str) -> Path:
    return ROOT / "configs" / f"{model}_{source}_irt4_{setting}.yaml"


def run_dir(model: str, source: str, setting: str) -> Path:
    suffix = "zeroshot" if setting == "zeroshot" else "50ep"
    return OUT_DIR / f"{model}_{source}_irt4_{setting}_{suffix}"


def split_counts(config: dict[str, Any]) -> dict[str, int]:
    return {split: len(build_dataset(config, split)) for split in ["train", "val", "test"]}


def history_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    data = load_json(path)
    rows = data.get("history", [])
    return {
        "exists": True,
        "train_entries": sum(1 for row in rows if row.get("split") == "train"),
        "val_entries": sum(1 for row in rows if row.get("split") == "val"),
        "loss_modes": sorted({row.get("loss_mode") for row in rows}),
        "num_samples_for_loss": sorted({row.get("num_samples_for_loss") for row in rows}),
        "mask_points_min": min((row["mask_points_min"] for row in rows if "mask_points_min" in row), default=None),
        "mask_points_max": max((row["mask_points_max"] for row in rows if "mask_points_max" in row), default=None),
        "best_val_loss": data.get("best_val_loss"),
    }


def collect_zero(model: str, source: str) -> dict[str, Any]:
    cfg_path = config_path(model, source, "zeroshot")
    cfg = load_yaml(cfg_path)
    rd = run_dir(model, source, "zeroshot")
    row: dict[str, Any] = {
        "name": f"{model}_{source}_irt4_zeroshot",
        "setting": "zero-shot",
        "model": model.upper(),
        "source": SOURCES[source],
        "config": str(cfg_path.relative_to(ROOT)),
        "run_dir": str(rd.relative_to(ROOT)),
        "exists": rd.exists(),
        "num_tx": cfg["data"].get("num_tx"),
        "loader": cfg["data"].get("loader"),
        "source_checkpoint": cfg["evaluation"].get("source_checkpoint"),
        "source_training_target": cfg["evaluation"].get("source_training_target"),
    }
    checkpoint = ROOT / row["source_checkpoint"]
    row["source_checkpoint_exists"] = checkpoint.exists()
    row["source_checkpoint_sha256"] = file_sha256(checkpoint) if checkpoint.exists() else None
    row["split_counts"] = split_counts(cfg)
    if not rd.exists():
        row["gate"] = False
        return row
    metrics_path = rd / "zeroshot_test_metrics.json"
    rerun_path = rd / "zeroshot_test_metrics_rerun.json"
    row["metrics_exists"] = metrics_path.exists()
    row["rerun_exists"] = rerun_path.exists()
    if metrics_path.exists() and rerun_path.exists():
        metrics = load_json(metrics_path)
        rerun = load_json(rerun_path)
        phase = metrics.get("checkpoint_phase", "secondU")
        row["checkpoint_phase"] = phase
        row["metrics_git_dirty"] = metrics.get("git", {}).get("dirty")
        row["rerun_max_abs_diff"] = max_abs_diff(metrics, rerun)
        row["dense_mse"] = metrics[phase]["mse"]
        row["dense_nmse"] = metrics[phase]["nmse"]
        row["rmse_db_80"] = metrics[phase]["rmse_db_80"]
        row["sparse_points"] = metrics[phase].get("sparse_points")
        row["test_samples"] = metrics.get("samples")
    figures = sorted((rd / "figures").glob("*.png"))
    row["figure_count"] = len(figures)
    row["figures_nonempty"] = all(path.stat().st_size > 0 for path in figures)
    row["manifest_exists"] = (rd / "irt4_zeroshot_manifest.json").exists()
    row["gate"] = all(
        [
            row["num_tx"] == 2,
            row["source_checkpoint_exists"],
            row["split_counts"] == {"train": 1002, "val": 200, "test": 198},
            row.get("test_samples") == 198,
            row.get("metrics_git_dirty") is False,
            row.get("rerun_max_abs_diff") == 0.0,
            row.get("figure_count") == 8,
            row.get("figures_nonempty"),
            row.get("manifest_exists"),
        ]
    )
    return row


def collect_adapt(model: str, source: str) -> dict[str, Any]:
    cfg_path = config_path(model, source, "adapt")
    cfg = load_yaml(cfg_path)
    rd = run_dir(model, source, "adapt")
    expected_loss_points = 600 if model == "s" else 300
    row: dict[str, Any] = {
        "name": f"{model}_{source}_irt4_adapt",
        "setting": "sparse adaptation",
        "model": model.upper(),
        "source": SOURCES[source],
        "config": str(cfg_path.relative_to(ROOT)),
        "run_dir": str(rd.relative_to(ROOT)),
        "exists": rd.exists(),
        "num_tx": cfg["data"].get("num_tx"),
        "loader": cfg["data"].get("loader"),
        "source_checkpoint": cfg["evaluation"].get("source_checkpoint"),
        "init_checkpoint": cfg["training"].get("init_checkpoint"),
        "source_training_target": cfg["evaluation"].get("source_training_target"),
        "loss_mode": cfg["training"].get("loss_mode"),
        "num_samples_for_loss": cfg["training"].get("num_samples_for_loss"),
        "sample_policy": {
            "num_samples": cfg["data"].get("num_samples"),
            "data_samples": cfg["data"].get("data_samples"),
            "fix_samples": cfg["data"].get("fix_samples"),
            "num_samples_low": cfg["data"].get("num_samples_low"),
            "num_samples_high": cfg["data"].get("num_samples_high"),
        },
    }
    init_checkpoint = ROOT / row["init_checkpoint"]
    row["init_checkpoint_exists"] = init_checkpoint.exists()
    row["init_matches_source_checkpoint"] = row["init_checkpoint"] == row["source_checkpoint"]
    row["init_checkpoint_sha256"] = file_sha256(init_checkpoint) if init_checkpoint.exists() else None
    row["split_counts"] = split_counts(cfg)
    if not rd.exists():
        row["gate"] = False
        return row
    metrics_path = rd / "secondU_test_metrics.json"
    rerun_path = rd / "secondU_test_metrics_rerun.json"
    row["metrics_exists"] = metrics_path.exists()
    row["rerun_exists"] = rerun_path.exists()
    if metrics_path.exists() and rerun_path.exists():
        metrics = load_json(metrics_path)
        rerun = load_json(rerun_path)
        row["metrics_git_dirty"] = metrics.get("git", {}).get("dirty")
        row["rerun_max_abs_diff"] = max_abs_diff(metrics, rerun)
        row["dense_mse"] = metrics["secondU"]["mse"]
        row["dense_nmse"] = metrics["secondU"]["nmse"]
        row["rmse_db_80"] = metrics["secondU"]["rmse_db_80"]
        row["sparse_points"] = metrics["secondU"].get("sparse_points")
        row["test_samples"] = metrics.get("samples")
    row["history"] = history_summary(rd / "secondU_history.json")
    figures = sorted((rd / "figures").glob("*.png"))
    row["figure_count"] = len(figures)
    row["figures_nonempty"] = all(path.stat().st_size > 0 for path in figures)
    row["manifest_exists"] = (rd / "stage3c_run_manifest.json").exists()
    row["sparse_audit_exists"] = (rd / "stage3c_sparse_audit" / f"{cfg_path.stem}_audit.json").exists()
    row["gate"] = all(
        [
            row["num_tx"] == 2,
            row["init_checkpoint_exists"],
            row["init_matches_source_checkpoint"],
            row["split_counts"] == {"train": 1002, "val": 200, "test": 198},
            row["loss_mode"] == "sparse_mse",
            row["num_samples_for_loss"] == expected_loss_points,
            row.get("test_samples") == 198,
            row.get("metrics_git_dirty") is False,
            row.get("rerun_max_abs_diff") == 0.0,
            row["history"].get("train_entries") == 50,
            row["history"].get("val_entries") == 50,
            row["history"].get("loss_modes") == ["sparse_mse"],
            row.get("figure_count") == 8,
            row.get("figures_nonempty"),
            row.get("manifest_exists"),
            row.get("sparse_audit_exists"),
            row.get("sparse_points") is not None,
        ]
    )
    return row


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# IRT4 Transfer 全矩阵审计",
        "",
        f"- gate：`{audit['gate']['pass']}`。",
        "- 口径：source coarse target x RadioUNet_C/S x zero-shot/adaptation；IRT4 固定 Tx 0/1，即 `num_tx=2`。",
        "- adaptation：C 使用 300 sparse loss receivers；S 使用 600 receiver pool、输入随机 1..300、loss on full 600 sparse points。",
        "",
        "| run | setting | source | model | dense MSE | dense NMSE | RMSE dB | sparse MSE | figures | gate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in audit["runs"]:
        sparse = row.get("sparse_points") or {}
        lines.append(
            f"| `{row['name']}` | {row['setting']} | {row['source']} | {row['model']} | "
            f"{row.get('dense_mse', float('nan')):.10f} | {row.get('dense_nmse', float('nan')):.10f} | "
            f"{row.get('rmse_db_80', float('nan')):.6f} | {sparse.get('mse', float('nan')):.10f} | "
            f"{row.get('figure_count', 0)} | `{row['gate']}` |"
        )
    lines.extend(["", "## 缺口"])
    missing = [row for row in audit["runs"] if not row["gate"]]
    if not missing:
        lines.append("- 无。")
    for row in missing:
        setting = "zeroshot" if row["setting"] == "zero-shot" else "adapt"
        lines.append(f"- `{row['name']}` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run {row['name']} --device auto`。")
        if row["setting"] != ("zero-shot" if setting == "zeroshot" else "sparse adaptation"):
            pass
    (OUT_DIR / "irt4_transfer_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for source in SOURCES:
        for model in MODELS:
            rows.append(collect_zero(model, source))
            rows.append(collect_adapt(model, source))
    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "runs": rows,
        "gate": {"pass": all(row["gate"] for row in rows)},
    }
    save_json(audit, OUT_DIR / "irt4_transfer_matrix.json")
    write_markdown(audit)
    print(f"irt4 transfer gate: {audit['gate']['pass']}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
