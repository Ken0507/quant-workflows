# Phase 7: Latency → PnL Realization 深度研究（FINAL）

**Time**: 2026-04-18
**Status**: Valid 分析完整，经三轮 Codex 对抗评审；Train 数据补跑中
**Sample**: Exp C Valid, matched clean **n=280**（Phase 6 common ∩ Phase 7a hs-clean ∩ Phase 7c clean）；mid-basis identity on n=279
**Data**: Tardis L2 incremental (exchange μs) + BT trade/entrust log + Phase1 bars

---

## Executive Summary — 3 key findings (Codex-approved headline set)

**Meta update (Train 结果纳入)**：Train 期 artifact (+11.8 bps) 和 Valid (+11.7 bps) **几乎相同大小**，是 LGBM top-0.1% bars 的 stable structural feature。Train mid-basis alpha evidence is mixed and aggregation-sensitive（episode mean -1.89, (sym,ds) cluster +2.64 p=.009, sym cluster -2.37 p=.008）— **不是 cleanly positive across aggregation levels**。因此：artifact 大小 Train/Valid 一致说明 gap 不是 artifact 主导；而 mid-basis 信号本身较弱、不稳定，可能在 Valid 进一步退化。


1. **Valid 期 close-basis alpha (+7.61 bps) 几乎完全是 reference bias；真实 mid-basis alpha 非正**
   - artifact = close_to_mid_t0 (+12.00) − close_to_mid_t100 (+0.31) ≈ **+11.70 bps**（highly cluster-robust）
   - mid-basis fwd100 = **-4.09 bps** 点估计，但 (sym,ds) cluster 下 t=-1.37 p=0.18 **NOT significantly different from 0**
   - 严谨表达：Valid **没有 evidence of positive mid-basis alpha**；close-basis alpha 完全由 entry-bar close-to-mid bias 解释

2. **Phase 6 的 +8.47 bps entry_slip 其中 82% 是 close-basis reference artifact**
   - Same-time decomposition: Term1 (fill - mid_fill) = **+1.55 bps** ≈ 真正 taker 执行成本（half-spread + impact）
   - Term2 (mid_fill - close_fill_bar) = **+6.92 bps** = bar close 深在 bid stack (85.7% 的 fill_bar close 低于 best_bid at T0)
   - Reconstruction residual 0.07 bps（exact）

3. **在固定 realized exit 下，更早 entry (Δ=0 vs Δ=50ms) 让 PnL 平均差 2.84 bps**；post-trigger timing drag 最大的来源是 **passive maker-exit queue wait**（~1.86s），不是 entry 的网络延迟
   - Δ=0 vs Δ=50 cluster-robust: (sym,ds) t=-7.59 p<0.0001, day t=-6.93, sym t=-3.49
   - Passive exit queue drift 期间 mid 漂移 **-6.13 bps**（1.86s maker wait while market continues dropping）
   - **术语澄清**：maker queue 是 **decision-to-fill passive wait**，不是网络 latency；不能据此推论 "生产应延长 entry latency"

---

## 1. 方法论

### 1.1 Sample hierarchy

| Level | n |
|---|---|
| Exp C Valid 全部 | 321 |
| Phase 6 common sample (entry_fwd100_clipped.notna()) | 294 |
| + Phase 7a hs>0 all delays (clean) | 280 |
| + Phase 7c mid@t0 & mid@t100 有效 | 280 matched |
| + Phase 7e mid@exit_trig & mid@exit_fill (mid-identity) | 279 |

### 1.2 L2 重建
- Tardis `incremental_book_L2`, exchange timestamp (μs)
- 顺序扫描，dict[price]=amount，amount=0 删除
- Snapshot at 目标 exchange ns before next update
- 过滤: 要求 all-delay `hs>0` (过滤 Tardis 漏 cancel 造成的 crossed dust) — 丢弃 14/294 episodes

