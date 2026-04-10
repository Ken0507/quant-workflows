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

**全部工作通过 subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 1: 主进程概括最终成果

在主进程中，概括整个讨论的最终成果（5-10 句话），包含：
- 这个 issue 要解决什么问题
- 做了哪些关键尝试（包括走过的弯路）
- 最终方案是什么
- 产出了什么具体结果
- 有什么遗留问题

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
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

1. **完整读取 issue 历史（必须！）**：
   gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues
   gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues --comments

   **重要原则**：
   - issue 上的 comments 可能来自多种来源：本次会话的 Claude Code、之前的 Claude 会话、Codex、其他 agent、或人类（cken/lgj 等）
   - 主进程提供的"最终成果概括"只反映**当前 Claude 会话**的视角，可能遗漏其他 agent 或之前会话的产出
   - 因此**必须**完整阅读所有 comment（不要跳读、不要只看最后几条），把每条 comment 都当作独立信息源
   - 对每条 comment，识别其作者、时间、贡献的内容（决策/产出/疑问等）
   - 如果同一话题在不同 comment 中有冲突或迭代，按时间线整理出真实的演进过程

2. **整合所有信息源后起草 conclusion**：
   conclusion 必须综合反映：
   - 当前会话的产出（来自主进程的"最终成果概括"）
   - issue body 的原始定义
   - 所有 comments 的累积贡献（包括非当前会话的）
   
   如果发现某个 comment 提到的产出/决策没有出现在主进程概括中，**必须**纳入 conclusion 而不是忽略。

   格式（**前两行必须是 Time 和 Participants**）：

Time: YYYY-MM-DD HH:MM:SS
Participants: cken + Claude Code

## Conclusion

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
