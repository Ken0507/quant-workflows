---
name: claude-to-codex-skill-batch-sync
description: "检查 quant-workflows 中现有的 Codex skills 是否落后于对应 Claude 源 skill，并对有更新的 skill 逐个做增量同步。适用于：批量巡检 shared/hft/crypto/all 范围内的已有 Codex skills；不新建缺失的 Codex sibling，只更新已经存在的那些。"
---

# Claude To Codex Skill Batch Sync

## Goal

批量检查 quant-workflows 中**已经存在的 Codex skills**，找出哪些对应的 Claude 源 skill 在其基线 commit 之后又发生了更新，然后只对这些命中的 skill 逐个做增量同步。

这个 skill 是**批量编排器**，不是首次迁移工具，也不是单 skill 增量同步器。

- 首次迁移：使用 `$claude-to-codex-skill-migration`
- 单个已有 skill 的增量同步：使用 `$claude-to-codex-skill-sync`

## Scope

支持的范围参数：

- `all`：默认。检查 `shared`、`hft`、`crypto`
- `shared`
- `hft`
- `crypto`

使用方式：

```text
$claude-to-codex-skill-batch-sync
$claude-to-codex-skill-batch-sync all
$claude-to-codex-skill-batch-sync shared
$claude-to-codex-skill-batch-sync hft
$claude-to-codex-skill-batch-sync crypto
```

## Non-Negotiables

- **只扫描现有 Codex skills**：只遍历 `skills/<scope>/codex/` 中已经存在的 skill 目录。
- **不新建 skill**：即使发现某个 Claude skill 变了但根本没有 Codex sibling，也只报告，不创建。
- **逐个处理**：对每个命中的 outdated skill，逐个调用 `$claude-to-codex-skill-sync` 的逻辑，不做 ad hoc patch。
- **基线仍来自目标 Codex skill**：每个 skill 的是否过期，都以该 skill 自己最近一次 Codex commit 为基线。
- **Codex-only skills 允许跳过**：如果一个 Codex skill 没有 Claude 对应源，它不算错误，只记为 skip。
- **先扫描后修改**：先完成全量扫描和分类，再开始逐个同步，避免半程切换导致统计不一致。

## Inputs

批量检查前先明确：

1. 范围参数：`all/shared/hft/crypto`
2. 是否允许实际执行同步，还是仅做 dry-run 报告
3. 是否存在用户已明确批准的 Codex 特例映射

如果用户没有特别说明：

- 默认范围：`all`
- 默认行为：**扫描并直接同步命中的已有 Codex skills**

## Workflow

### 1. 读取依赖 skill

先读取并遵守：

- `skills/shared/codex/claude-to-codex-skill-sync/SKILL.md`
- `skills/shared/codex/claude-to-codex-skill-sync/references/sync_audit.md`
- `skills/shared/codex/claude-to-codex-skill-migration/SKILL.md`

本 skill 不复制单 skill 同步细节，只负责批量筛选、排序、调度和汇总。

### 2. 解析范围

将用户输入映射为要扫描的目录集合：

- `all` -> `shared`, `hft`, `crypto`
- `shared` -> `shared`
- `hft` -> `hft`
- `crypto` -> `crypto`

如果用户给出未知范围，先问用户，不要猜测。

### 3. 枚举现有 Codex skills

对每个选中的 category，只遍历：

```text
skills/<category>/codex/<skill-name>/
```

得到候选列表。

注意：

- 只看 repo 内已有目录
- 不看 `~/.codex/skills/` 软链接层
- 不把缺失的 Codex sibling 加入候选

### 4. 为每个候选 skill 建立匹配关系

对每个候选 Codex skill：

1. 计算对应 Claude 源路径：
   `skills/<category>/claude/<same-skill-name>/`
2. 分三类：
   - **matched**：Claude 源存在
   - **codex-only**：Claude 源不存在
   - **ambiguous**：路径映射不清楚或历史 rename 无法稳定判断

处理原则：

- `matched`：进入下一步基线检查
- `codex-only`：记为 skip，不报错
- `ambiguous`：暂停该 skill，记入待确认列表