### 1.3 BT 设置 (Exp C)
- Taker entry (`use_maker_entry=False`)
- Maker exit with 15s timeout fallback (`use_maker_exit=True`, `exit_market_timeout_ms=15000`)
- `latency_ms=50` 硬编码（entry 网络延迟模拟）
- Entry 实测延迟: p50=51ms, p99=96ms
- Exit 实测延迟: mean=1.86s, p95=6.7s, max=15s（**maker queue，不是网络延迟**）

### 1.4 Unified episode key
Phase 7a 使用 Phase 6 common sample re-index; Phase 7c 使用 Phase 4 full Valid re-index — ep_global_idx **不对齐**。统一用 `(sym, episode)` tuple 作为 key（Codex R2 提出）。

---

## 2. 核心结果

### 2.1 Mid drift 曲线（matched n=280）

| Δ (ms) | mid_drift mean | mid_drift median | half-spread mean |
|---|---|---|---|
| 0 | 0.00 | 0.00 | 1.30 |
| 10 | -0.55 | 0.00 | 1.65 |
| **50** | **-3.69** | **-2.55** | **2.15 (peak spike)** |
| 100 | -4.00 | -2.89 | 1.40 |
| 500 | -5.11 | -4.01 | 1.13 |
| 1000 | -5.98 | -4.71 | 0.95 |
| 2000 | -5.65 | -4.62 | 1.00 |

frac(drift>0) at 50ms = 21%, at 1s = 28% — 系统性负漂移。

Pre-trigger 窗口（Phase 7b, -500 → 0ms）: 均值 +0.3 至 +1.2 bps, 点估计 positive。所以触发时刻附近 market 有 heterogeneous micro-regimes（一些在 local high 回落，一些在 sell sweep 尾部继续下跌 — 见 case studies）。

### 2.2 Entry slip 同时点分解（matched n=280）

```
P6 entry_slip_bps = (fill_actual - close_fill_bar) / close_fill_bar × 1e4
                 = Term1 + Term2
Term1 = (fill - mid_fill_bar) / mid_fill_bar × 1e4           [pure execution cost at fill time]
Term2 = (mid_fill_bar - close_fill_bar) / mid_fill_bar × 1e4 [close-vs-mid reference bias]
```

| | Mean | Median |
|---|---|---|
| P6 entry_slip (close-basis) | +8.47 | +7.20 |
| Term 1 (pure exec @ fill) | **+1.55** | +0.80 |
| Term 2 (close vs mid @ fill) | **+6.92** | +5.71 |
| Reconstruction residual | +0.07 (additive approximation, near-exact) | — |

Separate: drift T0 → entry_fill (50ms): mean -3.70, median -2.52（not part of slip by definition; this is market moving during delay — below）

**机制**: 85.7% 的 fill_bar close 低于 best_bid(T0)，均值偏低 9.25 bps. 这和 half-spread 只 ~1.3 bps 的事实结合说明：bar 的 close_price 不仅是 bid-side（half-spread 能解释），而是 **last trade 是 aggressive sell sweep 的尾部成交，落在 bid stack 的更深 levels**。

### 2.3 fwd100 "alpha" 是 close-basis artifact

对每个 episode 测 `mid@entry_bar` 和 `mid@entry_bar+100`（matched clean n=280）。

```
fwd100_close = (close_{t+100} - close_t) / close_t × 1e4
fwd100_mid   = (mid_{t+100}   - mid_t)   / mid_t   × 1e4
artifact     = fwd100_close - fwd100_mid
             = close_to_mid_t0 - close_to_mid_t100
```

Identity closes: LHS +7.61 vs RHS +7.58, residual 0.03 bps ✓

| | Mean | (sym,ds) cluster | Episode t/p | (sym,ds) t/p |
|---|---|---|---|---|
| fwd100_close | **+7.61** | +8.81 | +3.93 / <.001 *** | +3.91 / <.001 *** |
| **fwd100_mid** | **-4.09** | -2.77 | -2.13 / .034 ** | **-1.37 / .18 (NS)** |
| artifact | +11.70 | +11.58 | +22.17 / <.0001 *** | +19.43 / <.0001 *** |
| close_to_mid_t0 | +12.00 | +12.04 | +24.58 / <.0001 *** | — |
| close_to_mid_t100 | +0.31 | +0.48 | +1.12 / .26 | +1.28 / .20 |

