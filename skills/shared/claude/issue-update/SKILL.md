---
name: issue-update
description: "将当前对话的阶段性进展（方案、决策、实验结果、待办）整理为 comment 追加到已有 issue 上。用于讨论过程中的 checkpoint 记录。"
---

# Issue Update — 进展记录

将当前对话的阶段性成果整理为一条 comment，追加到已有的 issue 上。

## 使用方式

```
/issue-update <issue编号>
/issue-update <issue编号> <可选的补充说明>
/issue-update <仓库名> <issue编号>                 # 指定目标仓库，只写仓库名即可（不用带 owner）
/issue-update <issue编号> notification             # 重要进展，加 notification 标签
/issue-update <issue编号> notification:@<用户名>   # 加标签并在 comment 末尾 cc 该用户
/issue-update <issue编号> notification <补充说明>
```

## 执行流程

**除仓库解析外，全部工作通过 subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 0: 确定目标仓库

按以下优先级确定目标仓库（下文记为 `<REPO>`；后续 gh 命令需要完整 `owner/name`，但用户只需给仓库名）：

1. **用户指定**：参数或对话中明确给出仓库名时直接采用。只给了短名（不带 owner）时，按下方「短名补全」补全。
2. **会话内沿用**：本次对话中已经用 issue 系列 skill 操作过某个仓库（如刚 `/issue-open` 创建了这个 issue），直接沿用。
3. **自动寻找**：优先取当前工作目录的 GitHub remote（`gh repo view --json nameWithOwner -q .nameWithOwner`）；不在 git 仓库时，结合对话上下文和项目 CLAUDE.md 推断（如团队使用专门的 issue 跟踪仓）。**自动找到的仓库必须先向用户确认一句再继续**（如「准备更新 <REPO> 的 #N，对吗？」）。
4. **问用户**：找不到或不确定时直接问，不要猜。

**短名补全**（用户只给了 `name` 没给 owner）：
- 候选 owner = 自己（`gh api user -q .login`）+ 所属 org（`gh api user/orgs -q '.[].login'`）
- 逐个试 `gh api repos/<owner>/<name> -q .full_name`，命中即用
- 极少数情况下多个 owner 有同名仓库，列出让用户选

### Step 1: 主进程概括对话进展

在主进程中，概括当前对话中**自上次记录以来**的内容（5-10 句话），包含：
- 讨论了什么话题和探索方向
- 达成了哪些结论/决策（及原因）
- 产出了什么（代码、配置、文件等，写明路径）
- 遗留了什么待解决的问题

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
- 目标仓库 `<REPO>`（Step 0 的结果）
- issue 编号
- 对话进展概括（Step 1 的结果）
- 是否需要 notification（及 cc 的用户名，如有）
- 可选的补充说明

subagent prompt 模板：

```
为 <REPO> 的 issue #<N> 追加进展 comment。

## 对话进展
{主进程概括的 5-10 句话}

## 补充说明
{用户的补充说明，如有}

## Notification
{no / yes / yes, cc @username}

## 执行步骤

1. **读取 issue 上下文**：
   gh issue view <N> --repo <REPO>
   gh issue view <N> --repo <REPO> --comments
   了解之前记录到哪里了。

2. **起草 comment**，格式（**前两行必须是 Time 和 Participants**；用户名用 `gh api user -q .login` 获取）：

Time: YYYY-MM-DD HH:MM:SS
Participants: {github 用户名} + Claude Code

## 进展更新

### 本次讨论
{2-5 句话概括}

### 决策/结论（如有）
- {决策}：{选择了什么，为什么}

### 产出（如有）
- {具体交付物，含文件路径}

### 待办 / 下一步（如有）
- [ ] {下一步}

格式灵活，按实际内容增减 section。记结论不记过程。

3. **提交 comment**：
   gh issue comment <N> --repo <REPO> --body "{comment}"

4. **如果 notification=yes**：
   gh label create "notification" --repo <REPO> --description "Important update, needs attention" --color "E11D48" 2>/dev/null || true
   gh issue edit <N> --repo <REPO> --add-label "notification"
   如果指定了 cc 用户，在 comment 末尾追加：
   ---
   cc @{username}

5. **返回结果**：确认 comment 已追加，返回 comment URL
```

### Step 3: 报告结果

简要告知用户 comment 已追加到 #N。
