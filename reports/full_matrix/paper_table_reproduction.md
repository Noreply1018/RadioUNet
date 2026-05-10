# 论文图表复现汇总

| 论文图/表 | 本仓库复现图 | 参与 run | gate | residual risk |
| --- | --- | --- | --- | --- |
| `fig8_radio_unet_performance` | `reports/full_matrix/fig8_radio_unet_performance.png` | `c_irt4_missing0_zeroshot, s_irt4_missing0_zeroshot, c_irt4_dpm_adapt, s_irt4_dpm_adapt_pool600` | `False` | 仅 DPM-source 子集，缺 IRT2/rand source transfer。 |
| `fig9_wnet_missing_buildings` | `reports/full_matrix/fig9_wnet_missing_buildings.png` | `c_irt4_missing0_zeroshot, c_irt4_missing1_zeroshot, c_irt4_missing2_zeroshot, c_irt4_missing4_zeroshot, c_irt4_missing1_adapt, c_irt4_missing2_adapt, c_irt4_missing4_adapt, s_irt4_missing0_zeroshot, s_irt4_missing1_zeroshot, s_irt4_missing2_zeroshot, s_irt4_missing4_zeroshot, s_irt4_missing1_adapt, s_irt4_missing2_adapt, s_irt4_missing4_adapt` | `False` | official-loader-faithful 子集；缺 fixed receiver 和 IRT2/rand source。 |
| `fig10_state_of_art_comparison` | `reports/full_matrix/fig10_state_of_art_comparison.png` | `s_dpm_fixed50, s_dpm_fixed100, s_dpm_fixed300, s_dpm_rand1_300` | `False` | 缺 RBF、tensor completion、tomography、MLP baseline。 |
