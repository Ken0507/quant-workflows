下面这份是**增量因子簇 v3**（在你们已经开始生产上一版簇的基础上，继续往“更深的微观结构 + 行为学 + 机制分解”方向扩展）。我会把你提到的“人类订单 vs 机器订单”作为一个重点簇，同时也会把你朋友 roadmap 里提到的一些研究问题（Flawed Cancel / Ghost Moves / Clustering / Auto-corr / Herding / Unreasonable Orders / 心理价位等）拆成可落地的因子簇，并额外补一批我们此前没展开过的新方向。
（roadmap 里这些关键词与研究问题我会直接引用作为灵感来源。）

---

## 因子簇A：订单“风格/参与者类型”proxy（人类 vs 机器）——你新提想法的系统化版本

> 目标不是做“精确识别某个人/某机构”，而是用**可解释的启发式**把订单流拆成不同“行为风格”的子流：
> **手工型（human-like）**、**做市/刷单型（quote-like）**、**执行/信息型（execution-like）**。
> 然后你用这些子流的**净流、撤单质量、激进度、持续性**去预测 next20。

### A1. 为什么可能对 next20 work

* 你当前 Top80 里大量是 add/trade/cancel 的净流与不平衡（而且 bar 聚合 last_valid 会把很多量类因子变成“bar 末端冲击/状态”）。
* 但“同样的净流”如果来自不同风格的订单，含义完全不同：

  * quote-like（机器）可能带来**短期噪声与撤单虚深度**；
  * execution-like（机器/半机器）可能带来**更持续的漂移**；
  * human-like 更可能在**心理价位/整数价**附近堆量、并呈现**慢变量**。
* next20（~1000 tick）这个尺度，正好处在“风格差异能持续一段时间、但又不会被日内长周期完全淹没”的区间。

### A2. 如何给每个订单打“风格分数”（不做fit）

对每个 `ORDER+ADD`（或你们能识别的委托新增事件）计算一组**启发式打分**，最后合成 `style_score ∈ [0,1]`：

1. **数量“整齐度”/手数指纹（Size Roundness）**

* `round_size = 1[vol % base_lot == 0]`
* `multi10 = 1[vol 是 10/50/100 的倍数]`
* `size_digit_entropy`：统计最近窗口的 vol 末位分布熵（机器更均匀？人更集中？这要数据验证）
* `size_z = (log(vol)-median)/mad`：极端大/小单（常与执行/信息相关）

2. **价格“整齐度”/尾数指纹（Price Digit Preference）**

* `price_tail_class`：价格小数尾数属于 {0, 0.5, 0.1, 0.01…} 的哪个集合
* `dist_to_round_tick`：距最近“整数价/半整数价/0.1价位”的 tick 距离
  （你朋友 roadmap 也提到“整数价/阻力位聚集”值得研究，这里正好能与心理价位簇联动）

3. **生命周期/撤单速度（Lifetime / Cancel Latency）**

* `life_ms = t_cancel - t_add`（需要 order_id 追踪；如果只有聚合层也可做近似）
* `fleeting = 1[life_ms < T_short]`（典型 quote-like）
* `sticky = 1[life_ms > T_long]`（更像手工/意图单）
* 还可以分 `near` 与 `far`（靠近盘口 vs 远端挂单）的生命周期差异

4. **时间结构（Inter-arrival / Burstiness）**

* `dt_same_side_add`：与上一次同方向 add 的时间差
* `sub_ms_ratio`：近窗口内 dt < 1ms 的比例（明显偏机器环境）
* `burst_score = fast_rate - slow_rate`（你们已有 event_rate 思路，可复用）

5. **策略动作模式（Cancel→Replace / Chase）**

* `reprice_flag`: 在 Δt 内 cancel 后又 add，且价格更追（买更高/卖更低）
* `laddering_flag`: 同方向连续小幅改价追逐（典型 algo 执行）

