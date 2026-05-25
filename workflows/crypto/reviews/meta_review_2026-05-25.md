# Meta Review 2026-05-25

## 覆盖区间

- **since**: 2026-04-17（Update #1 Bootstrap）
- 上次 update 编号: #1
- 本次编号候选: **#2**
- 实际研究停滞期：2026-04-23 之后 crypto 侧基本停滞（用户工作重心切到 HFT/lgj SDK audit）
- 本期主要为 2026-04-17 → 2026-04-23 之间约一周的高密度补 SOTA + label 大迁移 + benchmark refresh 工作

## 扫描结果摘要

- 新增 session: **1**（#65 queue_survival_panel，停在 Phase 1，无 factor_definition.md）
- 新增 FA: **1**（FA4，来源 #42 + #52-64 共 14 项研究，55 因子，CONDITIONAL PASS）
- 新增 realize: **1**（fa4，工程已交付 54 因子 + analyzer 报告齐全）
- 新增 analyzer run: **大批** —
  - `fa4/` 7 个子实验（含 close-label 4 个 + mid-label 3 个）
  - `campaign122_mid/` 5 pairs (mid-label 复检) × h100
  - `campaign122_mid_h400/` 5 pairs × h400
  - `campaign123_clean_sota/` 12 实验 E1-E12 + ckpt4_clean
- 检测到 benchmark refresh: **是（Refresh #1）** —
  - 新 SOTA: **`campaign123_clean_sota/E2_mid_sota100/`**（100 维 fa1+fa2 mid-label FI top100）
  - 取代了 Bootstrap #0 的 `fa3_tuning_stage1/fi_top100_mdil100k/`
- 候选 ad-hoc 报告: **9 份**（见下）
- 相关 GitHub issues 候选: 9 个（#114/#115/#116 上轮已收录但本期有更新；#117-#125 新开）
- 新增 signal backtest 报告: **15+ 份**（close-label 6 + mid-label 3 + E2 3 + ckpt4_clean 2 + …）

---

## 候选 research_updates 新条目（严格对齐模板）

### [2026-05-25] Update #2

**时间区间**：2026-04-17 → 2026-05-25
**子目录**：[`updates/20260525_update/`](updates/20260525_update/)

> ⚠️ 本期为"高强度 + 长停滞"两段式：04-17 到 04-23 完成了 label 大迁移 + benchmark refresh #1 + FA4 落地；04-23 之后约 5 周用户工作切到 HFT/lgj SDK audit，crypto 侧无新增产出。本 Update 主要追认 04-17→04-23 一周的工作。

#### 1. 本期产出概览（聚合计数）

| 类别 | 新增 | 明细 |
|------|------|------|
| research session | 1 | #65 queue_survival_panel（2026-04-18 启动，Phase 1 完成，未到 Phase 2，无 factor_definition.md） |
| factor list (FA) | 1 | FA4（来源 #42 + #52-64 共 14 项研究，55 因子，7 分组，CONDITIONAL PASS） |
| realized pool | 1 | fa4（54 因子工程交付；FA list 55 vs realize 54 的 1 个差异来自实施合并/剔除） |
| analyzer run | 多批 | (a) `fa4/` 4 close-label + 3 mid-label；(b) `campaign122_mid/` 5 pairs h100；(c) `campaign122_mid_h400/` 5 pairs h400；(d) `campaign123_clean_sota/` 12 实验 + ckpt4_clean |
| benchmark refresh | **是（#1）** | **新 SOTA: `campaign123_clean_sota/E2_mid_sota100/`**（100 维 fa1+fa2 mid-label FI top100，57 fa1 + 43 fa2） |
| ad-hoc 课题报告 | 9 份 | 见 §3 |
| 相关 issue | 9 个 | #114-#125 范围（见 §4） |

#### 2. SOTA 提升量

**SOTA 模型对比表**（Bootstrap #0 close-label → Refresh #1 mid-label）：

