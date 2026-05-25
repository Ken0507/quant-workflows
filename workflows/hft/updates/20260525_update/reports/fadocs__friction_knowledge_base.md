# 已知摩擦模式知识库

> 本文件记录研究 pipeline 中反复出现的已知问题。每次 deep research 启动时（Phase 0）必须阅读本文件，在编写代码和脚本时主动规避这些问题。
>
> **维护原则**：发现新的重复摩擦模式时，及时补充到本文件。

---

## 1. SZSE Cancel 事件 price=0

**触发条件**：因子代码中使用 `trans.price` 处理 cancel 事件（SZSE 标的的 cancel 事件 price 恒为 0，side 为 UNKNOWN）

**检测方法**：检查因子代码中是否在 cancel 分支直接使用了 `t.price` 或 `trans.price` 计算金额/价格相关指标

**修复方案**：维护 `order_info_map`（order_id → {price, side}），ORDER ADD 时写入，FILL/CANCEL 时通过 bid_id/ask_id 查找原始委托价格和方向。参考实现：`HFTPool/workspace/EventDominance11/projects/ed11_factor_project/src/ed11_event_dominance.hpp`（OrderInfoEntry + try_lookup 模式）。可选 mid price fallback。

---

## 2. NaN/Inf 因子值污染下游

**触发条件**：因子计算中存在除法（分母可能为 0）、log（参数可能 ≤ 0）、或累积量溢出

**检测方法**：因子输出后运行 `df.isna().sum()` + `np.isinf(df.values).sum()`，非零即有问题

**修复方案**：
- 除法：分母加 epsilon 保护（如 `x / (y + 1e-12)`）或分母为 0 时输出 NaN 并在最终 clip
- log：参数 clamp 到正数范围
- 输出前统一做 `np.clip(values, -1e6, 1e6)` 或 `replace([np.inf, -np.inf], np.nan)`

---

## 3. 筛选脚本性能不足

**触发条件**：Phase 2/3 新写的 Python 筛选/验证脚本

**检测方法**：先对 1 code × 1 date 做 dry-run，评估全量运行时间是否合理

**修复方案**：
- 使用 pandas/numpy 内置聚合（`.agg({'col': 'mean'})`），避免 `lambda` 和 `apply`
- 批量加载 parquet（glob 一次读入），避免逐 code 循环加载
- groupby 后用向量化操作，避免 Python for 循环遍历分组

---

## 4. 后台任务 OOM (exit code 143/144)

**触发条件**：workers > 1 的大规模批量任务（如全 universe 刷因子、大样本筛选）

**检测方法**：进程退出码为 143（SIGTERM）或 144（超出资源限制）

**修复方案**：降低并发重试（workers=1）。143/144 是系统 OOM kill，不是逻辑错误，降低并发通常可解决。大型因子集（>30 因子）默认考虑 workers=1。

---

## 5. 时间戳 / Join Key 类型不匹配

**触发条件**：因子 parquet 与 basic_table merge 时

**检测方法**：merge 后行数显著少于预期（< 95% 的预期行数），或 merge 结果全为 NaN

**修复方案**：
- 检查 join key 的 dtype 是否一致（常见：一边 int64 一边 float64，或 datetime vs int timestamp）
- 使用 `df.dtypes` 对比两个 DataFrame 的 join 列类型
- 优先使用 index-based join（`merge(left_index=True, right_index=True)`）或显式转型后再 merge

---

## 6. 开盘集合竞价 crossed book（从 order/transaction 重建 book 时）

**触发条件**：因子代码从 order/transaction parquet **从零重建 book** 以检测 cross event / 深档状态

**检测方法**：重建的 book 在开盘 09:30 附近会出现 crossed state（best_bid > best_ask）；如果 cross_event 计数在 bar 1 异常高（如 > 10000），即是此陷阱

**原因**：集合竞价阶段订单已进入 book 但按集合价撮合（不是逐笔撮合），事件驱动重建没有处理这个特殊撮合阶段

**修复方案**：
- **Cross 检测用 `basic_table` 的 bid1/ask1/mid snapshot**（权威 L1 快照），不要重建 book
- 深档状态判定用 "距 L1 的 bps 距离"（如 5 < d_bps ≤ 100），不依赖 L-index
- 如必须重建 book，在 continuous trading 开始后（09:30:xx 以后数秒）做 warm-up 初始化

