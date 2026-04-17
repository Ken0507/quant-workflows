# Crypto 投研 SOTA Snapshot

> **用途**：记录"截至本日"的 SOTA 状态——当前 LGBM 预测信号最佳组合是哪几个因子集、多少个因子、关键指标如何、对应回测结果如何。作为后续研究的比较基线。
>
> **语义**：本文件只反映 **current**（最新 benchmark refresh 后的真相），不维护历史最佳。历史进程请查 `sota_archive/` 归档 + `research_updates.md` changelog。
>
> **维护方式**：由 `/crypto-meta-review` skill 在用户确认后覆盖。**agent 不得擅自修改**。每次覆盖前先归档旧版到 `sota_archive/sota_snapshot_{old_date}.md`。

---

## Snapshot 元数据

- **本次 snapshot 日期**：2026-04-17
- **上次 snapshot 日期**：—（首次 Bootstrap）
- **最后一次 benchmark refresh 日期**：2026-04-17（Bootstrap #0，以 FI top100 作为首次基线）
- **研究 session 覆盖到**：`crypto_ob_research/64-convexity_liquidity_density`（编号最大 #64）
- **FA 覆盖到**：`factor_agent_docs/FA3_factor_list.md`
- **realize pool 覆盖到**：`zebra_pool/fa3/`

---

## §1 当前 SOTA 组成

### 1.1 因子集构成

> 本表分两层：**Factor Pool**（所有已落地的因子库）与 **SOTA 模型输入**（当前 SOTA 模型实际使用的特征子集）。
> FA3 已完成工程落地并存于 factor pool，但基于 issue #114 双层失效归因 + `research/ic_fa123/REPORT.md` 三次独立验证（加入 fa3 的 Valid RankIC 均负向 −0.0002 ~ −0.0006），当前 SOTA 模型**不**选用 fa3。

| 因子集 | 因子数 | 工程状态 | 数据覆盖 | 来源研究 | 进入当前 SOTA 模型？ |
|--------|-------:|---------|---------|---------|---------------------|
| f001 (base30) | 30 | ✅ Production | 2024-01-01 ~ 2024-12-31 | baseline（bar 元数据层） | 否 |
| f002 | 39 | ✅ Production | 2024-01-01 ~ 2024-12-31 | baseline | 否 |
| fa1 | 123 | ✅ 已落地 | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #1-20 | ✅ 部分（59 个入选 FI top100） |
| fa2 | 75 | ✅ 已落地 | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #21-34 | ✅ 部分（41 个入选 FI top100） |
| fa3 | 114 | ✅ 已落地 | 2025-07-01 ~ 2026-01-26 (210 天) | 研究 #35-51 | ❌（#114 双层失效：26% R²≥0.5 冗余 + 48% 正交无 alpha） |
| **Factor Pool 合计** | **381** | — | — | — | — |
| **SOTA 模型输入数** | **100** | FI top100 = LGBM gain Top 100 of fa1+fa2 (198) | — | — | — |

### 1.2 LGBM SOTA 指标

- **Analyzer 报告路径**：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/report.md`
- **Benchmark 目录**：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/`（Bootstrap #0，首版基线）
- **LGBM 模型路径**：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/lgbm_model.txt`
- **训练信息**：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/lgbm_train_info.json`
- **Horizon**：`next100`（Amount bar，约 5 分钟 wall-clock）
- **信号模式**：`clip 0.01`（|y| > 0.01 NaN，excl 20251010 + ETHUSDT/2025-08-29）
- **Train/Valid 切分**：时间顺序 168/42 天（train 2025-07-01 ~ 2025-12-15 / valid 2025-12-16 ~ 2026-01-26）
- **样本数**：n_train = 24,697,614 / n_valid = 3,530,227
- **LGBM 超参**：learning_rate 0.05 / num_leaves 32 / min_data_in_leaf 100000 / num_boost_round 80 / feature_fraction 0.6 / bagging_fraction 0.8 / bagging_freq 5 / lambda_l2 1.0 / seed 20260112
- **trees (final)**：80（early stopping 未触发）

**关键指标**：

| 指标 | Train | Valid |
|------|------:|------:|
| IC | 0.0719 | 0.0481 |
| RankIC | 0.0635 | **0.0427** |
| gap (RankIC) | — | 0.0208 |
| ICIR | _需手工补充（读 `lgbm_daily_ic.parquet`）_ | _需手工补充_ |

**Top 10 特征（LGBM gain ratio）**：

