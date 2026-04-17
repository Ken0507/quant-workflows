---
name: crypto-deep-factor-research
description: "从种子想法出发，使用 crypto-research MCP 对加密货币逐笔成交 + L2 订单簿数据进行深度微观结构研究，发现统计规律，设计 AmountBar 级因子。适用于：用户给出因子研究方向（一句话想法），需要通过深度 Trade/OB 观察 -> 统计验证 -> 因子设计 -> 主口径验证的完整研究流程。覆盖 Phase 0-4（研究阶段），不含 C++ 工程实现。"
metadata:
  short-description: "Crypto 深度因子研究：Trade/OB 观察 -> AmountBar 因子设计 -> 主口径验证"
  argument-hint: "[种子想法]"
---

# Crypto 深度因子研究流程（Skill Orchestrator）

> **本 Skill 是长流程研究任务的调度器。** 使用 crypto-research MCP 工具对加密货币微观结构进行探索式研究，产出 Zebra AmountBar 框架下可实现的因子。

> ## ⛔ 最高优先级规则（不可违反，context 压缩后仍必须遵守）
>
> 1. **不得在 Phase 之间或 Phase 内部暂停询问用户是否继续。** 用户启动本 Skill 即授权 Phase 0→4 全程自主执行。"需要继续吗？"、"这是计算密集型工作，是否进行？"之类的确认提问是**绝对禁止的**。唯一需要用户介入的情况是无法自行解决的技术阻塞（权限不足、数据缺失、工具故障）。
> 2. **research_report.md 必须在每个 Phase 结束时与 research_log.md 同步。** Phase 边界的 Logger 必须同步完成（非后台），确认 report 已更新后再触发 Reviewer 和 Compliance Monitor。
> 3. **每个 Phase 结束时 quality_review.md 必须存在且包含该 Phase 的审查结果。** Compliance Monitor 在每个 Phase 边界产出的合规报告必须追加到 quality_review.md。

## 0. 启动前强制步骤

### 0.1 读取工具文档

**必须先完整阅读以下文档，不得凭记忆执行：**

```
/home/cken/crypto_world/crypto_mcp/README.md
```

确认了解 crypto-research MCP 全部工具的用途和参数。在 research_log.md 中确认已通读并记录关键要点。

### 0.2 读取已知陷阱

目前 crypto 研究尚无独立的已知陷阱参考文档（相当于 HFT 的附录 B）。随着研究推进，应在 `/home/cken/crypto_world/crypto_ob_research/friction_knowledge_base.md` 中积累常见陷阱（如 AmountBar 边界处理、Binance 数据时间戳精度、L2 增量快照重建等）。如果该文件已存在，必须在此步阅读。

### 0.3 了解数据资产

阅读后确认以下数据的可用性：

| 数据 | 路径 | 覆盖范围 |
|------|------|----------|
| 逐笔成交 (trades) | `/data/db/crypto/futures/binance_histroy/raw/trades/{SYM}/` | 7 币种, 2019~2026.03 |
| L2 订单簿 (Tardis) | `/data/db/crypto/futures/tardis/binance-futures/incremental_book_L2/{SYM}/` | 7 币种, 2025-07-01 ~ 2026-02-10 (225 天) |
| AmountBar 阈值 | `/data/db/crypto/futures/world/bod_data/daily_thres_28800/{SYM}/` | 7 币种, 2020~2026.01 |

**研究阶段仅允许使用**：
- 研究集 A：`2025-07-01 ~ 2025-09-30`（trades + L2，92 天）
- 研究集 B：`2026-01-10 ~ 2026-01-20`（trades + L2，11 天）
- 详见 §3 数据纪律红线

**支持的币种**：BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT

### 0.3b 了解 Zebra 因子框架

阅读 Zebra Agent 开发文档以了解因子最终如何实现：

```
/home/cken/crypto_world/zebra/docs/研究员使用手册.md
```

关键概念：
- **AggTrans**: 1ms 同方向聚合成交（sweep 事件），是因子计算的核心输入
- **AmountBar**: 按累积成交额切分的 bar（动态阈值 ~28800 bar/天）
- **Agent 生命周期**: OnAggTrans() 增量计算 -> OnBarClose() 输出
- 因子在 OnAggTrans 中增量维护状态，OnBarClose 时落盘

### 0.4 检查已有因子避免重复研究

**在 Phase 0 确定研究方向后执行（不需要在启动时全量扫读）。**

启动一个 **SubAgent** 完成以下检索，主进程等待其返回摘要后继续：

**SubAgent 任务**：
1. 在 Zebra 因子池中搜索与本次研究方向相关的已有因子（关键词搜索）：
   ```
   /home/cken/crypto_world/zebra_pool/f001/agents/base30_agent.h  — 30 个基础因子
   /home/cken/crypto_world/zebra_pool/f002/agents/f002_agent.h    — 39 个扩展因子
   /home/cken/crypto_world/zebra_pool/README.md                   — 因子列表概览
   ```
2. 如果发现表达式相近的因子，在历史研究目录中找到对应的研究报告：
   ```
   /home/cken/crypto_world/crypto_ob_research/
   ```
3. 返回：相关因子列表（名称+表达式摘要）、对应的历史研究报告路径及核心结论。

**主进程**：
- 根据 SubAgent 返回的摘要，如有高度相关的历史研究，选择性阅读其 research_report.md
- 在 research_log.md 中记录与已有因子的关系，明确本次研究的增量方向
- **不要重复提交表达式基本一样的因子**
- **⛔ 禁止修改或续写已有研究**：即使发现高度相关的历史研究，也必须在新的编号目录下开始全新研究。不得修改、追加、或以任何方式改动 `crypto_ob_research/` 下已有目录中的任何文件。已有研究仅作为参考阅读

