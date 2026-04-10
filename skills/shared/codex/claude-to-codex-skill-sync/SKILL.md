---
name: claude-to-codex-skill-sync
description: "将单个已存在的 Codex skill 与其 Claude 源 skill 的后续更新做增量同步，并在成功后提交 repo commit 推进该 skill 的同步基线。适用于：quant-workflows 中某个 Claude skill 更新后，需要以该 Codex skill 上次更新 commit 为基线，分析之后的 Claude commits，并只同步发生变化的部分；平台绑定边界与 claude-to-codex-skill-migration 保持一致。"
---

# Claude To Codex Skill Sync

## Goal

把一个**已存在**的 Codex skill，与其对应 Claude skill 在后续 commit 中发生的更新做**增量同步**，同时保持 Codex 平台适配语义不被冲掉，并在同步完成后创建一个 scoped git commit，让该 skill 的同步基线真正前移。

这不是首次迁移工具。若目标 Codex skill 不存在，回退到 `$claude-to-codex-skill-migration`。

## Non-Negotiables

- **单 skill 范围**：一次只处理一个 skill，不做批量同步。
- **基线来自 Codex**：以目标 Codex skill 最近一次被创建或更新的 commit 作为同步基线。
- **Claude source of truth**：基线之后，所有非平台绑定的语义变化都以 Claude 源 skill 为准。
- **边界复用 migration skill**：平台绑定、agent 编排、Consultant 替换、后台执行语义、`agents/openai.yaml` 处理规则，全部复用 `$claude-to-codex-skill-migration`。
- **同步的是变更，不只是添加**：允许新增、替换、删除、重命名；禁止把“同步”误做成只追加内容。
- **覆盖整个 skill tree**：`SKILL.md`、`references/`、`scripts/`、`assets/` 都在同步范围内。
- **commit-aware，不是 patch 盲抄**：commit 用来理解“为什么改”；最终同步依据是 `Claude@baseline_commit` 与 `Claude@HEAD` 的区间差异。
- **同步成功后必须 commit**：如果实际改动了 Codex skill 而不提交，下次运行时 `BASELINE_COMMIT` 不会前移，skill 会被重复识别为 outdated。

## Inputs

同步前先明确以下信息：

1. Claude 源 skill 目录
2. Codex 目标 skill 目录
3. 是否存在用户已明确批准的 Codex 特例映射
4. 目标 Codex skill 当前是否有未提交的本地改动

如果用户没有给出路径，默认使用与 migration skill 相同的同名映射：

```text
skills/<domain>/claude/<skill-name>/
-> skills/<domain>/codex/<skill-name>/
```

## Workflow

### 1. 读取同步边界

先读取并遵守以下文件：

- `skills/shared/codex/claude-to-codex-skill-migration/SKILL.md`
- `skills/shared/codex/claude-to-codex-skill-migration/references/fidelity_audit.md`

本 skill 不重新定义平台适配边界，只增加“如何基于 commit 增量同步”的流程。

### 2. 解析源 / 目标路径

确认：

- Claude 源 skill 存在
- Codex 目标 skill 存在

如果 Codex 目标 skill 不存在：

- 不做增量同步
- 视为首次迁移场景
- 若用户已明确接受回退到首次迁移流程，则改用 `$claude-to-codex-skill-migration`
- 否则先问用户

### 3. 检查工作区状态

优先检查与本次 skill 相关的路径是否已有未提交改动：

- `skills/<domain>/claude/<skill-name>/`
- `skills/<domain>/codex/<skill-name>/`

如果 Codex 目标 skill 已有未提交改动，且无法明确判断这些改动是否属于本次同步前的人工 override：

- 先问用户
- 不要把本地工作树误当作“上次已同步状态”

### 4. 找到同步基线 commit

用 git 找到**最近一次触及目标 Codex skill 路径**的 commit：

```bash
git log -1 --format=%H -- skills/<domain>/codex/<skill-name>/
```

该 commit 记为：

- `BASELINE_COMMIT`

它表示“当前 Codex skill 最后一次被正式更新时，repo 里看到的完整状态”。

然后读取同一 commit 下的 Claude 源 skill 快照，作为：

- `Claude@BASELINE_COMMIT`

如果在 `BASELINE_COMMIT` 时 Claude 源路径不存在，或无法稳定映射到当前 Claude skill：

- 先问用户
- 不要擅自猜测 rename / move 历史

### 5. 审阅基线之后的 Claude commits

列出自 `BASELINE_COMMIT` 之后、所有触及 Claude 源 skill 路径的 commits：

```bash
git log --reverse --format=fuller BASELINE_COMMIT..HEAD -- skills/<domain>/claude/<skill-name>/
```

对这些 commits：

- 逐个阅读 commit message
- 按需阅读对应 diff / hunk
- 目标是理解这次更新的**意图和边界**

如果这个区间内没有任何 Claude commits：

- 报告“无需同步”
- 不改 Codex skill

### 6. 计算真正需要同步的语义差异

以完整树对比：

- `Claude@BASELINE_COMMIT`
- `Claude@HEAD`

对 skill tree 内的文件分类：

1. **新增文件**
2. **修改文件**
3. **删除文件**
4. **重命名文件**
5. **未变化文件**

同步范围只针对 1-4 类；5 保持 Codex 现状不动。

### 7. 将差异映射到 Codex skill

#### 7.1 新增文件