| 指标 | 上期 (Bootstrap #0) | 本期 (Refresh #1 = E2 mid_sota100) | 变化 |
|------|--------:|--------:|--------|
| Label 口径 | close-to-close | **mid-to-mid (basic_table anchor)** | 切换（issue #119/#121） |
| 模型路径 | `fa3_tuning_stage1/fi_top100_mdil100k/` | `campaign123_clean_sota/E2_mid_sota100/clip/` | — |
| 因子集 | fa1 59 + fa2 41 | **fa1 57 + fa2 43**（同 100 维，2 个互换） | 接近 |
| Train RankIC | 0.0635 | 0.0705 | +0.0070 |
| **Valid RankIC** | 0.0427 | **0.0579** | **+0.0152 (+36%)** |
| Gap RankIC | 0.0208 | 0.0126 | −0.0082（缩小 39%） |
| RICIR (Valid) | _未补_ | 2.68 | — |
| **Valid Top0.1% net (bps)** | 不可直接对比（close-bias） | **8.82** | 全 campaign #123 最高 |
| Valid RankIC pos% | _未补_ | 100% | — |
| 已落地因子总数 (factor pool) | 381 | **436**（+ fa4 55；以 list 计） | +14% |
| BT Total Net (Exp D 同 recipe) | +1,650 USDT | **+1,830 USDT** | +11% |
| BT Train Sharpe | 6.63 | **7.93** | +20% |
| BT Valid Sharpe | −1.29 | **+0.16** | 由负翻正 |

**关键洞察**（Refresh #1 的两个本质改变）：

1. **mid-label 修复了 close-bias 导致的 Valid alpha 衰减**：Phase 7 归因证明 Valid 期 close-basis "+7.61 bps Top0.1% alpha" 几乎 100% 是 close→mid reference bias。切到 mid-label 后 Valid Sharpe 从 −1.29 翻正到 +0.16，证实"先前 valid 期 alpha 衰减"主要不是结构问题。
2. **fa4 落地但不进入 SOTA 模型**：campaign #123 E4 (fa124_full) Valid Top0.1% **6.99 < E2 8.82**；E8/E9 (fa4 IC-selected) 微弱正但 price path 不稳；ckpt4_clean (E2+54 fa4) Valid Top0.1% 跌到 7.66。**fa4 与 fa3 同列入 factor pool 但不入默认 SOTA 模型**。

**SOTA 模型锚点**：
- 模型目录：`/data/db/crypto/analyzer/campaign123_clean_sota/E2_mid_sota100/clip/`
- 模型文件：`lgbm_model.txt`
- Whitelist：`/home/cken/crypto_world/research/ic_fa1234_mid/wl_mid_fi_top100.txt`
- Top 特征 (gain ratio)：`fa2_confirmed_flow_h20` (8.1%) / `fa1_stale_log_ratio` (6.8%) / `fa2_ofi_regime_z` (6.1%) / `fa1_stale_ema_logmax_50` (5.8%) / `fa2_impact_delta_10_100` (4.3%) / `fa2_big_interarrival` (4.3%) / `fa2_big_share_ema60` (3.0%) / `fa1_stale_ask_log` (2.6%) / `fa1_imb_x_herf` (2.6%) / `fa1_ewm_add_imbalance_60s` (2.6%)

**SOTA 决策依据**：
- campaign #123 用 12 个对照（E1-E12）+ E2 vs E10 (74 feat) 决战：E10 metrics 略优（Valid RankIC +0.0593 / 最小 gap / 最高 RICIR），但 E2 的 **price path 更稳 + Valid Top0.1% net 8.82 vs 7.70**，最终采纳 E2。
- 教训沉淀进项目 memory（[[feedback_sota_judgement_multi_metric]]）：**SOTA 判定不能只用 Valid RankIC 单一数字**，须叠加 price path + Top0.1% net bps。
- ckpt4_clean (E2 + 54 fa4) 作为后续验证：Top0.1% 退化、price path 不稳 → 维持 E2 为 SOTA。

#### 3. 收录的 ad-hoc 课题研究报告

> 本节 9 份报告全部为非 skill 标准产出，建议完整复制到 `updates/20260525_update/reports/`。

##### 3.1 Phase 7: Latency → PnL Realization 深度研究（FINAL）
- **原路径**：`/home/cken/crypto_world/research/analyzer_bt_gap/reports/PHASE7_REPORT_FINAL.md`
- **本地副本**：`updates/20260525_update/reports/analyzer_bt_gap_PHASE7_REPORT_FINAL.md`
- **研究方向**：归因 issue #117 中 "Analyzer LGBM Top0.1% 前瞻 +13.92 bps 但 BT Valid 反号" 的 capture gap
- **核心结论**：Valid 期 close-basis "+7.61 bps alpha" 几乎 100% 是 close→mid reference bias（artifact = close_to_mid_t0 +12.00 − close_to_mid_t100 +0.31 ≈ +11.70 bps）；真实 mid-basis alpha 在 (sym,ds) cluster 下 t=-1.37 p=0.18 不显著。**直接催生 issue #119 label 大迁移**。

##### 3.2 Basic Table Alignment Report
- **原路径**：`/home/cken/crypto_world/research/spread_distribution/BASIC_TABLE_ALIGNMENT_REPORT.md`
- **本地副本**：`updates/20260525_update/reports/spread_distribution_BASIC_TABLE_ALIGNMENT_REPORT.md`
- **研究方向**：验证 basic_table 与 fa1/fa2/fa3/fa4 pool 在 7 币种 × 3 日期的 Join 对齐
- **核心结论**：168 cells 全 PASS，0 FAIL，0 MISSING。basic_table 作为统一 alignment anchor 上线成立（issue #121）。

##### 3.3 BT mid-label 全量回测
- **原路径**：`/home/cken/crypto_world/research/spread_distribution/BT_MIDLABEL_REPORT.md`（同时另有 `report/BT_REPORT.md`）
- **本地副本**：`updates/20260525_update/reports/spread_distribution_BT_MIDLABEL_REPORT.md`
- **研究方向**：mid-label 模型（155 维 fa4_merged_sota100_midlabel）接入 zebra 回测后的真实 PnL
- **核心结论**：Valid Rank IC +0.0558（close-SOTA +0.0427，+31%）；IC decay 3× 更慢。证实切 mid-label 后 LGBM 信号质量整体上升。

##### 3.4 Basic Table vs Phase1 差异分析
- **原路径**：`/home/cken/crypto_world/research/spread_distribution/BASIC_TABLE_VS_PHASE1_DIFF.md`
- **本地副本**：`updates/20260525_update/reports/spread_distribution_BASIC_TABLE_VS_PHASE1_DIFF.md`
- **研究方向**：basic_table 与 Phase 1 原始 spread 分布的差异定位
- **核心结论**：辅助证据，支持 §1.3 数据 schema 决策

##### 3.5 Campaign 123 Metrics Matrix
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/campaign123_metrics.md`
- **本地副本**：`updates/20260525_update/reports/ic_fa1234_mid_campaign123_metrics.md`
- **研究方向**：12 个对照实验（E1-E12）的标准化 metrics 矩阵
- **核心结论**：见 §2。本期 SOTA 决策的最终矩阵依据。

##### 3.6 Campaign 123 Top-10 Feature Importance per Experiment
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/campaign123_fi_top10.md`
- **本地副本**：`updates/20260525_update/reports/ic_fa1234_mid_campaign123_fi_top10.md`
- **研究方向**：12 实验各自 top-10 LGBM gain 因子对照
- **核心结论**：`fa2_confirmed_flow_h20` 是所有实验 #1 特征（gain 8-13%）；fa1 stale 系列 + fa2 big/ofi 系列普遍居前

##### 3.7 IC fa1234 mid h100 全量
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/ic_fa1234_mid_h100.md`
- **本地副本**：`updates/20260525_update/reports/ic_fa1234_mid_ic_fa1234_mid_h100.md`
- **研究方向**：mid-label h100 下 fa1+fa2+fa3+fa4 全部因子的单因子 IC
- **核心结论**：作为 corr filter / IC-selected 子集的数据底座

##### 3.8 Mid corr filter top100 / top200
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/corr_filter_mid_top100.md` / `corr_filter_mid_top200.md`
- **本地副本**：`updates/20260525_update/reports/ic_fa1234_mid_corr_filter_mid_top100.md` + `corr_filter_mid_top200.md`
- **研究方向**：mid-label 上 |r|<0.7/0.8 相关性过滤
- **核心结论**：对应 E10 (~74 feat) / E11 (~148 feat)；filter pipeline 留作未来 FA5+ baseline 工具

##### 3.9 FA4 Analyzer 完整 Metrics 汇总
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa4/report/analyzer_summary.md`
- **本地副本**：`updates/20260525_update/reports/fa4_analyzer_summary.md`
- **研究方向**：fa4 落地后 close-label 4 份 analyzer 报告（A-only/clip, B-only/rank, C-merged/clip, D-merged/rank）的核心 IC/RankIC 汇总
- **核心结论**：fa4 单 FA Valid RankIC 0.0153~0.0202 偏弱；fa4+SOTA100 merged 在 rank 模式 Valid RankIC 提升到 0.0444，但与本期最终 mid-label SOTA E2 (0.0579) 不直接可比

> ⚠️ 注：上述 9 份均为 ad-hoc 课题报告，符合 research_updates 收录规则；fa4 的 `analyzer_summary.md` 严格意义上是 realize-factor skill 的副产物，但因其 close-label 出身、与本期 mid-label 决策有直接对照价值，按个例收录。

#### 4. 相关 Project Issues

| # | 标题 | 状态 | 一句话（进展/结论） | 链接 |
|---|------|------|-------------------|------|
| #117 | Analyzer LGBM 前瞻收益 vs Backtest 实盘：85-120% capture gap 深度归因 | OPEN | Phase 7 完成：Valid close-basis "+7.61 bps" 几乎 100% artifact；催生 #119 mid 迁移 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/117 |
| #118 | crypto MCP 改进设计（对齐 HFT 投研流程） | OPEN | 设计稿讨论中，未落地 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/118 |
| #119 | Crypto Spread 分布研究 + Label/Net-Return 口径评估 | OPEN | mid-label 主口径确认 + basic_table 锚点确认（target §1.2.1/§1.6 已更新） | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/119 |
| #120 | Close-based features 全面 mid 化 follow-up | OPEN | fa1/fa2/fa3/fa4 整池 mid 化已完成 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/120 |
| #121 | basic_table 底表实现计划 | OPEN | basic_table 上线，168 cells alignment 全 PASS（见 §3.2） | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/121 |
| #122 | FA3/FA4 mid-label 重验 campaign | OPEN | campaign #122/#123 完成；最终 mid SOTA = E2_mid_sota100 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/122 |
| #124 | Analyzer RankIC 与 BT PnL 不一致：评价体系需要迭代对齐 | OPEN | 评价体系问题立项；memory feedback 沉淀；待后续 BT pipeline 迭代 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/124 |
| #114 | Crypto 投研方法论改进：fa3 评估流程漏洞归因 | OPEN | 本期新增证据：mid-label 下 fa3/fa4 仍无法进 SOTA，4 条 hard gate 进一步强化 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/114 |
| #116 | Crypto 投研首次 benchmark #0 落定 | OPEN | 已被 Refresh #1 (E2 mid_sota100) 取代，建议关闭 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/116 |

不收录（虽然在窗口内但跨项目）：
- #123（HFT analyzer2 symlink dangling，HFT 侧）
- #125（HFT deep-factor-research agent horizon 误用）
- #126/#127（HFT SDK / 实盘部署）

#### 5. Target / 方法论变化

> 本期 target_and_workflow.md **已被用户在 04-19 手工更新**（4 次 commit：`f0ad5c2` / `8014978` / `c234b0a` / `ce13fd4` / `35ffa84`），主要变更：
> - 顶部加 "重大变更 2026-04-19" 横幅
> - §1.2.1 新增 "Label basis（mid-label 主口径）"
> - §1.3 数据表新增 basic_table 行
> - §1.6 方法论原则加 mid-label 主口径条款
>
> 本 meta-review 仅记录这些变化已生效，不再提调整建议。

新出现的方法论沉淀（仅 memory 层，target 暂未引用）：
- `[[feedback_sota_judgement_multi_metric]]` — SOTA 不能单凭 Valid RankIC，须看 price path + Top0.1% net
- `[[feedback_statistical_power_small_valid]]` — 42 天 Valid 难以区分 +0.001 RankIC 量级差异，需 Welch t-test

建议下一轮（或独立 session）把这两条吸收进 target_and_workflow.md §1.5 评估口径或 §1.6 方法论原则。

#### 6. 本期观察到的模式 / 待关注方向

1. **mid-label 大迁移闭环已完成**：从 issue #117 归因 → #119 决策 → #120/#121 工程 → campaign #122/#123 重验 → SOTA Refresh #1，一周内完成大型基础设施 + 模型口径迁移。这是 crypto 投研架构上最重要的进展。
2. **fa3 与 fa4 都进入了"已落地但不入 SOTA"状态**：连续两个 FA 整体净负向，需在下一轮 FA 之前正面回应 SKILL 同步（issue #114 v2 + #122 都指向同一 gap）。
3. **Stage 5 benchmark refresh 已经形成 ad-hoc 路径但仍缺独立 skill**：本期 Refresh #1 完全是手工 + ad-hoc 脚本（research/ic_fa1234_mid/），未抽象为 repeatable skill。下一次 Refresh #2 之前建议先把流程标准化。
4. **回测评价体系成熟度不足**（issue #124）：Analyzer RankIC vs BT PnL 不一致暴露评价体系层级问题，影响 SOTA 决策可信度。
5. **04-23 之后 crypto 进入长停滞**：用户工作切到 HFT 与 lgj SDK audit，crypto 侧无新增 session / FA / realize。这是合理的节奏调整，但 Update #2 之后需明确 "下次 meta-review 触发条件"。
6. **session #65 是新方向起点未完成**：queue_survival_panel 仅完成 Phase 1，下一轮回 crypto 时若续做将是 fa5 的第一个候选源。

#### 7. 深度分析报告

> 本期未触发定向深度分析（当前为可选项）。
>
> 候选定向题目（如未来需要）：
> - "Refresh #1 后 fa3/fa4 仍负向的根因是什么？是研究质量问题还是 LGBM 集成层问题？"
> - "评价体系迭代（issue #124）的具体方案"
> - "Stage 5 benchmark refresh skill 化方案"

---

## 候选 sota_snapshot 更新 diff

### 元数据段

| 字段 | 原值 | 新值 |
|---|---|---|
| 本次 snapshot 日期 | 2026-04-17 | **2026-05-25** |
| 上次 snapshot 日期 | — (Bootstrap) | **2026-04-17** |
| 最后一次 benchmark refresh 日期 | 2026-04-17 (Bootstrap #0) | **2026-04-22 (Refresh #1, campaign #123 E2 决策日)** |
| 研究 session 覆盖到 | #64 convexity_liquidity_density | **#65 queue_survival_panel**（Phase 1 only） |
| FA 覆盖到 | FA3 | **FA4** |
| realize pool 覆盖到 | fa3 | **fa4** |

### §1.1 因子集构成

- 新增 fa4 行：55 因子 / ✅ 已落地（工程 54 个） / 2025-07-01 ~ 2026-01-26 / 来源 #42+#52-64 / 进入 SOTA 模型？❌（campaign #123 验证负向）
- 修改 fa1/fa2 行的 "进入 SOTA 模型？" 列：
  - fa1: "59 入选 FI top100" → "**57 入选 mid FI top100**"
  - fa2: "41 入选 FI top100" → "**43 入选 mid FI top100**"
- Factor Pool 合计：381 → **436**（+55 fa4）
- 新加表头说明："SOTA 模型现为 **mid-label** FI top100，构成与原 close-label SOTA 相比有 2 个 fa1↔fa2 互换"

### §1.2 LGBM SOTA 指标

- Analyzer 报告路径：`fa3_tuning_stage1/fi_top100_mdil100k/` → **`campaign123_clean_sota/E2_mid_sota100/clip/`**
- 信号模式：`clip 0.01` 保持；excl 列表保持
- Train/Valid 切分 / 样本数 / LGBM 超参 / trees：基本保持（具体见 lgbm_train_info.json）
- **关键指标全更新**：

| 指标 | Train | Valid |
|------|------:|------:|
| IC | 0.0761 | 0.0616 |
| RankIC | **0.0705** | **0.0579** |
| gap (RankIC) | — | 0.0126 |
| RICIR | 4.14 | 2.68 |
| Valid Top0.1% net (bps) | — | **8.82** |
| Valid RankIC pos% | — | 100% |

- Top 10 特征全更新（见 §2 上方列表）
- SOTA 选型说明改写：从 "FI top100 vs full fa1+fa2 (198)" 改为 "campaign #123 E2 vs E10 多维判据决战"

### §1.3 SOTA 回测结果

- 回测锚点（升级）：`fi_top100_q999_close_m05_consec3/` → **`E2_mid_sota100_q999_close_m05_consec3/`**
- 关键指标全更新（来自 E2 BT 实际数据）：

| 指标 | Train | Valid | 合计 |
|------|------:|------:|------:|
| Net PnL (USDT) | +1,822 | +7 | +1,830 |
| Net Rate (bps) | +1.88 | +0.04 | — |
| **Sharpe** | **7.93** 🥇 | **+0.16** 🆕 由负翻正 | — |
| MaxDD (USDT) | −62 | −146 | — |
| Roundtrips | 14,267 | 2,850 | 17,117 |
| Avg Daily RTs | — | — | 84.7 |

- "相对原 baseline 的改善"段重写为 "相对 close-label SOTA 的改善"
- 选型依据段补充：campaign #123 E2 vs E10 决战 + 多维判据原则
- 历史变迁段新增：2026-04-22 Refresh #1: E2 mid_sota100 取代 Bootstrap #0
- Alpha 衰减观察：**已修复**（mid-label 切换后 Valid Sharpe 由 −1.29 翻正到 +0.16）
- 关联 Issue 新增：#119/#121/#122/#124

### §2 研究管线累计状态

| 字段 | 旧值 | 新值 |
|------|-----:|-----:|
| research session 总数（编号） | 64 | **65** |
| factor list (FA) 总数 | 3 | **4** |
| realized pool 总数 | 3 | **4** |
| benchmark refresh 次数 | 1 (Bootstrap #0) | **2** (Bootstrap #0 + Refresh #1 = E2 mid_sota100) |
| 待编译 session 数 | ~13 (#52-64) | **0**（FA4 已合编完成；#65 在 Phase 1 不构成"待编译"） |

### §3 开放研究方向 / 待关注模式

新增条目（旧的可选择性保留）：
1. **mid-label SOTA 已锁定**：下一轮 deep-research / realize 直接对标 E2 mid_sota100 的 Valid RankIC 0.0579 / Top0.1% net 8.82 bps
2. **fa3 + fa4 双失效闭环**：连续两个 FA 进 pool 不入模型，issue #114 + #122 都未根本解决；下一轮 FA 之前建议 skill 同步 + 评价体系迭代
3. **Stage 5 skill 化优先级提升**：Refresh #1 完全 ad-hoc，Refresh #2 之前必须形成 repeatable
4. **评价体系迭代（issue #124）**：Analyzer RankIC ↔ BT PnL gap 是当前 SOTA 决策的最大不确定性来源
5. **session #65 Phase 2 续做**：queue_survival_panel 是 fa5 的第一个候选源

### §4 本版 snapshot 生成说明

- **生成来源**：`/crypto-meta-review` 第二次运行（2026-05-25），扫描 since=2026-04-17 之后所有 delta
- **本期 update 子目录**：`updates/20260525_update/`（含 9 份 ad-hoc 报告副本）
- **归档**：旧版本归档于 `sota_archive/sota_snapshot_2026-04-17.md`
- **完整 meta-review 报告**：`reviews/meta_review_2026-05-25.md`（本文件）

---

## 观察到的问题 / 建议（非落盘内容，仅供用户参考）

1. **04-23 之后停滞期**：crypto 侧 5 周无产出，主要因为用户重心在 lgj SDK audit。建议下次 meta-review 在 audit 结束后触发，或在 session #65 Phase 2 续做时触发。
2. **Refresh #1 的 ad-hoc 性**：campaign #123 的脚本与决策流程全在 research/ic_fa1234_mid/ 临时目录，未沉淀为 skill。**强烈建议**在下一轮 Refresh 前 skill 化（与 crypto-meta-review 同层级的 crypto-benchmark-refresh skill）。
3. **fa3 / fa4 连续失效**：是否要修改 deep-factor-research 在 Phase 3 的评价标准？现行标准只看单因子 IC + LGBM 联合 IC，但实际 SOTA 决策已转向多维（price path + Top0.1% net）。这是 SKILL 同步的下一个高优先级点。
4. **建议关闭 issue #116**（Bootstrap #0 落定）：已被 Refresh #1 取代，可标 ready-to-close。
5. **新增 reference memory 候选**：sota_snapshot 的"模型路径 + whitelist 路径"组合应进 memory `[[reference_sota_anchor]]`，避免后续 agent 引用过期路径。
