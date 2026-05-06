# Stage 1 审计报告：RadioUNet_C + DPM + threshold=0.2

日期：2026-05-06

## 结论

本次完整 Stage 1 基线实验已从 smoke test 升级为可报告结果。配置为 `configs/c_dpm_thr2.yaml`，模型为 `RadioWNet`，数据路径为 `RadioMapSeer/`，loader 为 `RadioUNet_c`，目标为 DPM，threshold 为 `0.2`，firstU 和 secondU 均完整训练 50 epoch。

主要 test 结果如下：

| checkpoint | 输出头 | samples | MSE | NMSE | RMSE | RMSE dB = 80 * RMSE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| firstU.pt | firstU | 7920 | 0.0004726781 | 0.0107978450 | 0.0217411614 | 1.7392929098 |
| secondU.pt | secondU | 7920 | 0.0004197670 | 0.0096473684 | 0.0204882173 | 1.6390573846 |

secondU 相比 firstU 的 test MSE 改善约 11.19%，RMSE 改善约 5.76%，复现了 WNet 第二阶段带来的改善。

## 实验前审计

- git status：实验启动前为干净工作区。
- 固定 commit：`c2e282ce28a5ba6fd5f54a3a6b1176fd04ed4c7f`。
- 数据审计命令：`python scripts/validate_dataset.py --dataset-dir RadioMapSeer/`。
- 数据审计产物：
  - `reports/dataset_validation/dataset_validation.json`
  - `reports/dataset_validation/dataset_validation.md`
- 数据目录大小：约 `4.0G`。
- 数据文件数：`355408`。
- GPU：`NVIDIA GeForce RTX 4090, 24564 MiB`。
- NVIDIA driver：`570.172.08`。
- Python：`3.12.3`。
- PyTorch：`2.6.0+cu124`。
- CUDA available：`True`。
- torch CUDA：`12.4`。
- cuDNN：`90100`。

数据集校验摘要：

| 路径 | PNG 数量 | 状态 |
| --- | ---: | --- |
| `png/buildings_complete` | 701 | OK |
| `png/antennas` | 56080 | OK |
| `gain/DPM` | 56080 | OK |
| `gain/IRT2` | 56080 | OK |
| `gain/IRT4` | 1402 | OK |

说明：`png/buildings_complete` 中包含 701 个 PNG，其中官方 loader 实际使用 map id `1..700`。文件 `0.png` 不进入当前 split 逻辑，不影响本次 train/val/test 样本数。

样本 `map=1, tx=0` 的 buildings、antenna、DPM、IRT2、IRT4 均通过尺寸和值域校验。

## 命令记录

```bash
python scripts/validate_dataset.py --dataset-dir RadioMapSeer/

python scripts/train.py \
  --config configs/c_dpm_thr2.yaml \
  --phase firstU

python scripts/evaluate.py \
  --config configs/c_dpm_thr2.yaml \
  --checkpoint reports/c_dpm_thr2/20260506_182311/checkpoints/firstU.pt \
  --split test \
  --output reports/c_dpm_thr2/20260506_182311/firstU_test_metrics.json

python scripts/train.py \
  --config configs/c_dpm_thr2.yaml \
  --phase secondU \
  --init-checkpoint reports/c_dpm_thr2/20260506_182311/checkpoints/firstU.pt \
  --run-dir reports/c_dpm_thr2/20260506_182311

python scripts/evaluate.py \
  --config configs/c_dpm_thr2.yaml \
  --checkpoint reports/c_dpm_thr2/20260506_182311/checkpoints/secondU.pt \
  --split test \
  --output reports/c_dpm_thr2/20260506_182311/secondU_test_metrics.json

python scripts/make_figures.py \
  --config configs/c_dpm_thr2.yaml \
  --checkpoint reports/c_dpm_thr2/20260506_182311/checkpoints/secondU.pt \
  --split test \
  --limit 8 \
  --output-dir reports/c_dpm_thr2/20260506_182311/figures
```

## 训练产物

run 目录：`reports/c_dpm_thr2/20260506_182311`

| 阶段 | 训练样本/epoch | 验证样本/epoch | epoch | best val loss | best epoch | checkpoint |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| firstU | 40080 | 8000 | 50 | 0.0004492493 | 29 | `checkpoints/firstU.pt` |
| secondU | 40080 | 8000 | 50 | 0.0003981426 | 45 | `checkpoints/secondU.pt` |

