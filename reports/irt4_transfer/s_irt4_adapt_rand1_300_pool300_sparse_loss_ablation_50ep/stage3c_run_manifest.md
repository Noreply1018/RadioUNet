# Stage 3C run manifest

- 配置：`configs/s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation.yaml`
- run dir：`reports/irt4_transfer/s_irt4_adapt_rand1_300_pool300_sparse_loss_ablation_50ep`
- git commit：`c5646069d20052ac90992019ff7f79a433d550f8`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`35e2739a25e003a921f4e8f842e7a2185e73ce1c9a25996f3b8a2fecad009d32`

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
