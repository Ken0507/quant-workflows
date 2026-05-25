Conversation History



User:

我现在正在做HFTPool的高频挖因子项目。市场是中国可转债市场，使用的数据是逐笔委托、逐笔成交、和根据逐笔数据逐笔更新的重构的盘口数据。

目前我有80个研究员做出来的因子的baseline，附件是他们的介绍。

我目前的主要预测目标是就entrust bar 1m (1 million CNY的委托做成的bar)下，next20个bar的return。换成tick的话大约在1000tick左右。我的因子会过一个LGBM模型进行预测。注意：我们虽然预测的时候按照entrust bar采样，但生产因子的时候会每个tick都产一个值，在采样时我们目前的做法是对state的因子取last，对amount/volume类的因子取bar内的sum。

目前的这些因子我觉得大部分还是太浅、太简单了，不能够足以捕捉市场的深度变化。所以想让你进行详尽的思考，看看在这个场景下，我们该新增哪些因子，或者已有的因子有哪些值得做的改进。你应该以“因子簇”的思维进行思考，具体的参数不是很重要，但是想法、因子构造的思路、逻辑是重要的。

除了比较经典但我们还缺少的因子以外，你还应该更注重一些具有一些深度逻辑的因子。比如说委托单的生命周期是否可以写成一些因子？我算imbalance等时候使用“考虑固定volume/amount内的单”而非“固定档位的单”，是否会更好？我对每个单在订单簿的位置、自身大小等等进行分类，是不是就能写更多样的因子？是否应该用更好的micro price来代替mid price？是否应该对一些连续的同方向单根据某些方式做聚合，这样处理后的数据写出来的一些因子会不会更好？这样具有深度的想法应该有很多，你必须在除了我讲的几个想法以外，自己独立思考，挖掘出更多更多的想法、逻辑，想出多种类的有深度的因子簇。

请你最后交付一份我可以新写的因子簇的建议，尽可能详细、因子簇数量尽可能多，你可以花费非常多时间进行思考，以提交一份高质量的回答。同时，对每个因子簇，你都要详细阐述因子背后的逻辑、原理、为什么会对我们这个horizon的预测work，让读者能根据你的回答做深度的学习和研究。



Agent:

我已经把你给的 Top80 baseline 因子说明通读了一遍：目前模型最依赖的仍然是**订单新增/撤单/成交的净流向（多用 EMA 比值或 EMA 强度）+ 盘口静态形状（spread、gap、slope/convexity、深度不平衡）+ 波动/活动度状态**这条主线；并且这版 baseline 的 bar 聚合口径里 `sum_cols=[]`，导致不少“事件量/金额”类原始因子在 downsample 时更接近 **bar 结束附近的一次冲击（last_valid）**而不是“整根 bar 的总量/强度”。

你现在想要的是：跳出“浅层 snapshot/简单 imbalance”，做能刻画**深度结构变化**、并且在你们这个预测 horizon（entrust_1m bar 的未来 20 根，约 1000 tick 左右）上依然能“持续发力”的因子簇。下面我按“因子簇”的方式给出一套可直接开工的新方向；每个簇我都会写清楚：

- **核心机制/为什么能对 next20 work**
- **建议的一族因子（不用纠结参数，重点是构造逻辑）**
- **实现要点（你们有逐笔委托/逐笔成交/重构盘口，很多都能在线 tick 更新）**
- **和你们 entrust bar 采样/聚合的配合方式**

------

## 先给一个总框架：要从“状态量”升级到“过程量”

你们现在的 Top80（从描述看）有两类角色：

1. **方向信号**：订单新增净流/成交流向/净流动性（add vs cancel）一类；
2. **状态门控**：spread、gap、波动、深度、slope/convexity、订单笔数结构等。

但要捕捉“深度变化”，真正缺的往往不是再来一个 imbalance，而是三类更“过程化”的东西：

1. **队列与生命周期（Queue & Lifetime）**：盘口深度不是静态数，是一堆订单的“生老病死”。
2. **固定金额/固定风险尺度的流动性（Volume/Amount-based liquidity）**：不要被固定档位绑架。
3. **冲击—吸收—恢复（Impact / Absorption / Resilience）**：next20 的可预测性往往来自“冲击之后市场怎么消化”。

下面的因子簇就是围绕这三条主线展开，同时补齐你提到的 microprice、连续同向聚合、订单分类等。

------

# 因子簇 1：订单生命周期与“存活结构”因子（Order Survival / Aging）

### 核心逻辑

盘口里的每一份深度都有“质量差异”：

- **年轻的流动性**（刚挂上）更可能撤掉（“虚”），也更可能是追价/信息单；
- **年老的流动性**（挂很久不撤）更像真实支撑/阻力；
- 未来 next20 的价格路径，很多时候取决于：**某一侧的支撑/阻力到底是“真墙”还是“泡沫”**。

尤其在可转债这种常见“薄盘 + 事件驱动 + 短时段流动性骤变”的市场里，**撤单行为**往往比“挂单量本身”更领先。

### 一族因子建议

按 side（bid/ask）× 距离桶（见簇 4）分别统计：

1. **活跃订单年龄结构**

- `age_mean_near_bid / age_mean_near_ask`
- `age_p90_near_bid - age_p90_near_ask`
- “年轻占比”：`vol(age<T)/total_vol`（T 用秒或事件数）

1. **撤单 hazard / 生存率**

- `cancel_rate_per_live_vol = cancel_vol / live_vol`（滚动/EMA）
- `survival_ratio(T) = vol(存活超过T)/live_vol`
- “撤单加速度”：`cancel_rate_fast - cancel_rate_slow`

1. **“墙”的寿命**

- 识别 near 区域里大体量价位（见簇 12），跟踪其存在时间、衰减速度（撤单/被成交）

### 实现要点

- 如果逐笔委托里能拿到 `order_id`（或至少能追踪单子级别的 add/delete/fill），就可精确维护：
  - 每个 price level 的 `sum_age_vol`、`sum_vol`、`count`，tick 更新时增量维护。
- 如果 order_id 不完整，也可用近似：把“某价位新增 volume 的时间戳”当作“该价位新鲜度” proxy。

### 与 entrust bar 采样

这些都是**状态量**，tick 产出后采样取 `last` 即可；也可以在 bar 内同时输出“bar 内新进入的年轻流动性占比变化”（flow 量）。

------

# 因子簇 2：队列位置与“预计排队时间”因子（Queue Position / Expected Time-to-Fill）

### 核心逻辑

L1/L2 的深度不平衡只是表象，真正影响 next20 的，是**队列会不会被吃穿**：

- 若 ask 队列很薄，同时 buy aggressor（成交/可成交挂单）强，价格上行更可能在 next20 里延续；
- 反过来，若队列很厚且 replenishment 快，冲击会被吸收，走势更可能回归。

“排队时间”把**队列长度 + 对手盘主动强度**合成一个更机制化的量。

### 一族因子建议

对 best bid/ask（也可以扩到 L2/L3）：

1. **预计耗尽时间**

- `T_deplete_ask = Q_ask1 / buy_trade_rate`
- `T_deplete_bid = Q_bid1 / sell_trade_rate`
  其中 `buy_trade_rate` 可用最近窗口（EMA）的“打到 ask 的成交量/成交笔数/成交额”。

1. **队列推进速度**

- `dqdt_ask = -d(ask1_vol)/dt`（也可以用事件数）
- `dqdt_bid` 同理

1. **队列压力不对称**

- `(1/T_deplete_ask) - (1/T_deplete_bid)`
- 或者 `log(T_deplete_bid/T_deplete_ask)`

1. **“排队时间 surprise”**

- `T_deplete - EMA(T_deplete)`（结构突变更重要）

### 实现要点

- 你们有逐笔成交，可直接按 trade sign 估计 “hit ask 的买单强度 / hit bid 的卖单强度”。
- 用事件时间（每成交一次更新一次）也行；用真实 dt 也行。建议两套都留。

### 与 entrust bar 采样

状态量取 `last`；也可以在 bar 内累计“队列耗尽事件次数（best price change 触发）”。

------

# 因子簇 3：盘口变化版 OFI（用“深度变化”而不是“事件标签”）

### 核心逻辑

你们现在的 flow 多是从事件类型（ORDER+ADD/DELETE、TRANS+FILL）直接累积 signed volume/turnover。
但更稳健的一条路是：**直接用重构订单簿的 Δdepth** 来定义 Order Flow Imbalance（OFI）——它把新增、撤单、成交等所有导致深度变化的东西都“统一到结果层”。

- 这对“逐笔数据重构盘口”尤其合适：你们可以拿到每个 tick 前后的 L1..Ln 深度变化。
- 也更容易捕捉一些“事件分类噪声/漏标”。

### 一族因子建议

对每档 i：

- `ΔBid_i = BidVol_i(t) - BidVol_i(t-1)`
- `ΔAsk_i = AskVol_i(t) - AskVol_i(t-1)`

经典 OFI 可以做：

- `OFI_i = ΔBid_i - ΔAsk_i`（或按价位变动做更严谨定义，价位跳变时要做对齐）
  然后构造：

1. `OFI_L1, OFI_L1-3, OFI_L1-10`（加权/求和）
2. `OFI_fast / OFI_slow / diff`（多尺度）
3. `OFI_PCA1`：把 `[OFI_1..OFI_10]` 做 PCA，第一主成分常常是“整体买压/卖压”。

### 为什么对 next20 有效

- OFI 描述的是**供需净变化的结果**，天然更贴近“未来价格要往哪边漂”。
- 多档 OFI + PCA 能刻画“压力是集中在近端还是远端”，这比单一 imbalance 更能解释 next20 的持续性。

### 与 entrust bar 采样

OFI 是“变化量”，更像 flow：

- tick 级别做 EMA（变成状态量）→ 采样取 last
- 或者做“bar 内累计 OFI”（见簇 24 的 bar-reset 思路）→ 采样 last 等于 bar sum

------

# 因子簇 4：从“固定档位”升级到“固定金额/固定 volume 的流动性尺度”（你提出的关键点）

### 核心逻辑

固定 L10 或 L5 的定义在不同标的/不同流动性状态下“经济意义不一致”：

- 有时 L2 就已经是空的；有时 L10 仍然很密；
- 你们的 bar 是按 **entrust amount** 定义的（本身就是“金额尺度”），所以用固定 amount/volume 的盘口特征，和标签尺度更一致。

### 一族因子建议

给定一个目标金额/目标量阈值 `X`（例如 10w/30w/100w CNY 或对应手数）：

1. **达到 X 所需的价格距离（liquidity cost / depth-to-X）**

