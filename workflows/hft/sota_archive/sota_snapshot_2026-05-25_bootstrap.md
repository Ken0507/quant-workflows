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

- **本次 snapshot 日期**：2026-05-25（Bootstrap）
- **上次 snapshot 日期**：—（首次 Bootstrap，无上期）
- **最后一次 benchmark refresh 日期**：2025-03-23（**Refresh #0**，benchmark0323 锁定日）
- **研究 session 覆盖到**：`HFTPool/ob_research/111-*`（编号最大 #111；目录总数 112；#11 与 #76 重复，#70 缺号）
- **FA 覆盖到**：`HFTPool/factor_agent_docs/FA28_factor_list.md`
- **realize pool 覆盖到**：`HFTPool/pool/FA28/`

---

## §1 当前 SOTA 组成

### 1.1 因子集构成

> 本表分两层：**Factor Pool**（所有已落地的因子库）与 **SOTA 模型输入**（当前 SOTA 模型实际使用的特征子集）。
> SOTA 模型现为 **benchmark0323_top100**（Refresh #0，2025-03-23 锁定）。FA15、FA26、FA27、FA28 已完成工程落地并存于 factor pool，但**当前 SOTA 模型不包含它们**——FA15 在 benchmark0323 编译时被跳过（原因待补充），FA26/27/28 是 post-Refresh #0 累积，待下一次 benchmark refresh 评估是否纳入。

| 因子集 | 因子数 | 工程状态 | 数据覆盖（标准提交集） | 来源研究 | 进入 SOTA 模型？ | 备注 |
|--------|-------:|---------|---------|---------|------|------|
| baseline_150_new | 150 | ✅ Production | 20250102 ~ 20250730 | ob_research 早期 + FA6/7/8/9/10/11 折叠 | ✅ 部分（37 a*/ga*/lg2* + 多数 fa6-10 入 top100） | 历史 baseline，已折叠 FA6/7/8/9/10/11 |
| FA12 (cken/fa12_factor_v1) | ~59 | ✅ 已落地 | 20250102 ~ 20250730 | ob_research（编号待补充） | ⚠️ DATASETS_DEF 列出但 top100 中 0 个 fa12_ 信号 — 进 SOTA 但未入 top100 | 需用户复核 |
| FA15 | ? | ✅ 已落地，**未入 benchmark0323** | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（历史遗留：编译 benchmark0323 时被跳过） | 跳过原因待用户补充 |
| FA16 | 64 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（10 fa16_ 入 top100） | |
| FA20 | 22 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（3 fa20_ 入 top100；fa20_session_position 是 top100 gain #1） | |
| FA21 | 28 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（top100 中 0 个；信号名为 `ac*/buy_*/cancel_*/chase_*` 等，未带 fa21 前缀） | 命名混淆需归档说明 |
| FA22 | 16 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（1 fa22_ 入 top100） | |
| FA23 | 51 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（top100 中 0 个 ed2_/ga_/...） | |
| FA24 | 43 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（top100 含 bps36_/lc40_/ofi34_ 等） | |
| FA25 | 36 | ✅ Production | 20250102 ~ 20250730 | ob_research（编号待补充） | ✅ 部分（9 fa25_ 入 top100） | |
| FA26 | 82 | ✅ 已落地（post-Refresh #0） | 20250102 ~ 20250730 | ob_research 49-68 | ❌（未进 benchmark0323，待 Refresh #1） | merged analyzer 输出已被清理 |
| FA27 | 33 | ✅ 已落地（post-Refresh #0） | 20250102 ~ 20250730 | ob_research 69-88 | ❌（未进 benchmark0323，待 Refresh #1） | merged analyzer 输出已被清理 |
| FA28 | 56 | ✅ 已落地（post-Refresh #0） | 20250102 ~ 20250730 | ob_research（编号待补充） | ❌（merged 评估完成：LGBM gain 占比 6.33%，机制独立但单因子弱） | merged_benchmark0323_top100 v1 报告完整 |
| **Factor Pool 合计（已落地）** | **≥ 740** | — | — | — | — | baseline150 + FA12-28（已 realize 部分；FA12/FA15 实际列数待复核） |
| **SOTA 模型输入数** | **100** | benchmark0323_top100 = LGBM gain Top 100 of {baseline150 + FA12 + FA16 + FA20-25}（410 候选） | — | — | — | |

**已编译但未 realize 的 FA**（factor_list.md 存在，pool/FA{N}/ 不存在）：

