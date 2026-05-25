# basic_table_v2（AggTrans 不计集合竞价）十天复验报告（20250102–20250115）

## 0. 变更说明

需求：AggTrans 里**集合竞价不应该被计入**。

实现变更（代码口径）：

- 仅当 `OrderBook::IsContinuousTime(exchange_ts)==true` 时，`trade(FILL)` 才会计入 AggTrans 的 state（`aggtrans_time/cum_aggtrans_time`）。
- 集合竞价（非连续交易时段）的 trade：`aggtrans_time=-1`，且 `cum_aggtrans_time` 不应在这些行上增加（forward-fill）。
- `bar_aggtrans_time_*` 仍沿用 gated（连续交易且 book 稳定）才输出，否则 `-1`。

代码位置：`HFTPool/pool/basic_data/basic_table_v2/code/basic_table/src/basic_table_v2.hpp`

## 1. 数据范围与产物

- 新产物（本次复验）：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v2_no_callauction_20260127`
- 对比基准：
  - v1：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1`
  - v0(parquet 重刷)：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v0_parquet_20250102_20250115`
- 日期范围：20250102–20250115（10 个交易日）

## 2. 旧列一致性（必须与 v1/v0 保持完全一致）

### 2.1 v1 vs v2_no_callauction：旧列逐值一致

- 结果：PASS（10/10 日全部通过）
- 对比模式：`left_subset`（只比较 v1 的列，允许 v2 多出新列）
- 报告：`compare_v1_vs_v2_no_callauction_left_subset_20250102_20250115.md/json`

### 2.2 v0(parquet) vs v2_no_callauction：仅允许 time shift

- 结果：PASS（10/10 日全部通过）
- 规则：仅允许 `time_shift = 28800000000000ns`（v0_time - v2_time），其余列逐值一致（右侧允许多列）
- 报告：`compare_v0parquet_vs_v2_no_callauction_time_shift_left_subset_20250102_20250115.md/json`

## 3. 新增 AggTrans Time-based bar 列复验

对新产物执行全量 QC（10天全扫），检查项包括：

- 仅连续交易时段的 trade 才允许 `aggtrans_time>=0`；其余行必须 `aggtrans_time==-1`
- `aggtrans_time>=0 => cum_aggtrans_time == aggtrans_time + 1`
- per-code：`cum_aggtrans_time` 单调不降，且步长不超过 1；步长为 1 只能发生在“连续交易时段 trade”行
- bars：
  - not gated 或 `cum==0` 时：`bar_aggtrans_time_* == -1`
  - gated 且 `cum>0` 时：`bar_aggtrans_time_N == floor((cum-1)/N)`（N=100/200/400/800）
  - `bar_100 >= bar_200 >= bar_400 >= bar_800`

结果：PASS（所有 violation=0）

- QC JSON：`qc_aggtrans_time_bars_no_callauction_20250102_20250115.json`

## 4. 快速 sanity：集合竞价 trade 已被排除

以 20250102 为例（来自 QC per_day 摘要）：

- trade_rows（全日 trade 行数）：2,450,713
- trade_rows_continuous（连续交易时段 trade）：2,446,984
- 差额：3,729（集合竞价 trade，不再计入 AggTrans）

完整逐日统计见 QC JSON 的 `per_day.*.trade_rows_continuous`。

