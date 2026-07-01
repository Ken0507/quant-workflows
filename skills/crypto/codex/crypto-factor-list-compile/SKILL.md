---
name: crypto-factor-list-compile
description: "将多个深度研究报告（crypto_ob_research/{N}-{topic}）的因子定义合并整理成一份标准化的 FA*_factor_list.md 文档。调用格式：/crypto-factor-list-compile 3-6 -> FA20（研究编号3到6合并为FA20）或 /crypto-factor-list-compile 3,5,8 -> FA21（指定编号合并）。整理完成后由独立 Codex Reviewer SubAgent 检查口径一致性和无歧义性。"
---
# Crypto 因子列表编译（Factor List Compile）

> 将多个 `/crypto-deep-factor-research` 产出的研究报告合并整理为一份标准化的 `FA*_factor_list.md`，供后续 `crypto-realize-factor` 使用。

## 0. 参数解析

**调用格式**（两种）：
- 范围：`/crypto-factor-list-compile 2-4 -> FA19`（研究编号 2、3、4 合并为 FA19）
- 列表：`/crypto-factor-list-compile 3,5,8 -> FA20`（研究编号 3、5、8 合并为 FA20）

**解析规则**：
- `->` 左边：研究编号（对应 `crypto_ob_research/{N}-{topic}/` 目录）
- `->` 右边：目标因子集编号（输出到 `factor_agent_docs/{FA编号}_factor_list.md`）

```bash
# 示例：/crypto-factor-list-compile 3,4 -> FA20
# 输入：
#   crypto_ob_research/3-liquidity-geometry-fair-price/factor_definition.md
#   crypto_ob_research/3-liquidity-geometry-fair-price/research_report.md
#   crypto_ob_research/4-orderbook-cog-centroid/factor_definition.md
#   crypto_ob_research/4-orderbook-cog-centroid/research_report.md
# 输出：
#   factor_agent_docs/FA20_factor_list.md

OB_ROOT="/home/cken/crypto_world/crypto_ob_research"
OUT_DIR="/home/cken/crypto_world/factor_agent_docs"
```

## 1. 强制前置步骤

### 1.1 验证输入研究完整性与合规分级

对每个输入的研究编号，检查以下文件是否存在：
- `crypto_ob_research/{N}-{topic}/factor_definition.md`（必须存在）
- `crypto_ob_research/{N}-{topic}/research_report.md`（必须存在）
- `crypto_ob_research/{N}-{topic}/quality_review.md`（应该存在）

**准入规则**：
- **factor_definition.md 不存在 -> 排除**，不收录该研究（如研究未完成、仅有 mechanism-stage 候选而无定稿因子定义）。在最终 factor_list §7 "已排除因子"中记录排除原因。
- **factor_definition.md 存在 -> 收录**，无论研究的 Phase gate 是否全部通过。

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

- `/home/cken/crypto_world/zebra/docs/研究员使用手册.md` — Zebra Agent 框架、AggTrans 字段定义（§7）、OrderBook API（§8）、编写规范
- `/home/cken/crypto_world/zebra/docs/design_orderbook_extension.md` — OrderBook 扩展设计文档（数据结构、内置原语、时间同步、chunk 模式）
- 参考已有 factor_list 的格式（如存在）：`factor_agent_docs/` 下最新的 `FA*_factor_list.md`（结构模板）
- 参考已有因子池了解 baseline：
  - `/home/cken/crypto_world/zebra_pool/f001/agents/base30_agent.h` — 30 个基础因子
  - `/home/cken/crypto_world/zebra_pool/f002/agents/f002_agent.h` — 39 个扩展因子
  - `/home/cken/crypto_world/zebra_pool/f002/factor_design_report.md` — f002 设计文档

### 1.4 无歧义七要素预检

**在开始编写前**，对每个研究报告的 factor_definition.md 逐因子检查七要素完整性：

