# Full Matrix 最终审计

## 结论
- final gate：`False`。
- 这次审计没有把缺失矩阵伪装为完成；所有未覆盖项均标为 blocking gap。
- 当前 git 状态（排除 reports）：dirty=`True`，commit=`98c674dbf97842c0a0902ecec7f0609a3475bcdd`。

## Prompt-to-artifact checklist
| 要求 | 证据 | 通过 | 缺口 |
| --- | --- | --- | --- |
| 1. Coarse simulation 全矩阵：DPM/IRT2/rand x C/S，50 epoch firstU+secondU，metrics/rerun/history/manifest/8图。 | 由 reports/full_matrix/coarse_simulation_audit.json 检查 DPM/IRT2/rand x C/S 的 metrics、rerun、history、manifest 和 8 张图。 | `True` | 无。 |
| 2. IRT4 transfer 全矩阵：source DPM/IRT2/rand x C/S x zero-shot/adapt。 | 由 reports/full_matrix/irt4_transfer_matrix.json 检查 12 个 zero-shot/adapt 单元、Tx 0/1、init checkpoint、sparse policy、rerun 和图。 | `True` | 无。 |
| 3. Cars 场景完整复现：DPM/IRT2/IRT4 cars、cars input、no-cars 对照。 | 由 reports/full_matrix/cars_audit.json 检查 cars target、cars input channel、metrics/rerun、manifest 和 qualitative figures。 | `False` | 未通过 run：s_irt2cars_carinput_thr2_rand1_300。 |
| 4. Missing buildings 全矩阵与 fixed receiver 对照。 | reports/full_matrix/missing_buildings_matrix.json 已区分 official-loader archived evidence、fixed receiver policy hash gate、DPM/IRT2/rand fixedrx configs 与 full-run 缺口。 | `False` | official-loader DPM rows are archived evidence but do not all satisfy clean full-matrix gate；缺全部 fixed receiver full runs/metrics/rerun/manifest |
| 5. Sample count 曲线与 state-of-the-art 对比：RadioUNet_S、RBF、TC、tomography、MLP、C baseline。 | 由 reports/full_matrix/state_of_art_comparison.json 检查 RBF、tensor-completion proxy、tomography proxy、one-step MLP proxy、RadioUNet_S reference 和 C baseline。 | `True` | 无。 |
| 6. WNet/model size/threshold 矩阵：size、with/without secondU、threshold、400/100/200 split。 | reports/full_matrix/wnet_size_threshold_audit.json 已检查 size 参数化、参数量、architecture hash、shape、threshold preprocessing 和 split overlap；full runs 尚未完成。 | `False` | 缺各 size/threshold/split 配置的 50 epoch full runs、metrics/rerun 和 qualitative figures。 |
| 7. 论文图表级汇总：paper_table_reproduction、Fig8/9/10、summary docs。 | 本脚本生成图表级汇总草案和现有子集图；由于上游矩阵缺口，final gate 仍失败。 | `True` | 图表只覆盖现有子集，不能代表论文全矩阵。 |

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

## 下一批必须执行的命令
1. 补 `python scripts/run_full_matrix_cars.py --run s_irt2cars_carinput_thr2_rand1_300 --device auto`。
2. 跑 missing buildings fixed receiver full runs，并补 IRT2/rand source missing matrix。
3. 补 model size、with/without secondU、threshold、400/100/200 split 矩阵。
4. 每批跑对应 audit 后重跑 `python scripts/audit_full_matrix_readiness.py`，直到 final gate 为 `True`。
