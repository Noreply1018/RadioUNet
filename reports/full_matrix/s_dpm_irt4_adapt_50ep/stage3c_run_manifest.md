# Stage 3C run manifest

- 配置：`configs/s_dpm_irt4_adapt.yaml`
- run dir：`reports/full_matrix/s_dpm_irt4_adapt_50ep`
- git commit：`171a9ac54012b4f01208f741a02ae39e754e50be`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`99e285f4ab4fdabf344ae5917e34e2bf5ee1efdfce9b4b3775827c5b53cfa951`

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
