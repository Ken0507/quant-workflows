# Claude -> Codex Batch Sync Audit

批量同步完成后，检查以下项目。

## 1. Scope Resolution

- [ ] 已明确本次范围是 `all/shared/hft/crypto` 之一
- [ ] 范围目录解析正确
- [ ] 没有把 repo 外的软链接目录混入扫描

## 2. Candidate Enumeration

- [ ] 只枚举了 `skills/<category>/codex/` 下已有 skill 目录
- [ ] 没有把缺失的 Codex sibling 当成候选
- [ ] 候选列表已记录清楚

## 3. Matching And Baseline

- [ ] 每个候选 skill 都已分类为 `matched / codex-only / ambiguous`
- [ ] 每个 `matched` skill 都已找到自己的 `BASELINE_COMMIT`
- [ ] 没有把单个 skill 的基线误套到其他 skill 上

## 4. Outdated Detection

- [ ] 已检查 `BASELINE_COMMIT..HEAD` 区间内 Claude 源 skill 的 commits
- [ ] `up-to-date / outdated / blocked` 分类清楚
- [ ] 每个 `outdated` skill 的 Claude commit 列表已保存

## 5. Sync Execution

- [ ] 实际修改前已先形成扫描摘要
- [ ] 每个 `outdated` skill 都通过单 skill sync 逻辑处理
- [ ] 没有在批量 skill 中直接手写 patch 代替单 skill sync
- [ ] 遇到待确认项时已正确暂停后续批量处理

## 6. Coverage Boundary

- [ ] 没有自动新建缺失的 Codex sibling
- [ ] `codex-only` skills 已被正确跳过

## 7. Final Summary

- [ ] 已汇总 `synced`
- [ ] 已汇总 `up-to-date`
- [ ] 已汇总 `codex-only skipped`
- [ ] 已汇总 `blocked`

## 8. Commit Discipline

- [ ] 如果本次批量存在实际改动且无 `blocked`，已创建 batch commit
- [ ] batch commit 只 stage 了本次被更新的 Codex skill 目录
- [ ] commit message 清楚表达“批量同步了过期 Codex skills”
- [ ] commit body 已记录本次范围、被同步的 skills 和各自 `BASELINE_COMMIT`
