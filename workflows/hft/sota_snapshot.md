# HFT 投研 SOTA Snapshot

> **用途**：记录"截至本日"的 SOTA 状态——当前 LGBM 预测信号最佳组合是哪几个因子集、多少个因子、关键指标如何。作为后续研究的比较基线。
>
> **范围**：严格只追踪 **Layer 1（LGBM 信号质量）**。Layer 2（SignalReplay 回测）和 Layer 3（实盘）的 SOTA 演进各自独立追踪，不在本文件维护。
>
> **语义**：本文件只反映 **current**（最新 benchmark refresh 后的真相），不维护历史最佳。历史进程请查 `sota_archive/` 归档 + `research_updates.md` changelog。
>
> **维护方式**：由 `/hft-meta-review` skill 在用户确认后覆盖。**agent 不得擅自修改**。每次覆盖前先归档旧版到 `sota_archive/sota_snapshot_{old_date}.md`。

---

## Snapshot 元数据

- **本次 snapshot 日期**：2026-05-25（Bootstrap，含 LGBM 重跑修复）
- **上次 snapshot 日期**：—（首次 Bootstrap，无上期）
- **最后一次 benchmark refresh 日期**：2025-03-23（**Refresh #0**，benchmark0323 锁定日）
- **本期重跑事件**：2026-05-25 重跑 `benchmark0323_top100` LGBM，恢复历史清理丢失的 model.txt + IC parquet + feature_importance_gain.parquet。模型物理副本存于 `HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/`
- **研究 session 覆盖到**：`HFTPool/ob_research/111-*`（编号最大 #111；目录总数 112；#11 与 #76 重复，#70 缺号）
- **FA 覆盖到**：`HFTPool/factor_agent_docs/FA28_factor_list.md`
- **realize pool 覆盖到**：`HFTPool/pool/FA28/`

---

## §1 当前 SOTA 组成

### 1.1 因子集构成

> 本表分两层：**Factor Pool**（所有已落地的因子库）与 **SOTA 模型输入**（当前 SOTA 模型实际使用的特征子集）。
> SOTA 模型现为 **benchmark0323_top100**（Refresh #0，2025-03-23 锁定）。FA15、FA26、FA27、FA28 已完成工程落地并存于 factor pool，但**当前 SOTA 模型不包含它们**——FA15 在 benchmark0323 编译时被跳过（merged LGBM gain 仅 1.75%，evaluator horizon 不匹配），FA26/27/28 是 post-Refresh #0 累积，待下一次 benchmark refresh 评估是否纳入。

| 因子集 | 因子数 | 工程状态 | 数据覆盖（标准提交集） | 来源研究 | 进入 SOTA 模型？ | 备注 |
|--------|-------:|---------|---------|---------|------|------|
| baseline_150_new | 150 | ✅ Production | 20250102 ~ 20250730 | ob_research 早期 + FA6/7/8/9/10/11 折叠 | ✅ 部分（37 a*/ga*/lg2* + 多数 fa6-10 入 top100） | 历史 baseline，已折叠 FA6/7/8/9/10/11 |
| FA12 (cken/fa12_factor_v1) | ~59 | ✅ 已落地，但 factor_pool 已清理 | 20250102 ~ 20250730 | ob_research（编号待补充） | ⚠️ DATASETS_DEF 列出但 top100 中 0 个 fa12_ 信号 | rerun 2026-05-25 时 fa12 parquet 已不在 /data/db/hft/factor_pool/debug/cken/；rerun 跳过 fa12，但 cache 仍包含其历史列。**需复核 fa12 命名前缀** |
| FA15 | 35 | ✅ 已落地，**未入 benchmark0323** | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌ | quality_review CONDITIONAL：merged LGBM gain 1.75%；evaluator h20 与因子主优势 horizon h100+ 不匹配 |
| FA16 | 64 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（10 fa16_ 入 top100） | |
| FA20 | 22 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（3 fa20_ 入 top100；**fa20_session_position 是 top100 gain #1，13.66%**） | |
| FA21 | 28 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（top100 中 0 个；信号名为 `ac*/buy_*/cancel_*/chase_*` 等，无 fa21_ 前缀） | 命名混淆需归档说明 |
| FA22 | 16 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（1 fa22_ 入 top100） | |
| FA23 | 51 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（top100 中 0 个 ed2_/ga_/...） | |
| FA24 | 43 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（top100 含 bps36_/lc40_/ofi34_ 等） | |
| FA25 | 36 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（9 fa25_ 入 top100） | |
| FA26 | 82 | ✅ 已落地（post-Refresh #0） | 20250102 ~ 20250730 | ob_research 49-68 | ❌（未进 benchmark0323，待 Refresh #1） | merged analyzer 软链已断（2026-04-23 事故） |
| FA27 | 33 | ✅ 已落地（post-Refresh #0） | 20250102 ~ 20250730 | ob_research 69-88 | ❌（未进 benchmark0323，待 Refresh #1） | merged analyzer 软链已断（同上） |
| FA28 | 56 | ✅ 已落地（post-Refresh #0） | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（merged 评估完成：LGBM gain 占比 6.33%，机制独立但单因子弱） | merged_benchmark0323_top100 v1 报告完整（FA28 是第一个走"物理复制"新规的 FA） |
| **Factor Pool 合计（已落地）** | **~635** | — | — | — | — | baseline150 + FA15 + FA16 + FA20-28 = 150+35+64+22+28+16+51+43+36+82+33+56 = 616（FA12 已不在 disk，但 cache 含其列） |
| **SOTA 模型输入数** | **100** | benchmark0323_top100 = LGBM gain Top 100 of {baseline150 + FA12 + FA16 + FA20-25}（410 候选） | — | — | — | |

