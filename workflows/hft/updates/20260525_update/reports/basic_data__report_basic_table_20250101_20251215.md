# basic_table 底表刷取报告（全量）

## 0. 声明
- 统计口径：基于全量 20250101–20251215（闭区间）已刷取产物。
- factor_pool：`/data/db/hft/factor_pool/debug/basic_data/basic_table`

## 1. 字段定义与出处（严格以文档 + SDK 样例头文件为准）
### 1.1 time / exchange_ts / md_id / 成交价字段
- `time`：parquet 固定列（`int64`）。由 `DataStore::AddRow(code, time, ...)` 的 `time` 参数决定；hft_tools 文档约定 `time=int64, ns epoch`。
- 本实现使用 `MarketEvent.local_ts` 写入 `time`（回放驱动时间）。
- `exchange_ts`：来自 `hft::MarketEvent.exchange_ts`（`int64_t`）。
- `md_id`：来自 `OrderData.biz_index` / `TransData.biz_index`（`int64_t`），`GetMdId()==biz_index`。
- trade 成交价字段：`hft::TransData.price`（`int64_t` 缩放价，`PRICE_SCALE=1000`；换算 `price/1000.0`）。
  - 头文件出处：`/data/share/dev/hft/include/orderbook/event_types.h`
  - SDK 样例 hpp：`/data/share/dev/hft/sdk_tools/templates/project/tick_feature_agent.hpp`
  - hft_tools 文档：`/home/cken/hft_projects/hft_tools/docs/user_guide_zh.md`
  - 数据接口文档：`/home/cken/hft_projects/HftKnowledge/data/data.md`

### 1.2 盘口一档字段出处
- `ask1/bid1`：`OrderBook::GetBestAsk()/GetBestBid()`（`int64_t` 缩放价；空簿返回 0）。
- `askvol1`：`OrderBook::GetAskVol(best_ask_price)`（`int64_t`）。
- `bidvol1`：`OrderBook::GetRangeVol(best_bid_price, best_bid_price, Side::BUY, ...)`（`int64_t`）。
  - 头文件出处：`/data/share/dev/hft/include/orderbook/orderbook.h`

### 1.3 LGJ bar tag 字段（IntervalCutter 口径）
- 字段：`bar_time_1s`, `bar_tick_100`, `bar_fill_1m`, `bar_entrust_1m`, `bar_entrust_v1`, `cum_fill_turnover`, `cum_entrust_amount`, `cum_entrust_v1`（均为 int64）。
- gating：仅当 `OrderBook::IsContinuousTime(exchange_ts) && OrderBook::IsSessionEnd()` 时推进 bar 状态；否则 bar_id 置为 -1。
- 时间口径：`bar_time_1s` 用 `local_ts` 做 1s 切分；其余 bar 使用与 LGJ 一致的 session 视图累计。
- 阈值：time=1s；tick=每 100 个“订单新增”事件；fill/entrust=每累计 1,000,000 RMB（milli-yuan=1e9）。
- ENTRUST_AMOUNT_V1：仅统计偏离最优价 <=2% 的委托/撤单（买对 best bid，卖对 best ask）。

- QC 摘要：bar_id 有效（>=0）的总行数占比（全表口径）：
  - bar_time_1s: 2,719,826,015/3,434,365,627 = 79.1944%
  - bar_tick_100: 2,719,826,015/3,434,365,627 = 79.1944%
  - bar_fill_1m: 2,719,826,015/3,434,365,627 = 79.1944%
  - bar_entrust_1m: 2,719,826,015/3,434,365,627 = 79.1944%
  - bar_entrust_v1: 2,719,826,015/3,434,365,627 = 79.1944%

- QC 摘要：cum 字段最大值（全表口径）：
  - cum_fill_turnover: max=15817652403022
  - cum_entrust_amount: max=80930308898302
  - cum_entrust_v1: max=78643411296959

## 2. 产出 schema
- 固定列（框架自动）：`code`（string）、`time`（int64）
- 手动列：`exchange_ts`(int64), `md_id`(int64), `ask1`(double), `bid1`(double), `mid`(double), `askvol1`(int64), `bidvol1`(int64), `spread`(double), `micro_price`(double), `last_trade_price`(double), `event_type`(string), `bar_time_1s`(int64), `bar_tick_100`(int64), `bar_fill_1m`(int64), `bar_entrust_1m`(int64), `bar_entrust_v1`(int64), `cum_fill_turnover`(int64), `cum_entrust_amount`(int64), `cum_entrust_v1`(int64)

