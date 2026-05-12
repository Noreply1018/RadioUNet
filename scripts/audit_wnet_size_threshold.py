#!/usr/bin/env python3
"""Audit WNet size, threshold preprocessing, and split-matrix readiness."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataset, build_model
from radiounet.utils import git_metadata, load_yaml, save_json

OUT_DIR = ROOT / "reports/full_matrix"
SIZE_CONFIGS = {
    "small": "configs/c_dpm_thr2_size_small.yaml",
    "base": "configs/c_dpm_thr2_size_base.yaml",
    "large": "configs/c_dpm_thr2_size_large.yaml",
}
THRESHOLD_CONFIGS = {
    "0.0": "configs/c_dpm_thr0p0.yaml",
    "0.1": "configs/c_dpm_thr0p1.yaml",
    "0.2": "configs/c_dpm_thr0p2.yaml",
    "0.3": "configs/c_dpm_thr0p3.yaml",
    "0.4": "configs/c_dpm_thr0p4.yaml",
}
SPLIT_CONFIG = "configs/c_dpm_thr2_split400_100_200.yaml"
LEGACY_SPLIT = {"train": (0, 500), "val": (501, 600), "test": (601, 699)}
PAPER_SPLIT = {"train": (0, 399), "val": (400, 499), "test": (500, 699)}


def model_hash(model: torch.nn.Module) -> str:
    payload = {
        name: {
            "shape": list(param.shape),
            "requires_grad": param.requires_grad,
        }
        for name, param in model.named_parameters()
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def config_exists(path: str) -> bool:
    return (ROOT / path).exists()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def size_rows() -> list[dict[str, Any]]:
    rows = []
    for label, path in SIZE_CONFIGS.items():
        exists = config_exists(path)
        row: dict[str, Any] = {"label": label, "config": path, "config_exists": exists}
        if exists:
            cfg = load_yaml(ROOT / path)
            model = build_model(cfg, phase="firstU")
            dummy = torch.zeros(1, int(cfg["model"]["inputs"]), 256, 256)
            with torch.no_grad():
                outputs = model(dummy)
            row.update(
                {
                    "width_scale": float(cfg["model"].get("width_scale", 1.0)),
                    "parameters": sum(param.numel() for param in model.parameters()),
                    "trainable_parameters": sum(param.numel() for param in model.parameters() if param.requires_grad),
                    "architecture_hash": model_hash(model),
                    "input_shape": list(dummy.shape),
                    "output_shapes": [list(output.shape) for output in outputs],
                    "shape_gate": all(list(output.shape) == [1, 1, 256, 256] for output in outputs),
                }
            )
            smoke_dir = ROOT / "reports/full_matrix" / f"{Path(path).stem}_smoke"
            smoke_manifest = smoke_dir / "wnet_matrix_manifest.json"
            row["smoke_dir"] = str(smoke_dir.relative_to(ROOT))
            row["smoke_manifest_exists"] = smoke_manifest.exists()
            row["smoke_gate"] = load_json(smoke_manifest).get("gate", {}).get("pass") is True if smoke_manifest.exists() else False
        row["gate"] = bool(row.get("config_exists") and row.get("shape_gate") and row.get("parameters", 0) > 0)
        rows.append(row)
    return rows


def threshold_rows() -> list[dict[str, Any]]:
    rows = []
    tensors: dict[str, torch.Tensor] = {}
    for label, path in THRESHOLD_CONFIGS.items():
        exists = config_exists(path)
        row: dict[str, Any] = {"threshold": float(label), "config": path, "config_exists": exists}
        if exists:
            cfg = load_yaml(ROOT / path)
            ds = build_dataset(cfg, "test", smoke=True)
            _inputs, target = ds[0]
            tensors[label] = target
            row.update(
                {
                    "target_min": float(target.min().item()),
                    "target_max": float(target.max().item()),
                    "target_mean": float(target.float().mean().item()),
                    "target_shape": list(target.shape),
                }
            )
        row["gate"] = bool(row.get("config_exists") and row.get("target_shape") == [1, 256, 256])
        rows.append(row)
    for row in rows:
        label = f"{row['threshold']:.1f}"
        if label != "0.2" and label in tensors and "0.2" in tensors:
            row["diff_vs_thr0p2_max"] = float(torch.abs(tensors[label] - tensors["0.2"]).max().item())
            row["threshold_transform_differs"] = row["diff_vs_thr0p2_max"] > 0
            row["gate"] = row["gate"] and row["threshold_transform_differs"]
    return rows


def split_indices(policy: dict[str, tuple[int, int]]) -> dict[str, set[int]]:
    return {name: set(range(start, end + 1)) for name, (start, end) in policy.items()}


def split_audit() -> dict[str, Any]:
    exists = config_exists(SPLIT_CONFIG)
    legacy = split_indices(LEGACY_SPLIT)
    paper = split_indices(PAPER_SPLIT)
    overlap = {
        f"{left}_vs_{right}": len(legacy[left] & paper[right])
        for left in legacy
        for right in paper
    }
    row = {
        "config": SPLIT_CONFIG,
        "config_exists": exists,
        "legacy_map_counts": {key: len(value) for key, value in legacy.items()},
        "paper_map_counts": {key: len(value) for key, value in paper.items()},
        "overlap_counts": overlap,
        "test_overlap_legacy_vs_paper": sorted(legacy["test"] & paper["test"]),
    }
    row["gate"] = exists and row["paper_map_counts"] == {"train": 400, "val": 100, "test": 200}
    return row


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# WNet / model size / threshold 矩阵审计",
        "",
        f"- gate：`{audit['gate']['pass']}`。",
        "- 本审计覆盖 size 参数化、参数量、architecture hash、输入输出 shape、threshold preprocessing 与 split 文件级 overlap。",
        "- 50 epoch full runs 尚未全部完成，因此最终 plan gate 仍不能仅凭本 readiness 审计通过。",
        "",
        "## Model Size",
        "| label | width_scale | parameters | architecture hash | shape gate |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for row in audit["model_size"]:
        lines.append(
            f"| `{row['label']}` | {row.get('width_scale', '')} | {row.get('parameters', '')} | "
            f"`{row.get('architecture_hash', '')}` | `{row.get('shape_gate')}` |"
        )
    lines.extend(["", "## Smoke Evidence", "| label | smoke manifest | smoke gate |", "| --- | --- | ---: |"])
    for row in audit["model_size"]:
        lines.append(f"| `{row['label']}` | `{row.get('smoke_dir', '')}` | `{row.get('smoke_gate', False)}` |")
    lines.extend(["", "## Threshold", "| threshold | target mean | diff vs 0.2 max | gate |", "| ---: | ---: | ---: | ---: |"])
    for row in audit["thresholds"]:
        lines.append(
            f"| {row['threshold']} | {row.get('target_mean', float('nan')):.6f} | "
            f"{row.get('diff_vs_thr0p2_max', 0.0):.6f} | `{row['gate']}` |"
        )
    split = audit["split"]
    lines.extend(
        [
            "",
            "## Split",
            f"- config：`{split['config']}`",
            f"- legacy counts：`{split['legacy_map_counts']}`",
            f"- paper 400/100/200 counts：`{split['paper_map_counts']}`",
            f"- legacy test 与 paper test overlap map 数：`{len(split['test_overlap_legacy_vs_paper'])}`",
        ]
    )
    (OUT_DIR / "wnet_size_threshold_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    sizes = size_rows()
    thresholds = threshold_rows()
    split = split_audit()
    gate = {
        "model_size_ready": all(row["gate"] for row in sizes),
        "threshold_ready": all(row["gate"] for row in thresholds),
        "split_ready": split["gate"],
        "smoke_cells_passed": any(row.get("smoke_gate") for row in sizes),
        "full_runs_complete": False,
    }
    gate["pass"] = all(gate.values())
    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        "model_size": sizes,
        "thresholds": thresholds,
        "split": split,
        "gate": gate,
        "blocking_gap": "缺各 size/threshold/split 配置的 50 epoch full runs、metrics/rerun 和 qualitative figures。",
    }
    save_json(audit, OUT_DIR / "wnet_size_threshold_audit.json")
    write_markdown(audit)
    print(f"wnet size/threshold gate: {audit['gate']['pass']}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
