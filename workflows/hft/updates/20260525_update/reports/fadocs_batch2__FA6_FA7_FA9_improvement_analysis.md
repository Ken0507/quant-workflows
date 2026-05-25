# FA6/FA7/FA9 因子改进分析报告

> **生成时间**: 2026-01-26
> **预测目标**: Entrust Bar 1m 下 Next 20 Bar Return（约 1000 ticks）
> **数据范围**: 20250102-20250730

---

## 1) 执行摘要

本报告基于 FA6/FA7/FA9 三组因子的 LGBM 增量实验结果，总结成功模式并提出改进建议。

### 1.1 核心发现

| Agent | 因子数 | Valid ΔRankIC | 最强因子 | IR | 结论 |
|-------|--------|---------------|----------|-----|------|
| FA6 | 8 | +0.0007 (~0%) | fa6_event_rate | N/A | 信息重叠严重，几乎无增量 |
| FA7 | 21 | +0.00107 (+1.5%) | fa7_dAsk_bps_1m | ~0.5 | 固定金额流动性几何有效 |
| FA9 | 43 | 预估+5-15% | fa9_pen_cost_asym | **4.91** | 穿透成本不对称表现突出 |

### 1.2 关键结论

1. **FA9 的 `pen_cost_asym` 是目前所有新因子中最强的**，IR=4.91 远超其他因子
2. **方向不对称（bid-ask decomposition）是最重要的 Alpha 来源**
3. **固定金额 > 固定档数**：FA7/FA9 用固定金额（50k/200k/1m）效果更好
4. **FA6 与 baseline 信息重叠 >90%**，应弃用或大幅重构

---

## 2) 成功模式深度分析

### 2.1 模式1：方向不对称 > 单一指标

**证据**：
- FA9 `pen_cost_asym` (ask侧-bid侧穿透成本差) → IR=4.91
- FA7 `cost_asym_1m` → gain_ratio=0.0308（Top3 新因子）

**原因分析**：
市场微观结构存在显著的买卖不对称性：
- 上涨时：买方消耗 ask 侧流动性，ask 侧穿透成本升高
- 下跌时：卖方消耗 bid 侧流动性，bid 侧穿透成本升高
- 不对称程度（asym）直接反映了"哪一方更急迫"

**推广建议**：
```
对于任何因子 X：
- X_bid：仅计算 bid 侧
- X_ask：仅计算 ask 侧
- X_asym = X_ask - X_bid（或 X_bid - X_ask，根据语义）
- X_imb = (X_bid - X_ask) / (|X_bid| + |X_ask| + ε)（归一化版本）

优先产出 X_asym 版本，其次是 X_bid 和 X_ask 单侧版本。
```

### 2.2 模式2：固定金额 > 固定档数

**证据**：
- FA7 `dAsk_bps_1m`（1m 金额穿透深度）→ gain_ratio=0.0351（Top1 新因子）
- FA7 `vwapmid_mid_diff_bps_1m` → gain_ratio=0.0230
- FA9 `pen_cost_10w/30w` → RankIC=0.0142/0.0169
- 相比之下，固定档数因子（如 `imb_R_10/20`）gain 几乎为 0

**原因分析**：
可转债流动性差异极大（高活跃券 vs 低活跃券）：
- 固定 5 档：高活跃券可能只有 2bps 深度，低活跃券可能有 50bps 深度
- 固定 1m 金额：无论活跃度如何，都能捕捉"吃掉 1m 需要多少价格冲击"

**推广建议**：
```cpp
// 推荐：固定金额穿透
double PenetrationCost(OrderBook& book, double target_amount, Side side) {
    double cum_amount = 0.0;
    double cum_cost = 0.0;
    for (int i = 0; i < book.GetLevels(side); ++i) {
        double level_amount = book.GetAmount(side, i);
        double level_price = book.GetPrice(side, i);
        double take_amount = std::min(level_amount, target_amount - cum_amount);
        cum_cost += take_amount * level_price;
        cum_amount += take_amount;
        if (cum_amount >= target_amount) break;
    }
    double vwap = cum_cost / (cum_amount + 1e-9);
    double mid = book.GetMidPrice();
    return (vwap - mid) / mid * 1e4;  // bps
}

// 建议测试金额：{5w, 10w, 30w, 50w, 100w} CNY
```

