# HFT 投研：目标与研究流程

> **用途**：本文件是整个 HFT 可转债高频投研工作的"北极星"文档。供所有 agent 在接手任务前快速理解：我们要去哪里（目标）+ 我们怎么走（流程）。
>
> **维护节奏**：慢变。仅在投研目标或流程发生结构性调整时由用户手工更新。**agent 不得自行修改本文件**，只能在 meta-review 结束时提出 diff 建议，由用户审阅后落盘。

---

## 1. 投研目标

### 1.1 最终目标（北极星 · 三层递进）

把 LGBM 融合后的**预测信号**逐层推进到实盘可上线：

- **Layer 1 — LGBM 信号质量**：在 valid / holdout 上保持稳定、显著的 IC / ICIR（超越当前 benchmark0323_top100，且 ICIR 不能靠单日异常值撑起）。**sota_snapshot.md 严格只追踪到这一层。**
- **Layer 2 — SignalReplay 回测可稳定盈利**：通过 `/aef-hft-playground-signalreplay-backtest`，从 LGBM 信号导出到回测能拿到稳定的夏普、可控的回撤、合理的换手率。
- **Layer 3 — 实盘可上线**：通过 `cken_benchmark0323_v0` / Benchmark100Trader 等实盘策略在交易机上拿到可观察的 PnL，验证从信号到撮合的完整链路。

不设时间重心、不预先规划方向家族——任何能提高 LGBM 预测信号质量的因子都欢迎。

**为什么 SOTA snapshot 只到 Layer 1**：回测和实盘有独立的产出物（`daily_trading_report` / playground backtest 报告 / 实盘 PnL），它们的演进节奏比因子层快得多，强行揉进同一份 snapshot 会拖累信号层的迭代纪律。

### 1.2 单因子研究（deep-factor-research）子目标

在单次 `/aef-hft-deep-factor-research` session 中，目标是**挖掘尽可能多、尽可能高质量**的、对 **bar 级 next100 horizon** 有预测性的因子。预测性包括：

- **线性预测性**：对主预测口径（`ret_lag0_next100`）有显著 IC
- **非线性预测性**：线性 IC 不强但在 LGBM 中作为条件分裂特征有价值（stump ratio、conditional IC、与已有 baseline 的 LGBM 联合表现）

⚠️ 不要只盯线性 IC 筛因子。非线性预测性同样是合法的价值来源。

#### 1.2.1 Label basis（mid-label 主口径）

- **主预测口径**：`ret_lag0_next100`（bar 模式，单位是 bar 不是 tick）
- **底层计算**：`mid[t+h] / mid[t] - 1`，within_session 限定
- **辅助 horizon**：`ret_lag0_next1 / next2 / ... / next200`，共 18 个 horizon，供 IC-decay 曲线和 LGBM 多 horizon 评估
- **采样**：bar 模式 + `bar_col=bar_aggtrans_time_1`

### 1.3 数据资产

| 数据 | 路径 | 覆盖范围 | 字段要点 |
|------|------|---------|---------|
| 逐笔成交 + L2 订单簿 | 通过 HFT SDK（`source /data/share/dev/hft/setup_sdk.sh`） | 2025-01-02 起，bond_sz 全市场 190 codes | 深交所原始 tick：order / cancel / transaction；SZSE cancel 事件 price 恒为 0（需通过 bid_id/ask_id 回查原始委托） |
| basic_table 底表 | `/data/db/hft/factor_pool/debug/basic_data/basic_table/` | bond_sz 190 codes, 2025-01-02 ~ 2025-07-30+ | bar 级 OHLCV + quote（mid / spread）+ bar_aggtrans_time_1 切分。所有 factor pool 的 alignment 锚点 |
| Factor Pool | `/data/db/hft/factor_pool/{stage}/{author}/{factor_set_name}/{ds}/.../*.parquet` | 按 stage(debug/production) × FA × 日期分区 | 每 FA 输出一个 parquet（多列，每列一个因子） |
| Analyzer2 输出 | `/data/db/hft/analyzer2/{author}/{factor_set_name}/v{N}/` | 按 FA × version | report.md / metadata.json / daily_ic.parquet / signal_summary.parquet / signal_rank_table.parquet / coverage.parquet / img/ |
| Model Output | `/data/db/hft/model_output/{author}/{factor_set_name}/v{N}/` | LGBM 模型 + memmap + feature_importance | model.txt / lgbm_daily_ic_{train,valid}.parquet / feature_importance_gain.parquet / memmap/ |