### 5. 为每个 matched skill 判断是否过期

对每个 `matched` skill：

1. 找到目标 Codex skill 最近一次 commit：

```bash
git log -1 --format=%H -- skills/<category>/codex/<skill-name>/
```

2. 将该 commit 记为该 skill 的 `BASELINE_COMMIT`
3. 列出这个基线之后、触及 Claude 源 skill 路径的 commits：

```bash
git log --reverse --format=%H BASELINE_COMMIT..HEAD -- skills/<category>/claude/<skill-name>/
```

4. 分类：
   - **up-to-date**：区间内无 Claude commits
   - **outdated**：区间内有 >=1 个 Claude commits
   - **blocked**：基线无法确定，或 `Claude@BASELINE_COMMIT` 无法稳定读取

### 6. 输出扫描摘要

在真正修改前，先形成一张批量摘要：

- 扫描了多少 Codex skills
- 其中多少 `matched`
- 多少 `codex-only`
- 多少 `up-to-date`
- 多少 `outdated`
- 多少 `blocked`

并列出每个 `outdated` skill：

- category
- skill name
- `BASELINE_COMMIT`
- 基线后触及 Claude 源的 commit 列表

### 7. 逐个同步 outdated skills

若本次不是 dry-run：

按固定顺序逐个处理 `outdated` skills：

1. `shared`
2. `hft`
3. `crypto`
4. 同一 category 内按 skill name 排序

对每个命中的 skill：

- 调用 `$claude-to-codex-skill-sync`
- 输入该 skill 的 Claude 源目录和 Codex 目标目录
- 保留该 skill 的 `BASELINE_COMMIT`、Claude commits 列表和同步摘要

如果某个 skill 在同步中遇到需要用户确认的分支：

- 停止后续同步
- 先把已完成 / 未完成状态汇总给用户
- 不要在存在歧义时继续批量推进

### 8. 不要把批量扫描误做成首次迁移

本 skill 的候选集只来自**已有 Codex skill**。因此：

- 不主动枚举 Claude-only skills
- 不自动创建缺失的 Codex sibling
- 需要首次迁移时，让用户显式调用 `$claude-to-codex-skill-migration`

### 9. 最终汇总

最终至少报告以下四组结果：

1. **synced**：本次已成功同步的 skills
2. **up-to-date**：已是最新，无需动作
3. **codex-only skipped**：没有 Claude 对应源的 Codex skills
4. **blocked**：因歧义或未决确认而暂停的 skills

## Allowed Changes

默认允许：

1. 扫描选定范围内所有已有 Codex skills 的 baseline 状态
2. 只对 `outdated` 的已有 Codex skills 执行增量同步
3. 跳过没有 Claude 对应源的 Codex-only skills

## Forbidden Changes

默认禁止：

1. 因为扫描到 Claude 更新，就直接新建缺失的 Codex skill
2. 跳过单 skill sync，直接在批量 skill 中手写 patch
3. 在没有形成全量扫描摘要前就开始修改
4. 对 `blocked` skill 擅自选择一种映射继续同步
5. 把 `codex-only` skill 误报成异常

## When To Ask The User

遇到以下情况必须先问用户：

- 用户给出的范围参数不合法
- 某个 skill 的 Claude/Codex 路径映射存在 rename / move 歧义
- 某个 skill 的工作树已有未提交本地改动，无法判断是否要保留
- 批量过程中某个命中的 skill 进入 `$claude-to-codex-skill-sync` 的待确认分支

## Deliverables

完成后，至少产出：

1. 一份扫描摘要
2. 对每个 `outdated` skill 的基线信息与 commit 列表
3. 更新后的 Codex skill 目录（仅限命中的已有 skills）
4. 一份最终分类汇总：`synced / up-to-date / codex-only skipped / blocked`

## Final Check

结束前再次确认：

- 本次没有新建任何缺失的 Codex sibling
- 所有实际修改都来自单 skill sync 逻辑，而不是批量 skill 自己重写
- 每个被同步的 skill 都有自己的 `BASELINE_COMMIT`
- 最终报告能清楚回答“哪些更新了，哪些没动，哪些没覆盖，为什么”