- `dAsk(X) = (p_ask_at_cumAmount=X - mid)/mid`（bps）
- `dBid(X) = (mid - p_bid_at_cumAmount=X)/mid`（bps）
- 组合：
  - `eff_spread_X = dAsk(X) + dBid(X)`
  - `cost_asym_X = dAsk(X) - dBid(X)`（上行更容易 vs 下行更容易）
  - `log(dAsk(X)/dBid(X))`

1. **固定金额的“近端厚度”**

- 在 `|price-mid| <= d` 的范围内，累积 amount：`cumAmount_near_bid(d), cumAmount_near_ask(d)`
- 再做 imbalance：`(bid-ask)/(bid+ask)`

1. **深度曲线的“弹性/斜率”**
   把 cumulative amount 曲线看成 `Amount(p)`，计算：

- `elasticity_bid = dPrice/dAmount` 在 near 区域的平均（相当于“每 1w 金额推动多少 bps”）
- ask 同理，做不对称

### 为什么对 next20 有效

- next20 事件窗口内，价格漂移的主要驱动之一是“**某一侧的可交易流动性到底薄不薄**”。
- `dAsk(X)` 这类量比 L10 depth 更直接回答“吃掉 X 金额要走多远”，其持续性往往能跨过数百 tick。

### 实现要点

- 你们 book 目前可能只存 L10：那就用 L10 的 cumAmount 近似；如果 L10 仍不够覆盖 X，则设为缺失/截断并输出“不足覆盖标记”。
- 这类因子天然适合做多尺度 X（小 X 捕捉短期推进，大 X 捕捉中期阻力）。

------

# 因子簇 5：按“距离桶”分层的净流动性迁移（Near/Far Liquidity Migration）

### 核心逻辑

同样是 add/cancel，发生在不同距离上含义完全不同：

- **近端补给**（贴近 best）会直接影响 next20 的可推进性；
- **远端补给/撤离**更像“意图/墙”的变化，影响中期阻力；
- 价格常见的过程是：先撤近端 → 价动 → 再在更远处重新挂墙。
  因此你要的是“流动性在 price axis 上的迁移”。

### 一族因子建议

定义距离桶（示例）：

- `B0`: inside-spread（若存在）
- `B1`: best level
- `B2`: 1–2 ticks away
- `B3`: 3–5 ticks
- `B4`: >5 ticks（或直到 L10）

对每个桶、每个 side 维护：

- `add_amount`, `cancel_amount`, `net_liq = add - cancel`（可再拆 marketable/passive）

组合成：

1. `net_liq_imb_Bk = (net_bid_Bk - net_ask_Bk)/(|net_bid_Bk|+|net_ask_Bk|+eps)`
2. `migration_index = net_liq_near - net_liq_far`（或比值）
3. `reposition_speed`: 近端撤离同时远端补给增强（典型追价/防守迁移）

### 为什么对 next20 有效

- next20 里价格能不能继续走，取决于**前方阻力是不是被撤走、后方支撑是不是补上**。
- 迁移型特征比单点 imbalance 更能捕捉“深度变化”。

------

# 因子簇 6：侵略性分解（Marketable / Inside-spread / Join-queue / Away）

### 核心逻辑

“挂单净流”里混了太多不同意图：

- marketable add（本质接近市价单）表达的是“立刻成交意图”；
- inside-spread add 表达的是“愿意改善价格抢队列”；
- join-queue 表达“愿意排队但不追”；
- away 表达“挂墙/意图”。
  把它们拆开，模型才更容易学到稳定规律。

### 一族因子建议

对 ORDER+ADD 分类（以事件发生时的 best quotes 为参照）：

1. `marketable_add_signed_amount_ema`（你 baseline 已有类似 marketable/passive，但可以更体系化）
2. `inside_spread_add_rate_imb`：bid 侧改善报价 vs ask 侧改善报价
3. `join_best_add_imb`：挂在 bid1/ask1 的净流
4. `away_add_wall_building`：在 3–10 ticks 的大额挂单净增

同时对撤单也分类：

- `cancel_best_imb`、`cancel_near_imb`、`cancel_far_imb`

### 为什么对 next20 有效

- next20 的方向性持续，往往来自“持续侵略性动作”（marketable/inside-spread）或来自“某侧近端撤离”（cancel_best）。
- 这些动作的“意图纯度”远高于混合净流。

------

# 因子簇 7：连续同向事件聚合（Metaorder / Run-length，你提到的重点）

### 核心逻辑

高频里最常见的“可持续”不是单笔信号，而是**执行流的持续性**（metaorder）：

- 一个买方执行会连续打 ask、或连续用 marketable add、或连续改善报价；
- 这种持续性在 20 个 entrust bar（~1000 tick）尺度上经常还没结束。
  所以把 tick 级别事件聚合成“同向簇”，能显著提升 SNR。

### 一族因子建议

对 trades、marketable adds、inside-spread adds 分别做 run 聚合：

1. **run 基本统计**

- `run_len`（连续同向事件数）
- `run_signed_amount`、`run_abs_amount`
- `run_duration`（秒/事件数）

1. **run 效率**

- `run_price_drift = mid_now - mid_run_start`
- `run_efficiency = run_price_drift / run_abs_amount`
- `run_slippage = VWAP_run - mid_run_start`（可选）

1. **run 仍在继续的概率 proxy**

- `time_since_last_same_side_event`
- `run_intensity = run_abs_amount / run_duration`

1. **run 转折信号**

- 同向 run 变弱：`intensity_fast - intensity_slow`
- 出现反向小 run（对冲/吸收）作为转折提示

### 为什么对 next20 有效

- 单笔 trade 的 impact 很短，但 metaorder 的执行会在更长窗口持续影响 mid。
- LGBM 很擅长用这些 run 特征做分段：小 run 可能噪声，大 run 更像信息/执行。

### 与 entrust bar 采样

run 状态是状态量（last）；run 内累计 amount 可作为 flow，在 bar 内自然累积。

------

# 因子簇 8：冲击穿透与“走档”特征（Walk-the-book / Penetration）

### 核心逻辑

真正的信息型/紧急型交易，往往表现为：

- 单笔成交吃穿多档（walk the book）
- 或者成交量占 best depth 的比例非常高（penetration）
  这种“侵略性强度”不仅影响下一跳，更经常延续到 next20。

### 一族因子建议

1. **走档深度**

- `levels_consumed`：成交价相对 best 穿透了几档（需要 trade_price 对照当时盘口价阶）
- `trade_through_flag`：是否越过 best

1. **穿透比例**

- `penetration = trade_amount / (amount_at_best + eps)`
- `penetration_X = trade_amount / (cumAmount_within_Xbps + eps)`

1. **穿透不对称**

- `EWM(penetration_buy) - EWM(penetration_sell)`

### 为什么对 next20 有效

- 走档/高穿透常对应“薄盘+急单”，会触发流动性撤退和更大级别的再定价，影响能跨过数百 tick。

------

# 因子簇 9：吸收 vs 毒性（Flow–Price Divergence / Absorption Residual）

### 核心逻辑

你们已有很多 flow imbalance，但缺“价格如何响应 flow”的二阶信息：

- **同样的买流**，如果价格动得很小，说明被动盘在吸收（可能预示反转，也可能预示“吸收完会突破”）；
- 如果价格动得超预期，说明交易更“毒”（informed），趋势更可能延续。
  这类“响应函数残差”在 next20 尺度往往更稳定。

### 一族因子建议

1. **flow 与 return 的偏离**

- `flow = net_liq_flow (add-cancel) + trade_flow`（可分权重）
- `pred_ret = beta_hat * flow`（beta_hat 在线估计：滚动回归或简单比率）
- `residual = ret_fast - pred_ret`

1. **吸收指数**

- `absorption = |flow| / (|ret| + eps)`
  高吸收：大流但价格不动。

1. **吸收方向性**

- `absorption_signed = flow - k*ret`（标准化后）

### 为什么对 next20 有效

- next20 的走势很多是“冲击→吸收→继续/回补”的中期过程。
- 仅看 flow 会把两类状态混在一起；加上响应残差就能分开。

------

# 因子簇 10：韧性/恢复速度（Resilience / Recovery）

### 核心逻辑

对 next20 来说，最关键的问题常常不是“发生了冲击没”，而是“冲击之后盘口恢复得快不快、恢复偏哪边”。

- 恢复慢的一侧往往成为价格漂移方向；
- 恢复快意味着冲击更可能被均值回归吞掉。

### 一族因子建议

定义 shock 事件（满足其一即可）：

- spread 扩大
- best price 被打穿（bid1/ask1 价格变化）
- 大额 trade/marketable add

然后统计：

1. **恢复时间**

- `time_to_spread_normal`
- `time_to_depth_restore`（ask1_vol 回到过去分位/均值）

1. **恢复强度**

- `replenish_speed = add_near_amount / time`
- `cancel_speed` 同理

1. **恢复不对称**

- ask 侧恢复慢于 bid 侧 → 上行更容易延续（反之亦然）

### 实现要点

- 在线实现可以用“状态机”：进入 shock 状态后累计直到恢复阈值；把最近 N 次恢复统计做 EMA。

------

# 因子簇 11：有效价差/有效冲击成本曲线（Cost Curve Features）

### 核心逻辑

spread 只是最表层交易成本；真正影响 next20 走势的是“成本曲线”：

- 同样 1 tick spread，若 L1 很薄、L2/L3 也薄，则一冲就走；
- 若 spread 不大但深度陡峭，趋势推进困难。
  把“执行 X 金额的 VWAP 成本”做成曲线，比 slope/convexity 更直观。

### 一族因子建议

对 X 金额执行，计算：

- `VWAP_buy(X)`：按 ask 档吃到 X 金额的加权均价
- `VWAP_sell(X)`：按 bid 档吃到 X 金额
  构造：
- `impact_cost_buy(X) = (VWAP_buy(X)-mid)/mid`（bps）
- `impact_cost_sell(X) = (mid-VWAP_sell(X))/mid`
- `cost_asym(X) = impact_cost_buy(X)-impact_cost_sell(X)`
- `curve_slope = cost(X2)-cost(X1)`（成本曲线陡峭度）

### 为什么对 next20 有效

- 这是“可推进性”的直接度量：当上行成本显著低于下行成本时，价格在未来一段事件窗口里更容易向上漂移。

------

# 因子簇 12：墙单/支撑阻力的“强度 + 持久性 + 侵蚀”

### 核心逻辑

可转债常见的结构性特征是“某价位挂大墙”。但墙的预测力来自三件事：

1. 墙有多大（强度）
2. 墙挂多久（持久性）
3. 墙是被吃掉还是自己撤掉（侵蚀机制）
   这三个结合起来，才是“深度变化”的核心。

### 一族因子建议

