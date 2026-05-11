# IRT4 Transfer 全矩阵审计

- gate：`True`。
- 口径：source coarse target x RadioUNet_C/S x zero-shot/adaptation；IRT4 固定 Tx 0/1，即 `num_tx=2`。
- adaptation：C 使用 300 sparse loss receivers；S 使用 600 receiver pool、输入随机 1..300、loss on full 600 sparse points。

| run | setting | source | model | dense MSE | dense NMSE | RMSE dB | sparse MSE | figures | gate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `c_dpm_irt4_zeroshot` | zero-shot | DPM | C | 0.0015082982 | 0.0308228291 | 3.106945 | 0.0015546557 | 8 | `True` |
| `c_dpm_irt4_adapt` | sparse adaptation | DPM | C | 0.0010237258 | 0.0210642466 | 2.559657 | 0.0009881779 | 8 | `True` |
| `s_dpm_irt4_zeroshot` | zero-shot | DPM | S | 0.0009222977 | 0.0189631393 | 2.429548 | 0.0007703437 | 8 | `True` |
| `s_dpm_irt4_adapt` | sparse adaptation | DPM | S | 0.0007541992 | 0.0156007245 | 2.197015 | 0.0006012259 | 8 | `True` |
| `c_irt2_irt4_zeroshot` | zero-shot | IRT2 | C | 0.0019253841 | 0.0400277999 | 3.510336 | 0.0019964829 | 8 | `True` |
| `c_irt2_irt4_adapt` | sparse adaptation | IRT2 | C | 0.0008885960 | 0.0184061759 | 2.384746 | 0.0008523535 | 8 | `True` |
| `s_irt2_irt4_zeroshot` | zero-shot | IRT2 | S | 0.0010094359 | 0.0210819472 | 2.541730 | 0.0008089368 | 8 | `True` |
| `s_irt2_irt4_adapt` | sparse adaptation | IRT2 | S | 0.0006407046 | 0.0132558711 | 2.024972 | 0.0005100919 | 8 | `True` |
| `c_rand_irt4_zeroshot` | zero-shot | random coarse simulation | C | 0.0015609360 | 0.0322578199 | 3.160695 | 0.0016119401 | 8 | `True` |
| `c_rand_irt4_adapt` | sparse adaptation | random coarse simulation | C | 0.0008520787 | 0.0176178042 | 2.335231 | 0.0008058680 | 8 | `True` |
| `s_rand_irt4_zeroshot` | zero-shot | random coarse simulation | S | 0.0007217814 | 0.0149385420 | 2.149279 | 0.0005915852 | 8 | `True` |
| `s_rand_irt4_adapt` | sparse adaptation | random coarse simulation | S | 0.0006103793 | 0.0126035350 | 1.976468 | 0.0004930784 | 8 | `True` |

## 缺口
- 无。
