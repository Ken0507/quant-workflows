---
name: issue-search
description: "Search a GitHub repo's issues by keyword, topic, or label. Used standalone during conversation, or internally by issue-open to find related context."
---

# Issue Search

在目标 GitHub 仓库中搜索相关 issue。

## 使用方式

```
/issue-search <关键词或话题描述>
/issue-search <仓库名> <关键词>    # 指定目标仓库，只写仓库名即可（不用带 owner）
/issue-search label:<label名>      # 按 label 过滤
/issue-search                      # 无参数时从当前对话上下文推断搜索词
```

## 执行流程

**除仓库解析外，全部工作通过独立 Codex subagent 完成，不在主进程中执行搜索命令。**

### Step 0: 确定目标仓库

按以下优先级确定目标仓库（下文记为 `<REPO>`；后续 gh 命令需要完整 `owner/name`，但用户只需给仓库名）：

1. **用户指定**：参数或对话中明确给出仓库名时直接采用。只给了短名（不带 owner）时，按下方「短名补全」补全。
2. **会话内沿用**：本次对话中 issue 系列 skill 已操作过某个仓库，直接沿用。
3. **自动寻找**：优先取当前工作目录的 GitHub remote（`gh repo view --json nameWithOwner -q .nameWithOwner`）；不在 git 仓库时，结合对话上下文和项目说明文件 推断（如团队使用专门的 issue 跟踪仓）。**自动找到的仓库必须先向用户确认一句再继续**（如「准备在 <REPO> 上搜索，对吗？」）。
4. **问用户**：找不到或不确定时直接问，不要猜。

**短名补全**（用户只给了 `name` 没给 owner）：
- 候选 owner = 自己（`gh api user -q .login`）+ 所属 org（`gh api user/orgs -q '.[].login'`）
- 逐个试 `gh api repos/<owner>/<name> -q .full_name`，命中即用
- 极少数情况下多个 owner 有同名仓库，列出让用户选

### Step 1: 确定搜索词

如果用户提供了参数，直接使用。否则从当前对话上下文提炼 1-3 个搜索关键词。

### Step 2: 启动 subagent

使用 Codex subagent 启动独立执行者，默认使用：
- `model: gpt-5.4`
- `reasoning_effort: xhigh`

prompt 中包含：
- 搜索关键词
- 搜索目标：`<REPO>`

subagent prompt 模板：

```
在 <REPO> 中搜索以下关键词相关的 issue：{keywords}

执行步骤：
1. 对每个关键词执行：gh issue list --repo <REPO> --search "<keyword>" --state all --limit 15 --json number,title,state,labels,createdAt
2. 如果指定了 label 过滤：gh issue list --repo <REPO> --label "<label>" --state all --limit 15
3. 合并去重，按相关性分层（高度相关 / 可能相关）
4. 对高度相关的 issue（最多 3 个），用 gh issue view <N> --repo <REPO> 读取摘要

输出格式：
- 表格列出所有结果（#, State, Title, Labels, Date）
- 分层说明每个相关 issue 为什么相关（一句话）
```

### Step 3: 展示结果

将 subagent 返回的搜索结果直接展示给用户。