**来源**：研究 #94 micro_ripple_contagion Phase 2 POC v1 → v2 修正

---

## 7. 大样本 residual IC OOM (load baseline_150 全 parquet)

**触发条件**：Phase 3 做 baseline residual IC 时，顺序加载所有 baseline 因子的完整 parquet（150+ 列 × 多日 × 多 code）

**检测方法**：Python 进程被 OOM kill，dmesg 显示 "total-vm:~50 GB" 的 Python 进程

**原因**：`baseline_150_new` 每日 parquet 合起来约 500-800k rows × 150 列 = 可轻易超过单进程 20 GB；并发 workers 累计会超 50 GB

**修复方案**：
- **只读必要列**：`pd.read_parquet(path, columns=[required_3_cols])`
- Per-task 处理：加载单 (date, code) baseline + 本研究因子 → 计算 residual IC → `del df; gc.collect()`
- 限 workers ≤ 12（非 24），每 task 内存占用 ~1-2 GB
- 若仍 OOM：chunked 处理，单进程 sequential

**来源**：研究 #94 Phase 3 P1 baseline residual 实战

---

## 8. basic_table 的 `spread` 列是相对值，不是绝对差

**触发条件**：因子代码使用 basic_table 的 `spread` 列（如 `spread_ticks = spread / tick_size`）以为它是 ask1 - bid1 的绝对值。

**检测方法**：取 `spread / (ask1 - bid1)` 应≈1 / mid，即数量级是 1e-2（百分之几）；如果代码假设 spread = ask1-bid1 yuan，则 `spread / tick_size` 会得到 0.x 而非应有的几十 ticks。

**修复方案**：始终使用 `(ask1 - bid1)` 直接计算绝对 spread；如果需要相对 spread，用 `(ask1-bid1)/mid` 或直接读 `spread` 列。
- `spread_ticks = (ask1 - bid1) / tick_size`
- `spread_bps = (ask1 - bid1) / mid * 10000` 等价于 `spread * 10000`

**症状**：研究 #103 R2/R3 中 `spread_pre_ticks` median = -0.083（应为 ~10-30 ticks），导致按 `spread_pre_ticks > 0` 过滤 episode 时**丢弃了 100% 样本**。

**来源**：研究 #103 R5 自查发现并修复（v3 提取脚本）

---

## 9. Episode-level 逻辑成立 ≠ Bar-level 因子有效

**触发条件**：研究中发现某 microstructure mechanism 在 episode-level 有清晰物理含义（如"trade-driven flicker = 续行信号"、"persistent = 退场信号"），直接将其聚合到 bar-level 后期望预测 forward return。

**检测方法**：bar-level 聚合后该 mechanism 的 share / count / sum 类因子的 IC 跨 code-days **方向不一致**（< 50% 方向一致率），或 pooled IC < 0.005。

**原因**：bar 级（如 bar_aggtrans_time_1 = ~100 aggtrades）粒度可能让 episode-level 的 100ms-级信号被强 baseline（OFI / trade flow）掩盖；同时不同 mechanism 在 bar 内可能互相抵消。

**修复方案**：
- 不在 Phase 2 候选中包含未经 bar-level IC 验证的 mechanism share 因子。
- 如必须 bar-化，先做"controlling for OFI / ghost_dir_ema 后是否仍有信号"的残差测试。
- 考虑更细粒度（如 bar_aggtrans_time_1/2 或 tick-level）的 LGBM 输入，但这超出 Phase 2 范围。
- Episode-level 的 mechanism 分类作为**描述性 microstructure 知识贡献**保留，不强行因子化。

**症状（研究 #103 实例）**：
- R8 三元修订（active_tighten 后果分为 trade-driven 续行 / persistent 退场 / cancel-driven 真噪声）逻辑清晰自洽。
- R9 因子化测试（F4 = consumed_share, F5 = persistent_share）跨 9 code-days 方向 2-3/9 正 vs 6-7/9 负，**方向不一致**；pooled IC 全部 < 0.005。
- 修订解释作为 description 有 microstructure 价值，但不能直接因子化。

**来源**：研究 #103 R8 三元修订 + R9 F4/F5 因子化失败的复盘

