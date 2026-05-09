#!/usr/bin/env python3
"""Generate the final Stage 3C IRT4 transfer audit."""

from __future__ import annotations

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

from radiounet.utils import git_metadata, save_json


OUT_DIR = ROOT / "reports/irt4_transfer"
RUNS = {
    "paper_faithful_mainline": {
        "label": "S sparse-loss pool600 mainline",
        "category": "paper-faithful",
        "run_dir": OUT_DIR / "s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep",
        "metrics": OUT_DIR / "s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics.json",
        "rerun": OUT_DIR / "s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics_rerun.json",
        "manifest": OUT_DIR / "s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/stage3c_run_manifest.json",
        "semantic_audit": OUT_DIR
        / "s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/stage3c_sparse_audit/s_irt4_adapt_rand1_300_pool600_sparse_loss_audit.json",
    },
    "dense_loss_pilot": {
        "label": "S dense-loss pool300 pilot",
        "category": "dense-loss pilot",
        "metrics": OUT_DIR / "baseline_reruns/s_irt4_dense_loss_pilot_pool300_metrics.json",
        "rerun": OUT_DIR / "baseline_reruns/s_irt4_dense_loss_pilot_pool300_metrics_rerun.json",
        "original_metrics": ROOT / "reports/irt4_adapt/rand1_300_50ep/secondU_test_metrics.json",
    },
    "pool300_sparse_ablation": {
        "label": "S sparse-loss pool300 ablation",
        "category": "ablation",
        "run_dir": OUT_DIR / "s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_50ep",
        "metrics": OUT_DIR / "s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_50ep/secondU_test_metrics.json",
        "rerun": OUT_DIR / "s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_50ep/secondU_test_metrics_rerun.json",
        "manifest": OUT_DIR / "s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_50ep/stage3c_run_manifest.json",
        "semantic_audit": OUT_DIR
        / "s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_50ep/stage3c_sparse_audit/s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_audit.json",
    },
    "c_sparse_baseline": {
        "label": "C sparse-loss pool300 baseline",
        "category": "C baseline",
        "run_dir": OUT_DIR / "c_irt4_adapt_sparse_loss_50ep",
        "metrics": OUT_DIR / "c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics.json",
        "rerun": OUT_DIR / "c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics_rerun.json",
        "manifest": OUT_DIR / "c_irt4_adapt_sparse_loss_50ep/stage3c_run_manifest.json",
        "semantic_audit": OUT_DIR / "c_irt4_adapt_sparse_loss_50ep/stage3c_sparse_audit/c_irt4_adapt_sparse_loss_audit.json",
    },
    "s_zero_shot": {
        "label": "S zero-shot",
        "category": "zero-shot baseline",
        "metrics": OUT_DIR / "baseline_reruns/s_irt4_zeroshot_rand1_300_metrics.json",
        "rerun": OUT_DIR / "baseline_reruns/s_irt4_zeroshot_rand1_300_metrics_rerun.json",
    },
    "c_zero_shot": {
        "label": "C zero-shot",
        "category": "zero-shot baseline",
        "metrics": OUT_DIR / "baseline_reruns/c_irt4_zeroshot_metrics.json",
        "rerun": OUT_DIR / "baseline_reruns/c_irt4_zeroshot_metrics_rerun.json",
    },
}


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


def git_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ROOT, text=True, capture_output=True)
    return result.returncode == 0


