# Crypto 投研进度更新日志

> **用途**：时间序列 changelog，记录每次 meta-review 之间的投研增量。**Append-only**，新条目追加到文件**顶部**（最新在上）。
>
> **结构**：两层。本文件是索引 + 每期中等篇幅总结；每期的 ad-hoc 课题报告副本 + 可选深度分析放在 `updates/{yyyymmdd}_update/` 子目录。
>
> **维护方式**：由 `/crypto-meta-review` skill 在用户确认后追加新条目 + 创建对应子目录。**agent 不得修改历史条目**，只能追加新条目和补充当前期子目录。

---

## 目录结构约定

```
workflows/crypto/
├── research_updates.md             # 本文件：索引 + 每期摘要
└── updates/
    ├── 20260416_update/
    │   ├── reports/                # 本期收录的 ad-hoc 课题研究报告副本
    │   │   ├── fa3_stage1_failure_analysis.md
    │   │   └── ...
    │   └── summary.md              # 可选：本期定向深度分析报告
    ├── 20260320_update/
    │   └── ...
```

### 收录规则

| 内容 | 处理方式 | 理由 |
|------|---------|------|
| **ad-hoc 课题研究报告** | 完整复制一份到 `reports/` | 这类是非固定流程产出（如 fa 失效归因、方法论实验、专项实验报告），值得冻结快照。原路径也要记录以便追溯 |
| Skill 固定产出（ob research_report / FA factor_list / zebra_pool analyzer / backtest 报告） | **不收录**，仅在本文件以聚合计数方式提及（如"本期新增 ob #47-49 / 新增 FA4 / 刷了 fa4 全历史"） | 这些由对应 skill 在自己的工作目录里维护，数量多且位置稳定，无需冗余复制 |
| **Project-related GitHub issues** | 不做本地快照，只在本文件用 "#编号 + 标题 + 一句话 + 链接" 列出 | 跟 GitHub 上游永远一致，省去同步成本 |
| **本期深度分析** | 写入 `summary.md` | 可选——质量分析当前为可选项，非每期必做 |

### Ad-hoc 报告判定

"ad-hoc 课题报告" 指用户临时开题做的深度分析或实验，典型特征：
- 不是某个 skill 的标准产出
- 文件名通常是 `REPORT.md` / `analysis.md` / `failure_analysis.md` 这类临时命名
- 通常放在 `zebra_pool/*/experiments/` 或 `crypto_ob_research/*/` 之外的临时路径
- 例子：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/REPORT.md`

skill 在 Step 4 询问用户时，应列出候选报告让用户勾选保留哪些（避免把临时草稿也拉进来）。

---

## 条目模板

````markdown
## [YYYY-MM-DD] Update #{N}

**时间区间**：{上次 update 日期} → {本次日期}
**子目录**：[`updates/{yyyymmdd}_update/`](updates/{yyyymmdd}_update/)

### 1. 本期产出概览（聚合计数）

| 类别 | 新增 | 明细 |
|------|------|------|
| research session | X 个 | #47, #48, #49（完成 X / 中断 Y / FAIL Z） |
| factor list (FA) | X 个 | FA4（来源 #42-45） |
| realized pool | X 个 | fa4 |
| analyzer run | X 个 | fa4_v1, fa4_merged_baseline69 |
| benchmark refresh | 是/否 | 新 benchmark: benchmark_{date} |
| ad-hoc 课题报告 | X 份 | 见 §3 |
| 相关 issue | X 个 | 见 §4 |

### 2. SOTA 提升量

**若本期有 benchmark refresh 或 signal backtest**：

| 指标 | 上期 | 本期 | 变化 |
|------|------|------|------|
| 已落地因子总数 | X | Y | +Z |
| Merged benchmark valid OOS IC (next400 rank) | X | Y | +Zbps |
| 回测 valid Sharpe (taker) | X | Y | +Z |
| 回测 valid Sharpe (maker) | X | Y | +Z |

**若本期未触发 benchmark refresh / backtest**：
> 本期未触发 benchmark refresh 或 signal backtest。SOTA 基准仍为 `benchmark_{old_date}`，指标无增量。
> 累计待合并 FA 数：X（target_and_workflow.md §2 Stage 5 建议每 2-3 个新 FA 触发一次 refresh）

### 3. 收录的 ad-hoc 课题研究报告

> 本节仅列 ad-hoc 课题型报告，不列 skill 固定产出的标准报告。
> 每份报告已完整复制到 `updates/{yyyymmdd}_update/reports/`。

#### 3.1 {报告标题}
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/REPORT.md`
- **本地副本**：[`updates/20260416_update/reports/fa3_stage1_report.md`](updates/20260416_update/reports/fa3_stage1_report.md)
- **研究方向**：{一句话描述该报告研究的问题或方向}
- **核心结论**：{1-3 句话摘要该报告的主要发现}

