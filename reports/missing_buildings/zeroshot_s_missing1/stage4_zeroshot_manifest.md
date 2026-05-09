# Stage 4 missing-buildings zero-shot manifest

- 配置：`configs/s_irt4_missing1_pool600_sparse_loss.yaml`
- run dir：`reports/missing_buildings/zeroshot_s_missing1`
- missing_buildings：`1`
- result bucket：`zero-shot missing-building degradation`
- source checkpoint：`reports/s_dpm_thr2/rand1_300_50ep/checkpoints/secondU.pt`
- source checkpoint sha256：`c0b00df604ab5c8b9c773ca8dafead8f76a74e0fcb330a7fd79f9adf678ef4bc`
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