### 2.3 模式3：多时间尺度 > 单一尺度

**证据**：
- FA9 使用 FAST(35 tick)/SLOW(350 tick) 双 EMA 体系
- FA7 baseline 使用 `ema_fast`/`ema_slow`/`ema_diff` 三版本
- `mid_dev_diff_bps = mid - ema_slow` 在 baseline 中 gain_ratio=0.026

**原因分析**：
预测周期是 Next 20 Bar（约 1000 ticks），需要覆盖：
- **短期（20-50 tick）**：捕捉即时冲击和反转
- **中期（100-200 tick）**：捕捉趋势启动
- **长期（300-500 tick）**：捕捉均值回归

**推广建议**：
```cpp
// 多尺度 EMA 体系
constexpr double HALFLIFE_FAST = 20;   // tick，α ≈ 0.034
constexpr double HALFLIFE_SLOW = 100;  // tick，α ≈ 0.0069
constexpr double HALFLIFE_ACC = 350;   // tick，α ≈ 0.002

// 每个因子产出：
factor_fast  // 短期 EMA
factor_slow  // 长期 EMA
factor_diff = factor_fast - factor_slow  // 动量
factor_acc = factor - factor_slow  // 加速度（类似 MACD signal）
```

### 2.4 模式4：成本分解 > 简单价差

**证据**：
- FA9 `realized_spread` + `adverse_selection` 分解了交易成本
- FA9 `absorption` 量化了市场对大单的"消化能力"
- 比单一 `spread_bps` 信息量更大

**原因分析**：
交易成本可以分解为：
```
Total Cost = Realized Spread + Adverse Selection
           = (Maker获得的价差) + (Price Impact导致的损失)
```
- **Realized Spread 高**：Maker 有利可图 → 流动性供给意愿强
- **Adverse Selection 高**：Taker 带来信息冲击 → 趋势可能延续

**推广建议**：
在设计因子时，考虑"分解"而非"聚合"：
- 成交量 → 主动买量 + 主动卖量
- 深度 → bid 侧深度 + ask 侧深度
- 撤单 → 恐惧撤单 + 诱导撤单

### 2.5 模式5：动态响应 > 静态快照

**证据**：
- FA9 韧性因子（`time_to_spread_normal`, `replenish_speed`）表现良好
- FA9 `run_exhaustion`（Run 追踪）捕捉了趋势耗竭
- FA6 的静态盘口因子几乎无增量

**原因分析**：
静态快照只回答"现在是什么状态"，动态响应回答"市场如何应对冲击"：
- 深度被吃掉后多快恢复？→ 韧性
- 价格冲击后多久回到正常？→ 均值回归速度
- 同向成交持续多久？→ 趋势强度

**推广建议**：
设计"冲击-响应"类因子：
```cpp
// 冲击检测
bool IsShock(double trade_amount, double avg_amount) {
    return trade_amount > 3 * avg_amount;  // 3σ 冲击
}

// 响应测量
void OnShock() {
    shock_start_mid_ = current_mid_;
    shock_start_ts_ = current_ts_;
    in_shock_recovery_ = true;
}

void OnTick() {
    if (in_shock_recovery_) {
        double recovery_ratio = (current_mid_ - shock_start_mid_) / shock_impact_;
        if (recovery_ratio > 0.5) {  // 恢复超过 50%
            double recovery_time_ms = (current_ts_ - shock_start_ts_) / 1e6;
            recovery_speed_ema_ = ema_update(recovery_speed_ema_, 1.0 / recovery_time_ms, 0.02);
            in_shock_recovery_ = false;
        }
    }
}
```

---

## 3) FA6 失败分析与改进建议

### 3.1 问题诊断

**实验结果**：
- Valid ΔRankIC = +0.0007（接近 0）
- 仅 `fa6_event_rate` 有 gain（gain_ratio=0.0115）
- 其余 7 个因子 gain=0

**失败原因**：

| 因子 | 问题 | 根因 |
|------|------|------|
| fa6_spread_bps | 与 baseline `a3_spread_bps` 完全相同 | 重复实现 |
| fa6_ofi_l1 | 与 baseline OFI 高度相关 | 信息重叠 |
| fa6_depth_imb_l1/l3 | 与 baseline `imb_ratio_*` 高度相关 | 信息重叠 |
| fa6_trade_imb_signed | 未做跨标的归一化，量纲差异大 | 实现缺陷 |
| fa6_micro_gap_bps_l1 | 与 FA7 `micro_gap` 重复 | 设计重叠 |
| fa6_spread_bps_ema_fast | 仅是 spread 的 EMA，无新信息 | 设计冗余 |