checkpoint manifest：

| 阶段 | manifest | sha256 |
| --- | --- | --- |
| firstU | `reports/c_dpm_thr2/20260506_182311/firstU_checkpoint_manifest.json` | `cfec8caf23f20231e95a6c63f221e3e5f5515a05cf92a1522ad73081aad6ae25` |
| secondU | `reports/c_dpm_thr2/20260506_182311/secondU_checkpoint_manifest.json` | `cd36e18b88c07309825a5d1f8a4dac32818681d434c3cf02de28d836e03d1e06` |

checkpoint 文件按 `.gitignore` 不纳入 Git；轻量报告产物，包括 manifest、metrics、Markdown 和 PNG 图像，会纳入 Git，便于 clone 后直接审计。

## 官方 notebook / 论文对照

官方 notebook：`reference/RadioUNet/RadioWNet_c_DPM_Thr2.ipynb`。

notebook 中 DPM test 输出：

| 来源 | firstU MSE | secondU MSE | firstU NMSE | secondU NMSE |
| --- | ---: | ---: | ---: | ---: |
| 官方 notebook | 0.000463 | 0.000409 | 0.008737 | 0.007728 |
| 本次复现 | 0.0004726781 | 0.0004197670 | 0.0107978450 | 0.0096473684 |
| 相对差异 | +2.09% | +2.63% | +23.59% | +24.83% |

论文源码：`reference/RadioUNet_paper_source/RadioUNet_paper_ver3.tex`。相近设置 `accurate map, deterministic simulation with no cars` 的 RadioUNet_C coarse simulations 行给出：

| 来源 | NMSE | RMSE |
| --- | ---: | ---: |
| 论文表格 | 0.0075 | 0.0200 |
| 本次 secondU | 0.0096473684 | 0.0204882173 |
| 相对差异 | +28.63% | +2.44% |

本次复现的 MSE/RMSE 与官方 notebook 和论文表格接近，secondU RMSE 为 `0.02049`，对应 dB RMSE 为 `1.63906`。NMSE 偏高更明显，主要因为 NMSE 对 target energy 分母敏感：本次 secondU `MSE/NMSE` 推回的平均 target energy 约为 `0.0435`，官方 notebook 对应约为 `0.0529`。这提示仍需后续核对数据集版本、target 阈值变换和官方 notebook 的确切依赖版本，但不改变本次 MSE/RMSE 基线已进入可报告范围的结论。

## 图像产物

已生成 8 张 test split 预测/误差图：

- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0000.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0001.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0002.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0003.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0004.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0005.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0006.png`
- `reports/c_dpm_thr2/20260506_182311/figures/c_dpm_thr2_test_0007.png`

每张图包含输入、target、prediction 和 absolute error 面板，可用于报告中的预测图与误差图展示。

## 偏差说明

- firstU 与 secondU 的 MSE/RMSE 均略高于官方 notebook，但差异在约 2% 到 3% 范围内。
- NMSE 比官方 notebook 和论文表格高约 24% 到 29%，比 RMSE 差异更明显，原因可能是 target 能量分母差异、数据集版本差异、图像读取/阈值变换细节或依赖版本差异。该问题已登记为 Stage 2 前的审计项：在推进 RadioUNet_S 之前，需要复算官方 notebook 的 NMSE 分母、当前 loader 阈值后 target energy，以及当前数据集是否与官方 notebook 使用的数据包一致。
- 本实现沿用官方训练超参：Adam、学习率 `1e-4`、StepLR `step_size=30`、`gamma=0.1`、batch size `15`、每个 U-Net 50 epoch、按验证集最小 loss 保存 best checkpoint。
- 当前训练脚本在 epoch 开头调用 `scheduler.step()`，因此学习率在日志中的 epoch 29 开始变为 `1e-5`；官方 notebook 代码也采用相同调用顺序。

## 可报告性判断

Stage 1 明确交付物均已生成：

- 数据集审计摘要：已完成。
- firstU/secondU 完整 50 epoch checkpoint：已完成。
- firstU/secondU history、metadata、manifest：已完成。
- firstU/secondU test 指标：已完成。
- secondU 预测图、误差图：已完成。
- 官方 notebook / 论文数值对照：已完成。
- 偏差原因说明：已完成。
- 命令记录：已完成。

结论：项目状态已从“真实 smoke 闭环通过”升级为“Stage 1 基线实验可报告”。
