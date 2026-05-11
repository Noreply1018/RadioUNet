# Cars 场景全矩阵审计

- gate：`False`。
- 覆盖：DPM/IRT2 cars simulation；C baseline 无 cars input；S 使用 cars input channel 与随机 1..300 measurement input。
- IRT4 cars 数据：`available`。

| run | model | simulation | cars input | firstU MSE | secondU MSE | target cars diff | cars channel nnz | figures | gate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `c_dpmcars_thr2` | C | DPM | no | 0.0007187337 | 0.0006577803 | 0.107843 | 0 | 8 | `True` |
| `c_irt2cars_thr2` | C | IRT2 | no | nan | nan | 0.107843 | 0 | 0 | `False` |
| `s_dpmcars_carinput_thr2_rand1_300` | S | DPM | yes | nan | nan | 27.500000 | 772 | 0 | `False` |
| `s_irt2cars_carinput_thr2_rand1_300` | S | IRT2 | yes | nan | nan | 27.500000 | 772 | 0 | `False` |

## 缺口
- `c_irt2cars_thr2` 未满足 gate；运行 `python scripts/run_full_matrix_cars.py --run c_irt2cars_thr2 --device auto`。
- `s_dpmcars_carinput_thr2_rand1_300` 未满足 gate；运行 `python scripts/run_full_matrix_cars.py --run s_dpmcars_carinput_thr2_rand1_300 --device auto`。
- `s_irt2cars_carinput_thr2_rand1_300` 未满足 gate；运行 `python scripts/run_full_matrix_cars.py --run s_irt2cars_carinput_thr2_rand1_300 --device auto`。
