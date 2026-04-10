---
name: crypto-deep-factor-research
description: "从种子想法出发，使用 crypto-research MCP 对加密货币逐笔成交和 L2 订单簿数据进行深度微观结构研究，发现统计规律，设计 AmountBar 级因子。适用于：用户给出因子研究方向（一句话想法、idea 文档中的条目、或需要把某个微观结构直觉系统化研究），需要完成深度 Trade/OB 观察、统计验证、因子设计和主口径验证的完整研究流程。覆盖 Phase 0-4（研究阶段），不含 C++ 工程实现。"
---

# Crypto 深度因子研究流程（Skill Orchestrator）

> **本 Skill 是长流程研究任务的调度器。** 使用 `crypto-research` MCP 工具对加密货币微观结构进行探索式研究，产出 Zebra AmountBar 框架下可实现的因子。

> ## ⛔ 最高优先级规则（不可违反，context 压缩后仍必须遵守）
>
> 1. **不得在 Phase 之间或 Phase 内部暂停询问用户是否继续。** 用户启动本 Skill 即授权 Phase 0->4 全程自主执行。"需要继续吗？"、"这是计算密集型工作，是否进行？"之类的确认提问是绝对禁止的。唯一需要用户介入的情况是无法自行解决的技术阻塞（权限不足、数据缺失、工具故障）。
> 2. **`research_report.md` 必须在每个 Phase 结束时与 `research_log.md` 同步。** Phase 边界的 Logger 必须同步完成，确认 report 已更新后再触发 Reviewer 和 Compliance Monitor。
> 3. **每个 Phase 结束时 `quality_review.md` 必须存在且包含该 Phase 的审查结果。** Compliance Monitor 在每个 Phase 边界产出的合规报告必须追加到 `quality_review.md`。
> 4. **本 Skill 只能启动一项全新的研究。** 无论检索到多少相似/相关历史研究，都只允许把它们当作参考资料阅读；禁止进入并修改已有 `crypto_ob_research/*` 工作目录，禁止在已有 `research_report.md`、`research_log.md`、`quality_review.md`、`factor_definition.md` 上续写。
> 5. **如果当前平台要求用户显式授权子 Agent，则必须在研究开始前获得该授权。** 未获授权前，不得用主进程自审替代 Reviewer、Compliance Monitor、Logger 或 Phase 1 的独立饱和审查。推荐授权语句：`本次明确授权你使用子 Agent / 多 Agent / 并行 Agent 完成 Reviewer、Compliance Monitor、Logger 与 Phase 1 独立饱和审查，无需再次询问。`

## 0. 启动前强制步骤

### 0.0 确认 crypto-research 工具链可用

优先使用 `crypto-research` MCP 工具完成交互式调查。

- 首先确认当前环境可访问 `crypto-research` 工具。
- 参考配置位于：
  - `/home/cken/crypto_world/.mcp.json`
  - `/home/cken/crypto_world/crypto_mcp/.mcp.json`
- 如果当前平台无法访问 `crypto-research`，不得伪装成已完成交互式 MCP 调查；应明确报告阻塞并要求用户先启用工具链。

### 0.1 读取工具文档

**必须先完整阅读以下文档，不得凭记忆执行：**

```
/home/cken/crypto_world/crypto_mcp/README.md
```

阅读后在 `research_log.md` 中确认已通读并记录关键要点。

### 0.2 读取已知陷阱

Crypto 研究暂无像 HFT 那样固定的附录 B，但如果以下文件存在，必须先阅读：

```
/home/cken/crypto_world/crypto_ob_research/friction_knowledge_base.md
```

该文件用于沉淀历史研究中反复出现的问题，例如 AmountBar 边界处理、Binance 时间戳精度、L2 增量快照重建、批量预计算性能瓶颈、因子定义与 Zebra 实现口径不一致等。

### 0.3 了解数据资产

确认以下数据可用性与覆盖范围：

