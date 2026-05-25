# FactorAgent3 阶段反馈（阻塞点 / 耗时点 / 口径不清晰点）

- [2026-01-22 05:51:46 UTC+8] 本文件用于记录本次任务执行过程中的阻塞与口径问题，供后续流程/文档改进与复盘。
- [2026-01-22 07:03:16 UTC+8] 更新：在用户确认 `bs_flag/side` 不可用后，已改为使用 `bid_id/ask_id` 推断主动方，并将旧报告/旧验证产物全部作废重做；同时补齐了 basic_table 对齐相关的口径与验证闸门。

## 1) 曾经 block 进度 / 需要返工的点（按影响排序）

### 1.1 Analyzer2(bar) `join_rows=0`：time_key 推断与 `time=local_ts` 冲突

- 触发：首次跑 Analyzer2（bar 模式）时，`error_reports/{ds}.json` 显示 `join_rows=0`、`join_ratio=0`，导致整份报告无法生成有效结果。
- 根因：Analyzer2 会在 `basic_table.time` 与 `basic_table.exchange_ts` 间推断 `time_key`。对本因子集推断为 `exchange_ts`，并用 `(code,time,md_id)` 将因子表与 basic_table 精确 join；但因子表 `time=event.local_ts`（硬规则），与 `exchange_ts` 存在秒级偏移，导致精确 join 全部失败。
- 修复（不违反硬规则）：在因子输出新增 int64 列 `exchange_ts=event.exchange_ts`；Analyzer2 在 `time_key=exchange_ts` 时会用该列替换 join 用的 `time`，从而恢复对齐。
- 代价：需要回到 Step1 修改代码并**重刷全历史**（否则旧 parquet 无 `exchange_ts` 列），工期损耗显著。

### 1.2 Analyzer2 内存硬上限 <100GB：多次降并发重跑

- 触发：Analyzer2 标准报告在 bar 模式（`downsample=1`）下，workers 过大时 RSS 超过硬上限：
  - `workers=12` → RSS 约 124GB（超限）
  - `workers=8` → RSS 约 106GB（仍超限）
- 处理：中止并归档半成品目录（目录不可覆盖且环境不允许直接删除时，使用 `mv` 隔离）；最终 `workers=6` 才在 <100GB 内稳定完成。
- 影响：多次中止/重跑耗时较大；建议文档提供更明确的 workers/内存估算与推荐区间，并提示同步下调 LGBM `n_jobs`。

### 1.3 交易方向字段缺失：`trade_bs_flag` 无法提供 `'B'/'S'`（导致信号退化）

- 现象：
  - new-only Analyzer2 报告中，各信号 `RankIC≈0`，`IC` 大量为 `NaN`，Top tail return 近乎一致，看起来“完全不合理”。
  - Analyzer2 bar-cache 内多数 `fa3_*` 列 `nunique==1`（常数：大多为 0；`fa3_book_valid` 为 1）。
  - factor_pool 单日 parquet 体积显著偏小（~60–80MB/天），与对照集合（例如 Agent3 的 60sig 单日 3–6GB）差距巨大。
- 根因定位（已核实）：源 transaction 数据 `.../transaction/{ds}/bond_sz_*.parquet` 中 `bs_flag` 在多日全量抽查均为 `\\0`（NUL），`side` 也全为 0（UNKNOWN），导致基于 `trade_bs_flag/side` 的方向无法使用。
- 返工点：一开始严格按旧口径“方向缺失则 sign=0 且不推断”，会导致依赖方向的簇长期不更新 → 大量信号常数化（0/1）→ 文件显著变小、Analyzer2 指标退化。
- 已采取的解决方案（用户显式授权的口径变更）：
  - 改用 `bid_id/ask_id` 推断主动方：id 更大的一方为主动方（`bid_id>ask_id => +1`；`ask_id>bid_id => -1`；否则 0）。
  - 所有依赖方向的信号逻辑统一切换到该规则，并重刷（旧报告/旧验证全部作废）。

### 1.4 basic_table 对齐口径不一致：`md_id` 与 `time` 的“隐含 legacy 规则”

- 现象：按 data.md 的“推荐写法”使用 `GetMdId()` 与 `time=event.local_ts` 输出后，发现与 `/data/db/hft/factor_pool/debug/basic_data/basic_table` 的 `(time,md_id,exchange_ts)` 无法逐行对齐（出现大量 key mismatch）。
- 根因：`basic_table` 工程中：
  - `md_id` 取 `order/trans.biz_index`（非 `GetMdId()`）
  - `time` 取 `event.local_ts + 28800000000000(ns)` 固定偏移（legacy offset）
- 修复：本因子输出同步对齐上述口径（并在验证脚本中加入 axis 对齐检查），避免后续 Analyzer2/LGBM join 轴错位。

### 1.5 parquet vs csv loader 的“极少量事件差异”（导致少量 missing tick）

- 现象：在单日单标的对齐检查中，因子输出（Playground `run-agent`=parquet loader）相对 `basic_table`（历史上由 csv loader 口径生成）存在极少量 missing 行（例如 `20250730/127053` 缺 4 行，且是 csv-only 的重复 trade 事件）。
- 影响：missing 占比极低，但若不显式监控，容易被误解为“没逐 tick 输出/没全 code”。
- 应对：
  - 在月度强验证中增加按日 `axis_ratio` 与抽样 code 的 key-set spot-check，确保缺失规模可解释且可控。

