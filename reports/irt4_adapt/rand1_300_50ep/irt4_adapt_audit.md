# Stage 3B IRT4 sparse adaptation audit

## 范围
- 训练模式：`secondU-only adaptation`。
- 初始化 checkpoint：`reports/s_dpm_thr2/rand1_300_50ep/checkpoints/firstU.pt`。
- target/input samples：IRT4；所有 split 固定 `num_tx=2`。
- 本报告只比较 IRT4 test 指标，不混用 DPM 指标。

## 样本数
- train/val/test：`{'train': 1002, 'val': 200, 'test': 198}`。

## IRT4 对比
| run | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 1 C zero-shot | 0.0014888853 | 0.0304327418 | 0.0287934302 | 0.0385860765 | 3.0868861175 |
| Stage 2 S zero-shot | 0.0009654228 | 0.0196769458 | 0.0186702326 | 0.0310712540 | 2.4857003215 |
| Stage 3 S adaptation | 0.0007365961 | 0.0151911565 | 0.0142449718 | 0.0271403045 | 2.1712243563 |

## 训练和 artifact
- secondU history：train entries `50`，val entries `50`，best val loss `43.63565683364868`。
- test samples `198`；rerun diff `0.0`；metrics `git.dirty=False`。
- checkpoint 进 git：`False`；sha256 匹配：`True`。
- prediction/error 图数量：`8`。

## Gate：`True`
- `mode_secondU_only_adaptation=True`
- `train_val_test_samples=True`
- `history_50_train_and_val_entries=True`
- `test_samples_198=True`
- `metrics_git_dirty_false=True`
- `rerun_diff_zero=True`
- `checkpoint_not_tracked=True`
- `figures_8=True`