**已编译但未 realize 的 FA**（factor_list.md 存在，pool/FA{N}/ 不存在）：

- FA6, FA7, FA8, FA9, FA10, FA11 — 已**折叠进 baseline_150_new**，无独立 pool 目录（FA6/7/9/10 在 baseline150 中有具名因子；FA8/11 在 benchmark0323 全池中 0 个具名因子，可能完全没落地）
- FA17, FA18, FA19 — factor_list 编译但未走 realize 流程；FA19 在 benchmark0323 全池中出现 5 个 fa19_ 信号（折叠路径待用户复核），FA17/FA18 未见
- **跳号**：FA13、FA14 不存在（factor_list 未编译）

### 1.2 LGBM SOTA 指标（benchmark0323_top100，2026-05-25 重跑实测）

**模型与报告路径**：

- **报告（持久副本）**：`HFTPool/pool/benchmark0323/report_top100/report.md`（与原 2025-03-23 版本一致）
- **重跑报告（含 IC parquet）**：`HFTPool/pool/benchmark0323/report_top100_rerun_20260525/report.md`
- **LGBM 模型（物理副本）**：`HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/model.txt`
- **LGBM IC parquet（物理副本）**：`HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/lgbm_daily_ic_{train,valid,}.parquet`
- **Feature importance（物理副本）**：`HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/feature_importance_gain.parquet`
- **工作目录原始路径（可能被清理）**：`/data/db/hft/model_output/cken/benchmark0323/v1_top100_rerun_20260525/`

**Universe / 日期 / 切分**：

- Universe: bond_sz, 190 codes
- 日期范围：20250102 ~ 20250730 (n_days = 139, 标准提交集)
- Train/Valid 切分：时间顺序，train **111 天**（20250102 ~ 20250620）/ valid **28 天**（20250623 ~ 20250730）
- 样本数：n_train = 81,763,385 / n_valid = 23,030,246
- Sampling: bar 模式，`bar_col=bar_aggtrans_time_1`
- 主 Label: `ret_lag0_next100`（horizon=100 bars, mid, within_session）
- 辅助 Label: 18 个 horizon（next1, 2, 3, 4, 5, 7, 10, 13, 16, 20, 25, 30, 40, 50, 75, 100, 150, 200）
- LGBM cfg: learning_rate 0.1 / num_leaves 32 / min_data_in_leaf 10000 / num_boost_round 50 / n_jobs 120 / **seed 20260323**
- Downsample: 1（无降采样）

**Layer 1 关键指标（实测自 rerun 的 `lgbm_daily_ic_{train,valid}.parquet`）**：

| 指标 | Train (111 天) | Valid (28 天) | All (139 天) |
|------|------:|------:|------:|
| LGBM daily IC (mean) | 0.1437 | **0.1327** | 0.1415 |
| LGBM daily IC (std) | 0.0214 | 0.0204 | 0.0216 |
| LGBM daily RankIC (mean) | 0.1225 | **0.1123** | 0.1204 |
| LGBM daily RankIC (std) | 0.0159 | 0.0116 | 0.0157 |
| RankIC IR (mean/std, no annualize) | 7.70 | **9.68** | 7.69 |
| Train/Valid Gap (RankIC) | — | **0.0102** | — |
| Days with positive daily RankIC | 111/111 (100%) | **28/28 (100%)** | 139/139 (100%) |
| Days with positive daily IC | 111/111 (100%) | 28/28 (100%) | 139/139 (100%) |

