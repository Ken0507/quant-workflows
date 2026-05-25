# basic_table_v0 vs basic_table_v1 一致性对比（time shift）

- v0_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table`
- v1_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_v1`
- date_range: 20250102–20250115
- expected_time_shift_ns: 28800000000000（v0_time - v1_time）
- batch_size: 1000000
- workers: 4

## 1. 总结
- compared_days: 10
- ok: 0
- bad: 10
- missing: 0

## 3. 失败详情（最多 20 条）
- 20250102: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250102/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250102/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=12304263 right=12297878` rows=(12304263,12297878)
- 20250103: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250103/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250103/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=12656074 right=12649519` rows=(12656074,12649519)
- 20250106: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250106/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250106/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=12974084 right=12967702` rows=(12974084,12967702)
- 20250107: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250107/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250107/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=11286784 right=11279389` rows=(11286784,11279389)
- 20250108: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250108/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250108/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=11381441 right=11375935` rows=(11381441,11375935)
- 20250109: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250109/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250109/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=11905762 right=11899148` rows=(11905762,11899148)
- 20250110: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250110/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250110/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=11200752 right=11193981` rows=(11200752,11193981)
- 20250113: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250113/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250113/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=10827810 right=10822438` rows=(10827810,10822438)
- 20250114: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250114/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250114/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=13690388 right=13682283` rows=(13690388,13682283)
- 20250115: left=`/data/db/hft/factor_pool/debug/basic_data/basic_table/20250115/TickFeatureAgent/basic_table_basic_table.parquet` right=`/data/db/hft/factor_pool/debug/basic_data/basic_table_v1/20250115/TickFeatureAgent/basic_table_basic_table.parquet` reason=`row_count_mismatch: left=12135314 right=12129044` rows=(12135314,12129044)

## 4. time shift 统计（仅 ok 的日）
- NA

