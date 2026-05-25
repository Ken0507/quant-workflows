# HFTPool 高频因子任务分配（基于 `conversation_history_0121.md` v2）

面向：中国可转债｜逐笔委托/逐笔成交/重构订单簿（含 full_book）  
预测口径：`bar_aggtrans_time_1` bar 采样，label=`ret_lag0_next100`（单位：bar）  
产因子口径：逐 tick 更新 + bar_last 落盘（每个 `bar_aggtrans_time_1` 仅 1 行，同一 bar 内取最后一条；过滤只按 `is_continuous && is_session_end`）；不再维护 `signal_agg.json`；如需量类/累计量，必须在 Agent 内按 bar 自行维护并在采样点输出。

本文只做**任务分解与分工**；框架/API/刷数/Analyzer2 细节请直接看：
- `/home/cken/hft_projects/HftKnowledge/research_docs/data.md`
- `/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md`
- `/home/cken/hft_projects/HftKnowledge/research_docs/analyzer_user_manual.md`

---

## 1) FactorAgent 分工总览（5 人版本，可按需合并成 3–4 人）

### FactorAgent1：参考价体系 + 固定金额/固定风险尺度的流动性几何（偏 full_book 工具链）
覆盖 v2：第 1、2 节；补充：25-D/25-H/（可选 25-G）
- `p_ref` 家族：本任务几何因子默认用 `mid` 做 ref；并输出 `vwapmid(X)`、`micro_Lk`、`micro_queue_Lk`、`efficient price`（简化滤波）等差异项供模型选择
- 深度到 X、成本曲线斜率/曲率、bps 半径内可交易量、稀疏度/不规则网格、tradability

### FactorAgent2：队列/激进度 + 订单生命周期/撤单风险 + 结构因子（墙/闪烁/大小单）
覆盖 v2：第 3、4、12 节；补充：25-C
- `T_deplete`、被动单排队激进度（ahead_amount）、撤单 hazard、年龄结构
- 墙单强度/寿命/侵蚀、quote churn、大小单分层、crowding 指数

### FactorAgent3：成交侧预处理 + Metaorder/Run + 走档/穿透 + 毒性（固定延迟 realized spread）+ 库存压力
覆盖 v2：第 7、8、9 节；补充：25-F
- 逐笔成交微聚合（micro-batch）A/B 两套规则
- run 统计、穿透强度（levels/bps/ratio）、realized spread / adverse selection（不回归）
- realized spread 的 `p_ref` 建议 A/B：`mid` vs `vwapmid(200k)`（若已实现），用少量版本做消融
- inventory pressure（passive fills），impact efficiency

### FactorAgent4：结果层 OFI + 距离分桶迁移 + Cross-spread 分层 + 事件主导权/一致性/机制拆解
覆盖 v2：第 5、6、13 节；补充：25-A/25-B/25-E
- Δdepth 定义 OFI（无 PCA，确定性汇总）
- bps/amount 分桶的 add/cancel/trade 迁移；cross-spread 深度分层
- add/cancel/trade dominance；flow consistency；cancel-share 驱动拆分；forward barrier change

### FactorAgent5：时间尺度自适应 + 韧性/恢复（连续 proxy + 事件型）+ 条件化动量/回归交互
覆盖 v2：第 10、11、14、15 节
- time-based EMA（`alpha=1-exp(-dt/tau)`）与强度归一（per-sec/per-event/per-amount）
- resilience proxy（coverage≈100%）+ shock-recovery（覆盖低但强）
- 条件化交互项（thinness/absorption/resilience 门控的 mom/mr）
- bar-reset（v2 §15.1）：若需要量类/累计量，允许在 Agent 内按 bar 重置/维护累加器，并在采样点输出最终值（不再使用 `sum_signals` / `signal_agg.json`）

---

## 2) 建议共用的“中间量/工具函数”（减少重复开发）

强烈建议 5 位 FactorAgent 对齐**同一套中间量定义**，否则后续合并/消融会变得非常痛苦：

### 2.1 统一单位与基础量（务必对齐）
- `PRICE_SCALE=1000`：所有 `int64 price` 与 `GetMidPrice/GetMicroPrice` 返回的 double 仍是缩放价，需要 `/1000.0` 还原。
- `amount_milli = price_scaled * volume`（单位：milli-yuan；用于“固定金额阈值 X”与 flow/成本计算）。
- 时间戳：`exchange_ts/local_ts` 为 ns epoch（`1s=1e9ns`，`1ms=1e6ns`）；建议用 `exchange_ts` 计算 dt。
- 输出时间：按项目规范用 `time=event.local_ts`。

### 2.2 full_book 相关通用函数（FactorAgent1 牵头沉淀）
- `CumAmountWithinBps(side, p_ref, R_bps)`：在 `p_ref±R` 内累计 amount（bid/ask 分开）。
- `PriceAtCumAmount(side, X_amt)`：从 best 向外吃到累计 amount≥X 时的最差价（不可达则返回最远价 + `coverage=0`）。
- `VwapToCumAmount(side, X_amt)`：吃到 X 金额的 VWAP（不可达同上）。
- `GapStatsWithinBps(side, p_ref, R_bps)`：max/mean/std gap_bps、large_gap_ratio、effective_tick_bps 等。

### 2.3 事件分类与 signed 规则（FactorAgent4 牵头对齐）
- ORDER：`ADD`/`QUEUEING` 视为 add；`DELETE/CANCELED/REJECTED` 视为 cancel。
- TRADE：`exec_type==FILL` 视为 trade；`exec_type==CANCEL` 视为 cancel（若确实出现在回放流）。
- trade sign：优先用 `trade_bs_flag`（`'B'`=buy aggressor，`'S'`=sell aggressor，其他当 UNKNOWN=0）。
- order sign：用 `event.order->side`（BUY=+1，SELL=-1）。

### 2.4 统一的 EMA（FactorAgent5 牵头）
- event-based EMA：固定 `alpha=2/(N+1)`（N 用 `{64,256}` 两档足够）。
- time-based EMA：`alpha=1-exp(-dt/tau)`（tau 用 `{1s,5s}` 两档足够）。

---

## 3) 统一参数建议（控制参数爆炸；可做小集合 A/B）

建议先按下列“最小可用”参数集落地，后续再做消融：

- 金额阈值 `X`（milli-yuan）：先做 3 档 `{50k, 200k, 1m} CNY`（即 `{5e7,2e8,1e9}` milli-yuan）；同时输出 `coverage_X`。
- bps 半径 `R_bps`：`{5,10,20}`。
- OFI 权重：指数权重 `exp(-λ·dist)` 仅做 `λ∈{0.3,0.6}`（或仅做 0.6）。
- trade 微聚合：`Δt∈{1ms,5ms}` 二选一（A/B）。
- realized spread 延迟：`Δt=3s`（先做 time-based 一档；后续再加 tick-based）。
- shock 阈值：用分位（如 90%/95%）控制事件型覆盖率在 1%–10%。

---

## 4) 每位 FactorAgent 的交付物（建议）

每人至少交付：
- 1 个 factor agent（Playground 工程），包含本任务包的 signals（按本文定义）。
- 1 份 `README.md`/`factor_set_metadata.json`：明确采样口径（bar_last + gated）与如有的 manual_sum 列名/代码位置。
- 1 个最小自检：单日单标的跑通、parquet schema 固定、数值无 NaN/Inf（流程见 `factor_workflow.md`）。

对应的详细因子定义与易错点：见同目录下 5 份 FactorAgent 任务文档。
