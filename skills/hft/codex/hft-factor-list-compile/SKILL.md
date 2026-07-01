---
name: hft-factor-list-compile
description: "将多个深度研究报告（ob_research/{N}-{topic}）的因子定义合并整理成一份标准化的 FA*_factor_list.md 文档。调用格式：/hft-factor-list-compile 3-6 -> FA20（研究编号3到6合并为FA20）或 /hft-factor-list-compile 3,5,8 -> FA21（指定编号合并）。整理完成后由独立 Codex Reviewer SubAgent 检查口径一致性和无歧义性。"
---
# 因子列表编译（Factor List Compile）

> 将多个 `/hft-deep-factor-research` 产出的研究报告合并整理为一份标准化的 `FA*_factor_list.md`，供后续 `hft-playground-factor-write` 使用。

## 0. 参数解析

**调用格式**（两种）：
- 范围：`/hft-factor-list-compile 2-4 -> FA19`（研究编号 2、3、4 合并为 FA19）
- 列表：`/hft-factor-list-compile 3,5,8 -> FA20`（研究编号 3、5、8 合并为 FA20）

**解析规则**：
- `->` 左边：研究编号（对应 `ob_research/{N}-{topic}/` 目录）
- `->` 右边：目标因子集编号（输出到 `factor_agent_docs/{FA编号}_factor_list.md`）

```bash
# 示例：/hft-factor-list-compile 3,4 -> FA20
# 输入：
#   ob_research/3-vol_of_vol_asymmetry/factor_definition.md
#   ob_research/3-vol_of_vol_asymmetry/research_report.md
#   ob_research/4-quote_staleness/factor_definition.md
#   ob_research/4-quote_staleness/research_report.md
# 输出：
#   factor_agent_docs/FA20_factor_list.md

OB_ROOT="/home/cken/hft_projects/HFTPool/ob_research"
OUT_DIR="/home/cken/hft_projects/HFTPool/factor_agent_docs"
```

## 1. 强制前置步骤

### 1.1 验证输入研究完整性与合规分级

对每个输入的研究编号，检查以下文件是否存在：
- `ob_research/{N}-{topic}/factor_definition.md`（必须存在）
- `ob_research/{N}-{topic}/research_report.md`（必须存在）
- `ob_research/{N}-{topic}/quality_review.md`（应该存在）

**准入规则**：
- **factor_definition.md 不存在 → 排除**，不收录该研究（如研究未完成、仅有 mechanism-stage 候选而无定稿因子定义）。在最终 factor_list §7 "已排除因子"中记录排除原因。
- **factor_definition.md 存在 → 收录**，无论研究的 Phase gate 是否全部通过。

**合规分级**（对所有收录的研究执行）：

读取 `quality_review.md` 和 `research_report.md`，对每个研究判定合规等级：

| 等级 | 条件 | 处理方式 |
|------|------|---------|
| **正常** | Phase 1-3（或 1-4）全部 PASS 或 CONDITIONAL PASS（仅含非阻塞项） | 因子进入 factor_list §3 正文 |
| **警告** | 存在以下任意一项：(1) Phase 1 未通过/不合规；(2) Phase 2/3 有未解决的 blocking 项；(3) research_report 含已知数据错误；(4) Phase 终审 pending/未触发；(5) Reviewer 轮次缺失（blocking 级别）；(6) factor_definition 与验证代码存在不一致 | 因子**同样进入** factor_list §3 正文（保证工程可实现），但同时写入 `FA{N}_warning_factors.md` 警告报告 |

**输出**：生成两个列表供后续步骤使用：
- `normal_sessions[]`：合规等级为"正常"的研究编号
- `warning_sessions[]`：合规等级为"警告"的研究编号，以及每个研究的具体警告原因

### 1.2 通读全部输入