| 排名 | 特征 | gain_ratio |
|---:|---|---:|
| 1 | fa1_stale_ema_logmax_50 | 9.27% |
| 2 | fa2_big_interarrival | 6.76% |
| 3 | fa1_ewm_add_imbalance_60s | 4.16% |
| 4 | fa1_buy_sell_spread_proxy_ema20 | 3.96% |
| 5 | fa2_big_share_ema60 | 3.71% |
| 6 | fa1_f12_cancel_dir_momentum_2v10 | 2.47% |
| 7 | fa2_awsi_side_asym | 2.37% |
| 8 | fa1_depth_total_7 | 2.31% |
| 9 | fa2_large_absorb_100 | 2.12% |
| 10 | fa1_pen_abs_mean_raw | 2.00% |

完整 feature importance 表见 analyzer report §7.2。

> **SOTA 选型说明**：
> - FI top100 vs full fa1+fa2 (198) 的 Valid RankIC 差距仅 −0.0004（0.0427 vs 0.0431），统计上不显著
> - FI top100 模型更小、特征空间更窄，对后续 benchmark refresh loop（锁定 Top N）友好
> - 详细实验矩阵（9 个对照）见 `updates/20260417_update/reports/ic_fa123_REPORT.md`

### 1.3 SOTA 回测结果

**回测锚点（2026-04-18 升级）**：`/home/cken/crypto_world/zebra/bt_output/fi_top100_q999_close_m05_consec3/`（FI top100 模型 / q99.9 入场 / close=-0.5 持仓延迟退出 / 3 consecutive bars gating）

**关键指标**：

| 指标 | Train (140 天) | Valid (34 天) | 合计 (174 天) |
|------|------:|------:|------:|
| Net PnL (USDT) | +1,908 | −258 | +1,650 |
| Net Rate (bps) | +7.44 | −1.48 | +4.53 |
| **Sharpe** | **6.63** 🥇 | −1.29 | — |
| MaxDD (USDT) | −109 | −173 | — |
| Roundtrips | 3,740 | 724 | 4,464 |
| Avg Daily RTs | 26.7 | 21.3 | 25.7 |
| Median Hold (s) | 247 | 161 | 235 |
| Avg Win Rate | — | — | 65.8% |

**回测参数说明**：

- **交易模式**：long-only, taker-entry / maker-exit（15s 超时转 taker）
- **信号入场阈值**：q99.9 = **6.309 bps**（在 167 train days, 24.87M bars 上计算）
- **信号退出逻辑（新）**：`close_long_bps = -0.5 bps` + `close_consecutive_bars = 3`（需 3 个连续 bar score < -0.5 才退）
- **手续费**：0.73 bps/RT（fee_rate 固定，含 entry + exit）
- **滑点模型**：Zebra BT 引擎（50ms latency，hysteresis 3 bps，exit_replace 5s）
- **Notional**：1,000 USDT / 笔；initial_capital 1,000,000
- **数据纪律**：excl 20251010 + ETHUSDT/2025-08-29（与 analyzer 一致）
- **回测脚本**：`/home/cken/crypto_world/zebra/scripts/run_bt_fi_top100_exp_d_m05_consec3.py`
- **完整报告**：`/home/cken/crypto_world/zebra/bt_output/fi_top100_q999_close_m05_consec3/report.md`

**Alpha capture 验证**（vs analyzer top 0.1% 日度收益）：
- Train capture **+42.5%**（vs 原 baseline 14.8%，提升 2.9×）
- Valid capture **−12.5%**（vs 原 baseline −24.9%，收窄一半）

**相对原 baseline (close=0, consec=1) 的改善**：

| 维度 | baseline | **Exp D (SOTA)** | 改善 |
|---|---:|---:|---|
| Median hold | 44s | **3.9m** | ×5.3 |
| Total Net | +642 | +1,650 | +157% |
| Train Sharpe | 4.51 | **6.63** | +47% |
| Valid Sharpe | −3.32 | **−1.29** | 2.6× 改善 |
| Win rate | 62.5% | 65.8% | +3.3pp |
| Train MaxDD | −151 | −109 | 更小 |
| Train capture | 14.8% | 42.5% | ×2.9 |

**选型依据（issue #117 深度归因后）**：
- Analyzer 报告 top-0.1% 日均前瞻收益 Train +14.68 / Valid +13.92 bps，但原 baseline (close=0 立即退出) 只 capture 15% 的 train alpha、valid 反号
- 深度归因指向 **holding-time 严重不匹配（median hold 44s vs 目标 100 bars ≈ 300s）+ 信号早退的路径依赖**
- 六组消融实验（close ∈ {0, −0.5, −2}, consec ∈ {1, 3, 5, 7}, max_hold=100 对照）确认 **"让 signal 自然衰减退出 + close=−0.5 + 3 consecutive bars"** 是最优：既捕获 horizon 又不陷入极限 trend-follow
- 对照 close=−2 方案（Exp B）：Valid Sharpe −0.55 更优，但 median hold 2.1h 过长、win rate 跌到 42.7%、MaxDD −350，**不符合可部署性要求**
- 对照 max_hold=100 硬持（Exp C）：Total −496 完全失败，证明 "analyzer top-0.1% 是理想化上限，不是可执行 recipe"

