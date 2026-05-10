#!/usr/bin/env python3
"""Audit the repository against plan.md full-matrix reproduction requirements."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import git_metadata, load_yaml, save_json

OUT_DIR = ROOT / "reports/full_matrix"
DOC_PATH = ROOT / "docs/full_matrix_reproduction_summary.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def exists(path: str | Path) -> bool:
    return (ROOT / path).exists()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def file_nonempty(path: str | Path) -> bool:
    target = ROOT / path
    return target.exists() and target.stat().st_size > 0


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


def metric_status(metrics_path: str, rerun_path: str | None = None) -> dict[str, Any]:
    out = {"metrics_path": metrics_path, "exists": exists(metrics_path)}
    if not out["exists"]:
        out["gate"] = False
        return out
    metrics = load_json(metrics_path)
    out["samples"] = metrics.get("samples")
    out["git_dirty"] = metrics.get("git", {}).get("dirty")
    out["secondU_mse"] = metrics.get("secondU", {}).get("mse")
    out["secondU_nmse"] = metrics.get("secondU", {}).get("nmse")
    if rerun_path:
        out["rerun_path"] = rerun_path
        out["rerun_exists"] = exists(rerun_path)
        out["rerun_max_abs_diff"] = max_abs_diff(metrics, load_json(rerun_path)) if out["rerun_exists"] else None
    out["gate"] = out["exists"] and (not rerun_path or (out.get("rerun_exists") and out.get("rerun_max_abs_diff") == 0.0))
    return out


def config_status(path: str, required: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"path": path, "exists": exists(path)}
    if not out["exists"]:
        out["gate"] = False
        return out
    cfg = load_yaml(ROOT / path)
    checks = {}
    for dotted, expected in (required or {}).items():
        value: Any = cfg
        for part in dotted.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        checks[dotted] = {"expected": expected, "actual": value, "pass": value == expected}
    out["checks"] = checks
    out["gate"] = all(item["pass"] for item in checks.values())
    return out


def run_command(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def collect_configs() -> dict[str, Any]:
    expected = {
        "c_irt2_thr2": {"data.simulation": "IRT2", "data.loader": "RadioUNet_c"},
        "s_irt2_thr2_rand1_300": {"data.simulation": "IRT2", "data.loader": "RadioUNet_s", "data.num_samples_low": 1, "data.num_samples_high": 301},
        "c_rand_thr2": {"data.simulation": "rand", "data.IRT2maxW": 1.0},
        "s_rand_thr2_rand1_300": {"data.simulation": "rand", "data.num_samples_low": 1, "data.num_samples_high": 301},
        "s_dpmcars_carinput_thr2_rand1_300": {"data.cars_simulation": "yes", "data.cars_input": "yes", "model.inputs": 4},
        "s_irt2cars_carinput_thr2_rand1_300": {"data.cars_simulation": "yes", "data.cars_input": "yes", "model.inputs": 4},
        "c_dpmcars_thr2": {"data.cars_simulation": "yes", "data.cars_input": "no"},
        "c_irt2cars_thr2": {"data.cars_simulation": "yes", "data.cars_input": "no"},
    }
    for source in ["dpm", "irt2", "rand"]:
        for model in ["c", "s"]:
            for mode in ["zeroshot", "adapt"]:
                expected[f"{model}_{source}_irt4_{mode}"] = {"data.simulation": "IRT4", "data.num_tx": 2}
    for count in [0, 1, 2, 4]:
        expected[f"c_dpm_irt4_missing{count}_fixedrx_adapt"] = {"data.receiver_seed_policy": "fixed_map", "data.num_tx": 2}
        expected[f"s_dpm_irt4_missing{count}_fixedrx_adapt"] = {"data.receiver_seed_policy": "fixed_map", "data.num_tx": 2}
    return {name: config_status(f"configs/{name}.yaml", required) for name, required in expected.items()}


def collect_existing_runs() -> dict[str, Any]:
    runs = {
        "c_dpm_clean": metric_status(
            "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json",
            "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics_rerun.json",
        ),
        "s_dpm_rand1_300": metric_status(
            "reports/s_dpm_thr2/rand1_300_50ep/secondU_test_metrics.json",
            "reports/s_dpm_thr2/rand1_300_50ep/secondU_test_metrics_rerun.json",
        ),
        "s_dpm_fixed50": metric_status(
            "reports/s_dpm_thr2/fix50_50ep/secondU_test_metrics.json",
            "reports/s_dpm_thr2/fix50_50ep/secondU_test_metrics_rerun.json",
        ),
        "s_dpm_fixed100": metric_status(
            "reports/s_dpm_thr2/fix100_50ep/secondU_test_metrics.json",
            "reports/s_dpm_thr2/fix100_50ep/secondU_test_metrics_rerun.json",
        ),
        "s_dpm_fixed300": metric_status(
            "reports/s_dpm_thr2/fix300_50ep/secondU_test_metrics.json",
            "reports/s_dpm_thr2/fix300_50ep/secondU_test_metrics_rerun.json",
        ),
        "s_dpm_rand10_300": metric_status(
            "reports/s_dpm_thr2/rand10_300_50ep/secondU_test_metrics.json",
            "reports/s_dpm_thr2/rand10_300_50ep/secondU_test_metrics_rerun.json",
        ),
        "s_irt4_dpm_adapt_pool600": metric_status(
            "reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics.json",
            "reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics_rerun.json",
        ),
        "c_irt4_dpm_adapt": metric_status(
            "reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics.json",
            "reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics_rerun.json",
        ),
    }
    for model in ["c", "s"]:
        for count in [0, 1, 2, 4]:
            runs[f"{model}_irt4_missing{count}_zeroshot"] = metric_status(
                f"reports/missing_buildings/zeroshot_{model}_missing{count}/zeroshot_test_metrics.json",
                f"reports/missing_buildings/zeroshot_{model}_missing{count}/zeroshot_test_metrics_rerun.json",
            )
        for count in [1, 2, 4]:
            if model == "s":
                stem = f"s_irt4_missing{count}_pool600_sparse_loss_50ep"
            else:
                stem = f"c_irt4_missing{count}_sparse_loss_50ep"
            runs[f"{model}_irt4_missing{count}_adapt"] = metric_status(
                f"reports/missing_buildings/{stem}/secondU_test_metrics.json",
                f"reports/missing_buildings/{stem}/secondU_test_metrics_rerun.json",
            )
    return runs


def make_figures(runs: dict[str, Any]) -> dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    figures: dict[str, str] = {}

    labels = ["C zero-shot", "S zero-shot", "C adapt", "S adapt"]
    keys = [
        "c_irt4_missing0_zeroshot",
        "s_irt4_missing0_zeroshot",
        "c_irt4_dpm_adapt",
        "s_irt4_dpm_adapt_pool600",
    ]
    values = [runs[key].get("secondU_mse") for key in keys]
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    ax.bar(labels, [value if value is not None else 0 for value in values], color=["#64748b", "#2563eb", "#f97316", "#16a34a"])
    ax.set_ylabel("MSE")
    ax.set_title("Fig. 8 reproduction subset: DPM-source IRT4")
    ax.tick_params(axis="x", rotation=20)
    fig8 = OUT_DIR / "fig8_radio_unet_performance.png"
    fig.savefig(fig8, dpi=160)
    plt.close(fig)
    figures["fig8_radio_unet_performance"] = rel(fig8)

    src_fig9 = ROOT / "reports/missing_buildings/stage4_missing_count_curves.png"
    fig9 = OUT_DIR / "fig9_wnet_missing_buildings.png"
    if src_fig9.exists():
        shutil.copy2(src_fig9, fig9)
        figures["fig9_wnet_missing_buildings"] = rel(fig9)

    src_fig10 = ROOT / "reports/s_dpm_thr2/sample_count_metric_curves.png"
    fig10 = OUT_DIR / "fig10_state_of_art_comparison.png"
    if src_fig10.exists():
        shutil.copy2(src_fig10, fig10)
        figures["fig10_state_of_art_comparison"] = rel(fig10)
    return figures


def build_requirements(configs: dict[str, Any], runs: dict[str, Any], figures: dict[str, str]) -> list[dict[str, Any]]:
    def all_configs(names: list[str]) -> bool:
        return all(configs.get(name, {}).get("gate") for name in names)

    def all_runs(names: list[str]) -> bool:
        return all(runs.get(name, {}).get("gate") for name in names)

    rows = [
        {
            "requirement": "1. Coarse simulation 全矩阵：DPM/IRT2/rand x C/S，50 epoch firstU+secondU，metrics/rerun/history/manifest/8图。",
            "evidence": "DPM C/S 已有；IRT2/rand 配置已补齐；IRT2/rand full runs 尚缺。",
            "paths": ["configs/c_irt2_thr2.yaml", "configs/s_irt2_thr2_rand1_300.yaml", "configs/c_rand_thr2.yaml", "configs/s_rand_thr2_rand1_300.yaml"],
            "pass": all_runs(["c_dpm_clean", "s_dpm_rand1_300"]) and all_configs(["c_irt2_thr2", "s_irt2_thr2_rand1_300", "c_rand_thr2", "s_rand_thr2_rand1_300"]),
            "blocking_gap": "缺 IRT2/rand 的 50 epoch run、rerun、manifest、qualitative figures 和 coarse_simulation_audit。",
        },
        {
            "requirement": "2. IRT4 transfer 全矩阵：source DPM/IRT2/rand x C/S x zero-shot/adapt。",
            "evidence": "DPM-source C/S zero-shot/adapt 已有主要产物；IRT2/rand-source transfer 只有配置骨架。",
            "paths": ["scripts/audit_stage3c_final.py", "configs/c_irt2_irt4_adapt.yaml", "configs/s_rand_irt4_adapt.yaml"],
            "pass": False,
            "blocking_gap": "缺 IRT2/rand source checkpoint，不能完成对应 zero-shot/adapt；缺 reports/full_matrix/irt4_transfer_matrix。",
        },
        {
            "requirement": "3. Cars 场景完整复现：DPM/IRT2/IRT4 cars、cars input、no-cars 对照。",
            "evidence": "cars 数据目录存在；cars configs 已补；尚无 cars 训练/评估/审计产物。",
            "paths": ["RadioMapSeer/gain/carsDPM", "RadioMapSeer/gain/carsIRT2", "RadioMapSeer/gain/carsIRT4", "configs/s_dpmcars_carinput_thr2_rand1_300.yaml"],
            "pass": False,
            "blocking_gap": "缺 cars full runs、cars_audit、cars qualitative figures。",
        },
        {
            "requirement": "4. Missing buildings 全矩阵与 fixed receiver 对照。",
            "evidence": "official-loader-faithful missing0/1/2/4 已有；fixed receiver loader 参数、DPM-source configs 和 hash-level policy audit 已补。",
            "paths": ["src/radiounet/data.py", "configs/s_dpm_irt4_missing4_fixedrx_adapt.yaml", "reports/full_matrix/fixed_receiver_policy_audit.json"],
            "pass": False,
            "blocking_gap": "缺 fixed receiver policy 的 full runs/metrics/rerun/manifest；缺 IRT2/rand source missing matrix。",
        },
        {
            "requirement": "5. Sample count 曲线与 state-of-the-art 对比：RadioUNet_S、RBF、TC、tomography、MLP、C baseline。",
            "evidence": "已有 RadioUNet_S sample-count ablation；传统/MLP baseline 脚本和结果缺失。",
            "paths": ["reports/s_dpm_thr2/sample_count_sweep_audit.json"],
            "pass": False,
            "blocking_gap": "缺 src/radiounet/baselines.py、run_state_of_art_baselines.py、baseline metrics/runtime、公平性审计。",
        },
        {
            "requirement": "6. WNet/model size/threshold 矩阵：size、with/without secondU、threshold、400/100/200 split。",
            "evidence": "当前模型未参数化 size；threshold/split 矩阵缺失。",
            "paths": ["src/radiounet/models.py"],
            "pass": False,
            "blocking_gap": "缺模型 size 参数化、参数量/architecture hash、threshold preprocessing audit、split overlap audit。",
        },
        {
            "requirement": "7. 论文图表级汇总：paper_table_reproduction、Fig8/9/10、summary docs。",
            "evidence": "本脚本生成图表级汇总草案和现有子集图；由于上游矩阵缺口，final gate 仍失败。",
            "paths": ["reports/full_matrix/paper_table_reproduction.md", "reports/full_matrix/fig8_radio_unet_performance.png", "docs/full_matrix_reproduction_summary.md"],
            "pass": all(file_nonempty(path) for path in figures.values()),
            "blocking_gap": "图表只覆盖现有子集，不能代表论文全矩阵。",
        },
    ]
    return rows


def write_paper_table(audit: dict[str, Any]) -> None:
    table = {
        "fig8_radio_unet_performance": {
            "reproduction_path": audit["figures"].get("fig8_radio_unet_performance"),
            "runs": ["c_irt4_missing0_zeroshot", "s_irt4_missing0_zeroshot", "c_irt4_dpm_adapt", "s_irt4_dpm_adapt_pool600"],
            "gate": False,
            "residual_risk": "仅 DPM-source 子集，缺 IRT2/rand source transfer。",
        },
        "fig9_wnet_missing_buildings": {
            "reproduction_path": audit["figures"].get("fig9_wnet_missing_buildings"),
            "runs": [key for key in audit["runs"] if "missing" in key],
            "gate": False,
            "residual_risk": "official-loader-faithful 子集；缺 fixed receiver 和 IRT2/rand source。",
        },
        "fig10_state_of_art_comparison": {
            "reproduction_path": audit["figures"].get("fig10_state_of_art_comparison"),
            "runs": ["s_dpm_fixed50", "s_dpm_fixed100", "s_dpm_fixed300", "s_dpm_rand1_300"],
            "gate": False,
            "residual_risk": "缺 RBF、tensor completion、tomography、MLP baseline。",
        },
    }
    save_json(table, OUT_DIR / "paper_table_reproduction.json")
    lines = [
        "# 论文图表复现汇总",
        "",
        "| 论文图/表 | 本仓库复现图 | 参与 run | gate | residual risk |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, row in table.items():
        lines.append(
            f"| `{name}` | `{row['reproduction_path']}` | `{', '.join(row['runs'])}` | `{row['gate']}` | {row['residual_risk']} |"
        )
    (OUT_DIR / "paper_table_reproduction.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# Full Matrix 最终审计",
        "",
        "## 结论",
        f"- final gate：`{audit['gate']['pass']}`。",
        "- 这次审计没有把缺失矩阵伪装为完成；所有未覆盖项均标为 blocking gap。",
        f"- 当前 git 状态（排除 reports）：dirty=`{audit['git_excluding_reports']['dirty']}`，commit=`{audit['git_excluding_reports']['commit']}`。",
        "",
        "## Prompt-to-artifact checklist",
        "| 要求 | 证据 | 通过 | 缺口 |",
        "| --- | --- | --- | --- |",
    ]
    for row in audit["requirements"]:
        lines.append(f"| {row['requirement']} | {row['evidence']} | `{row['pass']}` | {row['blocking_gap']} |")
    lines.extend(["", "## 新增配置 gate", "| config | gate |", "| --- | ---: |"])
    for name, row in sorted(audit["configs"].items()):
        lines.append(f"| `{name}` | `{row['gate']}` |")
    lines.extend(["", "## 已有 run 可复验状态", "| run | metrics | samples | rerun diff | gate |", "| --- | --- | ---: | ---: | ---: |"])
    for name, row in sorted(audit["runs"].items()):
        diff = row.get("rerun_max_abs_diff")
        diff_text = "" if diff is None else f"{diff:.1f}"
        lines.append(f"| `{name}` | `{row['metrics_path']}` | {row.get('samples', '')} | {diff_text} | `{row['gate']}` |")
    lines.extend(
        [
            "",
            "## 下一批必须执行的命令",
            "1. 先跑 `python scripts/generate_full_matrix_configs.py` 固化配置。",
            "2. 对 IRT2/rand coarse configs 跑 smoke audit 和 50 epoch firstU+secondU。",
            "3. 用 IRT2/rand firstU checkpoint 跑 IRT4 zero-shot/adapt 矩阵。",
            "4. 跑 cars、fixed receiver missing、baselines、model size/threshold/split 矩阵。",
            "5. 每批跑对应 audit 后重跑本脚本，直到 final gate 为 `True`。",
        ]
    )
    (OUT_DIR / "final_full_matrix_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(audit: dict[str, Any]) -> None:
    passed = sum(1 for row in audit["requirements"] if row["pass"])
    total = len(audit["requirements"])
    lines = [
        "# Full Matrix 复现收尾状态",
        "",
        f"- 当前通过项：{passed}/{total}。",
        f"- final gate：`{audit['gate']['pass']}`。",
        "- reduced reproduction 仍以 `reports/final_reproduction_audit.*` 为准；full matrix 交付以 `reports/full_matrix/final_full_matrix_audit.*` 为准。",
        "- 当前主要缺口：IRT2/rand full runs、cars runs、fixed receiver missing runs、state-of-the-art baselines、model size/threshold/split 矩阵。",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    configs = collect_configs()
    runs = collect_existing_runs()
    figures = make_figures(runs)
    audit = {
        "objective": "严格完成 plan.md 的论文 full-matrix reproduction 收尾。",
        "git": git_metadata(),
        "git_excluding_reports": git_metadata(exclude_paths=["reports"]),
        "configs": configs,
        "runs": runs,
        "figures": figures,
        "requirements": [],
        "gate": {},
    }
    audit["requirements"] = build_requirements(configs, runs, figures)
    audit["gate"] = {
        "pass": all(row["pass"] for row in audit["requirements"]),
        "reason": "所有 plan.md 要求均必须有具体 config/run/metrics/rerun/manifest/figure/audit 证据。",
    }
    save_json(audit, OUT_DIR / "final_full_matrix_audit.json")
    write_paper_table(audit)
    write_markdown(audit)
    write_summary(audit)
    print(f"final gate: {audit['gate']['pass']}")
    print(f"saved: {rel(OUT_DIR / 'final_full_matrix_audit.json')}")
    return 0 if audit["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