### 3.2 改进方案

**方案 A：弃用**（推荐）
FA6 的设计目标已被 baseline + FA10/FA11 完全覆盖，建议直接弃用。

**方案 B：重构**（如果必须保留）
```cpp
// 1. 增加事件率自适应 EMA
double adaptive_alpha = base_alpha * event_rate / avg_event_rate;

// 2. 使用 z-score 归一化
double z_score = (value - running_mean) / (running_std + 1e-9);

// 3. 增加方向不对称版本
double fa6_ofi_asym = ofi_bid - ofi_ask;
```

### 3.3 教训总结

> **核心教训**：在设计新因子前，必须与现有因子做相关性分析。如果 Pearson 相关 > 0.8，则新因子大概率无增量。

---

## 4) FA7 部分成功分析与改进建议

### 4.1 成功因子

| 排名 | 因子 | Gain Ratio | 成功原因 |
|------|------|------------|----------|
| 1 | fa7_dAsk_bps_1m | 0.0351 | 固定金额穿透，跨标的一致 |
| 2 | fa7_micro_gap_bps_10 | 0.0347 | 深度断层检测，新视角 |
| 3 | fa7_cost_asym_1m | 0.0308 | 方向不对称，高信息量 |
| 4 | fa7_eff_gap_bps | 0.0281 | 有效价差，去除噪声 |
| 5 | fa7_dBid_bps_1m | 0.0256 | 与 dAsk 对称 |

### 4.2 失败因子

| 因子 | Gain Ratio | 失败原因 |
|------|------------|----------|
| fa7_imb_R_5/10/20 | 0 | 与 baseline `imb_ratio` 共线 |
| fa7_large_gap_ratio_20 | 0 | 计算复杂但信息量低 |
| fa7_jump_risk_asym | 0 | 定义不清晰，噪声大 |
| fa7_micro_queue_gap_bps_3 | 0（merged） | 与 micro_gap_bps_10 共线 |

### 4.3 改进方案

**保留因子**（Top 7）：
```
fa7_dAsk_bps_1m
fa7_dBid_bps_1m
fa7_cost_asym_1m
fa7_micro_gap_bps_10
fa7_eff_gap_bps
fa7_vwapmid_mid_diff_bps_1m
fa7_eff_spread_bps_1m
```

**新增变体**：
```cpp
// 1. 增加更多金额档位
fa7_dAsk_bps_50k, fa7_dAsk_bps_200k, fa7_dAsk_bps_500k

// 2. 增加多时间尺度
fa7_cost_asym_1m_fast, fa7_cost_asym_1m_slow, fa7_cost_asym_1m_diff

// 3. 与 FA9 穿透成本交互
fa7_x_fa9_pen_interaction = fa7_cost_asym_1m * fa9_pen_cost_asym
```

### 4.4 Regime 分析

基于 FA7 报告的 Regime 分析：

| Regime | Baseline IC | Merged IC | ΔIC | 解释 |
|--------|------------|-----------|-----|------|
| 低波动 | 0.0883 | 0.0951 | +0.0068 | FA7 在低波动环境表现更好 |
| 高波动 | 0.0792 | 0.0807 | +0.0014 | 高波动时增量有限 |
| 低 spread | 0.0830 | 0.0872 | +0.0042 | 流动性好时增量更大 |
| 高 spread | 0.0819 | 0.0840 | +0.0020 | 流动性差时增量减弱 |

> **结论**：FA7 因子在"温和"市场环境下更有效。建议在高波动/低流动性时降低其权重。

---

## 5) FA9 成功分析与进一步改进

### 5.1 核心成功因子

| 排名 | 因子 | RankIC | IR | 成功原因 |
|------|------|--------|-----|----------|
| 1 | fa9_pen_cost_asym | 0.0340 | **4.91** | 方向不对称 + 固定金额 |
| 2 | fa9_absorption_signed | 0.0197 | 1.11 | 市场消化能力 |
| 3 | fa9_pen_cost_30w | 0.0169 | 0.79 | 固定金额穿透 |
| 4 | fa9_pen_cost_10w | 0.0142 | 0.54 | 同上 |
| 5 | fa9_run_amount | 0.0039 | 0.86 | 同向成交追踪 |