**Codex-approved wording**：
> Valid top-0.1% close-basis alpha (+7.6 bps) is cluster-robust positive. Mid-basis point estimate (-4.1 bps) is not statistically distinguishable from zero under (sym,ds) clustering. The close-to-mid reference bias (+11.7 bps) fully accounts for the close-basis positive alpha. **No evidence of positive mid-basis alpha in Valid**.

Per-symbol:
| Sym | n | close | mid | t0_bias | t100_bias |
|---|---|---|---|---|---|
| ADA | 19 | +7.84 | -2.10 | +10.52 | +0.58 |
| BNB | 9 | -1.81 | -11.44 | +10.43 | +0.79 |
| BTC | 1 | +11.68 | +5.14 | +8.14 | +1.60 |
| DOGE | 81 | +6.63 | -7.68 | +14.40 | +0.09 |
| ETH | 79 | +8.92 | -2.47 | +11.79 | +0.41 |
| SOL | 69 | +8.30 | -2.71 | +11.28 | +0.27 |
| XRP | 22 | +10.68 | -0.28 | +12.97 | +2.01 |

5/7 symbols (ADA, BNB, DOGE, ETH, SOL) mid-fwd100 负; BTC 太少 (n=1); XRP ≈ 0.

### 2.4 Counterfactual entry-latency (matched n=280, fixed exit)

用 proper exit VWAP (= Σsell_notional/Σsell_qty, 76% 多笔 sell):

| Δ(ms) | cf_net mean | ΔPnL vs actual mean |
|---|---|---|
| 0 | -10.00 | **-4.81** |
| 50 | -7.16 | -1.97 (residual from `fill_buy_vwap` vs actual BT fill basis) |
| 500 | -4.77 | +0.43 |
| 1000 | -3.66 | **+1.54 (peak)** |
| 2000 | -4.00 | +1.20 |

Paired Δ=0 vs Δ=50:
| Cluster | n | mean diff | t | p |
|---|---|---|---|---|
| Episode | 280 | -2.84 | -6.48 | <.0001 |
| (sym,ds) | 88 | -3.30 | -7.59 | <.0001 |
| Day | 34 | -4.06 | -6.93 | <.0001 |
| Sym | 7 | -3.49 | -3.49 | .013 |

**Codex-approved safe wording**：
> On the matched Valid sample, **holding realized exits fixed**, replacing the observed ~50ms entry with 0ms entry worsens counterfactual PnL by 2.84 bps on average. This is not evidence that production should delay entry; exit policy would also change.

### 2.5 Mid-basis identity (matched n=279)

Identity 用 exact VWAP-return basis (Codex R3 correction)：

```
pnl_vwap_bps = (exit_vwap / entry_vwap - 1) × 1e4
            = drift_{entry_fill → exit_fill, mid} - entry_slip_mid + (-exit_slip_mid)
```

where:
- `entry_slip_mid = (entry_vwap - mid_entry_fill) / mid_entry_fill × 1e4`  (> 0 = paid above mid)
- `exit_slip_mid = (mid_exit_fill - exit_vwap) / mid_exit_fill × 1e4`  (> 0 = sold below mid)

| Term | Mean | Median |
|---|---|---|
| pnl_vwap_bps (reference) | -4.65 | -1.35 |
| drift entry_fill → exit_fill (mid) | -5.73 | -3.14 |
| entry_slip_mid | +1.55 | +0.80 |
| exit_slip_mid | **-2.65** | -0.45 |
| **reconstructed pnl_vwap** = drift - entry_slip - exit_slip | **-4.63** | — |
| **Residual (additive approx)** | **-0.02** | 0 |

**Note**: 真正的 exact identity 是 multiplicative: `exit_vwap/entry_vwap = (exit_vwap/mid_exit_fill) × (mid_exit_fill/mid_entry_fill) × (mid_entry_fill/entry_vwap)`，这个 numerically 闭合。以上 additive bps 分解是一阶近似，residual mean -0.02, std 0.13 bps（即近似误差很小）。

