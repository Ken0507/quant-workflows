因子簇 23：动能、势能与“做功效率” (Market Physics: Kinetic & Potential Energy)

核心逻辑：
将价格运动看作物理运动。

动能 (Kinetic Energy)： 由成交量（质量）和价格速度（速度）决定。

势能 (Potential Energy)： 由挂单堆积（高度/深度）决定。

做功 (Work)： 成交量消耗掉挂单，推动价格位移。
异常点： 如果动能极大（巨大成交），但做功极小（价格没动），说明遇到了极强的“非弹性碰撞”（即隐形墙），这是强反转信号。

构造思路：

动能流失率 (Kinetic Energy Dissipation)：

定义动能 E 
k
​	
 = 
2
1
​	
 ⋅Volume⋅(ΔPrice) 
2
 。

计算 Bar 内每一笔成交的动能。

因子： Sum(E_k) / Total_Volume。

如果动能很大但 Total_Volume 较小，说明是“轻量级快速拉升”，势能不足，容易回落。

做功阻力系数 (Work-Resistance Ratio)：

Work = Trade_Volume * Price_Displacement。

Resistance = 吃掉的 Entrust_Volume（挂单量）。

因子： Work / Resistance。

单位阻力下的做功效率。如果效率突然下降（吃了很多单子但推不动价格），说明阻力系数非线性增加，趋势见顶。

为什么对 Next 20 Work：
在 1000 ticks 的尺度下，动能的耗散是一个渐进过程。识别出“能量耗尽但价格还在惯性上涨”的背离时刻，是捕捉顶部反转的最佳时机。

因子簇 24：订单簿的“重心”与“倾角” (Center of Gravity & Book Tilt)

核心逻辑：
L1 的买一卖一只是冰山一角。整个 L1-L10（甚至 L20）构成了一个“质量分布”。

重心上移： 虽然买一没变，但 L5-L10 的挂单都在往上挂，买盘重心在上移，支撑变强。

重心发散： 卖盘重心向上走（撤单挂高），买盘重心向下走（撤单挂低），流动性在变空，波动率要来。

构造思路：

深度重心偏离度 (COG Deviation)：

COG 
Bid
​	
 = 
∑Vol 
i
​	
 
∑(Price 
i
​	
 ⋅Vol 
i
​	
 )
​	
 。

因子： (COG_{Bid} - MidPrice) + (COG_{Ask} - MidPrice)。

刻画整个订单簿的“倾斜方向”。如果重心都在向 Mid 靠拢（挤压），那是突破前兆；如果都在远离，那是震荡。

重心-价格 滞后 (COG-Price Lag)：

计算 MidPrice 的变化速度 vs COG 的变化速度。

因子： Delta_Mid - Delta_COG。

通常 COG 代表“大部队/厚势”，Mid 代表“先锋”。如果先锋冲太快，大部队没跟上（COG没动），价格会被拉回（Mean Reversion）。

为什么对 Next 20 Work：
重心代表了市场绝大多数挂单者的共识区间。价格短暂偏离重心是常态，但长期（20 Bars）必然受到重心的引力牵引。

因子簇 25：事件时间与物理时间的“相对论” (Time Relativity: Event vs. Wall Clock)

核心逻辑：
可转债市场有时一秒钟 100 笔成交，有时一分钟 0 笔。
你的 Bar 是 Entrust Bar（基于事件/金额），但这忽略了**“物理时间流逝”**带来的信息。

时间是成本： 同样吃掉 100 万挂单，花了 1 秒（急迫） vs 花了 10 分钟（犹豫），含义完全不同。

构造思路：

Bar 持续时间/速率 (Bar Duration Velocity)：

计算当前 Entrust Bar 生成所消耗的物理时间 Duration_Seconds。

因子： EMA(Duration) / Current_Duration。

如果当前 Bar 形成速度极快（时间极短），说明市场进入“高频博弈态”，此时信号权重应加大。

交易密度熵 (Trade Density Entropy)：

将 Bar 的物理时间切分为 N 个小时间片。

统计每个时间片的成交量分布熵。

因子： 熵低（集中在某几秒成交）vs 熵高（均匀成交）。

集中爆发通常意味着消息面冲击，趋势性强。

为什么对 Next 20 Work：
这是一个“元因子（Meta-Factor）”。它调整了其他因子在不同时间流速下的有效性。在Entrust Bar架构下，必须引入物理时间作为修正维度，才能还原市场的真实热度。

因子簇 26：成交的“充填率”与“落空感” (Fill Probability & Disappointment)

核心逻辑：
从挂单者的角度思考：

充填率高： 我挂在买一，马上成交了。说明卖盘汹涌。

