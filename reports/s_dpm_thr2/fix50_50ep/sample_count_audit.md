# Stage 2 fixed-50 audit

## 关键约束

- 固定目录：`reports/s_dpm_thr2/fix50_50ep`。
- 配置：`configs/s_dpm_thr2_fix50.yaml`，run copy 已保存。
- loader/simulation/threshold：`RadioUNet_s` / `DPM` / `0.2`。
- firstU/secondU epoch：`50` / `50`。
- fix_samples：`50`。
- metrics git dirty：`False`，exclude_paths：`['reports']`。
- checkpoint manifest：`firstU_checkpoint_manifest.json`、`secondU_checkpoint_manifest.json`；checkpoint 文件本地存在且未进 git：`True`。
- 预测图数量：`8`。
- eval rerun 最大差异：firstU `0.0`，secondU `0.0`。
- gate passed：`True`。

## secondU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0004045899 | 0.0095794999 | 0.0075491820 | 0.0201144196 | 1.6091535706 |

## firstU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0004785095 | 0.0112734726 | 0.0089284362 | 0.0218748589 | 1.7499887108 |

## sparse sample 审计

- 配置采样点数：`50`。
- test 抽检样本数：`120`。
- sparse channel 非零数量范围：`34..49`，均值 `42.78333333333333`。
- sparse 与 target 对齐最大绝对误差：`0.0`。
