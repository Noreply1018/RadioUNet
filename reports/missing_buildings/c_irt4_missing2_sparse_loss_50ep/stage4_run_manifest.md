# Stage 4 missing-buildings run manifest

- 配置：`configs/c_irt4_missing2_sparse_loss.yaml`
- run dir：`reports/missing_buildings/c_irt4_missing2_sparse_loss_50ep`
- missing_buildings：`2`
- result bucket：`C baseline`
- git commit：`d76d6a4052137efbf84f394e451533826135ce06`
- git dirty：`True`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`12aed675dc9e57a9e46fc60a93f1b703a9fd6f8226cffc702b305a71a5862013`

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
