# Stage 2 final synthesis audit

## 范围

- 本报告统一 Stage 1 C baseline、fixed 50/100/200/300、implementation-default random 10..299、paper-faithful random 1..300。
- fixed sweep 是 controlled ablation；random 10..299 是历史 implementation-default 对照；random 1..300 是本阶段的 paper-faithful random sample count run。
- checkpoint 和 log 只作为本地复现实物，不进入 git；报告、metrics、manifest、PNG 和配置副本进入归档。
- final synthesis 生成源码提交：`601d7e6e239b9c6bdd8d9f7421f22d012c7c5859`，生成时排除 `reports/` 后源码干净。
- final synthesis 轻量产物入库提交：`2987ae495e2689176d8c5c33a1f5b5ddf31346f7`；该提交加入 `stage2_final_audit.json`、`stage2_final_audit.md` 和 `stage2_final_metric_curves.png`。

## firstU 全指标表

| setting | category | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stage 1 C baseline | baseline | 0.0004726781 | 0.0107978450 | 0.0087019187 | 0.0217411614 | 1.7392929098 |
| fixed 50 | controlled ablation | 0.0004785095 | 0.0112734726 | 0.0089284362 | 0.0218748589 | 1.7499887108 |
| fixed 100 | controlled ablation | 0.0003916606 | 0.0092568709 | 0.0073079367 | 0.0197904171 | 1.5832333682 |
| fixed 200 | controlled ablation | 0.0003268413 | 0.0077409654 | 0.0060984833 | 0.0180787533 | 1.4463002601 |
| fixed 300 | controlled ablation | 0.0003050918 | 0.0072132220 | 0.0056926623 | 0.0174668773 | 1.3973501838 |
| implementation-default random 10..299 | comparison variant | 0.0003582760 | 0.0084449454 | 0.0066850185 | 0.0189281803 | 1.5142544253 |
| paper-faithful random 1..300 | paper-faithful random sample count | 0.0003632125 | 0.0085622352 | 0.0067771270 | 0.0190581338 | 1.5246507009 |

## secondU 全指标表

| setting | category | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stage 1 C baseline | baseline | 0.0004197670 | 0.0096473684 | 0.0077278358 | 0.0204882173 | 1.6390573846 |
| fixed 50 | controlled ablation | 0.0004045899 | 0.0095794999 | 0.0075491820 | 0.0201144196 | 1.6091535706 |
| fixed 100 | controlled ablation | 0.0003137517 | 0.0074780237 | 0.0058542454 | 0.0177130366 | 1.4170429304 |
| fixed 200 | controlled ablation | 0.0002553442 | 0.0060987900 | 0.0047644284 | 0.0159794918 | 1.2783593414 |
| fixed 300 | controlled ablation | 0.0002526154 | 0.0060052292 | 0.0047135126 | 0.0158938788 | 1.2715103015 |
| implementation-default random 10..299 | comparison variant | 0.0002844340 | 0.0067724183 | 0.0053072106 | 0.0168651699 | 1.3492135894 |
| paper-faithful random 1..300 | paper-faithful random sample count | 0.0002833113 | 0.0067283779 | 0.0052862625 | 0.0168318528 | 1.3465482233 |

## 相比 Stage 1 的改进表

