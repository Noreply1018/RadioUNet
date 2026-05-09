# Stage 3C run manifest

- 配置：`configs/c_irt4_adapt_sparse_loss.yaml`
- run dir：`reports/irt4_transfer/c_irt4_adapt_sparse_loss_50ep`
- git commit：`f83dd4160c48dd1ca25709b587d23fc78fc32933`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`7de3625d6491ea14321b8c24d423f0b05e5257e14d06e91b85e1ead6d6b1d49c`

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