| # | 要素 | 检查 |
|---|------|------|
| 1 | 触发事件 | 事件类型（OnAggTrans / OnBarClose / OnBookUpdate）+ side + guard 条件是否明确？使用 OB 的因子是否标注在哪个回调中调用 `ctx.GetBook()`？ |
| 2 | 输入变量 | 字段引用是否精确？数据来源（AggTrans 字段 / OrderBook API / DataStore）是否明确？OB 原语调用（如 `depth_imbalance_levels(20)`, `cost_buy_bps(target)`）是否精确到参数？ |
| 3 | 计算公式 | 是数学公式还是自然语言？ |
| 4 | 参数值 | 精确数值 + 单位 + bar 数换算？ |
| 5 | 状态管理 | state 变量 + 初始值 + bar-reset 行为？ |
| 6 | 输出范围 | 精确值域 + 边界返回值？ |
| 7 | 边界条件 | 首bar/低活跃期/除零/极端值？ |

**如果某因子七要素不完整**：在编译过程中补充（基于 research_report.md 的上下文推断），但必须标记为"编译时补充"，在审阅时重点检查。

---

## 2. 编译流程

### 2.1 因子合并与去重

- 汇总所有研究（含 normal 和 warning）的保留因子
- 检查跨研究的因子名冲突（不同研究产出同名因子 -> 需要加前缀区分或合并）
- 检查跨研究的因子冗余（不同研究产出高度相关的因子 -> 标注，建议后续验证）
- 检查与 baseline（f001 + f002 共 69 因子）的冗余度 -> 标注已知冗余
- **warning 因子不做特殊隔离**：在 §3 因子定义中与 normal 因子混排（按主题分组），但在每个 warning 因子的"已知限制"末尾追加一行：`WARNING: 本因子来自流程不完整的研究 #{N}，详见 FA{FA编号}_warning_factors.md`

### 2.2 分组设计

将合并后的因子按主题分组（参考来源研究的分组），确保：
- 每组有明确的主题名
- 组内因子在微观机制上相关
- 跨组因子在逻辑上独立

### 2.3 共用结构识别（可选优化）

检查多个因子是否共享计算逻辑：
- 多个因子使用相同的 EMA 更新？
- 多个因子依赖相同的中间变量（如 sweep 分类、价格层级）？
- 多个因子需要 prev bar 的状态？
- 多个因子使用相同的 OrderBook 原语调用（如多个因子都需要 `depth_imbalance_levels(20)`）？→ 标注可在 OnBarClose 中一次调用、缓存结果
- 多个因子使用相同的 OB 区间参数（如 0-5bps, 5-10bps 分层）？→ 标注统一定义分层常量

如果发现显著的共享结构，在 factor_list 的 §2 中描述共用工具/数据结构建议（不含 C++ 代码，描述逻辑和接口）。标注："建议由独立 code agent 实现共用结构，并由独立审阅 agent 验证口径一致性和性能。"

### 2.4 生成 factor_list.md

按以下结构生成文档：

