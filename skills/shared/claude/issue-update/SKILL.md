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
/issue-update <issue编号> notification              # 重要进展，加 notification 标签并 @lgj
/issue-update <issue编号> notification <补充说明>
```

## 执行流程

**全部工作通过 subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 1: 主进程概括对话进展

在主进程中，概括当前对话中**自上次记录以来**的内容（5-10 句话），包含：
- 讨论了什么话题和探索方向
- 达成了哪些结论/决策（及原因）
- 产出了什么（代码、配置、文件等，写明路径）
- 遗留了什么待解决的问题

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
- issue 编号
- 对话进展概括（Step 1 的结果）
- 是否需要 notification
- 可选的补充说明

subagent prompt 模板：

```
为 ligenjian001-ai/hft-sdk-issues 的 issue #<N> 追加进展 comment。

## 对话进展
{主进程概括的 5-10 句话}

## 补充说明
{用户的补充说明，如有}

## Notification
{yes/no}

## 执行步骤

1. **读取 issue 上下文**：
   gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues
   gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues --comments
   了解之前记录到哪里了。

2. **起草 comment**，格式：

## 进展更新 (YYYY-MM-DD)

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
   gh issue comment <N> --repo ligenjian001-ai/hft-sdk-issues --body "{comment}"

4. **如果 notification=yes**：
   gh label create "notification" --repo ligenjian001-ai/hft-sdk-issues --description "Important update, needs attention" --color "E11D48" 2>/dev/null || true
   gh issue edit <N> --repo ligenjian001-ai/hft-sdk-issues --add-label "notification"
   并在 comment 末尾追加：
   ---
   cc @ligenjian001-ai

5. **返回结果**：确认 comment 已追加，返回 comment URL
```

### Step 3: 报告结果

简要告知用户 comment 已追加到 #N。