逐一阅读每个研究的：
1. `factor_definition.md` — 因子精确定义
2. `research_report.md` — 完整研究过程（重点关注 §5 最终因子定义、§2 失败因子档案、§7 已知限制）
3. `quality_review.md` — Reviewer 终审意见（关注未解决的条件/风险）

### 1.3 阅读参考文档

- `/home/cken/hft_projects/HftKnowledge/research_docs/data.md` — 数据字段定义
- `/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md` — 采样口径、实现规范
- 参考已有 factor_list 的格式：`factor_agent_docs/FA15_factor_list.md`（结构模板）

### 1.4 无歧义七要素预检

**在开始编写前**，对每个研究报告的 factor_definition.md 逐因子检查七要素完整性：

| # | 要素 | 检查 |
|---|------|------|
| 1 | 触发事件 | 事件类型 + side + guard 条件是否明确？ |
| 2 | 输入变量 | 字段引用是否精确？snap 来源是否明确？ |
| 3 | 计算公式 | 是数学公式还是自然语言？ |
| 4 | 参数值 | 精确数值 + 单位 + h_bar 换算？ |
| 5 | 状态管理 | state/amount + 初始值 + bar-reset 行为？ |
| 6 | 输出范围 | 精确值域 + 边界返回值？ |
| 7 | 边界条件 | 空盘口/首bar/低活跃期/除零/极端值？ |

**如果某因子七要素不完整**：在编译过程中补充（基于 research_report.md 的上下文推断），但必须标记为"编译时补充"，在审阅时重点检查。

---

## 2. 编译流程

### 2.1 因子合并与去重

- 汇总所有研究（含 normal 和 warning）的保留因子
- 检查跨研究的因子名冲突（不同研究产出同名因子 → 需要加前缀区分或合并）
- 检查跨研究的因子冗余（不同研究产出高度相关的因子 → 标注，建议后续验证）
- **warning 因子不做特殊隔离**：在 §3 因子定义中与 normal 因子混排（按主题分组），但在每个 warning 因子的"已知限制"末尾追加一行：`⚠️ 本因子来自流程不完整的研究 #{N}，详见 FA{FA编号}_warning_factors.md`

### 2.2 分组设计

将合并后的因子按主题分组（参考来源研究的分组），确保：
- 每组有明确的主题名
- 组内因子在微观机制上相关
- 跨组因子在逻辑上独立

### 2.3 共用结构识别（可选优化）

检查多个因子是否共享计算逻辑：
- 多个因子使用相同的 EMA 更新？
- 多个因子依赖相同的中间变量（如 is_nice_lot, price_bucket）？
- 多个因子需要 prev_snap？

如果发现显著的共享结构，在 factor_list 的 §2 中描述共用工具/数据结构建议（不含 C++ 代码，描述逻辑和接口）。标注："建议由独立 code agent 实现共用结构，并由独立审阅 agent 验证口径一致性和性能。"

### 2.4 生成 factor_list.md

按以下结构生成文档：

