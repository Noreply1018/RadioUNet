# Stage 2 implementation-default random 10..299 audit

## 范围

- 本 run 是 `implementation-default random 10..299 run`：`data.fix_samples=0`，每个样本重新随机抽 sparse sample count。
- 本 run 不是 paper-faithful `1..300`；原因是配置为 `num_samples_low=10`，`num_samples_high=300`，而 `np.random.randint(low, high)` 的 high 为排他上界，实际 drawn count 为 `10..299`。
- 本 run 保留为对照变体，不删除、不覆盖 paper-faithful random `1..300` run。
- 本 run 不是 fixed sample count controlled ablation；fixed 50/100/200/300 只作为对照曲线/表格。
- 固定权威目录：`reports/s_dpm_thr2/rand10_300_50ep`；未使用时间戳目录作为权威结果。
- 配置：`configs/s_dpm_thr2_rand10_300.yaml`，run copy 已保存为 `reports/s_dpm_thr2/rand10_300_50ep/s_dpm_thr2_rand10_300.yaml`。
- loader/simulation/threshold：`RadioUNet_s` / `DPM` / `0.2`。
- artifact add commit：`535b7b3`。
- firstU/secondU epoch：`50` / `50`；history 条数：`100` / `100`。
- metrics git dirty：firstU `False`，secondU `False`；exclude_paths 均包含 `reports`。
- checkpoint sha256 匹配：`True`；checkpoint 进 git：`False`。
- eval rerun 最大差异：firstU `0.0`，secondU `0.0`。
- 预测图数量：`8`；gate passed：`True`。

## random sparse sample 审计

- 配置：`fix_samples=0`，`num_samples_low=10`，`num_samples_high=300`。
- 实现细节：`np.random.randint(low, high)` 的 high 是排他上界；本次 RNG replay 记录到的 drawn sample count 范围是 `10..299`，均值 `155.1460`。
- drawn count 前 16 个：`[222, 108, 256, 74, 41, 88, 283, 82, 241, 117, 22, 141, 281, 287, 171, 108]`。
- drawn count 分桶：`{'10..49': 1047, '50..99': 1379, '100..149': 1394, '150..199': 1351, '200..249': 1381, '250..299': 1368}`。
- 真实 DataLoader 抽检样本数：`120`；sparse channel 非零数范围：`8..263`，均值 `127.2167`。
- sparse 与 target 对齐最大绝对误差：`0.0`。

## secondU fixed sweep + random 对照表

| setting | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| fixed 50 | 0.0004045899 | 0.0095794999 | 0.0075491820 | 0.0201144196 | 1.6091535706 |
| fixed 100 | 0.0003137517 | 0.0074780237 | 0.0058542454 | 0.0177130366 | 1.4170429304 |
| fixed 200 | 0.0002553442 | 0.0060987900 | 0.0047644284 | 0.0159794918 | 1.2783593414 |
| fixed 300 | 0.0002526154 | 0.0060052292 | 0.0047135126 | 0.0158938788 | 1.2715103015 |
| implementation-default random 10..299 | 0.0002844340 | 0.0067724183 | 0.0053072106 | 0.0168651699 | 1.3492135894 |

## firstU / secondU random metrics

| phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| firstU | 0.0003582760 | 0.0084449454 | 0.0066850185 | 0.0189281803 | 1.5142544253 |
| secondU | 0.0002844340 | 0.0067724183 | 0.0053072106 | 0.0168651699 | 1.3492135894 |

## 相比 Stage 1 C baseline

| phase | metric | Stage 1 C | implementation-default random 10..299 | Stage 1 - random | improvement |
| --- | --- | ---: | ---: | ---: | ---: |
| firstU | mse | 0.0004726781 | 0.0003582760 | 0.0001144021 | 24.20% |
| firstU | nmse | 0.0107978450 | 0.0084449454 | 0.0023528995 | 21.79% |
| firstU | global_nmse | 0.0087019187 | 0.0066850185 | 0.0020169002 | 23.18% |
| firstU | rmse_db_80 | 1.7392929098 | 1.5142544253 | 0.2250384845 | 12.94% |
| secondU | mse | 0.0004197670 | 0.0002844340 | 0.0001353331 | 32.24% |
| secondU | nmse | 0.0096473684 | 0.0067724183 | 0.0028749501 | 29.80% |
| secondU | global_nmse | 0.0077278358 | 0.0053072106 | 0.0024206252 | 31.32% |
| secondU | rmse_db_80 | 1.6390573846 | 1.3492135894 | 0.2898437952 | 17.68% |

## 结论

- implementation-default random 10..299 的 secondU 表现按 MSE/NMSE/global NMSE/dB RMSE 距离看，整体更接近 fixed `200` 点；逐指标最近点：`[{'metric': 'mse', 'closest_fix_samples': 200, 'abs_distance': 2.9089797532254693e-05}, {'metric': 'nmse', 'closest_fix_samples': 200, 'abs_distance': 0.0006736282161772106}, {'metric': 'global_nmse', 'closest_fix_samples': 200, 'abs_distance': 0.0005427821701719012}, {'metric': 'rmse_db_80', 'closest_fix_samples': 100, 'abs_distance': 0.06782934103690885}]`。
- implementation-default random 10..299 是否优于 Stage 1 C baseline：`True`。secondU MSE 从 `0.0004197670` 降到 `0.0002844340`，NMSE 从 `0.0096473684` 降到 `0.0067724183`。
- 对照曲线图：`reports/s_dpm_thr2/rand10_300_50ep/rand10_300_vs_fixed_metrics.png`。
