# Crypto 投研 SOTA Snapshot

> **用途**：记录"截至本日"的 SOTA 状态——当前 LGBM 预测信号最佳组合是哪几个因子集、多少个因子、关键指标如何、对应回测结果如何。作为后续研究的比较基线。
>
> **语义**：本文件只反映 **current**（最新 benchmark refresh 后的真相），不维护历史最佳。历史进程请查 `sota_archive/` 归档 + `research_updates.md` changelog。
>
> **维护方式**：由 `/crypto-meta-review` skill 在用户确认后覆盖。**agent 不得擅自修改**。每次覆盖前先归档旧版到 `sota_archive/sota_snapshot_{old_date}.md`。

---

## Snapshot 元数据

- **本次 snapshot 日期**：2026-05-25
- **上次 snapshot 日期**：2026-04-17（Bootstrap）
- **最后一次 benchmark refresh 日期**：2026-04-22（**Refresh #1**，campaign #123 E2 决策日）
- **研究 session 覆盖到**：`crypto_ob_research/65-queue_survival_panel`（编号最大 #65，停在 Phase 1，无 `factor_definition.md`）
- **FA 覆盖到**：`factor_agent_docs/FA4_factor_list.md`
- **realize pool 覆盖到**：`zebra_pool/fa4/`

---

## §1 当前 SOTA 组成

> ⚠️ **2026-04-19 label 大迁移**：当前 SOTA 已经是 **mid-label** 主口径（issue #119），与 2026-04-17 Bootstrap 版的 close-label SOTA 不可直接对比。详见 `target_and_workflow.md` §1.2.1 + §1.6 mid-label 主口径条款 + `sota_archive/sota_snapshot_2026-04-17.md` 归档版。

### 1.1 因子集构成

> 本表分两层：**Factor Pool**（所有已落地的因子库）与 **SOTA 模型输入**（当前 SOTA 模型实际使用的特征子集）。
> SOTA 模型现为 **mid-label** FI top100（campaign #123 E2 决策，2026-04-22）。FA3 与 FA4 已完成工程落地并存于 factor pool，但 campaign #123 多维证据均显示净负向或 marginal，当前 SOTA 模型**均不选用**。

| 因子集 | 因子数 | 工程状态 | 数据覆盖 | 来源研究 | 进入当前 SOTA 模型？ |
|--------|-------:|---------|---------|---------|---------------------|
| f001 (base30) | 30 | ✅ Production | 2024-01-01 ~ 2024-12-31 | baseline（bar 元数据层） | 否 |
| f002 | 39 | ✅ Production | 2024-01-01 ~ 2024-12-31 | baseline | 否 |
| fa1 | 123 | ✅ 已落地 | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #1-20 | ✅ 部分（**57** 入选 mid FI top100） |
| fa2 | 75 | ✅ 已落地 | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #21-34 | ✅ 部分（**43** 入选 mid FI top100） |
| fa3 | 114 | ✅ 已落地 | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #35-51 | ❌（#114 双层失效 + campaign #123 mid-label 重验仍负） |
| **fa4** | **55** | ✅ 已落地（工程 54） | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #42 + #52-64（14 项） | ❌（campaign #123 E4 Valid Top0.1% 6.99 < E2 8.82；ckpt4 加 fa4 后 Top0.1% 跌到 7.66） |
| **Factor Pool 合计** | **436** | — | — | — | — |
| **SOTA 模型输入数** | **100** | mid FI top100 = LGBM gain Top 100 of mid-label fa1+fa2 (198) | — | — | — |

### 1.2 LGBM SOTA 指标