| 数据 | 路径 | 覆盖范围 |
|------|------|----------|
| 逐笔成交 (trades) | `/data/db/crypto/futures/binance_histroy/raw/trades/{SYM}/` | 7 币种，2019~2026.03 |
| L2 订单簿 (Tardis) | `/data/db/crypto/futures/tardis/binance-futures/incremental_book_L2/{SYM}/` | 7 币种，2025-07-01 ~ 2026-02-10 (225 天) |
| AmountBar 阈值 | `/data/db/crypto/futures/world/bod_data/daily_thres_28800/{SYM}/` | 7 币种，2020~2026.01 |

**支持的币种**：`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`, `DOGEUSDT`, `ADAUSDT`

### 0.3b 了解 Zebra 因子框架

阅读 Zebra Agent 开发文档：

```
/home/cken/crypto_world/zebra/docs/研究员使用手册.md
```

重点理解：

- `AggTrans`: 1ms 同方向聚合成交，是因子计算的核心输入
- `AmountBar`: 按累积成交额切分的 bar，默认动态阈值约 28800 bar/天
- `OnAggTrans()`: 增量更新状态
- `OnBarClose()`: 输出当前状态到 parquet

### 0.4 检查已有因子避免重复研究

**在 Phase 0 确定研究方向后执行，不需要在启动时全量扫读。**

启动一个 **SubAgent** 完成以下检索，主进程等待其返回摘要后继续：

**SubAgent 任务**

1. 在 Zebra 因子池中搜索与本次研究方向相关的已有因子：
   - `/home/cken/crypto_world/zebra_pool/f001/agents/base30_agent.h`
   - `/home/cken/crypto_world/zebra_pool/f002/agents/f002_agent.h`
   - `/home/cken/crypto_world/zebra_pool/README.md`
2. 如果发现表达式相近的因子，在历史研究目录中找到对应研究报告：
   - `/home/cken/crypto_world/crypto_ob_research/`
3. 返回：
   - 相关因子列表（名称 + 表达式摘要）
   - 对应历史研究路径
   - 核心结论摘要

**主进程**

- 根据 SubAgent 摘要，如有高度相关历史研究，可选择性阅读其 `research_report.md`
- 在 `research_log.md` 中记录与已有因子的关系，明确本次研究的增量方向
- 不要重复提交表达式基本一样的因子
- 历史研究只读不续做；即使发现高度相关、甚至存在 `[INTERRUPTED]` 标记，也必须新建编号目录重新开始

### 0.5 初始化工作目录

**路径规范（强制）**

- 工作路径：`/home/cken/crypto_world/crypto_ob_research/{N}-{topic}/`
- 代码：`{工作路径}/code/`
- 报告：`research_report.md`, `research_log.md`, `quality_review.md`, `factor_definition.md`
- 临时数据：`/data/db/crypto/ob_research/{N}-{topic}/`（自行创建，禁止写 `/tmp` 或 `/home`）

**编号规则**：查找 `crypto_ob_research/` 下已有目录最大编号，加 1。

**新开研究强制规则**

- 只能创建新的 `{N}-{topic}` 目录并在其中工作
- 禁止复用、进入后续写、或修改任何已有 `crypto_ob_research/*` 目录
- 即使历史目录主题相同或存在未完成研究，也必须以新的编号重新开始

```bash
OB_ROOT="/home/cken/crypto_world/crypto_ob_research"
mkdir -p "$OB_ROOT"
LAST_N=$(ls -d "$OB_ROOT"/[0-9]*-* 2>/dev/null | sed 's|.*/\([0-9]*\)-.*|\1|' | sort -n | tail -1)
N=$(( ${LAST_N:-0} + 1 ))

TOPIC="<topic_name>"

WORK_DIR="$OB_ROOT/${N}-${TOPIC}"
if ls -d "$OB_ROOT"/${N}-* 2>/dev/null | grep -q .; then
    echo "WARNING: 编号 $N 已被占用，递增至 $((N+1))"
    N=$((N+1))
    WORK_DIR="$OB_ROOT/${N}-${TOPIC}"
fi

mkdir -p "$WORK_DIR"/code
touch "$WORK_DIR/research_log.md"
touch "$WORK_DIR/research_report.md"

DATA_DIR="/data/db/crypto/ob_research/${N}-${TOPIC}"
mkdir -p "$DATA_DIR"

echo "Work dir: $WORK_DIR"
echo "Data dir: $DATA_DIR"
```