- FA6, FA7, FA8, FA9, FA10, FA11 — 已**折叠进 baseline_150_new**，无独立 pool 目录（FA6/7/9/10 在 baseline150 中有具名因子；FA8/11 在 benchmark0323 全池中 0 个具名因子，可能完全没落地）
- FA17, FA18, FA19 — factor_list 编译但未走 realize 流程；FA19 在 benchmark0323 全池中出现 5 个 fa19_ 信号（折叠路径待用户复核），FA17/FA18 未见
- **跳号**：FA13、FA14 不存在（factor_list 未编译）

### 1.2 LGBM SOTA 指标（benchmark0323_top100）

- **Analyzer 报告路径**：`/home/cken/hft_projects/HFTPool/pool/benchmark0323/report_top100/report.md`
- **Top 100 元数据**：`HFTPool/pool/benchmark0323/report_top100/metadata.json`
- **完整 410 池报告**：`HFTPool/pool/benchmark0323/report/`
- **构建脚本**：`HFTPool/pool/benchmark0323/run_benchmark.py`（合并 410）+ `run_top100.py`（gain Top 100）
- **LGBM 模型路径**：⚠️ `/data/db/hft/model_output/cken/benchmark0323/v1_top100/` 目录已被清理；纯 SOTA model.txt 不可用。**最近可用代理**：`/data/db/hft/model_output/fa28/fa28_merged_benchmark0323_top100/v1/model.txt`（含 100 SOTA + 56 FA28 = 156 features）
- **Universe**：bond_sz, 190 codes
- **日期范围**：20250102 ~ 20250730 (n_days = 139, 标准提交集)
- **Train/Valid 切分**：时间顺序，train 111 天（20250102 ~ 20250620）/ valid 28 天（20250623 ~ 20250730）
- **样本数**：n_train = 81,763,385 / n_valid = 23,030,246
- **Sampling**：bar 模式，`bar_col=bar_aggtrans_time_1`
- **主 Label**：`ret_lag0_next100`（horizon = 100 bars，mid-to-mid，within_session）
- **辅助 Label**：18 个 horizon（next1, 2, 3, 4, 5, 7, 10, 13, 16, 20, 25, 30, 40, 50, 75, 100, 150, 200）
- **LGBM 超参**：learning_rate 0.1 / num_leaves 32 / min_data_in_leaf 10000 / num_boost_round 50 / n_jobs 120 / seed 20260323
- **Downsample**：1（无降采样）

**LGBM 层关键指标**：

| 指标 | Train | Valid |
|------|------:|------:|
| LGBM IC (mean) | **需用户从 `report_top100/img/lgbm_daily_ic.png` 核对，或重跑 benchmark0323_top100 model 提取** | **同左** |
| LGBM RankIC (mean) | **同上** | **同上** |
| Valid RankIC pos% | — | **同上** |
| Valid Top0.1% net (bps) | — | **见 `report_top100/img/lgbm_top0p1_net_return_*.png` / `signal_summary.parquet` 但仅单因子层** |
| Valid Top0.01% net (bps) | — | **同上** |

> ⚠️ **关于 LGBM 层指标缺失**：纯 `benchmark0323_top100` LGBM 模型文件（位于 `/data/db/hft/model_output/cken/benchmark0323/v1_top100/`）已被清理，PNG 图保留但 parquet 形式的 LGBM IC 不在 report_top100 下。可用三种方式补齐：
> 1. 从 `report_top100/img/lgbm_daily_ic.png` 视觉读出
> 2. 用 FA28-merged 版本（156 features）做近似代理：train mean RankIC ≈ 0.135 / valid mean RankIC ≈ 0.119（**这含 FA28，非纯 SOTA**）
> 3. 重跑 `pool/benchmark0323/run_top100.py` 一次（cache 还在）
>
> 待用户决定补齐路径。

**单因子层关键指标**（实测自 `report_top100/daily_ic.parquet`，100 个 top 因子）：

| 指标 | 全期（139 天） | Train (111 天) | Valid (28 天) |
|------|------:|------:|------:|
| Mean cross-signal Daily RankIC | — | 0.0101 | 0.0085 |
| Days with positive cross-signal mean RankIC | — | 111/111 (100%) | 28/28 (100%) |
| 100 因子 \|valid RankIC\| 均值 | — | — | 0.0224 |
| 100 因子 \|valid RankIC\| 中位数 | — | — | 0.0196 |
| 因子数 \|valid RankIC\| ≥ 0.03 | — | — | 32 |
| 因子数 \|valid RankIC\| ≥ 0.04 | — | — | 18 |
| 因子数 \|valid RankIC\| ≥ 0.05 | — | — | 7 |

**Top 10 单因子（按 \|valid RankIC\|）**：