- **Analyzer 报告路径**：`/data/db/crypto/analyzer/campaign123_clean_sota/E2_mid_sota100/clip/report.md`
- **Benchmark 目录**：`/data/db/crypto/analyzer/campaign123_clean_sota/E2_mid_sota100/clip/`（Refresh #1）
- **LGBM 模型路径**：`/data/db/crypto/analyzer/campaign123_clean_sota/E2_mid_sota100/clip/lgbm_model.txt`
- **训练信息**：`/data/db/crypto/analyzer/campaign123_clean_sota/E2_mid_sota100/clip/lgbm_train_info.json`
- **Whitelist**：`/home/cken/crypto_world/research/ic_fa1234_mid/wl_mid_fi_top100.txt`
- **Horizon**：`next100`（Amount bar，约 5 分钟 wall-clock）
- **Label 口径**：**mid-to-mid**（`mid[t+h]/mid[t]-1`，mid 来自 basic_table 的 bar 级 L1 midpoint）
- **信号模式**：`clip 0.01`（|y| > 0.01 NaN，excl 20251010 + ETHUSDT/2025-08-29）
- **Train/Valid 切分**：时间顺序 168/42 天（train 2025-07-01 ~ 2025-12-15 / valid 2025-12-16 ~ 2026-01-26）
- **样本数**：n_train = 24,684,814 / n_valid = 3,530,798
- **LGBM 超参**：learning_rate 0.05 / num_leaves 32 / min_data_in_leaf 100000 / num_boost_round 80 / feature_fraction 0.6 / bagging_fraction 0.8 / bagging_freq 5 / lambda_l2 1.0 / seed 20260112
- **trees (final)**：80（early stopping 未触发）

**关键指标**（实测自 lgbm_daily_ic.parquet）：

| 指标 | Train | Valid |
|------|------:|------:|
| IC | 0.0761 | 0.0616 |
| RankIC | 0.0705 | **0.0579** |
| gap (RankIC) | — | 0.0126 |
| RICIR | 4.14 | **2.68** |
| Valid RankIC pos% | — | **100%** |
| Valid Top0.1% net (bps) | — | **8.82**（campaign #123 全 12 实验最高） |
| Valid Top0.01% net (bps) | — | 6.53 |

**Top 10 特征（LGBM gain ratio，E2 model）**：

| 排名 | 特征 | gain_ratio |
|---:|---|---:|
| 1 | fa2_confirmed_flow_h20 | 8.1% |
| 2 | fa1_stale_log_ratio | 6.8% |
| 3 | fa2_ofi_regime_z | 6.1% |
| 4 | fa1_stale_ema_logmax_50 | 5.8% |
| 5 | fa2_impact_delta_10_100 | 4.3% |
| 6 | fa2_big_interarrival | 4.3% |
| 7 | fa2_big_share_ema60 | 3.0% |
| 8 | fa1_stale_ask_log | 2.6% |
| 9 | fa1_imb_x_herf | 2.6% |
| 10 | fa1_ewm_add_imbalance_60s | 2.6% |

完整 feature importance 表见 analyzer report §7.2 + `updates/20260525_update/reports/ic_fa1234_mid_campaign123_fi_top10.md`。

> **SOTA 选型说明（campaign #123，2026-04-22）**：
> - 12 个对照实验（E1 fa12_full 198 / E2 mid_sota100 100 / E3 fa123_full 312 / E4 fa124_full 252 / E5 full_pool 366 / E6-E9 IC-selected fa3/fa4 子集 / E10 mid_corr_top74 / E11 mid_corr_top148 / E12 full_pool_sota100 100 conditional）
> - 决战 E2 vs E10：E10 metrics 略优（Valid RankIC +0.0593 / 最小 Gap / 最高 RICIR），但 **E2 的 price path 更稳 + Valid Top0.1% net 8.82 vs 7.70**
> - 最终采纳 E2，**关键教训**：SOTA 不能只看 Valid RankIC 单一数字，须叠加 price path + Top0.1% net bps（沉淀进 memory `[[feedback_sota_judgement_multi_metric]]`）
> - 详见 `updates/20260525_update/reports/ic_fa1234_mid_campaign123_metrics.md`
> - 后续 ckpt4_clean (E2+54 fa4) 验证：Valid Top0.1% 退化到 7.66，再次证明 fa4 不入 SOTA

### 1.3 SOTA 回测结果

**回测锚点（2026-04-23 升级到 mid SOTA）**：`/home/cken/crypto_world/zebra/bt_output/E2_mid_sota100_q999_close_m05_consec3/`（E2 mid_sota100 模型 / q99.9 入场 / close=-0.5 持仓延迟退出 / 3 consecutive bars gating，与上版 Exp D 同 recipe）

**关键指标**：

| 指标 | Train (162 天) | Valid (40 天) | 合计 (202 天) |
|------|------:|------:|------:|
| Net PnL (USDT) | +1,822 | +7 | **+1,830** |
| Net Rate (bps) | +1.88 | +0.04 | — |
| **Sharpe** | **7.93** 🥇 | **+0.16** 🆕 由负翻正 | — |
| MaxDD (USDT) | −62 | −146 | — |
| Roundtrips | 14,267 | 2,850 | 17,117 |
| Avg Daily RTs | — | — | 84.7 |
| Win Days | 100/162 (62%) | 18/40 (45%) | — |
| Avg Win Rate | — | — | 51.8% |

