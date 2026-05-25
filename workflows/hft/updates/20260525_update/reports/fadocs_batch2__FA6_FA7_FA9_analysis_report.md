# FA6/FA7/FA9 因子集分析报告

> **基于实验结果的因子构造思路复盘与改进建议**
> 
> **生成时间**: 2026-01-25

---

## 1. 实验结果概览

### 1.1 三组因子集的 LGBM 表现对比

| 因子集           | 因子数 | Valid RankIC | Δ vs Baseline    | 贡献最大因子                                      | IR   |
| ---------------- | ------ | ------------ | ---------------- | ------------------------------------------------- | ---- |
| FA6 (基础盘口)   | 8      | 0.0364       | +0.0007          | `event_rate`                                      | -    |
| FA7 (参考价体系) | 30     | 0.0495       | +0.0107          | `dAsk_bps_1m`, `micro_gap_bps_10`, `cost_asym_1m` | -    |
| FA9 (交易流冲击) | 43     | 0.0461       | ~+0.05-0.15 预估 | `pen_cost_asym` (IR=4.91), `absorption_signed`    | 4.91 |

### 1.2 关键发现

**FA6**：
- 8 个基础因子中，仅 `fa6_event_rate` 贡献了实质性 gain（rank 20）
- 其他因子（spread_bps, depth_imb, ofi, trade_imb）与 baseline top80 高度共线
- 启示：**简单因子与 baseline 信息重叠严重，需要更深的结构化信息**

**FA7**:
- Valid ΔRankIC = +0.0107，是三组中相对 baseline 提升最明显的
- Top 贡献因子：`dAsk_bps_1m` (固定金额达到成本), `micro_gap_bps_10` (多档 microprice), `cost_asym_1m` (成本不对称)
- 启示：**固定金额流动性几何 + 参考价变体 是高增量方向**

**FA9**:
- `pen_cost_asym` 单因子 IR=4.91，极为稳定
- `absorption_signed` 和其他吸收类因子表现良好
- 启示：**方向性不对称因子 + 成交-价格响应 是核心 Alpha 来源**

---

## 2. 正确的思路与操作（可推广）

### 2.1 固定金额 vs 固定档数

**最佳实践**: 使用**固定金额**阈值而非固定档数

| 维度         | 固定档数 (L1-L3)   | 固定金额 (10万/30万/100万)                  |
| ------------ | ------------------ | ------------------------------------------- |
| 跨标的一致性 | ❌ 差（深度差异大） | ✓ 好                                        |
| 经济意义     | ❌ 弱               | ✓ 强（对应实际交易成本）                    |
| FA7 验证     | -                  | `dAsk_bps_1m`, `cost_asym_1m` 均为 top 贡献 |

**推广建议**:
- 所有涉及"深度"的因子都应提供固定金额版本
- Batch2 因子中的 `trapped_score`, `iceberg_score` 等应按金额归一化

### 2.2 方向性不对称 (Asymmetry) 因子

**最佳实践**: 买卖分侧计算后取差值

| 因子                | 单侧版本                       | 不对称版本                | 效果对比             |
| ------------------- | ------------------------------ | ------------------------- | -------------------- |
| FA7 cost            | `dAsk_bps`, `dBid_bps`         | `cost_asym = dAsk - dBid` | cost_asym 贡献更大   |
| FA9 pen_cost        | `pen_cost_bid`, `pen_cost_ask` | `pen_cost_asym` (IR=4.91) | 不对称版本远优于单侧 |
| FA9 realized_spread | 总体 EMA                       | `_buy`, `_sell`, `_asym`  | 分侧有增量           |

**推广建议**:
- 对于所有买卖对称的因子，都应计算 `_bid`, `_ask`, `_asym` 三个版本
- Batch2 因子中：`trapped_imb`, `iceberg_imb`, `cancel_at_risk_imb` 都应遵循此模式

### 2.3 多尺度 EMA (fast-slow)

**最佳实践**: 使用 tick-based EMA，提供 fast/slow 两档 + burst = fast - slow

