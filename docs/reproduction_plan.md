# RadioUNet 复现计划

本项目目标是复现以下论文：

Ron Levie, Cagkan Yapar, Gitta Kutyniok, and Giuseppe Caire, "RadioUNet: Fast Radio Map Estimation with Convolutional Neural Networks," IEEE Transactions on Wireless Communications, 2021.

本地参考材料保存在 `reference/`。早期 Word/Markdown 草稿已移除，因为其中混合了有价值的高层总结和未经验证的复现假设。

## 最终版审计结论

从“复现计划”本身的质量看，当前文档已经可以作为最终版主计划使用。它明确了事实来源、复现标准、实验优先级、阶段交付物、核心配置、指标范围和当前工程差距，足以指导后续实现和实验执行。

当前仓库已经具备 Stage 0/Stage 1 的基础命令入口：数据准备、数据校验、训练、评估和制图脚本均已接入配置、loader、模型与指标。完整实验仍依赖本地 `RadioMapSeer/` 数据集；在数据集未准备好之前，只能完成语法、导入、模型前向和缺数据失败路径检查。

计划质量评价：

- 覆盖范围合理：先做数据和 loader 校验，再做干净 DPM 基线，最后推进 RadioUNet_S、IRT4 迁移和鲁棒性实验，顺序符合复现风险。
- 事实依据清楚：把论文 PDF、论文源码、官方代码和数据集入口列为权威依据，降低了凭记忆复现的风险。
- 阶段边界明确：每个阶段都有目标、设置和交付物，适合拆分实现任务和实验任务。
- 工程约束明确：保留 `reference/` 只读、迁移代码放入 `src/radiounet/`、优先保证忠实度，这些约束是合理的。
- 审计信息诚实：文档区分了“代码链路已实现”和“真实数据实验尚未运行”，避免把 smoke 能力误写成论文指标复现。

建议在最终版计划中继续保留以下待补项，作为执行检查清单，而不是作为“计划未完成”的阻塞项：

- 环境说明：Python、PyTorch、torchvision、CUDA、系统依赖和安装命令；
- 数据说明：RadioMapSeer 下载、解压、目录校验、文件数量期望值和不纳入 git 的路径策略；
- 可执行命令：每个阶段的训练、评估、制图、日志保存和 checkpoint 保存命令已具备基础入口，后续需用真实数据跑通并固化实测命令；
- 指标定义：MSE、NMSE、RMSE、dB RMSE 的精确公式、归一化范围和统计粒度；
- 结果验收：Stage 1 的最小可接受误差范围、要复现的论文表格/图编号、允许偏差和失败排查方式；
- 随机性控制：全局 seed、DataLoader worker seed、CUDA 确定性设置、稀疏采样固定策略；
- 产物规范：当前脚本会保存 config 快照、checkpoint、metrics、图像和 git commit，后续需在完整训练后审计命名与归档策略是否足够稳定。

审计结论：这份计划可以定为最终版复现计划；后续应基于它补实现、补命令和补实测结果，而不是频繁改动复现范围。

## 复现标准

目标不只是跑通一个示例，而是形成可追踪的复现链路。每个报告结果都必须能追溯到：

- 对应复现的论文章节、表格或图；
- 精确的数据集划分；
- 精确的模型变体；
- 版本化配置文件；
- 已保存的 checkpoint；
- 评估指标；
- 生成的图像；
- 运行实验时的 git commit。

## 权威依据

以下材料作为复现的事实来源：

- 论文 PDF：`reference/RadioUNet_1911.09002.pdf`
- 论文源码：`reference/RadioUNet_paper_source/RadioUNet_paper_ver3.tex`
- 官方代码：`reference/RadioUNet/`
- 官方数据集入口：https://radiomapseer.github.io

## 必须保留的论文事实

- RadioMapSeer 包含 700 张地图。
- 每张完整地图包含 80 个发射机位置。
- Radio map 是稠密的 `256 x 256` 网格，每个像素对应 1 米。
- 粗仿真包括 DPM 和 IRT2。
- 每张地图前两个发射机位置提供更高精度的 IRT4 仿真。
- 官方划分使用 seed 42 进行确定性 shuffle，然后按 map 索引范围划分：
  - train：0 到 500；
  - validation：501 到 600；
  - test：601 到 699。
- 干净基线输入为建筑物图和发射机位置图。
- RadioUNet_C 不使用 radio-map 测量值。
- RadioUNet_S 额外使用稀疏 pathloss 测量值。
- 官方 notebook 在最简单实验中使用阈值 `0.2`。
- 官方实现使用 WNet：第一个 U-Net 预测 radio map，第二个 U-Net 改善或适配第一个 U-Net 的输出。
- 论文训练设置包括 Adam、学习率 `1e-4`、每个 U-Net 50 个 epoch、batch size 15，并按验证集误差选择模型。

## 实验阶梯

### Stage 0：数据集和 loader 校验

目标：证明本地 RadioMapSeer 副本符合预期目录结构，并且所有 loader 路径可用。

任务：

- 在 git 跟踪目录之外下载 RadioMapSeer，推荐路径为 `RadioMapSeer/`。
- 校验必要目录：
  - `png/buildings_complete/`
  - `png/antennas/`
  - `gain/DPM/`
  - `gain/IRT2/`
  - `gain/IRT4/`
  - 可选的 cars 和 missing-building 目录。
- 渲染一个样本面板：
  - building map；
  - Tx map；
  - DPM label；
  - IRT2 label；
  - 可用时包含 IRT4 label。
- 确认张量形状、通道数、数值范围和阈值变换结果。

当前仓库状态：

