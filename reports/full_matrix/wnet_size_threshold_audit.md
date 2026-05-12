# WNet / model size / threshold 矩阵审计

- gate：`False`。
- 本审计覆盖 size 参数化、参数量、architecture hash、输入输出 shape、threshold preprocessing 与 split 文件级 overlap。
- 50 epoch full runs 尚未全部完成，因此最终 plan gate 仍不能仅凭本 readiness 审计通过。

## Model Size
| label | width_scale | parameters | architecture hash | shape gate |
| --- | ---: | ---: | --- | ---: |
| `small` | 0.5 | 3320454 | `b94e5f9b1134f74cd08e3c0f32f1ef51774c5b2d14242d658961a34680c2699d` | `True` |
| `base` | 1.0 | 13274031 | `b93a681aa8d558252ac91352f8419a0194525ba9fef4d35cd290172daddf76f3` | `True` |
| `large` | 1.5 | 29860858 | `48284e7921d2b45215b1225cb60e7cede08a0f3fc0174735aa84daeb148dc83b` | `True` |

## Smoke Evidence
| label | smoke manifest | smoke gate |
| --- | --- | ---: |
| `small` | `reports/full_matrix/c_dpm_thr2_size_small_smoke` | `True` |
| `base` | `reports/full_matrix/c_dpm_thr2_size_base_smoke` | `False` |
| `large` | `reports/full_matrix/c_dpm_thr2_size_large_smoke` | `False` |

## Threshold
| threshold | target mean | diff vs 0.2 max | gate |
| ---: | ---: | ---: | ---: |
| 0.0 | 0.408078 | 0.200000 | `True` |
| 0.1 | 0.353436 | 0.111111 | `True` |
| 0.2 | 0.285407 | 0.000000 | `True` |
| 0.3 | 0.202189 | 0.124650 | `True` |
| 0.4 | 0.115773 | 0.250000 | `True` |

## Split
- config：`configs/c_dpm_thr2_split400_100_200.yaml`
- legacy counts：`{'train': 501, 'val': 100, 'test': 99}`
- paper 400/100/200 counts：`{'train': 400, 'val': 100, 'test': 200}`
- legacy test 与 paper test overlap map 数：`99`