| 排名 | 信号 | Train RankIC | Valid RankIC | 来源 |
|---:|---|---:|---:|---|
| 1 | a1r2_r2_slope_imb_norm_ema_diff | +0.0653 | +0.0686 | baseline150 (a1r2) |
| 2 | ga_gap_first_asym | +0.0613 | +0.0661 | baseline150 (ga) |
| 3 | a2r2_sig2_price_gap_imb_l2 | −0.0612 | −0.0661 | baseline150 (a2r2) |
| 4 | a3_a3_gap_imb_bps | +0.0609 | +0.0650 | baseline150 (a3) |
| 5 | ga_island_iso_asym | +0.0567 | +0.0584 | baseline150 (ga) |
| 6 | fa16_micro_trunc_50k_bps | +0.0539 | +0.0527 | FA16 |
| 7 | fa7_vwapmid_mid_diff_bps_50k | +0.0538 | +0.0525 | baseline150 (FA7 折叠) |
| 8 | a1b_impact_imb_bps | +0.0491 | +0.0486 | baseline150 (a1b) |
| 9 | pfi38_fast | +0.0500 | +0.0471 | baseline150 (pfi) |
| 10 | fa7_micro_queue_gap_bps_3 | +0.0503 | +0.0461 | baseline150 (FA7 折叠) |

**Top 10 features（LGBM gain ratio）**：

> 来源：`pool/benchmark0323/report_top100/report.md` §7.1 训练信息 features 顺序（首 10 项按 metadata 中 `signals` 列表顺序，与 LGBM gain ranking **不一定一致**）。LGBM gain ratio 数值需从 `feature_importance_gain.parquet` 或 `img/lgbm_feature_importance_gain.png` 提取——纯 SOTA 模型文件已清理，建议参考 FA28-merged 的 importance 表（顺序略有偏移，因为多了 56 features）：

| 排名 | 特征（FA28-merged 模型中 bm0323__ 前缀，前 10 位） |
|---:|---|
| 1 | fa20_session_position |
| 2 | a1r2_r2_slope_imb_norm_ema_diff |
| 3 | bps36_cancel_churn_gradient |
| 4 | pfi38_fast |
| 5 | a3_a3_add_flow_imb_ema_fast |
| 6-10 | （需从 PNG 或重跑提取） |

> ⚠️ **诚实标注**：上表 #1-#5 来自 `pool/FA28/report/analyzer2_merged_summary.md` 中"Top 30 features by gain — 全部 bm0323"段；纯 SOTA 模型下顺序可能相同但 gain ratio 数值会略有不同（去掉 56 FA28 features 后归一化变化）。

### 1.3 SOTA 回测结果

> **范围说明**：依据 §1 §1.2 §3 的范围声明，本 snapshot **不维护回测层指标**。Layer 2（SignalReplay 回测）由 `/hft-playground-signalreplay-backtest` 独立产出，每次运行产物保留在 playground batch-backtest 工作区；Layer 3（实盘）由 `daily_trading_report` + 交易机 Session CSV 维护。
>
> 如未来希望把回测 SOTA 也纳入本 snapshot，需先扩展 target_and_workflow.md §1.1 的 SOTA 范围声明。

**当前 SOTA 模型对应的回测产出索引**：

- 工作区参考：`HFTPool/backtest/`（待 meta-review 扫描后补全具体路径）
- 实盘策略入口：`HFTPool/pool/benchmark0323/live_v0/` → 部署到交易机 `/home/userlgj/app/strategy/cken_benchmark0323_v0/`

---

## §2 研究管线累计状态

| 类别 | 累计数 | 备注 |
|------|-------:|------|
| research session 总数（目录） | **112** | `HFTPool/ob_research/1-*` ~ `111-*`；#11 与 #76 各有两个不同 topic 的目录，#70 缺号 |
| research session 编号最大值 | **#111** | 末尾 session（topic 待用户补充） |
| 完成 session（有 factor_definition.md） | **107** | 105 个同时有 quality_review.md |
| 未完成 / 中断 session（仅 research_report，无 factor_definition） | **4** | 编号待用户补充 |
| factor list (FA) 已编译 | **21** | FA6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28（跳过 13/14） |
| factor list 已 realize（pool/FA{N}/） | **12** | FA12, 15, 16, 20, 21, 22, 23, 24, 25, 26, 27, 28 |
| factor list 已编译但未 realize | **9** | FA6, 7, 8, 9, 10, 11（已折叠进 baseline_150_new）+ FA17, 18, 19（未折叠路径待复核） |
| **benchmark refresh 次数** | **1** | Refresh #0 = benchmark0323_top100（2025-03-23 锁定） |
| 待评估纳入 SOTA 的 post-Refresh #0 FA | **3-4** | FA26 / FA27 / FA28（已 merged 评估完）；FA15 是否补充重评待用户决定 |