- `scripts/prepare_dataset.py` 已提供自动下载、解压和校验入口；若 Google Drive 自动下载失败，会给出手动下载路径。
- `scripts/validate_dataset.py` 已检查必要目录、png 数量、指定样本文件、图片尺寸、值域，并写出 JSON/Markdown 校验报告。
- 样本预测可视化由 `scripts/make_figures.py` 生成；Stage 0 若只想看原始样本，可不传 checkpoint。

交付物：

- 数据集校验日志；
- 样本可视化图；
- 缺失目录或异常文件的说明。

### Stage 1：干净 DPM 基线

目标：高保真复现官方最简单路径。

配置：`configs/c_dpm_thr2.yaml`

对应设置：

- `RadioUNet_C`
- 完整建筑物图；
- 不使用稀疏测量；
- DPM target；
- 阈值 `0.2`；
- 官方 notebook：`RadioWNet_c_DPM_Thr2.ipynb`。

训练流程：

1. 训练第一个 U-Net。
2. 在 validation 和 test 上评估第一个 U-Net。
3. 冻结第一个 U-Net，训练第二个 U-Net，匹配官方 WNet 行为。
4. 分别评估两个输出。

当前仓库状态：

- `configs/c_dpm_thr2.yaml` 已定义核心配置。
- `src/radiounet/data.py` 和 `src/radiounet/models.py` 已从官方 loader/model 迁移。
- `scripts/train.py` 已接入配置、官方迁移 loader/model、firstU/secondU 阶段、smoke 子集、checkpoint 和训练历史保存。
- `scripts/evaluate.py` 已接入 checkpoint、test/val/train split、MSE、NMSE、RMSE 和 dB 口径输出。
- 当前尚未用真实 RadioMapSeer 数据集运行 smoke test，因此训练/评估链路仍需真实数据验证。

交付物：

- 第一个 U-Net 阶段 checkpoint；
- 第二个 U-Net 阶段 checkpoint；
- MSE、NMSE、RMSE；
- 代表性预测面板；
- 单张地图推理耗时。

### Stage 2：带稀疏测量的 RadioUNet_S

目标：复现 sample-assisted 版本。

设置：

- 输入通道：建筑物图、Tx 图、稀疏测量图；
- 稀疏样本数量按论文范围随机抽取；
- 条件允许时，与 RadioUNet_C 和插值基线比较。

交付物：

- 指标随样本数量变化的曲线；
- 标注样本位置的预测面板；
- 与干净基线的比较。

### Stage 3：迁移和鲁棒性实验

目标：复现论文中更难的部分。

设置：

- 缺失建筑物；
- DPM/IRT2 随机混合仿真；
- 含车辆仿真；
- 将车辆作为输入通道；
- 稀疏 IRT4 适配。

交付物：

- IRT4 zero-shot 指标；
- 稀疏 IRT4 adaptation 指标；
- 论文关键表格的选定行；
- 与论文结果不一致时的原因说明。

## 工程计划

`reference/` 目录是只读参考材料。复现代码放在 `src/radiounet/` 下。

初始迁移：

- `src/radiounet/data.py` 来源于官方 `lib/loaders.py`。
- `src/radiounet/models.py` 来源于官方 `lib/modules.py`。

第一优先级是复现忠实度。重构应保持小范围，并通过测试或与参考代码的等价性检查支撑。

计划中的命令入口：

- `scripts/validate_dataset.py`
- `scripts/train.py`
- `scripts/evaluate.py`
- `scripts/make_figures.py`

当前差距：

- 尚未建立 `requirements.txt` 或等价环境文件。
- 尚未下载 RadioMapSeer，因此缺少真实 smoke test、完整 Stage 1 训练和实测指标。
- 尚未把 Stage 1 的实测结果与官方 notebook/论文表格做数值对照。

## 指标

至少报告：

- 所有像素上的 MSE；
- 与官方 notebook 相同分母定义的 NMSE；
- 所有像素上的 RMSE；
- 论文使用 dB 约定时转换后的 RMSE；
- 单张地图推理耗时。

每个指标都要记录其计算对象：

- 第一个 U-Net 输出；
- 第二个 U-Net 输出；
- 稠密 DPM/IRT2 label；
- 稠密 IRT4 label；
- 稀疏 IRT4 样本点。

## 最终版验收清单

在本文件可以被标记为最终版前，应完成以下检查：

- `python scripts/prepare_dataset.py --dataset-dir RadioMapSeer/` 能下载或提示手动下载数据集。
- `python scripts/validate_dataset.py --dataset-dir RadioMapSeer/` 能输出完整数据集校验结果。
- Stage 0 能生成至少一个样本可视化面板。
- `python scripts/train.py --config configs/c_dpm_thr2.yaml --smoke` 能完成 smoke test。
- `python scripts/train.py --config configs/c_dpm_thr2.yaml --phase both` 能完成完整 Stage 1 训练。
- `python scripts/evaluate.py --config configs/c_dpm_thr2.yaml --checkpoint <path>` 能输出可复算指标。
- 每次实验都保存 config 快照、checkpoint、metrics、图像和 git commit。
- 文档中列出的每个命令都在当前仓库中实际可运行。
- Stage 1 结果与官方 notebook 或论文表格存在可解释的一致性。

## 立即下一步

1. 准备 RadioMapSeer 数据集：优先运行 `python scripts/prepare_dataset.py --dataset-dir RadioMapSeer/`。
2. 运行数据审计：`python scripts/validate_dataset.py --dataset-dir RadioMapSeer/`。
3. 运行 tiny subset smoke test，验证训练循环、checkpoint、指标文件和样本图。
4. 在 smoke test 通过后运行完整 Stage 1。
5. 根据 Stage 1 实测结果更新“最终版审计结论”和论文对照表。
