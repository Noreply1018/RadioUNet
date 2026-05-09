# Stage 4 missing-buildings loader 审计

- 配置：`configs/s_irt4_missing0_pool600_sparse_loss.yaml`
- loader：`RadioUNet_s_sprseIRT4`
- missing_buildings：`0`
- building dir：`RadioMapSeer/png/buildings_complete`
- target radio dir：`RadioMapSeer/gain/IRT4`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`

## 样本检查
- `test[0]` map `419` tx `0`：building 语义通过 `True`，target hash `1ae8979f91b821b9390331ce4c034be70f3835638517ce71012d142386b33c51`，input sparse/target 最大误差 `0.0`
- `test[1]` map `419` tx `1`：building 语义通过 `True`，target hash `a0eb45c235b4a45bcd563bdd589d09651babbe1895ce545398ba54df393f9771`，input sparse/target 最大误差 `0.0`
- `test[2]` map `392` tx `0`：building 语义通过 `True`，target hash `cae2f0218bbfd7326439071acf2e77a61535d93a38dbe33b80ea755041062ccc`，input sparse/target 最大误差 `0.0`

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
