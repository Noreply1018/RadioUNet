# Stage 2 前置审计：NMSE 分母口径

## 当前 test split target energy

- config: `configs/c_dpm_thr2.yaml`
- split: `test`
- samples: `7920`
- `mean(MSE(target, 0))`: `0.0543188367`
- global pixel mean: `0.0543188365`
- per-sample range: `0.0039388747` 到 `0.1413982064`

## 分母反推对照

| 来源 | firstU 分母 | secondU 分母 | 备注 |
| --- | ---: | ---: | --- |
| 当前 firstU/secondU 评估 | 0.0437752243 | 0.0435110367 | 由 Stage 1 test MSE/NMSE 反推。 |
| 官方 notebook | 0.0529930182 | 0.0529244306 | 由官方 notebook DPM 输出 MSE/NMSE 反推。 |
| 论文表格 | - | 0.0533333333 | 由 RMSE^2/NMSE 反推，表格只给最终方法行。 |

## 按全局 target energy 重算的 Stage 1 NMSE

| 输出头 | Stage 1 MSE | 原 Stage 1 NMSE | 全局分母 NMSE |
| --- | ---: | ---: | ---: |
| firstU | 0.0004726781 | 0.0107978450 | 0.0087019184 |
| secondU | 0.0004197670 | 0.0096473684 | 0.0077278349 |

## 结论

当前 test split 直接复算的 `MSE(target, 0)` 为 `0.0543`，与官方 notebook 反推分母 `0.0530` 和论文表格反推分母 `0.0533` 基本一致，因此不是数据版本差异，也不是 threshold=0.2 变换差异。Stage 1 报告中用 `平均 MSE / 平均 NMSE` 反推得到的 `0.0435` 到 `0.0438` 只是“比值平均后的有效分母”，不是 test split 的真实 target energy。按论文公式使用全局分母重算后，secondU NMSE 为 `0.0077278349`，与官方 notebook 的 `0.007728` 和论文表格的 `0.0075` 对齐。结论：遗留问题是 NMSE 统计粒度/比值平均口径差异；后续报告应优先使用全局平方误差和全局 target energy 的比值，并保留 batch-mean NMSE 时明确标注。

## 证据来源

- 当前 target energy：本脚本直接遍历当前仓库 `RadioMapSeer/` 的 `test` split target。
- 当前 firstU/secondU：`docs/stage1_c_dpm_thr2_audit.md` 已记录的完整 Stage 1 test metrics。
- 官方 notebook：`reference/RadioUNet/RadioWNet_c_DPM_Thr2.ipynb` 的 DPM threshold=0.2 输出。
- 论文表格：`reference/RadioUNet_paper_source/RadioUNet_paper_ver3.tex` 中 `accurate map, deterministic simulation with no cars` 行。