### 0.5 初始化工作目录

**路径规范（强制）：**

- **工作路径**：`/home/cken/crypto_world/crypto_ob_research/{N}-{topic}/`
- **代码**：`{工作路径}/code/`
- **报告**：直接放在工作路径下（`research_report.md`, `research_log.md`, `quality_review.md`, `factor_definition.md`）
- **临时数据**：`/data/db/crypto/ob_research/{N}-{topic}/`（自行创建，禁止写 /tmp 或 /home）

**编号规则**：查找 `crypto_ob_research/` 下已有目录的最大编号，加 1。

```bash
# 1. 确定编号（带唯一性检查，防止并行启动时编号冲突）
OB_ROOT="/home/cken/crypto_world/crypto_ob_research"
mkdir -p "$OB_ROOT"
LAST_N=$(ls -d "$OB_ROOT"/[0-9]*-* 2>/dev/null | sed 's|.*/\([0-9]*\)-.*|\1|' | sort -n | tail -1)
N=$(( ${LAST_N:-0} + 1 ))

# 2. 研究主题名由用户提供或从种子想法派生（小写下划线格式）
TOPIC="<topic_name>"

# 3. 创建工作目录（含唯一性检查）
WORK_DIR="$OB_ROOT/${N}-${TOPIC}"
if ls -d "$OB_ROOT"/${N}-* 2>/dev/null | grep -q .; then
    echo "WARNING: 编号 $N 已被占用，递增至 $((N+1))"
    N=$((N+1))
    WORK_DIR="$OB_ROOT/${N}-${TOPIC}"
fi
mkdir -p "$WORK_DIR"/code
touch "$WORK_DIR/research_log.md"
touch "$WORK_DIR/research_report.md"

# 4. 创建临时数据目录
DATA_DIR="/data/db/crypto/ob_research/${N}-${TOPIC}"
mkdir -p "$DATA_DIR"

echo "Work dir: $WORK_DIR"
echo "Data dir: $DATA_DIR"
```

写入 `[START]` 条目（UTC+8），记录种子想法来源、工作路径、数据路径。

---

## 1. 角色管理

本 Skill 管理 4 个角色：

### 主进程（Researcher）
推进研究流程、执行调查、设计因子、做分析决策。使用 crypto-research MCP 工具。

### Reviewer SubAgent（持久化角色）
**独立审计员。** 审查研究质量：挑战假设、检查方法论、提出替代解释。

- **生命周期**：Phase 1 开始时 spawn 一次，指定 `name="reviewer"`。后续所有审查通过 `SendMessage(to: "reviewer")` 触发，**Reviewer 保留完整的历次审查记忆**。
- **持久化能力**：
  - 追踪历次提出的建议及回应状态（如"R3 提的 X 在 R7 仍未回应"）
  - 检测跨轮次趋势（如"连续 4 轮无新发现，建议转向"）
  - Phase 终审时基于全程 context 给出比无状态 SubAgent 更深入的判断
- **context 压缩应对**：如果研究超过 15 轮，在 SendMessage 中附带未回应建议清单，防止 Reviewer auto-compaction 丢失关键历史。
- **触发节点**：每轮调查结束后 + 每个 Phase 结束后 + 最终交付前
- **不通过处理**：主进程必须改变思路/方法重新研究，不得忽略直接进入下一步
- Reviewer 的 prompt 模板见本 Skill 的 `references/reviewer_prompt.md`

### Compliance Monitor SubAgent（持久化角色）
**流程合规检查员。** 对照本 Skill 的研究流程检查主进程是否严格遵循流程。

- **生命周期**：Phase 1 开始时 spawn 一次，指定 `name="compliance"`。后续所有检查通过 `SendMessage(to: "compliance")` 触发，**Compliance Monitor 保留历次检查记忆**。
- **持久化能力**：
  - 追踪合规轨迹变化（如"R3 report 滞后 1 轮 → R6 滞后 3 轮 → 恶化趋势"）
  - 记住已发现的问题，在后续检查中验证是否修复
  - 积累 Phase 1 效率数据，为效率预警提供连续判断基础
- **触发节点**：
  - **Phase 1 中：嵌入到 Reviewer 前置门控中自动触发**（见 §2 Phase 1 循环第 0 步），不再依赖主进程单独记忆。具体时机：第 4/7/10 轮开始前（即第 3/6/9 轮 Reviewer 通过后）
  - **任何一轮 Reviewer 不通过时**，立即触发轻量合规检查
  - **每个 Phase 结束时**（与 Reviewer 同时但独立运行）— 完整合规检查
- **检查项**：见本 Skill 的 `references/compliance_checklist.md`
- 如发现违规，主进程必须立即纠正后才能继续
- **全程旁观原则**：Compliance Monitor 不只是 Phase 边界的门卫，它在 Phase 1 中持续监控研究质量走势。如果检测到"低效轮次堆积"（多轮无新发现）或"踩线趋势"（接近下限时突然加速），必须提前干预

### Logger SubAgent
**后台记录员。** 将研究进展、Reviewer 意见、决策理由详细记录到 `research_report.md`。
- **运行方式**：后台运行（`run_in_background=true`），不阻碍主进程
- **强制触发节点**（每个都必须触发，不可跳过）：
  - 每轮调查结束后 → 按 `target_and_workflow.md` §1.7 模板追加完整的调查记录章节（六要素）
  - 每次 Reviewer 返回后 → 在对应章节追加 Reviewer 意见和主进程回应
  - 每次统计分析完成后 → 追加分析结果和解读