**Note**: BT 报告的 `pnl_asset_bps` 使用 fixed-notional 口径（episode_pnl / 1000 × 1e4），不等于 VWAP-return basis。两者差 mean +1.14 bps (std 24.9, outlier-dominated)。这是 BT 内部 accounting convention 问题，不影响本研究的 mid-basis identity 有效性。

**Drift sub-breakdown** (exact per-term, not summing to total because of compounding in very short moves):

| 时段 | Drift mean (bps) |
|---|---|
| T0 → entry_fill (50ms 网络延迟) | -3.70 |
| entry_fill → exit_trigger (~20s position hold) | **+0.39** |
| exit_trigger → exit_fill (**~1.86s maker queue wait**) | **-6.13** |
| 3-term sum | -9.44 |
| Direct T0 → exit_fill | -9.43 |

**关键发现**: 在 realized exit path 下，**最大的 post-trigger 时机代价来自 exit-side maker queue wait** (-6.13 bps)，不是 entry 侧的 50ms 网络延迟 (-3.70 bps only during entry; but this "helps" us because we fill at lower ask)。

### 2.6 Close-basis vs Mid-basis 对比

| Term | Close-basis | Mid-basis | diff (close bias) |
|---|---|---|---|
| entry_slip | +8.47 | +1.55 | +6.92 |
| fwd100 | +7.61 | -4.09 | +11.70 |

两个 bias 项都是 close_to_mid artifact 在不同 time window 的表现。它们 **不 double-count** 在 realized PnL 里——realized 本身是 VWAP-to-VWAP，不依赖 close reference——但它们分别扭曲了 slip 和 alpha 的解读。

### 2.7 Maker exit 策略评估（谨慎）

- `exit_slip_mid` mean = -2.65 bps（maker 卖在 mid 之上 → 正收益相对 mid）
- 但 median 仅 -0.45 bps；cluster 下显著性有限
- 相对 hypothetical "immediate taker sell at exit_trigger mid" 的 advantage 约 +3.4 bps (from spread + sell above bid)
- **但** maker queue 1.86s 期间 mid drift -6.13 bps，完全覆盖了 maker 的 mid-above 优势
- **净 exit contribution ≈ +2.65 - 6.13 = -3.48 bps**（maker wait drift 大于 spread capture）

谨慎结论：**当前 maker exit 不是 unambiguously effective**。若要优化，方向有二：
- 缩短 timeout（e.g., 3s instead of 15s）减少 queue drift
- 有条件 taker fallback（detect adverse drift → switch to taker immediately）

---

## 3. Case Studies

### Case C: DOGE 2025-12-31 ep=444, net=-19.85 (Valid typical loser)

- T0 mid=0.1220, half-spread 2.46 bps
- 10ms 内 mid 跌到 0.1218（-12 bps）
- 2000ms 累计 mid=0.1216（-30 bps）

Trade tape 2s 窗口 seller aggressor fraction:
| Window (ms) | SELL notional | BUY notional | Seller % |
|---|---|---|---|
| [-50,0] | 482,027 | 300 | 99.94% |
| [0,50] | 50,335 | 1,416 | 97.26% |
| [50,100] | 283,476 | 48 | 99.98% |
| [100,500] | 774,794 | 26,198 | 96.73% |
| [500,2000] | 856,668 | 422,371 | 66.98% |

机制解读: LGBM 在大型 sell sweep 瞬间触发 LONG。这 **不是 "local high 回落"**，是 **sell-sweep 延续**。bar 的 close 被压深入 bid stack → LGBM "看到" close-to-mid bias → 学到 "这种 bias 会 revert"。但实际 price 方向是继续跌，artifact 不能提供 realized return。

### Case A: ADA ep=243, slip=+77.69, net=+9.56 (positive outlier)

