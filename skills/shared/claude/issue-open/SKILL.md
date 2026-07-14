---
name: issue-open
description: "为当前讨论的话题在目标 GitHub 仓库创建一个结构化 issue。梳理背景知识、关联 issue、问题现状，作为讨论的持久化载体。用于研究讨论、平台迭代、方案设计等场景。"
---

# Issue Open — 开题记录

为当前对话中的话题创建一个 GitHub issue，作为讨论记录的载体。

## 使用方式

```
/issue-open <话题标题或一句话描述>
/issue-open <仓库名> <话题标题>                 # 指定目标仓库，只写仓库名即可（不用带 owner）
/issue-open <话题标题> notification             # 重要话题，加 notification 标签
/issue-open <话题标题> notification:@<用户名>   # 加标签并在正文末尾 cc 该 GitHub 用户
/issue-open                                     # 无参数时从当前对话上下文推断话题
```

## 执行流程

**除仓库解析外，全部工作通过 subagent 完成，不在主进程中执行 gh 命令或起草内容。**

### Step 0: 确定目标仓库

按以下优先级确定目标仓库（下文记为 `<REPO>`；后续 gh 命令需要完整 `owner/name`，但用户只需给仓库名）：

1. **用户指定**：参数或对话中明确给出仓库名时直接采用。只给了短名（不带 owner）时，按下方「短名补全」补全。
2. **会话内沿用**：本次对话中 issue 系列 skill 已操作过某个仓库，直接沿用。
3. **自动寻找**：优先取当前工作目录的 GitHub remote（`gh repo view --json nameWithOwner -q .nameWithOwner`）；不在 git 仓库时，结合对话上下文和项目 CLAUDE.md 推断（如团队使用专门的 issue 跟踪仓）。**自动找到的仓库必须先向用户确认一句再继续**（如「准备在 <REPO> 上操作，对吗？」）。
4. **问用户**：找不到或不确定时直接问，不要猜。

**短名补全**（用户只给了 `name` 没给 owner）：
- 候选 owner = 自己（`gh api user -q .login`）+ 所属 org（`gh api user/orgs -q '.[].login'`）
- 逐个试 `gh api repos/<owner>/<name> -q .full_name`，命中即用
- 极少数情况下多个 owner 有同名仓库，列出让用户选

### Step 1: 主进程概括对话上下文

在主进程中，用 2-5 句话简要概括当前对话中与本话题相关的内容：
- 讨论了什么话题
- 达成了哪些初步结论
- 还有什么待解决的问题

### Step 1.5: 判定 System Goal 归属

每条新 issue 须在正文标明所属 System Goal（完整 URL），供 Goal Dashboard 回填时把 Commit → PR → Issue → System Goal 串起来。

**当前 System Goal 注册表**（Goal 变更时更新此表）：
- 基本面线：https://github.com/hft-prop/alpha-roadmap/issues/26
- 高频线：https://github.com/hft-prop/hft-sdk-issues/issues/183

主进程结合对话上下文判定归属，三档：
- **确定归属某条 Goal** → 标 `System Goal: <完整 URL>`
- **疑似相关但不确定** → 标 `Candidate System Goal: <完整 URL>`
- **无法判断** → 整行省略，**不要硬猜**（回填系统会自行提出 Candidate）

介于确定与不确定之间时，先问用户一句再定档，不要自行决定。

### Step 2: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含：
- 目标仓库 `<REPO>`（Step 0 的结果）
- 话题标题 / 用户参数
- 对话上下文概括（Step 1 的结果）
- System Goal 判定结果（Step 1.5 的结果）
- 是否需要 notification（及 cc 的用户名，如有）
- 完整的执行指令（见下方 subagent prompt 模板）

subagent prompt 模板：

```
在 <REPO> 创建一个讨论/迭代 issue。

## 话题
{话题标题或描述}

## 对话上下文
{主进程概括的 2-5 句话}

## Notification
{no / yes / yes, cc @username}

## System Goal
{none / System Goal: <完整 URL> / Candidate System Goal: <完整 URL>}

## 执行步骤

1. **搜索关联 issue**：用 2-3 个关键词搜索
   gh issue list --repo <REPO> --search "<keyword>" --state all --limit 10 --json number,title,state,labels
   对高度相关的 issue，用 gh issue view <N> --repo <REPO> 读取详情

2. **确定 labels**：
   - 先看仓库现有 label 体系：gh label list --repo <REPO> --limit 100
   - 类型 label（必选一个，不存在则后续创建）：`discussion`（纯讨论）/ `infra`（框架/基础设施迭代）/ `feature`（新功能）
   - 团队自有的分类 label（如 project:*、模块名等）：按仓库现有体系酌情选用，不要新发明
   - 来源 label：`agent:claude-code`（标记该 issue 由 agent 创建）
   - 不加优先级类 label（P0/P1/P2、needs-triage 等），留给人工 triage

3. **起草 issue 正文**。

   **正文风格（硬规则）**：
   - 只写：问题/疑问本身、背景事实与数据、约束/红线、中性的开放问题（不能 hint 答案）、关联 issue/docs/路径。
   - 默认禁写：**尚未拍板**的推荐方案、milestone 拆解（M1/M2…）、待办 checklist、多选项对比表、带「建议」语气的句子。Issue 是登记问题供后续推进的载体，过早 propose 未定方案会锚定讨论。
   - **例外**：方案/决策**已在对话中讨论拍板**的，应当如实记录。判据是「定了没」——已定的方案/已发生的事实要写，未定的提案不写。
   - **拿不准就问**：若某段内容（尤其方案是否算「已拍板」）不确定该不该写进 issue，先向用户确认，不要自行决定。

   格式（**前两行必须是 Time 和 Participants**；用户名用 `gh api user -q .login` 获取）：

Time: YYYY-MM-DD HH:MM:SS
Participants: {github 用户名} + Claude Code

# {话题标题}

**Type**: Discussion / Design / Research
{System Goal 非 none 时紧跟一行，原样写入主进程给出的标注，如 `System Goal: https://github.com/hft-prop/alpha-roadmap/issues/26`；none 则整行省略}

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
   gh label create "<label>" --repo <REPO> --description "<desc>" --color "<color>" 2>/dev/null || true

   gh issue create --repo <REPO> --title "{title}" --label "{labels}" --body "{body}"
   gh issue edit <N> --repo <REPO> --add-label "agent:claude-code"

5. **如果 notification=yes**：
   gh label create "notification" --repo <REPO> --description "Important update, needs attention" --color "E11D48" 2>/dev/null || true
   gh issue edit <N> --repo <REPO> --add-label "notification"
   如果指定了 cc 用户，在 body 末尾追加：
   ---
   cc @{username}

6. **返回结果**：issue 编号、URL、标题、labels
```

### Step 3: 报告结果

将 subagent 返回的 issue 编号和 URL 告知用户，提示后续可用 `/issue-update <N>` 追加进展。