- **完整性检查**：主进程每 2 轮调查后应核对 research_report.md，确保上一轮的记录包含 §1.7 要求的六要素（目的/现象/假设对比/因子启示/效应时间特征/新问题）。如有缺失，立即要求 Logger 补充
- **中点快照**：Phase 1 第 5 轮完成后，Logger 必须生成一份中间总结，列出已发现的微观机制、候选因子草案、待探索方向

### Codex（结构化咨询伙伴）

通过 `mcp__codex__codex` 工具与 Codex 交流。

**固定咨询节点**（共 2 个）：
1. **Phase 1 Exit Protocol**：饱和审查的独立审查方之一。详见 §Phase 1 Exit Protocol。
2. **Phase 2 因子设计后**：候选因子列表完成后、小样本筛选前。详见 §Phase 2 第 1.5 步。

**主动咨询条件**（事件驱动，非固定节点）：
- Reviewer 连续 2 轮标记"探索深度不足"或"假设未演化" → 建议咨询 Codex 获取新视角
- Phase 2 因子数量不足且研究方向似已饱和 → 咨询 Codex 确认是否遗漏设计空间

**建议跟进纪律**：每次 Codex 返回建议后，主进程必须在 research_log 中写结构化处置表：

```markdown
### [CODEX-{节点}] Codex 建议处置

| # | Codex 建议 | 处置 | 理由 |
|---|-----------|------|------|
| 1 | ... | ✅ 采纳 → R{N} | ... |
| 2 | ... | ❌ 拒绝 | ... |
| 3 | ... | ⏳ 推迟到 Phase {N} | ... |
```

持久化 Reviewer 会在后续审查中检查：被采纳的建议是否已执行？执行结果如何？

**独立思考原则（核心）**：Codex 的建议是参考意见，不是指令。主进程必须独立评估每条建议的合理性，不盲目采纳。采纳或拒绝都需要基于自己的分析判断，并在 research_log 中记录理由。

---

## 2. Phase 执行流程

### Phase 0: Seed Idea

> **⛔ 自动继续：** 完成 Phase 0 后，直接进入 Phase 1，不得暂停。

1. 接收用户输入（一句话种子想法）
2. 产出 `research_report.md` 的 §0 部分：核心假设、直觉来源、微观行为猜测、与已有因子关系（执行 §0.4）
3. **不需要预定义因子列表**

### Phase 1: 深度微观结构调查（核心阶段）

**⚠️ 这是整个研究的重心。执行前重新阅读 `crypto_mcp/README.md` 工具列表。**

#### 工具使用指南

研究时应充分利用 crypto-research MCP 的多层工具：

| 工具 | 典型用途 |
|------|----------|
| `open_session` + `navigate` | 打开数据、定位到感兴趣的时刻 |
| `get_status` | 快速查看当前位置的全面状态 |
| `get_events(level="agg_trans")` | 查看周围的 AggTrans 扫单事件流 |
| `get_events(level="trades")` | 细看原始逐笔成交 |
| `get_book` | 查看 L2 订单簿深度快照 |
| `analyze_sweep` | 分析大额扫单的冲击和恢复 |
| `flow_analysis` | 分析 order flow 特征（VPIN、持续性、Kyle lambda） |
| `liquidity_profile` | 分析盘口流动性动态 |
| `inspect_bar` | 分析 AmountBar 内部构成 |
| `explain_move` | 分析一段价格变动的成因 |
| `forward_returns` | 验证假设：某模式后的前瞻收益 |
| `search_events` | 搜索全天符合条件的事件 |
| `gen_heatmap` / `gen_depth_chart` / `gen_ob_panorama` | 可视化 |

**每轮调查应至少使用 3-4 种不同工具。**

#### 执行循环

> **⚠️ 每轮调查应是一次真正的探索，不是任务清单上的打勾。** 好的调查会让你感到惊讶、产生新疑问、推翻旧假设。如果连续 2-3 轮都"符合预期"且没有新发现，这不是好事——说明你的调查设计太保守，没有在探索边界。此时应主动调整方向，去看你"不确定会发现什么"的场景。
>
> **⚠️ 假设修正是研究质量的标志，不是失败。** 最好的研究会在 Phase 1 结束时对现象的理解与 Phase 0 种子假设显著不同。典型的高质量研究路径包括：原始假设被证据推翻 → 从反例中发现更精确的机制 → 基于修正后的机制设计出更好的因子。如果你的核心假设从 Phase 0 到 Phase 1 结束始终未被挑战或修正，这可能说明探索不够深入。

