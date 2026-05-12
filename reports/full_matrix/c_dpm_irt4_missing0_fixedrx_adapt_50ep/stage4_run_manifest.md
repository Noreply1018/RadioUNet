# Stage 4 missing-buildings run manifest

- 配置：`configs/c_dpm_irt4_missing0_fixedrx_adapt.yaml`
- run dir：`reports/full_matrix/c_dpm_irt4_missing0_fixedrx_adapt_50ep`
- missing_buildings：`0`
- result bucket：`None`
- git commit：`55e3da8a377181c65e2eb596437c4db7469c5bea`
- git dirty：`True`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`cf4a4c334daf9acad672c856072e377c6f7b96ced9c8aaff8a63c7f31f2a83fb`

## History / mask
- history entries：`100`
- loss modes：`['sparse_mse']`
- num_samples_for_loss：`[300]`
- mask 点数范围：`295..300`

## Gate
- `checkpoint_sha256_matches=True`
- `rerun_diff_zero=True`
- `figures_requested=True`
- `figures_nonempty=True`
- `sparse_history_recorded=True`
- `mask_distribution_recorded=True`
- `test_samples_198=True`
- `sparse_metrics_recorded=True`
- `pass=True`