写入 `[START]` 条目（UTC+8），记录种子想法来源、工作路径、数据路径。

## 1. 角色管理

本 Skill 管理 4 个角色：

### 主进程（Researcher）

推进研究流程、执行调查、设计因子、做分析决策。主进程负责最终判断，不把决策权外包给 Reviewer 或 Compliance。

### Reviewer SubAgent

**独立审计员。** 审查研究质量：挑战假设、检查方法论、提出替代解释。

- 触发节点：每轮调查结束后、每个 Phase 结束后、最终交付前
- 不通过处理：主进程必须改变思路或方法重新研究，不得忽略直接进入下一步
- Prompt 模板见 `references/reviewer_prompt.md`

### Compliance Monitor SubAgent

**流程合规检查员。** 对照本 Skill 检查主进程是否严格遵循流程。

- 触发节点：
  - Phase 1 中，每完成 3 轮调查后执行轻量合规检查
  - 任何一轮 Reviewer 不通过时，立即触发轻量合规检查
  - 每个 Phase 结束时，执行完整合规检查
- 检查项见 `references/compliance_checklist.md`
- 如发现违规，主进程必须立即纠正后才能继续

### Logger SubAgent

**后台记录员。** 将研究进展、Reviewer 意见、决策理由写入 `research_report.md`。

- 运行方式：后台并行，不阻碍主进程
- 强制触发节点：
  - 每轮调查结束后，追加完整记录
  - 每次 Reviewer 返回后，追加 Reviewer 意见和主进程回应
  - 每次统计分析完成后，追加分析结果和解读
- 主进程每 2 轮调查后核对一次 `research_report.md` 完整性
- Phase 1 第 5 轮完成后，Logger 必须生成中间总结

## 2. Phase 执行流程

### Phase 0: Seed Idea

> **⛔ 自动继续：** 完成 Phase 0 后，直接进入 Phase 1，不得暂停。

1. 接收用户输入的一句话种子想法，或来自 idea 文档的具体条目
2. 产出 `research_report.md` 的 §0 部分：核心假设、直觉来源、微观行为猜测、与已有因子关系
3. 不需要预定义因子列表

### Phase 1: 深度微观结构调查

**这是整个研究的重心。执行前重新阅读 `crypto_mcp/README.md` 的工具列表。**

#### 工具使用指南

研究时应充分利用 `crypto-research` MCP 的多层工具：

| 工具 | 典型用途 |
|------|----------|
| `open_session` + `navigate` | 打开数据、定位到感兴趣时刻 |
| `get_status` | 快速查看当前位置全面状态 |
| `get_events(level="agg_trans")` | 查看 AggTrans 扫单事件流 |
| `get_events(level="trades")` | 细看原始逐笔成交 |
| `get_book` | 查看 L2 盘口深度快照 |
| `analyze_sweep` | 分析大额扫单冲击与恢复 |
| `flow_analysis` | 分析 order flow 特征 |
| `liquidity_profile` | 分析盘口流动性动态 |
| `inspect_bar` | 分析 AmountBar 内部构成 |
| `explain_move` | 分析价格变动成因 |
| `forward_returns` | 验证某模式后的前瞻收益 |
| `search_events` | 搜索全天符合条件的事件 |
| `gen_heatmap` / `gen_depth_chart` / `gen_ob_panorama` | 可视化 |

**每轮调查应至少使用 3-4 种不同工具。**

