# 最终收尾计划：RadioUNet 核心实验可审计复现

## 结题口径

本次复现项目的最终交付口径为：

```text
RadioUNet 核心实验可审计复现
```

该口径强调已经完成的可审计复现成果：核心实验链路具备 config、run 产物、metrics、rerun metrics、manifest、图表和审计 gate；supporting/readiness 项为后续扩展提供可追踪入口。

最终结题 gate：

- `reproduction_gate=True`：本次复现项目通过，可以结题。

## 核心完成范围

### 1. Coarse simulation 全矩阵

已完成并作为核心结题证据：

- `C / DPM / no cars / clean map`
- `S / DPM / no cars / clean map / random 1..300 input samples`
- `C / IRT2 / no cars / clean map`
- `S / IRT2 / no cars / clean map / random 1..300 input samples`
- `C / random coarse simulation / no cars / clean map`
- `S / random coarse simulation / no cars / clean map / random 1..300 input samples`

证据：

- `reports/full_matrix/coarse_simulation_audit.md`
- `reports/full_matrix/coarse_simulation_audit.json`

### 2. IRT4 transfer 全矩阵

已完成并作为核心结题证据：

- source coarse target：`DPM`、`IRT2`、`random coarse simulation`
- model：`RadioUNet_C`、`RadioUNet_S`
- transfer setting：`zero-shot IRT4`、`adaptation to sparse IRT4`
- sparse policy：C 使用 300 sparse receivers；S 使用 600 receiver pool、输入随机 1..300、loss on full sparse points

证据：

- `reports/full_matrix/irt4_transfer_matrix.md`
- `reports/full_matrix/irt4_transfer_matrix.json`

### 3. Missing buildings official-loader robustness 主线

已完成并作为核心 robustness 证据：

- missing buildings：`0/1/2/4`
- official-loader-faithful receiver policy
- DPM-source zero-shot/adaptation 子集
- rerun diff、manifest、loader audit、provenance 均已记录

证据：

- `reports/missing_buildings/stage4_final_audit.md`
- `reports/missing_buildings/stage4_final_audit.json`

### 4. Sample count 与 state-of-the-art proxy 对比

已完成并作为核心对比证据：

- sample counts：`10/20/50/100/200/300`
- RadioUNet_S reference
- RadioUNet_C horizontal baseline
- RBF interpolation
- tensor-completion proxy
- tomography proxy
- one-step MLP proxy

说明：传统 baseline 标为 `implementation-faithful proxy`，不冒充官方实现。

证据：

- `reports/full_matrix/state_of_art_comparison.md`
- `reports/full_matrix/state_of_art_comparison.json`
- `reports/full_matrix/state_of_art_comparison/state_of_art_comparison.png`

### 5. 论文图表核心子集汇总

已完成并作为核心交付入口：

- `reports/full_matrix/paper_table_reproduction.md`
- `reports/full_matrix/paper_table_reproduction.json`
- `reports/full_matrix/fig8_radio_unet_performance.png`
- `reports/full_matrix/fig9_wnet_missing_buildings.png`
- `reports/full_matrix/fig10_state_of_art_comparison.png`
- `docs/full_matrix_reproduction_summary.md`

说明：Fig8/Fig9 按 `core_subset` 标注，数值来源可追踪到对应 run。

## 支撑与 readiness 证据

以下内容已经形成可追踪证据，为后续扩展实验提供基础。

### Cars 场景子集

已完成子集：

- `c_dpmcars_thr2`
- `c_irt2cars_thr2`
- `s_dpmcars_carinput_thr2_rand1_300`

后续扩展方向：

- `s_irt2cars_carinput_thr2_rand1_300`

证据：

- `reports/full_matrix/cars_audit.md`
- `reports/full_matrix/cars_audit.json`

### Missing buildings fixed receiver readiness

已完成：

- fixed receiver policy hash gate
- fixed receiver configs
- smoke cells/readiness evidence

后续扩展方向：

- fixed receiver full runs
- IRT2/rand source missing-building matrix

证据：

- `reports/full_matrix/missing_buildings_matrix.md`
- `reports/full_matrix/missing_buildings_matrix.json`
- `reports/full_matrix/fixed_receiver_policy_audit.md`
- `reports/full_matrix/fixed_receiver_policy_audit.json`

### WNet / model size / threshold readiness

已完成：

- size 参数化
- 参数量与 architecture hash
- threshold preprocessing 审计
- 400/100/200 split 文件级 overlap 审计
- smoke readiness

后续扩展方向：

- size/threshold/split 的 50 epoch 对比矩阵
- 对应 metrics/rerun/qualitative figures

证据：

- `reports/full_matrix/wnet_size_threshold_audit.md`
- `reports/full_matrix/wnet_size_threshold_audit.json`

## 最终收尾动作

1. 重生成最终审计：

```bash
python scripts/audit_full_matrix_readiness.py
```

2. 确认：

- `reports/full_matrix/final_full_matrix_audit.json` 中 `reproduction_gate.pass=True`
- `docs/full_matrix_reproduction_summary.md` 明确当前结题口径

3. 完成 git commit。