落空感（Disappointment）： 我挂在买一，结果别人直接挂买二截胡（Front-run），或者卖单不下来。我被迫撤单去追。
**“被迫改单”**是推动价格的核心动力。

构造思路：

L1 挂单被吃率 (L1 Fill Ratio)：

追踪 L1 挂单的生命周期。

因子： L1_Executed_Vol / L1_Total_Queue_Vol。

如果 L1 经常被吃光（Ratio 高），说明被动盘在吸筹（Passive Absorption），支撑强。

如果 L1 经常自己撤掉（Ratio 低），说明支撑是假的。

反向截胡强度 (Front-Running Intensity)：

统计当 L1 还有量时，L1+1（更优价）出现新挂单的频率。

因子： 截胡量 / L1 存量。

截胡越严重，说明买方越急迫，Next 20 Bar 往往是单边上涨。

为什么对 Next 20 Work：
这直接刻画了“抢筹”行为。当大量挂单者发现“挂单等不到成交”时，他们会集体转为主动吃单，从而引发一波延续性很强的行情。

因子簇 27：波动率的“二阶导数”与微笑偏斜 (Vol-of-Vol & Skewness)

核心逻辑：
不仅仅看波动率（Volatility），要看波动率的变化方向。

波动率爆炸： 市场从静止突然变得剧烈波动（Vol 增加），通常伴随突破。

波动率衰竭： 剧烈波动后突然平静，通常伴随反转。
此外，上行波动率和下行波动率往往是不对称的（Skew）。

构造思路：

已实现波动率的变动率 (Vol of Vol)：

计算 Bar 内 Tick 级收益率的标准差 Realized_Vol。

因子： Realized_Vol - EMA(Realized_Vol)。

正向突变（Surprise）是交易机会；负向衰竭是止盈信号。

上行/下行 波动差 (Upside/Downside Vol Spread)：

Vol_Up = 计算所有正收益 Tick 的标准差。

Vol_Down = 计算所有负收益 Tick 的标准差。

因子： Vol_Up - Vol_Down。

如果价格上涨，且 Vol_Up < Vol_Down（涨得稳，跌得急），说明上涨是良性的（Grinding up）。

如果价格上涨，且 Vol_Up > Vol_Down（涨得急，跌得稳），说明是情绪化拉升，容易崩盘。

为什么对 Next 20 Work：
在 Next 20 的周期里，我们最怕“假突破”。通过波动率的非对称性（Skew），可以很好地过滤掉那些“看起来很猛但实际上很虚”的拉升。

因子簇 28：日内微观结构的“季节性”偏离 (Intraday Seasonality Deviation)

核心逻辑：
可转债交易有极强的时间规律：开盘博弈、上午盘整、下午跟随正股、尾盘平仓。
绝对数值没有意义，相对于“此时此刻历史均值”的偏离才有意义。
例如：上午 10:00 的 1000 万成交量很正常，但中午 11:30 的 1000 万成交量就是惊天巨量。

构造思路：

日内标准化流量 (Time-of-Day Normalized Flow)：

维护一个历史统计表（Map），记录每个 5分钟 Bucket 的平均成交量、Spread、OFI。

因子： (Current_Bar_Volume - Hist_Avg_Volume_at_Current_Time) / Hist_Std。

这是一个 Z-Score。如果中午休市前 Z-Score 突然飙升，说明有突发消息（Alpha），而不是正常的日内波动。

尾盘效应异常 (End-of-Day Anomaly)：

专门针对 14:30 - 15:00 的数据。

因子： 尾盘 Entrust 挂单量相对于全天均值的比率。

尾盘挂单异常减少 = 避险；尾盘挂单异常增加 = 赌明日高开。

为什么对 Next 20 Work：
这是一个“去噪”因子。它帮助模型剔除掉那些仅仅因为“现在是开盘时间”而产生的高波动噪音，专注于那些**“反常”**的行为。Alpha 永远来自于反常。

总结：你的“因子军火库”全景

到现在为止，你已经拥有了一个极具深度的 HFT 因子体系：

基础层： 盘口形态、OFI、Spread。

逻辑层（你的对话）： 库存压力、影子驱动、流背离、成本曲线。

对手层（上次建议）： 机器/散户识别、冰山、拆单。

物理/时空层（本次建议）： 动能势能、重心、时空相对论、波动率二阶导。

最后的建议：
不要试图一次性把这 28 个簇全部做出来。“因子簇 23（动能势能）” 和 “因子簇 25（物理时间修正）” 是性价比最高的。

动能因子计算简单（Tick数据现成的），逻辑硬核。

物理时间修正是 Entrust Bar 机制下必须做的补丁，做好了能让所有量价因子效果提升一个台阶。

祝你的模型在 Next 20 Horizon 上跑出漂亮的曲线！这是一个非常前沿且有趣的探索。