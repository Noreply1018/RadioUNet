# Missing Buildings Full Matrix 审计

- gate：`False`。
- official-loader DPM run gate：`False`。
- fixed receiver policy hash gate：`True`。
- fixed receiver configs complete：`True`。
- fixed receiver full runs complete：`False`。

## Official-loader 已有 run
| policy | source | model | transfer | missing | samples | mse | rerun diff | gate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| official_loader | dpm | c | zeroshot | 0 | 198 | 0.0014888853 | 0.0 | `False` |
| official_loader | dpm | c | zeroshot | 1 | 198 | 0.0022372528 | 0.0 | `False` |
| official_loader | dpm | c | zeroshot | 2 | 198 | 0.0040011905 | 0.0 | `False` |
| official_loader | dpm | c | zeroshot | 4 | 198 | 0.0056903721 | 0.0 | `False` |
| official_loader | dpm | c | adapt | 1 | 198 | 0.0017711031 | 0.0 | `False` |
| official_loader | dpm | c | adapt | 2 | 198 | 0.0032057920 | 0.0 | `False` |
| official_loader | dpm | c | adapt | 4 | 198 | 0.0045580263 | 0.0 | `False` |
| official_loader | dpm | s | zeroshot | 0 | 198 | 0.0009213352 | 0.0 | `False` |
| official_loader | dpm | s | zeroshot | 1 | 198 | 0.0018950003 | 0.0 | `False` |
| official_loader | dpm | s | zeroshot | 2 | 198 | 0.0028734735 | 0.0 | `False` |
| official_loader | dpm | s | zeroshot | 4 | 198 | 0.0047639349 | 0.0 | `False` |
| official_loader | dpm | s | adapt | 1 | 198 | 0.0016115039 | 0.0 | `False` |
| official_loader | dpm | s | adapt | 2 | 198 | 0.0023793743 | 0.0 | `False` |
| official_loader | dpm | s | adapt | 4 | 198 | 0.0029527322 | 0.0 | `False` |

## Fixed receiver matrix 缺口
| source | model | missing | config | run exists | gap |
| --- | --- | ---: | --- | ---: | --- |
| dpm | c | 0 | `True` | `False` | missing fixed receiver full run |
| dpm | c | 1 | `True` | `False` | missing fixed receiver full run |
| dpm | c | 2 | `True` | `False` | missing fixed receiver full run |
| dpm | c | 4 | `True` | `False` | missing fixed receiver full run |
| dpm | s | 0 | `True` | `False` | missing fixed receiver full run |
| dpm | s | 1 | `True` | `False` | missing fixed receiver full run |
| dpm | s | 2 | `True` | `False` | missing fixed receiver full run |
| dpm | s | 4 | `True` | `False` | missing fixed receiver full run |
| irt2 | c | 0 | `True` | `False` | missing fixed receiver full run |
| irt2 | c | 1 | `True` | `False` | missing fixed receiver full run |
| irt2 | c | 2 | `True` | `False` | missing fixed receiver full run |
| irt2 | c | 4 | `True` | `False` | missing fixed receiver full run |
| irt2 | s | 0 | `True` | `False` | missing fixed receiver full run |
| irt2 | s | 1 | `True` | `False` | missing fixed receiver full run |
| irt2 | s | 2 | `True` | `False` | missing fixed receiver full run |
| irt2 | s | 4 | `True` | `False` | missing fixed receiver full run |
| rand | c | 0 | `True` | `False` | missing fixed receiver full run |
| rand | c | 1 | `True` | `False` | missing fixed receiver full run |
| rand | c | 2 | `True` | `False` | missing fixed receiver full run |
| rand | c | 4 | `True` | `False` | missing fixed receiver full run |
| rand | s | 0 | `True` | `False` | missing fixed receiver full run |
| rand | s | 1 | `True` | `False` | missing fixed receiver full run |
| rand | s | 2 | `True` | `False` | missing fixed receiver full run |
| rand | s | 4 | `True` | `False` | missing fixed receiver full run |