```markdown
# FA{N} 因子集：{主题概述}

## §0 概述
- 来源研究：crypto_ob_research/{编号1}-{主题1}, crypto_ob_research/{编号2}-{主题2}, ...
- **溯源研究报告路径**（供后续工程实现阶段追溯因子设计意图）：
  - `crypto_ob_research/{编号1}-{主题1}/research_report.md`
  - `crypto_ob_research/{编号1}-{主题1}/factor_definition.md`
  - ... （逐个列出）
- 因子总数：X 个（Y 组）
- 因子分组总表（编号 / 名称 / 组 / 类型标记 / 来源研究）
- 主预测口径：ret_lag0_next100 ~ next200（AmountBar 时间轴）
  - **Label basis = mid-to-mid**（issue #119 之后）：`ret_lag0_nextH` 底层由 `basic_table.mid` 计算（`mid[t+H]/mid[t]-1`），列名不变但语义已切换，不再是 close-to-close
- 与 baseline（f001+f002, 69 因子）的关系（增量/正交性/已知冗余）

## §1 数据依赖简述
- 使用的事件类型：AggTrans / OnBookUpdate / OrderBook (via ctx.GetBook())
- 是否需要 OrderBook：RequiresOrderBook() = true/false
- 是否需要逐次 L2 回调：RequiresBookUpdates() = true/false
- 关键字段引用表：
  | 字段 | 来源 | 说明 | 研究员使用手册章节 |
  |------|------|------|--------------------|
  | agg.side | AggTrans | 聚合成交方向 (buy/sell) | §7 |
  | agg.amount_sum() | AggTrans | 聚合成交额 (USDT) | §7 |
  | agg.price_first/last | AggTrans | 首末成交价 | §7 |
  | book.depth_imbalance_levels(n) | OrderBook | 前 N 档深度不平衡 | §8 |
  | book.cost_buy_bps(notional) | OrderBook | 买入执行成本 (bps) | §8 |
  | book.cost_asymmetry_bps(notional) | OrderBook | 成本非对称性 | §8 |
  | book.cog_signed_bps(inner, outer) | OrderBook | 签名加权重心 | §8 |
  | book.side_depth_bps(side, inner, outer) | OrderBook | 区间深度 | §8 |
  | book.spread_bps() | OrderBook | 盘口价差 (bps) | §8 |
  | book.depth_entropy(n) | OrderBook | 深度 Shannon 熵 | §8 |
  | update.old_amount / new_amount | BookUpdate | L2 增量变化 | §8 |
  | ... | ... | ... | ... |
- 完整 API 定义见研究员使用手册 §7 (AggTrans) 和 §8 (OrderBook)

## §2 共用结构建议（可选）
- 跨因子共享的计算逻辑描述
- 建议的共用数据结构接口
- 具体实现由独立 code agent 负责，需独立审阅验证

## §3 因子定义（核心）
### 分组 X：{主题}
#### {fa_name}
- **物理含义**：1-2句
- **微观机制来源**：crypto_ob_research/{N} 的哪个发现
- **触发事件**：EVENT_TYPE + side + guard（精确）
- **输入变量**：字段引用表
- **计算公式**：数学公式（精确，无自然语言替代）
- **参数**：
  | 参数名 | 值 | 单位 | bar 数换算 | 选取理由 |
- **状态管理**：state 变量，初始值，bar-reset
- **输出范围**：[min, max] + 边界行为（除零->?，样本不足->?）
- **边界条件**：首bar/低活跃期处理
- **类型标记**：A/B/AB/R + IC 摘要（IC 针对 mid-to-mid label，issue #119 之后口径）
- **已知限制**：流动性条件、时段效应、与 baseline 冗余度

## §4 采样口径与框架要求
- AmountBar 采样：动态阈值（daily_thres_28800, ~28800 bar/天）
- Agent 生命周期：OnAggTrans() 增量计算 -> OnBarClose() 输出
- Chunk 模式：Agent 状态（EMA/rolling）跨日延续，不在 OnDayStart 重置
- OB 依赖声明：RequiresOrderBook() / RequiresBookUpdates() 返回值
- OB 降级策略：L2 不可用时的输出（NaN / 默认值）
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
- 因子分类表：
  | 因子组 | 数据依赖 | 触发回调 | RequiresOrderBook | RequiresBookUpdates |
  |--------|---------|---------|-------------------|---------------------|
  | 纯 trade | AggTrans | OnAggTrans + OnBarClose | false | false |
  | OB 快照 | AggTrans + OrderBook | OnAggTrans/OnBarClose + ctx.GetBook() | true | false |
  | L2 事件 | AggTrans + BookUpdate | OnBookUpdate + OnBarClose | true | true |
- Zebra Agent 实现要点：
  - OnAggTrans 增量维护 trade 状态，OnBarClose 输出 + reset bar 状态
  - OB 因子在 OnBarClose 中 `if (ctx.HasBook()) { ... }` 包裹
  - EMA / rolling 状态在 chunk 模式下跨日延续，不在 OnDayStart 重置
  - OB 原语调用直接使用内置方法（如 `book.depth_imbalance_levels(20)`），不需自行遍历 levels
- 关键引用：研究员使用手册 §7 (AggTrans)、§8 (OrderBook API)
```

---

## 3. 独立 Codex Reviewer SubAgent

**编译完成后，启动独立 Codex Reviewer SubAgent（必须是独立 subagent，不是主进程自审）。**