> **稳定性极高**：valid 期 28 天每一天 LGBM RankIC > 0，std 仅 0.0116（远小于 mean 0.1123），RankIC IR ≈ 9.68（不年化），表明信号在 valid 期日度极其稳定。

**Top0.1% mean return @ horizon=100（实测 `lgbm_*_price_path.png` + `lgbm_*_net_grouped_return.png`）**：

| 指标 | Train | Valid |
|------|------:|------:|
| Top0.1% mean return (gross, bps) | ~26.7 | **~25.8** |
| Top0.01% net group return (return − spread, bps) | ~25.5 | **~30.7** |
| Top0.03% net group return (bps) | ~18.3 | **~22.9** |
| Top0.10% net group return (bps) | ~11.6 | **~10.0** |

**Top 10 LGBM features（gain ratio，实测自 `feature_importance_gain.parquet`）**：

| 排名 | 特征 | gain | gain_ratio |
|---:|---|---:|---:|
| 1 | fa20_session_position | 4.750 | **13.66%** |
| 2 | a1r2_r2_slope_imb_norm_ema_diff | 3.475 | 10.00% |
| 3 | pfi38_fast | 1.725 | 4.96% |
| 4 | a3_a3_add_flow_imb_ema_fast | 1.399 | 4.02% |
| 5 | bps36_cancel_churn_gradient | 1.193 | 3.43% |
| 6 | pfi38_slow | 1.174 | 3.38% |
| 7 | a2b_sig_mom_fast_bps | 1.071 | 3.08% |
| 8 | a1b_rvol_fast_bps | 0.832 | 2.39% |
| 9 | a3_a3_mid_ret_ema_fast | 0.778 | 2.24% |
| 10 | fa7_micro_queue_gap_bps_3 | 0.764 | 2.20% |

**Top 10 单因子（按 \|valid RankIC\|，实测自原 `daily_ic.parquet`）**：

| 排名 | 信号 | Train RankIC | Valid RankIC | 来源 |
|---:|---|---:|---:|---|
| 1 | a1r2_r2_slope_imb_norm_ema_diff | +0.0653 | +0.0686 | baseline150 |
| 2 | ga_gap_first_asym | +0.0613 | +0.0661 | baseline150 |
| 3 | a2r2_sig2_price_gap_imb_l2 | −0.0612 | −0.0661 | baseline150 |
| 4 | a3_a3_gap_imb_bps | +0.0609 | +0.0650 | baseline150 |
| 5 | ga_island_iso_asym | +0.0567 | +0.0584 | baseline150 |
| 6 | fa16_micro_trunc_50k_bps | +0.0539 | +0.0527 | FA16 |
| 7 | fa7_vwapmid_mid_diff_bps_50k | +0.0538 | +0.0525 | baseline150 (FA7 fold) |
| 8 | a1b_impact_imb_bps | +0.0491 | +0.0486 | baseline150 |
| 9 | pfi38_fast | +0.0500 | +0.0471 | baseline150 |
| 10 | fa7_micro_queue_gap_bps_3 | +0.0503 | +0.0461 | baseline150 (FA7 fold) |

**100 因子单因子统计**：

| 指标 | 全期（139 天） | Train (111 天) | Valid (28 天) |
|------|------:|------:|------:|
| Mean cross-signal Daily RankIC | — | 0.0101 | 0.0085 |
| Days with positive cross-signal mean RankIC | — | 111/111 (100%) | 28/28 (100%) |
| 100 因子 \|valid RankIC\| 均值 | — | — | 0.0224 |
| 100 因子 \|valid RankIC\| 中位数 | — | — | 0.0196 |
| 因子数 \|valid RankIC\| ≥ 0.03 | — | — | 32 |
| 因子数 \|valid RankIC\| ≥ 0.04 | — | — | 18 |
| 因子数 \|valid RankIC\| ≥ 0.05 | — | — | 7 |

### 1.3 SOTA 回测结果