1. **墙强度**

- `max_cumAmount_in_[1..K ticks]`（bid/ask 各自）
- `wall_ratio = max_level_amount / total_near_amount`

1. **墙持久性**

- `wall_age`、`wall_survival_prob`

1. **侵蚀类型**

- `erosion_by_trade`（被吃）
- `erosion_by_cancel`（撤走）
- `erosion_mix = cancel_erosion / (cancel_erosion+trade_erosion)`

1. **墙破裂事件**

- `wall_break_flag`（大墙突然消失）
  常是 next20 的强信号：若 ask 墙破，向上更容易加速。

------

# 因子簇 13：盘口“熵/集中度谱”与高阶形状（Entropy / Gini / Spectrum）

### 核心逻辑

你们 baseline 里已有 `ask_conc_l1` 这类集中度，但还可以更系统：
盘口形状本质是一个分布（L1..L10 的 depth 分布）。
分布的“熵/集中度/不对称”能捕捉做市风格与风险状态变化，作为 next20 的门控非常有效。

### 一族因子建议

对 bid、ask 分别把 `p_i = vol_i / Σvol`：

1. **熵**

- `H = -Σ p_i log p_i`
- `H_bid - H_ask`

1. **Herfindahl / Gini**

- `HHI = Σ p_i^2`（越大越集中）
- `Gini(vol_i)`（越大越不均）

1. **谱分解（PCA）**

- 对规范化 depth 向量做 PCA，取 PC1/PC2（可离线学出投影矩阵，在线只做点积）

### 为什么对 next20 有效

- 这些不是直接方向信号，而是强门控：
  - 集中度高（单个墙）→ 突破/反转更“离散化”；
  - 分布均匀（高熵）→ 小冲击更容易被吸收，趋势延续更难。

------

# 因子簇 14：报价稳定性/闪烁（Quote Churn / Flicker）

### 核心逻辑

“深度变化”很多时候不是量变，而是报价不断撤退/补给造成的**闪烁**：

- best bid/ask 频繁变化、挂撤频繁 → 流动性不稳定，next20 的波动与跳价概率显著上升；
- 闪烁的不对称（只在 ask 侧闪）会带方向性：卖方撤退更快 → 上行更容易。

### 一族因子建议

1. `quote_churn_rate_bid/ask`：单位时间/单位事件内 best price 变动次数
2. `best_queue_turnover`：bid1/ask1 的新增+撤单量占其存量比例
3. `best_lifetime`：best 价位持续的平均时长
4. 不对称：`churn_bid - churn_ask`

### 为什么对 next20 有效

- next20 里很多“可预测收益”来自流动性事件后的一段漂移；churn 是这类事件的早期刻画。

------

# 因子簇 15：订单大小分层（Large vs Small, Informed vs Noise）

### 核心逻辑

同样的净流，若主要来自“大单”，信息含量通常更高；若主要来自碎单，可能是噪声/做市。
你们已经有“订单笔数不平衡”作为门控（Top 因子之一），
但还缺“**按 size 分层**”的方向信号。

### 一族因子建议

对 add/cancel/trade 的 size（volume 或 amount）做分桶（如按分位数）：

1. `add_imb_large`、`add_imb_small`
2. `cancel_imb_large`（大单撤走=墙撤退）
3. `trade_imb_large`（大额主动成交净流）
4. `large_minus_small = imb_large - imb_small`（信息-噪声差）

再加一个“结构”：

- `mean_order_size_bid - mean_order_size_ask`（近端/远端分别算）

### 为什么对 next20 有效

- 大单执行/撤退往往跨越更长事件窗口；对 next20 更稳定。

------

# 因子簇 16：被动成交（maker fill）与“逆向库存压力”代理（Inventory Pressure Proxies）

### 核心逻辑

当一侧不断被动成交（例如 buy aggressor 连续打 ask），卖方做市商库存越来越短。
经典微观结构里，库存压力会导致做市行为改变（补给变慢、报价上移/价差变化），从而影响 next20 的 drift。

### 一族因子建议

1. **被动成交量（按被打的一侧统计）**

- `passive_sell_fill = volume(trades at ask)`（被动卖出量）
- `passive_buy_fill = volume(trades at bid)`

1. **库存压力不对称**

- `inv_pressure = EMA(passive_sell_fill) - EMA(passive_buy_fill)`
  （也可归一化到总成交）

1. **库存压力 × 补给速度**

- `inv_pressure * replenish_speed_ask`
  库存压力大但补给快 → 吸收/均值回归
  库存压力大且补给慢 → 趋势延续更强

### 为什么对 next20 有效

- 这类效应不是“一跳”结束，而是做市行为在一段窗口内逐步调整，天然适配 next20。

------

# 因子簇 17：有效价差、已实现价差与“逆向选择强度”（Adverse Selection / Toxicity）

### 核心逻辑

你们已有 trade impact 的 EMA 版本等，
但还可以更结构化地做“逆向选择”：

- **Effective spread**：交易发生时相对 mid 的偏离
- **Realized spread / price impact**：过一小段后 mid 往哪边走
  两者差就是“毒性”：毒性高说明对手盘信息强，趋势更可能延续。

### 一族因子建议

对每笔 trade，在其发生时记录 `mid_0`，过 `Δ`（例如 50~200 tick 或固定秒）后取 `mid_Δ`：

- `effective = 2*sign*(trade_px - mid_0)`
- `impact = sign*(mid_Δ - mid_0)`
- `adverse = impact` 或 `effective - realized`（视定义）

在线更新：

- `EMA(adverse_buy)`、`EMA(adverse_sell)`、它们的差与比值。

### 为什么对 next20 有效

- 毒性本质刻画“信息交易强度”，其状态往往持续一段时间，并决定 next20 内 trend vs mean-revert 的概率。

> 注意：这类因子需要用“过去发生的 trade 的延迟结果”更新，不会引入未来信息（只要你更新时只用已经到达的 mid）。

------

# 因子簇 18：更好的 micro price / efficient price 体系（替代 mid 的“目标价”）

### 核心逻辑

你们 baseline 里已有 L1 microprice gap、micro_edge（micro-mid 扣除 spread）等。
但 L1 microprice 有两个常见问题：

- 在薄盘/闪烁时噪声很大；
- 只用 L1 容易被“假量/瞬时补给”骗。
  所以建议升级一套“微价族谱”，把它做成一个因子簇，而不是单点。

### 一族因子建议

1. **多档 microprice**

- `micro_L1`（现有）
- `micro_L3`：用 L1-L3 的 depth 加权（可设计概率权重：越近权重越大）
- `micro_L10`：更稳、但慢

1. **队列调整 microprice**
   把队列耗尽时间纳入权重：

- 若 ask 侧 `T_deplete_ask` 很短（容易上穿），则 microprice 向 ask 偏移更大。

1. **efficient price（简化卡尔曼/滤波）**

- 状态：`p*`
- 观测：mid、trade price
- 用简单一阶滤波：`p*_t = p*_{t-1} + k1*(mid - p*) + k2*sign_trade`
  你不需要做学术级卡尔曼，核心是得到一个比 mid 更平滑、又比慢均线更快的“效率价”。

1. **微价导出的二阶特征**

- `micro_gap = (micro - mid)/mid`
- `micro_mom = EMA(Δmicro)`
- `micro_cross_flag`：micro-mid 符号翻转（状态切换触发器）
- `micro_vs_vwapmid`：微价与盘口重心的差

### 为什么对 next20 有效

- next20 不是 1~2 tick 的 horizon，但 micro/efficient price 提供的是“短端方向倾向”，在强净流/薄盘状态下往往能延续到更长窗口；更关键的是它能作为门控，让其它信号更可用。

------

# 因子簇 19：活动度自适应时间尺度（Adaptive EMA / Time-normalized Features）

### 核心逻辑

你们的 bar 是按 entrust amount，同一根 bar 内 tick 数波动很大；固定 α 的 EMA 在不同活动度下对应的“真实时间跨度”会变化。
解决思路是让平滑参数随 dt 或 event_rate 自适应，或者直接把特征做成“每单位时间/每单位金额”的形式。

### 一族因子建议

1. **按真实时间半衰期的 EMA**

- `alpha = 1 - exp(-dt/τ)`
  τ 用秒，保证在稀疏与密集行情下意义一致。

1. **强度归一**

- `flow_per_sec = flow / dt`
- `flow_per_event = flow / event_count`
- `flow_per_entrust_amount = flow / entrust_amount_progress`

1. **burstiness**

- `cv_dt = std(dt)/mean(dt)`（事件间隔的离散度）
- `burst = event_rate_fast - event_rate_slow`（你们已有类似，但可按 event type 拆分，见簇 20）

### 为什么对 next20 有效

- next20 的“有效时间长度”随活跃度变化；自适应时间尺度能显著减少 regime shift 带来的漂移。

------

# 因子簇 20：事件类型强度拆分与“市场主导权”（Add vs Cancel vs Trade dominance）

### 核心逻辑

你们已有 order_prob、trade_over_order_prob 等状态量。
但更深一层是把市场拆成三种主导状态：

- **新增主导**（补给/堆墙）
- **撤单主导**（流动性撤退）
- **成交主导**（出清/信息落地）
  同一条方向信号在不同主导状态下含义不同。

### 一族因子建议

1. `rate_add`, `rate_cancel`, `rate_trade`（分类型 event_rate）
2. `cancel_over_add = rate_cancel / (rate_add+eps)`
3. `trade_over_bookchange = trade_amount / (sum|Δdepth|+eps)`
4. `dominance_state`：soft 分类（例如三者占比向量）或一维投影

### 为什么对 next20 有效

- next20 的方向性更容易在“成交主导 + 净流一致”的状态出现；撤单主导则更像流动性事件，可能引发更大漂移但也更噪声。

------

# 因子簇 21：盘口稀疏度/空档的多尺度扩展（Gap/Sparsity 2.0）

### 核心逻辑

你们已有 L2 gap 及 gap_imb 等。
但“深度变化”常体现为：某侧从“连续报价”突然变成“断层”，这往往比单一 L2 gap 更关键。

### 一族因子建议

1. **多档 gap**

- `gap_12, gap_23, gap_35, ...`（bid/ask）
- `max_gap_within_L10`
- `sum_gap_within_L10`

1. **缺失档位计数**

- `missing_levels = count(vol_i==0)`（或 amount 很小视为缺失）

1. **稀疏度动态**

- `sparsity - EMA(sparsity)`
- `gap_burst = max_gap_fast - max_gap_slow`

1. **稀疏度不对称**

- bid vs ask 的差/比值

### 为什么对 next20 有效

- 稀疏度事件会改变冲击传播方式：更跳跃、更容易被推进，且影响持续一段窗口。

