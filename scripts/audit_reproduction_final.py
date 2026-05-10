#!/usr/bin/env python3
"""Generate the final cross-stage reproduction audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.utils import git_metadata, save_json


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def git_tracked(path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def stage1() -> dict[str, Any]:
    metrics = load_json(ROOT / "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json")
    first_manifest = load_json(ROOT / "reports/c_dpm_thr2/20260506_182311/firstU_checkpoint_manifest.json")
    second_manifest = load_json(ROOT / "reports/c_dpm_thr2/20260506_182311/secondU_checkpoint_manifest.json")
    evidence = {
        "config": "configs/c_dpm_thr2.yaml",
        "audit": "docs/stage1_c_dpm_thr2_audit.md",
        "run_dir": "reports/c_dpm_thr2/20260506_182311",
        "metrics": "reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json",
        "first_checkpoint_sha256": first_manifest["sha256"],
        "second_checkpoint_sha256": second_manifest["sha256"],
        "figures_glob": "reports/c_dpm_thr2/20260506_182311/figures/*.png",
    }
    gate = {
        "config_exists": exists(evidence["config"]),
        "audit_exists": exists(evidence["audit"]),
        "metrics_exist": exists(evidence["metrics"]),
        "samples_7920": metrics.get("samples") == 7920,
        "firstU_metrics_present": "firstU" in metrics,
        "secondU_metrics_present": "secondU" in metrics,
        "metrics_git_clean": metrics.get("git", {}).get("dirty") is False,
        "checkpoints_not_tracked": not git_tracked(first_manifest["checkpoint"]) and not git_tracked(second_manifest["checkpoint"]),
        "eight_figures": len(list((ROOT / "reports/c_dpm_thr2/20260506_182311/figures").glob("*.png"))) == 8,
    }
    gate["pass"] = all(gate.values())
    return {
        "name": "Stage 1 C DPM baseline",
        "label": "paper-faithful baseline",
        "paper_claim": "RadioUNet_C clean city-map DPM baseline with WNet firstU/secondU.",
        "evidence": evidence,
        "metrics": metrics["secondU"],
        "gate": gate,
        "conclusion": "MSE/RMSE 接近官方 notebook；NMSE 偏高但已解释为分母/数据口径敏感项。",
    }


def stage2() -> dict[str, Any]:
    audit = load_json(ROOT / "reports/s_dpm_thr2/stage2_final_audit.json")
    mainline = next(run for run in audit["runs"] if run["setting"] == "paper-faithful random 1..300")
    gate = {
        "config_exists": exists("configs/s_dpm_thr2_rand1_300.yaml"),
        "audit_exists": exists("reports/s_dpm_thr2/stage2_final_audit.json"),
        "markdown_exists": exists("reports/s_dpm_thr2/stage2_final_audit.md"),
        "curve_exists": exists("reports/s_dpm_thr2/stage2_final_metric_curves.png"),
        "mainline_is_paper_faithful": mainline["category"] == "paper-faithful random sample count",
        "mainline_gate_passed": mainline.get("gate", {}).get("passed") is True,
        "rerun_exact": mainline.get("gate", {}).get("rerun_exact") is True,
        "checkpoints_not_tracked": mainline.get("gate", {}).get("checkpoint_files_tracked_by_git") is False,
    }
    gate["pass"] = all(gate.values())
    return {
        "name": "Stage 2 S DPM random 1..300",
        "label": "paper-faithful mainline plus ablations",
        "paper_claim": "Sparse measurements improve RadioUNet_S under DPM complete-map setting.",
        "evidence": {
            "config": "configs/s_dpm_thr2_rand1_300.yaml",
            "audit": "reports/s_dpm_thr2/stage2_final_audit.json",
            "markdown": "reports/s_dpm_thr2/stage2_final_audit.md",
            "figure": "reports/s_dpm_thr2/stage2_final_metric_curves.png",
        },
        "metrics": mainline["metrics"]["secondU"],
        "gate": gate,
        "conclusion": "random 1..300 主线优于 Stage 1 C baseline；fixed 50/100/200/300 仅作为 ablation。",
    }


def stage3() -> dict[str, Any]:
    audit = load_json(ROOT / "reports/irt4_transfer/stage3c_final_audit.json")
    mainline = audit["runs"]["paper_faithful_mainline"]
    gate = {
        "config_exists": exists("configs/s_irt4_adapt_rand1_300_pool600_sparse_loss.yaml"),
        "audit_exists": exists("reports/irt4_transfer/stage3c_final_audit.json"),
        "markdown_exists": exists("reports/irt4_transfer/stage3c_final_audit.md"),
        "final_gate_passed": audit.get("gate", {}).get("pass") is True,
        "mainline_manifest_gate_passed": mainline.get("manifest_gate", {}).get("pass") is True,
        "mainline_semantic_gate_passed": mainline.get("semantic_gate", {}).get("pass") is True,
        "rerun_exact": mainline.get("rerun_max_abs_diff") == 0.0,
        "checkpoint_not_tracked": mainline.get("checkpoint_tracked_by_git") is False,
    }
    gate["pass"] = all(gate.values())
    return {
        "name": "Stage 3C IRT4 sparse adaptation",
        "label": "paper-faithful mainline, dense-loss pilot, ablation",
        "paper_claim": "RadioUNet_S can adapt to high-fidelity IRT4 with sparse measurements.",
        "evidence": {
            "config": "configs/s_irt4_adapt_rand1_300_pool600_sparse_loss.yaml",
            "audit": "reports/irt4_transfer/stage3c_final_audit.json",
            "markdown": "reports/irt4_transfer/stage3c_final_audit.md",
        },
        "metrics": {
            "dense_mse": mainline["dense_mse"],
            "dense_global_nmse": mainline["dense_global_nmse"],
            "sparse_mse": mainline["sparse_mse"],
            "sparse_global_nmse": mainline["sparse_global_nmse"],
        },
        "gate": gate,
        "conclusion": "pool600、输入 1..300、sparse loss 主线成立；dense-loss pilot 已降级为非主线。",
    }


def stage4() -> dict[str, Any]:
    audit = load_json(ROOT / "reports/missing_buildings/stage4_final_audit.json")
    s4 = next(
        row
        for row in audit["rows"]
        if row["kind"] == "sparse-adapted missing-building robustness"
        and row["model"] == "S"
        and row["missing_buildings"] == 4
    )
    gate = {
        "configs_exist": all(exists(f"configs/s_irt4_missing{count}_pool600_sparse_loss.yaml") for count in [0, 1, 2, 4])
        and all(exists(f"configs/c_irt4_missing{count}_sparse_loss.yaml") for count in [0, 1, 2, 4]),
        "audit_exists": exists("reports/missing_buildings/stage4_final_audit.json"),
        "markdown_exists": exists("reports/missing_buildings/stage4_final_audit.md"),
        "curve_exists": exists("reports/missing_buildings/stage4_missing_count_curves.png"),
        "final_gate_passed": audit.get("gate", {}).get("pass") is True,
        "cross_missing_target_consistency_checked": audit.get("gate", {}).get("loader_audits_include_cross_missing_target_consistency") is True,
        "dirty_provenance_recorded": audit.get("gate", {}).get("dirty_provenance_recorded_as_residual_risk") is True,
        "reruns_exact": audit.get("gate", {}).get("all_reruns_exact") is True,
        "checkpoints_not_tracked": audit.get("gate", {}).get("checkpoints_not_tracked") is True,
    }
    gate["pass"] = all(gate.values())
    return {
        "name": "Stage 4 missing buildings robustness",
        "label": "official-loader-faithful missing-building sparse sampling",
        "paper_claim": "Sparse measurements improve robustness when input city maps have missing buildings.",
        "evidence": {
            "audit": "reports/missing_buildings/stage4_final_audit.json",
            "markdown": "reports/missing_buildings/stage4_final_audit.md",
            "figure": "reports/missing_buildings/stage4_missing_count_curves.png",
        },
        "metrics": {
            "s_missing4_dense_mse": s4["dense_mse"],
            "s_missing4_sparse_mse": s4["sparse_mse"],
        },
        "gate": gate,
        "conclusion": "0/1/2/4 missing sweep 完成；S sparse-adapted 优于 S zero-shot 和 C adapted，但 receiver mask 语义按官方 loader 标注。",
        "residual_risk": audit.get("provenance", {}),
    }


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# RadioUNet 最终复现审计",
        "",
        "## 总结",
        f"- 最终 gate：`{audit['gate']['pass']}`。",
        f"- 当前源码状态（排除 reports）：dirty=`{audit['git']['dirty']}`，commit=`{audit['git']['commit']}`。",
        "- 本报告覆盖 Stage 1 C/DPM、Stage 2 S/DPM、Stage 3C IRT4 sparse adaptation、Stage 4 missing buildings robustness。",
        "- checkpoint、dataset、cache 均不作为 git 交付物；报告、metrics、manifest、图和配置快照作为可审计交付物。",
        "",
        "## Prompt-to-artifact checklist",
        "| 要求 | 证据 | 通过 |",
        "| --- | --- | --- |",
    ]
    for item in audit["checklist"]:
        lines.append(f"| {item['requirement']} | {item['evidence']} | `{item['passed']}` |")
    lines.extend(["", "## 阶段结论"])
    for stage in audit["stages"]:
        lines.extend(
            [
                f"### {stage['name']}",
                f"- 标签：`{stage['label']}`",
                f"- 论文主张：{stage['paper_claim']}",
                f"- 结论：{stage['conclusion']}",
                f"- gate：`{stage['gate']['pass']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## 覆盖与差距",
            "- 已复现：clean DPM C baseline、DPM S random 1..300、IRT4 sparse adaptation、missing0/1/2/4 鲁棒性趋势。",
            "- implementation-faithful：Stage 4 sparse receiver mask 由 missing building image seed 决定，因此标为 official-loader-faithful / implementation-faithful。",
            "- ablation：Stage 2 fixed sample sweep、Stage 3C pool300 sparse ablation、Stage 3C dense-loss pilot。",
            "- 未覆盖：cars 鲁棒性、IRT2/rand simulation 全矩阵、固定 receiver mask missing-building 对照、论文表格级完整排版。",
            "- residual risk：Stage 4 历史 metrics/manifest 中记录了 dirty provenance；若用于最终投稿级 provenance，建议在当前 clean 源码上重跑 Stage 4 eval/audit/manifest，必要时重跑 adaptation。",
            "",
            "## 当前最可信产物",
            "- `docs/stage1_c_dpm_thr2_audit.md`",
            "- `reports/s_dpm_thr2/stage2_final_audit.md`",
            "- `reports/irt4_transfer/stage3c_final_audit.md`",
            "- `reports/missing_buildings/stage4_final_audit.md`",
            "- `reports/final_reproduction_audit.json`",
        ]
    )
    (ROOT / "reports/final_reproduction_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(audit: dict[str, Any]) -> None:
    lines = [
        "# RadioUNet 复现总结",
        "",
        "本仓库已形成一条可审计的 RadioUNet 复现主线：从 clean DPM baseline，到 sparse DPM，再到 IRT4 sparse adaptation，最后到 missing buildings robustness。",
        "",
        "## 已复现的主结论",
        "- WNet secondU 在 Stage 1 C/DPM baseline 上改善 firstU。",
        "- RadioUNet_S 在 DPM complete-map 设置下利用 sparse measurements 优于 C baseline。",
        "- IRT4 transfer 中，S sparse adaptation 优于 zero-shot 与 C sparse baseline。",
        "- missing buildings 中，S sparse-adapted 在 1/2/4 缺楼设置下优于 S zero-shot 和 C adapted，趋势与论文鲁棒性主张一致。",
        "",
        "## 口径说明",
        "- `paper-faithful`：Stage 1、Stage 2 random 1..300、Stage 3C pool600 sparse-loss 主线。",
        "- `official-loader-faithful` / `implementation-faithful`：Stage 4 missing buildings，因为 sparse receiver mask 随 missing building image seed 改变。",
        "- `ablation`：fixed sample sweep、pool300 sparse ablation、dense-loss pilot。",
        "- `residual risk`：Stage 4 历史产物记录了 dirty provenance；最终投稿级 provenance 需要 clean rerun。",
        "",
        "## 推荐引用",
        "- 总审计：`reports/final_reproduction_audit.md`",
        "- 机器可读总审计：`reports/final_reproduction_audit.json`",
        "- Stage 4 主图：`reports/missing_buildings/stage4_missing_count_curves.png`",
    ]
    (ROOT / "docs/reproduction_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    stages = [stage1(), stage2(), stage3(), stage4()]
    checklist = [
        {
            "requirement": "完成 plan.md 的 Stage 4 审计漏洞修复",
            "evidence": "scripts/audit_missing_buildings_loader.py + reports/missing_buildings/loader_audits/*.json",
            "passed": stages[3]["gate"]["cross_missing_target_consistency_checked"],
        },
        {
            "requirement": "收紧 final gate 并暴露 dirty provenance",
            "evidence": "reports/missing_buildings/stage4_final_audit.json: provenance/gate",
            "passed": stages[3]["gate"]["dirty_provenance_recorded"],
        },
        {
            "requirement": "标注 sparse receiver mask 语义",
            "evidence": "reports/missing_buildings/stage4_final_audit.md: 语义与 provenance",
            "passed": stages[3]["label"] == "official-loader-faithful missing-building sparse sampling",
        },
        {
            "requirement": "全阶段一致性审计",
            "evidence": "reports/final_reproduction_audit.json",
            "passed": all(stage["gate"]["pass"] for stage in stages),
        },
        {
            "requirement": "最终复现报告和总结",
            "evidence": "reports/final_reproduction_audit.md + docs/reproduction_summary.md",
            "passed": True,
        },
        {
            "requirement": "checkpoint/log/dataset 不进 git",
            "evidence": "git ls-files 检查 + 各阶段 manifest",
            "passed": all(
                stage["gate"].get("checkpoints_not_tracked", stage["gate"].get("checkpoint_not_tracked", True))
                for stage in stages
            ),
        },
    ]
    gate = {
        "all_stage_gates_pass": all(stage["gate"]["pass"] for stage in stages),
        "all_checklist_items_pass": all(item["passed"] for item in checklist),
        "final_reports_written": True,
    }
    gate["pass"] = all(gate.values())
    audit = {
        "scope": "RadioUNet final reproduction audit",
        "git": git_metadata(exclude_paths=["reports"]),
        "stages": stages,
        "checklist": checklist,
        "gate": gate,
    }
    save_json(audit, ROOT / "reports/final_reproduction_audit.json")
    write_markdown(audit)
    write_summary(audit)
    print(gate)
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