> **范围说明**：依据 §1 §1.2 §3 的范围声明，本 snapshot **不维护回测层指标**。Layer 2 回测的合法口径（2026-07-12 #179 定稿）：**绝对 PnL 用 live_v2 trader 信号注入**（`--inject_signal_pack_dir`，执行语义经 #171 实盘对账验证）；`/hft-playground-signalreplay-backtest` 仅限信号相对比较（其 v20260712.1 前历史结果因堆仓 bug 全部作废）。Layer 3（实盘）由 `daily_trading_report` + 交易机 Session CSV 维护。
>
> ⚠️ **Layer 2 已知事实（2026-07-12）**：当前 SOTA（benchmark0323_top100）在真实执行语义下 2026Q2 开盘/全天均为负（−742/日 开盘，0/56 正日，hft-sdk-issues #179）——Layer 1 rankIC 真实但不足以过执行成本线。此前"开盘 5 分钟唯一真钱"等结论作废。
>
> 如未来希望把回测 SOTA 也纳入本 snapshot，需先扩展 target_and_workflow.md §1.1 的 SOTA 范围声明。

**当前 SOTA 模型对应的回测产出索引**：

- 工作区参考：`HFTPool/backtest/`（待 meta-review 扫描后补全具体路径；目前未发现独立 backtest 工作区）
- 实盘策略入口：`HFTPool/pool/benchmark0323/live_v0/` → 部署到交易机 `/home/userlgj/app/strategy/cken_benchmark0323_v0/`

---

## §2 研究管线累计状态

| 类别 | 累计数 | 备注 |
|------|-------:|------|
| research session 总数（目录） | **112** | `HFTPool/ob_research/1-*` ~ `111-*`；#11 与 #76 各有两个不同 topic 的目录，#70 缺号 |
| research session 编号最大值 | **#111** | 末尾 session（topic 待用户补充） |
| 完成 session（有 factor_definition.md） | **107** | 105 个同时有 quality_review.md |
| 未完成 / 中断 session（仅 research_report，无 factor_definition） | **4** | #2 fa17_part1, #14 unreasonable_orders, #47 order_lifecycle_deep, #107 bilateral_depth_signature |
| factor list (FA) 已编译 | **21** | FA6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28（跳过 13/14） |
| factor list 已 realize（pool/FA{N}/） | **12** | FA12, 15, 16, 20, 21, 22, 23, 24, 25, 26, 27, 28 |
| factor list 已编译但未 realize | **9** | FA6, 7, 8, 9, 10, 11（已折叠进 baseline_150_new）+ FA17, 18, 19（未折叠路径待复核） |
| **benchmark refresh 次数** | **1** | Refresh #0 = benchmark0323_top100（2025-03-23 锁定，2026-05-25 重跑 LGBM 恢复模型文件） |
| 待评估纳入 SOTA 的 post-Refresh #0 FA | **3-4** | FA26 / FA27 / FA28（已 merged 评估完）；FA15 是否补充重评待用户决定 |

---

## §3 开放研究方向 / 待关注模式

1. **触发 Refresh #1 是当前 SOTA 决策最大节点**（**立即触发**）：FA26 / FA27 / FA28 三组共 ~171 个因子已 post-Refresh #0 累积，FA28 的 merged 评估显示 LGBM gain 占比 6.33%（机制独立但单因子弱）。**Refresh #1 建议范围**：`baseline_150_new + FA12 + FA15? + FA16 + FA20-28`，重选 LGBM gain Top 100（或 Top 150）。Refresh #1 落地后，新 SOTA 模型应在 valid 28 天上的 LGBM RankIC 超越当前 0.1123 才算"真 refresh"。**由 `/hft-benchmark-refresh` skill 启动；新 skill 已强制物理拷贝 saved_model 防止再次丢失**

2. **FA15 历史遗留**（已澄清）：FA15 已 realize（35 因子）但被 benchmark0323 跳过。归因：quality_review CONDITIONAL（merged gain 1.75%，evaluator h20 不匹配 — 因子主优势 horizon 在 h100+）。其 B 组（价格整数偏好）和 G 组（联合整数）在 next200 RankIC 0.022-0.033。**建议 Refresh #1 中尝试纳入 FA15 评估**（horizon 已切到 next100 主口径，可能仍边际，但值得验证；该结论由本期 Bootstrap meta-review 闭环）

