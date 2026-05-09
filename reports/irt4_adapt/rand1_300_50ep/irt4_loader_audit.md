# IRT4 loader audit

- 审计对象：`RadioUNet_s_sprseIRT4` sparse adaptation 路径。
- 本地官方参考：`reference/RadioUNet/lib/loaders.py`；当前复现 loader：`src/radiounet/data.py`。
- 配置：`configs/s_irt4_adapt_rand1_300.yaml`，loader `RadioUNet_s_sprseIRT4`，simulation `IRT4`，num_tx `2`。
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`。
- sparse 数据池：每张 map 固定 `data_samples=300`；输入 sparse samples 从该池内抽取 `1..300`。
- sparse 与 target 对齐最大误差：`0.0`。

结论：IRT4 输入、target 和 sparse sample 均来自 IRT4 路径；train/val/test 都限制为前 2 个 Tx，可以开始 secondU-only adaptation。
