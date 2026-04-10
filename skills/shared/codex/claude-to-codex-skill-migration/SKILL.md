---
name: claude-to-codex-skill-migration
description: "将已有 Claude Code skill 迁移为语义等价的 Codex skill。适用于：在 quant-workflows 中新建或更新某个 Codex skill，对应已有 Claude skill，要求 workflow、提示词、checklist、阈值、禁止项和 references 高保真一致，只允许修改平台绑定部分。"
---

# Claude To Codex Skill Migration

## Goal

把一个已有的 Claude Code skill 迁移成 Codex skill，并保持**语义完全一致**。

默认权威来源永远是 Claude skill。已有 Codex skill 只能作为平台适配参考，不能反向覆盖 Claude 源内容。

## Non-Negotiables

- **Copy-first**：先复制 Claude skill 的完整目录树，再做最小改写。禁止从空白重写 Codex 版。
- **Claude source of truth**：workflow、提示词、checklist、样本规模、阈值、数据纪律、禁止项、退出条件，全部以 Claude skill 为准。
- **只改平台绑定**：只允许修改 Claude/Codex 平台差异、agent 编排表达、工具调用语法、路径和 UI metadata。
- **禁止语义削弱**：不得删除审查维度、不得降低硬约束强度、不得把必须项改成建议项。
- **保留完整目录树**：`SKILL.md`、`references/`、`scripts/`、`assets/` 都要纳入迁移，不只迁主文件。
- **不确定就问用户**：如果 agent 生命周期、跨模型咨询节点、或目标 skill 命名存在多种行为有差异的映射方案，先问用户，不要擅自简化。

## Inputs

迁移前先明确以下信息：

1. Claude 源 skill 目录
2. Codex 目标 skill 目录
3. 这是首次迁移，还是同步更新已有 Codex skill
4. 是否存在用户已明确授权的特例映射

如果用户没有给出目标目录，默认使用与源目录同名的：

```text
skills/<domain>/claude/<skill-name>/
-> skills/<domain>/codex/<skill-name>/
```

只有当仓库已有明确命名约定，或用户显式要求改名时，才更改 skill 名称。

## Workflow

### 1. 盘点源 skill

完整读取 Claude 源 skill 的：

- `SKILL.md`
- `references/`
- `scripts/`
- `assets/`

同时盘点目标 Codex skill 当前状态：

- 是否已存在
- 是否已有 `agents/openai.yaml`
- 是否存在仅属于 Codex 的兼容 skill 或辅助文件

### 2. Copy-first 建立基线

先把 Claude skill 目录树完整复制到 Codex 目标目录，再在复制结果上改写。

如果目标 Codex skill 已存在：

- 仍然以 Claude 源 skill 为基线重新对齐
- 逐项识别已有 Codex 特有改动
- 只保留经过确认的 Codex 平台适配，不把历史漂移继续继承下去

### 3. 迁移 SKILL.md frontmatter 与 UI metadata

Codex `SKILL.md` 前言默认只保留：

- `name`
- `description`

Claude frontmatter 中的额外 UI 字段不得直接丢失：

- `metadata.short-description` -> `agents/openai.yaml` 的 `short_description`
- `metadata.argument-hint` -> 写入 `default_prompt` 或 `SKILL.md` 的 `## Inputs` / 使用说明中

如果目标目录没有 `agents/openai.yaml`，必须创建。

### 4. 只做受控平台改写

允许改动的内容只有以下几类。

#### 4.1 平台身份与路径

- `.claude` -> `.codex`
- Claude skill 路径 -> Codex skill 路径
- Claude 平台标签、来源标识、agent 标签 -> Codex 对应标识
- Claude 专用 skill 入口名 -> 已存在的 Codex 兼容入口名

例：

- `/ob_mode` -> `ob-mode`，前提是仓库已有 Codex 兼容 skill

#### 4.2 Agent 编排语义

把 Claude 的 agent 编排语法翻译为 Codex 的真实 agent 语义，但**不改变角色语义**。

强制规则：

- 源 skill 明确写为**持久化角色**的 Reviewer / Compliance / Logger，在 Codex 中也必须是持久化 subagent
- 持久化角色 = 初次 spawn 后保存 agent id，后续持续 `send_input`
- 源 skill 明确要求独立审查、一次性咨询、或独立饱和审查的，Codex 中默认使用 **fresh consultant subagent**
- 不得因为平台差异，把持久化角色降级成一次性 agent
- 不得把独立审查偷换成主进程自审

如果源 skill 中存在 Claude 主进程通过 Codex MCP 获取外部意见的节点：

- Codex 版默认替换为 `Consultant SubAgent`
- 保留原有触发时机、问题 framing、建议处置表、独立思考纪律

如无用户另行指定，迁移后的 Codex subagents 默认使用：

- `model: gpt-5.4`
- `reasoning_effort: xhigh`

这条默认值适用于：

- `Reviewer SubAgent`
- `Compliance Monitor SubAgent`
- `Logger SubAgent`
- `Consultant SubAgent`
- 其他在迁移过程中新增、且承担认知审查或咨询职责的独立 subagent