**数据分区约定**（来自 `HFTPool/CLAUDE.md`）：

- **研究集**（exploratory）：`20250102-20250430`（4 个月）
- **标准提交集**（standard report 必用）：`20250102-20250730`（7 个月，139 个交易日）
- **Holdout**：`20250801` 之后 —— **禁止在因子研究阶段使用**，仅在最终交付报告解锁
- **Universe**：默认 `bond_sz`（190 codes），`--universe bond_sz`
- **统计显著性下限**：除 case_study 外，任何统计结论需 ≥ 1 个月全 universe 数据；tick 级最多 20× 均匀降采样

### 1.4 从因子到 LGBM 预测信号的链路

```
深交所 tick (order / cancel / transaction)
        │
        ▼
  单因子 Playground Agent（OnAggTrans / OnBookUpdate → bar_last 采样落 parquet）
        │
        ▼
  bar 级因子列（(code, time, bar_id) join key）
        │
        │  与 basic_table 在 join key 上 merge（取 mid / spread / bar_aggtrans_time_1）
        ▼
  Analyzer2 多数据集 cache（多 FA + baseline 在 join key 上合并）
        │
        ▼
  LGBM 训练（train/valid 按时间 80/20 顺序切分；111/28 天 = 标准提交集）
        │
        ▼
  LGBM 预测信号 (continuous score)
        │
        ▼
  Analyzer2 报告：单因子 IC / ICIR / 相关性 / LGBM 特征重要性 / Top0.1% Top0.01% 净收益
        │                                          ▲
        │                                          │
        │                                          │  benchmark refresh：每隔若干 FA 落地后，
        │                                          │  合并 baseline + 全部 FA 跑 LGBM，
        │                                          │  取 gain top N 作为新 benchmark
        ▼
  SignalReplay 回测（playground batch-backtest）→ PnL / Sharpe / MaxDD / 撤单率
        │
        ▼
  Benchmark100Trader 实盘部署（仅在 valid 回测稳定后）
```

**关键评估口径**：

- **单因子层**：IC / RankIC / 分位形状 / 条件 IC（用于 Phase 2/3 筛选）
- **LGBM 层**：valid RankIC / RICIR / LGBM 特征重要性 / 相对 baseline 的增量 gain（新 FA 的主验收口径）
- **回测层**：valid Sharpe / MaxDD / 换手率（Layer 2 验证口径）
- **实盘层**：日度 PnL / 撤单率 / 信号 Score 分布 / 延迟统计（Layer 3 验证口径）

### 1.5 方法论原则

- **微观机制优先于统计拟合**：每个因子必须有可口述的微观结构 rationale，不允许纯 mining
- **时序编码多样性**：同一个 raw signal 用不同时序操作可以提取完全不同维度的信息，它们可以**共存为多个独立因子**。EMA / fast-slow ratio / rolling rank / rolling correlation / run length / streak / z-score / 累积量 / difference / percentile / conditional aggregation / interaction term……agent 应在 Phase 2 主动设计**列表外的**时序操作
- **线性 + 非线性预测性都要**：Phase 2/3 筛选不得只用线性 IC 做唯一 gate，必须同时考察非线性预测力
- **数据墙红线**：研究阶段决策只能用 `20250101 ~ 20250630` 之前的数据；`20250701+` 是 holdout，研究阶段禁止使用，仅最终工程报告解锁
- **OB 深度要求**：Phase 1 ≥ 10 reviewer-passed 轮 + 独立 saturation 审查；"达到最低就停"不合规
- **失败因子也要记录**：失败因子的记录与成功因子同等重要
- **已知数据陷阱（SZSE cancel）**：CANCEL 事件 price 恒为 0、side 为 UNKNOWN，必须通过 bid_id/ask_id 从 order_info_map 查回原始委托。禁止直接用 `trans.price` 计算 cancel 相关金额

### 1.6 状态追踪单位

