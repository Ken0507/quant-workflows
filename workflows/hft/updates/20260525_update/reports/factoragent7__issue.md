[2026-01-23 04:22:10 UTC+8]
## Step2 强验证发现异常：`GetSnapshot()` 深档可能未填充导致极端值

### 现象
- 在 `20250102-20250127` 全 code 全量数据上做月度统计时，出现极端值：
  - `fa7_micro_gap_bps_3` max ~ 1e14 bps
  - `fa7_micro_queue_gap_bps_3` max ~ 1e10 bps
  - `fa7_eff_gap_bps` max ~ 1e12 bps
- 分位数（1%/50%/99%）均在合理范围（约 ±10bps），说明问题集中在极少数异常 tick。

### 根因判断
- `HftKnowledge/research_docs/data.md` 已提示：`GetSnapshot()` 的深档（以及在某些情况下的缺失档位）可能出现“离谱数值”，需要先判断档位有效性。
- 当前实现对 `GetSnapshot()` 的档位有效性判断不足，可能在“档位缺失但数组残留垃圾值”的情况下，将异常 price/vol 纳入计算，导致 micro 系列与基于 mid 的 bps 值爆炸。

### 临时处理/修复方向（将回到 Step1）
1) 不再直接依赖 `GetSnapshot()` 的 Lk 价量，改为从 `GetFullBidBook/GetFullAskBook` 提取 TopK（确保价位真实存在）。
2) mid/best bid/ask 改为使用 `OrderBook::GetBestBid/GetBestAsk`（避免 snapshot 不一致）。
3) 重新刷 1 个月数据并重做强验证，确认极端值问题闭环。

[2026-01-23 06:09:50 UTC+8]
## Step3 全历史刷数中断：BatchRunner 退出码非 0

### 现象
- 执行全历史刷数（`20250102-20250730`，`bond_sz` 全 code，workers=16）过程中，BatchRunner 进程退出码为 1。
- 输出目录：`/data/db/hft/factor_pool/debug/FactorAgent7/factor_agent_007/`
  - 已生成部分交易日的 parquet（截至目前可见到 `20250220` 的输出）
  - 之后若干日期目录存在但缺少 parquet（目录为空），疑似在某个交易日子进程失败后整体中断。

### 影响范围
- Step3.1 全历史数据集不完整，无法继续 Step3.2/3.3 两份 Analyzer2 报告与 Step4 LGBM uplift 对比。

### 临时处理/下一步
1) 定位失败交易日：优先从第一个缺失但应为交易日的日期开始（例如 `20250221`），单日单进程复跑以获取错误信息。
2) 复现后判断原因：
   - 若为数据缺失/损坏：按文档口径记录并将该日从分析范围中剔除（与 baseline 交集对齐）。
   - 若为代码/资源问题：修复后从失败日继续补刷缺失日期（不覆盖已生成日期）。

### 最新进展（已确认）
- `20250221` 单日全 universe（`bond_sz`）单进程复跑**可成功完成**，但该日单进程 RSS 峰值约 19GB（显著高于此前 20250102 的 ~3.3GB）。
- 推断：Step3 中断更可能与“峰值资源/并发组合”有关（而非该日数据必然损坏）；后续将采用“分段日期范围 + 降并发（workers≤6~8）”的方式补刷并持续验收。

[2026-01-23 13:59:46 UTC+8]
## Step3 分段 `20250401-20250430` 早停 + parquet 损坏（需补刷）

### 现象
- 触发分段刷数：`20250401-20250430`（`bond_sz` 全 universe，workers=6），刷数进程结束后发现该段数据不完整：
  - `20250401/02/03/07/08/09` parquet 正常
  - `20250411` parquet 文件存在但 **损坏**（pyarrow 报错：Parquet footer magic bytes 不存在）
  - `20250410, 20250414-20250430` 等多个交易日缺失 parquet（仅有空目录）

### 影响范围
- Step3 全历史数据集在 `202504` 段不完整，无法进入 Analyzer2 两份标准报告与 LGBM uplift。

### 初步判断
- BatchRunner stdout 未落盘（进程结束后会话输出不可回溯），无法直接确认失败点/失败原因。
- 已通过脚本验收定位：
  - `fa7_check_factor_pool_output.py`（已增强为可识别 corrupted parquet）显示 `20250401-20250430` expected_days=21，missing_days=14，corrupted_days=['20250411']。
- 同段运行期间观测单进程 RSS 峰值约 27GB，workers=6 时内存裕度变小；不排除资源/IO/异常退出导致某日写 parquet 中断。

### 临时处理/下一步
1) 清理本段缺失/损坏日期目录（仅清理自己产物）：删除 `20250410`、`20250411`、`20250414-20250430` 这些缺失/损坏日期目录（避免后续复跑混写/误判）。
2) 从 `20250410-20250430` 重新分段补刷（建议 workers 下调到 5），并将 stdout/stderr 重定向到日志文件以便定位真实失败原因。
3) 补刷完成后用 `fa7_check_factor_pool_output.py` 再次验收该段（missing_days=0 且 corrupted_days=0）后再继续后续月份。

[2026-01-23 18:37:12 UTC+8]
## Step3 Analyzer2 标准报告：workers 估算偏小导致内存超限（已中止并调整）

### 现象
- 执行 Analyzer2 标准报告（FA7 new-only，bar 模式）时，按 workers=20 启动。
- 运行期间通过 `ps` 统计 `run_analyzer2_fa7_new_only.py` 相关进程 RSS 之和约 **340GB**，超过本任务硬上限 180GB（目标 ≤160GB）。

