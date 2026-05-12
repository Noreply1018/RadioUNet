# State-of-the-art baseline 审计

- gate：`True`。
- 口径：传统 baseline 为 implementation-faithful proxy；没有把 proxy 标成官方实现。
- 结果：`reports/full_matrix/state_of_art_comparison/state_of_art_comparison.json`
- 图：`reports/full_matrix/state_of_art_comparison/state_of_art_comparison.png`

| baseline | sample count | samples | MSE | global NMSE | seconds | building postprocess | per-map optimized | implementation |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `rbf` | 10 | 32 | 0.0247880285 | 0.2845728421 | 21.8783 | `False` | `True` | scipy RBFInterpolator(thin_plate_spline, neighbors=8) |
| `tensor_completion` | 10 | 32 | 0.0243776100 | 0.2798611339 | 3.4378 | `False` | `True` | scipy griddata linear+nearest proxy for tensor completion |
| `tomography` | 10 | 32 | 0.0177053355 | 0.2032617333 | 6.9570 | `True` | `True` | distance-to-Tx regression with building attenuation proxy for tomography |
| `one_step_mlp` | 10 | 32 | 0.0204130070 | 0.2343464878 | 7.8062 | `False` | `True` | per-map linear least-squares proxy for one-step MLP |
| `rbf` | 20 | 32 | 0.0161041283 | 0.1848794698 | 29.9045 | `False` | `True` | scipy RBFInterpolator(thin_plate_spline, neighbors=18) |
| `tensor_completion` | 20 | 32 | 0.0177524585 | 0.2038027170 | 3.1325 | `False` | `True` | scipy griddata linear+nearest proxy for tensor completion |
| `tomography` | 20 | 32 | 0.0169189962 | 0.1942343590 | 2.6842 | `True` | `True` | distance-to-Tx regression with building attenuation proxy for tomography |
| `one_step_mlp` | 20 | 32 | 0.0173607602 | 0.1993059224 | 2.9703 | `False` | `True` | per-map linear least-squares proxy for one-step MLP |
| `rbf` | 50 | 32 | 0.0123971222 | 0.1423221017 | 63.7995 | `False` | `True` | scipy RBFInterpolator(thin_plate_spline, neighbors=47) |
| `tensor_completion` | 50 | 32 | 0.0128917431 | 0.1480004739 | 3.1446 | `False` | `True` | scipy griddata linear+nearest proxy for tensor completion |
| `tomography` | 50 | 32 | 0.0158256223 | 0.1816821499 | 2.6741 | `True` | `True` | distance-to-Tx regression with building attenuation proxy for tomography |
| `one_step_mlp` | 50 | 32 | 0.0147059142 | 0.1688276178 | 2.9835 | `False` | `True` | per-map linear least-squares proxy for one-step MLP |
| `radiounet_s_secondU` | 50 | 7920 | 0.0004045899 | 0.0075491820 | 45.3881 | `False` | `False` | existing trained RadioUNet_S secondU metrics |
| `rbf` | 100 | 32 | 0.0106179227 | 0.1218964408 | 36.9250 | `False` | `True` | scipy RBFInterpolator(thin_plate_spline, neighbors=50) |
| `tensor_completion` | 100 | 32 | 0.0109105691 | 0.1252560953 | 3.1142 | `False` | `True` | scipy griddata linear+nearest proxy for tensor completion |
| `tomography` | 100 | 32 | 0.0157250990 | 0.1805281171 | 2.8638 | `True` | `True` | distance-to-Tx regression with building attenuation proxy for tomography |
| `one_step_mlp` | 100 | 32 | 0.0146477638 | 0.1681600364 | 2.4023 | `False` | `True` | per-map linear least-squares proxy for one-step MLP |
| `radiounet_s_secondU` | 100 | 7920 | 0.0003137517 | 0.0058542454 | 43.9775 | `False` | `False` | existing trained RadioUNet_S secondU metrics |
| `rbf` | 200 | 32 | 0.0093430981 | 0.1072611309 | 46.4442 | `False` | `True` | scipy RBFInterpolator(thin_plate_spline, neighbors=50) |
| `tensor_completion` | 200 | 32 | 0.0096594491 | 0.1108929213 | 3.1451 | `False` | `True` | scipy griddata linear+nearest proxy for tensor completion |
| `tomography` | 200 | 32 | 0.0157151251 | 0.1804136147 | 2.4008 | `True` | `True` | distance-to-Tx regression with building attenuation proxy for tomography |
| `one_step_mlp` | 200 | 32 | 0.0144051530 | 0.1653748031 | 2.6111 | `False` | `True` | per-map linear least-squares proxy for one-step MLP |
| `rbf` | 300 | 32 | 0.0089114884 | 0.1023061422 | 57.0561 | `False` | `True` | scipy RBFInterpolator(thin_plate_spline, neighbors=50) |
| `tensor_completion` | 300 | 32 | 0.0091955379 | 0.1055671027 | 3.1607 | `False` | `True` | scipy griddata linear+nearest proxy for tensor completion |
| `tomography` | 300 | 32 | 0.0158156985 | 0.1815682229 | 2.7858 | `True` | `True` | distance-to-Tx regression with building attenuation proxy for tomography |
| `one_step_mlp` | 300 | 32 | 0.0135108847 | 0.1551083767 | 3.0883 | `False` | `True` | per-map linear least-squares proxy for one-step MLP |
| `radiounet_s_secondU` | 300 | 7920 | 0.0002526154 | 0.0047135126 | 42.7386 | `False` | `False` | existing trained RadioUNet_S secondU metrics |
| `radiounet_c_secondU` | None | 7920 | 0.0004197670 |  | 32.9737 | `False` | `False` | existing trained RadioUNet_C horizontal baseline |

## 缺口
- 无。
