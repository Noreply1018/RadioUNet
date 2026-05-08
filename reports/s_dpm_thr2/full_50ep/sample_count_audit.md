# Stage 2 fixed-200 audit

## 关键约束

- 固定目录：`reports/s_dpm_thr2/full_50ep`。
- 配置：`configs/s_dpm_thr2.yaml`，run copy 已保存。
- loader/simulation/threshold：`RadioUNet_s` / `DPM` / `0.2`。
- firstU/secondU epoch：`50` / `50`。
- fix_samples：`200`。
- metrics git dirty：`False`，exclude_paths：`['reports']`。
- checkpoint manifest：`firstU_checkpoint_manifest.json`、`secondU_checkpoint_manifest.json`；checkpoint 文件本地存在且未进 git：`True`。
- 预测图数量：`8`。
- eval rerun 最大差异：firstU `0.0`，secondU `0.0`。
- gate passed：`True`。

## secondU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0002553442 | 0.0060987900 | 0.0047644284 | 0.0159794918 | 1.2783593414 |

## firstU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0003268413 | 0.0077409654 | 0.0060984833 | 0.0180787533 | 1.4463002601 |

## sparse sample 审计

- 配置采样点数：`200`。
- test 抽检样本数：`120`。
- sparse channel 非零数量范围：`147..187`，均值 `171.025`。
- sparse 与 target 对齐最大绝对误差：`0.0`。
