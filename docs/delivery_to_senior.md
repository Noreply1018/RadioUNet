# RadioUNet 复现交付说明

这份文档是给师兄检查复现任务时的入口。仓库当前交付口径是“RadioUNet 核心实验可审计复现”，最终审计 gate 为 `True`。

## 建议交付内容

交付时建议直接给出整个仓库，并重点说明以下入口：

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| 总入口 | `README.md` | 仓库完成状态、复验方式、目录结构 |
| 交付说明 | `docs/delivery_to_senior.md` | 给师兄快速审阅的清单 |
| 最终审计 | `reports/full_matrix/final_full_matrix_audit.md` | 核心实验覆盖、gate、可复验状态 |
| 图表汇总 | `reports/full_matrix/paper_table_reproduction.md` | 论文 Fig8/Fig9/Fig10 复现图入口 |
| 简短总结 | `docs/full_matrix_reproduction_summary.md` | 一页式复现结论 |
| 机器可读结果 | `reports/full_matrix/*.json`、各 run 下 `*_metrics.json` | 指标、manifest、rerun 和 provenance |
| 核心图 | `reports/full_matrix/fig8_radio_unet_performance.png` | RadioUNet performance 核心子集 |
| 核心图 | `reports/full_matrix/fig9_wnet_missing_buildings.png` | missing buildings robustness 子集 |
| 核心图 | `reports/full_matrix/fig10_state_of_art_comparison.png` | state-of-the-art proxy 对比 |

## 已完成实验范围

- Coarse simulation 全矩阵：DPM、IRT2、random coarse simulation 下的 RadioUNet_C / RadioUNet_S 主线。
- IRT4 transfer 全矩阵：DPM、IRT2、random source 到 IRT4 的 zero-shot 和 sparse adaptation。
- Missing buildings robustness：official-loader-faithful 口径下 missing 0/1/2/4 子集。
- State-of-the-art proxy 对比：RadioUNet_S、RadioUNet_C、RBF、tensor-completion proxy、tomography proxy、one-step MLP proxy。
- 论文图表级汇总：已生成 Fig8/Fig9/Fig10 对应复现图，并在表格中标明 scope 和差异。

## 复验命令

只复验最终审计：

```bash
python scripts/audit_full_matrix_readiness.py
```

预期输出包含：

```text
reproduction gate: True
saved: reports/full_matrix/final_full_matrix_audit.json
```

复验单项审计：

```bash
python scripts/audit_full_matrix_coarse.py
python scripts/audit_full_matrix_irt4.py
python scripts/audit_stage4_final.py
python scripts/audit_state_of_art_baselines.py
python scripts/audit_wnet_size_threshold.py
```

如需重新训练一个典型 C/DPM baseline：

```bash
python scripts/train.py --config configs/c_dpm_thr2.yaml --phase both --epochs 50 --run-dir reports/c_dpm_thr2/recheck_50ep
```

如需重新评估 checkpoint：

```bash
python scripts/evaluate.py \
  --config configs/c_dpm_thr2.yaml \
  --checkpoint reports/c_dpm_thr2/recheck_50ep/checkpoints/secondU.pt \
  --split test \
  --output reports/c_dpm_thr2/recheck_50ep/secondU_test_metrics.json
```

如需重新生成可视化：

```bash
python scripts/make_figures.py \
  --config configs/c_dpm_thr2.yaml \
  --checkpoint reports/c_dpm_thr2/recheck_50ep/checkpoints/secondU.pt \
  --split test \
  --limit 8 \
  --output-dir reports/c_dpm_thr2/recheck_50ep/figures
```

## 数据和环境说明

数据集不随 git 提交，需要本地存在 RadioMapSeer 数据目录。典型配置项为：

```yaml
data:
  dataset_dir: RadioMapSeer/
```

Python 依赖见 `requirements.txt`。由于 PyTorch/CUDA 版本强依赖机器环境，建议按本机 CUDA 版本安装匹配的 `torch` 和 `torchvision`，再安装其余依赖。

## 结果解释口径

- `reproduction gate: True` 表示仓库内核心实验证据、metrics、rerun metrics、manifest、配置快照和图表入口完整。
- checkpoint 和原始数据集没有纳入 git；每个 run 目录下有 checkpoint manifest，用于记录 checkpoint 路径和 hash。
- 传统 baseline 标注为 `implementation-faithful proxy`，不是论文官方实现逐行复刻。
- Missing buildings 主线标注为 `official-loader-faithful`；fixed receiver missing 已作为 readiness/后续扩展方向归档。
- Cars、fixed receiver missing full runs、WNet/model size/threshold 50 epoch 全矩阵仍属于后续扩展，不影响当前核心复现 gate。

## 给师兄汇报时可以这样概括

本仓库已经完成 RadioUNet 核心实验的可审计复现：C/S coarse simulation、IRT4 transfer、missing buildings robustness 子集和 state-of-the-art proxy 对比均有配置、指标、复验指标、manifest、图和审计报告。最终 gate 为 `True`。主要差异是部分传统 baseline 采用 implementation-faithful proxy，missing buildings 固定 receiver 对照和 cars 全矩阵被归档为后续扩展。