#### 执行循环

> **⚠️ 每轮调查应是一次真正的探索，不是任务清单上的打勾。** 好的调查会让你感到惊讶、产生新疑问、推翻旧假设。如果连续 2-3 轮都"符合预期"且没有新发现，这不是好事——说明你的调查设计太保守，没有在探索边界。此时应主动调整方向，去看你"不确定会发现什么"的场景。
>
> **⚠️ 假设修正是研究质量的标志，不是失败。** 最好的研究会在 Phase 1 结束时对现象的理解与 Phase 0 种子假设显著不同。典型的高质量研究路径包括：原始假设被证据推翻 → 从反例中发现更精确的机制 → 基于修正后的机制设计出更好的因子。如果你的核心假设从 Phase 0 到 Phase 1 结束始终未被挑战或修正，这可能说明探索不够深入。

```text
for round in 1..N:
    1. 设计本轮调查（目的、币种、时段、工具组合）
       - 前 5 轮：结构化对比维度（不同币种、不同时段、不同波动环境）
       - 第 6 轮起：自主设计（从前序发现中衍生，不受预设列表约束）
       - 设计前先问自己：这轮期望看到什么？如果看到相反结果意味着什么？
    2. 执行调查（使用 crypto-research MCP 工具，每轮 >= 3-4 种工具）
    3. 按格式完整记录（详细描述现象 + 假设对比分析 + 因子启示 + 新问题）
    4. 触发 Logger SubAgent，记录到 research_report.md
    5. 触发 Reviewer SubAgent，审查本轮质量
    6. 将 Reviewer 结论写入 research_log.md：
       [REVIEWER R{N}] {PASS|FAIL|CONDITIONAL} — {一句话关键意见}
    7. 如果 Reviewer 不通过：
       - 该轮不计入有效轮数
       - 改变思路或方法，重新执行
    8. 如果 Reviewer 通过：
       - 计入有效轮数
       - 检查结束条件
    9. 每 3 轮通过后：
       - 触发 Compliance Monitor 轻量合规检查

配合执行：
    - forward_returns 统计验证
    - flow_analysis 跨币种对比
    - 数据范围: 研究集 A（2025-07-01 ~ 2025-09-30）+ 研究集 B（2026-01-10 ~ 2026-01-20），
      两个集均可自由使用，均有 trades + L2
```

**每轮记录必须包含**

- 观察到的具体现象（带数据）
- 与预期的对比分析
- 至少 1 个新问题或新假设（驱动下一轮调查的具体方向）
- 因子启示；除了直接编码方式，也要思考该现象在时序维度上的可能性（如信号随 bar 数的演化模式、不同时间尺度上的表现差异、跨币种传导的时滞），为 Phase 2 的因子设计积累素材

**主进程每 2 轮调查后应核对 `research_report.md`**，确保上一轮的记录包含五要素：目的、现象、假设对比、因子启示、新问题。

**Phase 1 第 5 轮完成后，Logger 必须生成中间总结**，列出已发现机制、候选因子草案、待探索方向。

**结束条件（必须同时满足）**

- >= 10 轮 **Reviewer 通过的** 调查，其中 >= 5 轮自主设计
- >= 3 个独立微观机制发现，每个有 >= 2 场景交叉验证
- 明确的饱和论证：最近观察开始重复，不再有意料之外的新发现
- 达到下限后不代表可以立即停止；如果仍有新发现在涌现，必须继续
- 完成独立饱和审查
- Phase 1 终审 Reviewer 与 Compliance Monitor 均通过

产出：微观机制理解、候选因子草案、已排除方向、信心判断。

#### Phase 1 Exit Protocol: 独立饱和审查

在主进程认为 Phase 1 可以结束时，必须执行以下流程：

1. 准备结构化审查 brief：
   - 种子想法和核心假设
   - 所有调查发现的摘要
   - 已设计的候选因子草案
   - 已排除的研究方向及原因
   - 饱和论证
