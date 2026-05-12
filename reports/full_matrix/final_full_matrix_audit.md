# 核心实验可审计复现最终审计

## 结论
- core reproduction gate：`True`。
- full paper matrix gate：`False`。
- 本次收尾不再声称论文全矩阵完整复现；cars、fixed receiver missing matrix、WNet size/threshold full runs 均作为扩展缺口保留。
- 当前 git 状态（排除 reports）：dirty=`True`，commit=`55e3da8a377181c65e2eb596437c4db7469c5bea`。

## Scope-to-artifact checklist
| scope | 要求 | 证据 | 通过 | 缺口 |
| --- | --- | --- | --- | --- |
| `core` | 1. Coarse simulation 全矩阵：DPM/IRT2/rand x C/S，50 epoch firstU+secondU，metrics/rerun/history/manifest/8图。 | 由 reports/full_matrix/coarse_simulation_audit.json 检查 DPM/IRT2/rand x C/S 的 metrics、rerun、history、manifest 和 8 张图。 | `True` | 无。 |
| `core` | 2. IRT4 transfer 全矩阵：source DPM/IRT2/rand x C/S x zero-shot/adapt。 | 由 reports/full_matrix/irt4_transfer_matrix.json 检查 12 个 zero-shot/adapt 单元、Tx 0/1、init checkpoint、sparse policy、rerun 和图。 | `True` | 无。 |
| `extension` | 3. Cars 场景扩展证据：DPM/IRT2 cars、cars input、no-cars 对照。 | reports/full_matrix/cars_audit.json 已检查 cars target、cars input channel、metrics/rerun、manifest 和 qualitative figures；未完成项不阻塞核心结题。 | `False` | 扩展缺口：未通过 run：s_irt2cars_carinput_thr2_rand1_300。 |
| `core` | 4a. Missing buildings official-loader robustness 主线。 | reports/missing_buildings/stage4_final_audit.json 检查 missing 0/1/2/4、zero-shot/adapt、rerun、manifest、loader audit 和 dirty provenance residual risk。 | `True` | 无。 |
| `extension` | 4b. Missing buildings fixed receiver 全矩阵与 IRT2/rand source 对照。 | reports/full_matrix/missing_buildings_matrix.json 已区分 official-loader archived evidence、fixed receiver policy hash gate、DPM/IRT2/rand fixedrx configs 与 full-run 缺口。 | `False` | 扩展缺口：official-loader DPM rows are archived evidence but do not all satisfy clean full-matrix gate；缺全部 fixed receiver full runs/metrics/rerun/manifest |
| `core` | 5. Sample count 曲线与 state-of-the-art 对比：RadioUNet_S、RBF、TC、tomography、MLP、C baseline。 | 由 reports/full_matrix/state_of_art_comparison.json 检查 RBF、tensor-completion proxy、tomography proxy、one-step MLP proxy、RadioUNet_S reference 和 C baseline。 | `True` | 无。 |
| `extension` | 6. WNet/model size/threshold readiness 审计。 | reports/full_matrix/wnet_size_threshold_audit.json 已检查 size 参数化、参数量、architecture hash、shape、threshold preprocessing、split overlap 和 smoke；full runs 不纳入核心结题。 | `True` | 扩展缺口：缺各 size/threshold/split 配置的 50 epoch full runs、metrics/rerun 和 qualitative figures。 |
| `core` | 7. 论文图表级核心子集汇总：paper_table_reproduction、Fig8/9/10、summary docs。 | 本脚本生成图表级汇总和现有子集图；Fig8/Fig9 按 subset reproduction 标注 residual risk。 | `True` | 无；图表按核心子集口径交付，不声明论文全矩阵完成。 |

