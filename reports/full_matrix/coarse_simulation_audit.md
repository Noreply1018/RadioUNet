# Coarse Simulation 全矩阵审计

- gate：`False`。
- 覆盖轴：RadioUNet_C/S x DPM/IRT2/random coarse simulation，clean map，no cars。

| run | model | simulation | run dir | firstU MSE | secondU MSE | figures | gate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `c_dpm_thr2` | C | DPM | `reports/c_dpm_thr2/20260506_182311` | nan | 0.0004197670 | 8 | `False` |
| `s_dpm_thr2_rand1_300` | S | DPM | `reports/s_dpm_thr2/rand1_300_50ep` | 0.0003632125 | 0.0002833113 | 8 | `True` |
| `c_irt2_thr2` | C | IRT2 | `/root/lanyun-tmp/projects/RadioUNet_hkf/reports/full_matrix/c_irt2_thr2_50ep` | nan | nan | 0 | `False` |
| `s_irt2_thr2_rand1_300` | S | IRT2 | `/root/lanyun-tmp/projects/RadioUNet_hkf/reports/full_matrix/s_irt2_thr2_rand1_300_50ep` | nan | nan | 0 | `False` |
| `c_rand_thr2` | C | rand | `/root/lanyun-tmp/projects/RadioUNet_hkf/reports/full_matrix/c_rand_thr2_50ep` | nan | nan | 0 | `False` |
| `s_rand_thr2_rand1_300` | S | rand | `/root/lanyun-tmp/projects/RadioUNet_hkf/reports/full_matrix/s_rand_thr2_rand1_300_50ep` | nan | nan | 0 | `False` |

## 缺口
- `c_dpm_thr2` 未满足 full-run gate；请运行 `python scripts/run_full_matrix_coarse.py --run c_dpm_thr2 --device auto`。
- `c_irt2_thr2` 未满足 full-run gate；请运行 `python scripts/run_full_matrix_coarse.py --run c_irt2_thr2 --device auto`。
- `s_irt2_thr2_rand1_300` 未满足 full-run gate；请运行 `python scripts/run_full_matrix_coarse.py --run s_irt2_thr2_rand1_300 --device auto`。
- `c_rand_thr2` 未满足 full-run gate；请运行 `python scripts/run_full_matrix_coarse.py --run c_rand_thr2 --device auto`。
- `s_rand_thr2_rand1_300` 未满足 full-run gate；请运行 `python scripts/run_full_matrix_coarse.py --run s_rand_thr2_rand1_300 --device auto`。