------

# 因子簇 22：动量/回归的“结构化版本”（用结构解释而不是纯 ret EMA）

### 核心逻辑

你们已有 fast/slow mom 与 mr（取负）以及 dev_diff 等。
升级方向不是再来一个 ret EMA，而是把动量/回归变成“有条件的机制”：

- 过冲是否会回归，取决于吸收/韧性/稀疏度/墙；
- 趋势是否延续，取决于净流持续性/侵略性/成本曲线。

### 一族因子建议（把结构变量显式做成“条件动量”）

1. `trend_confirm = sign(flow) * sign(micro_gap)` 一致性
2. `mom_under_thin = mom * 1[eff_spread_X 高 或 depth_log 低]`
3. `mr_under_absorption = mr * 1[absorption 高]`
4. `mom_x_resilience = mom * (1/recovery_time)`

> 你可以不直接乘指示函数，改成连续门控（例如乘以标准化后的薄盘指标）。LGBM 也能学，但显式构造能提升可解释性与样本效率。

------

# 因子簇 23：把“bar 内结构”直接做成因子（entrust bar 对齐的在线累积）

### 核心逻辑

你们预测目标是 entrust_1m bar，未来 20 根 bar 的 return。
现在采样时对 state 取 last、对 amount/volume 取 bar sum。这个没问题，但**很多“过程量”更适合在 bar 内就维护累计**（而不是事后再 sum），理由：

- 你可以得到“bar 进行到一半时”的即时状态；
- 采样时取 last 就自然是 bar 内累计；
- 更利于线上一致性（尤其对一些比值特征：分子分母都在 bar 内累计，最后再取 ratio）。

### 一族因子建议

每根 entrust bar 重置累计器，tick 内不断更新：

1. `bar_add_signed_amount`, `bar_cancel_signed_amount`, `bar_trade_signed_amount`
2. `bar_net_liq = add - cancel`
3. `bar_run_stats`：bar 内最大同向 run、bar 内前半段 vs 后半段净流差
4. `bar_path`：bar 内 mid 的 max-min、microprice 的 max-min、末端偏离

### 为什么对 next20 有效

- 标签是 bar-count，bar 内结构统计往往和后续 bar 的漂移更对齐，减少“事件密度差异”引入的尺度噪声。

------

# 因子簇 24：改进你们现有聚合口径的“关键升级点”（非常建议马上做）

你们 baseline 里明确提到这次 `sum_cols=[]`，很多事件量最后是 last_valid。
这会让不少“原始 turnover/vol 类”因子更像“最后一笔冲击”，有时反而有效，但也会带来不稳定与偶然性。建议你们把聚合升级做成系统化对照实验：

### 24.1 为每类因子输出“last / sum / mean / max / last-minus-mean”族

- 对于**事件冲击型**（单笔意义强）：保留 last
- 对于**强度累计型**（持续性强）：sum/mean 往往更稳
- 对于**极值触发型**（墙破/稀疏度）：max/min 很关键

### 24.2 对“比值类”避免直接 sum 后再 ratio

正确做法通常是：

- tick 维护分子累计 `N` 与分母累计 `D`（或 EMA）
- 采样时输出 `N_last`, `D_last`, 以及 `N_last/(D_last+eps)`
  这样避免 bar 内比例的非线性偏差。

### 24.3 “状态量 last”也可以输出 bar 内波动

例如 spread、micro_gap、depth_imb：

- `bar_std(spread)`、`bar_max(spread)` 作为“流动性事件强度”
  对 next20 很常见地是门控变量。

------

# 因子簇 25：一组“立刻能补齐 baseline 空白”的清单（偏经典但高性价比）

最后给一个更工程化的补齐清单（很多是经典、但你们 Top80 里并没有成体系出现）：

1. **imbalance 的变化率**：`imb - EMA(imb)`、`imb_fast - imb_slow`（对 depth_imb、wimb 都做）
2. **add/cancel/trade 三者的一致性指标**：`sign(add_imb) == sign(trade_imb)` 的强度
3. **price improvement rate**：inside-spread add 的强度与不对称（比纯 add_imb 更“信息”）
4. **order-to-trade conversion**：新增后实际成交的“转化率 proxy”（用净深度变化与成交去近似）
5. **depth shock 标记**：`|Δdepth|` 的 burst（结构突变触发器）

------

## 建议的落地优先级（如果你要“先做最可能提升”的 6 个簇）

在你们现在已有的基础上，我会优先做这 6 簇（因为它们最能体现“深度逻辑”，且对 next20 最匹配）：

1. **簇 4 固定金额/固定 volume 的流动性尺度**（直接对齐 entrust bar 的金额尺度）
2. **簇 1 生命周期/撤单 hazard**（把“虚假深度”显式化）
3. **簇 5 距离桶迁移**（把深度变化从“量”变成“迁移过程”）
4. **簇 9 吸收 vs 毒性残差**（把 flow 信号“去歧义”）
5. **簇 10 韧性/恢复速度**（next20 的持续性核心来源之一）
6. **簇 7 run/metaorder 聚合**（把单笔噪声升维成持续执行）

------

## 最后：你提到的几个问题，我的明确回答

- **委托单生命周期能不能写因子？**
  能，而且我认为这是你们从“浅”到“深”的关键跃迁之一（簇 1、簇 2、簇 12、簇 14 都围绕生命周期展开）。
- **imbalance 用固定 volume/amount 而不是固定档位，会不会更好？**
  很可能更好，尤其你们的 bar 是按金额定义的，这种尺度一致性通常能显著提升稳定性与可解释性（簇 4、簇 11）。
- **按订单簿位置/订单大小分类能不能写更多样因子？**
  绝对可以，而且建议你把“位置（距离桶）×大小分层 × 事件类型（add/cancel/marketable/inside-spread）”做成一个系统的特征生成器（簇 5、簇 6、簇 15）。
- **要不要用更好的 micro price 替代 mid？**
  建议做“微价族谱”（簇 18）：L1/L3/L10 微价 + 队列调整 + efficient price；然后所有 dev/mom/edge 都围绕这套价体系输出一族特征，让模型自己选。
- **连续同方向单聚合后再写因子会不会更好？**
  在你们这个 horizon 上非常值得（簇 7、簇 8、簇 9、簇 10）。单笔噪声太大，run/metaorder 聚合能显著提升持续性解释力。

------

如果你希望我再进一步“对照你们 Top80 已有因子，逐条标注：哪些簇已经覆盖、哪些簇完全空白、以及每簇建议新增的最小 MVP 集合（比如每簇先做 6~12 个）”，我也可以按你们的命名规范（Agent1/2/3 风格）把每个簇拆成可直接交给研究员实现的任务列表。



User:

我读了你的报告，做出了一些评价和提问。请你结合我的问题，仔细思考。我这些问题或评论可能有些是对的，有些是错的，你需要严谨思考，不能被我带偏，也不能不思考就否决。

完成思考和迭代后，请你做一版文档，写出每一个因子簇聚体包含哪些因子、逻辑是什么、建议等（也就是目前有的东西不能少），请遵从以下原则：

- 如果一个因子簇方案A和方案B都可能work，你一时间得不到确信的答案，那么最好的办法可能是两者都试一下，而不是把某些想法扼杀。当然，如果经过逻辑推理，确信某种方式更好，你也应该直接提出
- 对于一些量的明确定义（比如什么是小单大单？），如果你需要用数据做研究后才能决定，请你也同时写出决定其参数的可能思路、有哪些要做的可能的统计试验。请你注意，在这里我们为了避免过拟合，一般不采用非常复杂的方法（比如fit）
- 对于一些逻辑类似，或者交叉可以合并的因子簇，可以合并起来一起介绍、一起写



Comment 

因子簇1:

- "Near Ask" / "Near Bid" ，可以设置成amount截断，比如最优的多少CNY的买单的平均age，这样可能比附近多少个ticker的单更公平？

因子簇2:

- 是不是扩充到更深的几档，甚至可以20、50档？
- 多少档“具体有多深”是不是也需要考虑？稠密和稀疏的订单簿也会带来不同的结果

因子簇3:

- PCA太复杂了，后面还要进模型fit，容易过拟合，应该去掉

因子簇5:

- 是不是也可以有更激进的“Cross Spread”的单？并且这些单也应该被分类：打在对手价1和打在很远的地方的激进度是不一样的
- 不同bps分桶是不是也可以呢

因子簇6:

- 我觉得也可以用amout截断来判断一个单是否是“激进挂单”。比如如果ask1实际上有非常大的单堆积，那么即使新单挂在ask1，其实也要排队排很久才能排到，这种情况下他实际上挂单挂的并不激进。而有的时候ask1单量非常少，而第二档挂单就已经离盘口很远了。这时候，虽然新单挂在离盘口很远的地方，但实际上很快就能排队到他。这种情况下，可以认为他其实是“激进”的单
- 对于marketable的单也一样也是可以细分激进度的。但我觉得这边的激进度和passive的单不一样，应该用距离盘口的距离来判断，而不是“amount”来判断

因子簇7:

- 这边我觉得如何“聚合”这些单的算法会比较重要。比如是不是同一时间（或相差1ms以内）、同一方向的连续成交应该被聚集为一个trade，然后再基于这个聚合好的trade来写一些因子？

因子簇8:

- 走档深度怎么写成因子？目前我们的因子都是逐tick更新的，而每个tick有可能是成交事件，也有可能是委托事件。是不是只在成交的时候更新、然后order事件时填充上一个值？那么每个bar内又该怎么做聚合或者统计、使其能被entrust bar使用呢？

因子簇9:

- 尽量不要用回归，可以想想有没有什么简单点的估计方法，防止overfitting（并且回归还有多个品种的问题）

因子簇 10：

- 这样的因子是不是覆盖率很低？如何解决这个问题？

因子簇 11：

- 这里mid会不会用两边的固定amount的vwap算出来的价格更靠谱呢？

因子簇 12：

- 这些中间数据很有意思，但怎么用他们写成因子可能需要进一步考虑

因子簇 13：

- 依然是尽量不要用这种fit的方式，因为之后还要过lgbm

因子簇 15:

- 怎么定义大小单呢？是不是要做一些怎么样的研究再确定？

因子簇 17:

- 是不是也可以用加权的micro price来代替mid？会更好吗？

因子簇 18:

- 我希望这里可以多做些研究，但不要特别复杂（比如不要弄到fit之类的），之后我可能也会直接用不一样的micro price去做return

因子簇 19:

- 具体哪些因子适合做这样的改变呢

因子簇 23：

- 我暂时不想这样更新，因为bar的切分方式还可以改进，目前只是暂定是这种切分，后面可能会改。后面我会单独开课题来研究这个

