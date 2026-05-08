# Stage 2 sparse sample count sweep audit

## 范围

- 配置：RadioUNet_S / DPM / threshold=0.2 / firstU 50 epoch / secondU 50 epoch。
- 样本数：50、100、200、300；其中 200 复用已完成的 `reports/s_dpm_thr2/full_50ep`，未重复训练。
- 每个点包含 test eval、rerun eval、8 张预测图、checkpoint manifest 和单独 audit。

## secondU 指标曲线表

| fix_samples | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.0004045899 | 0.0095794999 | 0.0075491820 | 0.0201144196 | 1.6091535706 |
| 100 | 0.0003137517 | 0.0074780237 | 0.0058542454 | 0.0177130366 | 1.4170429304 |
| 200 | 0.0002553442 | 0.0060987900 | 0.0047644284 | 0.0159794918 | 1.2783593414 |
| 300 | 0.0002526154 | 0.0060052292 | 0.0047135126 | 0.0158938788 | 1.2715103015 |

## firstU 指标曲线表

| fix_samples | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.0004785095 | 0.0112734726 | 0.0089284362 | 0.0218748589 | 1.7499887108 |
| 100 | 0.0003916606 | 0.0092568709 | 0.0073079367 | 0.0197904171 | 1.5832333682 |
| 200 | 0.0003268413 | 0.0077409654 | 0.0060984833 | 0.0180787533 | 1.4463002601 |
| 300 | 0.0003050918 | 0.0072132220 | 0.0056926623 | 0.0174668773 | 1.3973501838 |

## 相比 Stage 1 C baseline 的 secondU 收益

| fix_samples | MSE 降低 | MSE 降低比例 | NMSE 降低 | NMSE 降低比例 | global NMSE 降低 | global NMSE 降低比例 | dB RMSE 降低 | dB RMSE 降低比例 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.0000151772 | 3.62% | 0.0000678684 | 0.70% | 0.0001786538 | 2.31% | 0.0299038141 | 1.82% |
| 100 | 0.0001060154 | 25.26% | 0.0021693447 | 22.49% | 0.0018735904 | 24.24% | 0.2220144542 | 13.55% |
| 200 | 0.0001644229 | 39.17% | 0.0035485783 | 36.78% | 0.0029634074 | 38.35% | 0.3606980433 | 22.01% |
| 300 | 0.0001671517 | 39.82% | 0.0036421391 | 37.75% | 0.0030143232 | 39.01% | 0.3675470832 | 22.42% |

## rerun 与产物约束

| fix_samples | run dir | metrics git dirty | exclude reports | firstU rerun diff | secondU rerun diff | figures | checkpoint tracked | gate |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 50 | `reports/s_dpm_thr2/fix50_50ep` | `False` | `True` | 0.0 | 0.0 | 8 | `False` | `True` |
| 100 | `reports/s_dpm_thr2/fix100_50ep` | `False` | `True` | 0.0 | 0.0 | 8 | `False` | `True` |
| 200 | `reports/s_dpm_thr2/full_50ep` | `False` | `True` | 0.0 | 0.0 | 8 | `False` | `True` |
| 300 | `reports/s_dpm_thr2/fix300_50ep` | `False` | `True` | 0.0 | 0.0 | 8 | `False` | `True` |

## 曲线图

- sample count vs metric 曲线：`reports/s_dpm_thr2/sample_count_metric_curves.png`。

## 结论

- 50/100/200/300 四个点均已形成同口径 secondU 与 firstU 表格。
- 200 点使用既有 fixed-200 强基线产物，作为曲线中的已完成点。
- 所有点 eval rerun 数值差异均为 0.0。