### 影响范围
- 当前 Analyzer2 任务需中止并降低并发，否则违反内存硬约束且有 OOM/系统不稳定风险。

### 初步判断
- 单 worker 峰值内存显著高于保守估计，推断每个 worker 在按日处理时会把当日大 parquet（~2-3GB）解压/中间 join 后占用 ~15GB+ 的 RSS。

### 临时处理/下一步
1) 立即中止该次 Analyzer2 运行（`pkill -f run_analyzer2_fa7_new_only.py`），避免继续占用超限内存。
2) 将 Analyzer2 workers 下调到 **8**（必要时进一步降到 6），并重新生成报告。
3) 由于工具沙箱限制无法在本次会话中删除 `/data/db/hft/analyzer2/...` 的半成品目录，重跑时将使用新的 `report_version` 避免“拒绝覆盖”。

[2026-01-23 18:41:13 UTC+8]
## Step3 Analyzer2 标准报告：workers=8 仍出现峰值超限（已再次下调）

### 现象
- new-only 标准报告改为 `workers=8` 重跑后，运行中期统计 RSS 合计约 **206GB**，仍超过硬上限 180GB。

### 临时处理/下一步
1) 再次中止该次运行，避免继续违反资源约束。
2) 将并发进一步下调到 `workers=6`（若仍偏高则降到 5），再重新生成报告。

[2026-01-23 19:13:17 UTC+8]
## Step3 Analyzer2 标准报告：join_rows=0（FA7 `time` 与 basic_table `time` 存在 +8h 偏移）

### 现象
- new-only 标准报告 cache 每日 parquet 为 0 行空表，最终 `generate_standard_report` 读取 cache 时提示缺失 signals 列。
- `error_reports/{ds}.json` 显示：
  - `join_rows=0` / `join_ratio=0.0`
  - `time_key=exchange_ts`
  - `join_keys=[code,time,md_id]`

### 根因判断
- 对照 basic_table 与 FA7 输出发现：在同一交易日内，FA7 `time` 与 basic_table `time` 存在 **严格 +8h（28800s）** 偏移，导致 Analyzer2 的 time_key 启发式推断选择 `exchange_ts`，但 FA7 的 `time` 并不与 basic_table `exchange_ts` 对齐，从而全量 join 失败。

### 临时处理/修复方向（已执行）
- 为避免重刷 139 天 factor_pool（磁盘与复跑风险较大），在 `HftAnalyzer2` 内做最小修复：
  - 自动识别 `factor_time + TZ_SHANGHAI_OFFSET_NS ~= basic_time`，并在 join 前对 factor `time` 做 `+8h` shift，再按 `local_ts` join。
  - 单数据集标准报告与多数据集 cache（bar/tick）均覆盖。
  - 更新 `HftAnalyzer2/docs/changelog_zh.md`（`v20260123.1`）。

[2026-01-23 19:24:58 UTC+8]
## Step3 Analyzer2 标准报告：workers=6 在有效 join 后出现内存超限（已下调）

### 现象
- 在 time shift 修复后，new-only 标准报告以 `workers=6` 运行时，RSS 随处理进度上升至约 **185GB**，超过硬上限 180GB。

### 临时处理/下一步
1) 中止该次运行，避免继续违反资源约束（cache 已生成部分日期，留作参考但不用于最终交付）。
2) 并发下调至 `workers=5`（必要时降到 4）并以新 `report_version` 重跑，确保全程 RSS <180GB。

[2026-01-23 20:09:12 UTC+8]
## Step3 合并报告 cache 样本异常偏小（原因：多数据集合并 join_keys 过严）

### 现象
- baseline top80 + FA7 合并 cache（bar 模式）在部分交易日出现样本数异常偏小：
  - 例如 `20250102/20250103/20250108` 等 cache 仅 0~1 行
  - 但 `20250107/20250114` 等日期 cache 正常（十万级行数）

### 初步判断
- 多数据集合并默认 join_keys 继承 AnalyzerConfig 默认值 `(\"code\",\"time\",\"md_id\")`；
- 不同 factor_set 的 `md_id` 口径可能不一致（或在部分日期不稳定），导致 join 过严 → 某些日期大量信号无法挂到共同样本轴，最终在 multi-cache 的“全信号 finite”筛选阶段样本塌陷。

### 临时处理/下一步
1) 中止该次合并缓存构建，避免继续产出不可用 cache。
2) 合并 cache 重跑时显式设置 `join_keys=(\"code\",\"time\")`，并换新 `report_version` 重新生成（保留 `md_id` 作为字段但不参与 join）。

[2026-01-23 20:35:25 UTC+8] Step3.3 合并报告 cache 样本塌陷（Agent1/agent2 数据集）
- 影响：multi-dataset cache 部分日仅 0~12 行，导致合并报告与后续 LGBM uplift 无法完成。
- 根因：HftAnalyzer2 `_infer_time_key_and_shift` 使用文件头部 2000 行做时间轴推断，遇到 factor/basictable 文件起始时间错位时误判 local_ts(+8h shift)。对 `time`=exchange_ts(ms) 的旧数据集会与 basic_table.time(ns) 精确 join，导致 join 失败。
- 修复：在 `_infer_time_key_and_shift` 增加 “ms 精度优先判定 exchange_ts” 的规则；修复后将重跑 Step3.3。