把这些合成三类分数（建议线性加权即可，不拟合）：

* `score_quote_like`（短寿命、subms、高 cancel/replace）
* `score_human_like`（价格尾数集中、size倍数明显、寿命较长、节奏慢）
* `score_exec_like`（大单、追价、穿透、聚合成交簇伴随）

### A3. 可直接产出的因子（每 tick state）

* `share_quote_like_add_near` / `share_human_like_add_near` / `share_exec_like_add_near`（近端/远端分开）
* `net_flow_quote_like`、`net_flow_human_like`、`net_flow_exec_like`（add-cancel 或 add 的 signed turnover/vol）
* `cancel_rate_quote_like`（quote-like 的撤单率）
* `style_shift = share_quote_like_fast - share_quote_like_slow`
* `style_asym = share_exec_like_buy - share_exec_like_sell`

### A4. 参数怎么定（不fit）

* `T_short/T_long`：用订单生命周期分布的分位数定（如 10%/90% 分位），并在 `{5ms,20ms,100ms}` 这种小网格做稳健性。
* `base_lot`：直接从交易制度/数据统计得到（订单量常见最小单位）；如果制度不确定，用众数/峰值检测即可。
* 评估：看“风格分组后的净流”是否比总净流更单调、更稳健（分箱即可）。

---

## 因子簇B：心理价位/整数价聚集与“阻力位”结构（roadmap 的 Psychological Levels）

你朋友 roadmap 明确把“整数价或阻力价位是否形成聚集”列为研究问题之一。这和可转债盘面“手工挂单 + 心理位堆量”很契合。

### B1. 为什么对 next20 work

* 心理位聚集通常会造成：

  * **短期反弹/回落（mean reversion）**：碰到阻力/支撑被打回；
  * 或 **突破后的加速（breakout continuation）**：一旦墙被吃穿/撤走，价格滑移更快。
* next20 正好能覆盖“接近心理位→试探→突破/回撤”的一个完整小周期。

### B2. 因子（建议结合 full_book）

1. **距离与吸引**

* `dist_to_round_price_bps`：p_ref 到最近整数/半整数/0.1 价位的距离（bps）
* `approach_speed`：最近窗口该距离的变化速度（是否正在“吸向”该价位）

2. **心理位深度占比**

* 定义一个集合 `RoundLevels(R)`：在 `±R bps` 内，价格尾数属于某类（整数/半整数/0.1）的价位
* `round_depth_ratio = depth_at_RoundLevels / depth_total_within_R`
* `round_wall_strength = max(depth_at_round_level)/depth_total_within_R`

3. **触碰-反应统计（事件型，但可 carry-forward）**

* `touch_round_count`：过去窗口触碰心理位次数
* `bounce_rate`：触碰后 Δt 内反向回撤的比例（用简单计数，不回归）
* `break_rate`：触碰后 Δt 内突破并延续的比例（同上）

### B3. 参数选择

* 心理位类别只选 2–3 个：`{整数, 半整数, 0.1}`
* `R` 选 `{5,10,20 bps}`
* Δt 用 `{200tick,1000tick}` 或 `{1s,5s}` 两档。

---

## 因子簇C：Ghost Moves（无真实成交却快速变价）——roadmap 的 Ghost Moves

roadmap 里明确问了“价格能否在没有真实成交时快速变化？”

### C1. 为什么对 next20 work

* “无成交变价”通常来自撤单/补单造成的 best 迁移：

  * 可能是**流动性撤退/恐慌**（有信息 → 后续继续漂移）
  * 也可能是**虚假报价/噪声**（后续回补）
* 对 next20 来说，这是一个非常强的“状态切换信号”。

### C2. 因子构造

关键是把 **mid/最佳价变化** 按“是否有成交贡献”分解。

1. **Ghost Move 强度**

* `ghost_mid_move_bps`: 在最近窗口内，**mid 发生变化但成交额为 0** 的 bps 累计（或 EMA）
* `ghost_best_move_up/down`: 仅由撤单/挂单导致 bid/ask best 迁移的次数与幅度

