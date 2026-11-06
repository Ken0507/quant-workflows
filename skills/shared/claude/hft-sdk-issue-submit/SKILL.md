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
gh issue list --repo hft-prop/hft-sdk-issues --state open
```

如果有疑似相关的 issue，读取详情再决定是新建还是追评：

```bash
gh issue view <N> --repo hft-prop/hft-sdk-issues
```

**判断原则**：
- 同一根因 + 同一代码位置 → 追评已有 issue，不重复提交
- 相关但不同问题 → 新建 issue 并在正文 Related 字段注明关联编号

---

## 第二步：鉴权确认

```bash
gh auth status
```

确认当前激活账号是 `ken-chen_scale`：输出里 `Logged in to github.com account ken-chen_scale` 下面是 `Active account: true`。hft-prop 是企业组织，要用 `ken-chen_scale` 操作；旧账号 `Ken0507` 不再用于 hft-prop（2026-11 核对：两个账号同时登录时，激活的必须是 `ken-chen_scale`）。

若激活的不是它，切换：

```bash
gh auth switch -u ken-chen_scale
```

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
[RFC] 简短描述设计议题
```

### 正文模板

正文必须以 `🤖 **[cken/claude-code]**` 开头，然后按以下结构组织：

```markdown
🤖 **[cken/claude-code]**

# {标题（与 issue title 一致）}

**Date**: YYYY-MM-DD
**Priority**: 🔴 P0 / 🟡 P1 / 🟢 P2
**Type**: Bug / Infra / Feature / RFC
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
  --repo hft-prop/hft-sdk-issues \
  --title "[BUG] 标题" \
  --label "kind:bug,P1,project:hft_build,agent:claude-code" \
  --body "$(cat <<'ISSUE_BODY'
{正文内容}
ISSUE_BODY
)"
```

**标签组合规则**（2026-11 按仓内现行用法核对）：每条 = 一个或多个 `kind:*` + 优先级 `P0`/`P1`/`P2` + `project:*` + `agent:claude-code`，需要时再加 `system-goal:*`。

| 类型 | kind 标签 | 优先级 | project 标签 |
|------|----------|--------|-------------|
| Bug | `kind:bug` | `P0`/`P1`/`P2` | 按涉及项目选 |
| Infra 需求 | `kind:infra` | `P0`/`P1`/`P2` | 按涉及项目选 |
| Feature | 仓里没有 `kind:feature`：实现类选 `kind:infra`，需先讨论设计选 `kind:rfc` | `P1`/`P2` | 按涉及项目选 |
| 设计讨论（`[RFC]`） | `kind:rfc` | `P0`/`P1`/`P2` | 按涉及项目选 |
| 长周期跟踪 | `kind:tracking` | 视情况 | 按涉及项目选 |

- `project:*` 可选值：`project:hft_build`（HFT C++ 构建与 SDK）、`project:cube_sdk`（cube 数据 SDK）、`project:quant_trading`、`project:workstation_ops`。
- 其余 `kind:*`：`kind:research`、`kind:decision`、`kind:incident`、`kind:goal`。不确定时先 `gh label list --repo hft-prop/hft-sdk-issues` 核对。
- 旧的类型 / 状态标签 `bug`、`infra`、`feature`、`needs-triage`、`confirmed` 仍在仓里，但近期提交不再使用，不要再打。

---

## 第五步：打 agent:claude-code 标签

第四步的命令已经带上 `agent:claude-code`（该标签在仓里已存在）。只有漏打时才需要本步。检查标签是否存在：

```bash
gh label list --repo hft-prop/hft-sdk-issues | grep "agent:claude-code"
```

若不存在，先创建：

```bash
gh label create "agent:claude-code" \
  --repo hft-prop/hft-sdk-issues \
  --description "Submitted by Claude Code" \
  --color "CC317C"
```

然后打到刚提交的 issue 上（用返回的 issue URL 确认编号 N）：

```bash
gh issue edit <N> \
  --repo hft-prop/hft-sdk-issues \
  --add-label "agent:claude-code"
```

---

## 第六步：验证提交结果

```bash
gh issue view <N> --repo hft-prop/hft-sdk-issues --json number,title,labels,state \
  -q '{number: .number, title: .title, state: .state, labels: [.labels[].name]}'
```

确认输出包含：
- `state: OPEN`
- labels 含 `agent:claude-code`、优先级标签（`P0`/`P1`/`P2`）、`kind:*` 标签和 `project:*` 标签

---

## 关键原则（必须遵守）

1. **不引用私有策略代码**：Infra Self-Verification Guide 中只能用框架内通用工具或伪代码，不能引用 `benchmark_100_trader_online` 等提交者私有二进制
2. **Deliverable 具体化**：不写"improve X"，要写具体文件路径 + 行号 + 改动方式
3. **查重优先**：每次提交前必须 list open issues，避免重复
4. **正文以 `🤖 **[cken/claude-code]**` 开头**：标识提交来源

---

## 执行清单

- [ ] `gh issue list` 已查重，无重复
- [ ] `gh auth status` 确认当前激活账号为 ken-chen_scale
- [ ] 标题以 `[BUG]` / `[INFRA]` / `[FEATURE]` / `[RFC]` 开头
- [ ] 标签为 `kind:*` + `P0`/`P1`/`P2` + `project:*` + `agent:claude-code`，不用旧的 `bug` / `infra` / `feature` / `needs-triage`
- [ ] 正文以 `🤖 **[cken/claude-code]**` 开头
- [ ] Verification Guide 不含私有策略代码
- [ ] `gh issue create` 返回了有效 URL
- [ ] `agent:claude-code` 标签已打上
- [ ] `gh issue view` 验证标签和状态正确