## 新增配置 gate
| config | gate |
| --- | ---: |
| `c_dpm_irt4_adapt` | `True` |
| `c_dpm_irt4_missing0_fixedrx_adapt` | `True` |
| `c_dpm_irt4_missing1_fixedrx_adapt` | `True` |
| `c_dpm_irt4_missing2_fixedrx_adapt` | `True` |
| `c_dpm_irt4_missing4_fixedrx_adapt` | `True` |
| `c_dpm_irt4_zeroshot` | `True` |
| `c_dpmcars_thr2` | `True` |
| `c_irt2_irt4_adapt` | `True` |
| `c_irt2_irt4_zeroshot` | `True` |
| `c_irt2_thr2` | `True` |
| `c_irt2cars_thr2` | `True` |
| `c_rand_irt4_adapt` | `True` |
| `c_rand_irt4_zeroshot` | `True` |
| `c_rand_thr2` | `True` |
| `s_dpm_irt4_adapt` | `True` |
| `s_dpm_irt4_missing0_fixedrx_adapt` | `True` |
| `s_dpm_irt4_missing1_fixedrx_adapt` | `True` |
| `s_dpm_irt4_missing2_fixedrx_adapt` | `True` |
| `s_dpm_irt4_missing4_fixedrx_adapt` | `True` |
| `s_dpm_irt4_zeroshot` | `True` |
| `s_dpmcars_carinput_thr2_rand1_300` | `True` |
| `s_irt2_irt4_adapt` | `True` |
| `s_irt2_irt4_zeroshot` | `True` |
| `s_irt2_thr2_rand1_300` | `True` |
| `s_irt2cars_carinput_thr2_rand1_300` | `True` |
| `s_rand_irt4_adapt` | `True` |
| `s_rand_irt4_zeroshot` | `True` |
| `s_rand_thr2_rand1_300` | `True` |

## 已有 run 可复验状态
| run | metrics | samples | rerun diff | gate |
| --- | --- | ---: | ---: | ---: |
| `c_dpm_clean` | `reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `c_irt2_full_matrix` | `reports/full_matrix/c_irt2_thr2_50ep/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `c_irt4_dpm_adapt` | `reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing0_zeroshot` | `reports/missing_buildings/zeroshot_c_missing0/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing1_adapt` | `reports/missing_buildings/c_irt4_missing1_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing1_zeroshot` | `reports/missing_buildings/zeroshot_c_missing1/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing2_adapt` | `reports/missing_buildings/c_irt4_missing2_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing2_zeroshot` | `reports/missing_buildings/zeroshot_c_missing2/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing4_adapt` | `reports/missing_buildings/c_irt4_missing4_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `c_irt4_missing4_zeroshot` | `reports/missing_buildings/zeroshot_c_missing4/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `s_dpm_fixed100` | `reports/s_dpm_thr2/fix100_50ep/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `s_dpm_fixed300` | `reports/s_dpm_thr2/fix300_50ep/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `s_dpm_fixed50` | `reports/s_dpm_thr2/fix50_50ep/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `s_dpm_rand10_300` | `reports/s_dpm_thr2/rand10_300_50ep/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `s_dpm_rand1_300` | `reports/s_dpm_thr2/rand1_300_50ep/secondU_test_metrics.json` | 7920 | 0.0 | `True` |
| `s_irt4_dpm_adapt_pool600` | `reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing0_zeroshot` | `reports/missing_buildings/zeroshot_s_missing0/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing1_adapt` | `reports/missing_buildings/s_irt4_missing1_pool600_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing1_zeroshot` | `reports/missing_buildings/zeroshot_s_missing1/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing2_adapt` | `reports/missing_buildings/s_irt4_missing2_pool600_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing2_zeroshot` | `reports/missing_buildings/zeroshot_s_missing2/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing4_adapt` | `reports/missing_buildings/s_irt4_missing4_pool600_sparse_loss_50ep/secondU_test_metrics.json` | 198 | 0.0 | `True` |
| `s_irt4_missing4_zeroshot` | `reports/missing_buildings/zeroshot_s_missing4/zeroshot_test_metrics.json` | 198 | 0.0 | `True` |

## 扩展缺口
- Cars：`s_irt2cars_carinput_thr2_rand1_300` 未跑 full run；现有 cars 证据保留为扩展子集。
- Missing buildings：fixed receiver policy/config/smoke 已审计，但 24 个 fixed receiver full runs 不纳入本次核心结题。
- WNet/model size/threshold：readiness 与 smoke 已审计，50 epoch full matrix 不纳入本次核心结题。
- 因上述范围调整，`full_paper_matrix_gate` 保持 `False` 是预期结果，不阻塞本项目收尾。