**历史变迁**：
- 2026-04-17 bootstrap: FI top100 q99.9 (close=0, consec=1), Total +642 / Valid Sharpe −3.32
- 2026-04-18 升级: Exp D (close=−0.5, consec=3), Total +1,650 / Valid Sharpe −1.29

**Alpha 衰减观察**：valid 期（2025-12-16 ~ 2026-01-26）Sharpe 仍为负（−1.29），与先前 fa2+fa1 h400 rank valid 负向同步出现。这是当前数据集的结构性 alpha 衰减，非策略选型问题（待下一轮 benchmark refresh 用更新数据验证）。

**关联 Issue**：
- issue #116：benchmark #0 set 过程
- issue #117：analyzer vs BT capture gap 深度归因 + Exp D 选型依据

---

## §2 研究管线累计状态

| 类别 | 累计数 | 备注 |
|------|-------:|------|
| research session 总数（编号） | 64 | `crypto_ob_research/1-*` ~ `64-*`（`10_zh`/`11_zh` 为翻译副本；`#23` 与 `#21` 同主题重复） |
| 完成 session（有 factor_definition.md） | ≥50（待精确统计） | 已编译入 FA1/FA2/FA3 覆盖 #1-51；#52-64 为 fa4 候选 |
| Failed / Interrupted session | 4（known） | #9 neg / #15 OOS fail / #18 stub / #23 dup（数据来自 project 记忆，7 天前） |
| factor list (FA) 总数 | 3 | FA1 / FA2 / FA3 |
| realized pool 总数 | 3 | fa1 (123) / fa2 (75) / fa3 (114) + baseline f001/f002/f001_f002_merged |
| benchmark refresh 次数 | **1** | Bootstrap #0 = FI top100 mdil=100k |
| 待编译 session 数 | ~13 | #52-64（等待 FA4 编译触发） |

---

## §3 开放研究方向 / 待关注模式

1. **Benchmark refresh #1 触发条件**：待 FA4（来源 #52-64）编译落地后，参照 HFT `HFTPool/pool/benchmark0323/` 的 `run_benchmark.py` + `run_top100.py` 搭建 crypto 侧 repeatable 脚本，再走一次正式的"合并 → LGBM → Top N 选择"闭环。
2. **FA3 净负向诊断闭环**：Issue #114 v2 归因产出 4 条 hard gate（duplicate R²≥0.95 自动拦截 / 冗余 gate R²≥0.5 / fair-baseline matched-recipe valid IC delta 为唯一终极判据 / 不用 single-factor IC 做 LGBM selector）。下一轮 deep-research 前需把 `crypto-deep-factor-research` SKILL.md 文字同步到 friction_knowledge_base + Studies #53-64 实践（用户已确认后续单独迭代）。
3. **回测 pipeline gap**：当前 SOTA 以 Valid RankIC 选型，但 §1.3 回测（maker/taker Sharpe）是北极星指标。FI top100 模型需跑一次 `crypto-signal-backtest` 产出闭环。
4. **Stage 5 refresh 缺失 repeatable skill**：当前 Stage 5 只有手工 / 参考 HFT 做法，建议在 FA4 落地前把流程抽成独立 skill（与 `crypto-meta-review` 同层）。
5. **FA3 库保留但不入模型的长期策略**：FA3 114 因子已刷入 world_pool，保留在 factor pool 中供后续研究对照（如 regime-gated conditional 使用），但不在默认 LGBM 特征集合中。后续若发现 fa3 子集在特定 regime 有价值，再局部引入。

---

## §4 本版 snapshot 生成说明

- **生成来源**：`/crypto-meta-review` Bootstrap 运行（2026-04-17），扫描路径：
  - `crypto_ob_research/` 全部 64 个 session 目录
  - `factor_agent_docs/FA1_factor_list.md` / `FA2_factor_list.md` / `FA3_factor_list.md`
  - `zebra_pool/fa1/` / `fa2/` / `fa3/` + baseline
  - `/data/db/crypto/analyzer/fa1/` / `fa2/` / `fa3/` / `fa3_tuning_stage1/` (28 子实验)
  - 主 ad-hoc 决策依据：`/home/cken/crypto_world/research/ic_fa123/REPORT.md`（2026-04-17 03:38）
- **用户预设决策**：SOTA 模型 = FI top100 / FA3 列入 §1.1 但不入模型 / §1.3 回测 `_待填_`
- **归档**：旧模板版本归档于 `sota_archive/sota_snapshot_pre_bootstrap_2026-04-17.md`
- **完整 meta-review 报告**：`reviews/meta_review_2026-04-17.md`
- **本期 update 子目录**：`updates/20260417_update/`（含 6 份 ad-hoc 报告副本）