```
for round in 1..N:
    0. 【前置门控 — 不可跳过】
       a. 如果 round > 1:
          - 读取 research_log.md，确认 [REVIEWER R{round-1}] 标记存在
            且包含实质性审查意见（非空/非 Pending）
          - 如果标记不存在 → 立即 SendMessage(to: "reviewer") 补执行
            上一轮审查，等待返回后才能继续
          - 如果上一轮为 FAIL → 按第 7 步规则重做上一轮（不可跳过进入新轮）
       b. 如果 round ∈ {4, 7, 10, 13, ...}（即每 3 轮 Reviewer 通过后）:
          - 【强制 Report 同步】触发 Logger（非后台，同步等待完成），
            确认 research_report.md 已覆盖到当前轮次
          - 如果 report 滞后 > 2 轮 → 阻塞，Logger 补齐后才能继续
          - SendMessage(to: "compliance") 执行轻量合规检查（见 §4.1）
          - 如有不合规项 → 必须纠正后继续
          - 【预测目标引导 — 引导性，非阻塞】SendMessage(to: "reviewer") 触发一次"预测目标连接"
            review（见 reviewer_prompt.md 模式 A 第 8 项）。Reviewer 会基于积累的发现，
            提出 1-2 个引导问题，主进程在下一轮调查的设计中考虑这些问题。
            ⚠️ 这不是 kill gate，不要求 agent 立即停止当前研究方向去回答这些问题。
            它的目的是在 agent 顺着自己的思路探索的同时，注入对预测目标的意识，
            自然地影响后续几轮的调查方向选择。如果 agent 暂时还没有清晰答案，没问题——
            把它当作启发，继续探索

    1. 设计本轮调查（目的、币种、时段、工具组合）
       - 前5轮: 结构化对比维度（不同币种、不同时段、不同波动环境）
       - 第6轮起: 自主设计（从前序发现中衍生，不受预设列表约束）
       - ⚠️ 设计调查前先问自己：这轮我期望看到什么？如果看到相反的结果意味着什么？
    2. 执行调查（使用 crypto-research MCP 工具，每轮 ≥3-4 种工具）
    3. 按 `target_and_workflow.md` §1.7 模板完整记录（六要素）：目的 / 现象（详细描述） / 假设对比 / 因子启示 / **效应时间特征** / 新问题
       - 每轮记录必须包含：观察到的具体现象（带数据）、与预期的对比分析、
         至少 1 个新问题或新假设（驱动下一轮调查的具体方向）
       - **效应时间特征（必填）**：本轮观察的现象在时间维度上是怎么展开的？
         是瞬时影响（一两个 bar 内结束）还是持续展开？forward return 在哪个 horizon 上最强 / 衰减最快？
         不同 horizon 上是否表现出不同方向？是否观察到 regime 依赖？
         这些观察不需要严格定量分析，但需要定性记录，作为 Phase 2 编码方式选择的依据
       - 记录因子启示时，除了直接编码方式，也思考该现象在时序维度上的可能性
         （如信号随 bar 数的演化模式、不同时间尺度上的表现差异、跨币种传导的时滞），
         为 Phase 2 的因子设计积累素材
    4. 触发 Logger SubAgent（后台记录到 research_report.md）
    5. SendMessage(to: "reviewer") 审查本轮质量 — 每轮必须触发，不可合并或跳过
    6. 将 Reviewer 结论写入 research_log.md，格式为：
       `[REVIEWER R{N}] {PASS|FAIL|CONDITIONAL} — {一句话关键意见}`
       例: `[REVIEWER R7] PASS — 跨币种对比充分，建议后续验证低流动性时段`
       此标记是 Compliance Monitor 验证逐轮 Reviewer 执行情况的依据。
    7. 如果 Reviewer 不通过 → 该轮不计入有效轮数，改变思路/方法重新执行
    8. 如果 Reviewer 通过 → 计入有效轮数，检查结束条件

    配合执行（穿插在调查之间）:
    - forward_returns 统计验证（验证发现的预测性）
    - flow_analysis 跨币种对比
    - 数据范围: 研究集 A（2025-07-01 ~ 2025-09-30）+ 研究集 B（2026-01-10 ~ 2026-01-20），
      两个集均可自由使用，均有 trades + L2
```

**主进程每 2 轮调查后应核对 research_report.md**，确保上一轮的记录包含 §1.7 的六要素（目的/现象/假设对比/因子启示/效应时间特征/新问题）。如有缺失，立即要求 Logger 补充。

**Phase 1 第 5 轮完成后，Logger 必须生成中间总结**，列出已发现的微观机制、候选因子草案、待探索方向。

**结束条件（必须同时满足）**：
- ≥10 轮 **Reviewer 通过的** 调查（其中 ≥5 轮自主设计）— 被拒绝的轮次不计入
- ≥3 个独立微观机制发现，每个有 ≥2 场景交叉验证
- **饱和条件（主要退出标准）**：观察开始重复，不再有意料之外的发现。必须在 research_log 中明确论证饱和原因。
- **⚠️ 达到下限后不代表可以停止。下限是地板不是天花板。如果仍有新发现在涌现，必须继续。Compliance Monitor 在第 9 轮后的轻量检查会特别关注"踩线停止"倾向。**
- **独立饱和审查（强制）**：详见 §Phase 1 Exit Protocol 节
- Phase 1 终审 Reviewer + Compliance Monitor 均通过

产出：微观机制理解、候选因子草案、已排除方向、信心判断。

#### Phase 1 Exit Protocol: 饱和审查循环

在主进程认为 Phase 1 可以结束时，进入以下**循环流程**（不是一次性门控）：

```
while True:
    1. 准备审查材料
    2. 并行启动 SubAgent + Codex 独立审查
    3. 处置审查建议
    4. 如有被采纳的建议 → 执行 → 独立思考 → 可能继续研究
    5. 再次认为饱和 → 回到步骤 1
    6. 两者都认为饱和 且 主进程无新方向 → 退出循环，进入终审
```

**详细步骤**：

**步骤 1：准备审查材料**

将以下内容整理为结构化的审查 brief：
- 种子想法和核心假设（及与 Phase 0 的差异——假设是否被修正过？）
- 所有调查发现的摘要（每个发现 2-3 句话）
- 已设计的候选因子草案
- 已排除的研究方向及原因
- 饱和论证（为什么认为没有更多值得探索的方向）