| 参数       | FA9 推荐值              | 理由                               |
| ---------- | ----------------------- | ---------------------------------- |
| ALPHA_FAST | 0.02 (半衰期≈35 tick)   | 捕捉短期动量                       |
| ALPHA_SLOW | 0.002 (半衰期≈350 tick) | 预测周期(1000 tick)的 1/3 作为基线 |
| burst      | fast - slow             | 加速/减速信号                      |

**推广建议**:
- 所有流量类因子都应提供 `_fast`, `_slow`, `_burst` 三个版本
- Batch2 中的 `ghost_mid_move`, `chase_rate` 等应遵循此模式

### 2.4 连续型优于二值型

**最佳实践**: 用连续值替代二值标记

| 概念        | 二值版本                             | 连续版本                                 | 效果                |
| ----------- | ------------------------------------ | ---------------------------------------- | ------------------- |
| FA10 墙突破 | `wall_break_flag = 1 if drop > 50%`  | `wall_drop_ratio = (prev - curr) / prev` | 连续版本更适合 LGBM |
| FA9 shock   | `in_shock = 1 if spread > threshold` | `shock_magnitude`, `time_since_shock`    | 拆成多个连续量      |

**推广建议**:
- 避免硬阈值触发的二值因子
- 如果必须有二值信号，同时提供连续版本（如"触发程度"）

---

## 3. 可改进的思路与操作

### 3.1 FA6 的问题：信息重叠

**问题**: FA6 的 spread/imb/ofi/trade_imb 与 baseline 中的 a3_/sig2_ 因子高度相关，导致边际贡献几乎为 0

**改进方向**:
1. **条件化**: 在特定 regime 下（如高波动、薄盘）单独计算
2. **去相关**: 对 baseline 因子做正交化处理后再入模
3. **更深的结构**: 使用 full_book 而非仅 L1-L3

### 3.2 FA6 的问题：EMA 参数过于简单

**问题**: FA6 使用固定 `alpha=0.1`，未考虑：
- 跨标的事件密度差异
- 预测 horizon (1000 tick) 的时间尺度匹配

**改进方向**:
- 改用 tick-based EMA（如 FA9/FA10）
- 提供 fast/slow 两档，捕捉不同时间尺度信息

### 3.3 FA6 的问题：量纲不一致

**问题**: `fa6_trade_imb_signed` 用成交额 (price*volume) 直接做 EMA，跨标的尺度差异大

**改进方向**:
- 除以近窗口成交额/深度做归一化
- 或使用 log 变换

### 3.4 FA7 的问题：部分因子未被使用

**问题**: 以下 FA7 因子在 merged 模型中 gain=0：
- `fa7_eff_spread_bps_50k`, `fa7_grid_irregular`, `fa7_effective_tick_bps`
- `fa7_max_gap_bps_20`, `fa7_imb_R_*`, `fa7_large_gap_ratio_20`
- `fa7_jump_risk_asym`, `fa7_micro_queue_gap_bps_3`

**改进方向**:
1. 检查是否与其他因子高度相关（共线性筛除）
2. 参数可能不合适（如 R=5 bps 可能太小）
3. 考虑做因子选择/正则化

### 3.5 FA9 的问题：时间轴对齐

**问题**: 10 个日期因时间轴对齐问题被排除（占比 8%）

**改进方向**:
- 确保 `time` 字段与 `basic_table` 的 legacy offset (8h) 一致
- 在 pipeline 中加入轴对齐检查

---

## 4. 对现有因子集的具体改进建议

### 4.1 FA6 改进建议

| 当前因子           | 改进措施                             | 预期效果         |
| ------------------ | ------------------------------------ | ---------------- |
| `spread_bps`       | 增加 `spread_state` (离散状态机)     | 捕捉状态转移信息 |
| `depth_imb_l1/l3`  | 改用固定金额版: `imb_R_5/10/20bps`   | 跨标的一致性     |
| `ofi_l1`           | 扩展到 OFI_exp (指数加权多档)        | 更多深度信息     |
| `trade_imb_signed` | 归一化: `/ (trade_amount_ema + ε)`   | 消除量纲差异     |
| -                  | 新增 `event_rate_diff = fast - slow` | 捕捉活跃度变化   |