3. **下一轮 deep-research 的对标基线**：当前 SOTA 单因子 \|valid RankIC\| 上限 ~0.069（a1r2_r2_slope_imb_norm_ema_diff）、Top 6 因子均 ≥ 0.05、Top 18 因子均 ≥ 0.04。新因子若要进 Top 50，需做到 \|valid RankIC\| ≥ 0.03。但非线性独立贡献（LGBM gain 占比）同样合法——FA28 单因子最强 0.028 仍能贡献 6.33% gain。**LGBM 层目标**：valid daily RankIC mean 0.1123、Top0.1% net (h100) 25.8 bps，新 SOTA 须超越

4. **FA12 / FA21 / FA23 命名前缀混乱**：FA12 在 SOTA 模型 top100 中无 fa12_ 前缀信号（虽然 DATASETS_DEF 列出），FA21 信号名为 `ac*/buy_*/cancel_*/chase_*`（无 fa21_ 前缀），FA23 信号名为 `ed2_/ga_/...`。这会让"哪个 FA 贡献了哪些因子"的归因变模糊。**2026-05-25 重跑时发现 FA12 factor_pool/debug/cken/fa12_factor_v1 已不在 disk**（仅在 cache 中以列形式残留）。建议在 Refresh #1 之前做一次"前缀清理"实验（重命名 / 加 metadata）

5. **数据持久化策略已固化**（本期 Bootstrap 闭环）：`/data/db/hft/analyzer2/` 和 `/data/db/hft/model_output/` 都是临时缓存，可能被清理。已更新 `hft-analyzer2-standard-report` 和 `hft-benchmark-refresh` skill SKILL.md，**强制**所有报告 + LGBM 模型 + IC parquet + feature_importance 都用 `cp -L` 物理拷贝到 HFTPool。**禁止** symlink。豁免：cache/ 和 memmap/ 可留在 /data/。**Refresh #1 必须遵守此规则**

6. **Session 编号清理**（低优先）：#11 / #76 都是"两个同号但内容不同的 session"（4 个目录都完成了 factor_definition.md），#70 缺号。**建议保持现状**，因为重新编号会破坏 git history 和已有 FA factor_list 中的"来源研究"引用

7. **中断 session**（4 个）：#2 fa17_part1, #14 unreasonable_orders, #47 order_lifecycle_deep, #107 bilateral_depth_signature——#107 是较新的，可能仍在 Phase 1。**建议低优先**，由用户决定继续 / 关停

8. **FA17 / FA18 / FA19 未独立 realize**：factor_list 已编译但 pool/FA17 等不存在。FA19 在 benchmark0323 全池中有 5 个 fa19_ 信号（折叠路径待复核），FA17/FA18 未见。**建议在下次 meta-review 时追问**：是否走完整 realize 流程，或正式标记为废弃

---

## §4 本版 snapshot 生成说明

- **生成来源**：首次 Bootstrap（手工初始化 + 本期 `/hft-meta-review` Bootstrap 运行），由用户在 2026-05-25 与 agent 协作建立
- **本期 update 子目录**：`updates/20260525_update/`（含 55 份 ad-hoc 课题报告物理副本）
- **归档**：本期是首次 Bootstrap，归档了 sota_snapshot 的初始化版本到 `sota_archive/sota_snapshot_2026-05-25_bootstrap.md`
- **完整 meta-review 报告**：`reviews/meta_review_2026-05-25.md`
- **核心引用文件**：
  - `HFTPool/pool/benchmark0323/run_benchmark.py` — DATASETS_DEF 权威来源
  - `HFTPool/pool/benchmark0323/report_top100/metadata.json` — Top 100 元数据
  - `HFTPool/pool/benchmark0323/report_top100/report.md` — 训练/验证日期、样本数
  - `HFTPool/pool/benchmark0323/report_top100/daily_ic.parquet` — 单因子 IC 实测来源
  - `HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/lgbm_daily_ic_{train,valid}.parquet` — **本期重跑产出，LGBM IC 实测来源**（之前丢失，现已物理保存）
  - `HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/feature_importance_gain.parquet` — **本期重跑产出，gain ratio 实测来源**
  - `HFTPool/pool/FA28/report/analyzer2_merged_summary.md` — FA28 merged 评估
  - `HFTPool/pool/FA15/report/fa15_quality_review.md` + `fa15_addendum_quant_evidence_codex_20260221.md` — FA15 未入 SOTA 归因
  - `/data/db/hft/factor_pool/debug/fa{16,20-28}/fa*_factor_v1/20250102/...parquet` — 各 FA 列数实测来源（FA12 已不在 disk）