## 3. 派生指标硬性定义（实现口径）
- `mid = (ask1 + bid1) / 2`
- `spread = (ask1 - bid1) / mid`；当 `mid==0` 或 `mid` 缺失时置为 NaN
- `micro_price = (ask1*askvol1 + bid1*bidvol1) / (askvol1 + bidvol1)`；当分母为 0 或任一输入缺失时置为 NaN
- `last_trade_price`：trade 行取当条成交价；非 trade 行取上一条 trade 成交价（前向填充）；在当日该 code 尚未出现过 trade 时为 NaN。

## 4. event_type 映射规则（可复现）
- 依据 `MarketEvent.type` + `OrderData.order_status` + `TransData.exec_type`（均定义于 `/data/share/dev/hft/include/orderbook/event_types.h`）
  - `TRADE + exec_type==CANCEL` → `cancel`
  - `TRADE + 其余(如 FILL)` → `trade`
  - `ORDER + order_status in {ADD, QUEUEING}` → `order`
  - `ORDER + order_status in {DELETE, CANCELED}` → `cancel`
  - `ORDER + order_status in {PART_TRADED_QUEUEING, ALL_TRADED}` → `order_modify`
  - `REJECTED` → `cancel`；其余/UNKNOWN 兜底 → `order`

## 5. 全量刷取过程与并行/分片策略
- tick feature 工程：`/home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table`
- 刷取命令：`python3 -m hft_tools extract-range --env debug --author basic_data --factor_set_name basic_table --start_date 20250101 --end_date 20251215 --project_dir /home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table --universe full --n_jobs 60`
- 分片策略：按日分片（hft_tools 内部按日期并行）。
- 断点续跑：日期目录存在则跳过；失败后可复跑同一命令，已完成日期不会重复（如需强制重跑加 `--overwrite`）。

## 6. 全量产出规模
- parquet 文件数：233（按日 1 文件）
- 日期覆盖：233/349 天（skip_no_data=116 天）
- 标的覆盖：269 个 code
- 总行数：3,434,365,627
- 产物总大小：134.48GB

## 7. 验收/质量检查（全量）
### 7.1 Schema 检查
- PASS：列齐全、列名一致、dtype 与预期一致。

### 7.2 event_type 检查
- order: 1,794,316,040 (52.2459%)
- trade: 691,966,062 (20.1483%)
- cancel: 948,083,525 (27.6058%)
- order_modify: 0 (0.0000%)

### 7.3 缺失率检查（NaN，占 double 列）
- ask1: 316,626/3,434,365,627 = 0.0092%
- bid1: 342,192/3,434,365,627 = 0.0100%
- mid: 658,671/3,434,365,627 = 0.0192%
- spread: 658,671/3,434,365,627 = 0.0192%
- micro_price: 658,671/3,434,365,627 = 0.0192%
- last_trade_price: 15,340,878/3,434,365,627 = 0.4467%

### 7.4 分 event_type 缺失率（示例列：spread/micro_price/last_trade_price）
- cancel: rows=948,083,525, spread_nan=0.0108%, micro_nan=0.0108%, last_trade_nan=0.0280%
- order: rows=1,794,316,040, spread_nan=0.0274%, micro_nan=0.0274%, last_trade_nan=0.8402%
- order_modify: rows=0, spread_nan=0.0000%, micro_nan=0.0000%, last_trade_nan=0.0000%
- trade: rows=691,966,062, spread_nan=0.0094%, micro_nan=0.0094%, last_trade_nan=0.0000%

### 7.5 合法性检查
- 检查范围：仅统计 `exchange_ts` 对应日内时间落在 09:30:00-11:30:00, 13:00:00-14:57:00 的样本（连续交易时段；其余时段为集合竞价/非连续交易）。
- 连续交易样本量：3,414,179,647/3,434,365,627 = 99.4122%
- ask1>=bid1（在 ask/bid 均非 NaN 的样本上）：2,924,268,658/3,413,873,606 = 85.6584%
- (ask1-bid1)<0 异常样本数：489,604,948
- micro_price in [bid1,ask1]（在 micro/bid/ask 均非 NaN 的样本上）：2,891,187,780/3,413,873,606 = 84.6894%
- micro_price 越界样本数：522,685,826

