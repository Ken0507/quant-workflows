---
name: issue-open
description: "为当前讨论的话题在 hft-sdk-issues 创建一个结构化 issue。梳理背景知识、关联 issue、问题现状，作为讨论的持久化载体。用于研究讨论、平台迭代、方案设计等场景。"
---

# Issue Open — 开题记录

为当前对话中的话题创建一个 GitHub issue，作为讨论记录的载体。

## 使用方式

```
/issue-open <话题标题或一句话描述>
/issue-open <话题标题> notification    # 重要话题，加 notification 标签并 @lgj
/issue-open                            # 无参数时从当前对话上下文推断话题
```

## 执行流程

**全部工作通过 subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 1: 主进程概括对话上下文

在主进程中，用 2-5 句话简要概括当前对话中与本话题相关的内容：
- 讨论了什么话题
- 达成了哪些初步结论
- 还有什么待解决的问题

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
- 话题标题 / 用户参数
- 对话上下文概括（Step 1 的结果）
- 是否需要 notification
- 完整的执行指令（见下方 subagent prompt 模板）

subagent prompt 模板：

```
在 hft-prop/hft-sdk-issues 创建一个讨论/迭代 issue。

## 话题
{话题标题或描述}

## 对话上下文
{主进程概括的 2-5 句话}

## Notification
{yes/no}

## 执行步骤

1. **搜索关联 issue**：用 2-3 个关键词搜索
   gh issue list --repo hft-prop/hft-sdk-issues --search "<keyword>" --state all --limit 10 --json number,title,state,labels
   对高度相关的 issue，用 gh issue view <N> 读取详情

2. **确定 labels**：
   - 类型 label（必选一个）：`discussion`（纯讨论）/ `infra`（框架迭代）/ `feature`（新功能）
   - 项目 label（如适用）：project:quant_trading / project:cube_sdk / project:workstation_ops / project:hft_build
   - 来源 label：agent:claude-code
   - 不加 P0/P1/P2 和 needs-triage

3. **起草 issue 正文**。

   **正文风格（硬规则）**：
   - 只写：问题/疑问本身、背景事实与数据、约束/红线、中性的开放问题（不能 hint 答案）、关联 issue/docs/路径。
   - 默认禁写：**尚未拍板**的推荐方案、milestone 拆解（M1/M2…）、待办 checklist、多选项对比表、带「建议」语气的句子。Issue 是登记问题供后续推进的载体，过早 propose 未定方案会锚定讨论。
   - **例外**：方案/决策**已在对话中讨论拍板**的，应当如实记录（如 #158 已敲定的本机日报方案、#164 已落地的 skill）。判据是「定了没」——已定的方案/已发生的事实要写，未定的提案不写。
   - **拿不准就问**：若某段内容（尤其方案是否算「已拍板」）不确定该不该写进 issue，先向用户确认，不要自行决定。

   格式（**前两行必须是 Time 和 Participants**）：

Time: YYYY-MM-DD HH:MM:SS
Participants: cken + Claude Code

# {话题标题}

**Type**: Discussion / Design / Research

---

## 背景
{当前状况是什么，为什么要讨论这个话题}

## 问题/目标
{希望解决什么问题或达成什么目标}

## 关联 Issue
- **#N** {title} — {为什么相关}

## 当前对话摘要
{对话到目前为止的关键信息点}

4. **创建 issue**：
   确保 label 存在（不存在则先创建）：
   gh label create "<label>" --repo hft-prop/hft-sdk-issues --description "<desc>" --color "<color>" 2>/dev/null || true

   gh issue create --repo hft-prop/hft-sdk-issues --title "{title}" --label "{labels}" --body "{body}"
   gh issue edit <N> --repo hft-prop/hft-sdk-issues --add-label "agent:claude-code"

5. **如果 notification=yes**：
   gh label create "notification" --repo hft-prop/hft-sdk-issues --description "Important update, needs attention" --color "E11D48" 2>/dev/null || true
   gh issue edit <N> --repo hft-prop/hft-sdk-issues --add-label "notification"
   并在 body 末尾追加：
   ---
   cc @genjian-li_scale

6. **返回结果**：issue 编号、URL、标题、labels
```

### Step 3: 报告结果

将 subagent 返回的 issue 编号和 URL 告知用户，提示后续可用 `/issue-update <N>` 追加进展。