**回测参数说明**：

- **交易模式**：long-only, taker-entry / maker-exit（15s 超时转 taker）
- **信号入场阈值**：q99.9（在 E2 mid_sota100 训练段 distribution 上计算）
- **信号退出逻辑**：`close_long_bps = -0.5 bps` + `close_consecutive_bars = 3`
- **手续费**：~0.74 bps/RT（fee_rate 固定，含 entry + exit）
- **滑点模型**：Zebra BT 引擎（50ms latency，hysteresis 3 bps，exit_replace 5s）
- **Notional**：1,000 USDT / 笔
- **数据纪律**：excl 20251010 + ETHUSDT/2025-08-29（与 analyzer 一致）
- **完整报告**：`/home/cken/crypto_world/zebra/bt_output/E2_mid_sota100_q999_close_m05_consec3/report.md`

**辅助 BT 对照**（pure-cross recipe，无 close gating）：

| BT 名 | Total Net | Train Sharpe | Valid Sharpe |
|---|---:|---:|---:|
| `E2_q999_pure_cross` | +219 | 1.73 | 0.55 |
| `E2_q9995_pure_cross` | _见报告_ | — | — |
| `ckpt4_clean_q999_pure_cross` (E2+54 fa4) | +268 | 1.63 | 3.30 |
| `ckpt4_clean_q9995_pure_cross` | +705 | — | — |

> ckpt4_clean (E2+fa4) 在 pure_cross 下 Valid Sharpe 3.30 高于 E2 的 0.55，提示 fa4 在去掉 close gating 后可能在 Valid 期有边际价值——但 Top0.1% net 退化 + Train 不稳，暂不作为新 SOTA 候选；issue #124 评价体系迭代后再统一评估。

**相对上版 SOTA（Bootstrap #0 close-label）的改善**：

| 维度 | Bootstrap #0 (close-label Exp D) | **Refresh #1 (E2 mid_sota100, Exp D recipe)** | 改善 |
|---|---:|---:|---|
| Valid RankIC | 0.0427 | **0.0579** | **+36%** |
| Gap RankIC | 0.0208 | 0.0126 | 缩小 39% |
| Total Net (USDT) | +1,650 | +1,830 | +11% |
| Train Sharpe | 6.63 | 7.93 | +20% |
| **Valid Sharpe** | **−1.29** | **+0.16** | **由负翻正** |
| MaxDD (Train) | −109 | −62 | 缩小 43% |

**选型依据**：
- mid-label 修复了 close-bias 导致的 Valid alpha 衰减（Phase 7 归因：close-basis "+7.61 bps Top0.1% alpha" 几乎 100% 是 close→mid reference bias，详见 `updates/20260525_update/reports/analyzer_bt_gap_PHASE7_REPORT_FINAL.md`）
- campaign #123 12 个对照中 E2 是 mid-label 多维最优（Top0.1% net 最高 + price path 最稳）
- 同 recipe (Exp D: close=-0.5, consec=3) 直接对比，BT 全维度优于上版

**历史变迁**：
- 2026-04-17 Bootstrap #0: close-label `fi_top100_mdil100k`, Total +642 / Valid Sharpe −3.32
- 2026-04-18 Exp D 升级: 仍 close-label, Total +1,650 / Valid Sharpe −1.29
- 2026-04-19 label 大迁移启动（issue #119）：basic_table 上线，整池 mid 化
- 2026-04-22 **Refresh #1**: mid-label E2 mid_sota100 锁定为新 SOTA，Total +1,830 / Valid Sharpe +0.16

**Alpha 衰减状态**：**已修复**（mid-label 切换后 Valid Sharpe 由 −1.29 翻正到 +0.16）。先前怀疑的"结构性 alpha 衰减"被 Phase 7 证明主要是 close-bias artifact，不是真实信号衰减。