- 说明：已按 `exchange_ts` 剔除集合竞价/非连续交易时段；但在 book 重构/撮合自修复过程中仍可能出现短暂 crossed（BestBid>=BestAsk），从而产生 `ask1<bid1`、`micro_price` 越界与 `spread` 负值等现象。若下游研究只需要稳定盘口，可按 `ask1>=bid1` 进一步过滤，或参考 SDK 接口 `OrderBook::IsSessionEnd()`（定义于 `/data/share/dev/hft/include/orderbook/orderbook.h`）做 gating。

### 7.6 spread 分布（相对价差）
- finite 样本数：3,413,873,606（hist 范围[-1.0,1.0]，under=0, over=0）
- p1/p50/p99（直方图近似）：-0.003949999999999898, 0.00045000000000006146, 0.0020500000000001073
- min/max：-0.4000149440532008, 0.20609926250747465

- 备注：`p1/p50/p99` 为基于全量数据直方图的近似分位点（QC 使用固定 bin 近似）。

### 7.7 唯一性检查
- 主键：code, time, exchange_ts, md_id
- 重复行数：0（重复率=0.0000%）

### 7.8 时间序检查
- 每个 code 序列中 time 逆序次数：0（占比=0.0000%）

### 7.8b time / exchange_ts / md_id 的单调性与重复性（全量统计）
- time: min=1735809299838554368, max=1765810801928840704, 同 code 相邻 time 相等次数=0
- exchange_ts: min=1735780500000000000, max=1765782000000000000, 逆序次数=0（占比=0.0000%）, 同 code 相邻相等次数=2,255,867,999
- md_id: min=1, max=4657977228170428520, 逆序次数=991,662,664（占比=28.8747%）, 同 code 相邻相等次数=605,656,145

### 7.9 last_trade_price 专项检查
- trade 行数：691,966,062
- trade 行 last_trade_price 为 NaN 的行数：0（非 NaN 比例=100.0000%）
- forward-fill 规则不匹配行数：0（占比=0.0000%）
- last_trade_price NaN 分解：total=15,340,878, prefix(当日首笔成交前)=15,340,878, after_first_trade=0（after 占 NaN 比例=0.0000%）

## 8. 异常样本（抽样，最多各 5 条）
### 8.1 ask1 < bid1
- 20250102 code=123147 time=1735810199865801984 exchange_ts=1735781400000000000 md_id=21062 event_type=order ask1=121.381 bid1=127.102 mid=124.2415 askvol1=140 bidvol1=300 spread=-0.04604741571858038 micro_price=125.28168181818182 last_trade_price=126.2 note=ask1 < bid1
- 20250102 code=123147 time=1735810199865882624 exchange_ts=1735781400000000000 md_id=25690216 event_type=trade ask1=126.989 bid1=127.001 mid=126.995 askvol1=20 bidvol1=1630 spread=-9.449190913028429e-05 micro_price=127.00085454545454 last_trade_price=126.97 note=ask1 < bid1
- 20250102 code=123147 time=1735810199865908992 exchange_ts=1735781400000000000 md_id=25690216 event_type=trade ask1=127.0 bid1=127.001 mid=127.0005 askvol1=1440 bidvol1=1610 spread=-7.873984748129139e-06 micro_price=127.00052786885246 last_trade_price=126.989 note=ask1 < bid1
- 20250102 code=123092 time=1735810199866309120 exchange_ts=1735781400000000000 md_id=21069 event_type=order ask1=132.065 bid1=154.532 mid=143.2985 askvol1=90 bidvol1=110 spread=-0.15678461393524715 micro_price=144.42185 last_trade_price=132.0 note=ask1 < bid1
- 20250102 code=123092 time=1735810199866331136 exchange_ts=1735781400000000000 md_id=25690216 event_type=trade ask1=132.123 bid1=154.532 mid=143.3275 askvol1=80 bidvol1=20 spread=-0.15634822347421132 micro_price=136.60479999999998 last_trade_price=132.065 note=ask1 < bid1

