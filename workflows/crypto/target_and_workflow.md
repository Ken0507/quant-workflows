# Crypto 投研：目标与研究流程

> **用途**：本文件是整个 crypto 投研工作的"北极星"文档。供所有 agent 在接手任务前快速理解：我们要去哪里（目标）+ 我们怎么走（流程）。
>
> **维护节奏**：慢变。仅在投研目标或流程发生结构性调整时由用户手工更新。**agent 不得自行修改本文件**，只能在 meta-review 结束时提出 diff 建议，由用户审阅后落盘。

---

## 1. 投研目标

### 1.1 最终目标（北极星）

把 LGBM 融合后的**预测信号**做到：
- **高样本外 IC**：在 valid / holdout 上保持稳定、显著的 IC（优于当前 benchmark，且 ICIR 不能靠单日异常值撑起）
- **回测可稳定盈利**：从信号到回测链路打通后，maker / taker 模式下都能拿到稳定的夏普和可控的回撤

这是唯一目标，不设时间重心、不预先规划方向家族——任何能提高 LGBM 预测信号质量的因子都欢迎。

### 1.2 Deep-factor-research 子目标

在单次 `/crypto-deep-factor-research` session 中，目标是**挖掘尽可能多、尽可能高质量**的、对 **100~200 bar horizon** 有预测性的因子。预测性包括：
- **线性预测性**：对主预测口径（`ret_lag0_next100 ~ ret_lag0_next200`）有显著 IC
- **非线性预测性**：线性 IC 不强但在 LGBM 中作为条件分裂特征有价值（如 regime gate / 交互特征 / 高阶条件化）

⚠️ 不要只盯线性 IC 筛因子。非线性预测性同样是合法的价值来源，在 Phase 2/3 的筛选中要主动考察分位形状、条件 IC、与已有 baseline 的 LGBM 联合表现。

### 1.3 可用数据简介

| 数据 | 路径 | 覆盖范围 | 字段要点 |
|------|------|---------|---------|
| 逐笔成交 (trades) | `/data/db/crypto/futures/binance_histroy/raw/trades/{SYM}/` | 7 币种, 2019 ~ 2026-03 | Binance 原始 trade：price / qty / side / ts_ms |
| L2 订单簿 (Tardis) | `/data/db/crypto/futures/tardis/binance-futures/incremental_book_L2/{SYM}/` | 7 币种, 2025-07-01 ~ 2026-02-10 (225 天) | 增量 + 定期全量快照，可重建任一时刻 L2 |
| AmountBar 阈值 | `/data/db/crypto/futures/world/bod_data/daily_thres_28800/{SYM}/` | 7 币种, 2020 ~ 2026-01 | 动态每日阈值，目标 ~28800 bar/day |

**支持的币种**：BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT（7 个 U 本位永续合约）

### 1.4 AmountBar 定义 + 时间尺度估算

**AmountBar 是按累积成交额（notional，USDT）切分的 bar**：
- 不是按 wall-clock 时间切，而是按"累积多少美金成交额"
- 每日阈值来自 `daily_thres_28800`（动态阈值，目标每天约 28800 根 bar），阈值随币种和日期变化
- Agent 生命周期：`OnAggTrans()` 增量累计成交额，累计到达阈值时 `OnBarClose()` 落一行

**时间尺度估算（非常重要，agent 设计因子时要有直觉）**：
- 28800 bars/day ≈ **每 bar 平均 3 秒**（86400 / 28800 = 3）
- `next100` ≈ **未来 5 分钟**左右
- `next200` ≈ **未来 10 分钟**左右
- `next400` ≈ **未来 20 分钟**左右
- `next800` ≈ **未来 40 分钟**左右

但注意：
- AmountBar 是 volume clock 而非 wall clock。**高活跃时段 bar 更快、低活跃时段 bar 更慢**，上述秒数是按日均的粗略换算，真实秒数在日内波动可达 ±50%
- 设计因子 lookback / halflife 时应以 **bar 数**为单位而非秒，避免被 volume clock 扭曲
- 跨币种时，同样 100 bar 对应的 wall-clock 时间也不同（大币种成交更密集）

