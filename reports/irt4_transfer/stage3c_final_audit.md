# Stage 3C IRT4 transfer 最终审计

## 结论分区
- paper-faithful 主线：`paper_faithful_mainline`，S / pool600 / 输入 1..300 / loss 在 pool600 sparse mask 上计算。
- dense-loss pilot：`dense_loss_pilot`，保留为旧结果，不作为 paper-faithful 结论。
- ablation：`pool300_sparse_ablation`，用于隔离 sparse-loss 语义修复与 600-pool 对齐。
- C baseline：`c_sparse_baseline`。
- zero-shot baselines：`s_zero_shot`、`c_zero_shot`。

## IRT4 test 指标
| run | 类别 | 样本数 | dense MSE | dense global NMSE | sparse MSE | sparse global NMSE | rerun diff |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `paper_faithful_mainline` | paper-faithful | 198 | 0.0007609739 | 0.0147164114 | 0.0006030457 | 0.0116471360 | 0.0 |
| `pool300_sparse_ablation` | ablation | 198 | 0.0008379128 | 0.0162043262 | 0.0005823452 | 0.0110996453 | 0.0 |
| `dense_loss_pilot` | dense-loss pilot | 198 | 0.0007365961 | 0.0142449718 | 0.0006065389 | 0.0115607829 | 0.0 |
| `c_sparse_baseline` | C baseline | 198 | 0.0010485411 | 0.0202776493 | 0.0010080370 | 0.0192134387 | 0.0 |
| `s_zero_shot` | zero-shot baseline | 198 | 0.0009654228 | 0.0186702326 | 0.0008533435 | 0.0162649403 | 0.0 |
| `c_zero_shot` | zero-shot baseline | 198 | 0.0014888853 | 0.0287934302 | 0.0015274379 | 0.0291133501 | 0.0 |

## 论文语义对齐
- IRT4 only first two Tx：`True`。
- RadioUNet_S random 1..300 input measurements：`True`。
- S 使用 600 sparse receivers，loss on all 600：`True`。
- adaptation second UNet：`True`。

## 关键限制说明
- 600 receivers 在当前 loader 语义下表示“随机采样 600 个坐标”，不是严格 600 个唯一像素；重复坐标会折叠，所以主线 loss mask 唯一非零像素为 `590..600`，test 平均 `597.18`。
- S 输入随机点数配置为 `np.random.randint(1, 301)`，语义是 1..300 个采样坐标；由于坐标重复，唯一输入像素审计为 `{'train': '1..299', 'val': '4..298', 'test': '5..296'}`，不保证每个样本唯一像素数也覆盖 1..300。
- dense-loss pilot 的 dense MSE `0.0007365961` 略低于 paper-faithful 主线 `0.0007609739`，但它使用 dense full-map IRT4 target 监督，不能作为论文对齐结论。
- `configs/s_irt4_adapt_rand1_300.yaml` 是 archived dense-loss pilot 配置；当前 `scripts/train.py` 会拒绝 IRT4 sparse adaptation 使用 `loss_mode: dense_mse`，因此它不是当前可复跑主线。

## 判定
- 当前代码真正按 sparse IRT4 measurements 训练：`True`。
- S 600 pool / input 1..300 / sparse loss 成立：`True`。
- 旧 dense-loss pilot 已降级：`True`。
- paper-faithful Stage 3C 优于 S zero-shot：`True`。
- S paper-faithful 优于 C sparse baseline：`True`。
- 可复跑/可审计/可逐项对齐：`True`。

最终 gate：`True`。