**步骤 2：并行启动两个独立审查**

使用同一份审查 brief，两个审查互相独立：

**a. Claude SubAgent**（使用 Agent 工具）：
```
Agent(prompt="[审查 brief 内容]... 请独立评估：(a) 是否有未被探索的重要方向？(b) 现有机制理解是否有逻辑漏洞？(c) 因子设计空间是否被充分探索？如果你认为有值得追加的探索方向，请给出具体的、可执行的建议（币种/时段/观察重点）。")
```

**b. Codex 审查**：将审查 brief 提交给 Codex，请求同样的独立评估。

**步骤 3：处置审查建议**

等待两个审查都返回后，对每条建议写处置表（见 §1 Codex 建议跟进纪律），明确采纳/拒绝/推迟及理由。

**步骤 4：执行 + 独立思考（关键步骤）**

- **如果有被采纳的建议**：执行对应的调查（正常走 Reviewer 审查流程）
- **执行完毕后，主进程必须独立思考**：基于新的发现，是否有自己想深挖的新方向？此时不是"Codex 的建议做完就结束"，而是把 Codex 的建议当作新一轮探索的起点。
  - 如果有新方向 → 继续自主研究（新的轮次，正常走 Reviewer），直到再次认为饱和 → 回到步骤 1
  - 如果没有新方向 → 回到步骤 1，重新提交审查

**步骤 5：退出条件**

- 两个审查者都认为饱和（无具体可执行建议）**且**主进程也无新方向 → 退出循环
- 退出后进入 Phase 1 终审 Reviewer + Compliance Monitor

**⚠️ 防无限循环**：如果已执行 3 次以上 Exit Protocol 循环，Compliance Monitor 应评估是否存在"审查者反复提建议但建议质量递减"的情况。如果后续建议都是对已有发现的微调而非新方向，可以判定饱和。

### Phase 2: Factor Design & Screening

> **⛔ 自动继续：** 完成 Phase 1 终审后，直接进入 Phase 2，不得暂停。

**⚠️ Phase 转换检查：** 确认 Phase 1 终审 Reviewer 和 Compliance Monitor 的状态已在 `quality_review.md` 和 `research_log.md` 中更新为最终结果（passed/failed），不得遗留 "pending"。

**⚠️ 执行前重新阅读 `crypto_mcp/README.md`，特别是工具列表和数据格式说明。**

#### 步骤 0: 编码反思（Phase 2 开始前必做，不可跳过）

在动手设计因子之前，主进程必须先在 research_log 中写一段结构化反思，回答以下三个引导问题。这是把 Phase 1 的"现象理解"转化为 Phase 2 的"因子设计方向"的关键过渡。

**引导问题（自由作答，不要求标准答案）**：

1. **核心 raw signal 是什么？** Phase 1 中你发现的、最值得编码成因子的 2-3 个原始信号是什么？它们各自捕捉的微观结构本质是什么？

2. **时序操作的探索空间在哪里？** 对每个 raw signal，你打算用什么时序操作来编码它？EMA 是默认选择，但远不是唯一选择。其他可能的时序操作包括（但不限于）：
   - difference / 变化率（捕捉信号的瞬时变化）
   - fast/slow ratio（捕捉相对趋势）
   - rolling rank / percentile（捕捉信号在近期历史中的极端程度）
   - rolling correlation（捕捉信号当前与某目标变量的同步性）
   - run length / streak（捕捉信号的持续状态）
   - z-score / standardization（捕捉相对历史分布的偏离）
   - 累积量 / cumulative sum 之类的积分变换
   
   ⚠️ **不要默认用 EMA 包一切。** 同一个 raw signal 用不同时序操作往往能提取不同维度的信息——它们可以**共存为多个独立的候选因子**，而不是非要选一个"最好的"。哪种操作最适合你发现的效应？为什么？

3. **lookback / 时间尺度怎么选？** 你的编码需要回看多少 bar 的历史？这个选择和效应的时间特征（Phase 1 步骤 3 第 5 要素中的记录）之间的关系是什么？

**输出格式**：在 research_log 中以 `[PHASE 2 编码反思]` 标记起一个章节，逐一回答上述问题。这段反思将成为后续步骤 1（编码探索）和步骤 2（因子定义）的设计依据。

#### 步骤 1a: 编码探索（小样本快速比较，不可跳过）

在大规模设计因子之前，先做一轮**编码方式的快速探索**。这是把"编码反思"中的设想落到实处的环节。

**做法**：
- 从 Phase 1 的发现中选取 **2-3 个核心 raw signal**（不必太多）
- 对每个 raw signal，**实际尝试多种时序编码方式**（不只是 EMA），例如：fast/slow ratio、difference、rolling rank、rolling correlation、run length、z-score 等
- 在**极小样本**（1-2 symbol-date 即可，成本很低）上快速计算每种编码与主预测口径的初步相关性
- 比较结果，记录每种编码各自捕捉了什么信息

**关键原则 — 多种编码可以共存**：
- 这一步的目的不是找"唯一最优编码"，而是**理解每个 raw signal 的不同时序操作各自能提取什么样的信息**
- 同一个 raw signal 用不同操作得到的多个因子，如果各自有独立的预测维度，**完全可以全部保留为独立的候选因子**——不需要从中挑一个
- 例如：对 same-price run intensity 这一个 raw signal，它的 EMA、其 fast/slow ratio、其 rolling rank 可能分别捕捉了水平、变化方向、相对极端度三个不同维度，这三个都可以成为独立因子

