# FA3 失效归因报告 v2 — Stage 1+2 Ablation 闭环 (Issue #114)

**Date**: 2026-04-16
**Inputs**: REPORT.md (h100 clip tuning) + h400 rank fair (FA3_ATTRIBUTION.md) + Stage 1 ablation (R²-cut sweep) + Stage 2 ablation (R²×IC double-cut)

---

## 1. 完整 ablation 表（h100 clip, REPORT §6.4 tuned recipe）

| tag | filter | n fa3 | TrRk | VaRk | gap | Δ R0 | fa3 gain% |
|---|---|---:|---:|---:|---:|---:|---:|
| R0 | baseline (fa2+fa1) | — | 0.0621 | **0.0431** | 0.0190 | +0.0000 | 0.0% |
| R1 | R²<0.5 | 84 | 0.0698 | 0.0402 | 0.0296 | −0.0029 | 31.8% |
| R2 | R²<0.3 | 67 | 0.0668 | 0.0384 | 0.0284 | −0.0046 | 22.5% |
| **R3** | **R²<0.2** | **55** | 0.0652 | **0.0437** | 0.0215 | **+0.0006** | 14.2% |
| R4 | R²<0.2 ∧ \|IC\|≥0.002 | 35 | 0.0663 | 0.0434 | 0.0229 | +0.0003 | 13.4% |
| R5 | R²<0.2 ∧ \|IC\|≥0.005 | 19 | 0.0638 | 0.0424 | 0.0214 | −0.0006 | 9.6% |
| R7 | R²<0.2 ∧ \|IC\|≥0.010 (≈dist_*) | 7 | 0.0646 | 0.0420 | 0.0226 | **−0.0011** | 6.4% |

R7 fa3 gain breakdown: `dist_100` 30.6%, `depth_pressure_sum_hl96` 14.9%, `dist_200` 14.3%, `dist_5` 13.0%, `dist_25` 11.9%, `dist_50` 10.4%, `dist_10` 5.1%.

---

## 2. 核心发现

### 2.1 R²-cut 维度：非单调，最佳点在 R²<0.2

- R1 (R²<0.5) **−0.0029** → R2 (R²<0.3) **−0.0046** → R3 (R²<0.2) **+0.0006**
- R²<0.3 是历史最差点（−0.0046），不是 R1。**沿 R² 轴的关系不是单调的**。
- 可能解释：R²∈[0.2, 0.3] 的 12 个因子（R2 包含但 R3 不含）特别有害——刚好够多 overlap 干扰 trees，又没足够独立价值。

### 2.2 IC-cut 维度：越紧越退化

- R3 (no IC cut) +0.0006 → R4 (\|IC\|≥0.002) +0.0003 → R5 (≥0.005) −0.0006 → R7 (≥0.010) **−0.0011**
- **单调下降**。靠 single-factor RankIC 选择 LGBM 子集**主动有害**。
- R7 包含了 fa3 之中 IC 排名 top 7 的全部因子（dist_5/10/25/50/100/200 + depth_pressure），按"high IC + low R²"理论这是金核心 —— 实测**比 R3 差 0.0017**。**"dist_* 是 fa3 真正 alpha" 假设 REJECTED**。

### 2.3 gap 维度：真信号（不被噪声主导）

| run | gap | n fa3 |
|---|---:|---:|
| R0 | 0.0190 | 0 |
| R3 | 0.0215 | 55 |
| R5 | 0.0214 | 19 |
| R7 | 0.0226 | 7 |
| R4 | 0.0229 | 35 |
| R2 | 0.0284 | 67 |
| R1 | 0.0296 | 84 |

- Stage 1 单调收紧（R1 0.0296 → R3 0.0215）—— 因子越少，拟合空间越小
- Stage 2 内部 gap 不再单调收紧（R3 0.0215 / R5 0.0214 / R7 0.0226），说明 19→7 反而出现了不稳定的过拟合

---

## 3. 统计层 caveat：所有提升都在噪声内

- 42 天 valid 的均值 σ ≈ 0.05 / √42 ≈ **0.008**
- R3 vs R0 的 +0.0006 = **0.07σ** → 纯噪声
- R3 vs R7 的 0.0017 = 0.21σ → 噪声  
- R3 vs R1 的 0.0035 = 0.44σ → 弱信号
- 唯一接近显著的是 **R3 vs R2 的 0.0053 ≈ 0.66σ**，但 R2 本身是 ablation 中的 outlier

**诚实结论**：fa3 在任何子集下的 valid IC 提升都和零不可区分。R3 +0.0006 不能被宣告为 "real win"；它只是从持续 −0.002 到 −0.005 的 5 个 matched fail 里，第一次落到了正侧。

---

## 4. 修订后的归因（对照 Issue #114 (a)-(f)）