信号在强 buy burst 后触发（[-50,0]ms BUY 237k vs SELL 2.7k = 99% buyer aggressor）。50ms 后 spread 爆到 26 bps，mid 跳 +38 bps，我们追高位但后续 100 bars 继续涨（fwd100 +83）。**这是少数 local-breakout continuation 案例，不是 top reversal**。

### 综合: heterogeneous micro-regimes

触发 bar 的 micro-structure 是 **混合**的：
- 部分是 sell-sweep 尾部（Case C 类，多数 loser）
- 部分是 buy-burst 尾部（Case A 类，追涨）
- 共性：last trade 方向 extreme → close_to_mid bias 大 → LGBM 触发

所以 **不能一概说 "信号在 local high 触发"**。正确表述：**触发后的短期价格行为是 adverse selection，方向与信号相反 on average**。

---

## 4. 对 Analyzer & LGBM 的建议

### P0 — 立刻做

1. **Analyzer 加 mid-basis fwd_ret 列**
   - `f_ret_100_mid = (mid_{t+100} - mid_t) / mid_t × 1e4`
   - 并排报告 top-0.1% close-basis vs mid-basis alpha
   - **预期影响**: Valid top-0.1% 从 +7.6 bps 降到 -4 ~ 0 bps

2. **LGBM 重训 with mid-basis label**（等 Train 分析完成后确定）
   - 如果 Train mid-basis alpha 也接近 0 → 模型 never 学到真 alpha，close-basis artifact 是主要信号
   - 如果 Train mid-basis alpha 显著正 → Train 真 alpha 存在，Valid 失效 (regime change)

### P1 — 近期

3. **完整 delayed-entry re-BT** (`latency_ms=500` or higher): verify counterfactual
4. **Exit 策略改造**: test maker timeout=3s, taker fallback，对比 exit_slip + queue drift 总和

### P2 — 长期

5. **Baseline / Exp D 做同样 artifact 分析**: 确认是不是所有配置都有相同程度的 close-basis bias
6. **Microstructure features 减少对 close bias 依赖**

---

## 5. Codex 评审历史

### Round 1（5 blockers, 已修正）
- Reference 未对齐 (trigger_bar vs fill_bar close)
- Term 1 "纯执行成本" 混了 drift + exec
- Counterfactual exit 用 last-fill 错误（76% 多笔 sell）
- "Reducing latency hurts" 过度 generalized
- fwd100 artifact 必须直接测 bar+100

### Round 2（6 blockers, 已修正）
- Phase 7a/7c 的 ep_global_idx 不一致 → 用 (sym, episode) key
- Matched sample is n=280 (非 307 或 other)
- fwd100_mid cluster 下 NS → headline 改为 "no positive evidence"
- close_to_mid_t100 ≠ 0 但不 significant
- 81% / 140% 不是 double count 但需补完 mid-basis identity
- Train 数据必须跑

### Round 3（6 blockers, 已修正）
- phase7e residual 报告错（+1.12 vs actual +4.81 in parquet）
- Residual misdiagnosis — 是 BT fixed-notional vs VWAP-return 口径差，不是 L2 精度
- Drift breakdown arithmetic error (entry_fill → exit_trig 应 +0.39 not -0.19)
- 过度使用 "latency" — maker queue 是 **passive queue wait**，不是网络延迟
- "Maker exit 有效" 过度宣称（median gain ≈ 0, cluster NS）
- "Local high 触发" 过简化（heterogeneous micro-regimes）

---

## 5b. Train 期对照结果（补充，2026-04-18 完成）

Phase 7c Train period: n=2035 → clean n=1986 (97.6%)

| Metric | Train mean | Valid mean | 差异 |
|---|---|---|---|
| fwd100_close_bps | **+9.92** | +7.61 | Train 略高 |
| fwd100_mid_bps | **-1.89** | -4.09 | Train 更接近 0 |
| artifact_bps | **+11.81** | +11.70 | **几乎相同** |
| close_to_mid_t0_bps | +12.51 | +12.00 | 相同 |
| close_to_mid_t100_bps | +0.72 | +0.31 | 都接近 0 |