### 4.2 FA7 改进建议

| 当前因子                | 改进措施                            | 预期效果     |
| ----------------------- | ----------------------------------- | ------------ |
| `imb_R_*`               | 增加 bps 范围：5/10/20 → 5/10/20/50 | 覆盖更多尺度 |
| `micro_queue_gap_bps_3` | 检查 `hit_rate` 的初始化是否正确    | 数据质量     |
| `jump_risk_asym`        | 简化定义，去掉 depth_after_gap      | 减少噪声     |
| 未被使用因子            | 做相关性分析后决定是否删除          | 降维         |

### 4.3 FA9 改进建议

| 当前因子        | 改进措施                                | 预期效果        |
| --------------- | --------------------------------------- | --------------- |
| `pen_cost_asym` | 这是核心因子，保持不变                  | -               |
| `absorption_*`  | 增加更多尺度版本 (fast/medium/slow)     | 多尺度信息      |
| `run_*` 系列    | 增加 `run_momentum = Δrun_intensity`    | 加速度信号      |
| shock 相关      | 确保 shock 阈值是动态分位数，而非固定值 | 适应不同 regime |

---

## 5. Batch2 因子的优化建议（来自本分析）

基于 FA6/FA7/FA9 的经验，对 Batch2 因子列表的补充建议：

### 5.1 高优先级优化

1. **§5 库存压力因子**:
   - 增加 `trapped_imb_burst = fast - slow`（加速度版本）
   - 归一化 `trapped_score`: 除以近窗口被动成交额

2. **§3 Ghost Moves**:
   - 增加 `ghost_move_asym = ghost_up - ghost_down`（方向性不对称）
   - 与 `quote_move_share` 交互：`ghost_strength = ghost_bps × quote_share`

3. **§6 冰山检测**:
   - 使用**固定金额**定义冰山（如"吃掉 10 万后仍有回补"）
   - 增加 `iceberg_persistence`（持续多少 tick 保持刷新）

### 5.2 中优先级优化

4. **§7 路径效率**:
   - 增加多尺度版本: `ER_50/ER_200/ER_500`
   - 与 FA9 `run_efficiency` 对比，选择信息增量更大的

5. **§9 深度重心**:
   - 与 FA7 `vwapmid` 对比相关性
   - 如果高度相关，只保留一个

### 5.3 注意事项

6. **避免与 FA10 重复**:
   - FA10 已覆盖: OFI 多档版、墙单检测、大小单分类
   - Batch2 应聚焦于: 库存压力、冰山、路径效率、撤单质量

7. **统一参数口径**:
   - EMA halflife: 统一使用 20/100/500 tick 三档
   - 固定金额: 统一使用 10 万/30 万/100 万 CNY

---

## 6. 总结：构造高预测力因子的原则

基于 FA6/FA7/FA9 的实验结果，总结以下因子构造原则：

| 原则                     | 证据                               | 应用                            |
| ------------------------ | ---------------------------------- | ------------------------------- |
| **固定金额优于固定档数** | FA7 `dAsk_bps_1m` >> `dAsk_bps_L3` | 所有深度因子使用金额归一化      |
| **不对称优于单侧**       | FA9 `pen_cost_asym` IR=4.91        | 所有对称因子提供 `_asym` 版本   |
| **多尺度优于单尺度**     | FA9 `burst = fast - slow` 有效     | EMA 提供 20/100/500 tick 半衰期 |
| **连续优于二值**         | FA10 `wall_drop_ratio` >> `flag`   | 避免硬阈值，提供连续程度量      |
| **归一化消除量纲**       | FA6 `trade_imb` 问题               | 流量类因子除以基准              |
| **避免信息重叠**         | FA6 与 baseline 共线               | 做相关性筛查                    |

---

> **文档版本**: v1.0  
> **基于材料**: FA6/FA7/FA9 LGBM 报告、task_retrospective.md、feature_importance 分析