2. 启动一个独立审查子 Agent：
   - 请其独立评估：
     - 是否仍有未被探索的重要方向
     - 现有机制理解是否存在逻辑漏洞
     - 因子设计空间是否已充分探索
   - 如果认为值得追加探索，必须给出具体、可执行建议（币种、时段、观察重点）
3. 等待审查返回后决定：
   - 认为饱和：进入 Phase 1 终审
   - 给出具体可执行建议：追加调查后重新提交审查
   - 建议模糊不可执行：记录到 `research_log.md` 后继续

### Phase 2: Factor Design & Screening

> **⛔ 自动继续：** 完成 Phase 1 终审后，直接进入 Phase 2，不得暂停。

**Phase 转换检查**：确认 Phase 1 终审 Reviewer 和 Compliance Monitor 状态已在 `quality_review.md` 与 `research_log.md` 中更新为最终结果，不得遗留 `pending`。

**执行前重新阅读 `crypto_mcp/README.md`，特别是工具列表和数据格式说明。**

1. **因子设计深度思考（创造性环节，不可跳过）**
   - 对每个 Phase 1 微观发现，先思考现象本质和最佳数学编码方式，再定义因子
   - **一个微观发现通常可以衍生多个因子**（不同编码方式、不同条件化维度、不同时间尺度）——不要一个发现只产出一个"最显然"的因子就停下
   - **时序探索（重要的因子衍生维度）**：
     微观信号的原始形态往往不是最优的因子编码。对每个发现都值得思考：通过时序变换能否产出更好的、或额外的因子？时序操作的空间非常广阔，鼓励创造性探索。特别是当一个信号在短 horizon 有预测性时，不要轻易放弃——时序变换可以将 AggTrans 级信号桥接到 AmountBar 级。即使信号已经在主 horizon 上有效，时序变换也常常能衍生出捕捉不同信息维度的新因子。
   - **思考 Zebra Agent 实现**：因子最终在 `OnAggTrans()` 中增量计算，`OnBarClose()` 输出。设计时考虑这个约束
   - 在 `research_log.md` 中记录设计决策：为什么选择这种编码？考虑过但放弃了什么？
   - **⚠️ 产出数量软目标**：一次研究建议产出 **≥10 个达到提交标准的因子**。如果经过充分探索（含独立饱和审查确认本方向已无更多可挖掘空间）仍不足 10 个，最低不应少于 **5 个**。如果连 5 个都达不到，需要在 `research_log.md` 中详细论证为什么本研究方向的因子空间确实有限，并由 Reviewer 确认
2. 因子精确定义（每个附微观机制 rationale）
3. **所有候选因子全部进入小样本初筛**
   - 不允许第一个通过就跳过其余候选
   - 若某些候选因子需要额外代码，启动 SubAgent 并行编写
   - 先做 1 code x 1 date dry-run，检查性能
   - 样本：**5 coins x 10 天**（从研究集 A 2025-07-01 ~ 2025-09-30 随机抽样非连续日期）
   - 通道 A：线性 IC（主看 `ret_lag0_next100`, `ret_lag0_next200`）
   - 通道 B：非线性预测力（quintile 形状、conditional IC）
   - 拓展观察：`next400`, `next800`
4. **大样本泛化**：7 coins × 全部研究集（集 A 92 天 + 集 B 11 天 = 103 天）
   - 只有通过小样本筛选的因子才进入大样本验证
   - 集 A 和集 B 分别报告 IC，检验跨时段一致性
5. 保留规则：A 类 / B 类 / AB 类 / R 类，不能把 IC 当唯一 gate
6. 失败因子详细记录：定义、指标、失败原因
7. Phase 2 终审 Reviewer + Compliance Monitor
8. **因子数量检查**
   - >= 10 个：正常进入 Phase 3
   - 5-9 个：在 `research_log.md` 中记录不足原因，回退到 Phase 1 补充调查，寻找新的微观机制或从已有发现中衍生更多因子编码方式，然后重新执行 Phase 2 的增量部分（仅处理新增因子）
   - < 5 个：必须回退到 Phase 1；若回退后仍不足 5 个，需再次独立饱和审查确认本方向确实已无更多可挖掘空间，并由 Reviewer 确认后方可继续

