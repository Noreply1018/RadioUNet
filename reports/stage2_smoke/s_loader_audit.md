# Stage 2 前置审计：RadioUNet_S loader

## 数据 shape

- config: `configs/s_dpm_thr2.yaml`
- split: `train`
- smoke: `True`
- batch length: `2`
- inputs shape: `[2, 3, 256, 256]`
- targets shape: `[2, 1, 256, 256]`

## 通道和值域

| 通道 | min | max | mean | nonzero |
| --- | ---: | ---: | ---: | ---: |
| buildings | 0.000000 | 0.996094 | 0.099144 | 13046 |
| Tx | 0.000000 | 0.996094 | 0.000015 | 2 |
| sparse_samples | 0.000000 | 157.250000 | 0.162651 | 264 |
| target | 0.000000 | 254.750000 | 68.837494 | 116329 |

## sparse samples

- 每张图 sparse 非零数量范围: `35` 到 `229`
- 每张图 sparse 非零数量列表: `[229, 35]`
- sparse 非零位置与 target 最大绝对误差: `0.0000000000`
- sparse 非零值域: `4.750000` 到 `157.250000`

## 结论

RadioUNet_s 当前真实 batch 满足 [B, 3, 256, 256]，三通道依次为 buildings、Tx、sparse samples；sparse samples 直接来自 threshold 后并乘以 256 的 target，在非零采样点与 target 完全对齐。该 loader 返回二元 batch `(inputs, targets)`；训练循环已兼容二元和三元 batch。
