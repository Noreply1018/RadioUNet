# IRT4 Transfer 全矩阵审计

- gate：`False`。
- 口径：source coarse target x RadioUNet_C/S x zero-shot/adaptation；IRT4 固定 Tx 0/1，即 `num_tx=2`。
- adaptation：C 使用 300 sparse loss receivers；S 使用 600 receiver pool、输入随机 1..300、loss on full 600 sparse points。

| run | setting | source | model | dense MSE | dense NMSE | RMSE dB | sparse MSE | figures | gate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `c_dpm_irt4_zeroshot` | zero-shot | DPM | C | 0.0015082982 | 0.0308228291 | 3.106945 | 0.0015546557 | 8 | `True` |
| `c_dpm_irt4_adapt` | sparse adaptation | DPM | C | nan | nan | nan | nan | 0 | `False` |
| `s_dpm_irt4_zeroshot` | zero-shot | DPM | S | 0.0009222977 | 0.0189631393 | 2.429548 | 0.0007703437 | 8 | `True` |
| `s_dpm_irt4_adapt` | sparse adaptation | DPM | S | nan | nan | nan | nan | 0 | `False` |
| `c_irt2_irt4_zeroshot` | zero-shot | IRT2 | C | 0.0019253841 | 0.0400277999 | 3.510336 | 0.0019964829 | 8 | `True` |
| `c_irt2_irt4_adapt` | sparse adaptation | IRT2 | C | nan | nan | nan | nan | 0 | `False` |
| `s_irt2_irt4_zeroshot` | zero-shot | IRT2 | S | 0.0010094359 | 0.0210819472 | 2.541730 | 0.0008089368 | 8 | `True` |
| `s_irt2_irt4_adapt` | sparse adaptation | IRT2 | S | nan | nan | nan | nan | 0 | `False` |
| `c_rand_irt4_zeroshot` | zero-shot | random coarse simulation | C | 0.0015609360 | 0.0322578199 | 3.160695 | 0.0016119401 | 8 | `True` |
| `c_rand_irt4_adapt` | sparse adaptation | random coarse simulation | C | nan | nan | nan | nan | 0 | `False` |
| `s_rand_irt4_zeroshot` | zero-shot | random coarse simulation | S | 0.0007217814 | 0.0149385420 | 2.149279 | 0.0005915852 | 8 | `True` |
| `s_rand_irt4_adapt` | sparse adaptation | random coarse simulation | S | nan | nan | nan | nan | 0 | `False` |

## 缺口
- `c_dpm_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_dpm_irt4_adapt --device auto`。
- `s_dpm_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_dpm_irt4_adapt --device auto`。
- `c_irt2_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_irt2_irt4_adapt --device auto`。
- `s_irt2_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_irt2_irt4_adapt --device auto`。
- `c_rand_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run c_rand_irt4_adapt --device auto`。
- `s_rand_irt4_adapt` 未满足 gate；运行 `python scripts/run_full_matrix_irt4.py --run s_rand_irt4_adapt --device auto`。
