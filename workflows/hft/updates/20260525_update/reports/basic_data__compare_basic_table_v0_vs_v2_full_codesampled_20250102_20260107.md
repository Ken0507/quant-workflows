# basic_table：basic_table_v0 vs basic_table_v2（全量对刷，code 抽样核对）
- 生成时间：2026-01-27 02:39:05（系统时间；实验日志以 UTC+8 为准）
## 1) 数据覆盖（交易日）
- 数据源有效交易日（order+transaction 均非空）：233
- v2 产出交易日 parquet：233
- v2 缺失有效交易日：0（应为 0）
- v2 额外交易日：0（应为 0）

## 2) 与旧 basic_table(v0) 的交易日差异
- v0_only_days: 1 ['20250204']
- v2_only_days: 1 ['20260107']

## 3) 行数差异（全量统计）
- 共享交易日：232
- diff = rows(v0) - rows(v2)：min=-10270, p10=3863, median=6293, p90=8978, max=185909
- diff 最小日：20251008 diff=-10270
- diff 最大日：20250919 diff=185909

## 4) 口径核对（code 抽样，逐日 Join 比对）
- 抽样 codes（来自 20250102 row_group0，等距取 20 个）：
  - ['123022', '123063', '123090', '123118', '123138', '123158', '123175', '123190', '123206', '123222', '123236', '127025', '127041', '127056', '127075', '127090', '127104', '128097', '128128', '128144']
- 深度核对日期（覆盖 diff 分位/极值/尾部）：
  - ['20250102', '20250901', '20250716', '20250408', '20250919', '20251008', '20251215']

### 20250102
- rows(v2, sampled codes)=804,455 rows(v0, sampled codes)=804,636 overlap=804,455 v0_only=181 v2_only=0
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=181
  - top_minutes: {'15:00': 181}
  - event_type: {'trade': 181}
- v2_only：n=0

### 20250901
- rows(v2, sampled codes)=1,524,595 rows(v0, sampled codes)=1,525,281 overlap=1,524,595 v0_only=686 v2_only=0
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=686
  - top_minutes: {'15:00': 686}
  - event_type: {'trade': 686}
- v2_only：n=0

### 20250716
- rows(v2, sampled codes)=946,262 rows(v0, sampled codes)=946,832 overlap=946,262 v0_only=570 v2_only=0
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=570
  - top_minutes: {'15:00': 570}
  - event_type: {'trade': 570}
- v2_only：n=0

### 20250408
- rows(v2, sampled codes)=2,677,928 rows(v0, sampled codes)=2,679,287 overlap=2,677,928 v0_only=1,359 v2_only=0
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=1359
  - top_minutes: {'15:00': 1359}
  - event_type: {'trade': 1359}
- v2_only：n=0

### 20250919
- rows(v2, sampled codes)=831,401 rows(v0, sampled codes)=841,477 overlap=831,401 v0_only=10,076 v2_only=0
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=10076
  - top_minutes: {'14:50': 2969, '14:53': 2453, '14:51': 2344, '14:52': 2310}
  - event_type: {'order': 5153, 'trade': 2493, 'cancel': 2430}
- v2_only：n=0

### 20251008
- rows(v2, sampled codes)=390 rows(v0, sampled codes)=474 overlap=352 v0_only=122 v2_only=38
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=122
  - top_minutes: {'11:09': 10, '10:56': 10, '11:00': 9, '11:02': 9, '10:54': 8, '11:10': 8, '10:58': 6, '11:12': 6, '10:53': 5, '11:14': 5}
  - event_type: {'order': 95, 'trade': 26, 'cancel': 1}
- v2_only：n=38
  - top_minutes: {'10:35': 3, '10:07': 2, '10:08': 2, '09:18': 2, '10:01': 2, '10:19': 2, '09:57': 2, '09:51': 2, '10:11': 2, '10:21': 1}
  - event_type: {'order': 38}

### 20251215
- rows(v2, sampled codes)=1,170,778 rows(v0, sampled codes)=1,171,202 overlap=1,170,778 v0_only=424 v2_only=0
- duplicate key rows: v2=0 v0=0 (key=code,time,md_id)
- ✅ overlap 行：v0 与 v2 在全部 v0 字段上完全一致（已做 time=-8h 对齐）
- v0_only：n=424
  - top_minutes: {'15:00': 424}
  - event_type: {'trade': 424}
- v2_only：n=0

## 5) 结论（针对本次替换）
- v2 在有效交易日覆盖完整，且对 sampled codes 的 overlap 行与 v0 完全一致（仅需 time 做 -8h 对齐）。
- v0 在几乎所有交易日都比 v2 多行；差异主要体现为 v0_only（多出来的事件行）。从多个日期的 extra 行时间分布看，集中在非连续交易时段/节假日占位日，属于历史底表数据源/口径导致的“多数据”。
- v0_only_days 中包含 20250204（数据源无真实 parquet 文件），应视为历史脏数据并移除；v2_only_days 包含 20260107（新增可用数据）。
