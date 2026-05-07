# Stage 2 正式审计：RadioUNet_S + DPM + threshold=0.2

## 结论

- Stage 2 full train 已完成：RadioUNet_S + DPM + threshold=0.2，`firstU` 和 `secondU` 各 50 epoch。
- 权威 run 目录：`reports/s_dpm_thr2/full_50ep`，没有使用时间戳目录作为权威结果。
- source commit：`5b27461bfb3059c5d128926cc434f4ca5bbe0e7e`。
- artifact commit：`0c7f31bc9505be65d7c9283ec5917527d59f3c99`（`Add Stage 2 full RadioUNet S artifacts`）。
- source clean gate：正式训练启动前 `git status --short` 为空；训练后 `git status --short -- ':!reports'` 为空。
- checkpoint 只保留本地，不进 git；checkpoint manifest 记录 sha256。

## 配置和种子

- 配置文件：`configs/s_dpm_thr2.yaml`，训练时复制到 `reports/s_dpm_thr2/full_50ep/s_dpm_thr2.yaml`。
- seed：`42`。
- loader：`RadioUNet_s`。
- simulation：`DPM`。
- city map：`complete`。
- threshold：`0.2`。
- model：`RadioWNet`，输入通道数 `3`。
- batch size：`15`。
- epoch：`50` per phase。
- sparse sample 策略：`fix_samples=200`；由于采样坐标可能重复且 sampled target 可能为 0，test split 观测到 sparse channel 非零数范围为 `24..199`，均值 `128.73661616161615`，前 8 个样本为 `[173, 166, 176, 170, 169, 170, 174, 174]`。

## 执行命令

1. 前置 gate：`git status --short`
2. 前置 gate：`git status --short -- ':!reports'`
3. 前置 gate：`git rev-parse HEAD`
4. 前置 gate：`git check-ignore -v reports/s_dpm_thr2/full_50ep/checkpoints/firstU.pt reports/s_dpm_thr2/full_50ep/checkpoints/secondU.pt`
5. firstU 训练：`python scripts/train.py --config configs/s_dpm_thr2.yaml --phase firstU --run-dir reports/s_dpm_thr2/full_50ep`
6. firstU 评估：`python scripts/evaluate.py --config configs/s_dpm_thr2.yaml --checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/firstU.pt --split test --output reports/s_dpm_thr2/full_50ep/firstU_test_metrics.json`
7. secondU 训练：`python scripts/train.py --config configs/s_dpm_thr2.yaml --phase secondU --init-checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/firstU.pt --run-dir reports/s_dpm_thr2/full_50ep`
8. secondU 评估：`python scripts/evaluate.py --config configs/s_dpm_thr2.yaml --checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/secondU.pt --split test --output reports/s_dpm_thr2/full_50ep/secondU_test_metrics.json`
9. 出图：`python scripts/make_figures.py --config configs/s_dpm_thr2.yaml --checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/secondU.pt --split test --limit 8 --output-dir reports/s_dpm_thr2/full_50ep/figures`
10. firstU eval 复跑：`python scripts/evaluate.py --config configs/s_dpm_thr2.yaml --checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/firstU.pt --split test --output reports/s_dpm_thr2/full_50ep/firstU_test_metrics_rerun.json`
11. secondU eval 复跑：`python scripts/evaluate.py --config configs/s_dpm_thr2.yaml --checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/secondU.pt --split test --output reports/s_dpm_thr2/full_50ep/secondU_test_metrics_rerun.json`

## 训练结果

| phase | best val loss | history entries | checkpoint sha256 |
| --- | ---: | ---: | --- |
| firstU | `20.16671122930944` | `100` | `5d36a1ddcfcd96a3e11f3e9d32b9ac9b7704f3aef029238ee0b3e26778c5ff88` |
| secondU | `15.752223132848739` | `100` | `b42869fa94873327b70e97b815f15c160498003bc14d549186f00bde9ce811ed` |

## Test 指标

| model / phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 2 RadioUNet_S firstU | `0.00032684131911358264` | `0.007740965432965437` | `0.006098483258523693` | `0.018078753251084066` | `1.4463002600867254` |
| Stage 2 RadioUNet_S secondU | `0.00025534415712944326` | `0.006098790043049094` | `0.004764428413299941` | `0.015979491766931864` | `1.278359341354549` |

## Stage 1 对照

| model / phase | MSE | NMSE | global NMSE | RMSE | dB RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 1 RadioUNet_C firstU | `0.00047267809781480923` | `0.010797844952486974` | `0.008701918665234756` | `0.021741161372263656` | `1.7392929097810925` |
| Stage 2 RadioUNet_S firstU | `0.00032684131911358264` | `0.007740965432965437` | `0.006098483258523693` | `0.018078753251084066` | `1.4463002600867254` |
| Stage 1 RadioUNet_C secondU | `0.000419767048463131` | `0.009647368385478992` | `0.007727835774406763` | `0.02048821730808054` | `1.6390573846464431` |
| Stage 2 RadioUNet_S secondU | `0.00025534415712944326` | `0.006098790043049094` | `0.004764428413299941` | `0.015979491766931864` | `1.278359341354549` |

- firstU MSE 相对 Stage 1 降低 `30.853297281052367%`，dB RMSE 降低 `0.2929926496943671`。
- secondU MSE 相对 Stage 1 降低 `39.17003298274122%`，dB RMSE 降低 `0.36069804329189403`。

## 复跑一致性

- `firstU_test_metrics.json` vs `firstU_test_metrics_rerun.json`：`samples=7920` 一致，`firstU` 和 `secondU` 的 `mse/raw_mse/nmse/global_nmse/rmse/rmse_db_80` 差异全为 `0.0`。
- `secondU_test_metrics.json` vs `secondU_test_metrics_rerun.json`：`samples=7920` 一致，`firstU` 和 `secondU` 的 `mse/raw_mse/nmse/global_nmse/rmse/rmse_db_80` 差异全为 `0.0`。
- 每个 metrics JSON 的 `git.dirty=false`，`exclude_paths=['reports']`；`artifact_git.dirty=true` 仅表示生成中的 `reports/` 产物未提交，不代表源码 dirty。

## 图像产物

- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0000.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0001.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0002.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0003.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0004.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0005.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0006.png`
- `reports/s_dpm_thr2/full_50ep/figures/s_dpm_thr2_test_0007.png`

## 最终 gate

- `git status --short -- ':!reports'`：为空。
- checkpoint git 跟踪检查：`git ls-files reports/s_dpm_thr2/full_50ep/checkpoints/firstU.pt reports/s_dpm_thr2/full_50ep/checkpoints/secondU.pt` 为空。
- checkpoint ignore 检查：`.gitignore:20:reports/**/checkpoints/` 命中 firstU 和 secondU checkpoint。
