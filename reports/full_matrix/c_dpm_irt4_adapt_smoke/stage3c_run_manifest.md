# Stage 3C run manifest

- 配置：`configs/c_dpm_irt4_adapt.yaml`
- run dir：`reports/full_matrix/c_dpm_irt4_adapt_smoke`
- git commit：`d273b26826ebc63f7bdac50bdd6b6903bfa4cd3f`
- git dirty：`False`
- smoke：`True`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`2`，非空：`True`
- checkpoint sha256：`3568b38a62f3a2677cd8db0a0a68c86410d8764f2099d796febfe4047258c55f`

## History / mask
- history entries：`2`
- loss modes：`['sparse_mse']`
- num_samples_for_loss：`[300]`
- mask 点数范围：`299..299`

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