### 1.5 从因子到 LGBM 预测信号的链路

```
AggTrans / L2 event
        │
        ▼
  单因子 Agent（OnAggTrans 增量更新 → OnBarClose 输出）
        │
        ▼
  AmountBar 级因子列（(symbol, bar_id, close_time_ms) join key）
        │
        ▼
  与 baseline (f001+f002+已落地 FA) 在 join key 上 merge
        │
        ▼
  LGBM 训练（train / valid 按时间 80/20 切分）
        │
        ▼
  LGBM 预测信号 (continuous score)
        │
        ▼
  Analyzer 报告：单因子 IC / ICIR / 相关性 / LGBM 重要性 / 预测信号 OOS IC
        │
        ▼
  Signal Backtest：信号导出 → 并行回测 → train/valid × maker/taker 报告
```

**关键评估口径**：
- **单因子层**：IC / ICIR / 分位形状 / 条件 IC（用于 Phase 2/3 筛选）
- **LGBM 层**：valid OOS IC / ICIR / LGBM 特征重要性 / 相对 baseline 的增量（新 FA 的主验收口径）
- **回测层**：maker/taker 双模式夏普、回撤、turnover（最终目标口径）

### 1.6 方法论原则

- **微观机制优先于统计拟合**：每个因子必须有可口述的微观结构 rationale，不允许纯 mining
- **时序编码多样性**：这是 deep-factor-research 的核心设计纪律。同一个 raw signal 用不同时序操作可以提取完全不同维度的信息，它们可以**共存为多个独立因子**。
  - **重点：这里列出的只是最常见的起点，不是完备清单**。EMA / fast-slow ratio / rolling rank / rolling correlation / run length / streak / z-score / 累积量 / difference / percentile / conditional aggregation / interaction term……任何你想得到的时序变换都值得尝试
  - **鼓励突破列表**：agent 应在 Phase 2 的编码反思和探索阶段主动设计**列表外的**时序操作。"我试了列出的所有操作"不是饱和，"我探索了明显能捕捉这个微观机制的编码空间"才是
  - **反面行为**：默认用 EMA 包装一切、或用同一 lookback 穷举几种操作凑数——这两种都是浅探索
- **线性 + 非线性预测性都要**：Phase 2/3 筛选不得只用线性 IC 做唯一 gate，必须同时考察非线性预测力（分位形状、conditional IC、LGBM 联合表现）
- **数据纪律红线**：研究阶段仅使用研究集 A (2025-07-01 ~ 2025-09-30) + 研究集 B (2026-01-10 ~ 2026-01-20)，其余为禁区（含 realize 阶段训练/验证集）
- **失败因子也要记录**：失败因子的记录与成功因子同等重要，构成知识沉淀

### 1.7 每轮调查的记录格式

> **用途**：`/crypto-deep-factor-research` 的 Logger SubAgent 按此模板向 `research_report.md` 追加每轮 Phase 1 调查记录。`compliance_checklist.md` 对"调查记录格式"与"Report 同步审计"的检查也以此为准。
>
> **与 SKILL.md 的关系**：SKILL.md 与 compliance_checklist.md 中 "§1.7 格式" 或 "六要素" 均指向本节。

每轮调查必须产出以下完整记录（由 Logger SubAgent 详细记录）：

~~~markdown
### 调查 N：[标题]
**标的/日期/时段**：[symbol, date, time range]
**调查目的**：[为什么要做这轮调查？源自什么前序发现或假设？]

#### 观察到的现象（详细描述）
- [完整描述观察到的 L2 book 状态、AggTrans 流、trades 序列、价格变化等]
- [包含关键数据点：book 快照、事件时间线、具体 seq / ts_ms、flow / sweep / depth 量化指标]
- [引用 crypto-research MCP 工具（`open_session` / `get_events` / `get_book` / `analyze_sweep` / `flow_analysis` / `liquidity_profile` / `inspect_bar` / `explain_move` / `forward_returns` 等）的具体输出，而不是只给结论]
- 宁可冗长也不要压缩到一句话概括——观察细节是 Phase 2 因子设计和未来 meta-review 的核心原材料