Train `fwd100_mid` cluster-robust 测试揭示 **sign-inconsistent** 结果：
| Cluster | n | mean | t | p |
|---|---|---|---|---|
| Episode | 1986 | -1.89 | -1.92 | .056 * |
| **(sym,ds)** | 470 | **+2.64** | **+2.63** | **.009 \*\*\*** |
| Day | 134 | +1.75 | +1.34 | .18 |
| **Symbol** | 7 | **-2.37** | **-3.86** | **.008 \*\*\*** |

所有 7 symbols 的 episode-mean fwd100_mid 都是负的（ADA -0.80, BNB -5.21, BTC -3.56, DOGE -1.97, ETH -0.66, SOL -1.57, XRP -2.83），但 (sym,ds) cluster 后变正（多数 sym-days 在小样本里混合）。

**关键结论**：
1. Train 期 artifact 和 Valid 几乎相同大小（+11.8 vs +11.7 bps），是 LGBM top-0.1% bars 的稳定结构性特征，不是 Valid 异常现象。
2. Train mid-basis "alpha" 是 aggregation-sensitive / sign-inconsistent（episode 略负、(sym,ds) cluster 显著正、symbol cluster 显著负）。**不能说"模型从未学到 alpha"，但也不能说"Train 学到了 clean positive mid alpha"——evidence 是 mixed**。

### Train vs Valid 整合叙事

Train: realized BT net ≈ +2.69 bps（来自 Phase 6 close-basis identity）
- fwd100_close +9.92 → fwd100_mid ≈ 0（artifact cancels close alpha）
- 扣除 fee ~1.5 bps + entry exec ~1.5 bps + exit maker gain ~2.5 bps ≈ 约 0（匹配 Train 略正 pnl）

Valid: realized BT net ≈ -5 bps
- fwd100_close +7.61 → fwd100_mid ≈ -4 bps（真实 alpha 轻微负）
- 扣除相同 exec costs ≈ -5 bps（匹配 Valid 实测）

**Train-Valid gap 解读要点**：
- Artifact 大小 stable (+11.8 vs +11.7) → **gap 不是 artifact 主导**
- Mid-basis 信号在 Train 已经 weak / unstable（aggregation-sensitive），在 Valid 进一步退化到更负
- 严格说**不是经典的"regime change"（强 alpha 突然消失）**，更像"弱信号被执行成本放大"

---

## 6. Open Items

1. ~~**Train period analysis**~~ — ✅ 完成（见 §5b）
2. **Delayed-entry full BT** (`latency_ms=500`) 未做
3. **Exit 策略改造 BT** (maker timeout=3s vs 15s) 未做
4. **Baseline + Exp D 的 artifact analysis** 未做

---

## 附录

### 数据文件
- `data/phase7_book_snapshots.parquet` — Phase 7a raw
- `data/phase7_latency_panel_clean.parquet` — clean panel
- `data/phase7b_ext_snapshots.parquet` — extended window -500ms to +60s
- `data/phase7c_valid.parquet` — mid@t0 + mid@t100 (307 clean, phase4-idx)
- `data/phase7d_matched_clean.parquet` — matched n=280 (sym, episode key)
- `data/phase7e_full_identity.parquet` — full mid-basis identity n=279
- `data/phase7_counterfactual_v2_episodes.parquet` — per-ep counterfactual
- `reports/phase7_case_studies.txt` — 5 case L2+trade evolution

### 代码
- `code/phase7_latency_book_replay.py` — main L2 replay
- `code/phase7b_extended_window.py` — -500ms to +60s
- `code/phase7c_fwd100_mid.py` — mid@entry_bar+100
- `code/phase7d_full_mid_identity_v2.py` — matched (sym, episode) join
- `code/phase7e_exit_mid.py` — mid@exit_trig + mid@exit_fill
- `code/phase7_reconcile_v3.py` — entry slip Codex-correct decomp
- `code/phase7_counterfactual_v2.py` — counterfactual with exit VWAP
- `code/phase7_case_studies.py` — case-level L2+trade analysis
