# Stage 3C sparse IRT4 adaptation 审计

- 配置：`configs/s_dpm_irt4_adapt.yaml`
- loader：`RadioUNet_s_sprseIRT4`
- sparse pool 配置：`600`
- 输入随机点数配置：`low=1, high=301`（上界为 numpy randint exclusive）
- loss mode：`sparse_mse`
- loss 分母：`num_samples_for_loss=600`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`

## Loss 语义
- 训练入口计算值等于手算 sparse loss：`True`
- 训练入口计算值不同于 dense full-map MSE：`True`

## Loader / mask 对齐
- `train` 输入点数 `1..299`，loss mask 非零点数 `590..600`，输入点属于 loss mask 子集 `True`，输入 sparse 值与 target 最大误差 `0.0`
- `val` 输入点数 `4..298`，loss mask 非零点数 `593..600`，输入点属于 loss mask 子集 `True`，输入 sparse 值与 target 最大误差 `0.0`
- `test` 输入点数 `5..296`，loss mask 非零点数 `593..600`，输入点属于 loss mask 子集 `True`，输入 sparse 值与 target 最大误差 `0.0`

## Gate
- `sparse_loss_configured=True`
- `pool_matches_loss_denominator=True`
- `s_input_range_configured_1_to_300=True`
- `loss_matches_manual_sparse=True`
- `loss_not_dense_mse=True`
- `all_inputs_subset_of_loss_mask=True`
- `target_alignment_exact=True`
- `rng_replay_first_batch=True`
- `pass=True`