### 8.2 micro_price 越界
- 20250102 code=123147 time=1735810199865801984 exchange_ts=1735781400000000000 md_id=21062 event_type=order ask1=121.381 bid1=127.102 mid=124.2415 askvol1=140 bidvol1=300 spread=-0.04604741571858038 micro_price=125.28168181818182 last_trade_price=126.2 note=micro_price outside [bid1, ask1]
- 20250102 code=123147 time=1735810199865882624 exchange_ts=1735781400000000000 md_id=25690216 event_type=trade ask1=126.989 bid1=127.001 mid=126.995 askvol1=20 bidvol1=1630 spread=-9.449190913028429e-05 micro_price=127.00085454545454 last_trade_price=126.97 note=micro_price outside [bid1, ask1]
- 20250102 code=123147 time=1735810199865908992 exchange_ts=1735781400000000000 md_id=25690216 event_type=trade ask1=127.0 bid1=127.001 mid=127.0005 askvol1=1440 bidvol1=1610 spread=-7.873984748129139e-06 micro_price=127.00052786885246 last_trade_price=126.989 note=micro_price outside [bid1, ask1]
- 20250102 code=123092 time=1735810199866309120 exchange_ts=1735781400000000000 md_id=21069 event_type=order ask1=132.065 bid1=154.532 mid=143.2985 askvol1=90 bidvol1=110 spread=-0.15678461393524715 micro_price=144.42185 last_trade_price=132.0 note=micro_price outside [bid1, ask1]
- 20250102 code=123092 time=1735810199866331136 exchange_ts=1735781400000000000 md_id=25690216 event_type=trade ask1=132.123 bid1=154.532 mid=143.3275 askvol1=80 bidvol1=20 spread=-0.15634822347421132 micro_price=136.60479999999998 last_trade_price=132.065 note=micro_price outside [bid1, ask1]

### 8.3 主键重复
- 无

### 8.4 time 逆序
- 无

### 8.5 last_trade_price ffill 不匹配
- 无

### 8.6 spread 极端值
- 20250102 code=123238 time=1735810199866782976 exchange_ts=1735781400000000000 md_id=21078 event_type=order ask1=123.12 bid1=184.68 mid=153.9 askvol1=940 bidvol1=1250 spread=-0.4 micro_price=158.25698630136986 last_trade_price=nan note=spread extreme
- 20250102 code=123089 time=1735810200097382912 exchange_ts=1735781400030000000 md_id=15914 event_type=order ask1=110.0 bid1=165.0 mid=137.5 askvol1=380 bidvol1=340 spread=-0.4 micro_price=135.97222222222223 last_trade_price=137.972 note=spread extreme
- 20250102 code=123152 time=1735815001696435200 exchange_ts=1735786202100000000 md_id=146276456 event_type=trade ask1=131.122 bid1=127.33 mid=129.226 askvol1=80 bidvol1=410 spread=0.029343940073979044 micro_price=127.94910204081634 last_trade_price=127.33 note=spread extreme
- 20250102 code=123152 time=1735815001696675840 exchange_ts=1735786202100000000 md_id=1854095 event_type=order ask1=131.122 bid1=127.536 mid=129.329 askvol1=80 bidvol1=3210 spread=0.027727733145698277 micro_price=127.62319756838906 last_trade_price=127.33 note=spread extreme
- 20250103 code=123118 time=1735896599837079808 exchange_ts=1735867800000000000 md_id=21468 event_type=order ask1=770.8 bid1=1156.2 mid=963.5 askvol1=10 bidvol1=10 spread=-0.4000000000000001 micro_price=963.5 last_trade_price=961.397 note=spread extreme

## 9. 已知不确定点（需补充信息）
- `exchange_ts/local_ts` 的单位（ns/us/ms）在 `/data/share/dev/hft/include/orderbook/event_types.h` 注释中未明确给出；本项目按 hft_tools 约定将 `time` 视作 ns epoch，并将 `exchange_ts` 作为原始 int64 字段原样落盘。
- `md_id=biz_index` 的唯一性范围（全局/按 code/按日）在头文件与本文档中未明确说明；本报告仅基于全量数据做了主键重复率统计（主键选用 `code+time+exchange_ts+md_id`）。若需要把 `md_id` 作为更强的业务主键，请提供 SDK/数据源对 `biz_index` 的唯一性承诺或数据字典说明。
