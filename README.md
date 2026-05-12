# RadioUNet 核心实验可审计复现

本仓库完成了 RadioUNet 核心实验的可审计复现。最终结题口径为：

```text
RadioUNet 核心实验可审计复现
```

最终审计结果：

```text
reproduction gate: True
```

本项目已经完成核心实验链路、关键迁移实验、missing-building robustness 子集、state-of-the-art proxy 对比和论文图表级汇总。所有核心结论均配套 config、metrics、rerun metrics、manifest、图表和审计报告，能够从仓库内产物追踪到具体 run。

## 已完成内容

### Coarse simulation 全矩阵

已覆盖 RadioUNet_C / RadioUNet_S 在 clean map、no-cars 口径下的主要 coarse simulation 轴：

- DPM
- IRT2
- random coarse simulation
- C 模型 dense input
- S 模型 random 1..300 sparse measurement input

证据入口：

- `reports/full_matrix/coarse_simulation_audit.md`
- `reports/full_matrix/coarse_simulation_audit.json`

### IRT4 transfer 全矩阵

已覆盖 source coarse target、model 和 transfer setting 的核心组合：

- source：DPM、IRT2、random coarse simulation
- model：RadioUNet_C、RadioUNet_S
- setting：zero-shot IRT4、sparse adaptation to IRT4

证据入口：

- `reports/full_matrix/irt4_transfer_matrix.md`
- `reports/full_matrix/irt4_transfer_matrix.json`

### Missing buildings robustness

已完成 official-loader-faithful robustness 主线，覆盖 missing buildings 0/1/2/4，并归档 zero-shot/adaptation、rerun、manifest、loader audit 和 provenance 记录。

证据入口：

- `reports/missing_buildings/stage4_final_audit.md`
- `reports/missing_buildings/stage4_final_audit.json`

### State-of-the-art proxy 对比

已完成 sample count 曲线与 baseline proxy 对比：

- RadioUNet_S reference
- RadioUNet_C horizontal baseline
- RBF interpolation
- tensor-completion proxy
- tomography proxy
- one-step MLP proxy

传统 baseline 标记为 implementation-faithful proxy，结果可由 JSON 重新生成图表。

证据入口：

- `reports/full_matrix/state_of_art_comparison.md`
- `reports/full_matrix/state_of_art_comparison.json`
- `reports/full_matrix/state_of_art_comparison/state_of_art_comparison.png`

## 最终交付入口

优先阅读以下文件：

- `reports/full_matrix/final_full_matrix_audit.md`
- `reports/full_matrix/final_full_matrix_audit.json`
- `docs/full_matrix_reproduction_summary.md`
- `reports/full_matrix/paper_table_reproduction.md`
- `reports/full_matrix/paper_table_reproduction.json`

核心图表：

- `reports/full_matrix/fig8_radio_unet_performance.png`
- `reports/full_matrix/fig9_wnet_missing_buildings.png`
- `reports/full_matrix/fig10_state_of_art_comparison.png`

## 复验方式

运行最终审计：

```bash
python scripts/audit_full_matrix_readiness.py
```

预期输出：

```text
reproduction gate: True
saved: reports/full_matrix/final_full_matrix_audit.json
```

如需复验单项审计，可运行：

```bash
python scripts/audit_full_matrix_coarse.py
python scripts/audit_full_matrix_irt4.py
python scripts/audit_stage4_final.py
python scripts/audit_state_of_art_baselines.py
python scripts/audit_wnet_size_threshold.py
```

## 仓库结构

```text
configs/                 实验配置
src/radiounet/           数据加载、模型、指标和 baseline 实现
scripts/                 训练、评估、审计和图表生成入口
reports/                 可审计结果、metrics、manifest 和图表
docs/                    复现总结与阶段文档
reference/               参考资料与外部实现快照说明
```

## 数据与大文件

数据集和 checkpoint 不纳入 git。`.gitignore` 已排除本地数据、训练 checkpoint、缓存和常见大文件，仅保留可审计的 JSON、Markdown、PNG、YAML 报告产物。

典型数据目录：

```text
RadioMapSeer/
```

典型 checkpoint 产物位于各 run 目录的 `checkpoints/` 下，但不作为仓库提交内容。

## 后续扩展方向

以下内容已经形成 supporting/readiness 证据，可在后续继续扩展：

- cars 场景：在现有 cars 子集与 loader 审计基础上扩展更多 cars input 组合。
- fixed receiver missing：在 fixed receiver policy/config/smoke 证据基础上扩展 full runs。
- WNet/model size/threshold：在 readiness 与 smoke 证据基础上扩展 50 epoch 对比矩阵。