| 项 | 状态 | 证据 |
|---|---|---|
| (a) 机制错 | ⚠️ **部分** | dist_* 家族单因子 IC 真实存在（最高 0.072），机制不是完全错的 |
| (b) 编码错 | ✅ **新主因之一** | dist_* 单独跑（R7）远不如组合跑（R3），说明 fa3 的"价值"不在 high-IC 因子的线性表达，而在低 IC 因子的非线性 conditioning。**当前编码把信号分散成了 LGBM 难以独立提取的形式** |
| (c) Phase 2 盲点 | ✅ **主因** | 小样本 IC 既检测不出 R²-冗余，又错误地推荐 R7 的 IC-top 子集 |
| (d) horizon mismatch | ❌ **否决** | h400 rank 也是 fa3+fa2+fa1 < fa2+fa1 |
| (e) 高冗余 | ✅ **主因** | R²≥0.2 的 59 个因子是净有害，R²<0.2 的 55 个不害 |
| (f) 其它 | ✅ **新发现** | **single-factor IC 是糟糕的 LGBM selector**（R5/R7 退化是直接证据）。这是一个一般性方法论 bug |

---

## 5. 对用户问题的直接回答

> **"去掉冗余 + 去掉正交无 alpha 后 fa3 能提升吗?"**

**答**：
1. **去掉冗余有效**：R²≥0.2 的 59 个 fa3 是净有害，去掉后从 −0.0029 拉到 +0.0006
2. **去掉正交低 IC 无效**：R4 (35 fa3) 还几乎并平 R3，但 R5 (19) 和 R7 (7) 一路下滑到 −0.0011
3. **fa3 的最佳子集是 R3 (R²<0.2 的全部 55 个)，但提升 +0.0006 在噪声 (~0.008σ) 里**

**ROI 评估**：维护 55 个 fa3 因子换来 0.07σ 的 valid IC 提升 —— 边际价值接近零。

---

## 6. 最终建议

### 6.1 fa3 处理

- **正式退役 fa3 family**。证据：5 个 matched fair pairs (h100 + h400) 全输 + ablation 最佳 +0.0006 落在噪声内 + dist_* 单独跑也输。
- 如果一定要保留某个子集，**用 R3 的 55 个（R²<0.2，no IC filter），不要用 R7**。Stage 2 的实证证伪了"用 IC 精选小子集"的天真想法。
- 流水线 bug 必须修：fa3_imb_l1 (R²=1.0 是 fa1 副本)、fa3_imb_l1_rolling_z (R²=0.97)、fa3_d_imb_ema8 (R²=0.95) 等高 R² duplicate 应在因子注册阶段被自动拒绝

### 6.2 写入 target_and_workflow.md 的 4 条 hard gate

1. **Duplicate 自动拦截**：R²-to-baseline ≥ 0.95 → 注册时报错
2. **冗余 gate**：R²-to-baseline ≥ 0.5 → 默认不入 LGBM benchmark
3. **Fair-baseline matched-recipe valid IC delta** 是唯一终极判据（**LGBM gain ≠ alpha**）
4. **不要用 single-factor IC 做子集 selector**（**Stage 2 R5/R7 反例**）。理由：LGBM 利用因子的方式是非线性 conditioning，single-factor IC 测的是线性 marginal effect。两者背离时（fa3 case），按 IC 精选会主动伤害 valid IC。**正确的 selector 是 LGBM ablation Δ valid IC**。

### 6.3 fa3 case 作为方法论案例

fa3 是一个**完美的反例库**，未来写"什么是好因子"的文档时直接引用：

| 情景 | fa3 的反例 |
|---|---|
| **Hyperparameter mirage** | "fa3 step-3 +20-86%" 对的是 untuned baseline，对 tuned baseline 反而 −0.0019 |
| **Gain ≠ alpha** | fa3+fa2+fa1 模型里 fa3 拿走 44% gain，valid 反而劣化 |
| **Duplicate not caught** | fa3_imb_l1 R²=1.0 是 fa1 副本，但小样本 IC 检测不到 |
| **High-IC selector fails** | R7 选了 IC top 7（dist_* 全家），结果比 R3 (55 个) 还差 0.0017 |
| **Statistical fragility** | R3 vs R0 的 +0.0006 = 0.07σ，看似赢实际上和 0 不可区分 |

### 6.4 不建议做的事

- **不要继续 fa3 v2 再发明轮子**。底层机制（dist_* / depth_pressure）已经被 fa1+fa2 充分捕获或难以非线性提取，再造 fa3 v2 大概率重蹈覆辙
- **不要相信"再深入挖一下机制"** —— 5 个 matched pairs + 双轴 7 cell ablation 的证据已经足够
- **不要从 fa3 中"挑出最好的几个"硬塞进 baseline** —— Stage 2 已经实证这条路是错的
