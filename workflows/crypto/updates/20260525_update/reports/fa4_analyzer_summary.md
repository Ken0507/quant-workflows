# FA4 Analyzer 完整 Metrics 汇总

Date: 2026-04-17 UTC+8
Source: `/data/db/crypto/analyzer/fa4/`
Raw metrics JSON: `analyzer_all_metrics.json`

## 1. 数据集配置

- **日期范围**：2025-07-01 ~ 2026-01-26 (210 天)
- **Symbols**：BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT
- **Train/Valid**：168 天 / 42 天，80/20 时间切分 (train 2025-07-01~2025-12-15, valid 2025-12-16~2026-01-26)
- **Main horizon**：next100 (AmountBar 时间轴，约 5 min wall-clock)
- **Excluded**：20251010 (极端行情)

四份报告共用 LGBM 参数：
- `learning_rate=0.1, num_leaves=32, min_data_in_leaf=10000, n_jobs=8, seed=20260112`

## 2. 四份报告一览

| # | 数据集 | Label Mode | #Factors | 样本数 | 输出路径 |
|:-:|--------|-----------|---------:|-------:|---------|
| A | `fa4_merged_for_report/fa4_full` | clip 0.01 | **54** | n_train=24.70M / n_valid=3.53M | `/data/db/crypto/analyzer/fa4/fa4_clip001/` |
| B | `fa4_merged_for_report/fa4_full` | rank | **54** | n_train=24.75M / n_valid=3.54M | `/data/db/crypto/analyzer/fa4/fa4_rank/` |
| C | `fa4_sota100_for_report/fa4_sota100_full` | clip 0.01 | **154** (59 fa1 + 41 fa2 + 54 fa4) | n_train=24.70M / n_valid=3.53M | `/data/db/crypto/analyzer/fa4/fa4_merged_sota100_clip001/` |
| D | `fa4_sota100_for_report/fa4_sota100_full` | rank | **154** | n_train=24.75M / n_valid=3.54M | `/data/db/crypto/analyzer/fa4/fa4_merged_sota100_rank/` |

## 3. 核心 IC / RankIC 指标

### 3.1 Train

| 模型 | IC | IC std | **ICIR** | RankIC | RIC std | **RICIR** | IC pos% | RIC pos% |
|------|----:|-------:|---------:|-------:|--------:|----------:|--------:|---------:|
| A: fa4-only clip | +0.0554 | 0.0338 | 1.638 | +0.0416 | 0.0316 | 1.315 | 97.0% | 92.3% |
| B: fa4-only rank | +0.0467 | 0.0253 | 1.843 | +0.0417 | 0.0249 | 1.672 | 97.0% | 95.2% |
| C: fa4+SOTA100 clip | +0.0720 | 0.0309 | 2.330 | +0.0574 | 0.0246 | 2.332 | 99.4% | 99.4% |
| D: fa4+SOTA100 rank | +0.0662 | 0.0260 | 2.545 | +0.0588 | 0.0222 | 2.642 | 98.8% | 99.4% |

### 3.2 Valid (样本外)

| 模型 | IC | IC std | **ICIR** | **RankIC** | RIC std | **RICIR** | IC pos% | RIC pos% |
|------|----:|-------:|---------:|-----------:|--------:|----------:|--------:|---------:|
| A: fa4-only clip | +0.0223 | 0.0513 | 0.434 | **+0.0202** | 0.0414 | 0.488 | 71.4% | 71.4% |
| B: fa4-only rank | +0.0187 | 0.0351 | 0.532 | **+0.0153** | 0.0339 | 0.450 | 71.4% | 66.7% |
| C: fa4+SOTA100 clip | +0.0477 | 0.0363 | 1.315 | **+0.0388** | 0.0287 | 1.350 | 90.5% | 90.5% |
| D: fa4+SOTA100 rank | +0.0506 | 0.0323 | 1.568 | **+0.0444** | 0.0292 | 1.522 | 92.9% | 92.9% |

### 3.3 Train-Valid Gap (过拟合衡量)

| 模型 | Gap IC | **Gap RankIC** |
|------|-------:|---------------:|
| A: fa4-only clip | +0.0331 | +0.0214 |
| B: fa4-only rank | +0.0280 | +0.0265 |
| C: fa4+SOTA100 clip | +0.0243 | +0.0186 |
| **D: fa4+SOTA100 rank** | **+0.0155** | **+0.0143** |

D 最低 gap，表明 fa4 合并到 SOTA 并使用 rank 口径降低了过拟合。

### 3.4 vs SOTA Baseline 对比

