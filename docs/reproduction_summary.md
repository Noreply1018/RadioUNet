# RadioUNet 复现总结

本仓库已形成一条可审计的 RadioUNet 复现主线：从 clean DPM baseline，到 sparse DPM，再到 IRT4 sparse adaptation，最后到 missing buildings robustness。

## 已复现的主结论
- WNet secondU 在 Stage 1 C/DPM baseline 上改善 firstU。
- RadioUNet_S 在 DPM complete-map 设置下利用 sparse measurements 优于 C baseline。
- IRT4 transfer 中，S sparse adaptation 优于 zero-shot 与 C sparse baseline。
- missing buildings 中，S sparse-adapted 在 1/2/4 缺楼设置下优于 S zero-shot 和 C adapted，趋势与论文鲁棒性主张一致。

## 口径说明
- `paper-faithful`：Stage 1、Stage 2 random 1..300、Stage 3C pool600 sparse-loss 主线。
- `official-loader-faithful` / `implementation-faithful`：Stage 4 missing buildings，因为 sparse receiver mask 随 missing building image seed 改变。
- `ablation`：fixed sample sweep、pool300 sparse ablation、dense-loss pilot。
- `residual risk`：Stage 4 历史产物记录了 dirty provenance；最终投稿级 provenance 需要 clean rerun。

## 推荐引用
- 总审计：`reports/final_reproduction_audit.md`
- 机器可读总审计：`reports/final_reproduction_audit.json`
- Stage 4 主图：`reports/missing_buildings/stage4_missing_count_curves.png`