#### 3.2 ...

**若本期无 ad-hoc 报告**：
> 本期无 ad-hoc 课题报告。

### 4. 相关 Project Issues

> 自动扫自 `ligenjian001-ai/hft-sdk-issues` 项目，筛选条件：label 含 `project:quant_trading` 且
> 本期内有更新。最终收录由用户在 meta-review 确认环节勾选。

| # | 标题 | 状态 | 一句话（解决的问题/结论/进展） | 链接 |
|---|------|------|-------------------------------|------|
| #114 | Crypto 投研方法论改进：小样本 IC 不可信 + fa3 评估流程漏洞归因 | open | 讨论 how to 替代 IC gate + fa3 失效归因 TODO 中 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/114 |

**若本期无相关 issue**：
> 本期内无 `project:quant_trading` issue 更新。

### 5. Target / 方法论变化

- [ ] target_and_workflow.md §1 是否调整？调整内容：...
- [ ] 方法论原则是否有更新？...
- [ ] 数据纪律红线是否有变？...

**若无变化**：
> 本期 target 与方法论无变化。

### 6. 本期观察到的模式 / 待关注方向

- {反复出现的问题 / blocker，如适用}
- {值得下一期关注的方向}
- {skill 本身需要改进的地方}

### 7. 深度分析报告

**若本期做了定向深度分析**：
- 完整分析：[`updates/{yyyymmdd}_update/summary.md`](updates/{yyyymmdd}_update/summary.md)
- 分析聚焦：{如 "最近 15 session 的 blocking pattern" / "factor 覆盖 gap" / ...}
- 关键发现：{3-5 句话摘要}

**若本期未做**：
> 本期未触发定向深度分析（当前为可选项）。
````

---

<!-- meta-review skill 在此行下方追加新条目，保持最新在上 -->

## [2026-05-25] Update #2

**时间区间**：2026-04-17 → 2026-05-25
**子目录**：[`updates/20260525_update/`](updates/20260525_update/)

> ⚠️ 本期为"高强度 + 长停滞"两段式：04-17 → 04-23 一周内完成 label 大迁移 + benchmark refresh #1 + FA4 落地；04-23 之后约 5 周用户工作切到 HFT/lgj SDK audit，crypto 侧无新增产出。本 Update 主要追认 04-17 → 04-23 一周的高密度工作。

### 1. 本期产出概览（聚合计数）

| 类别 | 新增 | 明细 |
|------|------|------|
| research session | 1 | #65 queue_survival_panel（2026-04-18 启动，Phase 1 完成，未到 Phase 2，无 factor_definition.md） |
| factor list (FA) | 1 | FA4（来源 #42 + #52-64 共 14 项研究，55 因子，7 分组，CONDITIONAL PASS） |
| realized pool | 1 | fa4（54 因子工程交付；FA list 55 vs realize 54 的 1 个差异来自实施合并/剔除） |
| analyzer run | 多批 | (a) `fa4/` 4 close-label + 3 mid-label；(b) `campaign122_mid/` 5 pairs h100；(c) `campaign122_mid_h400/` 5 pairs h400；(d) `campaign123_clean_sota/` 12 实验 E1-E12 + ckpt4_clean |
| benchmark refresh | **是（#1）** | **新 SOTA: `campaign123_clean_sota/E2_mid_sota100/`**（100 维 mid-label fa1+fa2 FI top100，57 fa1 + 43 fa2） |
| ad-hoc 课题报告 | 9 份（10 文件） | 见 §3 |
| 相关 issue | 9 个 | 见 §4 |

### 2. SOTA 提升量

**SOTA 模型对比表**（Bootstrap #0 close-label → Refresh #1 mid-label）：