```markdown
# FA{N} 因子集：{主题概述}

## §0 概述
- 来源研究：ob_research/{编号1}-{主题1}, ob_research/{编号2}-{主题2}, ...
- **溯源研究报告路径**（供后续工程实现阶段追溯因子设计意图）：
  - `ob_research/{编号1}-{主题1}/research_report.md`
  - `ob_research/{编号1}-{主题1}/factor_definition.md`
  - ... （逐个列出）
- 因子总数：X 个（Y 组）
- 因子分组总表（编号 / 名称 / 组 / 类型标记 / 来源研究）
- 主预测口径：ret_lag0_next100 ~ next200 (bar_aggtrans_time_1)
- 与 benchmark0323_top100 的关系（增量/正交性/已知冗余）

## §1 数据依赖简述
- 使用的事件类型：ORDER / FILL / OrderBook snapshot
- 关键字段引用表：
  | 字段 | 来源 | 说明 | data.md 章节 |
  |------|------|------|-------------|
  | event.order->volume | ORDER 事件 | 委托手数(张) | §X.X |
  | ... | ... | ... | ... |
- prev_snap 使用说明（如有因子需要）
- ⚠️ 完整 API 定义见 data.md 和 factor_workflow.md

## §2 共用结构建议（可选）
- 跨因子共享的计算逻辑描述
- 建议的共用数据结构接口
- ⚠️ 具体实现由独立 code agent 负责，需独立审阅验证

## §3 因子定义（核心）
### 分组 X：{主题}
#### {fa_name}
- **物理含义**：1-2句
- **微观机制来源**：ob_research/{N} 的哪个发现
- **触发事件**：EVENT_TYPE + side + guard（精确）
- **输入变量**：字段引用表
- **计算公式**：数学公式（精确，无自然语言替代）
- **参数**：
  | 参数名 | 值 | 单位 | h_bar 换算 | 选取理由 |
- **状态管理**：state/amount，初始值，bar-reset
- **输出范围**：[min, max] + 边界行为（除零→?，样本不足→?）
- **边界条件**：空盘口/首bar/低活跃期处理
- **类型标记**：A/B/AB/R + IC 摘要
- **已知限制**：流动性条件、时段效应、与 baseline 冗余度

## §4 采样口径
- 统一引用团队口径（bar_aggtrans_time_1, is_continuous && is_session_end）
- 所有输出列名表
- state vs amount 分类

## §5 参数总览
- 所有因子参数汇总表

## §6 因子完整清单
- 表格（编号 / 名称 / 类型 / 含义 / 输出范围 / 来源研究）

## §7 已排除因子
- 来自各研究的失败因子汇总（名称 / 原因 / 来源研究）
- 无 factor_definition.md 的研究编号及排除原因

## §8 验证检查项
- 每个因子的值域检查规则
- 预期均值/方差范围（来自研究报告的统计数据）
- 常见实现陷阱（来自研究过程中发现的坑）

## §9 实现注意事项
- 事件过滤表（因子组 → 触发事件 → 方向条件）
- 关键引用：data.md §X、factor_workflow.md §Y
```

---

## 3. 独立 Codex Reviewer SubAgent

**编译完成后，启动独立 Codex Reviewer SubAgent（必须是独立 subagent，不是主进程自审）。**

Reviewer SubAgent 需要阅读：
1. 全部输入研究报告的 `factor_definition.md`（原始定义）
2. 生成的 `FA*_factor_list.md`（编译结果）
3. `FA*_warning_factors.md`（如存在）
4. `data.md`（验证字段引用正确性）

### 审阅维度

**A. 完整性检查：**
- [ ] 每个输入研究的每个保留因子是否都在 factor_list 中有对应条目？
- [ ] 是否有遗漏的因子？是否有多出的因子？
- [ ] 每个因子的七要素是否全部填写？

**B. 口径一致性检查：**
- [ ] factor_list 中的计算公式是否与原始 factor_definition.md 完全等价？
- [ ] 参数值是否一致（数值、单位）？
- [ ] 输出范围是否一致？
- [ ] 类型标记（A/B/AB/R）是否一致？
- [ ] 已知限制是否完整保留？

**C. 无歧义检查：**
- [ ] 每个因子的触发事件是否精确到事件类型 + side + guard？
- [ ] 计算公式是否为数学公式（非自然语言）？
- [ ] 参数是否精确到数值 + 单位 + h_bar？
- [ ] 边界条件（除零、空盘口、首bar）是否每个都有明确返回值？
- [ ] **对照测试**：随机选 3 个因子，模拟"如果我是实现者，读完定义后是否有任何需要问的问题？"如果有 → 不通过。

**D. 跨研究一致性：**
- [ ] 不同研究的因子之间是否有命名冲突？
- [ ] 不同研究使用的数据字段引用是否一致（同一字段是否用了不同的名字）？
- [ ] 共用结构建议是否正确反映了实际的共享关系？