| setting | phase | metric | Stage 1 C | current | Stage 1 - current | improvement |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| fixed_50 | firstU | mse | 0.0004726781 | 0.0004785095 | -0.0000058314 | -1.23% |
| fixed_50 | firstU | nmse | 0.0107978450 | 0.0112734726 | -0.0004756276 | -4.40% |
| fixed_50 | firstU | global_nmse | 0.0087019187 | 0.0089284362 | -0.0002265176 | -2.60% |
| fixed_50 | firstU | rmse_db_80 | 1.7392929098 | 1.7499887108 | -0.0106958010 | -0.61% |
| fixed_50 | secondU | mse | 0.0004197670 | 0.0004045899 | 0.0000151772 | 3.62% |
| fixed_50 | secondU | nmse | 0.0096473684 | 0.0095794999 | 0.0000678684 | 0.70% |
| fixed_50 | secondU | global_nmse | 0.0077278358 | 0.0075491820 | 0.0001786538 | 2.31% |
| fixed_50 | secondU | rmse_db_80 | 1.6390573846 | 1.6091535706 | 0.0299038141 | 1.82% |
| fixed_100 | firstU | mse | 0.0004726781 | 0.0003916606 | 0.0000810175 | 17.14% |
| fixed_100 | firstU | nmse | 0.0107978450 | 0.0092568709 | 0.0015409741 | 14.27% |
| fixed_100 | firstU | global_nmse | 0.0087019187 | 0.0073079367 | 0.0013939820 | 16.02% |
| fixed_100 | firstU | rmse_db_80 | 1.7392929098 | 1.5832333682 | 0.1560595416 | 8.97% |
| fixed_100 | secondU | mse | 0.0004197670 | 0.0003137517 | 0.0001060154 | 25.26% |
| fixed_100 | secondU | nmse | 0.0096473684 | 0.0074780237 | 0.0021693447 | 22.49% |
| fixed_100 | secondU | global_nmse | 0.0077278358 | 0.0058542454 | 0.0018735904 | 24.24% |
| fixed_100 | secondU | rmse_db_80 | 1.6390573846 | 1.4170429304 | 0.2220144542 | 13.55% |
| fixed_200 | firstU | mse | 0.0004726781 | 0.0003268413 | 0.0001458368 | 30.85% |
| fixed_200 | firstU | nmse | 0.0107978450 | 0.0077409654 | 0.0030568795 | 28.31% |
| fixed_200 | firstU | global_nmse | 0.0087019187 | 0.0060984833 | 0.0026034354 | 29.92% |
| fixed_200 | firstU | rmse_db_80 | 1.7392929098 | 1.4463002601 | 0.2929926497 | 16.85% |
| fixed_200 | secondU | mse | 0.0004197670 | 0.0002553442 | 0.0001644229 | 39.17% |
| fixed_200 | secondU | nmse | 0.0096473684 | 0.0060987900 | 0.0035485783 | 36.78% |
| fixed_200 | secondU | global_nmse | 0.0077278358 | 0.0047644284 | 0.0029634074 | 38.35% |
| fixed_200 | secondU | rmse_db_80 | 1.6390573846 | 1.2783593414 | 0.3606980433 | 22.01% |
| fixed_300 | firstU | mse | 0.0004726781 | 0.0003050918 | 0.0001675863 | 35.45% |
| fixed_300 | firstU | nmse | 0.0107978450 | 0.0072132220 | 0.0035846229 | 33.20% |
| fixed_300 | firstU | global_nmse | 0.0087019187 | 0.0056926623 | 0.0030092564 | 34.58% |
| fixed_300 | firstU | rmse_db_80 | 1.7392929098 | 1.3973501838 | 0.3419427260 | 19.66% |
| fixed_300 | secondU | mse | 0.0004197670 | 0.0002526154 | 0.0001671517 | 39.82% |
| fixed_300 | secondU | nmse | 0.0096473684 | 0.0060052292 | 0.0036421391 | 37.75% |
| fixed_300 | secondU | global_nmse | 0.0077278358 | 0.0047135126 | 0.0030143232 | 39.01% |
| fixed_300 | secondU | rmse_db_80 | 1.6390573846 | 1.2715103015 | 0.3675470832 | 22.42% |
| implementation_default_random_10_299 | firstU | mse | 0.0004726781 | 0.0003582760 | 0.0001144021 | 24.20% |
| implementation_default_random_10_299 | firstU | nmse | 0.0107978450 | 0.0084449454 | 0.0023528995 | 21.79% |
| implementation_default_random_10_299 | firstU | global_nmse | 0.0087019187 | 0.0066850185 | 0.0020169002 | 23.18% |
| implementation_default_random_10_299 | firstU | rmse_db_80 | 1.7392929098 | 1.5142544253 | 0.2250384845 | 12.94% |
| implementation_default_random_10_299 | secondU | mse | 0.0004197670 | 0.0002844340 | 0.0001353331 | 32.24% |
| implementation_default_random_10_299 | secondU | nmse | 0.0096473684 | 0.0067724183 | 0.0028749501 | 29.80% |
| implementation_default_random_10_299 | secondU | global_nmse | 0.0077278358 | 0.0053072106 | 0.0024206252 | 31.32% |
| implementation_default_random_10_299 | secondU | rmse_db_80 | 1.6390573846 | 1.3492135894 | 0.2898437952 | 17.68% |
| paper_faithful_random_1_300 | firstU | mse | 0.0004726781 | 0.0003632125 | 0.0001094656 | 23.16% |
| paper_faithful_random_1_300 | firstU | nmse | 0.0107978450 | 0.0085622352 | 0.0022356097 | 20.70% |
| paper_faithful_random_1_300 | firstU | global_nmse | 0.0087019187 | 0.0067771270 | 0.0019247917 | 22.12% |
| paper_faithful_random_1_300 | firstU | rmse_db_80 | 1.7392929098 | 1.5246507009 | 0.2146422089 | 12.34% |
| paper_faithful_random_1_300 | secondU | mse | 0.0004197670 | 0.0002833113 | 0.0001364558 | 32.51% |
| paper_faithful_random_1_300 | secondU | nmse | 0.0096473684 | 0.0067283779 | 0.0029189905 | 30.26% |
| paper_faithful_random_1_300 | secondU | global_nmse | 0.0077278358 | 0.0052862625 | 0.0024415732 | 31.59% |
| paper_faithful_random_1_300 | secondU | rmse_db_80 | 1.6390573846 | 1.3465482233 | 0.2925091613 | 17.85% |