| 指标 | 上期 (Bootstrap #0) | 本期 (Refresh #1 = E2 mid_sota100) | 变化 |
|------|--------:|--------:|--------|
| Label 口径 | close-to-close | **mid-to-mid (basic_table anchor)** | 切换（issue #119/#121） |
| 模型路径 | `fa3_tuning_stage1/fi_top100_mdil100k/` | `campaign123_clean_sota/E2_mid_sota100/clip/` | — |
| 因子集 | fa1 59 + fa2 41 | **fa1 57 + fa2 43**（同 100 维） | 2 个 fa1↔fa2 互换 |
| Train RankIC | 0.0635 | 0.0705 | +0.0070 |
| **Valid RankIC** | 0.0427 | **0.0579** | **+0.0152 (+36%)** |
| Gap RankIC | 0.0208 | 0.0126 | −0.0082（缩小 39%） |
| RICIR (Valid) | _未补_ | 2.68 | — |
| **Valid Top0.1% net (bps)** | 不可直接对比（close-bias） | **8.82** | campaign #123 12 实验最高 |
| Valid RankIC pos% | _未补_ | 100% | — |
| 已落地因子总数 (factor pool) | 381 | **436** | +55 fa4 |
| BT Total Net (Exp D 同 recipe) | +1,650 USDT | **+1,830 USDT** | +11% |
| BT Train Sharpe | 6.63 | **7.93** | +20% |
| **BT Valid Sharpe** | **−1.29** | **+0.16** | **由负翻正** |

**关键洞察**（Refresh #1 的两个本质改变）：

1. **mid-label 修复了 close-bias 导致的 Valid alpha 衰减**：Phase 7 归因证明 Valid 期 close-basis "+7.61 bps Top0.1% alpha" 几乎 100% 是 close→mid reference bias。切到 mid-label 后 Valid Sharpe 从 −1.29 翻正到 +0.16，证实"先前 valid 期 alpha 衰减"主要不是结构问题。
2. **fa4 落地但不进入 SOTA 模型**：campaign #123 E4 (fa124_full) Valid Top0.1% **6.99 < E2 8.82**；E8/E9 (fa4 IC-selected) 微弱正但 price path 不稳；ckpt4_clean (E2+54 fa4) Valid Top0.1% 跌到 7.66。**fa4 与 fa3 同列入 factor pool 但不入默认 SOTA 模型**。

**SOTA 模型锚点**：
- 模型目录：`/data/db/crypto/analyzer/campaign123_clean_sota/E2_mid_sota100/clip/`
- 模型文件：`lgbm_model.txt`
- Whitelist：`/home/cken/crypto_world/research/ic_fa1234_mid/wl_mid_fi_top100.txt`
- Top 特征 (gain ratio)：`fa2_confirmed_flow_h20` (8.1%) / `fa1_stale_log_ratio` (6.8%) / `fa2_ofi_regime_z` (6.1%) / `fa1_stale_ema_logmax_50` (5.8%) / `fa2_impact_delta_10_100` (4.3%)

**SOTA 决策依据**：
- campaign #123 12 个对照 + E2 vs E10 决战：E10 (74 feat) metrics 略优（Valid RankIC +0.0593 / 最小 gap / 最高 RICIR），但 **E2 的 price path 更稳 + Valid Top0.1% net 8.82 vs 7.70**，最终采纳 E2
- 教训沉淀进项目 memory（`[[feedback_sota_judgement_multi_metric]]`）：**SOTA 判定不能只用 Valid RankIC 单一数字**，须叠加 price path + Top0.1% net bps
- ckpt4_clean (E2 + 54 fa4) 作为后续验证：Top0.1% 退化、price path 不稳 → 维持 E2 为 SOTA

### 3. 收录的 ad-hoc 课题研究报告

> 本节 9 份课题（10 文件）已完整复制到 `updates/20260525_update/reports/`。

#### 3.1 Phase 7: Latency → PnL Realization 深度研究（FINAL）
- **原路径**：`/home/cken/crypto_world/research/analyzer_bt_gap/reports/PHASE7_REPORT_FINAL.md`
- **本地副本**：[`updates/20260525_update/reports/analyzer_bt_gap_PHASE7_REPORT_FINAL.md`](updates/20260525_update/reports/analyzer_bt_gap_PHASE7_REPORT_FINAL.md)
- **研究方向**：归因 issue #117 中 "Analyzer LGBM Top0.1% 前瞻 +13.92 bps 但 BT Valid 反号" 的 capture gap
- **核心结论**：Valid 期 close-basis "+7.61 bps alpha" 几乎 100% 是 close→mid reference bias（artifact = close_to_mid_t0 +12.00 − close_to_mid_t100 +0.31 ≈ +11.70 bps）；真实 mid-basis alpha 在 (sym,ds) cluster 下 t=-1.37 p=0.18 不显著。**直接催生 issue #119 label 大迁移**。

#### 3.2 Basic Table Alignment Report
- **原路径**：`/home/cken/crypto_world/research/spread_distribution/BASIC_TABLE_ALIGNMENT_REPORT.md`
- **本地副本**：[`updates/20260525_update/reports/spread_distribution_BASIC_TABLE_ALIGNMENT_REPORT.md`](updates/20260525_update/reports/spread_distribution_BASIC_TABLE_ALIGNMENT_REPORT.md)
- **研究方向**：验证 basic_table 与 fa1/fa2/fa3/fa4 pool 在 7 币种 × 3 日期的 Join 对齐
- **核心结论**：168 cells 全 PASS，0 FAIL，0 MISSING。basic_table 作为统一 alignment anchor 上线成立（issue #121）。

#### 3.3 BT mid-label 全量回测
- **原路径**：`/home/cken/crypto_world/research/spread_distribution/BT_MIDLABEL_REPORT.md`
- **本地副本**：[`updates/20260525_update/reports/spread_distribution_BT_MIDLABEL_REPORT.md`](updates/20260525_update/reports/spread_distribution_BT_MIDLABEL_REPORT.md)
- **研究方向**：mid-label 模型（155 维 fa4_merged_sota100_midlabel）接入 zebra 回测后的真实 PnL
- **核心结论**：Valid Rank IC +0.0558（close-SOTA +0.0427，+31%）；IC decay 3× 更慢。证实切 mid-label 后 LGBM 信号质量整体上升。

#### 3.4 Basic Table vs Phase1 差异分析
- **原路径**：`/home/cken/crypto_world/research/spread_distribution/BASIC_TABLE_VS_PHASE1_DIFF.md`
- **本地副本**：[`updates/20260525_update/reports/spread_distribution_BASIC_TABLE_VS_PHASE1_DIFF.md`](updates/20260525_update/reports/spread_distribution_BASIC_TABLE_VS_PHASE1_DIFF.md)
- **研究方向**：basic_table 与 Phase 1 原始 spread 分布的差异定位
- **核心结论**：辅助证据，支持 §1.3 数据 schema 决策

#### 3.5 Campaign 123 Metrics Matrix
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/campaign123_metrics.md`
- **本地副本**：[`updates/20260525_update/reports/ic_fa1234_mid_campaign123_metrics.md`](updates/20260525_update/reports/ic_fa1234_mid_campaign123_metrics.md)
- **研究方向**：12 个对照实验（E1-E12）的标准化 metrics 矩阵
- **核心结论**：见 §2。本期 SOTA 决策的最终矩阵依据。

#### 3.6 Campaign 123 Top-10 Feature Importance per Experiment
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/campaign123_fi_top10.md`
- **本地副本**：[`updates/20260525_update/reports/ic_fa1234_mid_campaign123_fi_top10.md`](updates/20260525_update/reports/ic_fa1234_mid_campaign123_fi_top10.md)
- **研究方向**：12 实验各自 top-10 LGBM gain 因子对照
- **核心结论**：`fa2_confirmed_flow_h20` 是所有实验 #1 特征（gain 8-13%）；fa1 stale 系列 + fa2 big/ofi 系列普遍居前

#### 3.7 IC fa1234 mid h100 全量
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/ic_fa1234_mid_h100.md`
- **本地副本**：[`updates/20260525_update/reports/ic_fa1234_mid_ic_fa1234_mid_h100.md`](updates/20260525_update/reports/ic_fa1234_mid_ic_fa1234_mid_h100.md)
- **研究方向**：mid-label h100 下 fa1+fa2+fa3+fa4 全部因子的单因子 IC
- **核心结论**：作为 corr filter / IC-selected 子集的数据底座

#### 3.8 Mid corr filter top100 / top200
- **原路径**：`/home/cken/crypto_world/research/ic_fa1234_mid/corr_filter_mid_top100.md` + `corr_filter_mid_top200.md`
- **本地副本**：[`updates/20260525_update/reports/ic_fa1234_mid_corr_filter_mid_top100.md`](updates/20260525_update/reports/ic_fa1234_mid_corr_filter_mid_top100.md) + [`corr_filter_mid_top200.md`](updates/20260525_update/reports/ic_fa1234_mid_corr_filter_mid_top200.md)
- **研究方向**：mid-label 上 |r|<0.7/0.8 相关性过滤
- **核心结论**：对应 E10 (~74 feat) / E11 (~148 feat)；filter pipeline 留作未来 FA5+ baseline 工具

#### 3.9 FA4 Analyzer 完整 Metrics 汇总
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa4/report/analyzer_summary.md`
- **本地副本**：[`updates/20260525_update/reports/fa4_analyzer_summary.md`](updates/20260525_update/reports/fa4_analyzer_summary.md)
- **研究方向**：fa4 落地后 close-label 4 份 analyzer 报告（A-only/clip, B-only/rank, C-merged/clip, D-merged/rank）的核心 IC/RankIC 汇总
- **核心结论**：fa4 单 FA Valid RankIC 0.0153~0.0202 偏弱；fa4+SOTA100 merged 在 rank 模式 Valid RankIC 提升到 0.0444，但与本期最终 mid-label SOTA E2 (0.0579) 不直接可比

> ⚠️ fa4 的 `analyzer_summary.md` 严格意义上是 realize-factor skill 副产物，但因其与本期 mid-label 决策有直接对照价值，按个例收录。

### 4. 相关 Project Issues

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
| #116 | Crypto 投研首次 benchmark #0 落定 | OPEN (建议关闭) | 已被 Refresh #1 (E2 mid_sota100) 取代 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/116 |

### 5. Target / 方法论变化

> 本期 `target_and_workflow.md` 已被用户在 04-19 手工更新（5 个 commit：`f0ad5c2` / `8014978` / `c234b0a` / `35ffa84` / `ce13fd4`），主要变更：
> - 顶部加 "重大变更 2026-04-19" 横幅
> - §1.2.1 新增 "Label basis（mid-label 主口径）"
> - §1.3 数据表新增 basic_table 行（覆盖 225 天，ETH 224 天）
> - §1.6 方法论原则加 mid-label 主口径条款
>
> 本 meta-review 仅记录这些变化已生效。

新出现的方法论沉淀（仅 memory 层，target 暂未引用）：
- `[[feedback_sota_judgement_multi_metric]]` — SOTA 不能单凭 Valid RankIC，须看 price path + Top0.1% net
- `[[feedback_statistical_power_small_valid]]` — 42 天 Valid 难以区分 +0.001 RankIC 量级差异，需 Welch t-test

建议下一轮（或独立 session）把这两条吸收进 `target_and_workflow.md` §1.5 评估口径或 §1.6 方法论原则。

### 6. 本期观察到的模式 / 待关注方向

1. **mid-label 大迁移闭环已完成**：从 issue #117 归因 → #119 决策 → #120/#121 工程 → campaign #122/#123 重验 → SOTA Refresh #1，一周内完成大型基础设施 + 模型口径迁移。这是 crypto 投研架构上最重要的进展。
2. **fa3 与 fa4 都进入了"已落地但不入 SOTA"状态**：连续两个 FA 整体净负向，需在下一轮 FA 之前正面回应 SKILL 同步（issue #114 v2 + #122 都指向同一 gap）。
3. **Stage 5 benchmark refresh 已经形成 ad-hoc 路径但仍缺独立 skill**：本期 Refresh #1 完全是手工 + ad-hoc 脚本（`research/ic_fa1234_mid/`），未抽象为 repeatable skill。下一次 Refresh #2 之前建议先把流程标准化。
4. **回测评价体系成熟度不足**（issue #124）：Analyzer RankIC vs BT PnL 不一致暴露评价体系层级问题，影响 SOTA 决策可信度。
5. **04-23 之后 crypto 进入长停滞**：用户工作切到 HFT 与 lgj SDK audit，crypto 侧无新增 session / FA / realize。这是合理的节奏调整，但 Update #2 之后需明确"下次 meta-review 触发条件"。
6. **session #65 是新方向起点未完成**：queue_survival_panel 仅完成 Phase 1，下一轮回 crypto 时若续做将是 fa5 的第一个候选源。

### 7. 深度分析报告

> 本期未触发定向深度分析（当前为可选项）。
>
> 候选定向题目（如未来需要）：
> - "Refresh #1 后 fa3/fa4 仍负向的根因是什么？是研究质量问题还是 LGBM 集成层问题？"
> - "评价体系迭代（issue #124）的具体方案"
> - "Stage 5 benchmark refresh skill 化方案"

---

## [2026-04-17] Update #1 (Bootstrap)

**时间区间**：Bootstrap（历史全量） → 2026-04-17
**子目录**：[`updates/20260417_update/`](updates/20260417_update/)

### 1. 本期产出概览（聚合计数）

| 类别 | 新增 | 明细 |
|------|------|------|
| research session | 64 | `crypto_ob_research/1-*` ~ `64-*`（`10_zh`/`11_zh` 为翻译副本；`#23` 与 `#21` 同主题重复；4 known failed/interrupted: #9/#15/#18/#23） |
| factor list (FA) | 3 | FA1（来源 #1-20）/ FA2（来源 #21-34）/ FA3（来源 #35-51） |
| realized pool | 3 | fa1 (123 因子) / fa2 (75 因子) / fa3 (114 因子) + baseline f001 (30) / f002 (39) / f001_f002_merged |
| analyzer run | 4 目录（含 28 个 tuning 子实验） | `fa1` / `fa2` / `fa3` / `fa3_tuning_stage1/{stage1,stage1b~g,stage2a~h,h100clip_R1~R7,h400rank_*,fair_*,corr71_*,corr151_*,fa12_plus_fa3_*,fi_top100,fi_top150}` |
| benchmark refresh | **是（#0，Bootstrap 基线）** | `/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/` |
| ad-hoc 课题报告 | 6 份 | 见 §3 |
| 相关 issue | 6 个 | 见 §4 |

### 2. SOTA 提升量

> 本期为 **Bootstrap #1**，无上期对比。以下为首次 SOTA 基线（FI top100 模型）：

| 指标 | 本期值 | 备注 |
|------|--------|------|
| 已落地因子总数（factor pool） | 381 | f001(30)+f002(39)+fa1(123)+fa2(75)+fa3(114) |
| SOTA 模型输入特征数 | 100 | FI top100 (LGBM gain Top 100 from fa1+fa2 198)，59 fa1 + 41 fa2 |
| Train RankIC | 0.0635 | h100 clip, ret_lag0_next100 |
| **Valid RankIC** | **0.0427** | 42 天 valid (2025-12-16 ~ 2026-01-26) |
| gap (RankIC) | 0.0208 | — |
| trees (final) | 80 | — |
| 回测 Sharpe/MaxDD | **_待填_** | 用户稍后补 FI top100 signal backtest |

**SOTA 模型锚点**：
- 模型目录：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/`
- Top 特征 (gain ratio)：`fa1_stale_ema_logmax_50` (9.27%) / `fa2_big_interarrival` (6.76%) / `fa1_ewm_add_imbalance_60s` (4.16%) / `fa1_buy_sell_spread_proxy_ema20` (3.96%) / `fa2_big_share_ema60` (3.71%)

**SOTA 决策依据**（用户选定）：
- FI top100 vs full fa1+fa2 (198) Valid RankIC 差仅 −0.0004（非显著），但特征空间缩到一半，对后续 benchmark refresh loop 友好
- FA3 已落地但不入 SOTA 模型：issue #114 v2 双层失效归因（26% R²≥0.5 冗余 + 48% 正交无 alpha）+ `research/ic_fa123/REPORT.md` 三次独立验证（+6/+10/+16 fa3 全部 Valid RankIC 负向 −0.0006 ~ −0.0002）

### 3. 收录的 ad-hoc 课题研究报告

> 本节仅列 ad-hoc 课题型报告。每份已完整复制到 `updates/20260417_update/reports/`。

#### 3.1 IC-based Factor Selection & LGBM Benchmark Experiments — h100 clip
- **原路径**：`/home/cken/crypto_world/research/ic_fa123/REPORT.md`（⚠️ 超出 skill 标准扫描范围，按用户指示强制收录为本期主报告）
- **本地副本**：[`updates/20260417_update/reports/ic_fa123_REPORT.md`](updates/20260417_update/reports/ic_fa123_REPORT.md)
- **研究方向**：8 个对照实验评估 IC-based factor selection（single-factor IC + corr filter）vs LGBM gain-based selection 能否击败 SOTA；fa3 surgical selection 能否带来增量
- **核心结论**：无配置击败 full fa2+fa1 (198) 0.0431；FI top100 (100 features) 0.0427 为接近 SOTA 的最小特征集（本期 SOTA 选定），Δ=−0.0004；fa3 任何子集加入 valid RankIC 均负向；LGBM gain 严格优于 single-factor IC 作为 selector；相关性过滤适合 factor library 管理但不改善 LGBM 性能

#### 3.2 FA3 LGBM Hyperparameter Tuning Experiment Report
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/REPORT.md`
- **本地副本**：[`updates/20260417_update/reports/fa3_stage1_REPORT.md`](updates/20260417_update/reports/fa3_stage1_REPORT.md)
- **研究方向**：h100 clip 上 17 个控制实验（Stage 1/1b/1c/Stage 2/Stage 3-4）扫描 fa3+fa2+fa1 的 LGBM 超参空间
- **核心结论**：最优配置是 fa2+fa1 (无 fa3) tuned recipe at mdil=100k，Valid RankIC 0.0431（比未调优 baseline 0.0386 +11.7%）；任何 fair 比较下加入 fa3 都是 net-negative；原始"fa3 带来 +20-80% RankIC"是 merged-vs-fa3_only 错误基准导致的幻觉

#### 3.3 FA3 失效归因报告 v2
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/FA3_ATTRIBUTION_v2.md`
- **本地副本**：[`updates/20260417_update/reports/fa3_stage1_FA3_ATTRIBUTION_v2.md`](updates/20260417_update/reports/fa3_stage1_FA3_ATTRIBUTION_v2.md)
- **研究方向**：基于 R²-cut sweep (R1-R3) + R²×IC 双 cut (R4-R7) 的 ablation 闭环，归因 fa3 失效
- **核心结论**：R3 (R²<0.2, n=55) 单点 +0.0006 但沿 IC 轴精选 (R4-R7) 反而单调退化；single-factor IC 轴作为 LGBM selector 被否证；fa3 失效分双层：26% R²≥0.5 冗余 + 48% R²<0.2 正交无 alpha

#### 3.4 FA3 研究方法论深度诊断 v2
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/issue_114_analysis/FA3_RESEARCH_METHODOLOGY_DIAGNOSIS_V2.md`
- **本地副本**：[`updates/20260417_update/reports/issue_114_FA3_RESEARCH_METHODOLOGY_DIAGNOSIS_V2.md`](updates/20260417_update/reports/issue_114_FA3_RESEARCH_METHODOLOGY_DIAGNOSIS_V2.md)
- **研究方向**：深读 5 个研究 log (Study #31, #35, #37, #40, #46, #47) 定位 Phase 0-2 过程缺陷；回应 Issue #114 v1 方向偏差
- **核心结论**：SKILL.md 文字没跟上 friction_knowledge_base FK 与 Studies #53-64 实践；研究员已在 Study #47 自写 phase1_skill_update_proposal.md 提议迭代

#### 3.5 Codex FA3 Discovery 独立复核报告
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/issue_114_analysis/CODEX_FA3_DISCOVERY_REPORT.md`
- **本地副本**：[`updates/20260417_update/reports/issue_114_CODEX_FA3_DISCOVERY_REPORT.md`](updates/20260417_update/reports/issue_114_CODEX_FA3_DISCOVERY_REPORT.md)
- **研究方向**：Codex 独立复核 deep-factor-research / skill / target_and_workflow / crypto_mcp / zebra 链路，回答"怎样在研究阶段更高概率找到真正有用的因子"
- **核心结论**：deep-factor-research 非完全失效；主因在 workflow/skill/methodology 层而非 Zebra 工程；真正 gap 在 study-level slotting/admission 未落到研究产物

#### 3.6 FA3 研究流程深度诊断 v1
- **原路径**：`/home/cken/crypto_world/zebra_pool/fa3/experiments/stage1/issue_114_analysis/FA3_PROCESS_DIAGNOSIS.md`
- **本地副本**：[`updates/20260417_update/reports/issue_114_FA3_PROCESS_DIAGNOSIS.md`](updates/20260417_update/reports/issue_114_FA3_PROCESS_DIAGNOSIS.md)
- **研究方向**：v1 诊断，以 fa3 失效为样本逐层反推研究流程系统性缺陷（被 3.4 v2 superseded）
- **核心结论**：作为 v2 的历史对照保留；v2 已修正 v1 的方向偏差（从"筛选无用因子"转向"帮 agent 找到有用因子"）

### 4. 相关 Project Issues

| # | 标题 | 状态 | 一句话（进展/结论） | 链接 |
|---|------|------|-------------------|------|
| #115 | Crypto 投研 meta-review 文档架构：四件套设计与迭代 | OPEN | 四件套设计定稿 + 本期首次 bootstrap 运行完成 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/115 |
| #114 | Crypto 投研方法论改进：小样本 IC 不可信 + fa3 评估流程漏洞归因 | OPEN | fa3 双层失效归因 v2 + 4 条 hard gate 产出 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/114 |
| #113 | crypto-deep-factor-research skill 框架级改进：预测目标意识 + 编码探索机制 | OPEN | 上游 skill 改动；#114 v2 新 gap 直接关联 SKILL.md 同步 FK/Studies | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/113 |
| #112 | [DISCUSSION] 研究工作流 Skill 统一管理仓库设计 | OPEN (ready-to-close) | 四件套承载仓库 `quant-workflows` 起源 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/112 |
| #111 | [DISCUSSION] 单人研究平台迭代的记录与协同流程设计 | OPEN (ready-to-close) | 与 #115 同层（平台记录协同），带 notification | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/111 |
| #110 | [FEATURE] Crypto Research MCP Server — 加密货币微观结构交互式研究工具 | OPEN | Phase 1/2 观察底座；fa3 Phase 1 深度不足部分归因于此 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/110 |

### 5. Target / 方法论变化

> 本期 target 与方法论无直接变化。记录 **待观察的 gap**（用户已确认后续单独迭代，本期不改 target 文件）：
> - `target_and_workflow.md` §1.6 已吸收 #113 "时序编码多样性"原则
> - **但** #114 v2 诊断指出 SKILL.md 文字仍未跟上 friction_knowledge_base + Studies #53-64 实践（non-blocking）
> - §2 Stage 5 "benchmark refresh 每 2-3 个新 FA 一次"规则：本次 bootstrap 相当于 refresh #0，下一轮在 FA4-FA5 落地后触发 #1

### 6. 本期观察到的模式 / 待关注方向

- **FA3 是第一个净负向 FA**：#114 v2 归因指向 single-factor IC 做 LGBM selector 不成立 + SKILL.md 迭代滞后。下一轮 deep-research 之前建议先做 skill 同步（用户已确认后续独立迭代）
- **Stage 5 benchmark refresh 尚未形成 repeatable 流程**：本次以 FI top100 手动决策充当 refresh #0，未走正式"合并新 FA → LGBM → Top N 选择"闭环。建议在 FA4 落地前参照 HFT `HFTPool/pool/benchmark0323/` 的 `run_benchmark.py`+`run_top100.py` 搭一份 crypto 侧 repeatable 脚本
- **回测链路脱节**：FI top100 SOTA 选型基于 Valid RankIC，但 §1.3 maker/taker Sharpe（北极星指标）本期 `_待填_` 暴露 pipeline gap。下一轮 meta-review 前建议先跑一次 `/crypto-signal-backtest`
- **FA3 保留但不入模型的长期策略**：114 fa3 因子已刷入 world_pool 供后续 regime-gated 研究对照，但不在默认特征集。若后续发现 fa3 子集在特定 regime 有价值，再局部引入
- **研究 session 产出与 FA 编译的节奏 gap**：#52-64 已积累 13 个待编译 session，按 Stage 2 规则（积攒 ≥3-6 个完成研究）已具备编译触发条件

### 7. 深度分析报告

> 本期未触发定向深度分析（Bootstrap 以聚合计数 + SOTA 决策为主）。后续如需定向分析可另 `/crypto-meta-review "<direction>"` 触发。