为保持后续可扩展性，优先使用**角色名抽象**，例如：

- `Consultant SubAgent`
- `Independent Saturation Review SubAgent`

不要把文案写死成未来难以替换的后端绑定称呼，除非源 skill 的逻辑真的依赖该品牌或工具。

#### 4.3 后台执行语义

区分两类后台行为：

- **认知角色后台运行**：如 Logger / Reviewer / Compliance -> 迁移为 Codex subagent 语义
- **Shell 任务后台运行**：如长时同步、远程命令、守护进程 -> 继续保持为后台命令语义，不要误迁成 subagent

看到 Claude 文案中的 `run_in_background=true` 时，必须先判断它描述的是哪一类后台行为，再转换。

#### 4.4 工具与接口表达

允许替换：

- Claude 专属 agent 调用语法，如 `Agent(...)`
- Claude 专属消息语法，如 `SendMessage(...)`
- Claude 中调用 Codex 的 MCP 接口，如 `mcp__codex__codex`

但不允许因此删除对应的流程节点、职责或约束。

### 5. references/ scripts/ assets 的迁移规则

- `references/` 默认逐文件复制，只有出现平台绑定表达时才做最小改写
- `scripts/` 默认原样保留，除非脚本硬编码了 Claude 路径或 Claude CLI 行为
- `assets/` 默认原样保留

任何 reference 或 prompt template 的删段、压缩、概括性重写，默认都视为不合规。

### 6. 保留语义，不保留残差

迁移后必须主动扫描并清理以下常见残差：

- `Claude`
- `claude`
- `mcp__codex__codex`
- `Agent(`
- `SendMessage(`
- `run_in_background`
- `~/.claude`
- `/ob_mode`

如果这些字样仍然保留，必须逐条判断：

- 是不是源 skill 逻辑本身必须提及
- 还是未完成的平台迁移残差

### 7. 生成或更新 `agents/openai.yaml`

读取迁移后的 skill 内容，生成：

- `display_name`
- `short_description`
- `default_prompt`

要求：

- `display_name`：简洁、稳定、面向人
- `short_description`：优先吸收 Claude 的 `short-description`
- `default_prompt`：要明确这是什么 skill、何时使用、以及关键授权前提

如果该 skill 强依赖多 agent 协作，`default_prompt` 中应写明：

- 可以使用 sub-agents / multi-agent parallel work
- 如用户此前已给出一次性授权，应在 prompt 中体现，不要重复询问

### 8. 逐项 fidelity audit

迁移完成后，必须对照 `references/fidelity_audit.md` 执行审计。

重点检查：

- 有无删段
- 有无 prompt rubric 丢失
- 有无 checklist 项丢失
- 有无样本规模、阈值、日期范围漂移
- 有无把 must 改成 should / recommend
- 有无把双角色语义压扁成单角色自审

## Allowed Changes

只有以下改动默认允许：

1. Claude/Codex 平台身份字样、路径、标签
2. Claude agent 编排语法 -> Codex agent 编排语义
3. Claude 外部 Codex 咨询节点 -> Codex fresh consultant subagent
4. Claude UI frontmatter -> Codex `agents/openai.yaml`
5. 已存在 Codex 兼容 skill 的调用名映射

## Forbidden Changes

以下改动默认禁止：

1. 删除或压缩 prompt 审查维度
2. 删除 checklist 项、gate、退出条件、异常终止协议
3. 把硬约束改弱，例如：
   - `must` -> `should`
   - `禁止` -> `建议避免`
4. 修改样本规模、阈值、数据墙、日期范围、因子数量门槛
5. 把持久化角色改成一次性 agent
6. 把独立审查改成主进程自审
7. 丢弃 `references/`、`scripts/` 或 `assets/`
8. 静默丢弃 `argument-hint` 之类无直接字段映射的信息

## When To Ask The User

遇到以下情况必须先问用户：

- 源 skill 的 agent 生命周期写得不清楚，且不同映射会影响行为
- 源 skill 使用了跨模型咨询，而 Codex 侧存在多种独立性不同的替代方案
- 目标 Codex skill 已有大量人工改动，无法判断哪些是已批准适配、哪些是历史漂移
- 源 skill 名称是否应该在 Codex 侧改名，存在歧义

## Deliverables

完成迁移时，至少产出：

1. 迁移后的 Codex skill 目录
2. `agents/openai.yaml`
3. 一份简洁差异摘要，按以下三类说明：
   - 平台绑定替换
   - agent 编排替换
   - 需要用户确认的未决项

## Final Check

在结束前，再次确认：

- 目标 Codex skill 是从 Claude skill 拷贝而来，不是重新发挥写出来的
- 目标文件树没有漏掉 `references/`、`scripts/`、`assets/`
- 所有删除的文本都能用“平台绑定改写”解释
- 如果某段删除无法用平台绑定解释，就恢复 Claude 源内容

审计细则见 `references/fidelity_audit.md`。