2. **Quote-driven vs Trade-driven 归因比**

* `quote_move_share = |Δp_quote| / (|Δp_quote|+|Δp_trade|+ε)`

  * `Δp_trade`：只有 `TRANS+FILL` 时累积的价格变动
  * `Δp_quote`：只有 `ORDER add/cancel` 时累积的价格变动
* 分方向：`quote_move_share_up`, `quote_move_share_down`

3. **Ghost 的后效应**

* `ghost_then_trade_surge`: ghost move 后 Δt 内 trade_intensity 的提升（fast-slow）

### C3. 参数建议

* ghost 判断窗口：用 **事件数量窗**比时间窗更稳（你们 tick 密度变化大）
* 输出形态：推荐做成 state（EMA/fast-slow），避免 bar 内 max 聚合的工程争议。

---

## 因子簇D：Flawed Cancel / Distress Cancel（撤单“失误/慌撤”质量）——roadmap 的 Flawed Cancel

roadmap 把 Flawed Cancel 单独列出来：什么是 flawed cancel？是否表示 distress？

### D1. 机制直觉

“撤单”本身你们已有 cancel_flow_imb 等，但 **flawed cancel 的信息含量更高**：
它强调的是撤单发生在“本来应该成交/本来应该保留”的场景，往往对应：

* 看到信息后临时撤退（对未来方向更敏感）
* 或做市撤退导致的流动性断裂（对波动与跳价更敏感）

### D2. 三类可操作定义（都不需要回归）

1. **临成交撤单（Cancel-at-risk）**

* 撤单发生在 best 附近，且在撤单前 Δt 内出现对手方打单/成交压力
  例：ask1 上撤单，同时最近 Δt 内有大量 buy trades hitting ask（或 penetration 指标上升）
  输出：
* `cancel_at_risk_amount_side`（买/卖分别）
* `cancel_at_risk_ratio = cancel_at_risk / total_cancel_near`

2. **“等了很久才撤”（Regret Cancel）**

* `regret_cancel = 1[order_age > T_old] & cancel_near`
* 进一步细分：撤单后价格朝撤单方向走（说明撤对了）还是反向走（撤错了）

3. **撤单-追价重挂（Cancel→Replace Chase）**

* 同一 order_id 或同一“价位/方向”的短时间内：cancel 后在更差价位重新 add（买更高/卖更低）
  输出：
* `chase_replace_rate`
* `avg_chase_bps`（追价幅度）

### D3. 为什么对 next20 有效

* Cancel-at-risk / chase 行为往往具有持续性：撤完不会立刻回去补；
* 它们经常先于“真实成交推动”发生，是一种更早的状态信号。

---

## 因子簇E：Big Aggressive Clustering（大激进单簇）——roadmap 的 Clustering

roadmap 问“大的激进单会不会聚在一起？”

> 你们此前已经做了 run/metaorder（成交聚合），但这里再推进一步：
> **只盯“足够大的激进事件”**，做“簇强度/簇启动/簇衰减”的状态机。

### E1. 事件定义（建议两套并行）

* A：`penetration_bps > R` 或 `walk_levels >= L`
* B：`trade_turnover > Q90`（标的内分位）且 trade 是主动方向（hit/lift）

### E2. 因子

* `cluster_intensity_buy/sell`：近窗口大激进事件计数/成交额（EMA）
* `cluster_score = (count_fast - count_slow)/sqrt(count_slow+ε)`（不fit 的 z-like）
* `cluster_start_flag`：fast 突破 slow 的阈值（状态触发）
* `cluster_persistence`：触发后持续时间（carry-forward state）

### E3. next20 逻辑

* 大激进簇通常对应执行型资金的一段推进；推进一旦开始，next20 内“继续推进/冲击回补”概率显著改变。

---

