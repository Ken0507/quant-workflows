---
name: issue-conclusion
description: "关闭 issue 前的总结：回顾问题、尝试过程、最终方案与结果，加 ready-to-close 标签。可选 notification 参数通知相关人重要结论。"
---

# Issue Conclusion — 结题总结

对一个 issue 进行总结收尾，记录完整的问题解决过程。

## 使用方式

```
/issue-conclusion <issue编号>
/issue-conclusion <仓库名> <issue编号>                 # 指定目标仓库，只写仓库名即可（不用带 owner）
/issue-conclusion <issue编号> notification             # 重要结论，加 notification 标签
/issue-conclusion <issue编号> notification:@<用户名>   # 加标签并在结论末尾 cc 该用户
```

## 执行流程

**除仓库解析外，全部工作通过 subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 0: 确定目标仓库

按以下优先级确定目标仓库（下文记为 `<REPO>`；后续 gh 命令需要完整 `owner/name`，但用户只需给仓库名）：

1. **用户指定**：参数或对话中明确给出仓库名时直接采用。只给了短名（不带 owner）时，按下方「短名补全」补全。
2. **会话内沿用**：本次对话中已经用 issue 系列 skill 操作过某个仓库，直接沿用。
3. **自动寻找**：优先取当前工作目录的 GitHub remote（`gh repo view --json nameWithOwner -q .nameWithOwner`）；不在 git 仓库时，结合对话上下文和项目 CLAUDE.md 推断（如团队使用专门的 issue 跟踪仓）。**自动找到的仓库必须先向用户确认一句再继续**（如「准备给 <REPO> 的 #N 写结题总结，对吗？」）。
4. **问用户**：找不到或不确定时直接问，不要猜。

**短名补全**（用户只给了 `name` 没给 owner）：
- 候选 owner = 自己（`gh api user -q .login`）+ 所属 org（`gh api user/orgs -q '.[].login'`）
- 逐个试 `gh api repos/<owner>/<name> -q .full_name`，命中即用
- 极少数情况下多个 owner 有同名仓库，列出让用户选

### Step 1: 主进程概括最终成果

在主进程中，概括整个讨论的最终成果（5-10 句话），包含：
- 这个 issue 要解决什么问题
- 做了哪些关键尝试（包括走过的弯路）
- 最终方案是什么
- 产出了什么具体结果
- 有什么遗留问题

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
- 目标仓库 `<REPO>`（Step 0 的结果）
- issue 编号
- 最终成果概括（Step 1 的结果）
- 是否需要 notification（及 cc 的用户名，如有）

subagent prompt 模板：

```
为 <REPO> 的 issue #<N> 撰写 conclusion 并标记 ready-to-close。

## 最终成果概括
{主进程概括的 5-10 句话}

## Notification
{no / yes / yes, cc @username}

## 执行步骤

1. **完整读取 issue 历史（必须！）**：
   gh issue view <N> --repo <REPO>
   gh issue view <N> --repo <REPO> --comments

   **重要原则**：
   - issue 上的 comments 可能来自多种来源：本次会话的 Claude Code、之前的 Claude 会话、其他 agent（Codex 等）、或人类团队成员
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

   格式（**前两行必须是 Time 和 Participants**；用户名用 `gh api user -q .login` 获取）：

Time: YYYY-MM-DD HH:MM:SS
Participants: {github 用户名} + Claude Code

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
   gh issue comment <N> --repo <REPO> --body "{conclusion}"

4. **打标签**：
   gh label create "ready-to-close" --repo <REPO> --description "Conclusion posted, ready to close" --color "0E8A16" 2>/dev/null || true
   gh issue edit <N> --repo <REPO> --add-label "ready-to-close"

5. **如果 notification=yes**：
   gh label create "notification" --repo <REPO> --description "Important update, needs attention" --color "E11D48" 2>/dev/null || true
   gh issue edit <N> --repo <REPO> --add-label "notification"
   如果指定了 cc 用户，在 conclusion 末尾追加：
   ---
   cc @{username}

6. **返回结果**：确认 conclusion 已发布，返回 comment URL 和 labels
```

### Step 3: 报告结果

简要告知用户 conclusion 已发布到 #N，已标记 `ready-to-close`。