因子簇 24：

- 目前我们要求研究员写因子的同时写一份json文件，说明该因子是state还是amount，来决定后续怎么聚合。你说的max、ratio等如果已知能带来增量，那么应该在写因子的时候就明确写出来。

因子簇 25：

- 请详细一点补全



其他的一些补充：

- 目前我们维护的重构数据不仅在snap字段放了10档买卖盘口，也维护了full_ask、full_bid的完全订单簿的两个字段。一些深层次的订单或墙等也能获得到数据
- 比如L2比L1可能价格大的并不是1个最小变动单位，订单簿可能存在比较稀疏的情况



Agent:

下面这份是**v2 文档版**：我把你逐条 comment 都吸收进来，同时也刻意做了“反向检验”——哪些点我同意、哪些点我认为需要 A/B 都试、哪些点我认为逻辑上更应该偏向某一边，我都会在对应因子簇里写清楚，并给出**参数怎么定、怎么做简单统计试验**（尽量不引入 fit / 回归 / PCA 这类你明确担心过拟合的东西）。

> 背景对齐（重要）：你们是**tick 级产因子**，但按 `entrust_1m` bar 采样预测 `next20 bar` 的 return；采样时目前做法是 **state 取 last，amount/volume 取 bar 内 sum**。baseline Top80 的报告里也提示了当前 `sum_cols=[]`（默认 last_valid）会改变很多“量类因子”的经济含义：它们更像“bar 末端冲击/状态”而不是整根 bar 累计。
> 同时你补充说你们还有 `full_bid/full_ask` 的全量订单簿，并且盘口可能稀疏（L2-L1 不一定 1 tick）。这些会显著影响“距离”的定义与“深度”的构造方式。

------

# HFTPool 可转债逐笔因子簇建议 v2（面向 next20 entrust-bar）

## 0. 总体原则（你提的三条我都贯彻）

1. **A、B 都可能 work 时：两条都做，做消融（ablation）**
   - 但要把实验空间控制在“少量可解释参数”上，避免无限膨胀。
2. **参数需要数据才能定：给出“如何定”的研究路径**
   - 以“分位数/倍数/网格扫小集合 + 稳健性检查”为主，不做复杂拟合。
3. **相近逻辑簇合并**
   - 我把原先 25 个簇做了“保留全部内容 + 更合理归并”。你原来提到的簇号，我会在小标题里标注“来源簇”。

------

## 1. 参考价格体系因子簇（覆盖：原簇 18、11、17 的核心问题）

> **你问的关键点**：
>
> - 簇11：mid 会不会用“两边固定 amount 的 VWAP”更靠谱？
> - 簇17：effective/realized spread 用加权 micro price 替代 mid 会更好吗？
> - 簇18：希望多研究，但不要复杂/fit，并且可能直接用不同 micro price 去做 return。

### 1.1 核心逻辑（为什么对 next20 有效）

在你们这种“事件尺度 next20（~1000 tick）”里，mid 有两个常见问题：

- **薄盘 + 稀疏价阶**时，mid 的跳动会“被动放大”，导致很多响应类因子噪声变大；
- **深度不对称**时，mid 不一定是“更有效的均衡价”，micro/efficient 价更能代表“短中期漂移中心”。

所以建议把“参考价”升级为一个**小族谱**：同一套因子可以对不同参考价做版本，最终让 LGBM 选择。

### 1.2 建议实现的一组参考价（不需要 fit）

定义若干 `p_ref`（每 tick 都能更新）：

**A. 传统：mid**

- `p_mid = (bid1 + ask1)/2`

**B. 固定 amount 的 VWAP-mid（你提的）**

- 选定阈值 `X`（如 10w/30w/100w CNY，或按标的自适应，见 1.4）
- 计算：
  - `vwap_ask(X)`：吃 ask 侧累计到 `X` 金额的 VWAP
  - `vwap_bid(X)`：吃 bid 侧累计到 `X` 金额的 VWAP
- 定义：
  - `p_vwapmid(X) = (vwap_ask(X) + vwap_bid(X))/2`
  - 这在有 `full_book` 时非常自然，而且对稀疏价阶更稳健。

**C. 多档深度加权 microprice（不止 L1）**

- `p_micro_Lk = (ask1 * W_bid(k) + bid1 * W_ask(k)) / (W_bid(k)+W_ask(k))`
  - 其中 `W_bid(k)=Σ_{i=1..k} w_i * bidVol_i`，`W_ask(k)=Σ_{i=1..k} w_i * askVol_i`
  - `w_i` 用固定衰减（指数/1/i）即可，避免 PCA。

**D. 队列/耗尽时间调整 microprice（不 fit）**

- 结合“预计耗尽时间”（见簇 3），用 `1/T_deplete` 作为权重增强方向性偏移。

> 你说“之后可能直接用不同 micro price 去做 return”：完全可行。建议做两套标签做对照（mid-return vs vwapmid(X)-return vs micro_Lk-return），看哪个在 next20 上更稳定（不是为了优化标签，而是为了减少测量噪声）。

### 1.3 基于 p_ref 派生的统一特征接口（建议）

所有“bps 类距离/价差/冲击”都提供一个统一接口：

- `spread_ref = ask1 - bid1`（仍然用 L1）
- `dev_ref = (p_ref / EMA(p_ref) - 1) * 1e4`
- `edge_ref = (micro_ref - p_ref) - spread_ref`（如果 micro_ref 不等于 p_ref）

这样你们后面所有“冲击/响应/偏离”因子，可以用 `p_ref ∈ {mid, vwapmid(X), micro_L3,...}` 生成少量版本，不用引入任何拟合。

### 1.4 参数怎么定（不 fit）

- `X`（固定 amount 阈值）建议只选 3–5 个：例如 `{5w, 10w, 30w, 100w}` 或按标的“盘口可用性”自适应：
  - 统计 `cumAmount_within_10bps` 的分布，取其 {20%, 50%, 80%} 分位作为 X 候选（分位是统计，不是拟合）。
- `k`（micro 的档位深度）也只选 2–3 个：`k∈{1,3,10}` 或 `{3,10,50(用 full_book)}`。

------

## 2. 固定金额/固定风险尺度的流动性几何因子簇（覆盖：原簇 4、11、21 + 你提的稀疏性问题）

> **你关心**：
>
> - “Near/距离”用 amount 截断更公平（簇1/簇4/簇6都相关）
> - 订单簿稀疏：L2-L1 不一定 1 tick → 距离应该用 bps/真实价差
> - 深度要不要 20/50 档甚至 full book（簇2相关）

### 2.1 核心逻辑

你们的 bar 本身是按 “entrust amount” 构造的，所以用“固定 amount 的流动性结构”会更同尺度、更稳健。它对 next20 有效的原因是：**next20 内价格能漂多少，很大程度由“执行 X 金额的成本曲线”决定**，这比固定 L10 depth 更直接。

### 2.2 因子集合（建议最小可用集）

下面所有特征都建议以 `p_ref`（簇1）为基准输出 bps，增强跨标的一致性。

#### 2.2.1 Depth-to-X：达到 X 金额所需的价格距离

对每个阈值 `X`：

- `dAsk(X) = (p_at_cumAskAmount=X - p_ref)/p_ref * 1e4`
- `dBid(X) = (p_ref - p_at_cumBidAmount=X)/p_ref * 1e4`
  派生：
- `eff_spread_X = dAsk(X) + dBid(X)`
- `cost_asym_X = dAsk(X) - dBid(X)`
- `log_cost_ratio_X = log((dAsk(X)+ε)/(dBid(X)+ε))`
- `coverage_X = 1[full_book 累计到 X 可达]`（不可达时用截断值+coverage 作为信息）

> 你有 full_book：这组可以做到非常干净，而且能自然处理“稀疏价阶”。

#### 2.2.2 成本曲线斜率/曲率（不需要拟合）

对 `X1<X2<X3`：

- `curve_slope_12 = cost(X2) - cost(X1)`
- `curve_slope_23 = cost(X3) - cost(X2)`
- `curve_convex = (cost(X3)-cost(X2)) - (cost(X2)-cost(X1))`
  分别对 buy/sell 两侧与不对称版输出。

#### 2.2.3 固定 bps 半径内的可交易量（反过来）

对 `R`（如 5/10/20 bps）：

- `cumAskAmount(R)`: 价格 ≤ `p_ref*(1+R/1e4)` 的 ask 金额
- `cumBidAmount(R)` 同理
  派生：
- `imb_R = (cumBidAmount(R)-cumAskAmount(R))/(sum+ε)`
- `thin_flag_R = 1[cumAskAmount(R) 很小]` 等

> 这组回答了你说的“具体有多深要考虑”：不是用档数，而是用“在某个可交易价差半径内到底有多少量”。

#### 2.2.4 稀疏度/空档结构（支持“L2-L1 不等于 1 tick”）

基于 full_book 或 L10：

- `max_gap_bps_within_R`：在 `±R bps` 内相邻价位的最大 gap（bps）
- `gap_count_within_R`：gap 超过阈值（如 >2tick 或 >x bps）的次数
- `missing_levels_proxy`：在 `±R` 内价位数 vs 理论最大价位数（用 tick size 推断）
  不对称版本：ask/bid 分别算，再做差。

### 2.3 参数怎么定（不 fit）

- `X`（固定金额阈值）选择方法见 1.4；建议再加一个“相对深度归一”版本：
  - `X = q * cumAmount_within_10bps_median`，q 取 `{0.5, 1, 2}`
- `R`（bps 半径）建议只取 `{5,10,20}` 或 `{(1tick bps), 10, 20}`，避免过多。

------

## 3. 队列与“激进度”因子簇（覆盖：原簇 2、6 + 你对 amount 截断激进度的关键评论）

> 你最关键的两个观点：
>
> 1. passive 的“激进挂单”不能只看价格档位，要看**前方队列 amount**（amount 截断/排队时间）
> 2. marketable 的激进度要看**穿透距离/吃了多深**（距离盘口的距离），而不是 amount

我认为这两点都很对，并且建议你们把“激进度”做成统一指标体系。

### 3.1 核心逻辑

next20 内价格是否继续漂移，很大程度取决于：

- 一侧队列是否会被耗尽（deplete）
- 新单是在“抢先成交（高激进）”还是“排很久（低激进）”
  这比简单的“挂在 L1/L2”更机制化。

### 3.2 因子集合

#### 3.2.1 预计耗尽时间（Expected Time-to-Deplete）

对 L1 以及可扩展到更深：

- `T_deplete_ask1 = Q_ask1 / (buy_hit_rate + ε)`
- `T_deplete_bid1 = Q_bid1 / (sell_hit_rate + ε)`
  扩展版（你提到 20/50 档甚至 full）：
