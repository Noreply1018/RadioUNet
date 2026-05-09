# Stage 2 paper-faithful random 1..300 audit

## 范围

- 本 run 是 `paper-faithful random sample count run`：`data.fix_samples=0`，每个样本重新随机抽 sparse sample count。
- 配置为 `num_samples_low=1`、`num_samples_high=301`；由于 `np.random.randint(low, high)` 的 high 为排他上界，实际 drawn count 为 `1..300`。
- 本 run 是论文随机样本数口径的 Stage 2 结果；`implementation-default random 10..299` 只保留为对照变体。
- 固定权威目录：`reports/s_dpm_thr2/rand1_300_50ep`。
- 配置：`configs/s_dpm_thr2_rand1_300.yaml`，run copy 已保存为 `reports/s_dpm_thr2/rand1_300_50ep/s_dpm_thr2_rand1_300.yaml`。
- loader/simulation/threshold：`RadioUNet_s` / `DPM` / `0.2`。
- firstU/secondU epoch：`50` / `50`；history 条数：`100` / `100`。
- run metadata git dirty：`False`；metrics git dirty：firstU `False`，secondU `False`。
- checkpoint sha256 匹配：`True`；checkpoint 进 git：`False`。
- eval rerun 最大差异：firstU `0.0`，secondU `0.0`。
- 预测图数量：`8`；gate passed：`True`。

## random sparse sample 审计

- 配置：`fix_samples=0`，`num_samples_low=1`，`num_samples_high=301`。
- RNG replay 记录到的 drawn sample count 范围是 `1..300`，均值 `150.6538`。
- drawn count 前 16 个：`[251, 86, 211, 65, 90, 92, 3, 12, 150, 89, 108, 276, 198, 279, 162, 241]`。
- drawn count 分桶：`{'1..49': 1349, '50..99': 1252, '100..149': 1327, '150..199': 1259, '200..249': 1379, '250..300': 1354}`。
- 真实 DataLoader 检查样本数：`7920`；sparse channel 非零数范围：`0..287`，均值 `96.8232`。
- sparse 与 target 对齐最大绝对误差：`0.0`。

## secondU fixed sweep + random 对照表

| setting | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| fixed 50 | 0.0004045899 | 0.0095794999 | 0.0075491820 | 0.0201144196 | 1.6091535706 |
| fixed 100 | 0.0003137517 | 0.0074780237 | 0.0058542454 | 0.0177130366 | 1.4170429304 |
| fixed 200 | 0.0002553442 | 0.0060987900 | 0.0047644284 | 0.0159794918 | 1.2783593414 |
| fixed 300 | 0.0002526154 | 0.0060052292 | 0.0047135126 | 0.0158938788 | 1.2715103015 |
| implementation-default random 10..299 | 0.0002844340 | 0.0067724183 | 0.0053072106 | 0.0168651699 | 1.3492135894 |
| paper-faithful random 1..300 | 0.0002833113 | 0.0067283779 | 0.0052862625 | 0.0168318528 | 1.3465482233 |

## firstU / secondU random metrics

| phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| firstU | 0.0003632125 | 0.0085622352 | 0.0067771270 | 0.0190581338 | 1.5246507009 |
| secondU | 0.0002833113 | 0.0067283779 | 0.0052862625 | 0.0168318528 | 1.3465482233 |

## 相比 Stage 1 C baseline

| phase | metric | Stage 1 C | paper-faithful random 1..300 | Stage 1 - random | improvement |
| --- | --- | ---: | ---: | ---: | ---: |
| firstU | mse | 0.0004726781 | 0.0003632125 | 0.0001094656 | 23.16% |
| firstU | nmse | 0.0107978450 | 0.0085622352 | 0.0022356097 | 20.70% |
| firstU | global_nmse | 0.0087019187 | 0.0067771270 | 0.0019247917 | 22.12% |
| firstU | rmse_db_80 | 1.7392929098 | 1.5246507009 | 0.2146422089 | 12.34% |
| secondU | mse | 0.0004197670 | 0.0002833113 | 0.0001364558 | 32.51% |
| secondU | nmse | 0.0096473684 | 0.0067283779 | 0.0029189905 | 30.26% |
| secondU | global_nmse | 0.0077278358 | 0.0052862625 | 0.0024415732 | 31.59% |
| secondU | rmse_db_80 | 1.6390573846 | 1.3465482233 | 0.2925091613 | 17.85% |

## 结论

- paper-faithful random 1..300 的 RNG replay 已覆盖 test split 全部 `7920` 个样本，drawn count 明确覆盖 `1..300`。
- 本 run 满足训练前干净源码、metrics `git.dirty=false`、checkpoint manifest hash 匹配、checkpoint/log 不进 git、eval rerun diff 为 `0.0`、8 张预测图完整这些 Stage 2 归档约束。
- 对照曲线图：`reports/s_dpm_thr2/rand1_300_50ep/rand1_300_vs_fixed_rand10_metrics.png`。