**输出**：
- 在 research_log 中以 `[PHASE 2 编码探索]` 标记记录：
  - 试了哪些 raw signal × 哪些时序操作的组合
  - 每种组合的初步表现（不需要正式 IC 计算，定性观察即可）
  - 哪些组合值得保留进入步骤 1b 做完整定义
  - 哪些组合明显无效，已被排除（说明理由）
- ⚠️ **不要把这一步当成 grid search**：这是探索性的，agent 自己决定试什么、试多少。重点是打开编码思路，避免无脑套 EMA

#### 步骤 1b: 因子设计深度思考（创造性环节，不可跳过）

基于步骤 1a 的探索结果，进行完整的因子设计。

1. **因子设计深度思考**：
   - 对每个 Phase 1 微观发现，结合步骤 1a 的编码探索结果，设计完整的候选因子列表
   - **一个微观发现通常可以衍生多个因子**——不仅来自不同的微观侧面（如 buy/sell 分支、不同 conditioning），也来自**同一个 raw signal 的不同时序编码**（步骤 1a 中保留的多个组合都进入候选）
   - **不要一个发现只产出一个"最显然"的因子就停下**
   - **时序探索（贯穿步骤 1a 和 1b）**：微观信号的原始形态往往不是最优的因子编码。时序变换可以把 AggTrans 级信号桥接到 AmountBar 级，也可以从同一信号中提取多个互补维度。步骤 1a 已经做了快速探索，本步骤是把探索结果落实为正式因子定义
   - **思考 Zebra Agent 实现**：因子最终在 OnAggTrans() 中增量计算，OnBarClose() 输出。设计时考虑这个约束
   - 在 research_log 中记录设计决策：为什么选择这种编码？考虑过但放弃了什么？步骤 1a 中的探索结果如何影响了最终选择？
   - **⚠️ 产出数量软目标**：一次研究建议产出 **5-8 个达到提交标准的高质量因子**。重点在质量和编码多样性而非数量堆砌。理想的因子集应覆盖：
     - (a) 多个 raw signal / 微观机制
     - (b) 多种时序编码方式（不全是 EMA 变体）
     - (c) 因子间互补而非高度相关
     
     如果经过充分探索（含独立饱和审查确认本方向已无更多可挖掘空间）仍不足 5 个，需要在 research_log 中详细论证原因，并由 Reviewer 确认本方向的因子空间确实有限
2. 因子精确定义（每个附微观机制 rationale）

**1.5. Phase 2 Codex 因子设计咨询（推荐）**：

在完成自主因子设计（第 1-2 步）后、进入小样本筛选前：
- 将候选因子列表 + Phase 1 机制摘要提交给 Codex，提问：
  - 是否有遗漏的编码方式（不同的数学变换、条件化维度、时间尺度）？
  - 哪些因子最可能与 f001/f002 已有因子冗余？
  - 有没有跨机制的交互因子值得尝试？
- Codex 建议按 §1 的处置表格式记录（采纳/拒绝/推迟 + 理由）
- 被采纳的建议加入候选因子列表，与自主设计的因子一起进入小样本筛选
- 在 research_log 中标注哪些因子来自 Codex 建议
- **⚠️ 独立思考原则**：Codex 的建议必须经过主进程的独立分析判断。不要因为"Codex 建议了"就直接采纳——要基于微观机制的合理性和与已有因子的差异性来决定

3. **所有候选因子全部进入小样本初筛（不允许过早收敛）**：
   - **⚠️ 反过早收敛规则**：Phase 1 产出的所有有微观机制支撑的候选因子，必须全部经过小样本 IC 筛选。不允许"第一个通过就跳过其余"。小样本筛选成本低（5 codes × 10 天），应该对所有候选因子都跑一遍，然后根据结果整体决策。
   - 如果某个候选因子的计算需要额外代码（如不同的数据处理逻辑、新的特征提取脚本），**启动 SubAgent 并行编写**，主进程继续推进其他因子的筛选，不要串行等待
   - **⚠️ 性能预检**：筛选脚本写完后，先对少量样本（如 1 code × 1 date）做 dry-run，评估全量运行时间是否合理。如果明显过慢，先优化（向量化、批量加载）再跑全量。
   - 样本：**5 coins × 10 天**（从研究集 A 2025-07-01 ~ 2025-09-30 随机抽样非连续日期）
   - 通道 A：线性 IC（vs ret_lag0_next100, next200）
   - 通道 B：非线性预测力（quintile 形状、conditional IC）
   - 拓展观察：next400, next800 表现
4. **大样本泛化**：7 coins × 全部研究集（集 A 92 天 + 集 B 11 天 = 103 天）
   - 只有通过小样本筛选的因子才进入大样本验证
   - 集 A 和集 B 分别报告 IC，检验跨时段一致性
