# FactorAgent3 问题记录（UTC+8）

> 说明：执行过程中若出现阻塞/不确定点（定义冲突、数据缺失、工具异常、资源超限等），按要求记录到此文件：包含时间（UTC+8）、问题点、影响范围与临时处理。

## 记录

- [2026-01-22 07:04:03 UTC+8] 口径变更与对齐修复说明（旧问题作废）
  - 说明：用户已确认 `bs_flag/side` 字段不可用，并授权改用 `bid_id/ask_id` 推断主动方；因此此前基于 `trade_bs_flag` 的问题记录与旧报告均 **作废**（保留仅用于过程追溯）。
  - 同步修复（对齐 `basic_table` 基础字段）：
    - `time`：对齐 `basic_table` legacy offset（`event.local_ts + 28800000000000(ns)`）
    - `md_id`：对齐 `basic_table`，使用 `order/trans.biz_index`
    - `exchange_ts`：作为普通字段输出，便于 join/排查
  - 仍需持续监控的差异：
    - `basic_table` 历史上由 csv loader 口径生成，Playground `run-agent`=parquet loader 会出现极少量 missing tick（例如单标的单日缺 4 行的重复 trade）。已在月度强验证中加入 `axis_ratio` 与 key-set spot-check 监控。

- [2026-01-22 02:15:55 UTC+8]（OBSOLETE）交易方向字段缺失导致核心簇输出退化为 0
  - 现象：
    - 原始 transaction parquet（例如 `.../transaction/20250603/bond_sz_093000.parquet`）中 `bs_flag` 近乎全为 `\\0`，`side` 也为 0（UNKNOWN）
    - 因 SDK `TransData.trade_bs_flag` 无法得到 `'B'/'S'`，按文档硬规则 `sign=0` → 本任务中所有依赖方向的更新（micro-batch/run/realized spread/inv pressure/efficiency/penetration）均会跳过，最终大多数 `fa3_*` 信号长期为 0
  - 影响范围：
    - Step2 强验证虽然能“公式=实现”通过，但信号分布退化（zero_ratio≈1），后续 Analyzer2/LGBM 预期难有提升
  - 备注：该问题已由“改用 `bid_id/ask_id` 推断主动方”口径变更解决，旧口径不再使用。

- [2026-01-22 03:38:43 UTC+8]（OBSOLETE）Analyzer2(bar) 0 join_rows：因子时间键与 basic_table 对齐失败
  - 现象：
    - 运行 Analyzer2 `sample_mode=bar` 时，`error_reports/{ds}.json` 显示 `join_rows=0`、`join_ratio=0`
    - 触发原因：Analyzer2 会在 `basic_table.time` 与 `basic_table.exchange_ts` 之间推断 `time_key`；对本因子集而言推断为 `exchange_ts`，从而按 `(code,time,md_id)` 将因子表的 `time` 与 basic 的 `exchange_ts` 对齐。
    - 当前因子输出 `time=event.local_ts`（满足执行指令硬规则），但 `local_ts` 与 `exchange_ts` 存在 ~1s 级别偏移，导致**精确 join 全部失败**。
  - 备注：已统一按 `basic_table` 口径修复（time legacy offset + md_id=biz_index + 输出 exchange_ts），旧 join_rows=0 问题不再成立。

- [2026-01-22 05:34:15 UTC+8]（OBSOLETE）new-only Analyzer2 报告“数值不合理”与单日文件体积偏小（根因再确认：trade_bs_flag 全缺失 → 信号常数化）
  - 现象：
    - `/home/cken/hft_projects/HFTPool/pool/FactorAgent3/report/analyzer2_report_new_only/report.md` 中：
      - 大多数信号 `RankIC≈0`，`IC` 大量为 `NaN`，Top tail return 近乎相同（看起来“不合理”）
    - 单日因子 parquet 体积：`~60–80MB/天`，显著小于对照集合（例如 `Agent3/agent3_step1_sig60_v4_shape_full_20260116` 单日约 `3–6GB/天`）。
  - 快速复核证据：
    - new-only Analyzer2 cache（bar 采样）内：多数 `fa3_*` 列在整日范围 `nunique==1`（几乎全为 0；`fa3_book_valid` 为 1）。
    - 原始 transaction 数据（多日抽查 `20250102/20250304/20250610/20250730`）：
      - `bs_flag` **全为 `\\0`**（NUL），`side` 也全为 0（UNKNOWN），导致 `trade_bs_flag` 无法得到 `'B'/'S'`。
  - 解释：
    - 本任务定义（FactorAgent3 文档 §1.1/§9）要求：`sign` 只用 `trade_bs_flag`，否则 `sign=0` 且跳过更新（严禁推断）。
    - 因此在该数据版本下，绝大多数依赖 sign 的簇会长期保持初始值（0），从而：
      - parquet 压缩比极高（体积显著变小）
      - Analyzer2 单因子/组合因子指标退化（难有可解释信号）
  - 备注：口径已切换到 `bid_id/ask_id` 推断主动方，本问题所述“信号常数化”预计不再出现；后续以新版月度强验证/Analyzer2/LGBM 结果为准。