#### 假设与结论对比分析
- **原始假设/预期**：[进入调查前预期会看到什么？]
- **实际观察**：[实际看到了什么？]
- **一致/不一致分析**：
  - 如果一致：[为什么一致？这增强了对哪个机制的信心？]
  - 如果不一致：[哪里不一致？不一致的原因是什么？需要修正哪个假设？]
  - 如果发现了意料之外的现象：[详细描述意外发现，分析其可能的原因]

#### 因子设计启示
- [如果要捕捉这个现象，AmountBar 级因子应该怎么设计/计算？]
- [对已有因子草案需要做什么调整？与 f001 / f002 / 已落地 FA 的关系？]

#### 效应时间特征
- [本轮观察的现象在时间维度上是怎么展开的？瞬时影响（一两个 bar 内结束）还是持续展开？]
- [forward return 在哪个 horizon 上最强 / 衰减最快？不同 horizon 是否表现出不同方向（如短反弹 + 中期延续）？]
- [是否观察到 regime 依赖、币种差异、跨币种传导时滞？]
- 定性记录即可，不要求严格定量分析；目的是给 Phase 2 编码方式的选择（EMA / fast-slow / rolling rank / run length / z-score / 条件聚合 …）提供依据

#### 新问题 / 新发现（驱动下一轮调查）
- [这轮调查引出了什么新的疑问？]
- [下一步应该调查什么？（对比组 / 反例 / 更极端场景 / 不同币种 / 不同 regime）]
~~~

**六要素硬性要求**：每轮记录必须包含 目的 / 现象（详细描述） / 假设对比 / 因子启示 / 效应时间特征 / 新问题 六个小节，缺一不可。Compliance Monitor 会逐轮核对，缺项视为不合规（report 滞后），Logger 必须补写后主进程才能进入下一轮调查。

---

## 2. 完整研究流程图

