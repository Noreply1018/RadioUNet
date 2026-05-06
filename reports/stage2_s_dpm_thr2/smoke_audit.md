# Stage 2 smoke 审计：RadioUNet_S + DPM + threshold=0.2

## 追溯性

- source git commit：`16bef7e691ee2f4ea717bac7089c1437e1578df9`。
- source dirty：`False`（检查时排除 `reports/` 产物目录）。
- source status：`clean`。
- artifact dirty 说明：JSON 中 `artifact_git.dirty=true` 只表示报告和 smoke 产物生成后位于 `reports/` 待提交，不表示源码/配置 dirty。
- artifact commit：`d32dc2505a086c4a4b6226c4d8fdd4e8dae64be0`（`Refresh Stage 2 smoke provenance report`）。
- artifact commit 查询命令：`git log -1 --format='%H %s' -- reports/stage2_s_dpm_thr2/smoke_audit.md reports/stage2_s_dpm_thr2/smoke_audit.json reports/s_dpm_thr2/clean_smoke`。

## 权威产物

- 审计报告目录：`reports/stage2_s_dpm_thr2`。
- smoke run 目录：`reports/s_dpm_thr2/clean_smoke`。
- 旧版 `reports/stage2_smoke/` 和时间戳 smoke run 不再作为 Stage 2 权威证据。

## 结论

- 当前 test split 直接统计的 `MSE(target, 0)` 为 `0.0543188366`；全局像素口径为 `0.0543188365`，两者一致到可忽略量级。
- 官方 notebook 由 `MSE/NMSE` 反推的分母均值为 `0.0529587244`；论文表格由 `RMSE^2/NMSE` 反推的分母为 `0.0533333333`。
- 当前直接 target energy 比 notebook 高 `2.57%`，比论文表格高 `1.85%`，属于小差异；Stage 1 报告中由“平均 MSE / 平均 NMSE”反推的 `0.0435..0.0438` 不是 test split 真实 target energy。
- 结论：遗留 NMSE 偏差主要是统计粒度差异，也就是 batch-mean NMSE 与全局 `sum(error^2)/sum(target^2)` 的口径差异；不支持归因于数据版本差异或 threshold=0.2 差异。

## NMSE 口径审计

| 来源 | 分母口径 | 数值 |
| --- | --- | ---: |
| 当前 test split | `MSE(target, 0)` batch 加权均值 | `0.0543188366` |
| 当前 test split | `sum(target^2)/Npixels` 全局像素均值 | `0.0543188365` |
| 官方 notebook | firstU `MSE/NMSE` 反推 | `0.0529930182` |
| 官方 notebook | secondU `MSE/NMSE` 反推 | `0.0529244306` |
| 论文表格 | `RMSE^2/NMSE` 反推 | `0.0533333333` |

Stage 1 firstU 当前 batch-mean NMSE 有效分母：`0.0437752255`。
Stage 1 secondU 当前 batch-mean NMSE 有效分母：`0.0435110417`。
按全局 target energy 重算 firstU NMSE：`0.008701918665234756`。
按全局 target energy 重算 secondU NMSE：`0.007727835774406763`。

## RadioUNet_S loader 审计

- loader：`RadioUNet_s`。
- 输入 shape：`[2, 3, 256, 256]`。
- target shape：`[2, 1, 256, 256]`。
- 三个输入通道：`buildings, Tx, sparse samples`。
- sparse samples 非零数量范围：`178..182`。
- sparse samples 值域：`0.000000..164.750000`，target 值域：`0.000000..254.750000`。
- sparse samples 与 target 对齐检查最大绝对误差：`0.0000000000`。
- sparse sample 可视化：`reports/stage2_s_dpm_thr2/figures/s_dpm_thr2_sparse_samples.png`。

## Stage 2 配置

- 配置文件：`configs/s_dpm_thr2.yaml`。
- 关键设置：`loader=RadioUNet_s`，`simulation=DPM`，`city_map=complete`，`inputs=3`，`threshold=0.2`。
- 当前配置只作为 smoke 入口，不声明 full train 结果。
- 后续正式训练固定权威 run 目录：`reports/s_dpm_thr2/full_50ep`。
- firstU 正式训练命令：`python scripts/train.py --config configs/s_dpm_thr2.yaml --phase firstU --run-dir reports/s_dpm_thr2/full_50ep`。
- secondU 正式训练命令：`python scripts/train.py --config configs/s_dpm_thr2.yaml --phase secondU --init-checkpoint reports/s_dpm_thr2/full_50ep/checkpoints/firstU.pt --run-dir reports/s_dpm_thr2/full_50ep`。

## Smoke training

- 命令：`python scripts/train.py --config configs/s_dpm_thr2.yaml --phase firstU --smoke --run-dir reports/s_dpm_thr2/clean_smoke`。
- firstU smoke loss：`6404.4189453125` train / `6402.39501953125` val，best val `6402.39501953125`。

## Smoke evaluation / figure

- firstU smoke MSE：`0.09770692139863968`。
- firstU smoke NMSE：`0.9968146085739136`。
- firstU smoke RMSE：`0.3125810637236998`。
- prediction/error 图：`reports/s_dpm_thr2/clean_smoke/figures/s_dpm_thr2_test_0000.png`。