- 用 fixed amount 阈值替代“几档”：
  - `Q_ask_near(X)`：从 ask1 开始累计到 X 金额的队列量
  - `T_deplete_ask(X)=Q_ask_near(X)/(buy_hit_rate+ε)`
    同理 bid。

派生：

- `inv_Tdiff = 1/T_deplete_ask - 1/T_deplete_bid`
- `log_T_ratio = log((T_bid+ε)/(T_ask+ε))`
- `T_surprise = T_fast - T_slow`（两尺度 EMA，不依赖 fit）

> **你问“扩到 20/50 档？”**
> 我建议优先做“fixed amount 的队列深度”，比固定档数更稳健；同时也可以做固定档数作为对照（A/B），但用 full_book 时更建议 fixed amount。

#### 3.2.2 Passive 单的“排队激进度”（你提出的 amount 截断版本）

对每一个新增被动单（ORDER+ADD 且价格不跨 spread）定义：

- `ahead_amount =` 该价格档位上**在它之前**的排队量（若无 order_id 只能近似为该价位现存量）
- `ahead_amount_cum =` 从 best 到该价位（含该价位）累计的 ask/bid amount（full_book 很适合）
- 定义激进度指标（建议两种都试）：

**A. amount 归一激进度**

- `passive_aggr_A = 1 / (ahead_amount_cum + ε)`（越小越不激进）
- 或 `-log1p(ahead_amount_cum)`（稳定压缩）

**B. time-to-fill proxy**

- `passive_aggr_T = (buy_hit_rate)/(ahead_amount_cum+ε)`（对 ask 侧挂单；bid 类似）

然后做统计聚合（tick 级持续更新）：

- `EMA(passive_aggr_T)`（按 side 分别）
- `imb_passive_aggr = EMA(bid_side) - EMA(ask_side)`
- `passive_aggr_burst = fast - slow`

#### 3.2.3 Marketable 单的“穿透激进度”（你说要用距离盘口）

对 marketable 行为（包括 cross-spread add 与成交，见簇5/簇6）：

- `penetration_levels`：吃穿了几档
- `penetration_bps = (trade_price - best_price)/p_ref*1e4`（按方向取正）
- `penetration_cost_X`：吃到 X 金额后的 VWAP 相对 p_ref 的成本（与簇2联动）

聚合：

- `EMA(penetration_bps_buy)`、`EMA(penetration_bps_sell)`
- `penetration_imb = buy - sell`
- `penetration_tail = p90(penetration_bps)`（用 EMA of clipped 值近似，不需要真正分位）

### 3.3 参数怎么定（不 fit）

- `buy_hit_rate/sell_hit_rate`：用最近窗口成交量（EMA）即可；窗口用“事件时间半衰”与“真实时间半衰”两套都做（见簇10）。
- `X`：同簇2的金额阈值体系，尽量共用，减少参数维度。

------

## 4. 订单生命周期与“存活质量”因子簇（覆盖：原簇 1 + 你的 amount 截断 near 定义）

> 你提的点：Near Ask/Bid 用 amount 截断比“多少 tick”更公平？
> 我认为**非常值得作为主版本**，但也建议保留 tick/bps 版本做对照，因为：

- amount 截断在极端薄盘时可能“覆盖到很远的价位”，混入远端意图；
- bps 截断在不同流动性标的间更稳健。

因此建议三种 near 定义并行（A/B/C），模型/消融会告诉你谁更稳。

### 4.1 核心逻辑

“深度变化”很大一部分来自撤单与订单寿命结构：

- 年轻深度更“虚”、撤单风险高；
- 老深度更“实”、更像支撑阻力；
  这对 next20 有效，是因为撤单/补给的行为往往持续一段时间，不是 1–2 tick 的超短信号。

### 4.2 near 的三种定义（建议并行）

- **A. fixed amount near**：从 best 向外累计到 `X` 金额的订单集合（你提的）
- **B. fixed bps near**：距离 `p_ref` 在 `±R bps` 内
- **C. fixed levels near**：L1–Lk（作为 baseline 对照）

### 4.3 因子集合

#### 4.3.1 年龄结构（age moments）

对 bid/ask 分别在 near 区域统计（按 volume/amount 加权）：

- `age_mean_near_side`
- `age_p90_near_side`（无须精确分位，可用“分桶计数”近似：例如 age<1s,1–5s,>5s 三桶）
- `young_ratio = amount(age<T)/amount_total`
- `old_ratio = amount(age>T)/amount_total`
  再做不对称：
- `age_imb = age_mean_bid - age_mean_ask`
- `young_imb = young_ratio_bid - young_ratio_ask`

#### 4.3.2 撤单 hazard（撤单速率 / 存活率）

- `cancel_rate = cancel_amount_near / live_amount_near`
- `survival_ratio(T) = live_amount_age>T / live_amount_near`
- `cancel_acc = cancel_rate_fast - cancel_rate_slow`

#### 4.3.3 “墙”的寿命（与簇8联动）

识别 near 中的大额价位（见簇8墙单定义），跟踪：

- `wall_age`
- `wall_decay_by_cancel` vs `wall_decay_by_trade`

### 4.4 参数怎么定（不 fit）

- `T`（年轻/年老阈值）：不用拟合，做 3 档：`{0.5s, 2s, 10s}` 或 `{50tick,200tick,1000tick}`
- 对每个 T，看：
  - coverage（是否所有标的都能算）
  - 与 next20 的分位收益单调性（简单分箱，不需要回归）

------

## 5. 订单簿结果层 OFI 因子簇（覆盖：原簇 3 + 你对 PCA 的担忧）

> 你说 PCA 太复杂、还要进模型 fit，容易过拟合。
> 我同意你在工程纪律上的担忧：**这里完全可以不用 PCA**。PCA 的“降维收益”在有 LGBM 的情况下通常不是必须，而且确实会引入“先验变换”的管理成本。

### 5.1 核心逻辑

“用 Δdepth 定义 OFI”最大的优势是：把 add/cancel/trade 统一到结果层，减少事件分类噪声。对 next20 有效是因为它是供需净变化的直接度量，且具有跨事件持续性。

### 5.2 因子集合（无 PCA 版本）

对每档 i（可以 L1–L10，也可扩到更深，但建议先做 L1–L20 或用 bps/amount 截断）：

- `ΔBid_i = BidAmt_i(t) - BidAmt_i(t-1)`
- `ΔAsk_i = AskAmt_i(t) - AskAmt_i(t-1)`
- `OFI_i = ΔBid_i - ΔAsk_i`（必要时做“价格跳变对齐”，即 best 变化时按新档位重映射）

然后做几种**确定性汇总**（替代 PCA）：

**A. 近端/远端分段汇总**

- `OFI_near = Σ_{i∈near} OFI_i`
- `OFI_far = Σ_{i∈far} OFI_i`
- `OFI_migration = OFI_near - OFI_far`

**B. 指数加权（固定权重，无 fit）**

- `OFI_exp = Σ exp(-λ·i) · OFI_i`，λ 取 `{0.3,0.6}` 两个即可

**C. “形状”统计（不回归的等价公式）**

- `OFI_slope_proxy = Σ i·OFI_i / (Σ |OFI_i| + ε)`
  （它不是回归，是一个“重心”型指标，表达 OFI 更集中在近端还是远端）

**D. surprise/多尺度**

- `OFI_fast = EMA_fast(OFI_exp)`
- `OFI_slow = EMA_slow(OFI_exp)`
- `OFI_acc = OFI_fast - OFI_slow`

------

## 6. 距离分桶迁移 + Cross-Spread 激进行为因子簇（覆盖：原簇 5 + 你关于 cross-spread & bps 分桶）

### 6.1 核心逻辑

同样是 add/cancel/trade，发生在不同距离含义完全不同；而 cross-spread（直接打到对手）是最强的“执行/信息”行为之一。对 next20 有效是因为它同时影响：

- 立即冲击（impact）
- 后续补给/撤退（resilience）
- 队列结构（queue）

### 6.2 距离分桶（建议用 bps 为主，兼容稀疏）

桶定义（举例）：

- bps 桶：`[0,1] [1,3] [3,5] [5,10] [10,20] [20,50]`（可少一点）
- 或 amount 桶：到 `X1/X2/X3` 金额为止（与簇2共用）

### 6.3 事件分类（你提到的激进度差异）

把订单行为分成：

1. **Inside-spread improvement**：挂到 spread 内、改善报价
2. **Join best**：挂在 best（但是否“激进”由 ahead_amount 决定，见簇3）
3. **Away**：挂在远端（但也可能“其实很快轮到”，同样用 ahead_amount/耗尽时间判断，见簇3）
4. **Cross-spread / Marketable add**：价格跨过对手 best，立即成交（或部分成交）
5. **Trade**：成交事件（可按是否 walk-the-book 细分，见簇7）

### 6.4 因子集合

对每个距离桶、每个 side，维护（EMA 或滚动窗口）：

- `add_amount(bucket, side)`
- `cancel_amount(bucket, side)`
- `net_liq(bucket, side)=add-cancel`
- `trade_hit_amount(bucket, side)`（如果能映射成交穿透到桶）

派生：

- `net_liq_imb(bucket) = (net_bid - net_ask)/(abs+ε)`
- `migration_index = net_liq_near - net_liq_far`
- `cross_spread_intensity = EMA(marketabl_add_amount)`（买/卖分开）
- **cross-spread 激进度分层（你说“打在对手价1 vs 打很远”）**
  - `cross_depth_bps = penetration_bps`（见簇3.2.3）
  - `cross_depth_levels = penetration_levels`
  - 分桶统计：`cross_far_ratio = amount(penetration_bps>R)/total_cross_amount`

------

## 7. 交易聚合 + Metaorder/Run 因子簇（覆盖：原簇 7 + 你关于 1ms 聚合的评论）

> 你说“聚合算法重要：同一时间（或1ms内）、同方向连续成交应聚为一个 trade”。
> 我非常赞同，并建议你们把“原始逐笔成交 → 微聚合成交（micro-batch）”作为一个**标准预处理层**，不光服务因子，也能服务标签/诊断。

### 7.1 核心逻辑

next20 的可预测性很多来自“执行流持续性”（metaorder）。微聚合可以：

- 降噪：把拆单/撮合碎片合并
- 让 run-length 特征更稳定（减少毫秒级抖动）

### 7.2 两层聚合建议（A/B 都试）

**A. 时间聚合（你提的 1ms）**

- 规则：同方向、时间戳差 ≤ Δt（如 1ms/2ms/5ms）、且成交价不逆向跳变，则合并
- 输出聚合 trade：`agg_price(VWAP)`, `agg_amount`, `agg_levels_consumed`, `agg_duration`