**关联 Issue**：
- issue #116: Bootstrap #0 set 过程（已被 Refresh #1 取代，建议关闭）
- issue #117: analyzer vs BT capture gap 深度归因 + Exp D 选型依据（Phase 7 完成）
- issue #119: Spread 分布研究 + Label/Net-Return 口径评估（mid-label 主口径确认）
- issue #121: basic_table 底表实现（已上线）
- issue #122: FA3/FA4 mid-label 重验 campaign（E2 SOTA 决策）
- issue #124: Analyzer RankIC vs BT PnL 评价体系迭代（OPEN，下一轮 SOTA 决策前需先解决）

---

## §2 研究管线累计状态

| 类别 | 累计数 | 备注 |
|------|-------:|------|
| research session 总数（编号） | **65** | `crypto_ob_research/1-*` ~ `65-*`；`#65 queue_survival_panel` 停在 Phase 1 无 factor_definition.md |
| 完成 session（有 factor_definition.md） | ≥64 | 已编译入 FA1/FA2/FA3/FA4 覆盖 #1-64；#65 未完成 |
| Failed / Interrupted session | 4（known） | #9 neg / #15 OOS fail / #18 stub / #23 dup |
| factor list (FA) 总数 | **4** | FA1 / FA2 / FA3 / FA4 |
| realized pool 总数 | **4** | fa1 (123) / fa2 (75) / fa3 (114) / fa4 (54) + baseline f001/f002/f001_f002_merged |
| **benchmark refresh 次数** | **2** | Bootstrap #0 (close-label FI top100) + **Refresh #1 (mid-label E2 mid_sota100)** |
| 待编译 session 数 | **0** | FA4 已合编完成；#65 在 Phase 1 不构成"待编译" |

---

## §3 开放研究方向 / 待关注模式

1. **下一轮 deep-research 的对标基线**：E2 mid_sota100 / Valid RankIC 0.0579 / Top0.1% net 8.82 bps。新因子若不能显著提升这两个数（叠加 price path 稳定性）则不进 SOTA。
2. **fa3 + fa4 双失效闭环未根本解决**：连续两个 FA 进 pool 不入模型。issue #114（fa3 失效归因）+ #122（mid-label 重验）均指向同一 root cause（研究阶段评价标准与 SOTA 决策标准脱节）。下一轮 FA 之前建议：
   - 同步 `crypto-deep-factor-research` SKILL.md 到 friction_knowledge_base + Studies #53-64 实践（issue #114 v2 4 条 hard gate）
   - 把 Phase 3 评价从单因子 IC + LGBM 联合 IC 扩展到 price path + Top0.1% net bps（与 SOTA 决策口径对齐）
3. **Stage 5 benchmark refresh skill 化**：Refresh #1 完全 ad-hoc（脚本 + 决策都在 `research/ic_fa1234_mid/` 临时目录），未沉淀为 skill。**Refresh #2 之前必须形成 repeatable**（与 `crypto-meta-review` 同层的 `crypto-benchmark-refresh` skill）。
4. **评价体系迭代（issue #124）优先级最高**：Analyzer RankIC ↔ BT PnL gap 是当前 SOTA 决策的最大不确定性来源。ckpt4_clean (E2+fa4) 在 RankIC 接近 + Top0.1% 略低的情况下 BT pure_cross Valid Sharpe 反而更高（3.30 vs 0.55），说明评价体系仍有盲点。
5. **session #65 续做**：queue_survival_panel 是下一个 FA（fa5）的第一个候选源，回 crypto 后续 Phase 2-4。
6. **FA3/FA4 库保留但不入模型的长期策略**：已落地的 168 个 fa3+fa4 因子保留在 factor pool 中供后续 regime-gated / conditional 研究对照。

---

## §4 本版 snapshot 生成说明

- **生成来源**：`/crypto-meta-review` 第二次运行（2026-05-25），since=2026-04-17
- **本期 update 子目录**：`updates/20260525_update/`（含 10 份 ad-hoc 报告副本）
- **归档**：旧版本归档于 `sota_archive/sota_snapshot_2026-04-17.md`
- **完整 meta-review 报告**：`reviews/meta_review_2026-05-25.md`
- **核心决策依据原始报告**：
  - `updates/20260525_update/reports/analyzer_bt_gap_PHASE7_REPORT_FINAL.md`（issue #117 → #119 触发）
  - `updates/20260525_update/reports/ic_fa1234_mid_campaign123_metrics.md`（E2 SOTA 决策矩阵）
  - `updates/20260525_update/reports/spread_distribution_BT_MIDLABEL_REPORT.md`（mid-label BT 全量回测）
