# Stage 3C run manifest

- 配置：`configs/c_irt2_irt4_adapt.yaml`
- run dir：`reports/full_matrix/c_irt2_irt4_adapt_50ep`
- git commit：`68fe737d9db96db7468e77cb3e73bcbe7e2a2c9b`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`cae51f91c78b88673bd1e6de285563f98950cadf6800a6a9d4ccbac6c5ac0949`

## History / mask
- history entries：`100`
- loss modes：`['sparse_mse']`
- num_samples_for_loss：`[300]`
- mask 点数范围：`297..300`

## Gate
- `checkpoint_sha256_matches=True`
- `rerun_diff_zero=True`
- `figures_requested=True`
- `figures_nonempty=True`
- `sparse_history_recorded=True`
- `mask_distribution_recorded=True`
- `test_samples_recorded=True`
- `sparse_metrics_recorded=True`
- `pass=True`
