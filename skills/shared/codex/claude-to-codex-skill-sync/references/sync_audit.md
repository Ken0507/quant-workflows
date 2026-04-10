# Claude -> Codex Incremental Sync Audit

增量同步完成后，先检查本清单，再执行 migration skill 的 `fidelity_audit.md`。

## 1. Baseline Detection

- [ ] 已找到最近一次触及目标 Codex skill 路径的 commit
- [ ] `BASELINE_COMMIT` 记录清楚
- [ ] 已读取 `Claude@BASELINE_COMMIT`
- [ ] 没有把未提交工作树误当作基线

## 2. Claude Commit Window Review

- [ ] 已列出 `BASELINE_COMMIT..HEAD` 区间内触及 Claude 源 skill 的全部 commits
- [ ] 已逐个阅读 commit message
- [ ] 对关键 commit 已按需阅读 diff / hunk
- [ ] 如果区间为空，已正确报告 no-op

## 3. Tree Delta Classification

- [ ] 已比较 `Claude@BASELINE_COMMIT` 与 `Claude@HEAD`
- [ ] 已按新增 / 修改 / 删除 / rename 分类所有变化文件
- [ ] 未变化文件没有被无故改动

## 4. Codex Delta Application

- [ ] 新增文件已同步到 Codex 对应位置
- [ ] 修改文件只同步了语义变化，未盲覆盖 Codex 平台适配
- [ ] Claude 删除的非平台专属文件，Codex 侧已对应删除
- [ ] Claude rename / move 已在 Codex 侧正确镜像，或已向用户升级确认

## 5. Codex-owned Surfaces Preserved

- [ ] `.claude` / `.codex` 路径映射仍正确
- [ ] agent 编排仍是 Codex 真实语义
- [ ] Consultant / Reviewer / Compliance / Logger 的 Codex 角色语义未被冲掉
- [ ] `agents/openai.yaml` 仍与 Codex skill 触发语义一致

## 6. No Semantic Weakening

- [ ] 没有漏同步基线后新增的硬约束
- [ ] 没有把 `必须` / `禁止` / gate / checklist 同步弱化
- [ ] 没有漏掉阈值、日期范围、退出条件、异常协议

## 7. Final Summary

- [ ] 已向用户说明 `BASELINE_COMMIT`
- [ ] 已说明本次读取了哪些 Claude commits
- [ ] 已说明同步了哪些文件 / 片段
- [ ] 已说明保留了哪些 Codex 平台适配
- [ ] 如有歧义，已明确列为待确认项

## 8. Commit Discipline

- [ ] 如果本次有实际改动，已只 stage 目标 Codex skill 目录
- [ ] 已创建同步 commit，而不是把改动留在工作树里
- [ ] commit message 清楚表达“同步了哪个 skill”
- [ ] commit body 已记录 `BASELINE_COMMIT` 与本次读取的 Claude commits
