# basic_table_v2 十天校验报告（20250102–20250115）

## 0. 范围与产物

- 校验数据集：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v2`
- 对比基准：
  - v1：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1`
  - v0(parquet 重刷)：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v0_parquet_20250102_20250115`
- 日期范围：20250102–20250115（10 个交易日）

## 1. v2 旧列（v1 列）一致性校对

目标：确认 v2 在新增 bar 列以外，**所有旧列值/行数/行序**与 v1 完全一致。

- 结果：PASS（10/10 日全部通过）
- 对比模式：`left_subset`（仅比较 v1 的列，允许 v2 多出新列）
- 详见：`compare_v1_vs_v2_left_subset_20250102_20250115.md/json`

## 2. v2 与 v0(parquet) 的一致性（time shift）

说明：v0(parquet) 的 `time = local_ts + 8h(ns)`，v2 的 `time = local_ts`。

- 结果：PASS（10/10 日全部通过）
- 规则：仅允许 `time_shift = 28800000000000ns`，其余列逐值精确一致（右侧允许多列）
- 详见：`compare_v0parquet_vs_v2_time_shift_left_subset_20250102_20250115.md/json`

## 3. v2 新增列（AggTrans Time-based bar）口径检查

### 3.1 新增列定义（来自实现）

新增列（均为 int64）：

- `aggtrans_time`：对 `event_type=trade` 输出当前 AggTrans 序号（0-index），非 trade 为 `-1`
- `cum_aggtrans_time`：AggTrans 累计计数（forward-fill）
- `bar_aggtrans_time_{100,200,400,800}`：基于 AggTrans 计数的 bar_id（0-index）；仅在 gated（连续交易且 book 稳定）输出，否则 `-1`

AggTrans 合并规则（per code）：

- 以 `exchange_ts` 为时间轴
- trade 的 taker_side：`bid_id > ask_id => BUY(+1)`，否则 SELL(-1)
- 若相邻 trade（按“trade 序列”）满足 `dt<=1ms` 且 `taker_side` 不变 → 合并为同一 AggTrans；否则 AggTrans 序号 +1

### 3.2 校验项与结果

对 v2 10 天产物执行以下硬约束检查（全量扫描）：

- `event_type=trade => aggtrans_time>=0`；`event_type!=trade => aggtrans_time==-1`
- `aggtrans_time>=0 => cum_aggtrans_time == aggtrans_time + 1`
- `cum_aggtrans_time >= 0`
- 以 `bar_time_1s>=0` 作为 gated proxy：
  - not gated 或 `cum==0` 时：`bar_aggtrans_time_* == -1`
  - gated 且 `cum>0` 时：`bar_aggtrans_time_N == floor((cum-1)/N)`（N=100/200/400/800）
- `bar_100 >= bar_200 >= bar_400 >= bar_800`（gated 且 `cum>0`）
- per-code（按输出顺序、stable）：
  - `cum_aggtrans_time` 单调不降
  - 相邻步长不超过 1
  - `cum` 的增加只能发生在 trade 行

结果：PASS（所有 violation=0）

- QC JSON：`qc_aggtrans_time_bars_20250102_20250115.json`

## 4. 需要你确认的“口径选择点”（非代码错误，但会影响下游解释）

当前实现中，AggTrans 的 state（`cum_aggtrans_time`）对 **所有 trade** 都会更新；gated 仅影响 `bar_aggtrans_time_*` 的输出是否为 `-1`。

这意味着：开盘集合竞价（例如 09:25）的 trade 也会计入 `cum_aggtrans_time`，从而影响后续连续交易时段的 bar_id 起点。

如果你的预期是“只统计连续交易时段的 AggTrans”（排除集合竞价），需要在 state 更新时也加 gating（或至少 `IsContinuousTime(exchange_ts)`）过滤。

