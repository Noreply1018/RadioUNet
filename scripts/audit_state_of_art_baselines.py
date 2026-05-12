#!/usr/bin/env python3
"""Audit state-of-the-art comparison baseline artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import git_metadata, save_json

OUT_DIR = ROOT / "reports/full_matrix"
BASELINE_DIR = OUT_DIR / "state_of_art_comparison"
RESULT_PATH = BASELINE_DIR / "state_of_art_comparison.json"
FIGURE_PATH = BASELINE_DIR / "state_of_art_comparison.png"
REQUIRED_BASELINES = {"rbf", "tensor_completion", "tomography", "one_step_mlp"}
REQUIRED_SAMPLE_COUNTS = {10, 20, 50, 100, 200, 300}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect() -> dict[str, Any]:
    if not RESULT_PATH.exists():
        return {
            "exists": False,
            "gate": {"pass": False, "reason": f"missing {RESULT_PATH.relative_to(ROOT)}"},
        }
    result = load_json(RESULT_PATH)
    rows = result.get("runs", [])
    classical = [row for row in rows if row.get("baseline") in REQUIRED_BASELINES]
    baselines = {row.get("baseline") for row in classical}
    sample_counts = {int(row["sample_count"]) for row in classical if row.get("sample_count") is not None}
    missing_pairs = []
    for baseline in REQUIRED_BASELINES:
        for count in REQUIRED_SAMPLE_COUNTS:
            if not any(row.get("baseline") == baseline and row.get("sample_count") == count for row in classical):
                missing_pairs.append(f"{baseline}:{count}")
    fairness_fields = [
        "seconds",
        "samples",
        "sample_count",
        "input_information",
        "building_postprocessing",
        "per_map_optimized",
        "implementation",
    ]
    rows_with_all_fairness_fields = all(all(field in row for field in fairness_fields) for row in classical)
    metrics_present = all(row.get("mse") is not None and row.get("global_nmse") is not None for row in classical)
    radio_unet_refs = {row.get("sample_count") for row in rows if row.get("baseline") == "radiounet_s_secondU"}
    c_ref = any(row.get("baseline") == "radiounet_c_secondU" for row in rows)
    gate = {
        "result_exists": True,
        "figure_exists": FIGURE_PATH.exists() and FIGURE_PATH.stat().st_size > 0,
        "required_baselines_present": REQUIRED_BASELINES.issubset(baselines),
        "required_sample_counts_present": REQUIRED_SAMPLE_COUNTS.issubset(sample_counts),
        "all_baseline_sample_pairs_present": not missing_pairs,
        "fairness_fields_present": rows_with_all_fairness_fields,
        "metrics_present": metrics_present,
        "radio_unet_reference_present": {50, 100, 300}.issubset(radio_unet_refs),
        "c_baseline_present": c_ref,
        "pass": False,
    }
    gate["pass"] = all(value for key, value in gate.items() if key != "pass")
    return {
        "exists": True,
        "source": str(RESULT_PATH.relative_to(ROOT)),
        "figure": str(FIGURE_PATH.relative_to(ROOT)),
        "source_gate": result.get("gate", {}),
        "baselines": sorted(baselines),
        "sample_counts": sorted(sample_counts),
        "missing_pairs": missing_pairs,
        "radio_unet_reference_sample_counts": sorted(count for count in radio_unet_refs if count is not None),
        "rows": rows,
        "gate": gate,
    }


def write_markdown(audit: dict[str, Any]) -> None:
    def fmt(value: Any, digits: int = 10) -> str:
        if value is None:
            return ""
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    lines = [
        "# State-of-the-art baseline 审计",
        "",
        f"- gate：`{audit['gate']['pass']}`。",
        "- 口径：传统 baseline 为 implementation-faithful proxy；没有把 proxy 标成官方实现。",
        f"- 结果：`{audit.get('source')}`",
        f"- 图：`{audit.get('figure')}`",
        "",
        "| baseline | sample count | samples | MSE | global NMSE | seconds | building postprocess | per-map optimized | implementation |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in audit.get("rows", []):
        lines.append(
            f"| `{row.get('baseline')}` | {row.get('sample_count', '')} | {row.get('samples', '')} | "
            f"{fmt(row.get('mse'))} | {fmt(row.get('global_nmse'))} | "
            f"{fmt(row.get('seconds'), 4)} | `{row.get('building_postprocessing')}` | "
            f"`{row.get('per_map_optimized')}` | {row.get('implementation')} |"
        )
    lines.extend(["", "## 缺口"])
    if audit["gate"]["pass"]:
        lines.append("- 无。")
    else:
        if audit.get("missing_pairs"):
            lines.append(f"- 缺 baseline/sample_count 组合：`{', '.join(audit['missing_pairs'])}`。")
        for key, value in audit["gate"].items():
            if key != "pass" and not value:
                lines.append(f"- gate `{key}` 未通过。")
    (OUT_DIR / "state_of_art_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    audit = {
        "git": git_metadata(exclude_paths=["reports"]),
        "artifact_git": git_metadata(),
        **collect(),
    }
    save_json(audit, OUT_DIR / "state_of_art_comparison.json")
    write_markdown(audit)
    print(f"state-of-art baseline gate: {audit['gate']['pass']}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