---

## §3 开放研究方向 / 待关注模式

1. **触发 Refresh #1 是当前 SOTA 决策最大节点**：FA26 / FA27 / FA28 三组共 ~171 个因子已 post-Refresh #0 累积，FA28 的 merged 评估显示 LGBM gain 占比 6.33%（机制独立但单因子弱）。**Refresh #1 建议范围**：`baseline_150_new + FA12 + FA15? + FA16 + FA20-28`，重选 LGBM gain Top 100（或 Top 150，待用户决定）。Refresh #1 落地后，新 SOTA 模型应在 valid 28 天上的 LGBM RankIC 超越当前 benchmark0323_top100 才算"真 refresh"。

2. **FA15 历史遗留待澄清**：FA15 已完整 realize（pool/FA15/ 有完整 report，含 `fa15_quality_review.md` 和 `fa15_addendum_quant_evidence_codex_20260221.md` 等多份分析），但在 benchmark0323 的 DATASETS_DEF 中被跳过。原因不在 git history 中明确，需用户在下次 meta-review 时补充说明（可能是 quality 未达标 / 命名冲突 / 数据问题）。

3. **下一轮 deep-research 的对标基线**：当前 SOTA 单因子 \|valid RankIC\| 上限 ~0.069（a1r2_r2_slope_imb_norm_ema_diff）、Top 6 因子均 ≥ 0.05、Top 18 因子均 ≥ 0.04。新因子若要进 Top 50，需做到 \|valid RankIC\| ≥ 0.03。但非线性独立贡献（LGBM gain 占比）同样合法——FA28 单因子最强 0.028 仍能贡献 6.33% gain。

4. **FA12 / FA21 / FA23 命名前缀混乱**：FA12 在 SOTA 模型 top100 中无 fa12_ 前缀信号（虽然 DATASETS_DEF 列出），FA21 信号名为 `ac*/buy_*/cancel_*/chase_*`（无 fa21_ 前缀），FA23 信号名为 `ed2_/ga_/...`。这会让"哪个 FA 贡献了哪些因子"的归因变模糊，建议在 Refresh #1 之前先做一次因子前缀清理（重命名 / 加 metadata）。

5. **会话编号冲突清理**：`ob_research/` 下 #11 有两个目录（`11-event_dominance`, `11-psychological_levels`）、#76 有两个（`76-frequency_domain_heartbeat`, `76-lob_queue_survival`），#70 缺号。建议用户决定如何处理（重新编号 / 标记其中一个为废弃）。

6. **Layer 2/3 演进追踪缺位**：本 snapshot 不维护回测和实盘 SOTA。若希望对齐 crypto 那边在 sota_snapshot §1.3 维护的回测指标，需扩展本文件范围（详见 target_and_workflow.md §1.1 第三层说明）。

7. **纯 benchmark0323_top100 LGBM 模型文件已清理**：`/data/db/hft/model_output/cken/benchmark0323/v1_top100/` 不再存在，纯 SOTA LGBM 指标只能从 PNG 视觉读或重跑 `run_top100.py` 提取。如未来要做"逐次对比新 benchmark vs 旧 benchmark"的精确数字对照，**建议 Refresh #1 之前先重跑一次 benchmark0323_top100 把 LGBM 指标的 parquet 保留下来**。

---

## §4 本版 snapshot 生成说明

- **生成来源**：首次 Bootstrap（手工初始化），由用户在 2026-05-25 与 agent 协作建立
- **本期 update 子目录**：—（Bootstrap 不创建期内 ad-hoc 报告目录；首次 `/hft-meta-review` 运行时建立 `updates/{yyyymmdd}_update/`）
- **归档**：—（无上版可归档）
- **完整 meta-review 报告**：—（待首次 `/hft-meta-review` 运行后落 `reviews/meta_review_{date}.md`）
- **核心引用文件**：
  - `HFTPool/pool/benchmark0323/run_benchmark.py` — DATASETS_DEF 权威来源
  - `HFTPool/pool/benchmark0323/report_top100/metadata.json` — Top 100 元数据
  - `HFTPool/pool/benchmark0323/report_top100/report.md` — 训练/验证日期、样本数
  - `HFTPool/pool/benchmark0323/report_top100/daily_ic.parquet` — 单因子 IC 实测来源
  - `HFTPool/pool/FA28/report/analyzer2_merged_summary.md` — FA28 merged 评估
  - `/data/db/hft/factor_pool/debug/fa{16,20-28}/fa*_factor_v1/20250102/...parquet` — 各 FA 列数实测来源
