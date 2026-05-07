# Stage 2 fixed-100 audit

## 关键约束

- 固定目录：`reports/s_dpm_thr2/fix100_50ep`。
- 配置：`configs/s_dpm_thr2_fix100.yaml`，run copy 已保存。
- loader/simulation/threshold：`RadioUNet_s` / `DPM` / `0.2`。
- firstU/secondU epoch：`50` / `50`。
- fix_samples：`100`。
- metrics git dirty：`False`，exclude_paths：`['reports']`。
- checkpoint manifest：`firstU_checkpoint_manifest.json`、`secondU_checkpoint_manifest.json`；checkpoint 文件本地存在且未进 git：`True`。
- 预测图数量：`8`。
- eval rerun 最大差异：firstU `0.0`，secondU `0.0`。
- gate passed：`True`。

## secondU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0003137517 | 0.0074780237 | 0.0058542454 | 0.0177130366 | 1.4170429304 |

## firstU test metrics

| MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 0.0003916606 | 0.0092568709 | 0.0073079367 | 0.0197904171 | 1.5832333682 |

## sparse sample 审计

- 配置采样点数：`100`。
- test 抽检样本数：`120`。
- sparse channel 非零数量范围：`70..97`，均值 `85.79166666666667`。
- sparse 与 target 对齐最大绝对误差：`0.0`。