## fixed sweep 曲线表

| fix_samples | phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 50 | firstU | 0.0004785095 | 0.0112734726 | 0.0089284362 | 0.0218748589 | 1.7499887108 |
| 50 | secondU | 0.0004045899 | 0.0095794999 | 0.0075491820 | 0.0201144196 | 1.6091535706 |
| 100 | firstU | 0.0003916606 | 0.0092568709 | 0.0073079367 | 0.0197904171 | 1.5832333682 |
| 100 | secondU | 0.0003137517 | 0.0074780237 | 0.0058542454 | 0.0177130366 | 1.4170429304 |
| 200 | firstU | 0.0003268413 | 0.0077409654 | 0.0060984833 | 0.0180787533 | 1.4463002601 |
| 200 | secondU | 0.0002553442 | 0.0060987900 | 0.0047644284 | 0.0159794918 | 1.2783593414 |
| 300 | firstU | 0.0003050918 | 0.0072132220 | 0.0056926623 | 0.0174668773 | 1.3973501838 |
| 300 | secondU | 0.0002526154 | 0.0060052292 | 0.0047135126 | 0.0158938788 | 1.2715103015 |

## random 10..299 vs random 1..300 差异表

| phase | metric | random 10..299 | random 1..300 | 1..300 - 10..299 | relative delta |
| --- | --- | ---: | ---: | ---: | ---: |
| firstU | mse | 0.0003582760 | 0.0003632125 | 0.0000049365 | 1.38% |
| firstU | nmse | 0.0084449454 | 0.0085622352 | 0.0001172898 | 1.39% |
| firstU | global_nmse | 0.0066850185 | 0.0067771270 | 0.0000921085 | 1.38% |
| firstU | rmse | 0.0189281803 | 0.0190581338 | 0.0001299534 | 0.69% |
| firstU | rmse_db_80 | 1.5142544253 | 1.5246507009 | 0.0103962757 | 0.69% |
| secondU | mse | 0.0002844340 | 0.0002833113 | -0.0000011227 | -0.39% |
| secondU | nmse | 0.0067724183 | 0.0067283779 | -0.0000440403 | -0.65% |
| secondU | global_nmse | 0.0053072106 | 0.0052862625 | -0.0000209480 | -0.39% |
| secondU | rmse | 0.0168651699 | 0.0168318528 | -0.0000333171 | -0.20% |
| secondU | rmse_db_80 | 1.3492135894 | 1.3465482233 | -0.0026653661 | -0.20% |

## paper-faithful run 与论文设定对齐检查表

| item | passed |
| --- | --- |
| loader_RadioUNet_s | `True` |
| simulation_DPM | `True` |
| threshold_0_2 | `True` |
| fix_samples_0 | `True` |
| drawn_count_1_300 | `True` |
| firstU_50_epochs | `True` |
| secondU_50_epochs | `True` |
| batch_size_15 | `True` |
| seed_42 | `True` |
| passed | `True` |

## 论文复现判断

### 已按论文口径复现
- RadioUNet_s / DPM / threshold=0.2 / seed=42 / batch_size=15 的 Stage 2 random 1..300 训练、评估和 rerun 已完成。
- random 1..300 的 test split RNG replay 证明 drawn count 为 1..300。
- firstU/secondU 50 epoch、checkpoint manifest、8 张图和 metrics 归档完整。

### controlled ablation
- fixed 50/100/200/300 是 controlled ablation，用来隔离 sparse sample count 对性能的影响。
- implementation-default random 10..299 是历史实现默认口径对照，不是论文 1..300。

### 仍不是论文完整复现
- Stage 2 仍只覆盖当前 DPM/complete-city-map/test split 口径，不覆盖论文所有仿真/缺楼/transfer 设置。
- IRT4 transfer、missing buildings 和 robustness 尚未在本阶段训练或评估。

## Stage 2 关闭结论

- Stage 2 能否关闭：`True`。
- 下一阶段：Stage 3 应进入 IRT4 zero-shot transfer / missing buildings / robustness，因为 Stage 2 已完成 S 输入与随机样本数口径收口，剩余差距属于跨仿真与鲁棒性问题。
- 总汇总曲线图：`reports/s_dpm_thr2/stage2_final_metric_curves.png`。