- **research session**：`HFTPool/ob_research/{N}-{topic}/` 一个目录 = 一次深度研究，含完整四阶段产出
- **factor set (FA)**：`HFTPool/factor_agent_docs/FA{N}_factor_list.md` 一个文件 = 一组已编译待实现的因子
- **realized pool**：`HFTPool/pool/FA{N}/` 一个目录 = 已落地的 C++ Playground Agent + Analyzer2 报告
- **factor parquet**：`/data/db/hft/factor_pool/debug/{author}/{factor_set_name}/` 一个数据集 = 全历史刷数产出
- **analyzer run**：`/data/db/hft/analyzer2/{author}/{factor_set_name}/v{N}/` 一次分析报告
- **benchmark**：`HFTPool/pool/benchmark{YYYYMMDD}/` 一个目录 + 一个 LGBM 模型 + 一个 Top N 因子清单 = 一个历史版本的预测信号基线
- **signal backtest**：playground batch-backtest 的 `report.md / metrics.csv / dashboard.png`（Layer 2 验证）
- **实盘 daily report**：`hft_projects/daily_trading_report/` 或交易机 session CSV（Layer 3 验证）

meta-review skill 按这些单位扫描 delta。

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
│  Skill: /aef-hft-deep-factor-research {seed}                             │
│                                                                      │
│  目标: 尽可能多、尽可能高质量的 next100 bar 预测性因子                  │
│        （线性 + 非线性预测性都要）                                     │
│                                                                      │
│  工作目录: HFTPool/ob_research/{N}-{topic}/                           │
│    Phase 0  Seed Idea                                                │
│    Phase 1  深度微观结构调查 (≥10 轮 Reviewer 通过 + 饱和审查)         │
│    Phase 2  Factor Design & Screening                                │
│    Phase 3  Main Caliber Validation                                  │
│    Phase 4  Final Review & Report                                    │
│                                                                      │
│  产出: factor_definition.md / research_report.md /                   │
│        research_log.md / quality_review.md                           │
│  权威规范: HFTPool/factor_agent_docs/deep_research_workflow.md         │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │  (积攒若干个 session)
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 2: 因子集编译                                                  │
│  Skill: /aef-hft-factor-list-compile {范围|列表} -> FA{N}                 │
│                                                                      │
│  输入: HFTPool/ob_research/{N1,N2,...}/factor_definition.md           │
│  输出: HFTPool/factor_agent_docs/FA{N}_factor_list.md                 │
│        HFTPool/factor_agent_docs/FA{N}_prompt.md                     │
│        HFTPool/factor_agent_docs/FA{N}_task.md（如有）                │
│                                                                      │
│  步骤: 合规分级 → 合并去重 → 分组 → 独立审阅 Agent                     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 3: 工程落地                                                    │
│  Skill: /aef-hft-realize-factor {FA*_factor_list.md}                     │
│                                                                      │
│  工作区: HFTPool/pool/FA{N}/                                          │
│  子 Skill 调用:                                                       │
│    aef-hft-playground-factor-write       — C++ Agent 实现 + smoke test   │
│    aef-hft-axis-alignment-check          — bar 级 join key 对齐验证        │
│    aef-hft-playground-factor-batch-run   — 批量刷历史数据                  │
│    aef-hft-analyzer2-standard-report     — Analyzer2 标准报告              │
│                                                                      │
│  Step 1: 实现 + Code Review + Smoke Test                             │
│  Step 2: 性能优化 + Perf Review                                      │
│  Step 3: Axis Alignment + 1 个月强验证                                │
│  Step 4: 刷全历史（standard set 20250102-20250730）                    │
│  Step 5: Analyzer2 报告 × 2                                          │
│           ├─ analyzer2_new_only           （仅本 FA 自评）             │
│           └─ analyzer2_merged_benchmark0323_top100 （叠加当前 SOTA）   │
│  Step 6: 交付目录组装                                                  │
│                                                                      │
│  权威规范: HftKnowledge/research_docs/factor_workflow.md +            │
│            HftKnowledge/research_docs/analyzer_user_manual.md         │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 4: SignalReplay 回测 (Layer 2 验证)                            │
│  Skill: /aef-hft-playground-signalreplay-backtest                        │
│                                                                      │
│  从 Analyzer2 LGBM 模型导出 SignalPack (bar_ffill / tick_predict)     │
│  → playground batch-backtest 回放                                    │
│  → 产出 report.md / metrics.csv / dashboard.png / 撮合日志             │
│                                                                      │
│  权威规范: HftAnalyzer2/docs/howto_playground_backtest_signalreplay_zh.md │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Stage 5: 实盘部署 (Layer 3 验证)                                      │
│  Skill: /aef-hft-live-strategy-deploy + /aef-hft-intraday-trading-analysis    │
│                                                                      │
│  Playground deploy（Docker 编译 + SCP 上传交易机）                     │
│  → 上传 prod_run/run.sh                                              │
│  → 交易机 systemd / crontab 启动 Benchmark100Trader                  │
│  → 盘中 /aef-hft-intraday-trading-analysis 拉日志 + Session CSV           │
│  → 收盘 daily_trading_report                                         │
│                                                                      │
│  实盘红线: 见 HFTPool/CLAUDE.md "Strict Safety Rules"                 │
└──────────────────────────────────────────────────────────────────────┘

   ──────── 周期性迭代 (Benchmark Refresh Loop) ────────