**B. 事件序列聚合（对 timestamp 噪声更鲁棒）**

- 规则：连续 N 笔同方向（例如 N=3/5）且中间无反向成交插入则合并

> 你担心过拟合：这里不是“拟合”，是规则聚合。建议 A/B 都做，选更稳的那个（看跨日、跨标的一致性）。

### 7.3 Run / Metaorder 因子集合

在“聚合 trade”序列上定义 run：

- `run_len`、`run_amount`、`run_duration`
- `run_intensity = run_amount/run_duration`
- `run_efficiency = price_drift/run_amount`（price_drift 用 p_ref）
- `run_acc = intensity_fast - intensity_slow`
- `time_since_last_same_side_run`

并提供“run 状态”类输出（tick 级持久化）：

- 当前 run 的方向、长度、累计量（state）
- run 结束时刷新一次，然后状态保持直到下一次更新（对采样友好）

------

## 8. Walk-the-book / Penetration 因子簇（覆盖：原簇 8 + 你对 tick 更新与 bar 聚合的工程问题）

> 你问得非常工程化：
>
> - 因子逐 tick 更新，但 walk-the-book 只在成交时有；非成交 tick 怎么办？
> - bar 内怎么聚合才能被 entrust bar 使用？

### 8.1 结论（严谨回答）

- **tick 级更新完全可行**：在成交事件更新 penetration 值；非成交 tick **carry-forward（保持上一个值）**。这在高频里是标准做法。
- 采样时如果你们对 state 取 last，那么它代表“bar 结束时最近一次成交的穿透强度”。这对 next20 是有意义的（近端冲击状态）。
- 若你希望 bar 内统计（max/mean），那属于“聚合器增强”的问题：
  - 你说你们现在 json 只区分 state/amount，不想隐式用 max。那就**显式产出**一个“滚动 max/EMA”版本（不依赖 bar 边界），或者扩展聚合器类型（你们自行决定工程路线）。

### 8.2 因子集合（bar-agnostic 版本，推荐）

在成交发生时计算：

- `pen_levels`（吃穿档数）
- `pen_bps`（穿透 bps）
- `pen_ratio_best = trade_amount/(best_amount+ε)`
- `trade_through_flag`

tick 输出（state）：

- `pen_bps_last`（carry-forward）
- `EMA_fast(pen_bps)`、`EMA_slow(pen_bps)`
- `pen_burst = fast - slow`
- `pen_tail_proxy = EMA(clip(pen_bps,0,Pmax)^2)`（用二阶矩 proxy 极端，不需要分位）

若你们希望“类似 bar max”的信息但不想依赖 bar：

- `rolling_max_pen_bps_{N}`：按最近 N tick 或最近 T 秒的 rolling max
  - N/T 可用 event_rate 自适应（见簇10），避免固定窗口失真。

------

## 9. 吸收/毒性/逆向选择因子簇（覆盖：原簇 9、16、17 + 你对“不要回归”的要求）

> 你说：尽量不要用回归，防止 overfitting，且多品种回归麻烦。
> 我同意：这簇完全可以用**简单比值、残差式 proxy、以及 realized spread 的“固定延迟法”**来做，不需要回归。

### 9.1 核心逻辑

同样的净流，价格响应弱 = 吸收（可能回归/也可能蓄势突破）；响应强 = 毒性强（更可能趋势延续）。这类“响应强弱”状态常常持续超过短端，适合 next20。

### 9.2 因子集合（无回归）

#### 9.2.1 吸收指数（flow 大但价格不动）

定义一个 flow（可多版本）：

- `flow_trade = signed_trade_amount_ema`
- `flow_ofi = OFI_exp`（簇5）
- `flow_netliq = add-cancel`（按近端桶）

然后：

- `absorption = |flow| / (|Δp_ref_fast| + ε)`
- `absorption_signed = flow * sign(Δp_ref_fast)`（同向推进 vs 反向抵消）
- `absorption_burst = absorption_fast - absorption_slow`

#### 9.2.2 realized spread / adverse selection（固定延迟法，不回归）

对每笔（聚合）成交记录 `p_ref0`，在 **Δticks 或 Δseconds 后**取 `p_refΔ`（注意只用已发生的未来时刻更新，在线不泄露）：

- `effective = 2*sign*(trade_px - p_ref0)`
- `impact = sign*(p_refΔ - p_ref0)`
- `realized = effective - impact`
- `adverse = impact`（或 `effective - realized`）

输出 EMA：

- `EMA(adverse_buy)`, `EMA(adverse_sell)`, `adverse_imb`

> 你问“用 micro 替代 mid 会更好吗？”
> 这里我建议 **A/B 都做**：`p_ref = mid` vs `p_ref = vwapmid(X)` vs `p_ref = micro_L3`。通常在稀疏盘里 micro/vwapmid 会更稳，但要用数据验证。

#### 9.2.3 库存压力 proxy（不需要知道做市商身份）

- `passive_sell_fill = amount(trades at ask)`
- `passive_buy_fill = amount(trades at bid)`
- `inv_pressure = EMA(passive_sell_fill) - EMA(passive_buy_fill)`
- 与补给速度交互（簇11）：`inv_pressure * replenish_speed_ask`

------

## 10. 时间尺度自适应 + 哪些因子需要改（覆盖：原簇 19 + 你问“哪些适合这样改变”）

### 10.1 核心逻辑

你们的 entrust bar 事件密度波动很大；固定 α 的 EMA 在不同活跃度下代表的真实时间跨度不一致 → 影响跨标的、跨日稳定性。
解决方案：**按 dt 或 event_rate 自适应平滑**，或直接把强度写成“每秒/每事件/每金额”。

### 10.2 哪些因子最适合做“自适应/归一”（明确回答你）

优先级从高到低：

1. **所有“强度类/流量类 EMA”**（最该改）

- add/cancel/trade 的 EMA：`a3_add_signed_turnover_ema_*`、`trade_imb_ema`、`net_liq_*` 等（你们 Top80 里很多）
  改法：
- `alpha = 1 - exp(-dt/τ)`（按真实时间半衰）
- 或输出 `flow_per_sec = flow/dt`、`flow_per_event = flow/event_cnt`

1. **活动度类（event_rate、order_prob、trade_prob）**

- 这些本身就是 dt 敏感的，建议统一成“每秒”并做 EMA。

1. **波动类（abs_ret、rvol）**

- 波动和时间尺度强相关；做 time-based EMA 会显著减少 regime 假切换。

1. **不建议优先改的**

- 纯盘口快照结构（imbalance、depth、gap、slope）本身不是时间序列累计，改动收益可能不如 flow 类显著。

### 10.3 简单试验（不 fit）

- 对同一因子输出两版：`event-EMA` vs `time-EMA`
- 看跨标的稳定性：按标的分组算 RankIC 分布、看方差是否下降；看 Top/Bottom 分位收益是否更稳（不需要回归）。

------

## 11. 韧性/恢复（Resilience）因子簇（覆盖：原簇 10 + 你说“覆盖率低怎么办”）

你这个质疑很关键：如果把韧性定义成“发生 shock 才进入状态机”，确实可能覆盖率不高。解决思路是：

- **把“事件型韧性”变成“连续型韧性 proxy”**，保证每 tick 都有值；
- 同时保留事件型作为“强触发信号”（覆盖低但强）。

### 11.1 连续型韧性 proxy（coverage≈100%）

（不需要定义 shock）

- `replenish_speed_near = EMA(add_near_amount) / (EMA(|Δp_ref|)+ε)`
  - 同样的补给，在价格更稳定时说明“吸收更强”
- `withdraw_speed_near = EMA(cancel_near_amount) / (EMA(|Δp_ref|)+ε)`
- `depth_recovery_proxy = -EMA(Δdepth_near_signed)`（深度变化回补的方向性）

以及不对称版：

- `replenish_asym = replenish_bid - replenish_ask`

### 11.2 事件型韧性（覆盖低但强）

定义 shock（满足一个即可）：

- `spread_z` 超阈值
- `pen_bps` 超阈值（簇8）
- `max_gap_bps_within_R` 突增（簇2）

然后测：

- `time_to_spread_normal`（到回到中位数/阈值）
- `time_to_depth_restore(X)`（到 fixed amount 深度恢复）
- `recovery_slope = (depth_now - depth_min)/elapsed`

### 11.3 参数怎么定（不 fit）

- shock 阈值用历史分位：如 spread_z 的 90/95 分位；pen_bps 的 90 分位。
- 覆盖率目标：让“事件型”覆盖率在 1%–10% 区间（太低没样本，太高就变成连续型了）。

------

## 12. 墙单/集中度/闪烁/大小单分层（覆盖：原簇 12、13、14、15 + 你的多条 comment）

你说：

- 簇12“中间数据很有意思，但怎么写成因子需要进一步考虑”
- 簇13“不要 fit/PCA”
- 簇15“大小单怎么定义，需要研究”
  这些我统一在一个“结构因子簇”里给出可落地方案。

### 12.1 墙单（Wall）——如何把中间数据变成可用因子（回答你簇12）

**墙的定义（建议 A/B/C）**

- A：价位 amount > `k * median(level_amount_within_R)`
- B：价位 amount 占 near 总额比例 > θ（如 20%）
- C：局部极大：该价位 amount > 邻近价位的 `m` 倍

墙相关因子（每 tick 更新）：

1. `wall_strength_side = max_level_amount_within_R / (total_amount_within_R + ε)`
2. `wall_distance_bps`：墙价位距离 p_ref（bps）
3. `wall_age`：墙首次出现到现在的时间
4. `wall_erosion_cancel`：墙量减少中，来自撤单的比例
5. `wall_erosion_trade`：来自成交的比例
6. `wall_break_flag`：墙强度在短窗口内跌破阈值（可用 fast-slow diff）

不对称：

- `wall_strength_imb = wall_strength_bid - wall_strength_ask`
- `wall_break_asym`

> 这里的关键是：你们有 full_book，可以把“墙”识别到更深位置，并且用 bps/amount 统一。

### 12.2 集中度/熵/HHI/Gini（无 PCA，回答你簇13）

对 near 区域（用 amount 截断 X 或 bps 半径 R）定义分布 `p_i = amount_i / Σ amount`：

- `entropy = -Σ p_i log(p_i+ε)`
- `HHI = Σ p_i^2`
- `gini`（可用近似公式，不需要 fit）
  输出：
- bid/ask 各自 + 差值/比值

### 12.3 报价闪烁/队列周转（回答你簇14）

- `quote_churn = count(best_price_change) / time`
- `best_queue_turnover = (add_best + cancel_best)/ (live_best + ε)`
- `best_lifetime`（best 价位平均持续时间）