**SOTA baseline** (FI top100 = 59 fa1 + 41 fa2, clip 0.01, 相同 train/valid split)：
- Train IC 0.0719 / RankIC 0.0635
- **Valid IC 0.0481 / Valid RankIC 0.0427** (ICIR 暂无，来自 `sota_snapshot.md §1.2`)

| 口径 | fa4+SOTA100 Valid IC | fa4+SOTA100 Valid RankIC | SOTA baseline RankIC | **Δ RankIC** |
|------|--------------------:|-------------------------:|---------------------:|-------------:|
| clip (matched) | 0.0477 | **0.0388** | 0.0427 | **−0.0039** ❌ |
| rank | 0.0506 | **0.0444** | 0.0427 | **+0.0017** ⚠️ |

## 4. Top-K Return（多空头部信号表现）

### 4.1 Top 0.1% (bps, 按日均值；clip 模式单位为 bps，rank 模式为排名空间，不可直接对比)

| 模型 | Train avg-d ret | Train net | Train n | Valid avg-d ret | Valid net | Valid n |
|------|----------------:|----------:|--------:|----------------:|----------:|--------:|
| A: fa4-only clip | +10.06 bps | +8.75 bps | 13,359 | +9.72 bps | +8.38 bps | 2,441 |
| C: fa4+SOTA100 clip | +15.49 bps | +14.62 bps | 9,265 | **+15.42 bps** | **+14.42 bps** | 3,487 |

### 4.2 Top 0.01% (bps, clip 口径)

| 模型 | Train avg-d ret | Train net | Train n | Valid avg-d ret | Valid net | Valid n |
|------|----------------:|----------:|--------:|----------------:|----------:|--------:|
| A: fa4-only clip | +9.14 bps | +8.57 bps | 1,039 | +11.36 bps | +10.57 bps | 238 |
| C: fa4+SOTA100 clip | +7.29 bps | +7.02 bps | 655 | +6.63 bps | +6.20 bps | 384 |

> 注：rank 口径的 top-return 数值在 rank 空间（非 bps），略去。

## 5. Feature Importance

### 5.1 Model A: fa4-only clip — Top-10

| # | Feature | Gain ratio |
|--:|---------|-----------:|
| 1 | fa4_s58_pos25_depthimb_ema16 | 10.66% |
| 2 | fa4_s63_shell_fail_aggr100_count_raw_ema32 | 8.89% |
| 3 | fa4_s58_core_balance_ema16 | 7.49% |
| 4 | fa4_s60_state_balance_ema16 | 7.26% |
| 5 | f_ret_1 | 7.00% |
| 6 | fa4_s56_fragile_gate_signed_count_ema64 | 6.54% |
| 7 | fa4_s63_shell_dual_fail_restore_count_raw_delta8_64 | 6.50% |
| 8 | fa4_s63_shell_fail_passive_rebuild_1s_count_raw_ema32 | 6.41% |
| 9 | fa4_s63_shell_fail_aggr300_count_raw_delta8_64 | 5.25% |
| 10 | fa4_s58_pos1_depthimb_ema16 | 5.04% |

### 5.2 Model B: fa4-only rank — Top-10

| # | Feature | Gain ratio |
|--:|---------|-----------:|
| 1 | f_ret_1 | 16.69% |
| 2 | fa4_s58_pos25_depthimb_ema16 | 9.49% |
| 3 | fa4_s58_core_balance_ema16 | 6.47% |
| 4 | fa4_s56_fragile_gate_signed_count_ema64 | 6.44% |
| 5 | fa4_s63_shell_fail_passive_rebuild_1s_count_raw_ema32 | 6.37% |
| 6 | fa4_s63_shell_fail_aggr100_count_raw_ema32 | 6.15% |
| 7 | fa4_s60_state_balance_ema16 | 5.00% |
| 8 | fa4_s63_shell_fail_aggr300_count_raw_delta8_64 | 4.34% |
| 9 | fa4_s56_fragile_gate_signed_count_ema16 | 3.89% |
| 10 | fa4_s54_core_dir_highcontam_raw | 3.66% |

### 5.3 Model C: fa4+SOTA100 clip — Top-10

| # | Feature | Gain ratio |
|--:|---------|-----------:|
| 1 | fa1_stale_ema_logmax_50 | 9.80% |
| 2 | fa2_big_interarrival | 8.86% |
| 3 | fa2_big_share_ema60 | 4.29% |
| 4 | fa1_ewm_add_imbalance_60s | 3.75% |
| 5 | fa2_crossover_20_100 | 3.15% |
| 6 | fa1_buy_sell_spread_proxy_ema20 | 2.75% |
| 7 | fa2_awsi_side_asym | 2.59% |
| 8 | fa2_awsi_ema20 | 2.47% |
| 9 | fa1_mom_imb_2s_minus_10s | 2.27% |
| 10 | fa2_impact_wt_dir_200 | 2.21% |

