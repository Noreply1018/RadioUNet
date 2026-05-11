# IRT4 Transfer 全矩阵审计

- gate：`False`。
- 口径：source coarse target x RadioUNet_C/S x zero-shot/adaptation；IRT4 固定 Tx 0/1，即 `num_tx=2`。
- adaptation：C 使用 300 sparse loss receivers；S 使用 600 receiver pool、输入随机 1..300、loss on full 600 sparse points。

| run | setting | source | model | dense MSE | dense NMSE | RMSE dB | sparse MSE | figures | gate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `c_dpm_irt4_zeroshot` | zero-shot | DPM | C | nan | nan | nan | nan | 0 | `False` |
| `c_dpm_irt4_adapt` | sparse adaptation | DPM | C | nan | nan | nan | nan | 0 | `False` |
| `s_dpm_irt4_zeroshot` | zero-shot | DPM | S | nan | nan | nan | nan | 0 | `False` |
| `s_dpm_irt4_adapt` | sparse adaptation | DPM | S | nan | nan | nan | nan | 0 | `False` |
| `c_irt2_irt4_zeroshot` | zero-shot | IRT2 | C | nan | nan | nan | nan | 0 | `False` |
| `c_irt2_irt4_adapt` | sparse adaptation | IRT2 | C | nan | nan | nan | nan | 0 | `False` |
| `s_irt2_irt4_zeroshot` | zero-shot | IRT2 | S | nan | nan | nan | nan | 0 | `False` |
| `s_irt2_irt4_adapt` | sparse adaptation | IRT2 | S | nan | nan | nan | nan | 0 | `False` |
| `c_rand_irt4_zeroshot` | zero-shot | random coarse simulation | C | nan | nan | nan | nan | 0 | `False` |
| `c_rand_irt4_adapt` | sparse adaptation | random coarse simulation | C | nan | nan | nan | nan | 0 | `False` |
| `s_rand_irt4_zeroshot` | zero-shot | random coarse simulation | S | nan | nan | nan | nan | 0 | `False` |
| `s_rand_irt4_adapt` | sparse adaptation | random coarse simulation | S | nan | nan | nan | nan | 0 | `False` |

## 缺口
- `c_dpm_irt4_zeroshot` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_dpm_irt4_zeroshot --device auto`。
- `c_dpm_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_dpm_irt4_adapt --device auto`。
- `s_dpm_irt4_zeroshot` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_dpm_irt4_zeroshot --device auto`。
- `s_dpm_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_dpm_irt4_adapt --device auto`。
- `c_irt2_irt4_zeroshot` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_irt2_irt4_zeroshot --device auto`。
- `c_irt2_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_irt2_irt4_adapt --device auto`。
- `s_irt2_irt4_zeroshot` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_irt2_irt4_zeroshot --device auto`。
- `s_irt2_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_irt2_irt4_adapt --device auto`。
- `c_rand_irt4_zeroshot` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_rand_irt4_zeroshot --device auto`。
- `c_rand_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_rand_irt4_adapt --device auto`。
- `s_rand_irt4_zeroshot` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_rand_irt4_zeroshot --device auto`。
- `s_rand_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_rand_irt4_adapt --device auto`。