**E. data.md 合规性：**
- [ ] 字段引用表中的每个字段是否在 data.md 中存在且描述一致？
- [ ] prev_snap 使用方式是否符合 data.md 的说明？

**F. 警告因子审查（当 warning_factors.md 存在时）：**
- [ ] 每个 warning 因子的七要素定义本身是否完整可实现？（不看流程合规，只看定义质量）
- [ ] warning 报告中的"对工程实现的影响"判断是否准确？
- [ ] 是否有 warning 因子的定义质量差到不应收录的程度（如七要素缺 3 个以上、IC 来自未修复的 bug 数据）？如果有 → 建议从 factor_list 移除

### 审阅流程

```
1. Reviewer SubAgent 产出审阅意见（通过 / 有条件通过 / 不通过 + 具体问题列表）
2. 如果不通过 → 主进程修正 factor_list
3. Reviewer SubAgent 二次确认
4. 通过后 → factor_list.md 定稿
```

审阅意见输出到 `factor_agent_docs/FA{N}_review.md`。

---

## 3.5 警告因子报告生成

**当 `warning_sessions[]` 非空时**，生成 `factor_agent_docs/FA{N}_warning_factors.md`。

### 报告结构

```markdown
# FA{N} 警告因子报告

> 本报告记录来自流程不完整研究的因子。这些因子已有明确的七要素定义和初步 IC 验证，
> 但其研究流程存在合规缺陷，工程实现时应关注下列风险项。
> 因子定义本身已收录至 FA{N}_factor_list.md 正文，本报告仅补充风险说明。

## 汇总表

| 研究编号 | 主题 | 因子数 | 警告等级 | 核心问题 |
|---------|------|--------|---------|---------|
| #{N1} | ... | X | PHASE_GATE / DATA_INTEGRITY / DEFINITION_MISMATCH / REVIEW_PENDING | 一句话 |

## 逐研究详情

### #{N} — {topic}

**警告类别**：{PHASE_GATE | DATA_INTEGRITY | DEFINITION_MISMATCH | REVIEW_PENDING}

**涉及因子**：
- {factor_name_1}
- {factor_name_2}
- ...

**具体问题**：
{从 quality_review.md 提取的 blocking items / 未通过的 Phase gate / 数据错误描述}

**对工程实现的影响**：
{判断：因子定义本身是否可信？IC 是否可能因流程问题而失真？参数是否与验证代码一致？}

**建议处理方式**：
- [ ] {具体修复建议，如"补执行 R11/R12 Reviewer"、"更新 factor_definition.md 参数至 V5 定稿值"等}
```

### 警告类别定义

| 类别 | 含义 | 典型场景 |
|------|------|---------|
| `PHASE_GATE` | 研究的某个 Phase gate 未通过或未触发 | Phase 1 不合规（Reviewer 轮数不足）、Phase 终审未执行 |
| `DATA_INTEGRITY` | 研究报告中存在已知数据错误 | report 含被 REJECT 证伪的 IC 数字、report 与 log 不同步 |
| `DEFINITION_MISMATCH` | factor_definition.md 与实际验证代码/参数存在不一致 | 定义写 hl=50 但验证用 hl=30、timing filter 代码与定义不匹配 |
| `REVIEW_PENDING` | Phase 终审或 Reviewer 存在 pending/缺失 | R11/R12 Reviewer 未返回、Phase 3/4 终审 pending |

---

## 4. 交付物

| 文件 | 路径 | 说明 |
|------|------|------|
| factor_list | `factor_agent_docs/FA{N}_factor_list.md` | 标准化因子定义文档（含所有有定义的因子） |
| review | `factor_agent_docs/FA{N}_review.md` | 审阅意见 |
| warning_factors | `factor_agent_docs/FA{N}_warning_factors.md` | 警告因子报告（仅当存在 warning session 时生成） |
