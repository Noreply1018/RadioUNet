# Stage 4 missing-buildings 最终审计

## 结论分区
- zero-shot missing-building degradation：S/C 源 DPM checkpoint 直接评估 missing0/1/2/4。
- sparse-adapted missing-building robustness：S missing1/2/4 采用 pool600、输入 1..300、sparse loss；missing0 使用 Stage 3C complete-map upper reference。
- complete-map upper reference：Stage 3C S/C complete-map IRT4 sparse adaptation。
- C baseline：C missing1/2/4 sparse adaptation，missing0 使用 Stage 3C C reference。

## 指标
| 类别 | 模型 | missing | 样本数 | dense MSE | sparse MSE | rerun diff |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| zero-shot missing-building degradation | C | 0 | 198 | 0.0014888853 | 0.0015274379 | 0.0 |
| zero-shot missing-building degradation | C | 1 | 198 | 0.0022372528 | 0.0022040660 | 0.0 |
| zero-shot missing-building degradation | C | 2 | 198 | 0.0040011905 | 0.0040703506 | 0.0 |
| zero-shot missing-building degradation | C | 4 | 198 | 0.0056903721 | 0.0056755599 | 0.0 |
| zero-shot missing-building degradation | S | 0 | 198 | 0.0009213352 | 0.0008077989 | 0.0 |
| zero-shot missing-building degradation | S | 1 | 198 | 0.0018950003 | 0.0018555564 | 0.0 |
| zero-shot missing-building degradation | S | 2 | 198 | 0.0028734735 | 0.0027084463 | 0.0 |
| zero-shot missing-building degradation | S | 4 | 198 | 0.0047639349 | 0.0047364171 | 0.0 |
| sparse-adapted missing-building robustness | S | 1 | 198 | 0.0016115039 | 0.0015122744 | 0.0 |
| sparse-adapted missing-building robustness | S | 2 | 198 | 0.0023793743 | 0.0021364905 | 0.0 |
| sparse-adapted missing-building robustness | S | 4 | 198 | 0.0029527322 | 0.0027546661 | 0.0 |
| complete-map upper reference | C | 0 | 198 | 0.0010485411 | 0.0010080370 | 0.0 |
| complete-map upper reference | S | 0 | 198 | 0.0007609739 | 0.0006030457 | 0.0 |
| C baseline | C | 1 | 198 | 0.0017711031 | 0.0017050532 | 0.0 |
| C baseline | C | 2 | 198 | 0.0032057920 | 0.0032213822 | 0.0 |
| C baseline | C | 4 | 198 | 0.0045580263 | 0.0044714421 | 0.0 |

## 回答
- 缺楼越多是否退化：`True`。
- sparse measurements 是否缓解退化：`True`。
- paper-faithful S 是否优于 C：`True`。
- complete-map Stage 3C 作为上界：`True`。
- 与论文趋势一致：`True`。

曲线图：`reports/missing_buildings/stage4_missing_count_curves.png`

最终 gate：`True`。
