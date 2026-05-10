# 最后一步计划：按论文全矩阵完整复现 RadioUNet

## 当前状态

当前仓库已经完成一条可审计主线：

- RadioUNet_C / DPM / clean map baseline。
- RadioUNet_S / DPM / random 1..300 sparse measurements。
- DPM -> IRT4 sparse adaptation。
- missing buildings 0/1/2/4 robustness 主线。

总审计 gate 已通过，但这还不是论文全矩阵完整复现。要达到“论文全矩阵完整复现”，最后一步必须把当前 reduced reproduction 扩展为覆盖论文所有主要实验轴、图表和对比方法的矩阵复现。

## 总目标

产出一份可以独立支撑“RadioUNet 论文全矩阵已复现”的最终交付：

- 每个论文实验单元都有 config、运行命令、checkpoint hash、metrics、rerun metrics、manifest、图表和审计 gate。
- 每个图表都有可复现脚本生成，数值能追踪到具体 run。
- 每个差异都明确标注为 paper-faithful、implementation-faithful、reduced、ablation 或 not reproduced。
- 最终总表能对齐论文 Fig. 8、Fig. 9、Fig. 10、state-of-the-art comparison 和 appendix/补充图表口径。
- 所有新增产物完成 git commit，工作区最终干净。

## 必须补齐的实验矩阵

### 1. Coarse simulation 全矩阵

目标：补齐论文中 coarse simulation 对 RadioUNet_C / RadioUNet_S 的主要训练与测试轴。

必须覆盖：

- `C / DPM / no cars / clean map`
- `S / DPM / no cars / clean map / random 1..300 input samples`
- `C / IRT2 / no cars / clean map`
- `S / IRT2 / no cars / clean map / random 1..300 input samples`
- `C / random coarse simulation / no cars / clean map`
- `S / random coarse simulation / no cars / clean map / random 1..300 input samples`

交付：

- 新增或确认 configs：`c_irt2_*`、`s_irt2_*`、`c_rand_*`、`s_rand_*`。
- 每个 run 都训练 firstU + secondU 50 epoch。
- 每个 run 都保存 firstU/secondU metrics、rerun metrics、history、checkpoint manifest、8 张 qualitative figures。
- 新增 `reports/full_matrix/coarse_simulation_audit.md/json`。

验收：

- 所有 run 的 test split、target scale、simulation source、cars flag、sample policy 均由审计脚本检查。
- secondU 不劣于 firstU，或若不成立必须在报告中解释并标为失败/异常。
- random coarse simulation 的采样权重、DPM/IRT2 混合语义必须可审计。

### 2. IRT4 transfer 全矩阵

目标：复现论文 Table/Fig. 8 中 zero-shot 与 sparse adaptation 的完整 transfer 结论。

必须覆盖：

- source coarse target：`DPM`、`IRT2`、`random coarse simulation`。
- model：`RadioUNet_C`、`RadioUNet_S`。
- transfer setting：`zero-shot IRT4`、`adaptation to sparse IRT4`。
- sparse policy：
  - C：300 receivers per transmitter for sparse loss。
  - S：600 receiver pool，输入随机 1..300，loss on full 600 sparse points。

交付：

- 新增或确认 configs：`*_irt4_zeroshot_*`、`*_irt4_adapt_*`，覆盖 DPM/IRT2/random 三类 source。
- 新增 `scripts/run_full_matrix_irt4.py` 或等价批处理入口。
- 新增 `scripts/audit_full_matrix_irt4.py`。
- 新增 `reports/full_matrix/irt4_transfer_matrix.md/json`。
- 新增 IRT4 transfer 总图，至少包含 dense MSE/NMSE、sparse MSE/NMSE、RMSE dB。

验收：

- IRT4 只使用 Tx 0/1 的限制必须在 config 和 audit 中固定。
- adaptation run 必须证明 init checkpoint 来自对应 source firstU。
- sparse receiver pool hash、input subset policy、loss mask policy 必须审计。
- zero-shot 与 adaptation 必须分栏报告，不能混口径。

### 3. Cars 场景完整复现

