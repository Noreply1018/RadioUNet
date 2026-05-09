# Stage 4 missing-buildings loader 审计

- 配置：`configs/c_irt4_missing2_sparse_loss.yaml`
- loader：`RadioUNet_c_sprseIRT4`
- missing_buildings：`2`
- building dir：`RadioMapSeer/png/buildings_missing2`
- target radio dir：`RadioMapSeer/gain/IRT4`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`

## 样本检查
- `test[0]` map `419` tx `0`：building 语义通过 `True`，target hash `6287630a629323160c36bbb8623af5b14ba1e5f525db4811173262ef63aa2e42`，input sparse/target 最大误差 `None`
- `test[1]` map `419` tx `1`：building 语义通过 `True`，target hash `b3b747bb636936a7315687b2046b7f4bea9d7b6dafc773d9c9312488e3dc9a14`，input sparse/target 最大误差 `None`
- `test[2]` map `392` tx `0`：building 语义通过 `True`，target hash `c3a660327d2e403362b6cc12538e25952545d8e9f6ce801fa3393c2c68a0c0bb`，input sparse/target 最大误差 `None`

## Gate
- `building_dir_exists=True`
- `target_radio_dir_exists=True`
- `antenna_dir_exists=True`
- `versions_present_if_missing=True`
- `test_split_is_198=True`
- `building_input_semantics_ok=True`
- `target_hash_stable_across_tx_duplicates=True`
- `s_sparse_input_from_target=True`
- `s_input_subset_of_loss_mask=True`
- `s_pool600_if_mainline=True`
- `pass=True`
