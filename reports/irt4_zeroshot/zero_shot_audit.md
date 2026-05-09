# Stage 3A IRT4 zero-shot transfer audit

## 范围
- 目标：不训练新模型，用 DPM 训练得到的 Stage 1/2 checkpoint 直接评估 IRT4 test target。
- IRT4 Tx 限制：所有配置都固定 `num_tx=2`，test split 为 99 张 map x 2 Tx = `198` 个样本。
- 本报告只讨论 IRT4 test 指标，不把 DPM 指标混进结论。

## 结果
| run | source | samples | secondU MSE | secondU NMSE | global NMSE | RMSE | dB RMSE | rerun diff |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| c_baseline | Stage 1 C secondU DPM checkpoint | 198 | 0.0014888853 | 0.0304327418 | 0.0287934302 | 0.0385860765 | 3.0868861175 | 0.0 |
| s_rand1_300 | Stage 2 S random 1..300 secondU DPM checkpoint | 198 | 0.0009654228 | 0.0196769458 | 0.0186702326 | 0.0310712540 | 2.4857003215 | 0.0 |

## Loader / artifact gate
- `c_baseline`：loader `RadioUNet_c_sprseIRT4`，simulation `IRT4`，split 样本数 `{'train': 1002, 'val': 200, 'test': 198}`。
- `c_baseline`：metrics `git.dirty=False`，checkpoint 进 git：`False`，图像数量 `8`。
- `s_rand1_300`：loader `RadioUNet_s_sprseIRT4`，simulation `IRT4`，split 样本数 `{'train': 1002, 'val': 200, 'test': 198}`。
- `s_rand1_300`：metrics `git.dirty=False`，checkpoint 进 git：`False`，图像数量 `8`。

## Gate：`True`
- `test_samples_198=True`
- `metrics_git_dirty_false=True`
- `rerun_diff_zero=True`
- `checkpoint_not_tracked=True`
- `figures_8_each=True`
