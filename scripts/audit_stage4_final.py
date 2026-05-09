#!/usr/bin/env python3
"""Generate the final Stage 4 missing-buildings audit."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import git_metadata, save_json

OUT_DIR = ROOT / "reports/missing_buildings"
COUNTS = [0, 1, 2, 4]


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


def metric_row(kind: str, model: str, count: int, metrics_path: Path, rerun_path: Path, manifest_path: Path) -> dict[str, Any]:
    metrics = load_json(metrics_path)
    rerun = load_json(rerun_path)
    second = metrics["secondU"]
    sparse = second.get("sparse_points", {})
    row = {
        "kind": kind,
        "model": model,
        "missing_buildings": count,
        "metrics_path": str(metrics_path.relative_to(ROOT)),
        "rerun_path": str(rerun_path.relative_to(ROOT)),
        "manifest_path": str(manifest_path.relative_to(ROOT)),
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
    manifest = load_json(manifest_path)
    row["manifest_gate"] = manifest.get("gate", {})
    if "checkpoint" in manifest:
        checkpoint = ROOT / manifest["checkpoint"]["checkpoint"]
        row["checkpoint_sha256"] = manifest["checkpoint"].get("sha256_actual", manifest["checkpoint"].get("sha256"))
        row["checkpoint_tracked_by_git"] = git_tracked(checkpoint)
        row["history"] = manifest.get("history", {})
    if "source_checkpoint" in manifest:
        row["source_checkpoint_sha256"] = manifest["source_checkpoint"]["sha256"]
    return row


def collect_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for count in COUNTS:
        rows.append(
            metric_row(
                "zero-shot missing-building degradation",
                "S",
                count,
                OUT_DIR / f"zeroshot_s_missing{count}/zeroshot_test_metrics.json",
                OUT_DIR / f"zeroshot_s_missing{count}/zeroshot_test_metrics_rerun.json",
                OUT_DIR / f"zeroshot_s_missing{count}/stage4_zeroshot_manifest.json",
            )
        )
        rows.append(
            metric_row(
                "zero-shot missing-building degradation",
                "C",
                count,
                OUT_DIR / f"zeroshot_c_missing{count}/zeroshot_test_metrics.json",
                OUT_DIR / f"zeroshot_c_missing{count}/zeroshot_test_metrics_rerun.json",
                OUT_DIR / f"zeroshot_c_missing{count}/stage4_zeroshot_manifest.json",
            )
        )

    rows.append(
        metric_row(
            "complete-map upper reference",
            "S",
            0,
            ROOT / "reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics.json",
            ROOT / "reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics_rerun.json",
            ROOT / "reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/stage3c_run_manifest.json",
        )
    )
    rows.append(
        metric_row(
            "complete-map upper reference",
            "C",
            0,
            ROOT / "reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics.json",
            ROOT / "reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics_rerun.json",
            ROOT / "reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep/stage3c_run_manifest.json",
        )
    )
    for count in [1, 2, 4]:
        rows.append(
            metric_row(
                "sparse-adapted missing-building robustness",
                "S",
                count,
                OUT_DIR / f"s_irt4_missing{count}_pool600_sparse_loss_50ep/secondU_test_metrics.json",
                OUT_DIR / f"s_irt4_missing{count}_pool600_sparse_loss_50ep/secondU_test_metrics_rerun.json",
                OUT_DIR / f"s_irt4_missing{count}_pool600_sparse_loss_50ep/stage4_run_manifest.json",
            )
        )
        rows.append(
            metric_row(
                "C baseline",
                "C",
                count,
                OUT_DIR / f"c_irt4_missing{count}_sparse_loss_50ep/secondU_test_metrics.json",
                OUT_DIR / f"c_irt4_missing{count}_sparse_loss_50ep/secondU_test_metrics_rerun.json",
                OUT_DIR / f"c_irt4_missing{count}_sparse_loss_50ep/stage4_run_manifest.json",
            )
        )
    return rows


def rows_by(rows: list[dict[str, Any]], kind: str, model: str) -> dict[int, dict[str, Any]]:
    return {row["missing_buildings"]: row for row in rows if row["kind"] == kind and row["model"] == model}


def loader_audit_paths() -> list[Path]:
    paths = []
    for prefix in ["s_irt4", "c_irt4"]:
        for count in COUNTS:
            if prefix == "s_irt4":
                name = f"{prefix}_missing{count}_pool600_sparse_loss"
            else:
                name = f"{prefix}_missing{count}_sparse_loss"
            paths.append(OUT_DIR / f"loader_audits/{name}_missing_loader_audit.json")
    return paths


def make_plot(rows: list[dict[str, Any]], output: Path) -> None:
    series = [
        ("S zero-shot", rows_by(rows, "zero-shot missing-building degradation", "S"), "#1f77b4"),
        ("S sparse-adapted", rows_by(rows, "sparse-adapted missing-building robustness", "S") | {0: rows_by(rows, "complete-map upper reference", "S")[0]}, "#2ca02c"),
        ("C zero-shot", rows_by(rows, "zero-shot missing-building degradation", "C"), "#d62728"),
        ("C sparse-adapted", rows_by(rows, "C baseline", "C") | {0: rows_by(rows, "complete-map upper reference", "C")[0]}, "#9467bd"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for label, data, color in series:
        xs = COUNTS
        axes[0].plot(xs, [data[x]["dense_mse"] for x in xs], marker="o", label=label, color=color)
        axes[1].plot(xs, [data[x]["sparse_mse"] for x in xs], marker="o", label=label, color=color)
    axes[0].set_title("Dense MSE")
    axes[1].set_title("Sparse-point MSE")
    for ax in axes:
        ax.set_xlabel("missing buildings")
        ax.set_xticks(COUNTS)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("MSE")
    axes[0].legend(fontsize=8)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def write_markdown(audit: dict[str, Any]) -> None:
    rows = audit["rows"]
    lines = [
        "# Stage 4 missing-buildings 最终审计",
        "",
        "## 结论分区",
        "- zero-shot missing-building degradation：S/C 源 DPM checkpoint 直接评估 missing0/1/2/4。",
        "- sparse-adapted missing-building robustness：S missing1/2/4 采用 pool600、输入 1..300、sparse loss；missing0 使用 Stage 3C complete-map upper reference。",
        "- complete-map upper reference：Stage 3C S/C complete-map IRT4 sparse adaptation。",
        "- C baseline：C missing1/2/4 sparse adaptation，missing0 使用 Stage 3C C reference。",
        "",
        "## 指标",
        "| 类别 | 模型 | missing | 样本数 | dense MSE | sparse MSE | rerun diff |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    order = {
        "zero-shot missing-building degradation": 0,
        "sparse-adapted missing-building robustness": 1,
        "complete-map upper reference": 2,
        "C baseline": 3,
    }
    for row in sorted(rows, key=lambda item: (order[item["kind"]], item["model"], item["missing_buildings"])):
        lines.append(
            f"| {row['kind']} | {row['model']} | {row['missing_buildings']} | {row['samples']} | "
            f"{row['dense_mse']:.10f} | {row['sparse_mse']:.10f} | {row['rerun_max_abs_diff']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## 回答",
            f"- 缺楼越多是否退化：`{audit['answers']['zero_shot_degrades_with_missing_count']}`。",
            f"- sparse measurements 是否缓解退化：`{audit['answers']['sparse_adaptation_improves_s_over_zero_shot']}`。",
            f"- paper-faithful S 是否优于 C：`{audit['answers']['s_adapted_beats_c_adapted']}`。",
            f"- complete-map Stage 3C 作为上界：`{audit['answers']['complete_map_reference_present']}`。",
            f"- 与论文趋势一致：`{audit['answers']['paper_trend_consistent']}`。",
            "",
            f"曲线图：`{audit['figures']['missing_count_curve']}`",
            "",
            f"最终 gate：`{audit['gate']['pass']}`。",
        ]
    )
    (OUT_DIR / "stage4_final_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = collect_rows()
    make_plot(rows, OUT_DIR / "stage4_missing_count_curves.png")
    s_zero = rows_by(rows, "zero-shot missing-building degradation", "S")
    s_adapt = rows_by(rows, "sparse-adapted missing-building robustness", "S")
    s_adapt[0] = rows_by(rows, "complete-map upper reference", "S")[0]
    c_adapt = rows_by(rows, "C baseline", "C")
    c_adapt[0] = rows_by(rows, "complete-map upper reference", "C")[0]
    loader_audits = [load_json(path) for path in loader_audit_paths()]
    answers = {
        "zero_shot_degrades_with_missing_count": s_zero[4]["dense_mse"] > s_zero[0]["dense_mse"],
        "sparse_adaptation_improves_s_over_zero_shot": all(
            s_adapt[count]["dense_mse"] < s_zero[count]["dense_mse"] and s_adapt[count]["sparse_mse"] < s_zero[count]["sparse_mse"]
            for count in COUNTS
        ),
        "s_adapted_beats_c_adapted": all(
            s_adapt[count]["dense_mse"] < c_adapt[count]["dense_mse"] and s_adapt[count]["sparse_mse"] < c_adapt[count]["sparse_mse"]
            for count in COUNTS
        ),
        "complete_map_reference_present": 0 in s_adapt and 0 in c_adapt,
    }
    answers["paper_trend_consistent"] = (
        answers["zero_shot_degrades_with_missing_count"]
        and answers["sparse_adaptation_improves_s_over_zero_shot"]
        and answers["s_adapted_beats_c_adapted"]
    )
    gate = {
        "counts_0_1_2_4_present": sorted({row["missing_buildings"] for row in rows}) == COUNTS,
        "all_test_samples_198": all(row["samples"] == 198 for row in rows),
        "all_reruns_exact": all(row["rerun_max_abs_diff"] == 0.0 for row in rows),
        "all_manifest_gates_pass": all(row["manifest_gate"].get("pass") for row in rows),
        "all_loader_audits_pass": all(item["gate"]["pass"] for item in loader_audits),
        "long_runs_have_50_train_epochs": all(
            row.get("history", {}).get("train_entries") == 50
            for row in rows
            if row["kind"] in {"sparse-adapted missing-building robustness", "C baseline", "complete-map upper reference"}
        ),
        "checkpoints_not_tracked": all(not row.get("checkpoint_tracked_by_git", False) for row in rows if "checkpoint_tracked_by_git" in row),
        "answers_true": all(answers.values()),
    }
    gate["pass"] = all(gate.values())
    audit = {
        "scope": "Stage 4 missing-buildings final audit",
        "git": git_metadata(exclude_paths=["reports"]),
        "rows": rows,
        "loader_audits": [str(path.relative_to(ROOT)) for path in loader_audit_paths()],
        "figures": {"missing_count_curve": "reports/missing_buildings/stage4_missing_count_curves.png"},
        "answers": answers,
        "gate": gate,
    }
    save_json(audit, OUT_DIR / "stage4_final_audit.json")
    write_markdown(audit)
    print(gate)
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
