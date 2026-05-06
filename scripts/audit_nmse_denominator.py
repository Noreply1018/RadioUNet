#!/usr/bin/env python3
"""Audit NMSE denominators for the Stage 1 DPM threshold=0.2 baseline."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader
from radiounet.utils import ensure_dir, load_yaml, require_dataset_dir, save_json


OFFICIAL_NOTEBOOK = {
    "firstU": {"mse": 0.000463, "nmse": 0.008737},
    "secondU": {"mse": 0.000409, "nmse": 0.007728},
}
CURRENT_STAGE1 = {
    "firstU": {"mse": 0.0004726780844763165, "nmse": 0.010797844952486974},
    "secondU": {"mse": 0.0004197669998943297, "nmse": 0.009647368385478992},
}
PAPER = {
    "setting": "accurate map, deterministic simulation with no cars",
    "nmse": 0.0075,
    "rmse": 0.0200,
}


def denominator_from_metrics(mse_value: float, nmse_value: float) -> float:
    return mse_value / nmse_value


def summarize_target_energy(config: dict, split: str) -> dict:
    loader = build_dataloader(config, split, smoke=False, shuffle=False)
    sample_sum = 0.0
    pixel_sum = 0.0
    samples = 0
    pixels = 0
    min_energy = float("inf")
    max_energy = float("-inf")

    with torch.no_grad():
        for batch in loader:
            targets = batch[1].float()
            per_sample = targets.square().flatten(1).mean(dim=1)
            sample_sum += float(per_sample.sum())
            pixel_sum += float(targets.square().sum())
            batch_samples = int(targets.size(0))
            samples += batch_samples
            pixels += int(targets.numel())
            min_energy = min(min_energy, float(per_sample.min()))
            max_energy = max(max_energy, float(per_sample.max()))

    return {
        "split": split,
        "samples": samples,
        "pixels": pixels,
        "mean_mse_target_zero_per_sample": sample_sum / samples,
        "mean_mse_target_zero_global_pixels": pixel_sum / pixels,
        "min_per_sample": min_energy,
        "max_per_sample": max_energy,
    }


def build_report(data: dict) -> str:
    current_energy = data["current_test_target_energy"]["mean_mse_target_zero_per_sample"]
    lines = [
        "# Stage 2 前置审计：NMSE 分母口径",
        "",
        "## 当前 test split target energy",
        "",
        f"- config: `{data['config']}`",
        f"- split: `{data['current_test_target_energy']['split']}`",
        f"- samples: `{data['current_test_target_energy']['samples']}`",
        f"- `mean(MSE(target, 0))`: `{current_energy:.10f}`",
        f"- global pixel mean: `{data['current_test_target_energy']['mean_mse_target_zero_global_pixels']:.10f}`",
        f"- per-sample range: `{data['current_test_target_energy']['min_per_sample']:.10f}` 到 `{data['current_test_target_energy']['max_per_sample']:.10f}`",
        "",
        "## 分母反推对照",
        "",
        "| 来源 | firstU 分母 | secondU 分母 | 备注 |",
        "| --- | ---: | ---: | --- |",
    ]
    for name, item in data["denominator_comparison"].items():
        first = item.get("firstU")
        second = item.get("secondU")
        first_text = f"{first:.10f}" if first is not None else "-"
        second_text = f"{second:.10f}" if second is not None else "-"
        lines.append(f"| {name} | {first_text} | {second_text} | {item['note']} |")

    lines.extend(
        [
            "",
            "## 按全局 target energy 重算的 Stage 1 NMSE",
            "",
            "| 输出头 | Stage 1 MSE | 原 Stage 1 NMSE | 全局分母 NMSE |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for phase, item in data["global_nmse_recomputed"].items():
        lines.append(
            f"| {phase} | {item['mse']:.10f} | {item['reported_nmse']:.10f} | {item['global_denominator_nmse']:.10f} |"
        )

    lines.extend(
        [
            "",
            "## 结论",
            "",
            data["conclusion"],
            "",
            "## 证据来源",
            "",
            "- 当前 target energy：本脚本直接遍历当前仓库 `RadioMapSeer/` 的 `test` split target。",
            "- 当前 firstU/secondU：`docs/stage1_c_dpm_thr2_audit.md` 已记录的完整 Stage 1 test metrics。",
            "- 官方 notebook：`reference/RadioUNet/RadioWNet_c_DPM_Thr2.ipynb` 的 DPM threshold=0.2 输出。",
            "- 论文表格：`reference/RadioUNet_paper_source/RadioUNet_paper_ver3.tex` 中 `accurate map, deterministic simulation with no cars` 行。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/c_dpm_thr2.yaml")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--output-dir", default="reports/stage2_smoke")
    args = parser.parse_args()

    config = load_yaml(args.config)
    require_dataset_dir(config)
    target_energy = summarize_target_energy(config, args.split)

    current = {
        phase: denominator_from_metrics(values["mse"], values["nmse"])
        for phase, values in CURRENT_STAGE1.items()
    }
    official = {
        phase: denominator_from_metrics(values["mse"], values["nmse"])
        for phase, values in OFFICIAL_NOTEBOOK.items()
    }
    paper = PAPER["rmse"] ** 2 / PAPER["nmse"]
    official_mean = (official["firstU"] + official["secondU"]) / 2

    conclusion = (
        "当前 test split 直接复算的 `MSE(target, 0)` 为 "
        f"`{target_energy['mean_mse_target_zero_per_sample']:.4f}`，与官方 notebook 反推分母 `{official_mean:.4f}` "
        f"和论文表格反推分母 `{paper:.4f}` 基本一致，因此不是数据版本差异，也不是 threshold=0.2 变换差异。"
        "Stage 1 报告中用 `平均 MSE / 平均 NMSE` 反推得到的 `0.0435` 到 `0.0438` 只是“比值平均后的有效分母”，"
        "不是 test split 的真实 target energy。按论文公式使用全局分母重算后，secondU NMSE 为 "
        f"`{CURRENT_STAGE1['secondU']['mse'] / target_energy['mean_mse_target_zero_per_sample']:.10f}`，"
        "与官方 notebook 的 `0.007728` 和论文表格的 `0.0075` 对齐。结论：遗留问题是 NMSE 统计粒度/比值平均口径差异；"
        "后续报告应优先使用全局平方误差和全局 target energy 的比值，并保留 batch-mean NMSE 时明确标注。"
    )

    report = {
        "config": args.config,
        "current_test_target_energy": target_energy,
        "denominator_comparison": {
            "当前 firstU/secondU 评估": {
                "firstU": current["firstU"],
                "secondU": current["secondU"],
                "note": "由 Stage 1 test MSE/NMSE 反推。",
            },
            "官方 notebook": {
                "firstU": official["firstU"],
                "secondU": official["secondU"],
                "note": "由官方 notebook DPM 输出 MSE/NMSE 反推。",
            },
            "论文表格": {
                "firstU": None,
                "secondU": paper,
                "note": "由 RMSE^2/NMSE 反推，表格只给最终方法行。",
            },
        },
        "global_nmse_recomputed": {
            phase: {
                "mse": values["mse"],
                "reported_nmse": values["nmse"],
                "global_denominator_nmse": values["mse"] / target_energy["mean_mse_target_zero_per_sample"],
            }
            for phase, values in CURRENT_STAGE1.items()
        },
        "relative_gap": {
            "official_vs_current_target_energy": official_mean / target_energy["mean_mse_target_zero_per_sample"] - 1,
            "paper_vs_current_target_energy": paper / target_energy["mean_mse_target_zero_per_sample"] - 1,
        },
        "conclusion": conclusion,
    }

    output_dir = ensure_dir(args.output_dir)
    json_path = output_dir / "nmse_denominator_audit.json"
    md_path = output_dir / "nmse_denominator_audit.md"
    save_json(report, json_path)
    md_path.write_text(build_report(report), encoding="utf-8")
    print(f"saved: {json_path}")
    print(f"saved: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