Reviewer SubAgent 需要阅读：
1. 全部输入研究报告的 `factor_definition.md`（原始定义）
2. 生成的 `FA*_factor_list.md`（编译结果）
3. `FA*_warning_factors.md`（如存在）
4. `/home/cken/crypto_world/zebra/docs/研究员使用手册.md`（验证字段引用正确性）

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
- [ ] 参数是否精确到数值 + 单位 + bar 数？
- [ ] 边界条件（除零、首bar）是否每个都有明确返回值？
- [ ] **对照测试**：随机选 3 个因子，模拟"如果我是实现者，读完定义后是否有任何需要问的问题？"如果有 -> 不通过。

**D. 跨研究一致性：**
- [ ] 不同研究的因子之间是否有命名冲突？
- [ ] 不同研究使用的数据字段引用是否一致（同一字段是否用了不同的名字）？
- [ ] 共用结构建议是否正确反映了实际的共享关系？

**E. 数据引用合规性：**
- [ ] AggTrans 字段引用表中的每个字段是否在研究员使用手册 §7 中存在且描述一致？
- [ ] OrderBook 原语调用是否与研究员使用手册 §8 中的 API 签名一致（方法名、参数类型、返回值语义）？
- [ ] 使用 OB 的因子是否正确声明了 `RequiresOrderBook() = true`？
- [ ] 使用 OnBookUpdate 的因子是否正确声明了 `RequiresBookUpdates() = true`？
- [ ] OB 因子是否处理了 `ctx.HasBook() == false` 的降级情况（L2 数据不可用时输出 NaN 或默认值）？

**F. 警告因子审查（当 warning_factors.md 存在时）：**
- [ ] 每个 warning 因子的七要素定义本身是否完整可实现？（不看流程合规，只看定义质量）
- [ ] warning 报告中的"对工程实现的影响"判断是否准确？
- [ ] 是否有 warning 因子的定义质量差到不应收录的程度（如七要素缺 3 个以上、IC 来自未修复的 bug 数据）？如果有 -> 建议从 factor_list 移除

### 审阅流程

```
1. Reviewer SubAgent 产出审阅意见（通过 / 有条件通过 / 不通过 + 具体问题列表）
2. 如果不通过 -> 主进程修正 factor_list
3. Reviewer SubAgent 二次确认
4. 通过后 -> factor_list.md 定稿
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
- [ ] {具体修复建议}
```

### 警告类别定义

| 类别 | 含义 | 典型场景 |
|------|------|---------|
| `PHASE_GATE` | 研究的某个 Phase gate 未通过或未触发 | Phase 1 不合规（Reviewer 轮数不足）、Phase 终审未执行 |
| `DATA_INTEGRITY` | 研究报告中存在已知数据错误 | report 含被 REJECT 证伪的 IC 数字、report 与 log 不同步 |
| `DEFINITION_MISMATCH` | factor_definition.md 与实际验证代码/参数存在不一致 | 定义写 hl=50 但验证用 hl=30、timing filter 代码与定义不匹配 |
| `REVIEW_PENDING` | Phase 终审或 Reviewer 存在 pending/缺失 | Reviewer 未返回、Phase 3/4 终审 pending |

---

## 4. 交付物

| 文件 | 路径 | 说明 |
|------|------|------|
| factor_list | `factor_agent_docs/FA{N}_factor_list.md` | 标准化因子定义文档（含所有有定义的因子） |
| review | `factor_agent_docs/FA{N}_review.md` | 审阅意见 |
| warning_factors | `factor_agent_docs/FA{N}_warning_factors.md` | 警告因子报告（仅当存在 warning session 时生成） |

---

## 5. Changes after issue #119 (2026-04-19)

- **七要素模板"预测口径"语义**：`ret_lag0_nextH` 列名保留，但底层 label basis 已切换为 mid-to-mid（`basic_table.mid`）。compile 时在 §0 概述处明确标注"Label basis = mid-to-mid"，防止下游读者误解为 close-to-close。
- **因子 IC 摘要口径**：§3 各因子的"类型标记 + IC 摘要"指 mid-based label 下的 IC；如源研究报告含历史 close-based IC，compile 时应注明对应数据取自切换前还是切换后。
- **Reviewer 审阅维度**：独立 Codex Reviewer SubAgent 在"口径一致性检查"中应确认 IC 数值与所声明的 label basis（mid-to-mid）匹配。