```
                    ┌─────────────────────────────────────────┐
                    │   用户种子想法 (seed idea, 一句话)       │
                    └──────────────────┬──────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 1: 深度单因子研究                                              │
│  Skill: /crypto-deep-factor-research {seed}                          │
│                                                                      │
│  目标: 尽可能多、尽可能高质量的 100~200 bar 预测性因子                 │
│        （线性 + 非线性预测性都要）                                     │
│                                                                      │
│  工作目录: crypto_ob_research/{N}-{topic}/                            │
│    Phase 0  Seed Idea                                                │
│    Phase 1  深度微观结构调查 (≥10 轮 Reviewer 通过 + 饱和审查)         │
│    Phase 2  Factor Design & Screening (编码反思 + 小样本 + 大样本)     │
│    Phase 3  Main Caliber Validation (多 horizon × window IC 矩阵)    │
│    Phase 4  Final Review & Report                                    │
│                                                                      │
│  产出: factor_definition.md / research_report.md /                   │
│        research_log.md / quality_review.md                           │
│  角色: Researcher + Reviewer + Compliance + Logger + Codex           │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │  (积攒若干个 session)
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 2: 因子集编译                                                  │
│  Skill: /crypto-factor-list-compile {范围|列表} -> FA{N}              │
│                                                                      │
│  输入: crypto_ob_research/{N1,N2,...}/factor_definition.md            │
│  输出: factor_agent_docs/FA{N}_factor_list.md                        │
│        factor_agent_docs/FA{N}_review.md                             │
│        factor_agent_docs/FA{N}_warning_factors.md (如有)              │
│                                                                      │
│  步骤: 合规分级 → 七要素预检 → 合并去重 → 分组 → 独立审阅 Agent        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 3: 工程落地                                                    │
│  Skill: /crypto-realize-factor {FA*_factor_list.md}                  │
│                                                                      │
│  工作区: zebra_pool/fa{N}/                                            │
│  子 Skill 调用:                                                       │
│    crypto-zebra-factor-write      — C++ Agent 实现 + smoke test      │
│    crypto-axis-alignment-check    — Join key 与 f001 对齐验证          │
│    crypto-zebra-factor-batch-run  — 批量刷数据                         │
│    crypto-analyzer-standard-report — LGBM 分析报告（单 FA）           │
│                                                                      │
│  Step 1: 实现 + Code Review + 性能优化 + Perf Review + Smoke           │
│  Step 2: 1 个月强验证 (数值/复算/不变量/口径/单测)                     │
│  Step 3: 刷全历史 + Analyzer 报告 × 2 (新因子单报 + merged baseline)    │
│  Step 4: 交付目录组装                                                  │
│                                                                      │
│  角色: PM + QD + QR + PO + Code Reviewer + Perf Reviewer + Compliance│
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 4: 信号回测（可选）                                             │
│  Skill: /crypto-signal-backtest                                      │
│                                                                      │
│  从 Analyzer LGBM 模型导出信号 → 并行回测 → train/valid × maker/taker │
│  产出: 持仓分布 + 收益曲线 + 综合报告                                   │
└──────────────────────────────────────────────────────────────────────┘

   ──────── 周期性迭代 (Benchmark Refresh Loop) ────────

┌──────────────────────────────────────────────────────────────────────┐
│  Stage 5: Benchmark 刷新（每隔 N 个 FA 跑一次）                        │
│  (目前无专用 skill，手工 / 参考 HFT pool/benchmark*/run_*.py)          │
│                                                                      │
│  触发: 每累计 2-3 个新 FA 落地后                                       │
│                                                                      │
│  步骤:                                                                │
│    1. 在 join key 上合并 [当前 benchmark] + [所有新 FA] 为大表         │
│    2. 跑一个完整 LGBM 训练 (train/valid 80/20 按时间切)                │
│    3. 取 LGBM feature importance 的 Top N（参考 HFT 的 top100 做法）  │
│    4. 固定 Top N 因子列表 + 该 LGBM 模型 → 作为"新 benchmark"          │
│    5. 新 benchmark 存档：带日期的目录（如 benchmark_{YYYYMMDD}）       │
│    6. 更新 sota_snapshot.md 中的 benchmark 指针和 Top N 清单           │
│                                                                      │
│  产出: 新 benchmark 的 LGBM 模型 + 因子清单 + Analyzer 报告             │
│  影响: 后续 deep-factor-research / realize 的 LGBM 训练都以新          │
│         benchmark 为起点，目标是"加入新因子后 valid OOS IC 超越        │
│         原 benchmark"                                                 │
│                                                                      │
│  参考 HFT 做法:                                                        │
│    /home/cken/hft_projects/HFTPool/pool/benchmark0323/                │
│      ├── run_benchmark.py   — 合并 baseline + 多个 FA 跑 LGBM          │
│      ├── run_top100.py      — 从 LGBM 重要性选 Top 100                 │
│      └── report_top100/     — Top 100 因子的独立报告                   │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼  (新 benchmark 回灌到下一轮 deep-research 的验收口径)
                               │
   ──────── 横向流程 (Meta Loop) ────────

┌──────────────────────────────────────────────────────────────────────┐
│  Meta Review (周期性自省)                                              │
│  Skill: /crypto-meta-review [direction]                              │
│                                                                      │
│  读取: target_and_workflow.md / sota_snapshot.md / research_updates.md│
│  扫描: 自上次 update 以来新增的 session / FA / realize / analyzer /  │
│        benchmark refresh                                              │
│  产出: 阶段总结 + 询问是否更新 sota_snapshot + research_updates        │
│                                                                      │
│  扩展: 用户可指定 direction 让其做定向深度分析（如 blocking 模式分析）  │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.1 Skill 总览表

| Stage | Skill | 输入 | 输出 | 典型触发 |
|-------|-------|------|------|---------|
| 1 | `crypto-deep-factor-research` | 种子想法 | `crypto_ob_research/{N}-{topic}/` | 用户给 idea |
| 2 | `crypto-factor-list-compile` | 研究编号范围/列表 | `factor_agent_docs/FA{N}_*.md` | 积攒 ≥3-6 个完成研究 |
| 3 | `crypto-realize-factor` | FA*_factor_list.md 路径 | `zebra_pool/fa{N}/` + analyzer 报告 | 编译通过后 |
| 3.子 | `crypto-zebra-factor-write` | factor_list + 研究报告 | C++ Agent 代码 | realize 内部 |
| 3.子 | `crypto-zebra-factor-batch-run` | 日期范围 + universe | parquet 数据 | realize / 验证 |
| 3.子 | `crypto-axis-alignment-check` | 因子输出路径 | 对齐报告 | smoke 后 |
| 3.子 | `crypto-analyzer-standard-report` | 因子数据路径 | LGBM 报告 | 刷数完成后 |
| 4 | `crypto-signal-backtest` | Analyzer 模型 | 回测报告 | 可选，作为最终验证 |
| 5 | _(暂无专用 skill)_ | baseline + 多 FA | 新 benchmark LGBM + Top N | 每 2-3 个新 FA 后 |
| Meta | `crypto-meta-review` | direction (可选) | 阶段总结 + 更新建议 | 定期自省 |

### 2.2 状态追踪单位

- **research session**：`crypto_ob_research/{N}-{topic}/` 一个目录 = 一次深度研究，含完整的四阶段产出
- **factor set (FA)**：`factor_agent_docs/FA{N}_factor_list.md` 一个文件 = 一组已编译待实现的因子
- **realized pool**：`zebra_pool/fa{N}/` 一个目录 = 已落地的 C++ 因子 Agent
- **analyzer run**：`/data/db/crypto/analyzer/fa{N}/{tag}/` 一次分析报告
- **benchmark**：带日期目录 + 一个 LGBM 模型 + 一个 Top N 因子清单 = 一个历史版本的预测信号基线

meta-review skill 按这些单位扫描 delta。

### 2.3 当前 benchmark 状态

当前 benchmark 清单 + Top N 指针维护在 `sota_snapshot.md` §1.4。每次 benchmark 刷新后，`research_updates.md` 必须记录一条 "benchmark refresh" 条目，说明：
- 本次刷新合并了哪些新 FA
- Top N 中进入/淘汰了哪些因子
- 新旧 benchmark 的 valid OOS IC 对比
- 下一轮 FA 研究的"待超越"目标

---

## 3. 本文件与其他文档的关系

| 文件 | 定位 | 谁写 | 更新频率 |
|------|------|------|---------|
| **target_and_workflow.md** (本文件) | 目标 + 流程图（慢变） | 用户手工 | 结构性调整时 |
| **sota_snapshot.md** | 当前最佳成果快照 + 当前 benchmark 指针 | meta-review skill 自动生成 | 每次 meta-review 确认后 |
| **research_updates.md** | 时间序列 changelog | meta-review skill 追加 | 每次 meta-review 确认后 |
| **crypto_ob_research/{N}/** | 单次研究全过程记录 | deep-factor-research skill | 每个 session |
| **factor_agent_docs/FA*.md** | 编译后的标准化因子定义 | factor-list-compile skill | 每次编译 |
| **zebra_pool/fa*/** | 落地工程代码 + 分析报告 | realize-factor skill | 每次实现 |

---

## 4. Skill 接入点与禁区

**允许的 skill 读写本目录**：
- `crypto-meta-review`：读本文件 + 读写 sota_snapshot + 追加 research_updates
- 所有其它 skill：只能**读**本文件（用于理解目标/流程），不得写

**agent 行为守则**：
- 运行任一 crypto 投研 skill 前，应先读本文件的 §1 确认任务对齐最终目标
- meta-review 产出的更新建议以 diff / 建议表形式呈现，由用户批准后才生效
- benchmark 刷新目前是手工触发的重要节点，agent 不应擅自决定触发时机——由用户判断是否时机成熟
