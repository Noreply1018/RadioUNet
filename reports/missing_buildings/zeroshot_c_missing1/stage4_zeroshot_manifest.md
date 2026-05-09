# Stage 4 missing-buildings zero-shot manifest

- 配置：`configs/c_irt4_missing1_sparse_loss.yaml`
- run dir：`reports/missing_buildings/zeroshot_c_missing1`
- missing_buildings：`1`
- result bucket：`zero-shot missing-building degradation`
- source checkpoint：`reports/c_dpm_thr2/20260506_182311/checkpoints/secondU.pt`
- source checkpoint sha256：`cd36e18b88c07309825a5d1f8a4dac32818681d434c3cf02de28d836e03d1e06`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`
- rerun 最大差异：`0.0`
- 图像数量：`8`，非空：`True`

## Gate
- `source_checkpoint_exists=True`
- `rerun_diff_zero=True`
- `figures_requested=True`
- `figures_nonempty=True`
- `test_samples_198=True`
- `sparse_metrics_recorded=True`
- `pass=True`
