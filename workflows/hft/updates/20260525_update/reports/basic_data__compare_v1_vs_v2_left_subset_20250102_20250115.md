# basic_table 新旧数据一致性对比报告

- old_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_v1`
- new_root: `/data/db/hft/factor_pool/debug/basic_data/basic_table_v2`
- date_range: 20250102–20250115
- compare_mode: `left_subset`（old->new 时建议用 left_subset，忽略 new 新增列）
- batch_size: 1000000

## 1. 总结
- old_dates: 10
- new_dates: 10
- missing_dates_in_new: 0
- extra_dates_in_new: 0
- compared_files: 10
- ok: 10
- bad: 0
- missing_entries: 0
- total_old_bytes: 4.78GB
- total_new_bytes: 5.31GB

## 4. 备注
- 该对比按行序与值做逐 batch 精确比较（浮点允许 NaN==NaN）。
- 若 compare_mode=left_subset：要求 old 的列在 new 中都存在，并仅比较 old 列；new 新增列不参与一致性判断。

