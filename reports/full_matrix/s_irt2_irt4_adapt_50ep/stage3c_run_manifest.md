# Stage 3C run manifest

- 配置：`configs/s_irt2_irt4_adapt.yaml`
- run dir：`reports/full_matrix/s_irt2_irt4_adapt_50ep`
- git commit：`68fe737d9db96db7468e77cb3e73bcbe7e2a2c9b`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`dcc74deffca02931134cea6999f3e69757112335ce2be8df61ab5d47b15bfc28`

## History / mask
- history entries：`100`
- loss modes：`['sparse_mse']`
- num_samples_for_loss：`[600]`
- mask 点数范围：`590..600`

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
