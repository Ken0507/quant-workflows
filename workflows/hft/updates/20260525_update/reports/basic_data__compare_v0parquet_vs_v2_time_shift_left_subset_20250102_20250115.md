# basic_table_v0(parquet) vs basic_table_v2 一致性对比（time shift + left subset）

- v0_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_v0_parquet_20250102_20250115`
- v2_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_v2`
- date_range: 20250102–20250115
- expected_time_shift_ns: 28800000000000（v0_time - v2_time）
- batch_size: 1000000
- workers: 4

## 1. 总结
- compared_days: 10
- ok: 10
- bad: 0
- missing: 0

## 4. time shift 统计（仅 ok 的日）
- min(time_shift_ns_min): 28800000000000
- max(time_shift_ns_max): 28800000000000

