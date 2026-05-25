# FA28 Issue Log

> 用于记录工程实现过程中无法立即解决、需后续讨论的问题。

---

## 2026-04-29 14:30 (UTC+8) — Iter-3 修复后状态

### 已修复（CLOSED — Step 2 1-month 验证 FAIL → 修复完成）

- ✅ **TZ-1 时区根因（影响 12+ 因子）** — `event.local_ts` 是 UTC ns；hhmm 计算前加 `kSh_offset_ns = 8h` 偏移转 Shanghai。grep 全文确认其他 event_ts 用法都是差值不需偏移。受影响因子（#14/#15/#18/#29/#34/#46/#51-#54/#55-#56）smoke 验证全部恢复正常。
- ✅ **#6 pnc_upside_reload_ema4 输出负值** — `(1 - avg_askvol1/D_s)` 在 askvol1>D_s 时变负。clip ask_ratio∈[0,1]，contrib 与 EMA 输出双重 clamp ≥0。Smoke: min=0 max=0.817 negatives=0。
- ✅ **md_id 4.6e18 garbage (2.9%)** — biz_index sanitize 到 (0, 1e15]；不合法时保留 pending.md_id 不覆写；bar 切换时 reset=-1；FlushBarIfAny 顶部跳过无效 emit。Smoke: max=2.06e9 garbage=0。

---

## 2026-04-29 13:35 (UTC+8) — Iter-2 修复后状态

### 已修复（CLOSED — Code Review FAIL → 修复完成）

- ✅ **#1 G7 #23/#24 at-touch 方向反向** — 改为 BUY ≤ best_bid / SELL ≥ best_ask（passive 语义）
- ✅ **#2 G14 #51-#54 pen_bps 实际计算** — 每个 FILL 在 OnMarketEvent 内计算有方向 pen_bps，按 vol 加权累积；aggtrade finalize 时写入 100-aggtrade rolling buffer
- ✅ **#3 G8 #28/#30 cluster fate 检测** — pending/resolved 双队列，cancel-ratio + 3s fate window resolution
- ✅ **#4 G8 #29 z-score** — per (code, session_bucket Q1-Q4) 当日 expanding stats，n≥2 后 z=clip((raw_ratio-μ)/σ, ±5)
- ✅ **#5 G8 #25 burst sync** — 50ms gap 形成 burst（≥3 members），60s 内匹配 ORDER↔CANCEL（first_ts 间隔 ≤500ms），sync = min/max
- ✅ **#6 跨日 reset** — `Fa28DayReset()` 自由函数 + `Fa28CodeState::last_day` 检测；30+ EMA / deque / order_info_map / 全部累计 counter 重置
- ✅ **#7 G15 Q5 阈值跨日 reset** — `g15_total_cancel_count` 包含在 Fa28DayReset 内

### 仍开放（OPEN — 非阻塞，Phase 4/5 处理）

#### Issue OPEN-1：#16 inv_sticky_interaction_residual 未做 OLS 残差化
- 状态：CONDITIONAL ACCEPT（reviewer §6 评语）
- 实现：直接输出 `EMA_50(interaction)`
- 原因：baseline 因子（fa9_inv_pressure / ghost_dir_ema_hl25 / trade_ofi_hl25）不在本 agent 范围
- 计划：Analyzer2 阶段补 OLS 残差化；标记为 ⚠️ 警告因子（#89 Phase 3 sign flip）

#### Issue OPEN-2：G14 spread Q2/Q4 阈值硬编码 (2.0/4.0/7.0 bps)
- 状态：保留 hardcoded（per-code 训练阈值不可在 runtime 注入）
- 计划：Phase 5 离线扫描 per-code 阈值后注入

#### Issue OPEN-3：G15 #56 lifetime 单位
- spec：`(cancel_seq - submit_seq) / 1e6` (基于 biz_index seq diff)
- 实现：`(event_ts - cancel_orig_add_ts) / 1e6` (wall-clock ms)
- 偏差：工程上 wall-clock 更稳健，但偏离 spec 的 seq-based 路径
- 计划：Phase 4 IC 验证若异常需切换到 biz_index 路径

#### Issue OPEN-4：G4 widening 阈值 (+1 int vs spec 0.25*tick)
- 实现：`cur_spread - prev_spread >= 1` (= 1 int = 1 tick)
- spec：`> 0.25 * tick`
- 在 int-缩放下最小变动是 1，因此 ≥1 实质上比 0.25 更严格
- 计划：保留以避免 sub-tick 浮点比较；如必要可改为 `>= 1` 比较 prev/cur 的差异

#### Issue OPEN-5：G2/G4 valid_bar<X 全天 NaN→0 行为缺失
- spec：当日 valid_bar<300 (G2) / <900 (G4) 整天不输出
- 实现：每 bar 都输出（valid_bar_count 统计但不 gate）
- 理由：streaming agent 实现 day-level NaN gate 需 buffer 整天后再决定，复杂度高
- 计划：Phase 4 LGBM 训练时若发现日级 IC 异常，由 Analyzer2 做 daily-aggregate filter（而不在 agent 内 gate）

#### Issue OPEN-6：G3 gap_ticks 简化
- 实现：`bid_gap_ticks = ask_gap_ticks = 0`（假设 reserve 紧邻 bid1/ask1 ± 1 tick）
- 影响因子：#10 qa_predecessor_interaction_h640
- 计划：如 IC 偏弱，扫描 g3_bid_levels / g3_ask_levels 找 reserve 与 best touch 的 tick gap

#### Issue OPEN-7：G15 Q5 universe per-day approximation
- 实现：当日累计 cancel ≥1000 即视为 Q5（Iter-2 跨日 reset 后准确）
- spec：跨日 p80 dynamic threshold
- 计划：Phase 4 验证；生产部署需替换为离线 p80（昨日历史）注入

---

## 2026-04-29 11:30 (UTC+8) — Iter-1 实现阶段记录（历史）

### 1. CMakeLists.txt 必要修复（已修改）

原模板缺失：
- `common_args_lib`：runner_tool.cpp 引用的 `FLAGS_date/data_path/code/output_dir/universe/universe_file` 在该库定义
- `fmt::fmt`：`backtest_runner.cpp` 内部使用 fmt::vformat_to

按 FA27 模板补齐 + `find_package(fmt CONFIG REQUIRED)`。属于必要修复，不影响 binary 名/项目名。

### 2. #22 F1 input requirement
F22 的 F1 输入应为 **published z-score**（#19 最终输出，含 60-bar rolling），而非原始 EMA。
实现：`g6_F1_z_history` 在 #19 z-score 计算后缓冲；F22 quantile 直接读取该 deque。✓ 满足规范。