目标：补齐论文明确涉及的 cars simulation、cars input，以及官方 notebook `RadioWNet_s_DPMcars_carInput_Thr2.ipynb` 对应实验。

必须覆盖：

- DPM with cars。
- IRT2 with cars。
- IRT4 with cars，如数据集可用则纳入 transfer/eval。
- RadioUNet_S with measurement input。
- cars map 作为输入 channel 的设置。
- no-cars input vs cars-input 对照。

交付：

- 新增 configs：`s_dpmcars_carinput_*`、`s_irt2cars_carinput_*`、必要的 `c_*cars*` baseline。
- 扩展 loader/factory 审计，确认 `cars_simulation` 与 `cars_input` 同时正确指向 dataset。
- 新增 `reports/full_matrix/cars_audit.md/json`。
- 新增 cars qualitative figures，至少复现论文示例图对应的 target/pred/input cars 对照。

验收：

- 审计必须证明 cars target 来自 cars simulation，而不是 clean target。
- 审计必须证明 cars input channel 非空、与 map/tx 对齐。
- 如果 IRT4 cars 文件缺失，必须将该单元标为 dataset-unavailable，并给出文件级证据。

### 4. Missing buildings 全矩阵与 fixed receiver 对照

目标：把当前 Stage 4 从 implementation-faithful 主线扩展到论文级 missing-building robustness。

必须覆盖：

- missing buildings：`0/1/2/4`。
- source coarse target：`DPM`、`IRT2`、`random coarse simulation`。
- model：`C`、`S`。
- transfer：`zero-shot`、`sparse adaptation`。
- receiver policy：
  - official-loader-faithful receiver mask。
  - paper-faithful fixed receiver mask 对照。

交付：

- 新增 fixed receiver mask loader 或 wrapper，保证同一 map/tx 跨 missing setting receiver mask 不变。
- 新增 configs：`*_missing{0,1,2,4}_fixedrx_*`。
- 新增 `reports/full_matrix/missing_buildings_matrix.md/json`。
- 新增 curves：missing count vs dense/sparse NMSE，分 source/model/transfer/receiver policy。

验收：

- 同一 map/tx 下 target IRT4 hash 和 Tx hash 跨 missing setting 不变。
- fixed receiver policy 下 receiver mask hash 跨 missing setting 不变。
- official-loader-faithful 与 fixed receiver 结论必须分开报告。
- 当前已有 dirty provenance 的历史 Stage 4 只能作为 archived evidence；全矩阵最终表必须使用 clean provenance run。

### 5. Sample count 曲线与 state-of-the-art 对比

目标：补齐论文中 RadioUNet_S 与 RBF、tensor completion、tomography、MLP 的测量点数量曲线对比。

必须覆盖：

- sample counts：至少 `10/20/50/100/200/300`，如论文图使用更多点则按论文补齐。
- RadioUNet_S。
- RBF interpolation。
- tensor completion。
- tomography。
- one-step MLP / Docomo-style baseline。
- RadioUNet_C horizontal baseline。

交付：

- 新增 `src/radiounet/baselines.py` 或 `scripts/baselines/*.py`。
- 新增 `scripts/run_state_of_art_baselines.py`。
- 新增 `scripts/audit_state_of_art_baselines.py`。
- 新增 `reports/full_matrix/state_of_art_comparison.md/json/png`。

验收：

- 每个 baseline 必须记录运行时间、样本数量、是否使用 building post-processing、是否按 map 单独优化。
- RadioUNet 与 baseline 的输入信息必须在报告中并列表明，避免不公平对比。
- 曲线必须能从 metrics JSON 重新生成。

### 6. WNet / model size / threshold 矩阵

目标：补齐论文关于 WNet retrospective improvement、模型大小、pathloss threshold 的性能图。

必须覆盖：

- C model 不同 size。
- with secondU vs without secondU。
- threshold 至少覆盖论文图中使用的多个 pathloss threshold。
- 400/100/200 split sanity check，如论文图要求则补齐。

交付：