### 12.4 大小单分层（回答你簇15：怎么定义、怎么研究）

**不要只给一个阈值**，建议给 2–3 套定义并行，最后选稳的：

**A. 标的内分位法（最稳健）**

- 大单：订单 amount 在该标的近 N 日（或当日）分布的 top 10%
- 小单：bottom 50%
  优点：跨标的一致性强；缺点：需要维护分位统计，但这是简单统计。

**B. 相对中位数倍数（更工程）**

- 大单：amount > `k * median_order_amount`，k 取 {3,5,10}
- 小单：amount < `1 * median`

**C. 绝对金额阈值（可解释但跨标不稳）**

- 例如 1w/5w/10w CNY

**要做的简单统计试验（不 fit）**

1. 看不同定义下“大单占比”是否稳定（不应极端稀少或过多）
2. 对每种定义，做 `add_imb_large`, `add_imb_small`, `cancel_imb_large`, `trade_imb_large` 的分位收益曲线（简单分箱）
3. 选“跨日稳定 + 单调性更好”的那套（而不是只看某段提升）

------

## 13. 事件主导权与分解（覆盖：原簇 20 + 你在簇5/6里对分类的要求）

### 13.1 核心逻辑

市场在不同状态下（新增主导/撤单主导/成交主导），同一个方向信号含义不同。next20 的可预测性高度依赖这种门控。

### 13.2 因子集合

分类型 event_rate（按时间或按事件）：

- `rate_add`, `rate_cancel`, `rate_trade`
  主导权：
- `cancel_over_add = rate_cancel/(rate_add+ε)`
- `trade_over_order = rate_trade/(rate_add+rate_cancel+ε)`
- `dominance_vec = [share_add, share_cancel, share_trade]`（三者占比，连续输出）

并与“激进分类”（簇6）结合：

- `rate_cross_spread`
- `rate_inside_spread`
- `rate_join_best`
- `rate_away`

------

## 14. 条件化动量/回归（保留原簇 22 的思想，但更工程化）

你们 baseline 已有很多 mom/mr/dev/vol 状态量。
这里的升级不是再造一个 EMA，而是把“动量/回归”变成**结构条件下的版本**（不需要任何拟合）：

- `trend_confirm = sign(flow_netliq) * sign(micro_gap)`
- `mom_thin = mom * f(thinness)`（thinness 用簇2的 eff_spread_X 或 cumAmount(R)）
- `mr_absorb = mr * f(absorption)`（簇9）
- `mom_resilience = mom * (1/replenish_speed)`（簇11）

这些都是显式交互项，LGBM 本来也能学，但显式构造能提升样本效率与可解释性。

------

## 15. 聚合/工程落地建议（对应你簇23、簇24的立场）

### 15.1 关于原簇23（bar 内累计）——按你要求：暂不推进，但不丢失

你明确说：bar 切分方式未来可能改，现在不想在因子产出阶段引入 bar-reset 逻辑。
我同意这个工程纪律：**因子尽量 bar-agnostic**，用 EMA/rolling 表达过程量；bar 变化不会导致因子定义重写。

所以原簇23我保留为“未来专题”，但这版文档里不把它作为当前落地路径。

### 15.2 关于簇24（你们已有 state/amount json）

你说得对：如果 max/ratio 等已知有增量，应该在写因子时显式写出来。

这里给一个**建议的“因子作者输出规范”**（不需要改聚合器就能做很多事）：

- 所有“原始冲击量”输出 **三件套**（都可标 state）
  1. `x_raw`（只在事件发生时更新，否则 0 或 carry）
  2. `x_ema_fast`（bar-agnostic）
  3. `x_ema_slow`
  4. `x_diff = fast - slow`
- 所有“比值/归一化”**直接输出最终比值**（避免下游 sum 后再 ratio）
  - 例：`imb = signed/(abs+ε)` 在因子内做完，输出 state

如果你们将来愿意扩展 json 类型，可以考虑：

- `state_last`, `state_ema`, `state_rolling_max_T`, `amount_sum`
  但这属于工程演进，不是这版必须。

------

# 16. 经典但 baseline 仍可补全的一组因子（原簇25：你要“更详细”）

下面这组我尽量做到“经典 + 可直接落地 + 不和已有 Top80 完全重复”，同时每条都给清楚构造思路。

> 说明：你们 Top80 已经有大量 flow_imb、spread、gap、wimb、depth、vol、event_rate、micro_gap 等。
> 所以下面更侧重“缺失的结构维度”或“把已有信号做二阶升级”。

------

## 25-A. 订单流一致性/冲突度（Flow Consistency）

**逻辑**：趋势更容易在“订单净流、成交净流、微价倾向”三者一致时延续；三者冲突时更像吸收/假信号。

因子：

- `consistency = sign(net_liq_flow) * sign(trade_flow) * sign(micro_gap)`（取 -1/0/1）
- `conflict_score = count(sign mismatch)`（0~2）
- `flow_align_strength = (net_liq_imb + trade_imb + micro_edge_norm)/3`

实验：按 conflict_score 分桶看 next20 分位收益差异。

------

## 25-B. 撤单驱动 vs 新增驱动（同净值不同机制）

**逻辑**：同样 `net = add - cancel`，如果是“cancel 驱动净变化”通常更像流动性撤退（跳价/波动），如果是“add 驱动”更像真实补给/趋势。

因子：

- `net = add - cancel`
- `cancel_share = |cancel|/(|add|+|cancel|+ε)`
- `net_given_cancel = net * cancel_share`
- `net_given_add = net * (1-cancel_share)`

------

## 25-C. 队列拥挤度结构（Order Count × Size）

你们已有 order_cnt_imb（L1/L5）且 gain 很高，是典型门控。
升级方向：让“笔数”不被极小碎单主导。

因子：

- `avg_order_size_near = near_amount / (near_order_cnt+ε)`
- `cnt_weighted = Σ_i cnt_i * w_i`（w_i 用 amount 或 1/(distance)）
- `crowding_index = order_cnt / (amount+ε)`（单位金额对应多少笔）

------

## 25-D. 价阶不规则性指数（Irregular Grid Index）

**逻辑**：稀疏/不规则价阶会改变冲击传播路径与回归速度。

因子（within R bps）：

- `grid_irregular = std(gap_bps)/(mean(gap_bps)+ε)`
- `large_gap_ratio = count(gap_bps>θ)/count(levels)`
- `effective_tick_bps = median(gap_bps)`（不同阶段 tick 有效尺度变化）

------

## 25-E. “前方阻力/支撑”净变化（Forward Barrier Change）

**逻辑**：next20 漂移往往由“前方墙是否撤走/补上”决定。

定义前方区域（例如上方 +10bps 内）：

- `forward_ask_amount(R)`、`forward_bid_amount(R)`
  做变化：
- `Δforward_ask = forward_ask - EMA(forward_ask)`
- `Δforward_bid`
  派生：
- `forward_release = -Δforward_ask`（上方供给减少 = 上行更容易）
- `support_build = +Δforward_bid`

------

## 25-F. “价格推动效率”无回归版本（Impact Efficiency）

**逻辑**：同样净流，价格动得更快/更慢反映毒性/吸收。

因子：

- `eff_trade = Δp_ref_fast / (trade_abs_amount_ema+ε)`
- `eff_ofi = Δp_ref_fast / (|OFI_exp|+ε)`
- `eff_netliq = Δp_ref_fast / (|net_liq|+ε)`
  以及对应的 `fast-slow` 变化（效率加速度）。

------

## 25-G. 方向性跳价概率 proxy（Jump Risk）

**逻辑**：next20 的尾部风险来自跳价；跳价有方向性（哪边更空/更薄）。

因子：

- `jump_risk_up = max_gap_ask_within_R * (1/cumAskAmount(R)+ε)`
- `jump_risk_down` 同理
- `jump_asym = up - down`

------

## 25-H. 价差-深度联合的“可交易性指数”（Tradability Index）

**逻辑**：同样信号，在低可交易性状态更难兑现/更噪声；这是高增益门控。

因子：

- `tradability = spread_bps / (cumAmount_within_10bps + ε)`
- `tight_deep_flag = 1[spread低且深度高]`
- `wide_thin_flag = 1[spread高且深度低]`

------

# 17. 你逐条 comment 的“简短结论索引”（方便你核对我没漏）

- 簇1 near 用 amount 截断：**同意**，并建议 amount/bps/levels 三套并行（簇4）。
- 簇2 扩到 20/50 档、考虑稠密稀疏：**同意但更推荐 fixed amount / fixed bps** 作为主版本（簇2/簇3）。
- 簇3 PCA：**按你建议去掉**，用确定性汇总替代（簇5）。
- 簇5 cross-spread 更激进、并按距离分层；bps 分桶：**已纳入**（簇6）。
- 簇6 passive 激进度按 ahead_amount；marketable 激进度按穿透距离：**同意并做成统一体系**（簇3+簇6+簇8）。
- 簇7 1ms 聚合成交：**强同意**，给出 A/B 两套规则（簇7）。
- 簇8 walk-depth tick 更新与采样：**可行**，trade 更新、非 trade carry-forward；并给 rolling/EMA 版本（簇8）。
- 簇9 不用回归：**同意**，用比值/固定延迟 realized spread（簇9）。
- 簇10 覆盖率低：**用连续型 proxy 解决**，事件型作为强信号保留（簇11）。
- 簇11 mid 用固定 amount vwap：**同意并纳入参考价体系**（簇1）。
- 簇12 如何写成因子：**给出墙强度/寿命/侵蚀/破裂等可落地指标**（簇12）。
- 簇13 不 fit：**同意**，只做 entropy/HHI/Gini 等（簇12）。
- 簇15 大小单定义：**给出三套定义 + 简单统计试验**（簇12.4）。
- 簇17 用 micro 替代 mid：**建议 A/B**（簇1 + 簇9）。
- 簇18 多研究但简单：**给出多种 micro/vwapmid，不用 fit**（簇1）。
- 簇19 哪些因子要自适应：**明确列出优先级**（簇10）。
- 簇23 bar-reset 暂不做：**尊重你的决定，作为未来专题保留**（簇15.1）。
- 簇24 max/ratio 要显式：**按你们 json 体系给出作者输出规范**（簇15.2）。
- 簇25 详细补全：**已给 8 个子类**（簇16）。

------

如果你愿意再往下走一步，我建议你给研究员一个“最小任务包”，按簇拆成可并行开发的卡片（每张卡片 6–12 个因子，统一命名、统一 p_ref、统一 X/R/τ 候选集合），这样你们 80 个研究员能在 1–2 轮就把这个体系铺开，同时实验空间不会炸掉。