## 因子簇F：Aggressive Flow 的自相关/切换状态（Auto-correlation Regimes）——roadmap 的 Auto-Correlation

roadmap 问“激进流是否有不同自相关 regime？”

### F1. 为什么是新信息

你们已有很多 EMA 流向，但**EMA 不等价于自相关结构**。
同样的 EMA 强度，在“强正自相关”（延续）和“负自相关”（来回打、做市对敲）下，next20 的含义不同。

### F2. 因子（无需回归）

把“激进事件方向”离散成 `s_t ∈ {-1,0,+1}`（例如 trade_imb 的 sign，或 marketable add sign）：

* `p_same_1 = P(s_t = s_{t-1} | s_{t-1}≠0)`
* `p_flip_1 = P(s_t = -s_{t-1})`
* `ac1_proxy = p_same_1 - p_flip_1`
* `run_len_mean`：同向 run 的平均长度（你们已有 run 概念，可复用但换成“激进事件序列”）
* `ac_regime_shift = ac1_fast - ac1_slow`

扩展：在不同条件下算一套（门控很重要）

* 条件：`spread_z` 高 vs 低、`thinness` 高 vs 低（你们已有 spread/薄厚状态）

---

## 因子簇G：Herding（羊群效应）——roadmap 的 Herding（可选：跨标的）

roadmap 问“能否检测 herding？”

如果你们训练/生产时能访问同一时刻全市场多只转债的特征（离线肯定可以，线上看系统架构），我建议做一类**市场广度/同步性**特征：

* `market_buy_cluster_share`：同时刻（或近窗口）有 buy cluster 的标的比例
* `market_netliq_imb_mean`：全市场净流不平衡均值/分位
* `market_vol_burst_share`：波动 burst 标的占比
* `self_minus_market`：本券信号减去市场均值（去掉共振项）

### 为什么对 next20 有效

* 很多行情是“市场共振”驱动：有了市场 herding 状态，本券信号的“纯 alpha”更清晰；
* 或者反过来：当市场极端 herding 时，本券的微结构信号更容易被放大（更趋势）。

---

## 因子簇H：Unreasonable / Irrational Orders（不合理订单/急迫订单）——roadmap 的 Unreasonable Orders

roadmap 举例：“spread 很大却下市价单”

### H1. 关键思想

“不合理”不等于“错”，它常常意味着：

* **非常急迫的执行需求**（信息/风控/止损/追涨）
* 或 **手工误操作/噪声**
  两者对 next20 的影响不同，所以要做分层。

### H2. 可落地定义与因子

1. **在极宽价差下的 marketable 行为**

* `unreasonable_cross = 1[spread_bps > S] & marketable_add_or_trade`
* `unreasonable_cross_share`：近窗口占比（买/卖分开）
* `unreasonable_cross_depth`：穿透 bps / levels 的均值（更急迫）

2. **极端滑点成交（trade_px_bps tail）**

* `tail_trade_bps_ema`：对 `|trade_px_bps|` 做 clipped EMA
* `tail_trade_dir_imb`：极端成交方向不平衡

3. **极端远端挂单（离盘口很远但金额很大）**

* 识别 “far & big” add：`dist_bps > R_far` 且 `amount > Q90`
* `far_big_add_rate`：这种行为可能是“挂墙/护盘/诱导”，也可能是手工保守单

### H3. 参数选择

* `S`（宽价差阈值）：用 spread_bps 分位（如 90/95）而不是绝对值
* `R_far`：用 bps（比如 >20/50 bps），适配稀疏价阶。

---

## 因子簇I：隐藏流动性/冰山/“打不穿”的价位（Iceberg / Refresh）

这是我们之前没系统展开的方向，且在转债这种盘里很常见：
你看到某个价位挂量不大，但成交总能不断在该价位发生，深度却反复回补。

### I1. 为什么对 next20 work

