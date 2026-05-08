# Stage 2 fixed-300 audit

## 关键约束

- 固定目录：`reports/s_dpm_thr2/fix300_50ep`。
- 配置：`configs/s_dpm_thr2_fix300.yaml`，run copy 已保存。
- loader/simulation/threshold：`RadioUNet_s` / `DPM` / `0.2`。
- firstU/secondU epoch：`50` / `50`。
- fix_samples：`300`。
- metrics git dirty：`False`，exclude_paths：`['reports']`。
- checkpoint manifest：`firstU_checkpoint_manifest.json`、`secondU_checkpoint_manifest.json`；checkpoint 文件本地存在且未进 git：`True`。
- 预测图数量：`8`。
- eval rerun 最大差异：firstU `0.0`，secondU `0.0`。
- gate passed：`True`。

## secondU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0002526154 | 0.0060052292 | 0.0047135126 | 0.0158938788 | 1.2715103015 |

## firstU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0003050918 | 0.0072132220 | 0.0056926623 | 0.0174668773 | 1.3973501838 |

## sparse sample 审计

- 配置采样点数：`300`。
- test 抽检样本数：`120`。
- sparse channel 非零数量范围：`215..278`，均值 `255.99166666666667`。
- sparse 与 target 对齐最大绝对误差：`0.0`。