5. 保留规则：A类/B类/AB类/R类（研究支撑），不用 IC 作为唯一 gate
6. **失败因子详细记录**（定义、指标、失败原因）
7. Phase 2 终审 Reviewer + Compliance Monitor
8. **⚠️ 因子数量与质量检查（Phase 2 → Phase 3 门控）**：
   - 统计通过大样本泛化的因子数量
   - **5-8 个高质量、低冗余、编码多样的因子是理想区间**：直接进入 Phase 3。Phase 2 终审 Reviewer 会重点检查：因子间相关性是否可控（避免高度冗余的变体堆砌）、编码方式是否有多样性（避免全部都是 EMA 变体）、每个因子是否有独立的微观机制 rationale
   - **超过 8 个** → 不是问题，但 Reviewer 会检查是否存在高冗余因子。如果发现 2 个或以上因子相关性 > 0.9 且无独立 rationale，建议合并或择优保留
   - **3-4 个** → 在 research_log 中记录原因（是 Phase 1 发现确实有限，还是编码探索不充分？）。如果是后者，回到步骤 1a 重新探索更多时序编码方式；如果是前者，由 Reviewer 评估是否合理后进入 Phase 3
   - **<3 个** → 必须回退到 Phase 1 或步骤 1a 重新探索。如果回退后仍不足 3 个，需独立饱和审查确认本方向确实已无更多可挖掘空间，并由 Reviewer 确认后方可继续
   - ⚠️ **不要为了凑数量而引入相关性极高的微小变体**。"5 个互补的因子" 优于 "10 个高度相关的同质因子"

### Phase 3: Main Caliber Validation

> **⛔ 自动继续：** 完成 Phase 2 因子数量检查后（达标或经审查确认），直接进入 Phase 3，不得暂停。

**⚠️ Phase 转换检查：** 确认 Phase 2 终审 Reviewer 和 Compliance Monitor 的状态已在 `quality_review.md` 和 `research_log.md` 中更新为最终结果（passed/failed），不得遗留 "pending"。

**⚠️ 执行前重新阅读 `crypto_mcp/README.md`。**

**⚠️ Phase 3 是强制步骤，不可跳过或与其他 Phase 合并。** 如遇数据量过大等技术困难，必须找替代方案（如降采样、分批处理），而不是跳过。跳过 Phase 3 = Compliance Monitor 判定不合规。

数据范围：研究集 A（2025-07-01 ~ 2025-09-30）+ 研究集 B（2026-01-10 ~ 2026-01-20），共 103 天。

> **⚠️ Phase 3 的核心心态是"试图打破你的因子"，而不是"确认它有效"。** 你在 Phase 1/2 已经建立了对因子的信心。Phase 3 的目标是主动寻找它可能失败的条件——如果找不到，信心更强；如果找到了，这是宝贵的知识。

1. **多 Horizon × 多 Window IC 矩阵**（next100/200/400/800 × ≥3 档 window）
   - ⚠️ **IC-vs-horizon profile 是诊断工具，不是 pass/fail gate**。不同因子可能在不同 horizon 上最强——这是正常的，反映了不同信号的时间尺度。一个因子在 next50 最强、另一个在 next400 最强，都可能是有价值的因子
   - 关键是**理解每个因子的 IC profile shape 意味着什么**：
     - 如果 IC 在短 horizon 强、长 horizon 快速衰减 → immediate impact 信号，可能更适合作为 LGBM 条件分裂特征
     - 如果 IC 在长 horizon 反而更强 → 慢信号 / 趋势型，可能需要更长 lookback 的编码
     - 如果 IC 跨 horizon 较平稳 → 信号有持续性，适合作为线性 alpha
   - 这些观察应记录在 factor_definition.md 的"特征说明"中，作为下游使用者（LGBM 训练 / 回测）的参考
2. **自主设计的稳健性验证**：
   - 对每个保留因子，先回答："这个因子在什么条件下最可能失败？"（例如：特定币种？特定时段？funding rate 结算期？与某个 f001/f002 因子高冗余？）
   - 然后设计针对性实验来检验这些失败假设
   - 典型的检验维度包括（但不限于）：跨币种一致性、24h 时段效应（亚/欧/美）、波动率分层、funding rate 周期效应、跨交易所行为差异——根据因子特性选择最相关的，而非机械执行全部
   - 在 research_log 中记录：你认为最可能的失败模式是什么？检验结果是否排除了这个风险？
3. **参数定稿**（halflife/window/是否 fast-slow 双轨）
4. **最终因子定义文档**
5. Phase 3 终审 Reviewer + Compliance Monitor

### Phase 4: Final Review & Report

> **⛔ 自动继续：** 完成 Phase 3 终审后，直接进入 Phase 4，不得暂停。

**⚠️ Phase 转换检查：** 确认 Phase 3 终审 Reviewer 和 Compliance Monitor 的状态已在 `quality_review.md` 和 `research_log.md` 中更新为最终结果（passed/failed），不得遗留 "pending"。

**⚠️ 执行前重新阅读 `crypto_mcp/README.md`。**

1. 触发最终 Reviewer 全面审查（数据纪律 + 方法论 + 因子质量 + 结论可靠性）
2. 触发最终 Compliance Monitor 全面检查
3. 完成 `research_report.md`（完整结构）
4. 产出最终交付物清单

---

## 3. 数据纪律红线（贯穿全流程）

研究阶段仅允许使用以下两个数据窗口，禁止接触窗口外的任何数据：

| 用途 | 数据范围 | 数据类型 | 说明 |
|------|---------|---------|------|
| **研究集 A（主）** | **2025-07-01 ~ 2025-09-30** | trades + L2 | 92 天，7 币种。Phase 1 观察 + 统计探索 + 因子设计 + 小样本筛选 |
| **研究集 B（辅）** | **2026-01-10 ~ 2026-01-20** | trades + L2 | 11 天，7 币种。跨时段风格验证 + 大样本泛化 |
| **禁区** | **上述两集之外的所有日期** | — | **研究阶段绝对禁止触碰**，包括 2025-10~12、2026-01-01~01-09、2026-01-21~02-10 |