┌──────────────────────────────────────────────────────────────────────┐
│  Stage R: Benchmark 刷新（每隔 N 个 FA 跑一次）                        │
│  Skill: /aef-hft-benchmark-refresh {date} {datasets...}                  │
│                                                                      │
│  触发: 每累计 2-3 个新 FA 落地后，由用户决定触发时机                    │
│                                                                      │
│  步骤:                                                                │
│    1. 在 join key 上合并 [当前 benchmark] + [所有新 FA] 为大池          │
│    2. 跑一个完整 LGBM 训练（train/valid 80/20 按时间顺序切分）           │
│    3. 取 LGBM feature importance gain Top N（默认 N=100）              │
│    4. 固定 Top N 因子白名单 + 该 LGBM 模型 → 作为"新 benchmark"          │
│    5. 新 benchmark 存档:                                              │
│         HFTPool/pool/benchmark{YYYYMMDD}/                            │
│           ├── run_benchmark.py    （合并 baseline + FA 跑 LGBM）       │
│           ├── run_top100.py       （选 Top 100）                       │
│           ├── report/             （全池 analyzer 报告）              │
│           └── report_top100/      （Top 100 因子的独立报告）            │
│    6. 更新 sota_snapshot.md 中的 benchmark 指针和 Top N 清单           │
│                                                                      │
│  产出: 新 benchmark 的 LGBM 模型 + 因子清单 + Analyzer2 报告             │
│  影响: 后续 deep-research / realize 的 LGBM 训练都以新 benchmark 为     │
│         起点，目标是"加入新因子后 valid OOS IC 超越原 benchmark"       │
│                                                                      │
│  历史 benchmark:                                                      │
│    HFTPool/pool/benchmark0323/   — Refresh #0 (锁定 2025-03-23)       │
│      ├── DATASETS_DEF: baseline_150_new + FA12/16/20-25              │
│      ├── 410 候选因子 → top100 LGBM                                   │
│      └── 标准提交集 139 天（20250102-20250730）                        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼  (新 benchmark 回灌到下一轮 deep-research 的验收口径)
                               │
   ──────── 横向流程 (Meta Loop) ────────

┌──────────────────────────────────────────────────────────────────────┐
│  Meta Review (周期性自省)                                              │
│  Skill: /aef-hft-meta-review [direction]                                 │
│                                                                      │
│  读取: target_and_workflow.md / sota_snapshot.md / research_updates.md│
│  扫描: 自上次 update 以来新增的 session / FA / realize / analyzer /  │
│        benchmark refresh / signal backtest / ad-hoc 报告 / issues      │
│  产出: 阶段总结 + 询问是否更新 sota_snapshot + research_updates        │
│                                                                      │
│  扩展: 用户可指定 direction 让其做定向深度分析                          │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.1 Skill 总览表