- 如果 Claude 新增了 `references/`、`scripts/`、`assets/` 文件，默认复制到 Codex 对应位置
- 如新增内容含平台绑定表达，再按 migration 规则做最小改写

#### 7.2 修改文件

对修改的文件，保留 Codex 已存在的平台适配，只同步 Claude 的语义增量。

典型做法：

- `SKILL.md`：同步 workflow、阈值、禁止项、checklist、使用说明等语义更新；保留 Codex 特有平台绑定改写
- `references/*`：默认高保真同步；只有平台绑定表达才最小改写
- `scripts/*`：如果只是语义逻辑更新，应同步；如果含 Claude CLI / 路径硬编码，再做平台适配

#### 7.3 删除文件

如果 Claude 在基线之后删除了某个文件：

- 对应的 Codex 文件也应删除

但以下内容默认不跟随 Claude 删除：

- `agents/openai.yaml`
- 仅为 Codex 平台适配存在的辅助文件

如无法判断某文件是“历史漂移”还是“Codex 必需适配文件”，先问用户。

#### 7.4 重命名文件

如果 Claude 对 skill tree 内文件做了 rename / move：

- Codex 默认镜像同样的重命名
- 但若新路径与 Codex 兼容结构冲突，先问用户

### 8. Codex-owned surfaces 不得被盲覆盖

以下位置允许根据 Claude 的新语义做**重新表达**，但不能盲拷贝回 Claude 原文：

- `.claude` -> `.codex`
- Claude agent 编排语法 -> Codex subagent 语义
- Claude 外部 Codex 咨询节点 -> `Consultant SubAgent`
- `run_in_background` 的平台映射
- Codex 技能入口名映射
- `agents/openai.yaml`

原则：

- **同步语义 delta**
- **保留 Codex 平台表达**

### 9. 更新 `agents/openai.yaml`

如果以下任一内容发生变化：

- skill 的触发场景
- `description`
- `metadata.short-description`
- `argument-hint`
- 工作流的关键授权前提

就必须重新检查并按需更新 `agents/openai.yaml` 的：

- `display_name`
- `short_description`
- `default_prompt`

要求仍与 migration skill 一致：明确“这是什么、何时使用、关键授权前提是什么”。

### 10. 双重审计

同步完成后，必须执行两层审计：

1. 先执行本 skill 的 `references/sync_audit.md`
2. 再执行 migration skill 的 `references/fidelity_audit.md`

只有两层都通过，才允许交付。

### 11. 提交同步结果

如果本次同步实际修改了目标 Codex skill：

1. 只 stage 本次目标 skill 目录内的改动：

```bash
git add skills/<domain>/codex/<skill-name>/
```

2. 创建一个 scoped commit，推荐格式：

```text
Sync <skill-name> Codex skill from latest Claude updates
```

3. commit body 至少记录：
   - `BASELINE_COMMIT`
   - 本次读取的 Claude commits 列表
4. 默认追加：

```text
Co-authored-by: Codex <codex@openai.com>
```

如果本次最终判断为 no-op：

- 不创建空 commit

## Allowed Changes

默认允许：

1. 将 `BASELINE_COMMIT..HEAD` 区间内 Claude 源 skill 的语义更新同步到 Codex
2. 按 migration skill 规则对平台绑定部分做最小 Codex 改写
3. 删除基线后已被 Claude 删除、且并非 Codex 平台专属的文件
4. 重命名 / 移动与 Claude 源一致的文件
5. 按需刷新 `agents/openai.yaml`
6. 在同步成功后为目标 skill 创建一个 scoped git commit

## Forbidden Changes

默认禁止：

1. 只看最近一条 commit 就下结论，不看完整区间历史
2. 只把新内容追加到 Codex，而不处理替换 / 删除 / rename
3. 直接用 Claude 原文覆盖 Codex 平台绑定区域
4. 因为“这次没改到那一段”就跳过 `references/` / `scripts/` / `assets/` 的 diff 检查
5. 把 Codex 目标 skill 当前工作树误当作已提交基线
6. 略过最终 audit
7. 实际更新了 skill 却不提交，导致基线不前移

## When To Ask The User

遇到以下情况必须先问用户：

- Codex 目标 skill 不存在，且用户未明确允许回退到 migration skill
- `BASELINE_COMMIT` 时 Claude 源路径不存在，或 rename / move 历史不清楚
- Codex 目标 skill 存在未提交本地改动，无法判断是否要保留
- Claude 在平台绑定段落发生了复杂更新，存在多种 Codex 映射方案
- 目标 Codex skill 的历史人工改动很多，无法区分哪些是已批准 override、哪些是历史漂移

## Deliverables

完成同步时，至少产出：

1. 更新后的 Codex skill 目录
2. 更新后的 `agents/openai.yaml`（如需要）
3. 一份简洁摘要，至少说明：
   - `BASELINE_COMMIT`
   - 基线后读取了哪些 Claude commits
   - 同步了哪些文件 / 片段
   - 保留了哪些 Codex 特有平台适配
   - 哪些地方需要用户确认
4. 如本次存在实际改动：提交后的 commit hash

## Final Check

结束前再次确认：

- 这次是对**已有 Codex skill**做增量同步，不是首次迁移
- `Claude@BASELINE_COMMIT -> Claude@HEAD` 的变更已完整审阅
- 同步动作不仅覆盖新增，也覆盖替换、删除、rename
- 所有平台绑定改写都能用 migration skill 的边界解释
- 如果某个变化是否该同步拿不准，已经向用户升级，而不是自行简化
