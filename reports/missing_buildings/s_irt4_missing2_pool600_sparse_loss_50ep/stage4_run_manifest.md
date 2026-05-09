# Stage 4 missing-buildings run manifest

- 配置：`configs/s_irt4_missing2_pool600_sparse_loss.yaml`
- run dir：`reports/missing_buildings/s_irt4_missing2_pool600_sparse_loss_50ep`
- missing_buildings：`2`
- result bucket：`sparse-adapted missing-building robustness`
- git commit：`d76d6a4052137efbf84f394e451533826135ce06`
- git dirty：`True`
- smoke：`False`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`
- checkpoint sha256：`4646747410ed47e68508520b9b28a794fc419518dc88077639aa59038426bf4e`

## History / mask
- history entries：`100`
- loss modes：`['sparse_mse']`
- num_samples_for_loss：`[600]`
- mask 点数范围：`591..600`

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