| Stage | Skill | 输入 | 输出 | 典型触发 |
|-------|-------|------|------|---------|
| 1 | `aef-hft-deep-factor-research` | 种子想法 | `HFTPool/ob_research/{N}-{topic}/` | 用户给 idea |
| 2 | `aef-hft-factor-list-compile` | 研究编号范围/列表 | `HFTPool/factor_agent_docs/FA{N}_*.md` | 积攒 ≥3-6 个完成研究 |
| 3 | `aef-hft-realize-factor` | FA*_factor_list.md 路径 | `HFTPool/pool/FA{N}/` + analyzer 报告 | factor_list 编译通过后 |
| 3.子 | `aef-hft-playground-factor-write` | factor_list + 研究报告 | C++ Agent 代码 + smoke | realize 内部 |
| 3.子 | `aef-hft-playground-factor-batch-run` | 日期范围 + universe | factor parquet（全历史） | realize / 验证 |
| 3.子 | `aef-hft-axis-alignment-check` | 因子输出路径 | 对齐报告 | smoke 后 |
| 3.子 | `aef-hft-analyzer2-standard-report` | 因子数据路径 + 是否合并 baseline | Analyzer2 LGBM 报告 | 刷数完成后 |
| 4 | `aef-hft-playground-signalreplay-backtest` | Analyzer2 模型 / SignalPack | 回测报告 + metrics + dashboard | Layer 2 验证 |
| 5 | `aef-hft-live-strategy-deploy` | 策略 build + 交易参数 | 交易机上的实盘策略 | Layer 3 上线 |
| 5 | `aef-hft-intraday-trading-analysis` | 交易机 logs + session CSV | 盘中 PnL/延迟/Score 分析 | 交易时段 |
| 5 | `aef-hft-sync-market-data` | 日期范围 | 同步行情到本地 | 数据更新 |
| R | `aef-hft-benchmark-refresh` | baseline + 多 FA + Top N | 新 benchmark 目录 + LGBM + Top N 报告 | 每 2-3 个新 FA 后 |
| Meta | `aef-hft-meta-review` | direction (可选) | 阶段总结 + 更新建议 | 定期自省 |

### 2.2 当前 benchmark 状态

当前 benchmark 清单 + Top N 指针维护在 `sota_snapshot.md` §1。每次 benchmark 刷新后，`research_updates.md` 必须记录一条 "benchmark refresh" 条目，说明：

- 本次刷新合并了哪些新 FA
- Top N 中进入/淘汰了哪些因子
- 新旧 benchmark 的 valid OOS RankIC 对比
- 下一轮 FA 研究的"待超越"目标

---

## 3. 本文件与其他文档的关系

| 文件 | 定位 | 谁写 | 更新频率 |
|------|------|------|---------|
| **target_and_workflow.md** (本文件) | 目标 + 流程图（慢变） | 用户手工 | 结构性调整时 |
| **sota_snapshot.md** | 当前最佳成果快照 + 当前 benchmark 指针（只到 Layer 1） | aef-hft-meta-review skill 自动生成 | 每次 meta-review 确认后 |
| **research_updates.md** | 时间序列 changelog | aef-hft-meta-review skill 追加 | 每次 meta-review 确认后 |
| **HFTPool/ob_research/{N}/** | 单次研究全过程记录 | aef-hft-deep-factor-research skill | 每个 session |
| **HFTPool/factor_agent_docs/FA*.md** | 编译后的标准化因子定义 | aef-hft-factor-list-compile skill | 每次编译 |
| **HFTPool/pool/FA*/** | 落地工程代码 + 分析报告 | aef-hft-realize-factor skill | 每次实现 |
| **HFTPool/pool/benchmark{YYYYMMDD}/** | 一代 benchmark 的快照 | aef-hft-benchmark-refresh skill | 每次 refresh |
| **HftKnowledge/research_docs/** | 数据/流程/Analyzer 权威手册 | 用户手工 | 工具升级时 |
| **HFTPool/CLAUDE.md** | repo 级规则 + 数据墙 + 实盘红线 | 用户手工 | 规则变更时 |

---

## 4. Skill 接入点与禁区

**允许的 skill 读写本目录**：

- `aef-hft-meta-review`：读本文件 + 读写 `sota_snapshot.md` + 追加 `research_updates.md`
- `aef-hft-benchmark-refresh`：触发新 benchmark 落盘到 `HFTPool/pool/benchmark{date}/`，**不动本目录**；只在下一次 meta-review 中被指针更新引用
- 所有其它 skill：只能**读**本文件（用于理解目标/流程），不得写

**agent 行为守则**：

- 运行任一 HFT 投研 skill 前，应先读本文件的 §1 确认任务对齐 Layer 1 目标
- meta-review 产出的更新建议以 diff / 建议表形式呈现，由用户批准后才生效
- benchmark 刷新由 `aef-hft-benchmark-refresh` skill 执行，但触发时机由用户判断（agent 不主动决定）
- **实盘相关操作**：所有涉及交易机的修改（部署 / 重启 / 配置变更）必须经用户明确许可，遵守 `HFTPool/CLAUDE.md` 的 "Strict Safety Rules"
