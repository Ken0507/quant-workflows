# FactorAgent8 Issues

## [2026-01-23 18:05:30 UTC+8] Step3 磁盘空间约束导致的流程调整

- 现象：`factor_agent_008` tick 级 parquet 单日约 4–7GB；若全历史 20250102-20250730 全量保留 tick parquet，/data 可能不足以支撑后续 Analyzer2 cache + LGBM memmap/model 等产物落盘。
- 临时处理：采用“分段构建 Analyzer2 bar-cache（entrust_1m_v1）→ 清理已被 cache 覆盖的历史 tick parquet（仅删自己 factorset）”以释放空间；Jan/Feb 已按该策略执行。
- 影响：原先计划在 Step3 结束后对全历史 tick parquet 跑一次性 `check_full_history_coverage.py`（basic_table vs factorset 行数对齐）将不可直接复现。
- 解决方案：后续改为以“Analyzer2 cache 覆盖日期集合 + 关键 cache 文件存在性/条数”做全历史覆盖验收，并在需要时按月对未清理的 tick parquet 做行数对齐抽检（保证全 code、全交易日口径不变）。

## [2026-01-23 19:18:10 UTC+8] Analyzer2 cache 全空（time_key 误判导致 join 失败）

- 现象：`fa8_new_only` 与 `fa8_merged_with_baseline_top80` 的 Analyzer2 `cache/*.parquet` 行数均为 0，导致后续标准报告与 LGBM 训练无法进行。
- 根因（进一步确认）：存在严格 +8h 偏移：`time_basic - time_factor == 28800s`；若强制覆盖 `time_key=local_ts` 但不做 +8h 修正，会导致 bar 模式 join 失败→cache 全空。
- 处理：取消脚本中对 `HFT_ANALYZER2_FORCE_TIME_KEY` 的强制覆盖，改为让 Analyzer2 自动识别“+8h 偏移”并在构建 cache 时对 factor_time 做修正。
- 状态：已用 20250312 单日验证 new-only cache 非空；后续全历史 cache 构建按该口径执行。

## [2026-01-23 21:39:10 UTC+8] “因子 time 与 basic_table time 严格 +8h 偏移”的处置口径

- 背景：存在严格 `time_basic - time_factor == 28800s`（ns 级对齐），若不修正会导致 Analyzer2 bar 模式 join 失败或 coverage 极低。
- 冲突点：ResearchDoc/Skill 要求 factorset 输出 `time=event.local_ts`；用户希望“手动把因子 time 偏移 8 小时后再刷数/出报告”。
- 采用方案（不改因子输出，改分析侧对齐）：保留 factorset 输出 `time=event.local_ts`，由 Analyzer2 内置 `_infer_time_key_and_shift` 在 build cache 时自动识别并修正 `factor_time_shift_ns=+8h`（等价于先把因子 time +8h 再与 basic_table join）。该方案可保持工程口径不变，同时保证 Analyzer2/合并 baseline/LGBM 的时间轴一致性。

## [2026-01-24 01:22:05 UTC+8] Step3 长任务会话退出与空目录残留

- 现象：全历史刷数过程中，`playground run-agent` 与 cache watcher 会话均发生退出；factorset 目录残留多个“仅有日期目录、内部无 parquet”的空目录，导致后续 cache 覆盖停滞。
- 影响：需要重新刷数，且必须先清理空目录避免复跑策略混乱（同一路径下混写/误判已完成）。
- 临时处理：
  - 仅删除本 agent factorset 下“无 parquet、无其它文件”的空日期目录；
  - 重新启动 `playground run-agent --date 20250409-20250730 --universe bond_sz --workers 8`；
  - 重新启动 watcher，并增强 watcher：若 cache 已存在但由于重跑导致 tick parquet 残留，则自动清理该日 tick 目录以避免磁盘占用。

## [2026-01-24 17:49:49 UTC+8] Step3 并发刷数内存峰值超限（>180GB）导致的降载

- 现象：在补齐缺口交易日时，`run_fa8_factor` 15 个交易日并行（13 个早期缺口 + 2 个 `20250310-20250311`）导致 RSS 总和上升到 ~190GB，同时 Swap 占用上升，违反“硬上限 <180GB（目标 ≤160GB）”约束。
- 处理：中止 `20250310-20250311` 的 run-agent/子进程，把并行交易日数回退到 13（RSS 总和回落到 ~170GB）。
- 后续：待早期批次完成后，以 workers<=2 的低并发重刷 `20250310-20250311`，并继续补齐 20250716-20250730 缺口；整个过程持续监控 RSS/Swap。

## [2026-01-24 17:54:39 UTC+8] Step3 并发刷数 RSS 再次逼近 180GB 的二次降载

- 现象：回退到 13 个交易日并行后，`run_fa8_factor` RSS 仍继续上升到 ~177GB，距离 180GB 硬上限 buffer 过小，且后续还需要 watcher/build cache/report/LGBM 占用。
- 处理：中止 `20250219-20250221`（3 个交易日）run-agent/子进程，将并行交易日数降到 10（`20250224-20250228` + `20250303-20250307`），RSS 总和回落到 ~140GB。
- 后续：待当前 10 个交易日完成后，使用 workers<=2 低并发补齐被中止的 `20250219-20250221` 与 `20250310-20250311`，再推进 20250716-20250730 缺口；全程监控 RSS/Swap。
