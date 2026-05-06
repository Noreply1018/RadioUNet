# RadioMapSeer Stage 0 + Stage 1 Smoke 审计记录

日期: 2026-05-06

## 目标

从工程骨架推进到真实 RadioMapSeer 数据驱动的 Stage 0 + Stage 1 smoke 闭环，验证真实 loader、tensor shape、threshold、firstU forward/backward、checkpoint 保存、评估和可视化。

## 执行记录

| 步骤 | 命令 | 结果 |
| --- | --- | --- |
| 自动准备数据 | `python scripts/prepare_dataset.py --dataset-dir RadioMapSeer/` | Google Drive 直连失败，脚本提示手动下载路径。 |
| 本地压缩包准备数据 | `python scripts/prepare_dataset.py --dataset-dir RadioMapSeer/ --archive /root/lanyun-tmp/RadioUNet/RadioMapSeer.tar.gz` | 通过，解压到 `RadioMapSeer/` 并自动触发数据审计。 |
| 显式数据审计 | `python scripts/validate_dataset.py --dataset-dir RadioMapSeer/` | 通过，报告写入 `reports/dataset_validation/`。 |
| Stage 0 原始样本图 | `python scripts/make_figures.py --config configs/c_dpm_thr2.yaml --split test --smoke --limit 1 --output-dir reports/stage0_samples` | 通过，生成 `reports/stage0_samples/c_dpm_thr2_test_0000.png`。 |
| firstU smoke 训练 | `python scripts/train.py --config configs/c_dpm_thr2.yaml --phase firstU --smoke` | 通过，训练样本 2，验证样本 2，保存 checkpoint。 |
| smoke 评估 | `python scripts/evaluate.py --config configs/c_dpm_thr2.yaml --checkpoint reports/c_dpm_thr2/20260506_180913/checkpoints/firstU.pt --smoke` | 通过，评估样本 2，指标写入 `reports/c_dpm_thr2/metrics.json`。 |
| checkpoint 预测图 | `python scripts/make_figures.py --config configs/c_dpm_thr2.yaml --checkpoint reports/c_dpm_thr2/20260506_180913/checkpoints/firstU.pt --smoke --limit 1` | 通过，生成 `reports/figures/c_dpm_thr2_test_0000.png`。 |

## 关键证据

- 数据目录: `RadioMapSeer/`，本地大小约 4.0G。
- 必要 PNG 数量:
  - `png/buildings_complete`: 701
  - `png/antennas`: 56080
  - `gain/DPM`: 56080
  - `gain/IRT2`: 56080
  - `gain/IRT4`: 1402
- 样本读取: `map=1, tx=0` 的 buildings、antenna、DPM、IRT2、IRT4 均为 `256x256`。
- loader smoke batch: `inputs=[2, 2, 256, 256]`，`targets=[2, 1, 256, 256]`。
- firstU smoke 训练:
  - train loss: 0.09924772381782532
  - val loss: 0.09922465682029724
  - checkpoint: `reports/c_dpm_thr2/20260506_180913/checkpoints/firstU.pt`
- smoke 评估:
  - samples: 2
  - firstU mse: 0.09922465682029724
  - firstU nmse: 0.9990440011024475
  - firstU rmse: 0.3149994552698421

## 修复说明

- `src/radiounet/factory.py`: 将 YAML 中解析成布尔值的 `yes/no` 规范化成官方 loader 期待的字符串，避免 `cars_input: no` 被误判为启用 cars 输入。
- `src/radiounet/data.py`: 对 `ToTensor()` 路径使用显式 HWC/HW 到 CHW float tensor 转换，避免 2 通道真实 PNG 输入被 PIL 路径扩成 3 通道。

