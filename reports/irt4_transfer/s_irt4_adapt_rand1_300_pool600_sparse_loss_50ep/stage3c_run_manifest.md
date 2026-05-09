# Stage 3C run manifest

- 配置：`configs/s_irt4_adapt_rand1_300_pool600_sparse_loss.yaml`
- run dir：`reports/irt4_transfer/s_irt4_adapt_rand1_300_pool600_sparse_loss_50ep`
- git commit：`8787a4f84b7d6559f028604fa22a2b0b73c702fb`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`a085e2e126bc49a03e9ef7b92c25dcd841005d8857c4f34b92d461f75effb94e`

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