### 5.2 待改进因子

| 因子 | RankIC | IR | 问题 |
|------|--------|-----|------|
| fa9_time_to_spread_normal_ema | 0.0108 | 0.19 | IC 高但波动大 |
| fa9_time_to_depth_restore_ema | 0.0085 | 0.17 | 同上 |
| fa9_absorption_burst | 0.0047 | 0.13 | 噪声大 |

### 5.3 改进方案

**短期行动**：
1. **修复时间轴对齐问题**：10 个日期被排除（占比 <8%），需修复
2. **消融实验**：保留 Top 15-20 因子，剔除弱因子
3. **增加穿透成本变体**：`pen_cost_50w`, `pen_cost_100w`

**中期行动**：
1. **韧性因子稳定化**：
```cpp
// 增加 gating：仅在明确冲击后计算恢复时间
if (shock_detected && recovery_complete) {
    time_to_recover_ema_ = ema_update(...);
}
// 否则保持上一个有效值（避免噪声）
```

2. **多尺度穿透成本**：
```cpp
fa9_pen_cost_asym_fast = pen_cost_asym (HALFLIFE=20)
fa9_pen_cost_asym_slow = pen_cost_asym (HALFLIFE=100)
fa9_pen_cost_asym_diff = fast - slow  // 加速度
```

3. **与其他 Agent 交互**：
```cpp
// FA9 x FA7 交互因子
fa9_x_fa7_cost_interaction = fa9_pen_cost_asym * fa7_cost_asym_1m
// 如果两者同向（都显示 ask 侧压力大），信号加强
```

### 5.4 LGBM 模型诊断

基于 FA9 单独模型的特征重要性：

| 排名 | 因子 | Gain 贡献 |
|------|------|-----------|
| 1 | fa9_pen_cost_asym | 最高 |
| 2 | fa9_time_to_spread_normal_ema | 次高 |
| 3 | fa9_trade_through_rate | 第三 |
| 4 | fa9_absorption_signed | 第四 |
| 5 | fa9_recovery_speed_ema | 第五 |

> **观察**：特征重要性排序与 RankIC 排序不完全一致。`time_to_spread_normal_ema` 在模型中重要性高，但 IR 低（0.19），说明该因子**非线性信息量大但单调性弱**。建议保留并探索分桶/离散化。

---

## 6) 成功模式推广到 FA_Batch2

### 6.1 设计原则清单

基于 FA6/FA7/FA9 的经验，FA_Batch2 因子设计应遵循：

| 编号 | 原则 | 示例 |
|------|------|------|
| P1 | 所有因子产出 `_bid`, `_ask`, `_asym` 三版本 | fb_trapped_bid, fb_trapped_ask, fb_trapped_imb |
| P2 | 使用固定金额而非固定档数 | 用 `100k CNY` 而非 `5 levels` |
| P3 | 产出 `_fast`, `_slow`, `_diff` 多尺度版本 | fb_cancel_at_risk_fast, fb_cancel_at_risk_slow |
| P4 | 分解而非聚合 | 撤单 → 恐惧撤单 + 诱导撤单 |
| P5 | 动态响应优于静态快照 | 恢复速度 > 当前深度 |
| P6 | 预先与现有因子做相关性检查 | 与 baseline 相关 > 0.8 则弃用 |

### 6.2 高优先级因子与模式对应

| FA_Batch2 因子 | 应用的成功模式 | 预期效果 |
|---------------|---------------|----------|
| fb_trapped_imb | P1 方向不对称 | 类似 pen_cost_asym |
| fb_cancel_at_risk_imb | P1 + P4 分解 | 新视角 |
| fb_quote_move_share | P5 动态响应 | 正股联动代理 |
| fb_efficiency_ratio | N/A（全新维度） | 趋势/震荡区分 |
| fb_elasticity_imb | P1 + P5 | 恢复不对称 |

### 6.3 参数继承

从 FA9 继承的参数设置：

