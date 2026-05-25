# basic_table_v1（Playground 适配）10天全量刷数与校对报告

- 日期范围：20250102–20250115（按 run-agent 实际交易日输出）
- 工程：`/home/cken/hft_projects/HFTPool/pool/basic_data/basic_table_v1/code/basic_table`
- 输出：`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1`

## 1. 口径说明
- **time**：`time = event.local_ts`（取消 legacy `+8h(ns)` 偏移）。
- **md_id**：与 v0 保持一致（`order/trans.biz_index`）。
- **其余字段/计算**：与 v0 保持一致（ask/bid/mid/spread/micro/last_trade_price、bar_tag/cum 口径不变）。

## 2. 产出规模（10天）
- parquet 文件数：10
- 总行数：120,297,317
- 总大小：4.78GB

## 3. QC 摘要（10天）
- Schema：PASS（列齐全、dtype 与预期一致；额外列为 0）。
- event_type 分布：
  - order: 63,058,228 (52.4186%)
  - trade: 23,581,607 (19.6028%)
  - cancel: 33,657,482 (27.9786%)
  - order_modify: 0 (0.0000%)
- double 列 NaN 比例：
  - ask1: 901/120,297,317 = 0.0007%
  - bid1: 25,140/120,297,317 = 0.0209%
  - mid: 26,036/120,297,317 = 0.0216%
  - spread: 26,036/120,297,317 = 0.0216%
  - micro_price: 26,036/120,297,317 = 0.0216%
  - last_trade_price: 646,881/120,297,317 = 0.5377%

## 4. 与 v0 的数据一致性校对
### 4.1 v0(parquet) vs v1：逐文件精确一致（仅允许 time shift）
- compared_days: 10, ok: 10, bad: 0, missing: 0
- time_shift_ns(min/max on ok days): 28800000000000/28800000000000（期望为 28800000000000）
- 结论：**v1 在 parquet 数据源下，与 v0 逻辑完全一致；差异仅为 time 口径调整。**

### 4.2 现网 v0(csv历史产物) vs v1：行数存在系统性差异
- compared_days: 10, ok: 0, bad: 10, missing: 0
- v0(csv) 相对 v1 的行数：extra_days=10, missing_days=0, extra_total=65,355, missing_total=0
- 结论：**差异来自数据源/loader（v0 历史产物为 csv loader；v1 为 parquet loader + run-agent）。**
- 进一步定位：这 65,355 行**全部**是 `event_type=trade` 且 `exchange_ts` 落在 **15:00**（收盘集合竞价/尾盘撮合）这一分钟的记录；连续交易时段（09:30-11:30, 13:00-14:57）两边逐日行数完全一致。
- 明细见 compare JSON/MD：
  - `HFTPool/pool/basic_data/basic_table_v1/report/compare_v0parquet_v1_20250102_20250115.json`
  - `HFTPool/pool/basic_data/basic_table_v1/report/compare_v0csv_v1_20250102_20250115.json`

## 5. 建议
- 后续 Analyzer2/因子验收，建议以 `basic_table_v1` 作为“Playground 新口径底表”。
- 若必须与旧产物（csv 口径）对齐，需要明确是否继续保留 csv loader 的额外事件；否则应以 parquet 口径为准。
