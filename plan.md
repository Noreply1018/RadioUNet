Stage 4 Missing-Buildings Robustness 主线

  目标：复现论文中 RadioUNet_S 在缺失建筑地图上的鲁棒性结果，尤其是 Fig. 6 /
  missing buildings 场景。现在 Stage 3C 已把 IRT4 transfer 主线收住，下一步应
  该检验论文声称的另一条关键结论：加入 sparse measurements 后，RadioUNet_S 对
  不完整 city map 更稳健。

  硬约束

  1. 不允许把完整建筑地图结果混入 missing-buildings 结论。
  2. 不允许只跑一个缺楼强度。至少覆盖 0, 1, 2, 4 missing buildings；如果代码和
     数据支持，再加 6 或 8。
  3. 每个 missing setting 必须明确：
      - 输入 building map 来自哪个目录；
      - target radio map 是否仍来自完整 IRT4/DPM；
      - sparse input 是否来自目标 IRT4；
      - test split 是否仍为 99 maps x 2 Tx = 198。
  4. RadioUNet_S 主线必须沿用 Stage 3C 的 paper-faithful 口径：pool600、输入
     1..300、sparse loss on full pool600。
  5. 旧 dense-loss pilot、300-pool ablation 不得作为主线，只能作为解释性对照。
  6. 所有结果必须分开标注：
      - zero-shot missing-building degradation；
      - sparse-adapted missing-building robustness；
      - complete-map upper reference；
      - C baseline。
  7. 每个 run 必须有 config snapshot、manifest、checkpoint sha256、rerun
     diff、figures、semantic audit。
  8. checkpoint/log/dataset/cache 不进 git。
  9. 如果发现 loader 实际没有使用缺楼建筑图，必须停止长跑并先修 loader，不允许
     靠文件名假设。

  执行计划，预计 30h+

  1. 论文与官方代码定位，预计 2-4h
      - 精读论文 missing buildings 段落和图表说明。
      - 定位官方 loader 如何选择 buildings_missing* 或相关目录。
      - 明确论文 Fig. 6 的横轴、模型类别、transfer/adaptation 口径。
      - 产出 docs/stage4_missing_buildings_plan.md，列出要复现的 exact
        settings。
  2. 数据与 loader 审计，预计 4-6h
      - 检查 RadioMapSeer 中缺楼建筑图目录数量、命名、map id 对齐。
      - 对每个 missing setting 抽样验证：
          - building input 确实变化；
          - Tx channel 不变；
          - IRT4 target 不变；
          - sparse IRT4 samples 与 target 对齐；
          - split 样本数正确。
      - 新增 scripts/audit_missing_buildings_loader.py。
      - 先跑 audit，不通过不训练。
  3. 实现 missing-building 配置矩阵，预计 3-5h
      - 新增 configs，例如：
          - s_irt4_missing0_pool600_sparse_loss.yaml
          - s_irt4_missing1_pool600_sparse_loss.yaml
          - s_irt4_missing2_pool600_sparse_loss.yaml
          - s_irt4_missing4_pool600_sparse_loss.yaml
      - 如果数据支持，加入 missing6/8。
      - 对照组：
          - S zero-shot missing buildings；
          - S sparse adaptation missing buildings；
          - C sparse adaptation baseline；
          - complete-map Stage 3C reference。
      - 所有配置必须显式写 city_map / missing_buildings 字段，避免隐式默认。
  4. 短跑验证，预计 2-3h
      - 每个 setting 先跑 smoke 或 2 epoch。
      - 检查 loss mode、mask 点数、input point subset、rerun diff、图像非空。
      - 检查不同 missing setting 的 building input hash 必须不同。
      - 检查 target hash 在同一 map/tx 下应一致。
  5. 主实验 A：S zero-shot missing-building sweep，预计 5-8h
      - 使用 Stage 2 / Stage 3C checkpoint，不训练或只 eval。
      - 对 0/1/2/4 missing settings 全部评估。
      - 输出 dense 和 sparse-point metrics。
      - 目的：量化缺楼输入导致的退化。
  6. 主实验 B：S pool600 sparse adaptation missing-building sweep，预计 12-18h
      - 对每个 missing setting 训练 secondU-only 50 epoch。
      - 初始化沿用 Stage 2 S firstU checkpoint。
      - loss 必须为 sparse MSE on pool600。
      - 每个 setting 单独 run dir、单独 manifest、单独 semantic audit。
      - 这是 Stage 4 主线。
  7. 主实验 C：C baseline missing-building sweep，预计 6-10h
      - 对 0/1/2/4 missing settings 跑 C sparse baseline 或至少 eval/adapt 关
        键点。
      - 目的：验证 sparse input 的 S 模型是否确实比 C 更鲁棒。
      - 如果时间不足，优先完整跑 0/4，但最终报告必须标记为 partial baseline，
        不能冒充完整 sweep。
  8. 最终审计与图表，预计 4-6h
      - 生成：
          - reports/missing_buildings/stage4_final_audit.md
          - reports/missing_buildings/stage4_final_audit.json
          - missing count vs MSE/NMSE 曲线图
          - 每个 setting 预测图
      - 报告必须回答：
          - 缺楼越多是否退化；
          - sparse measurements 是否缓解退化；
          - paper-faithful S 是否优于 C；
          - complete-map Stage 3C 是否作为上界合理；
          - 和论文趋势是否一致。

  验收标准

  完成后，Stage 4 才能算过关：

  - 至少 0/1/2/4 四个 missing settings 有完整结果。
  - S 主线每个 setting 都是 pool600 + input 1..300 + sparse loss。
  - loader audit 证明输入建筑图真的发生缺楼变化。
  - 所有 long runs 有 50 epoch history、manifest、rerun diff、checkpoint
    hash。
  - 最终图表能复现论文趋势，而不是只报单点数字。
  - 报告明确哪些是 paper-faithful，哪些是 ablation。

  预估总耗时：38-60h。实际 GPU 时间可能低于这个数，因为 IRT4 split 小；如果跑
  得太快，不代表失败，但必须用审计证明没有少跑 setting、少训练 epoch 或错误复
  用完整建筑图。