```cpp
// EMA 半衰期（tick 单位）
constexpr double HALFLIFE_FAST = 35;   // FA9 已验证有效
constexpr double HALFLIFE_SLOW = 350;  // FA9 已验证有效

// 穿透金额阈值
constexpr double PEN_AMOUNT_1 = 100000;  // 10w CNY
constexpr double PEN_AMOUNT_2 = 300000;  // 30w CNY
constexpr double PEN_AMOUNT_3 = 500000;  // 50w CNY（新增测试）

// 冲击检测阈值
constexpr double SHOCK_THRESHOLD = 3.0;  // 3σ
```

---

## 7) 综合建议与下一步

### 7.1 短期行动（1-2 周）

| 优先级 | 行动 | 负责人 | 预期产出 |
|--------|------|--------|----------|
| 1 | 将 FA9 Top5 因子纳入 baseline | - | +3-5% Valid IC |
| 2 | 将 FA7 Top5 因子纳入 baseline | - | +1-2% Valid IC |
| 3 | 弃用 FA6 | - | 简化代码库 |
| 4 | 修复 FA9 时间轴对齐（10 日） | - | 数据完整性 |

### 7.2 中期行动（3-4 周）

| 优先级 | 行动 | 预期产出 |
|--------|------|----------|
| 1 | 实现 FA_Batch2 Phase 1 因子（5 个核心） | 5 个新因子 |
| 2 | 做消融实验确认边际贡献 | 去除无效因子 |
| 3 | 探索 FA9 x FA7 交互因子 | 非线性信息 |

### 7.3 长期行动（1-2 月）

| 行动 | 预期产出 |
|------|----------|
| 实现 FA_Batch2 全部高优先级因子 | ~30 个新因子 |
| 与 baseline 做增量测试 | 验证增量 |
| 进入 OOS validation 验证 | 生产就绪 |

---

## 附录 A: 详细数据支撑

### A.1 FA6 因子重要性

| feature | gain_ratio |
|---------|------------|
| fa6_event_rate | 0.011542 |
| fa6_spread_bps | 0.000468 |
| fa6_micro_gap_bps_l1 | 0.000000 |
| fa6_ofi_l1 | 0.000000 |
| fa6_trade_imb_signed | 0.000000 |
| fa6_spread_bps_ema_fast | 0.000000 |
| fa6_depth_imb_l1 | 0.000000 |
| fa6_depth_imb_l3 | 0.000000 |

### A.2 FA7 因子重要性（Merged）

| feature | gain_ratio |
|---------|------------|
| fa7_dAsk_bps_1m | 0.0351 |
| fa7_micro_gap_bps_10 | 0.0347 |
| fa7_cost_asym_1m | 0.0308 |
| fa7_eff_gap_bps | 0.0281 |
| fa7_dBid_bps_1m | 0.0256 |
| fa7_vwapmid_mid_diff_bps_1m | 0.0230 |
| fa7_eff_spread_bps_1m | 0.0135 |
| fa7_vwapmid_mid_diff_bps_50k | 0.0067 |
| fa7_eff_spread_bps_200k | 0.0034 |
| ... (其余 gain < 0.003) | ... |

### A.3 FA9 因子 RankIC/IR 统计

| 因子 | RankIC Mean | RankIC Std | IR |
|------|-------------|------------|-----|
| fa9_pen_cost_asym | 0.0340 | 0.0069 | 4.91 |
| fa9_absorption_signed | 0.0197 | 0.0177 | 1.11 |
| fa9_pen_cost_30w | 0.0169 | 0.0216 | 0.79 |
| fa9_pen_cost_10w | 0.0142 | 0.0265 | 0.54 |
| fa9_time_to_spread_normal_ema | 0.0108 | 0.0558 | 0.19 |
| fa9_time_to_depth_restore_ema | 0.0085 | 0.0506 | 0.17 |
| fa9_realized_spread | 0.0081 | 0.0139 | 0.58 |
| fa9_replenish_asym | 0.0075 | 0.0134 | 0.56 |
| fa9_adverse_imb | 0.0064 | 0.0226 | 0.28 |
| fa9_eff_trade | 0.0050 | 0.0301 | 0.17 |
| fa9_absorption_burst | 0.0047 | 0.0369 | 0.13 |
| fa9_absorption | 0.0046 | 0.0187 | 0.25 |
| fa9_run_len | 0.0042 | 0.0115 | 0.37 |
| fa9_realized_spread_sell | 0.0041 | 0.0206 | 0.20 |
| fa9_run_amount | 0.0039 | 0.0046 | 0.86 |