### 1.6 工具/环境限制：目录不可直接删除导致“归档式清理”

- 现象：Analyzer2 与 factor_pool 产物目录默认拒绝覆盖；同时运行环境对删除目录存在限制（无法 `rm -rf` 清理）。
- 处理：使用 `mv` 将旧目录/半成品统一加 `__ABORTED__/__bak__` 后缀归档隔离。
- 影响：目录路径管理复杂度上升，必须在 `research_log.md` 中维护清晰的“源目录/交付目录/归档目录”索引，避免误用旧产物。

### 1.7 run 指标数值病态：`run_intensity` 在 run 启动 tick 被 `ε` 放大到 `1e18`

- 触发：用户反馈“报告数值明显错误”；进一步从 Analyzer2 `cache/*.parquet` 侧直接看分布发现 `fa3_run_intensity`/`fa3_run_intensity_fast/slow` 出现 `1e18` 量级极端值，污染分位数切分与 LGBM。
- 根因：run 刚启动时 `run_duration_sec≈0`，而实现中用 `run_amt/(duration + 1e-9)` 防除零，导致首笔成交被除以极小值 → 人为放大到 `1e17~1e18`。
- 修复：把 run duration 引入明确 `dt_floor`（对齐项目中其他 rate 类实现），改为 `dur_sec=DtSec(now, run_start, 1e-3)`，并同步修复 `run_intensity_fast/slow` 的 EMA 输入。
- 教训：这类问题点对点复算（p2p）无法发现（复算会复用同一错误口径），必须加入“数量级/极端值”闸门与 cache 分布验收。

### 1.8 /home 分区满导致验证写盘失败（Errno 28）

- 触发：`validate_1m.py` 需要落盘 `downsample_1over20/*.parquet`（用于 spot-check 与 p2p 抽样），但 `/home` 分区已满，出现 `OSError: [Errno 28] No space left on device`。
- 处理：不改因子数据，仅把强验证中间产物输出目录迁移到 `/data/db/hft/tmp/...`（空间充足），并在交付中保留最终 `data_validation_1m.md`（小文件）在 `/home` 交付目录。
- 建议：后续把“中间大文件默认落在 /data”写入 ResearchDoc/Skill，避免 agent 反复踩磁盘空间问题。

### 1.5 “Skill 要求用户确认”与“执行指令禁止对话”存在冲突

- 冲突点：
  - Skill 文档要求在给出可执行命令前“复述要点并让用户确认”；
  - 本次执行指令要求“禁止中断与对话/提问”。
- 临时处理：以可复现与不偏离口径为第一优先级，按 Skill/ResearchDoc 完整阅读并执行，同时在 `research_log.md` 明确记录该冲突与采取的处理策略（不做互动确认）。

## 2) 花了很多时间才澄清/修正的点

- “文件大小 vs 是否全 code”误判风险：
  - 文件大小不能作为“是否全 code”的可靠判据（常数列/低熵列会导致压缩比极高）。
  - 更可靠的验收是：`unique_codes`、行数、交易日覆盖性、与源数据 `bond_sz_*` 文件列表/数量交叉验证。
- baseline top80 的合并口径复杂：
  - baseline top80 是跨多个 agent 数据集组合而来，合并必须严格走 Analyzer2 第 6 章 multi-dataset 流程（`build_multi_dataset_cache` → `generate_standard_report(reuse_cache=True)`）。
  - signals 映射、同名冲突、`date_mode`、cache 复用等细节需要额外脚本与校验，准备与排查成本较高。

## 3) 口径不统一/不清晰（建议补文档的点）

1) `time=local_ts` 与 Analyzer2 join：建议在“因子输出规范”中明确要求**同时输出 `exchange_ts` 列**作为兼容字段，避免各 agent 反复踩坑。  
2) `basic_table` 的 `md_id/time` 口径：建议在 `data.md`/workflow 中显式写明 legacy offset 与 `biz_index` 规则，避免“按文档写”却对不上底表。  
3) 交易主动方字段缺失时的标准策略：建议对 `trade_bs_flag/side` 缺失制定统一口径（数据修复 or 明确允许某一种确定推断规则），减少返工。  
4) Analyzer2 资源配置指南：建议给出 bar 模式下 workers/n_jobs 与内存的经验推荐区间与估算方法，减少反复中止重跑。  
5) 复跑/隔离策略：当无法删除目录时，建议提供统一的“归档命名规范 + 最小清理步骤”，降低误用旧产物风险。  

## 4) 建议增加的前置检查（减少返工）

- 刷数前（1–2 天全 code preflight）：
  - 检查方向输入字段可用性（例如 `bid_id/ask_id` 非空比例、`bid_id==ask_id` 占比等），并对关键簇信号做 `std/zero_ratio` 诊断；
  - 若关键簇在全量统计 `std=0`（整体常数化）则直接 FAIL，不进入全历史/不出报告。
- 跑 Analyzer2 前（先跑 1–2 天 cache）：
  - 检查 `join_ratio`、bar 过滤后样本量、label 非空比例；
  - 通过后再扩全历史，避免全量运行后才发现 join/口径问题。