def collect_run(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    metrics = load_json(spec["metrics"])
    rerun = load_json(spec["rerun"])
    second = metrics["secondU"]
    sparse = second.get("sparse_points", {})
    out = {
        "name": name,
        "label": spec["label"],
        "category": spec["category"],
        "metrics_path": str(spec["metrics"].relative_to(ROOT)),
        "rerun_path": str(spec["rerun"].relative_to(ROOT)),
        "samples": metrics.get("samples"),
        "dense_mse": second["mse"],
        "dense_nmse": second["nmse"],
        "dense_global_nmse": second["global_nmse"],
        "sparse_mse": sparse.get("mse"),
        "sparse_global_nmse": sparse.get("global_nmse"),
        "sparse_points": sparse.get("points"),
        "sparse_points_per_sample": sparse.get("mean_points_per_sample"),
        "rerun_max_abs_diff": max_abs_diff(metrics, rerun),
        "metrics_git_dirty": metrics.get("git", {}).get("dirty"),
    }
    if "manifest" in spec:
        manifest = load_json(spec["manifest"])
        out["manifest_path"] = str(spec["manifest"].relative_to(ROOT))
        out["manifest_gate"] = manifest["gate"]
        out["checkpoint_tracked_by_git"] = git_tracked(ROOT / manifest["checkpoint"]["checkpoint"])
        out["figure_count"] = manifest["figures"]["count"]
        out["figures_nonempty"] = manifest["figures"]["all_nonempty"]
        out["history"] = manifest["history"]
    if "semantic_audit" in spec:
        semantic = load_json(spec["semantic_audit"])
        out["semantic_audit_path"] = str(spec["semantic_audit"].relative_to(ROOT))
        out["semantic_gate"] = semantic["gate"]
        out["semantic_data_samples"] = semantic.get("data_samples")
        out["semantic_input_low"] = semantic.get("num_samples_low")
        out["semantic_input_high"] = semantic.get("num_samples_high")
    if "original_metrics" in spec:
        out["original_metrics_path"] = str(spec["original_metrics"].relative_to(ROOT))
    return out


def write_markdown(audit: dict[str, Any]) -> None:
    runs = audit["runs"]
    lines = [
        "# Stage 3C IRT4 transfer 最终审计",
        "",
        "## 结论分区",
        "- paper-faithful 主线：`paper_faithful_mainline`，S / pool600 / 输入 1..300 / loss 在 pool600 sparse mask 上计算。",
        "- dense-loss pilot：`dense_loss_pilot`，保留为旧结果，不作为 paper-faithful 结论。",
        "- ablation：`pool300_sparse_ablation`，用于隔离 sparse-loss 语义修复与 600-pool 对齐。",
        "- C baseline：`c_sparse_baseline`。",
        "- zero-shot baselines：`s_zero_shot`、`c_zero_shot`。",
        "",
        "## IRT4 test 指标",
        "| run | 类别 | 样本数 | dense MSE | dense global NMSE | sparse MSE | sparse global NMSE | rerun diff |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in [
        "paper_faithful_mainline",
        "pool300_sparse_ablation",
        "dense_loss_pilot",
        "c_sparse_baseline",
        "s_zero_shot",
        "c_zero_shot",
    ]:
        run = runs[name]
        lines.append(
            f"| `{name}` | {run['category']} | {run['samples']} | {run['dense_mse']:.10f} | "
            f"{run['dense_global_nmse']:.10f} | {run['sparse_mse']:.10f} | "
            f"{run['sparse_global_nmse']:.10f} | {run['rerun_max_abs_diff']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## 论文语义对齐",
            f"- IRT4 only first two Tx：`{audit['paper_alignment']['irt4_first_two_tx']}`。",
            f"- RadioUNet_S random 1..300 input measurements：`{audit['paper_alignment']['s_random_1_to_300_input']}`。",
            f"- S 使用 600 sparse receivers，loss on all 600：`{audit['paper_alignment']['s_pool600_sparse_loss']}`。",
            f"- adaptation second UNet：`{audit['paper_alignment']['second_unet_adaptation']}`。",
            "",
            "## 判定",
            f"- 当前代码真正按 sparse IRT4 measurements 训练：`{audit['answers']['sparse_irt4_training']}`。",
            f"- S 600 pool / input 1..300 / sparse loss 成立：`{audit['answers']['s_pool600_input_sparse_loss']}`。",
            f"- 旧 dense-loss pilot 已降级：`{audit['answers']['dense_pilot_demoted']}`。",
            f"- paper-faithful Stage 3C 优于 S zero-shot：`{audit['answers']['paper_faithful_beats_s_zero_shot']}`。",
            f"- S paper-faithful 优于 C sparse baseline：`{audit['answers']['s_beats_c_sparse_baseline']}`。",
            f"- 可复跑/可审计/可逐项对齐：`{audit['answers']['reproducible_auditable']}`。",
            "",
            f"最终 gate：`{audit['gate']['pass']}`。",
        ]
    )
    (OUT_DIR / "stage3c_final_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    runs = {name: collect_run(name, spec) for name, spec in RUNS.items()}
    main = runs["paper_faithful_mainline"]
    s_zero = runs["s_zero_shot"]
    c_sparse = runs["c_sparse_baseline"]
    dense_pilot = runs["dense_loss_pilot"]
    paper_alignment = {
        "irt4_first_two_tx": all(run["samples"] == 198 for run in runs.values()),
        "s_random_1_to_300_input": main["semantic_input_low"] == 1 and main["semantic_input_high"] == 301,
        "s_pool600_sparse_loss": main["semantic_data_samples"] == 600
        and main["history"]["num_samples_for_loss"] == [600]
        and main["semantic_gate"]["pool_matches_loss_denominator"],
        "second_unet_adaptation": main["history"]["train_entries"] == 50 and main["history"]["val_entries"] == 50,
    }
    answers = {
        "sparse_irt4_training": all(
            runs[name].get("manifest_gate", {}).get("sparse_history_recorded")
            for name in ["paper_faithful_mainline", "pool300_sparse_ablation", "c_sparse_baseline"]
        ),
        "s_pool600_input_sparse_loss": all(paper_alignment[key] for key in ["s_random_1_to_300_input", "s_pool600_sparse_loss"]),
        "dense_pilot_demoted": dense_pilot["category"] == "dense-loss pilot",
        "paper_faithful_beats_s_zero_shot": main["dense_mse"] < s_zero["dense_mse"]
        and main["sparse_mse"] < s_zero["sparse_mse"],
        "s_beats_c_sparse_baseline": main["dense_mse"] < c_sparse["dense_mse"] and main["sparse_mse"] < c_sparse["sparse_mse"],
        "reproducible_auditable": all(run["rerun_max_abs_diff"] == 0.0 for run in runs.values())
        and all(run["metrics_git_dirty"] is False for run in runs.values())
        and all(
            runs[name].get("manifest_gate", {}).get("checkpoint_sha256_matches")
            and not runs[name].get("checkpoint_tracked_by_git")
            and runs[name].get("figure_count") == 8
            and runs[name].get("figures_nonempty")
            for name in ["paper_faithful_mainline", "pool300_sparse_ablation", "c_sparse_baseline"]
        ),
    }
    gate = {
        "runs_present": all(spec["metrics"].exists() and spec["rerun"].exists() for spec in RUNS.values()),
        "paper_alignment": all(paper_alignment.values()),
        "answers_true": all(answers.values()),
    }
    gate["pass"] = all(gate.values())
    audit = {
        "scope": "Stage 3C final IRT4 transfer audit",
        "git": git_metadata(exclude_paths=["reports"]),
        "runs": runs,
        "paper_alignment": paper_alignment,
        "answers": answers,
        "gate": gate,
    }
    save_json(audit, OUT_DIR / "stage3c_final_audit.json")
    write_markdown(audit)
    print(gate)
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
