# Stage 3C run manifest

- 配置：`configs/c_dpm_irt4_adapt.yaml`
- run dir：`reports/full_matrix/c_dpm_irt4_adapt_50ep`
- git commit：`116e810ee039b559304896d56622f73a845a2ae0`
- git dirty：`False`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`5e161345b74f246a82484c7ac26e5e1f744ebd8f9d6790c8236003129fc587cd`

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
