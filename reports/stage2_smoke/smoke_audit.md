# Stage 2 smoke 审计：RadioUNet_S 最小真实闭环

## 目标

本轮不启动 full train。目标是先解决 Stage 1 遗留的 NMSE 口径问题，并把 `RadioUNet_s` sample-assisted 真实数据链路跑通到 smoke training/evaluation。

## 1. NMSE 口径审计

命令：

```bash
python scripts/audit_nmse_denominator.py --config configs/c_dpm_thr2.yaml --split test
```

输出：

- JSON：`reports/stage2_smoke/nmse_denominator_audit.json`
- 报告：`reports/stage2_smoke/nmse_denominator_audit.md`

关键结果：

| 项目 | 数值 |
| --- | ---: |
| 当前 test split `mean(MSE(target, 0))` | `0.0543188367` |
| 当前 test split global pixel mean | `0.0543188365` |
| 官方 notebook firstU 反推分母 | `0.0529930182` |
| 官方 notebook secondU 反推分母 | `0.0529244306` |
| 论文表格 `RMSE^2/NMSE` 反推分母 | `0.0533333333` |

Stage 1 原报告中用 `平均 MSE / 平均 NMSE` 反推的 `0.0435..0.0438` 不是 test split 的真实 target energy，而是比值平均后的有效分母。按论文公式用全局 target energy 重算：

| 输出头 | Stage 1 MSE | 原 Stage 1 NMSE | 全局分母 NMSE |
| --- | ---: | ---: | ---: |
| firstU | `0.0004726781` | `0.0107978450` | `0.0087019184` |
| secondU | `0.0004197670` | `0.0096473684` | `0.0077278349` |

结论：Stage 1 遗留问题是 NMSE 统计粒度/比值平均口径差异，不是数据版本差异，也不是 threshold=0.2 差异。后续报告应优先使用全局平方误差除以全局 target energy 的 `global_nmse`；保留 batch-mean `nmse` 时必须明确标注。

## 2. RadioUNet_S loader 审计

命令：

```bash
python scripts/audit_s_loader.py --config configs/s_dpm_thr2.yaml --split train --smoke
```

输出：

- JSON：`reports/stage2_smoke/s_loader_audit.json`
- 报告：`reports/stage2_smoke/s_loader_audit.md`

关键结果：

- loader：`RadioUNet_s`
- batch length：`2`，即当前 DPM S loader 返回 `(inputs, targets)`
- inputs shape：`[2, 3, 256, 256]`
- targets shape：`[2, 1, 256, 256]`
- 三个输入通道：`buildings`, `Tx`, `sparse samples`
- sparse 非零数量：`[229, 35]`，范围 `35..229`
- sparse 非零值域：`4.750000..157.250000`
- target 值域：`0.000000..254.750000`
- sparse 非零位置与 target 最大绝对误差：`0.0000000000`

结论：`RadioUNet_s` 的 sparse samples 是 threshold 后并乘以 256 的 target 采样值，非零点与 target 完全对齐。

## 3. Stage 2 配置

新增配置：`configs/s_dpm_thr2.yaml`

关键设置：

- `loader: RadioUNet_s`
- `simulation: DPM`
- `city_map: complete`
- `threshold: 0.2`
- `model.inputs: 3`
- `target_scale: 256`

该配置只作为 smoke 入口，不声明 full train 结果。

## 4. RadioUNet_S smoke training

命令：

```bash
python scripts/train.py --config configs/s_dpm_thr2.yaml --phase firstU --smoke
```

本轮有效 run：

- run dir：`reports/s_dpm_thr2/20260507_004021`
- checkpoint：`reports/s_dpm_thr2/20260507_004021/checkpoints/firstU.pt`
- train samples：`2`
- val samples：`2`
- train loss：`6405.73583984375`
- val loss / best val：`6404.330078125`

训练循环已兼容 `(inputs, targets)` 和 `(inputs, targets, samples)` batch。

## 5. Smoke evaluation

命令：

```bash
python scripts/evaluate.py --config configs/s_dpm_thr2.yaml --checkpoint reports/s_dpm_thr2/20260507_004021/checkpoints/firstU.pt --smoke --output reports/stage2_smoke/s_firstU_smoke_metrics.json
```

输出：`reports/stage2_smoke/s_firstU_smoke_metrics.json`

关键结果：

| 输出头 | samples | MSE | raw MSE | NMSE | global NMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| firstU | `2` | `0.0978410095` | `6412.1083984375` | `0.9981825948` | `0.9981825656` |
| secondU | `2` | `0.0979058370` | `6416.35693359375` | `0.9988439679` | `0.9988439414` |

该评估只证明真实 sample-assisted 数据链路和模型 forward/evaluate 闭环通过，不代表训练收敛或论文指标。

## 完成审计

| 要求 | 证据 |
| --- | --- |
| 统计当前 test split target energy | `reports/stage2_smoke/nmse_denominator_audit.md`，7920 samples，`0.0543188367` |
| 对比当前 firstU/secondU、官方 notebook、论文表格分母 | 同上，包含三类反推分母和 global NMSE 重算 |
| 明确 NMSE 结论 | 本报告第 1 节：统计粒度/比值平均口径差异 |
| 使用 `RadioUNet_s` 读取真实样本 | `reports/stage2_smoke/s_loader_audit.md` |
| 检查输入 shape `[B, 3, 256, 256]` | `inputs shape: [2, 3, 256, 256]` |
| 检查三通道语义 | `buildings`, `Tx`, `sparse samples` |
| 检查 sparse 数量、值域、target 对齐 | 非零数量 `35..229`，值域 `4.75..157.25`，对齐误差 `0` |
| 新增 Stage 2 smoke 配置 | `configs/s_dpm_thr2.yaml` |
| 跑真实数据 tiny subset smoke training | `reports/s_dpm_thr2/20260507_004021/firstU_history.json` |
| 兼容二元/三元 batch | `scripts/train.py`, `scripts/evaluate.py`, `scripts/make_figures.py` 均有 `unpack_batch` |
| 输出 Stage 2 smoke 审计报告 | 本文件 |

结论：Stage 2 最小真实闭环已通过。下一步才适合讨论是否跑 `RadioUNet_S` full train。
