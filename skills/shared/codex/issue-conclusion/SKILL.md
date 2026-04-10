---
name: issue-conclusion
description: "关闭 issue 前的总结：回顾问题、尝试过程、最终方案与结果，加 ready-to-close 标签。可选 notification 参数 @lgj 通知重要结论。"
---

# Issue Conclusion — 结题总结

对一个 issue 进行总结收尾，记录完整的问题解决过程。

## 使用方式

```
/issue-conclusion <issue编号>
/issue-conclusion <issue编号> notification    # 重要结论，@lgj 通知
```

## 执行流程

**全部工作通过独立 Codex subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 1: 主进程概括最终成果

在主进程中，概括整个讨论的最终成果（5-10 句话），包含：
- 这个 issue 要解决什么问题
- 做了哪些关键尝试（包括走过的弯路）
- 最终方案是什么
- 产出了什么具体结果
- 有什么遗留问题

### Step 2: 启动 subagent

使用 Codex subagent 启动独立执行者，默认使用：
- `model: gpt-5.4`
- `reasoning_effort: xhigh`

prompt 中包含：
- issue 编号
- 最终成果概括（Step 1 的结果）
- 是否需要 notification

subagent prompt 模板：

```
为 ligenjian001-ai/hft-sdk-issues 的 issue #<N> 撰写 conclusion 并标记 ready-to-close。

## 最终成果概括
{主进程概括的 5-10 句话}

## Notification
{yes/no}

## 执行步骤

1. **读取 issue 全貌**：
   gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues
   gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues --comments
   了解完整的讨论历程。

2. **结合 issue 记录和主进程概括，起草 conclusion**，格式：

## Conclusion (YYYY-MM-DD)

### 问题
{一句话说清楚要解决什么}

### 过程
{按时间线简述关键步骤}
1. {步骤 1}
2. {步骤 2}

### 最终方案
{最终采用的方案，核心设计决策}

### 结果
- {具体产出}

### 遗留
{未解决的问题或后续可做的事；没有就写"无"}

3. **提交 comment**：
   gh issue comment <N> --repo ligenjian001-ai/hft-sdk-issues --body "{conclusion}"

4. **打标签**：
   gh label create "ready-to-close" --repo ligenjian001-ai/hft-sdk-issues --description "Conclusion posted, ready to close" --color "0E8A16" 2>/dev/null || true
   gh issue edit <N> --repo ligenjian001-ai/hft-sdk-issues --add-label "ready-to-close"

5. **如果 notification=yes**：
   gh label create "notification" --repo ligenjian001-ai/hft-sdk-issues --description "Important update, needs attention" --color "E11D48" 2>/dev/null || true
   gh issue edit <N> --repo ligenjian001-ai/hft-sdk-issues --add-label "notification"
   并在 conclusion 末尾追加：
   ---
   cc @ligenjian001-ai

6. **返回结果**：确认 conclusion 已发布，返回 comment URL 和 labels
```

### Step 3: 报告结果

简要告知用户 conclusion 已发布到 #N，已标记 `ready-to-close`。