**设计意图**：
- 研究集 A（2025 Q3）和 B（2026 Q1）在时间上分离 3+ 个月，避免因子过拟合于某一市场风格
- 集 B 提供 L2 数据，支持 OB 因子的设计和验证
- 禁区包含最终 realize 阶段的训练集（2025-10 ~ 2025-12）和验证集（2026-01-21 ~ 2026-02-09），防止研究阶段信息泄漏

**主预测口径**：`ret_lag0_next100` ~ `ret_lag0_next200`（AmountBar 时间轴）。拓展观察到 `ret_lag0_next800`。因子设计应匹配此 horizon，但研究阶段要理解市场本质，不要过度拟合。

**AmountBar 参数**：动态阈值（daily_thres_28800），每天约 28800 根 bar。使用 `compute_bars()` 工具时不指定 threshold 即使用默认动态阈值。

---

## 4. Phase 边界检查协议

**每个 Phase 结束时，执行以下检查协议：**

```
1. 重新阅读本 Skill 对应 Phase 的结束条件和产出要求
2. 【同步】先触发 Logger SubAgent，等待其完成对 research_report.md 本 Phase 内容的更新
3. 检查 research_report.md：本 Phase 对应的章节是否完整？如有缺失立即补充
4. 并行启动：
   a. Reviewer SubAgent（研究质量审查）
   b. Compliance Monitor SubAgent（流程合规检查）
5. 等待 Reviewer 和 Compliance Monitor 返回
6. Compliance Monitor 的合规报告追加到 quality_review.md（如文件不存在则创建）
7. 如果任一不通过：纠正后重新检查
8. 全部通过后：在 research_log.md 记录 Phase 完成，直接进入下一 Phase（不得暂停）
```

---

### 4.1 Phase 1 轻量合规检查

为防止"踩线停止"和逐轮 Reviewer 跳过，在 Phase 1 中周期性执行轻量合规检查。

**触发方式（已绑定到前置门控，无需单独记忆）**：
- 嵌入在 §2 Phase 1 循环的第 0.b 步中，当 round ∈ {4, 7, 10, 13, ...} 时自动执行
- 任何一轮 Reviewer 不通过时，由主进程立即 SendMessage(to: "compliance") 触发
- 由于 Compliance Monitor 是持久化角色，它会保留历次检查的记忆，能追踪趋势变化

**轻量检查内容**（Compliance Monitor 执行）：
1. **Reviewer 执行验证**：阅读 research_log.md 中的 `[REVIEWER R{N}]` 标记，核对：
   - 标记数量是否与声称的调查轮数一致？
   - 每个标记后是否有实质性的审查意见（不接受空白或纯"PASS"无理由）
   - 抽读 1-2 轮的完整 Reviewer 意见和主进程回应，检查是否有实质交互
2. **Report 同步审计**（注意：report 已在前置门控第 0.b 步强制同步，此处为二次确认）：
   - research_report.md 中已记录的调查轮次数是否与 research_log.md 中 `[REVIEWER R{N}]` 标记数一致？
   - 最近 2 轮的 report 记录是否包含 §1.7 完整六要素（目的/现象/假设对比/因子启示/效应时间特征/新问题）？
   - 如发现 report 仍滞后于 log → **标记为不合规**，阻塞直到补齐
3. **研究动态趋势**：
   - 最近 2-3 轮是否仍有意料之外的发现？（从 research_log 中查看"新发现"记录）
   - 是否有 Reviewer 提出但尚未通过调查回答的遗留问题？（持久化 Reviewer 可直接确认）
4. **踩线趋势预警**：如果已完成 ≥8 轮且 agent 表现出"准备收尾"的倾向，但仍有未回答的问题或新发现仍在涌现，发出警告

**输出**：轻量合规检查报告，追加到 research_log.md **和** quality_review.md。如有不合规项，主进程必须立即纠正。

---

## 5. Context 保鲜协议

**防止长对话中 workflow 要求被遗忘：**

1. **每个 Phase 开始时**：重新阅读本 Skill 对应 Phase 的要求
2. **每 3 轮调查后**：重新阅读 §Phase 1 核心要求
3. **做重大决策前**：重新阅读相关章节确认合规
4. **Compliance Monitor 每次检查时**：独立重新阅读完整 Skill 文档

这确保即使 context 被压缩，关键要求也会被周期性刷新。

---

## 6. 交付物清单

| 文件 | 内容 |
|------|------|
| `research_report.md` | 完整研究报告（§0-§7） |
| `research_log.md` | 带时间戳的完整日志 |
| `factor_definition.md` | 因子精确定义（Zebra Agent 可实现级别） |
| `quality_review.md` | Reviewer + Compliance 审查记录 |
| `code/` | 分析脚本和统计验证代码 |

**交付目录**：`/home/cken/crypto_world/crypto_ob_research/{N}-{topic}/`

---

## 7. 异常终止协议

如果因 context 限制、工具故障、或超时导致流程无法继续完成：

1. **立即**在 research_log.md 写入 `[INTERRUPTED]` 标记，记录：
   - 当前 Phase 和步骤
   - 已完成的工作清单（含已通过的调查轮数、已产出的因子列表）
   - 未完成的工作清单
   - 下次恢复的建议起点
2. 将当前已有的 factor_definition.md（即使是草稿版）和 research_report.md 保存
3. 写一份简要的 quality_review.md，标注状态为 `INCOMPLETE — Phase {N} 中断`，记录已完成的合规检查结果和未检查的项目
4. 确保 research_log.md 中所有已执行的调查轮次都有 `[REVIEWER R{N}]` 标记

这样后续可以恢复研究而非从零重来。用户可以将 `[INTERRUPTED]` 标记作为检索入口来决定是否继续。