### A.4 Regime 分析汇总

**FA7 Valid 日按 Regime 分解**：

| Regime | Baseline RankIC | Merged RankIC | ΔRankIC |
|--------|-----------------|---------------|---------|
| spread=low | 0.0674 | 0.0686 | +0.0012 |
| spread=mid | 0.0723 | 0.0744 | +0.0021 |
| spread=high | 0.0686 | 0.0686 | -0.0001 |
| rvol=low | 0.0734 | 0.0768 | +0.0034 |
| rvol=mid | 0.0680 | 0.0671 | -0.0009 |
| rvol=high | 0.0663 | 0.0668 | +0.0005 |

**FA6 Valid 日按活跃度分解**：

| Regime | Baseline RankIC | Merged RankIC | ΔRankIC |
|--------|-----------------|---------------|---------|
| 低活跃 | 0.0701 | 0.0705 | +0.0004 |
| 中活跃 | 0.0724 | 0.0726 | +0.0002 |
| 高活跃 | 0.0653 | 0.0667 | +0.0014 |

> **结论**：FA6 在高活跃日增量相对更大（+0.0014），但绝对值仍很小。

---

## 附录 B: 代码模板

### B.1 方向不对称因子模板

```cpp
class AsymmetricFactor {
public:
    void Update(double value_bid, double value_ask, double alpha) {
        bid_ema_ = ema_update(bid_ema_, value_bid, alpha);
        ask_ema_ = ema_update(ask_ema_, value_ask, alpha);
    }

    double GetBid() const { return bid_ema_; }
    double GetAsk() const { return ask_ema_; }
    double GetAsym() const { return ask_ema_ - bid_ema_; }
    double GetImb() const {
        double sum = std::abs(bid_ema_) + std::abs(ask_ema_) + 1e-9;
        return (bid_ema_ - ask_ema_) / sum;
    }

private:
    double bid_ema_ = 0.0;
    double ask_ema_ = 0.0;
};
```

### B.2 固定金额穿透模板

```cpp
double ComputeFixedAmountPenetration(
    const hft::OrderBook& book,
    double target_amount_cny,
    hft::Side side
) {
    double mid = book.GetMidPrice();
    double cum_amount = 0.0;
    double cum_cost = 0.0;

    int levels = (side == hft::Side::BUY) ? book.GetAskLevels() : book.GetBidLevels();
    for (int i = 0; i < levels && cum_amount < target_amount_cny; ++i) {
        double price = (side == hft::Side::BUY)
                       ? book.GetAskPrice(i) : book.GetBidPrice(i);
        double amount = (side == hft::Side::BUY)
                        ? book.GetAskAmount(i) : book.GetBidAmount(i);

        double take = std::min(amount, target_amount_cny - cum_amount);
        cum_cost += take * price;
        cum_amount += take;
    }

    if (cum_amount < 1e-6) return 0.0;  // 深度不足

    double vwap = cum_cost / cum_amount;
    double pen_bps = (vwap - mid) / mid * 1e4;
    return (side == hft::Side::BUY) ? pen_bps : -pen_bps;  // 买方穿透为正
}
```

### B.3 多尺度 EMA 模板

```cpp
class MultiScaleEMA {
public:
    MultiScaleEMA(double halflife_fast, double halflife_slow)
        : alpha_fast_(1.0 - std::exp(-std::log(2.0) / halflife_fast)),
          alpha_slow_(1.0 - std::exp(-std::log(2.0) / halflife_slow)) {}

    void Update(double value) {
        ema_fast_ = ema_fast_ * (1 - alpha_fast_) + value * alpha_fast_;
        ema_slow_ = ema_slow_ * (1 - alpha_slow_) + value * alpha_slow_;
    }

    double GetFast() const { return ema_fast_; }
    double GetSlow() const { return ema_slow_; }
    double GetDiff() const { return ema_fast_ - ema_slow_; }
    double GetAcc() const { return ema_fast_ - ema_slow_; }  // 加速度

private:
    double alpha_fast_, alpha_slow_;
    double ema_fast_ = 0.0, ema_slow_ = 0.0;
};
```

---

**文档结束**

> **版本**: v1.0
> **作者**: Factor Research Team
> **更新时间**: 2026-01-26