* 如果上方存在“刷新型卖方”（iceberg），上行推进会被吸收，next20 更容易回落或震荡；
* 如果刷新方被打穿/撤退，往往出现加速（突破）。

### I2. 因子（用 full_book 最舒服）

在某个价位（通常 best 或心理位）定义：

* `exec_at_price`：近窗口在该价位的成交额
* `displayed_depth_avg`：该价位平均显示深度
* `refresh_ratio = exec_at_price / (displayed_depth_avg + ε)`（>1 表示“成交远大于显示”）
* `replenish_time = E[hit后深度回补到阈值的时间]`（用简单均值/EMA）
* `iceberg_score = refresh_ratio / (replenish_time + ε)`（刷新快且吃得多）

输出：

* bid/ask 分开 + 不对称差值

---

## 因子簇J：Quote Staleness / 盘口“迟钝侧”（延迟/陈旧报价）

这是一个很“工程但很有用”的状态变量：
一侧盘口很久不更新，另一侧疯狂更新，往往意味着信息与风险不对称。

### 因子

* `age_bid1`, `age_ask1`：best 价位最后一次更新距今多久
* `stale_imb = age_bid1 - age_ask1`
* `stale_depth_imb`: “深度变动的 staleness”——某侧深度很久不变但成交/撤单在发生
* 与事件强度交互：`stale_imb * trade_intensity`（不需要你显式写交互，LGBM 也能学，但写出一个版本常常更省样本）

---

## 因子簇K：事件“语法/转移矩阵”（Event Grammar）——以前没谈过的一类结构特征

这里把订单流看作一个符号序列：
`{Add, Cancel, Trade}` × `{Buy, Sell}` × `{Aggressive, Passive}`
我们不做复杂序列模型，只做**转移概率/转移强度**（可解释、可工程化）。

### K1. 例子（rolling 计数即可）

* `P(Cancel | Add)`：新增后很快撤单的比例（quote stuffing / 虚深度 proxy）
* `P(Trade | Add_best)`：挂到 best 后被成交的概率（流动性毒性/被动成交风险）
* `P(Add | Trade_hit)`：被打之后是否快速补回（韧性/刷新）

### K2. 输出方式

* 每 tick 维护一个滑动计数（或 EMA 计数），输出这些概率（state）
* 再做 fast-slow 差：捕捉“行为语法突然变了”的 regime shift

---

## 因子簇L：Spread 的“状态机”与均衡回归（Spread Dynamics）——roadmap 的 spread equilibrium 问题

roadmap 里提到“spread 是否会向均衡收敛？宽 spread 是机会还是波动信号？”

你们已有 spread_ema / spread_z / spread_diff 等，但我建议再补一层**“持续时间/转移”**：

* `spread_state ∈ {1tick, 2-3tick, >3tick}`（或 bps 桶）
* `time_in_state`：进入该状态持续了多久
* `transition_rate_widen` / `transition_rate_tighten`：最近窗口 widen/tighten 的发生率
* `tighten_after_widen_prob`：宽 spread 后是否会快速收敛（一个很典型的 next20 结构）

---

# 最后：优先级建议（如果你要立刻排期）

如果只能先做 3 个新方向，我建议按“增量概率 × 工程成本”排序：

1. **A 订单风格/人类vs机器 proxy**（对所有 order/trade/cancel 信号都有门控增益，且你已经有生命周期/逐笔数据基础）
2. **C Ghost Moves + D Flawed Cancel**（属于“你们现有流向体系里最缺的一块：quote-driven price discovery & 撤单质量”）
3. **I 冰山/刷新 + B 心理价位**（可转债很容易出现“打不穿”的价位结构；full_book 能把这类信号做得很干净）

---

如果你愿意，我也可以把上面每个簇拆成一张“研发任务卡”（每卡 8–15 个因子，明确需要哪些字段、输出 state/amount、建议的 fast/slow 参数集合、以及最小验证图/统计），方便你直接丢给研究员实现与验收。