### 5.4 Model D: fa4+SOTA100 rank — Top-10

| # | Feature | Gain ratio |
|--:|---------|-----------:|
| 1 | fa1_stale_ema_logmax_50 | 6.36% |
| 2 | fa2_big_interarrival | 5.34% |
| 3 | fa2_samepx_break_buy | 4.95% |
| 4 | fa1_run_composite | 4.92% |
| 5 | fa2_crossover_20_100 | 4.10% |
| 6 | fa1_bar_return_momentum | 3.31% |
| 7 | fa1_pen_abs_mean_raw | 2.65% |
| 8 | fa1_ewm_add_imbalance_60s | 2.54% |
| 9 | fa2_ier_ema10 | 2.43% |
| 10 | fa2_ac100_x_imb | 2.30% |

### 5.5 fa4 在合并模型中的贡献分布

| Model | Top-20 fa4 count | Top-50 fa4 count | **Gain share by group** |
|-------|:----------------:|:----------------:|-------------------------|
| C: fa4+SOTA100 clip | **1/20** | 7/50 | fa1=45.8% · fa2=44.8% · **fa4=9.4%** |
| D: fa4+SOTA100 rank | **0/20** | 2/50 | fa1=51.1% · fa2=42.9% · **fa4=5.5%** |

**fa4 最强入选 (merged clip)**：
- rank 12: `fa4_s58_pos25_depthimb_ema16` (2.07%) — G4 relocation gradient primary
- rank 28: `fa4_s58_core_balance_ema16` (1.13%)
- rank 37: `fa4_s56_fragile_gate_signed_count_ema64` (0.83%)
- rank 43: `fa4_s60_state_balance_ema16` (0.68%) — G5 WARNING factor 竟进前 50
- rank 44: `fa4_s63_shell_fail_passive_rebuild_1s_count_raw_ema32` (0.64%) — G6 WARNING

**观察**：fa4-only 表中名列前茅的因子 (s58/s63/s60)，在 fa4+SOTA100 合并后排名跌出前 10，被 fa1/fa2 的成熟信号 (stale_ema, big_interarrival 等) 覆盖。**fa4 与 SOTA100 存在明显特征冗余**，gain share 仅 9.4%/5.5%，低于其因子数占比 (54/154 = 35.1%)，说明 fa4 平均"效率" (gain per factor) **约为 fa1+fa2 的 1/4 ~ 1/6**。

## 6. 决策依据

按 `sota_snapshot.md §3.2` 与 issue #114 v2 的 "fair-baseline matched-recipe valid IC delta 为唯一终极判据" 标准：

| 判据 | 口径 | 结果 | 结论 |
|------|:----:|:----:|------|
| Δ Valid RankIC ≥ 0 (hard gate) | **clip** | **−0.0039** | ❌ 不满足 |
| Δ Valid RankIC ≥ 0 | rank | +0.0017 | ⚠️ 边缘合格 |
| Train-Valid Gap < SOTA baseline | D: rank | 0.0143 < 0.0208 | ✅ |
| Gain share ≥ N/N_total (35.1%) | — | 5.5%-9.4% | ❌ 严重低于期望 |
| Top-20 feature count ≥ expected (~7) | — | 0-1 | ❌ |

**综合判断**：fa4 保留在 factor pool，但**不建议入当前 SOTA 模型特征集**。与 fa3 处理相同。

## 7. 实现限制对 alpha 上限的影响

详见 `issue.md`，关键近似：
1. **G5/G7 deferred OB snapshot**：用 event-time 近似 scheduled time，对精确的 t0+10/50/200ms post-event state 有影响
2. **G3 #56 500ms window**：用 L2 delta 累加近似 (`new_amount - old_amount`)，band 定义 touch ≤3bps / deep 3-10bps
3. **G5 head_raw**：`1/agg_count` 近似 `max_trade_qty/qty_sum`，对多 agg cluster 的 head/cascade 分流有影响
4. **G1 contam_ratio**：OB-state 近似替代 trade-flow 测量
5. **G6 gate**：连续近似（但 G6 是 WARNING-RESERVE_ONLY，spec 本就接受近似）

若未来重做 fa4，建议：
- 修改 Zebra framework 支持真正的 time-scheduled OB snapshot
- 对 G3/G5 primitives 重算并比较 delta vs 当前实现
- 单独 ablation 去掉 18 个 WARNING 因子，看剩 36 个 "normal compliance" 因子的增量