### Phase 3: Main Caliber Validation

> **⛔ 自动继续：** 完成 Phase 2 因子数量检查后（达标或经审查确认），直接进入 Phase 3，不得暂停。

**Phase 转换检查**：确认 Phase 2 终审 Reviewer 和 Compliance Monitor 状态已更新为最终结果，不得遗留 `pending`。

**执行前重新阅读 `crypto_mcp/README.md`。**

**⚠️ Phase 3 是强制步骤，不可跳过或与其他 Phase 合并。** 如遇数据量过大等技术困难，必须找替代方案（如降采样、分批处理、预计算），而不是跳过。跳过 Phase 3 = Compliance Monitor 判定不合规。

数据范围：研究集 A（2025-07-01 ~ 2025-09-30）+ 研究集 B（2026-01-10 ~ 2026-01-20），共 103 天。

> **⚠️ Phase 3 的核心心态是"试图打破你的因子"，而不是"确认它有效"。** 你在 Phase 1/2 已经建立了对因子的信心。Phase 3 的目标是主动寻找它可能失败的条件——如果找不到，信心更强；如果找到了，这是宝贵的知识。

1. 多 Horizon x 多 Window IC 矩阵（`next100/200/400/800 x >= 3 档 window`）
2. 自主设计稳健性验证
   - 先回答：这个因子最可能在哪些条件下失败
   - 再针对这些失败模式设计实验
   - 典型维度：跨币种一致性、24h 时段效应、波动率分层、funding rate 周期、跨交易所行为差异；根据因子特性选择最相关的，而非机械执行全部
   - 在 `research_log.md` 中记录失败假设与验证结果
3. 参数定稿（`halflife/window/fast-slow` 等）
4. 完成最终 `factor_definition.md`
5. Phase 3 终审 Reviewer + Compliance Monitor

### Phase 4: Final Review & Report

> **⛔ 自动继续：** 完成 Phase 3 终审后，直接进入 Phase 4，不得暂停。

**Phase 转换检查**：确认 Phase 3 终审 Reviewer 和 Compliance Monitor 状态已更新为最终结果，不得遗留 `pending`。

**执行前重新阅读 `crypto_mcp/README.md`。**

1. 触发最终 Reviewer 全面审查（数据纪律 + 方法论 + 因子质量 + 结论可靠性）
2. 触发最终 Compliance Monitor 全面检查
3. 完成 `research_report.md`（完整结构）
4. 产出最终交付物清单

## 3. 数据纪律红线（贯穿全流程）

研究阶段仅允许使用以下两个数据窗口，禁止接触窗口外的任何数据：

| 用途 | 数据范围 | 数据类型 | 说明 |
|------|---------|---------|------|
| **研究集 A（主）** | **2025-07-01 ~ 2025-09-30** | trades + L2 | 92 天，7 币种。Phase 1 观察 + 统计探索 + 因子设计 + 小样本筛选 |
| **研究集 B（辅）** | **2026-01-10 ~ 2026-01-20** | trades + L2 | 11 天，7 币种。跨时段风格验证 + 大样本泛化 |
| **禁区** | **上述两集之外的所有日期** | — | **研究阶段绝对禁止触碰**，包括 2025-10~12、2026-01-01~01-09、2026-01-21~02-10 |

**设计意图**：
- 研究集 A（2025 Q3）和 B（2026 Q1）在时间上分离 3+ 个月，避免因子过拟合于某一市场风格
- 禁区包含最终 realize 阶段的训练集（2025-10 ~ 2025-12）和验证集（2026-01-21 ~ 2026-02-09），防止研究阶段信息泄漏