- 新增模型 size 配置组。
- 新增 split 配置和 split audit。
- 新增 `reports/full_matrix/wnet_size_threshold_audit.md/json/png`。

验收：

- 每个 size 的参数量、architecture hash、输入输出 shape 必须记录。
- threshold 变换必须审计 target preprocessing，而不只是改报告标签。
- 400/100/200 split 与原 500/100/100 split 的 test overlap 必须文件级证明。

### 7. 论文图表级汇总

目标：把所有实验矩阵汇总成论文图表级交付，而不是分散 run 目录。

交付：

- `reports/full_matrix/paper_table_reproduction.md`
- `reports/full_matrix/paper_table_reproduction.json`
- `reports/full_matrix/fig8_radio_unet_performance.png`
- `reports/full_matrix/fig9_wnet_missing_buildings.png`
- `reports/full_matrix/fig10_state_of_art_comparison.png`
- `docs/full_matrix_reproduction_summary.md`

每张图表必须包含：

- 对应论文图/表名。
- 本仓库复现图路径。
- 参与 run 列表。
- 与论文数值差异。
- gate。
- residual risk。

## 执行顺序

1. 冻结当前主线产物
   - 当前 `reports/final_reproduction_audit.*` 作为 reduced reproduction baseline 保留。
   - 新增 `reports/full_matrix/`，后续全矩阵产物全部进入该目录。
   - 不覆盖历史主线报告，避免口径混淆。

2. 先补 loader/config 能力
   - IRT2 loader/config。
   - random coarse simulation loader/config。
   - cars simulation/input。
   - fixed receiver mask。
   - model size / threshold / split 参数化。

3. 先做 smoke audit，再启动长训练
   - 每个新实验轴先跑 smoke。
   - smoke 必须检查数据路径、target hash、input channel、sample policy、split size。
   - smoke 全通过后才启动 50 epoch full runs。

4. 分批训练与评估
   - Batch A：coarse simulation matrix。
   - Batch B：IRT4 zero-shot matrix。
   - Batch C：IRT4 sparse adaptation matrix。
   - Batch D：cars matrix。
   - Batch E：missing buildings fixed receiver matrix。
   - Batch F：baselines 与 model size/threshold。

5. 每批结束立即审计
   - rerun eval，要求 max numeric diff 为 0。
   - checkpoint hash 与 manifest 对齐。
   - git dirty provenance 必须 clean；否则该批作废重跑或降级为 residual evidence。

6. 最终汇总
   - 生成 `reports/full_matrix/final_full_matrix_audit.md/json`。
   - 更新 `docs/full_matrix_reproduction_summary.md`。
   - 明确列出 fully reproduced、implementation-faithful、failed、not available。
   - 最终 git commit。

## 最终 gate

全矩阵完成必须同时满足：

- `reports/full_matrix/final_full_matrix_audit.json` 中 `gate.pass=True`。
- 所有论文主图/主表都有本仓库复现版本。
- 所有新增 run 均有 clean provenance。
- 所有 checkpoint/log/dataset 未进入 git。
- 所有 metrics 可由 config + checkpoint + eval script 重跑得到 bitwise-identical JSON，非确定项必须解释。
- `git status --short --untracked-files=all` 为空。

## 不可接受的收尾方式

- 只把当前 reduced reproduction 改名为 full reproduction。
- cars、IRT2、random coarse simulation、state-of-the-art baselines 缺失但不标注。
- Stage 4 继续只用 official-loader receiver mask，却宣称 fixed receiver paper-faithful。
- 只截图论文图，不提供可重跑 metrics。
- checkpoint、dataset、cache 或 tensorboard log 进入 git。

## 预计成本

- loader/config/smoke 补齐：1-2 天。
- 全矩阵训练与评估：2-5 天，取决于 GPU 并行度。
- state-of-the-art baselines：1-3 天。
- 图表级汇总与最终审计：1-2 天。

总计约 5-12 天。若发现数据集缺少 IRT4 cars 或官方 baseline 细节不可复原，对应单元必须降级为 dataset-unavailable / implementation-faithful，并在最终审计中保留文件级证据。
