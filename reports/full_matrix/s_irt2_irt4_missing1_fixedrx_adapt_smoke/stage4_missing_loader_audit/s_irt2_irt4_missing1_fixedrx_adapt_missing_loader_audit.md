# Stage 4 missing-buildings loader 审计

- 配置：`configs/s_irt2_irt4_missing1_fixedrx_adapt.yaml`
- loader：`RadioUNet_s_sprseIRT4`
- missing_buildings：`1`
- building dir：`RadioMapSeer/png/buildings_missing1`
- target radio dir：`RadioMapSeer/gain/IRT4`
- split 样本数：`{'train': 1002, 'val': 200, 'test': 198}`

## 跨 missing target consistency
- 语义标签：`official-loader-faithful missing-building sparse sampling`
- 同一 map/tx：`True`
- target IRT4 hash 不变：`True`
- Tx hash 不变：`True`
- building input hash 随 missing 改变：`True`
- S sparse input 值与 target 对齐：`True`
- sparse receiver mask 由 missing building image seed 决定：`False`

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
- `same_map_tx_across_missing=True`
- `target_irt4_hash_stable_across_missing=True`
- `tx_hash_stable_across_missing=True`
- `building_input_hash_changes_across_missing=True`
- `s_sparse_input_from_target=True`
- `s_sparse_input_from_target_all_missing=True`
- `s_input_subset_of_loss_mask=True`
- `s_pool600_if_mainline=True`
- `pass=True`
