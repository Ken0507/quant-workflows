---
name: hft-sdk-issue-submit
description: "向 lgj 的 hft-sdk-issues 仓库提交 Bug / Feature / Infra Request。覆盖完整流程：查重、鉴权确认、标签管理、正文起草（按 README 模板）、提交、agent:claude-code 标签打标。"
---

# HFT SDK Issue 提交

## 使用场景

当你需要向 lgj 报告 SDK/Playground/Matcher 的问题或提出改进请求时使用。
支持三种类型：`[BUG]`、`[INFRA]`、`[FEATURE]`。

---

## 第一步：查重（必须先做）

提交前先列出现有 open issues，判断是否已有重复或高度相关的 issue：

```bash
gh issue list --repo ligenjian001-ai/hft-sdk-issues --state open
```

如果有疑似相关的 issue，读取详情再决定是新建还是追评：

```bash
gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues
```

**判断原则**：
- 同一根因 + 同一代码位置 → 追评已有 issue，不重复提交
- 相关但不同问题 → 新建 issue 并在正文 Related 字段注明关联编号

---

## 第二步：鉴权确认

```bash
gh auth status
```

确认输出包含 `Logged in to github.com account Ken0507`，且 `Active account: true`。

若未登录，执行：

```bash
gh auth login
```

---

## 第三步：起草 Issue 正文

### 标题格式

```
[BUG] 简短描述问题（动词+名词，<50字）
[INFRA] 简短描述需求
[FEATURE] 简短描述功能
```

### 正文模板

正文必须以 `🤖 **[cken/claude-code]**` 开头，然后按以下结构组织：

```markdown
🤖 **[cken/claude-code]**

# {标题（与 issue title 一致）}

**Date**: YYYY-MM-DD
**Priority**: 🔴 P0 / 🟡 P1 / 🟢 P2
**Type**: Bug / Feature / Tool
**Related**: #{N}（如有关联 issue）

---

## 问题描述

{描述现象、根因、代码位置（文件名+行号）}

### 根因代码（如是 Bug）

```cpp
// 文件路径 + 行号
// 贴出有问题的代码片段
```

### 观测到的行为偏差

{用表格对比预期行为 vs 实际行为}

---

## What I Need

### Deliverable：{修复/工具名称} (P0/P1/P2)

**What**: {一句话说明要做什么}

**改动说明**（如是代码修复）：

```cpp
// 改动前
// 改动后
```

**修复后的预期行为**：
1. {行为 1}
2. {行为 2}

---

## Why I Need This

1. {业务影响}
2. {风险影响}

---

## Files Involved

- `path/to/file.h` — {修改说明}

---

## Infra Self-Verification Guide

> 验证步骤不得引用提交者的私有策略代码，只能用框架级单元测试或 infra 侧可访问的工具验证。

### Step 1：复现问题

```bash
# 可直接运行的命令，不依赖提交者策略
```

### Step 2：验证修复

```python
# 验证脚本，使用通用数据路径
```

---

## Verification Criteria

| # | Test Case | Expected Result | Tolerance |
|---|-----------|-----------------|-----------|
| 1 | {测试场景} | {预期输出} | — |
| 2 | ... | ... | — |

## Success Definition

- [ ] {完成标准 1}
- [ ] {完成标准 2}
- [ ] 在 ≥2 天数据 / ≥3 标的上验证通过
```

### 优先级选择

| 优先级 | 含义 | 示例 |
|--------|------|------|
| P0 | 阻塞生产（回测完全无法运行、实盘崩溃）| Matcher 崩溃、数据读取失败 |
| P1 | 影响效率/准确性，有手动绕过方案 | 回测系统性偏差、工具缺失 |
| P2 | 体验改进，不影响核心功能 | 文档优化、日志格式改进 |

---

## 第四步：提交 Issue

```bash
gh issue create \
  --repo ligenjian001-ai/hft-sdk-issues \
  --title "[BUG] 标题" \
  --label "bug,P1,needs-triage" \
  --body "$(cat <<'ISSUE_BODY'
{正文内容}
ISSUE_BODY
)"
```

**标签组合规则**：

| 类型 | 必选标签 | 优先级标签 | 状态标签 |
|------|----------|-----------|---------|
| Bug  | `bug` | `P0`/`P1`/`P2` | `needs-triage` |
| Infra 需求 | `infra` | `P0`/`P1`/`P2` | `needs-triage` |
| Feature | `feature` | `P1`/`P2` | `needs-triage` |

---

## 第五步：打 agent:claude-code 标签

检查 `agent:claude-code` 标签是否已存在：

```bash
gh label list --repo ligenjian001-ai/hft-sdk-issues | grep "agent:claude-code"
```

若不存在，先创建：

```bash
gh label create "agent:claude-code" \
  --repo ligenjian001-ai/hft-sdk-issues \
  --description "Submitted by Claude Code" \
  --color "CC317C"
```

然后打到刚提交的 issue 上（用返回的 issue URL 确认编号 N）：

```bash
gh issue edit <N> \
  --repo ligenjian001-ai/hft-sdk-issues \
  --add-label "agent:claude-code"
```

---

## 第六步：验证提交结果

```bash
gh issue view <N> --repo ligenjian001-ai/hft-sdk-issues --json number,title,labels,state \
  -q '{number: .number, title: .title, state: .state, labels: [.labels[].name]}'
```

确认输出包含：
- `state: OPEN`
- labels 含 `agent:claude-code`、优先级标签、类型标签、`needs-triage`（或已被 lgj 变更为 `confirmed`）

---

## 关键原则（必须遵守）

1. **不引用私有策略代码**：Infra Self-Verification Guide 中只能用框架内通用工具或伪代码，不能引用 `benchmark_100_trader_online` 等提交者私有二进制
2. **Deliverable 具体化**：不写"improve X"，要写具体文件路径 + 行号 + 改动方式
3. **查重优先**：每次提交前必须 list open issues，避免重复
4. **正文以 `🤖 **[cken/claude-code]**` 开头**：标识提交来源

---

## 执行清单

- [ ] `gh issue list` 已查重，无重复
- [ ] `gh auth status` 确认登录为 Ken0507
- [ ] 标题以 `[BUG]` / `[INFRA]` / `[FEATURE]` 开头
- [ ] 正文以 `🤖 **[cken/claude-code]**` 开头
- [ ] Verification Guide 不含私有策略代码
- [ ] `gh issue create` 返回了有效 URL
- [ ] `agent:claude-code` 标签已打上
- [ ] `gh issue view` 验证标签和状态正确
