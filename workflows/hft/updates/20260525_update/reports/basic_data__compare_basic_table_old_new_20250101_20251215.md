# basic_table 新旧数据一致性对比报告

- old_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_old`
- new_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table`
- date_range: 20250101–20251215
- compare_mode: `left_subset`（old->new 时建议用 left_subset，忽略 new 新增列）
- batch_size: 500000

## 1. 总结
- old_dates: 232
- new_dates: 233
- missing_dates_in_new: 0
- extra_dates_in_new: 1
- compared_files: 232
- ok: 232
- bad: 0
- missing_entries: 0
- total_old_bytes: 79.34GB
- total_new_bytes: 134.48GB

## 4. 备注
- 该对比按行序与值做逐 batch 精确比较（浮点允许 NaN==NaN）。
- 若 compare_mode=left_subset：要求 old 的列在 new 中都存在，并仅比较 old 列；new 新增列不参与一致性判断。

