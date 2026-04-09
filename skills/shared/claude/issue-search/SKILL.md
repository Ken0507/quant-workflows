---
name: issue-search
description: "Search hft-sdk-issues for related issues by keyword, topic, or label. Used standalone during conversation, or internally by issue-open to find related context."
---

# Issue Search

在 `ligenjian001-ai/hft-sdk-issues` 中搜索相关 issue。

## 使用方式

```
/issue-search <关键词或话题描述>
/issue-search label:project:quant_trading
/issue-search          # 无参数时从当前对话上下文推断搜索词
```

## 执行流程

**全部工作通过 subagent 完成，不在主进程中执行搜索命令。**

### Step 1: 确定搜索词

如果用户提供了参数，直接使用。否则从当前对话上下文提炼 1-3 个搜索关键词。

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
- 搜索关键词
- 搜索目标：`ligenjian001-ai/hft-sdk-issues`

subagent prompt 模板：

```
在 ligenjian001-ai/hft-sdk-issues 中搜索以下关键词相关的 issue：{keywords}

执行步骤：
1. 对每个关键词执行：gh issue list --repo ligenjian001-ai/hft-sdk-issues --search "<keyword>" --state all --limit 15 --json number,title,state,labels,createdAt
2. 如果指定了 label 过滤：gh issue list --repo ligenjian001-ai/hft-sdk-issues --label "<label>" --state all --limit 15
3. 合并去重，按相关性分层（高度相关 / 可能相关）
4. 对高度相关的 issue（最多 3 个），用 gh issue view <N> 读取摘要

输出格式：
- 表格列出所有结果（#, State, Title, Labels, Date）
- 分层说明每个相关 issue 为什么相关（一句话）
```

### Step 3: 展示结果

将 subagent 返回的搜索结果直接展示给用户。
