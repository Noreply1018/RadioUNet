# RadioUNet 最终复现审计

## 总结
- 最终 gate：`True`。
- 当前源码状态（排除 reports）：dirty=`False`，commit=`b60f8b883733d801601d321363d32a2a8d4b10a9`。
- 本报告覆盖 Stage 1 C/DPM、Stage 2 S/DPM、Stage 3C IRT4 sparse adaptation、Stage 4 missing buildings robustness。
- checkpoint、dataset、cache 均不作为 git 交付物；报告、metrics、manifest、图和配置快照作为可审计交付物。

## Prompt-to-artifact checklist
| 要求 | 证据 | 通过 |
| --- | --- | --- |
| 完成 plan.md 的 Stage 4 审计漏洞修复 | scripts/audit_missing_buildings_loader.py + reports/missing_buildings/loader_audits/*.json | `True` |
| 收紧 final gate 并暴露 dirty provenance | reports/missing_buildings/stage4_final_audit.json: provenance/gate | `True` |
| 标注 sparse receiver mask 语义 | reports/missing_buildings/stage4_final_audit.md: 语义与 provenance | `True` |
| 全阶段一致性审计 | reports/final_reproduction_audit.json | `True` |
| 最终复现报告和总结 | reports/final_reproduction_audit.md + docs/reproduction_summary.md | `True` |
| checkpoint/log/dataset 不进 git | git ls-files 检查 + 各阶段 manifest | `True` |

## 阶段结论
### Stage 1 C DPM baseline
- 标签：`paper-faithful baseline`
- 论文主张：RadioUNet_C clean city-map DPM baseline with WNet firstU/secondU.
- 结论：MSE/RMSE 接近官方 notebook；NMSE 偏高但已解释为分母/数据口径敏感项。
- gate：`True`
### Stage 2 S DPM random 1..300
- 标签：`paper-faithful mainline plus ablations`
- 论文主张：Sparse measurements improve RadioUNet_S under DPM complete-map setting.
- 结论：random 1..300 主线优于 Stage 1 C baseline；fixed 50/100/200/300 仅作为 ablation。
- gate：`True`
### Stage 3C IRT4 sparse adaptation
- 标签：`paper-faithful mainline, dense-loss pilot, ablation`
- 论文主张：RadioUNet_S can adapt to high-fidelity IRT4 with sparse measurements.
- 结论：pool600、输入 1..300、sparse loss 主线成立；dense-loss pilot 已降级为非主线。
- gate：`True`
### Stage 4 missing buildings robustness
- 标签：`official-loader-faithful missing-building sparse sampling`
- 论文主张：Sparse measurements improve robustness when input city maps have missing buildings.
- 结论：0/1/2/4 missing sweep 完成；S sparse-adapted 优于 S zero-shot 和 C adapted，但 receiver mask 语义按官方 loader 标注。
- gate：`True`

## 覆盖与差距
- 已复现：clean DPM C baseline、DPM S random 1..300、IRT4 sparse adaptation、missing0/1/2/4 鲁棒性趋势。
- implementation-faithful：Stage 4 sparse receiver mask 由 missing building image seed 决定，因此标为 official-loader-faithful / implementation-faithful。
- ablation：Stage 2 fixed sample sweep、Stage 3C pool300 sparse ablation、Stage 3C dense-loss pilot。
- 未覆盖：cars 鲁棒性、IRT2/rand simulation 全矩阵、固定 receiver mask missing-building 对照、论文表格级完整排版。
- residual risk：Stage 4 历史 metrics/manifest 中记录了 dirty provenance；若用于最终投稿级 provenance，建议在当前 clean 源码上重跑 Stage 4 eval/audit/manifest，必要时重跑 adaptation。

## 当前最可信产物
- `docs/stage1_c_dpm_thr2_audit.md`
- `reports/s_dpm_thr2/stage2_final_audit.md`
- `reports/irt4_transfer/stage3c_final_audit.md`
- `reports/missing_buildings/stage4_final_audit.md`
- `reports/final_reproduction_audit.json`