**主预测口径**：`ret_lag0_next100` ~ `ret_lag0_next200`（AmountBar 时间轴）。拓展观察到 `ret_lag0_next800`。因子设计应匹配此 horizon，但研究阶段要理解市场本质，不要过度拟合。

**AmountBar 参数**：动态阈值（`daily_thres_28800`），每天约 28800 根 bar。使用 `compute_bars()` 工具时不指定 `threshold` 即采用默认动态阈值。

## 4. Phase 边界检查协议

每个 Phase 结束时执行以下协议：

```text
1. 重新阅读本 Skill 对应 Phase 的结束条件和产出要求
2. 先同步触发 Logger，等待其完成 research_report.md 更新
3. 检查 research_report.md 本 Phase 章节是否完整
4. 并行启动：
   a. Reviewer SubAgent
   b. Compliance Monitor SubAgent
5. 等待两者返回
6. 将 Compliance 报告追加到 quality_review.md
7. 若任一不通过，纠正后重新检查
8. 全部通过后，在 research_log.md 记录 Phase 完成并进入下一 Phase
```

### 4.1 Phase 1 轻量合规检查

为防止踩线停止和逐轮 Reviewer 跳过，在 Phase 1 中周期性执行轻量合规检查。

**触发时机**

- 第 3、6、9 轮 Reviewer 通过后
- 任意一轮 Reviewer 不通过时

**轻量检查内容**

1. Reviewer 执行验证
   - `[REVIEWER R{N}]` 标记数量是否与调查轮数一致
   - 是否有实质审查意见
   - 抽读 1-2 轮完整 Reviewer 意见和主进程回应
2. Report 同步审计
   - `research_report.md` 中的调查轮次数是否与 `research_log.md` 一致
   - 最近 2 轮是否包含完整五要素
   - 如发现 report 滞后，必须先补写
3. 研究动态趋势
   - 最近 2-3 轮是否仍有意料之外的新发现
   - 是否有 Reviewer 提出的遗留问题未被回答
4. 踩线趋势预警
   - 如果已完成 >= 8 轮且主进程有准备收尾倾向，但仍有未回答问题或新发现，发出警告

输出追加到 `research_log.md` 与 `quality_review.md`。

## 5. Context 保鲜协议

为防止长对话中流程要求被遗忘：

1. 每个 Phase 开始时，重新阅读本 Skill 对应章节
2. 每 3 轮调查后，重新阅读 Phase 1 核心要求
3. 做重大决策前，重新阅读相关章节确认合规
4. Compliance Monitor 每次检查时，独立重新阅读完整 Skill

## 6. 交付物清单

| 文件 | 内容 |
|------|------|
| `research_report.md` | 完整研究报告（§0-§7） |
| `research_log.md` | 带时间戳的完整日志 |
| `factor_definition.md` | 因子精确定义（Zebra Agent 可实现级别） |
| `quality_review.md` | Reviewer + Compliance 审查记录 |
| `code/` | 分析脚本和统计验证代码 |

**交付目录**：`/home/cken/crypto_world/crypto_ob_research/{N}-{topic}/`

## 7. 异常终止协议

如果因 context 限制、工具故障、或超时导致流程无法继续完成：

1. 立即在 `research_log.md` 写入 `[INTERRUPTED]`，记录：
   - 当前 Phase 和步骤
   - 已完成的工作清单
   - 未完成的工作清单
   - 下次重做时的建议起点
2. 保存当前已有的 `factor_definition.md` 和 `research_report.md`
3. 写一份简要的 `quality_review.md`，标注 `INCOMPLETE — Phase {N} 中断`
4. 确保所有已执行轮次都有 `[REVIEWER R{N}]` 标记

这样后续可以把该目录作为历史参考资料检索，但**不得**在原目录上恢复、续写或继续执行；若未来再次研究同一主题，也必须新建编号目录重新开始。
