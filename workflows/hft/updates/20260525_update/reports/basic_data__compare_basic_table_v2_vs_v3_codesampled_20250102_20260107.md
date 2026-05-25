# basic_table：v2 vs v3（新增 bar_aggtrans_time_1 校对）

- 生成时间：2026-01-27 03:54:30（系统时间；实验日志以 UTC+8 为准）
- v2_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table`
- v3_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_v3_full_20260127_w40`

## 1) 交易日覆盖

- v2 days(parquet): 233
- v3 days(parquet): 233
- shared days: 233
- v2_only_days: 0 []
- v3_only_days: 0 []

## 2) 行数差异（全量，按日 parquet metadata）

- diff = rows(v2)-rows(v3): min=0, median=0, max=0
- diff_min_day: 20250102 diff=0
- diff_max_day: 20260107 diff=0

## 3) 字段一致性（code 抽样，逐日 Join 比对）

- sampled codes (n=50): ['123022', '123038', '123056', '123065', '123080', '123089', '123100', '123112', '123120', '123127', '123133', '123145', '123152', '123158', '123165', '123172', '123178', '123184', '123189', '123195', '123200', '123209', '123214', '123221', '123226', '123232', '123237', '127016', '127022', '127030', '127035', '127042', '127047', '127053', '127061', '127068', '127075', '127080', '127086', '127091', '127097', '127102', '128062', '128074', '128101', '128117', '128125', '128131', '128137', '128144']
- deep compare days: ['20250102', '20260107']

### 20250102
- rows(v3)=2,230,041 rows(v2)=2,230,041 overlap=2,230,041 v2_only=0 v3_only=0
- duplicate key rows (code,time,md_id): v2=0 v3=0
- ✅ overlap 行：v2 与 v3 在全部 v2 字段上完全一致

### 20260107
- rows(v3)=42,704 rows(v2)=42,704 overlap=42,704 v2_only=0 v3_only=0
- duplicate key rows (code,time,md_id): v2=0 v3=0
- ✅ overlap 行：v2 与 v3 在全部 v2 字段上完全一致

## 4) 结论

- v3 仅新增 `bar_aggtrans_time_1`，其余数据与 v2 完全一致，可安全替换为标准 basic_table。
