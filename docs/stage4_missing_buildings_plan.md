# Stage 4 missing-buildings 复现实验计划

## 目标

复现 RadioUNet 论文中 missing buildings 场景的鲁棒性趋势：在输入 city map 缺失建筑时，RadioUNet_S 是否因 sparse IRT4 measurements 而比 RadioUNet_C 更稳健。

## 论文与官方代码定位

- 论文说明 RadioMapSeer 额外提供 perturbed city maps，其中每个原始 map 有 `m` 个建筑缺失。
- 论文鲁棒性段落考虑两类扰动：缺失 1 到 4 个建筑；以及输入无车但 target simulation 含车。
- 官方 loader 的 `cityMap != "complete"` 分支读取 `png/buildings_missing{missing}/{version}/{map_id}.png`，其中 `version` 为 1..6 的随机版本。
- 本仓库数据只包含 `buildings_missing1` 到 `buildings_missing4`，不包含 missing6 或 missing8；Stage 4 覆盖 `0, 1, 2, 4`。

## Exact Settings

所有 IRT4 run 均固定：

- target radio map：`RadioMapSeer/gain/IRT4/{map_id}_{tx}.png`，仍为完整仿真 target。
- test split：标准 split 的 `99 maps x 2 Tx = 198`。
- Tx input：`RadioMapSeer/png/antennas/{map_id}_{tx}.png`。
- checkpoint/log/dataset/cache 不进 git，只提交 config、manifest、audit、metrics、figures。

### missing0 / complete-map reference

- building input：`RadioMapSeer/png/buildings_complete/{map_id}.png`。
- S 主线：沿用 Stage 3C paper-faithful 口径，`pool600`、输入 `1..300`、`sparse_mse` loss on full `pool600`。
- 角色：complete-map upper reference，同时作为 missing count `0`。

### missing1 / missing2 / missing4

- building input：`RadioMapSeer/png/buildings_missing{m}/{version}/{map_id}.png`，`version` 为 1..6。
- target radio map：仍为 `gain/IRT4`，不使用缺楼 target。
- sparse input：由 target IRT4 的像素值填入 sparse input channel；S 的输入点为 `pool600` 的随机子集 `1..300`。
- S 主线：secondU-only 50 epoch，初始化 `reports/s_dpm_thr2/rand1_300_50ep/checkpoints/firstU.pt`，loss 为 full `pool600` sparse mask。
- C baseline：secondU-only 50 epoch，初始化 `reports/c_dpm_thr2/20260506_182311/checkpoints/firstU.pt`，loss 为 returned sparse IRT4 mask。

## 结果分区

- `zero-shot missing-building degradation`：S/C DPM checkpoint 直接在 missing input 上 eval。
- `sparse-adapted missing-building robustness`：S/C 在各 missing setting 上 sparse-loss adaptation。
- `complete-map upper reference`：Stage 3C complete-map S/C sparse adaptation。
- `C baseline`：RadioUNet_C 的 zero-shot 与 sparse adaptation 对照。

## Gate

每个 long run 必须有：

- config snapshot；
- manifest；
- checkpoint sha256；
- rerun diff；
- figures；
- semantic audit；
- missing-buildings loader audit。

若 loader audit 不能证明 building input 发生缺楼变化、target IRT4 不变、sparse input 来自 target IRT4、split 样本数为 198，则停止主跑。
