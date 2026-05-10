Final Stage：Reproduction Closeout

  目标：修复 Stage 4 审计漏洞，补齐 provenance，统一所有阶段结论，产出一份能独
  立说明“复现了什么、没复现什么、和论文差距在哪里”的最终报告。

  必须先修的 3 点

  1. 修 Stage 4 target hash 审计
      - 修掉 samples[0]["target_tensor_hash"] == samples[0]
        ["target_tensor_hash"] 这种无效自比较。
      - 新增跨 missing0/1/2/4 的 target consistency audit。
      - 验证同一 map_id/tx 下：
          - building input hash 随 missing setting 改变；
          - target IRT4 hash 不变；
          - Tx hash 不变；
          - S sparse input 值与 target 对齐。
  2. 收紧 final gate
      - stage4_final_audit 必须检查所有 metrics/manifest 的 git.dirty。
      - 已存在历史 run 的 git.dirty=True 不能伪装成 clean。
      - 报告里明确写：
          - Stage 4 run artifacts were generated while Stage 4 scripts were
            uncommitted；
          - current repository is now clean；
          - rerun is recommended only if final-grade provenance is required。
      - 如果要达到最终严谨版，重跑 Stage 4 或至少重跑 metrics/audits，让
        provenance clean。
  3. 标注 sparse receiver mask 语义
      - 明确当前 missing-building loader 的 sparse receiver mask 由 missing
        building image seed 决定。
      - 结论命名从无条件 paper-faithful fixed receivers 改为：
          - official-loader-faithful missing-building sparse sampling
          - 或 implementation-faithful Stage 4
      - 如果时间允许，补一个 fixed_receiver_mask 对照，不作为主线必需，但能增
        强说服力。

  最后一步执行计划

  1. Stage 4 小修复，预计 3-5h
      - 修改 scripts/audit_missing_buildings_loader.py。
      - 修改 scripts/audit_stage4_final.py。
      - 重新生成：
          - reports/missing_buildings/loader_audits/*
          - reports/missing_buildings/stage4_final_audit.md/json
      - 提交修复 commit。
  2. 可选 clean-provenance rerun，预计 8-14h
      - 如果追求最终高质量，建议重跑 Stage 4 的 eval/audit/manifest，必要时重
        跑 6 个 adaptation：
          - S missing1/2/4
          - C missing1/2/4
      - 因为每个 epoch 只有 6-8s，实际不会特别久。
      - 目标是让 metrics/manifest 的 git.dirty=False。
      - 如果不重跑，最终报告必须把 dirty provenance 标为 residual risk。
  3. 全阶段一致性审计，预计 4-6h
      - 新增 scripts/audit_reproduction_final.py。
      - 汇总检查：
          - Stage 1 C DPM baseline
          - Stage 2 S DPM random 1..300
          - Stage 3C IRT4 sparse adaptation
          - Stage 4 missing buildings robustness
      - 检查项：
          - configs 是否存在；
          - metrics 是否存在；
          - rerun diff 是否为 0；
          - checkpoint 是否未进 git；
          - 每阶段是否有明确 paper-faithful / ablation / pilot 标签；
          - target_scale 是否一致解释；
          - DPM、IRT4、missing-building 结论没有混口径。
  4. 最终复现报告，预计 6-10h
      - 产出：
          - reports/final_reproduction_audit.md
          - reports/final_reproduction_audit.json
          - docs/reproduction_summary.md
      - 报告必须回答：
          - 论文哪些主结论已复现；
          - 哪些只做了 implementation-faithful 或 reduced reproduction；
          - 哪些没有覆盖；
          - 与论文数值的差异；
          - 当前最可信的表格和图；
          - 后续如果投稿/开源，还需补什么。
  5. 最终 Git 收口，预计 1h
      - 清理 pycache 和临时文件。
      - 确认 .gitignore 没漏。
      - git status --short --untracked-files=all 为空。
      - git ls-files 确认 checkpoint/log/dataset 未追踪。
      - 最终提交，例如：
          - Fix Stage 4 audit strictness
          - Add final reproduction audit

  最终验收标准

  - Stage 4 审计漏洞已修。
  - 所有 final reports 明确区分：
      - paper-faithful
      - official-loader-faithful
      - ablation
      - pilot
      - residual risk
  - 至少一个最终总报告能从空白状态解释完整复现路线。
  - 所有主线指标可追踪到 config、commit、run dir 和 checkpoint hash。
  - git 工作区干净。
  - 不再有“看起来完成但语义不清”的结论。

  完成这一步后，复现主线可以收尾。后面再做的应是扩展项，例如 cars、IRT2/rand
  simulation 更完整对照、固定 receiver mask ablation、论文表格级排版，而不是主
  线阻塞项。

