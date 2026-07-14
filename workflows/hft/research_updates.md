# HFT 投研进度更新日志

> **用途**：时间序列 changelog，记录每次 meta-review 之间的投研增量。**Append-only**，新条目追加到文件**顶部**（最新在上）。
>
> **范围**：与 `sota_snapshot.md` 一致，严格只追踪 Layer 1（LGBM 信号质量）相关的因子研究增量。Layer 2 / Layer 3 演进各自独立追踪。
>
> **结构**：两层。本文件是索引 + 每期中等篇幅总结；每期的 ad-hoc 课题报告副本 + 可选深度分析放在 `updates/{yyyymmdd}_update/` 子目录。
>
> **维护方式**：由 `/aef-hft-meta-review` skill 在用户确认后追加新条目 + 创建对应子目录。**agent 不得修改历史条目**，只能追加新条目和补充当前期子目录。

---

## 目录结构约定

```
workflows/hft/
├── research_updates.md             # 本文件：索引 + 每期摘要
└── updates/
    ├── 20260601_update/             （示例）
    │   ├── reports/                # 本期收录的 ad-hoc 课题研究报告副本
    │   │   ├── benchmark_refresh1_decision_REPORT.md
    │   │   └── ...
    │   └── summary.md              # 可选：本期定向深度分析报告
    ├── 20260801_update/
    │   └── ...
```

### 收录规则

| 内容 | 处理方式 | 理由 |
|------|---------|------|
| **ad-hoc 课题研究报告** | 完整复制一份到 `reports/` | 这类是非固定流程产出（如 FA 失效归因、方法论实验、专项实验报告、benchmark refresh 决策报告），值得冻结快照。原路径也要记录以便追溯 |
| Skill 固定产出（ob research_report / FA factor_list / pool/FA*/report / analyzer2_*report / backtest 报告） | **不收录**，仅在本文件以聚合计数方式提及（如"本期新增 ob #112-115 / 新增 FA29 / 刷了 FA29 全历史"） | 这些由对应 skill 在自己的工作目录里维护，数量多且位置稳定，无需冗余复制 |
| **Project-related GitHub issues** | 不做本地快照，只在本文件用 "#编号 + 标题 + 一句话 + 链接" 列出 | 跟 GitHub 上游永远一致，省去同步成本 |
| **Benchmark refresh 决策报告** | 完整复制到 reports/ | 这是 Refresh #N 的核心证据，必须冻结 |
| **本期深度分析** | 写入 `summary.md` | 可选——质量分析当前为可选项，非每期必做 |

### Ad-hoc 报告判定

"ad-hoc 课题报告" 指用户临时开题做的深度分析或实验，典型特征：

- 不是某个 skill 的标准产出
- 文件名通常是 `REPORT.md` / `analysis.md` / `failure_analysis.md` 这类临时命名
- 通常放在 `pool/FA*/experiments/` 或 `pool/FA*/analysis*/` 或 `ob_research/*/experiments/` 之外的临时路径
- 例子：`HFTPool/pool/FA15/report/fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md`

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
| research session | X 个 | #112, #113, #114（完成 X / 中断 Y / FAIL Z） |
| factor list (FA) | X 个 | FA29（来源 #89-111） |
| realized pool | X 个 | FA29 |
| analyzer run | X 个 | fa29_factor_v1, fa29_merged_benchmark0323_top100 |
| benchmark refresh | 是/否 | 新 benchmark: `HFTPool/pool/benchmark{date}/` |
| ad-hoc 课题报告 | X 份 | 见 §3 |
| signal backtest 报告 | X 份 | 见 §3 或 (聚合提及, 路径在 HFTPool/backtest/) |
| 相关 issue | X 个 | 见 §4 |

### 2. SOTA 提升量

**若本期有 benchmark refresh**：

| 指标 | 上期 (Refresh #N-1) | 本期 (Refresh #N) | 变化 |
|------|------:|------:|------|
| 模型路径 | `pool/benchmark{old_date}/report_top100/` | `pool/benchmark{new_date}/report_top100/` | — |
| Factor Pool 合计 | X | Y | +Z |
| SOTA 模型输入数 | 100 | 100 | — |
| LGBM Valid RankIC | X | Y | +Z |
| LGBM Train RankIC | X | Y | +Z |
| Gap (Train - Valid) | X | Y | 缩小/扩大 |
| Valid Top0.1% net (bps) | X | Y | +Z |
| Top 10 features 变化 | | | 新进 X 个 / 淘汰 Y 个 |

**若本期未触发 benchmark refresh**：

> 本期未触发 benchmark refresh。SOTA 基准仍为 `benchmark{old_date}_top100`，Layer 1 指标无增量。
> 累计待合并 FA 数：X（target_and_workflow.md §2 Stage R 建议每 2-3 个新 FA 触发一次 refresh）

### 3. 收录的 ad-hoc 课题研究报告

> 本节仅列 ad-hoc 课题型报告，不列 skill 固定产出的标准报告。
> 每份报告已完整复制到 `updates/{yyyymmdd}_update/reports/`。

#### 3.1 {报告标题}
- **原路径**：`HFTPool/pool/FA*/experiments/.../REPORT.md`
- **本地副本**：[`updates/{yyyymmdd}_update/reports/fa{N}_xxx_REPORT.md`](updates/{yyyymmdd}_update/reports/fa{N}_xxx_REPORT.md)
- **研究方向**：{一句话描述该报告研究的问题或方向}
- **核心结论**：{1-3 句话摘要}

#### 3.2 ...

**若本期无 ad-hoc 报告**：

> 本期无 ad-hoc 课题报告。

### 4. 相关 Project Issues

> 自动扫自 `ligenjian001-ai/hft-sdk-issues` 项目，筛选条件：label 含 `project:quant_trading` 且
> 本期内有更新。最终收录由用户在 meta-review 确认环节勾选。

| # | 标题 | 状态 | 一句话（进展/结论） | 链接 |
|---|------|------|-------------------|------|

**若本期无相关 issue**：

> 本期内无 `project:quant_trading` issue 更新。

### 5. Target / 方法论变化

- [ ] target_and_workflow.md §1 是否调整？调整内容：...
- [ ] 方法论原则是否有更新？...
- [ ] 数据墙红线是否有变？...

**若无变化**：

> 本期 target 与方法论无变化。

### 6. 本期观察到的模式 / 待关注方向

- {反复出现的问题 / blocker，如适用}
- {值得下一期关注的方向}
- {skill 本身需要改进的地方}
- {是否建议触发 Stage R benchmark refresh}

### 7. 深度分析报告

**若本期做了定向深度分析**：
- 完整分析：[`updates/{yyyymmdd}_update/summary.md`](updates/{yyyymmdd}_update/summary.md)
- 分析聚焦：{如 "FA15 历史遗留归因" / "post-Refresh #0 FA 命名前缀清理" / ...}
- 关键发现：{3-5 句话摘要}

**若本期未做**：

> 本期未触发定向深度分析（当前为可选项）。
````

---

<!-- meta-review skill 在此行下方追加新条目，保持最新在上 -->

## [2026-05-25] Update #1 — Bootstrap

**时间区间**：bootstrap → 2026-05-25
**子目录**：[`updates/20260525_update/`](updates/20260525_update/)

> Bootstrap 模式首次运行。SOTA 基线锚定为 **Refresh #0 = `pool/benchmark0323/`**（锁定 2025-03-23）。本期不存在"上期对比"，只追认当前状态并产出累计快照。
>
> **本期闭环了三件历史遗留**：
> 1. **FA15 未入 benchmark0323 的归因找到了**：quality_review CONDITIONAL，merged LGBM gain 仅 1.75%，evaluator h20 不匹配（因子主优势在 h100+）
> 2. **纯 benchmark0323_top100 LGBM 模型文件已重跑恢复**：原 `/data/db/hft/model_output/cken/benchmark0323/v1_top100/` 被清理；本期 2026-05-25 重跑产出 `model.txt` + `lgbm_daily_ic_{train,valid}.parquet` + `feature_importance_gain.parquet`，**物理副本** 存于 `HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/`
> 3. **数据持久化策略已固化进 skill**：更新 `hft-analyzer2-standard-report` + `hft-benchmark-refresh` skill SKILL.md，强制所有报告 + 模型 + IC parquet 用 `cp -L` 物理拷贝到 HFTPool，禁止 symlink，豁免 cache/memmap

### 1. 本期产出概览（聚合计数）

| 类别 | 累计 | 明细 |
|------|-----:|------|
| research session（目录） | 112 | 编号 1-111；#11 / #76 重复，#70 缺号 |
| 已完成 session（有 factor_definition.md） | 107 | — |
| 中断 session（无 factor_definition.md） | 4 | #2 fa17_part1, #14 unreasonable_orders, #47 order_lifecycle_deep, #107 bilateral_depth_signature |
| factor list (FA) 已编译 | 21 | FA6-FA12, FA15-FA28（跳 13/14） |
| realized pool | 12 | FA12, FA15, FA16, FA20, FA21, FA22, FA23, FA24, FA25, FA26, FA27, FA28 |
| analyzer run | 多组 | benchmark0323/report + report_top100；FA*/report/analyzer2_*（FA26/27 symlink 已断；FA28 起改物理拷贝） |
| **本期重跑（remediation）** | **1** | benchmark0323_top100 LGBM 重跑（恢复丢失模型文件）；产出 `HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/` |
| benchmark refresh | 1 | **Refresh #0 = `pool/benchmark0323/`**（2025-03-23 锁定） |
| ad-hoc 课题报告 | 55 份 | 全部物理复制到 `updates/20260525_update/reports/`（见 §3） |
| signal backtest 报告 | 0 | `HFTPool/backtest/` 不存在；Layer 2 暂无产出 |
| 相关 issue | 2 | 见 §4 |

### 2. SOTA 提升量

> 首次 Bootstrap，无上期对比。本期为 **SOTA 基线（Refresh #0 = benchmark0323_top100）**。

**SOTA 模型锚点（实测自 2026-05-25 重跑产出）**：

| 项 | 值 |
|---|---|
| 报告路径 | `HFTPool/pool/benchmark0323/report_top100/report.md` |
| 模型路径（物理副本） | `HFTPool/pool/benchmark0323/saved_model/v1_top100_rerun_20260525/model.txt` |
| DATASETS_DEF | `baseline_150_new + FA12 + FA16 + FA20-FA25`（9 个 dataset，410 候选 → top100） |
| 标准提交集 | 20250102-20250730（139 天） |
| Train/Valid 切分 | 111 / 28 天（chronological 80/20） |
| 样本数 | n_train 81,763,385 / n_valid 23,030,246 |
| Universe | bond_sz 190 codes |
| Sampling | bar 模式 + `bar_col=bar_aggtrans_time_1` |
| 主 Label | `ret_lag0_next100`（horizon=100 bars, mid, within_session） |
| LGBM cfg | lr 0.1 / num_leaves 32 / min_data_in_leaf 10000 / num_boost_round 50 / seed 20260323 |

**Layer 1 关键指标**：

| 指标 | Train (111d) | Valid (28d) | All (139d) |
|------|------:|------:|------:|
| LGBM daily IC mean | 0.1437 | **0.1327** | 0.1415 |
| LGBM daily RankIC mean | 0.1225 | **0.1123** | 0.1204 |
| LGBM daily RankIC std | 0.0159 | 0.0116 | 0.0157 |
| RankIC IR (mean/std) | 7.70 | **9.68** | 7.69 |
| Train/Valid Gap (RankIC) | — | **0.0102** | — |
| Days with positive RankIC | 100% (111/111) | **100% (28/28)** | 100% |

**Top0.1% mean return @ h100**：Train ~26.7 bps / Valid **~25.8 bps**
**Top0.01% net group return**：Train ~25.5 bps / Valid **~30.7 bps**

**Top 10 LGBM features (gain ratio)**：

| 排名 | 特征 | gain_ratio |
|---:|---|---:|
| 1 | fa20_session_position | **13.66%** |
| 2 | a1r2_r2_slope_imb_norm_ema_diff | 10.00% |
| 3 | pfi38_fast | 4.96% |
| 4 | a3_a3_add_flow_imb_ema_fast | 4.02% |
| 5 | bps36_cancel_churn_gradient | 3.43% |
| 6 | pfi38_slow | 3.38% |
| 7 | a2b_sig_mom_fast_bps | 3.08% |
| 8 | a1b_rvol_fast_bps | 2.39% |
| 9 | a3_a3_mid_ret_ema_fast | 2.24% |
| 10 | fa7_micro_queue_gap_bps_3 | 2.20% |

**累计待合并 FA 数**：**3 个**——FA26 (82) / FA27 (33) / FA28 (56) = 171 个新因子，已 post-Refresh #0 累积。按 target_and_workflow.md §2 Stage R 规则（每 2-3 个新 FA 触发一次 refresh），**已具备触发 Refresh #1 的条件**（见 §6 第 1 条）。

### 3. 收录的 ad-hoc 课题研究报告

> Bootstrap 期共扫到 55 份 ad-hoc 候选（已应用严格过滤排除 skill 标准产出 + analyzer report + factor_list/review/prompt/task 等）。**全部 55 份**已物理复制到 `updates/20260525_update/reports/`，文件名带源前缀（`fa28__issue.md` 等）防冲突。

**关键 5 份核心证据级报告**（解释 SOTA 决策与历史遗留）：

#### 3.1 FA15 质量复盘补充量化证据（Codex Addendum）
- **原路径**：`HFTPool/pool/FA15/report/fa15_addendum_quant_evidence_codex_20260221.md`
- **本地副本**：[`updates/20260525_update/reports/fa15__fa15_addendum_quant_evidence_codex_20260221.md`](updates/20260525_update/reports/fa15__fa15_addendum_quant_evidence_codex_20260221.md)
- **研究方向**：分日 RankIC 统计、流动性分桶条件效应、E 组买侧因子方向反转分析
- **核心结论**：FA15 整体预测能力偏弱（merged LGBM gain 1.75%），但 B 组/G 组在 h100+ horizon 显著增强；E 组买侧因子方向反转（t=-11.83）

#### 3.2 FA15 质量复盘与迭代计划（主报告）
- **原路径**：`HFTPool/pool/FA15/report/fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md`
- **本地副本**：[`updates/20260525_update/reports/fa15__fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md`](updates/20260525_update/reports/fa15__fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md)
- **核心结论**：FA15 因评估 horizon 不匹配 + 35 因子中 11 对高相关冗余 + 5/35 因子在 merged 模型中贡献 ≤ 1.75%，**判定 CONDITIONAL pass，不进 benchmark0323**

#### 3.3 friction_knowledge_base.md（最新跨 FA 学习沉淀）
- **原路径**：`HFTPool/factor_agent_docs/friction_knowledge_base.md`（2026-04-29）
- **本地副本**：[`updates/20260525_update/reports/fadocs__friction_knowledge_base.md`](updates/20260525_update/reports/fadocs__friction_knowledge_base.md)
- **研究方向**：跨 FA 的研究流程摩擦点 + 经验教训累积
- **核心意义**：作为下一轮 deep-research 的入门知识；与 issue #125 标记的 "agent 主口径误用" 议题相关

#### 3.4 FA28 Issue Log（最新 FA 工程迭代记录）
- **原路径**：`HFTPool/pool/FA28/report/issue.md`
- **本地副本**：[`updates/20260525_update/reports/fa28__issue.md`](updates/20260525_update/reports/fa28__issue.md)
- **研究方向**：FA28 工程迭代过程中的时区根因修复、负值处理、garbage md_id 清理
- **核心结论**：3 轮迭代修复后，FA28 工程交付完成（Iter-3 最新状态 2026-05-01）；FA28 是第一个走"物理复制 / 禁止 symlink"新规的 FA

#### 3.5 axis_alignment_analysis_20260123 + workflow_review_report_20260123
- **原路径**：`HFTPool/factor_agent_docs/{axis_alignment_analysis_20260123.md, workflow_review_report_20260123.md, TASK_fix_basic_table_axis_alignment.md}`
- **本地副本**：见 `updates/20260525_update/reports/fadocs__*.md`
- **研究方向**：2026-01-23 一次 basic_table 轴对齐危机的完整记录 + 流程级 review
- **核心意义**：是 hft-axis-alignment-check skill 的起源；后续所有 FA 都把 axis_ratio ≥ 99.9% 作为硬性 gate

> 其余 50 份（各 FA / FactorAgent 的 issue.md / data_validation_*.md / basic_table v0-v3 对比报告 / batch2-3 conversation logs / FA9_factor_list_v2 / factor_agent_execution_prompt_template_v2 系列等）作为历史档案备份，留存供后续追溯，不在本节展开。

### 4. 相关 Project Issues

> 从 `ligenjian001-ai/hft-sdk-issues` `project:quant_trading` label 中过滤 HFT 投研直接相关的 2 条。其余 21 个 `project:quant_trading` issue（#67-#122 中绝大多数）属于 crypto 投研或非投研 infra/feature，不收录。

| # | 标题 | 状态 | 一句话（进展/结论） | 链接 |
|---|------|------|-------------------|------|
| #126 | [INFRA] HFT SDK 缺失 tick 级 L1-L10 book snapshot：阻塞 ob_research #101 的 4 个因子实施 | OPEN | ob_research #101 的 4 个深度因子依赖 L1-L10 tick snapshot，当前 SDK 不支持；阻塞实施，需 lgj 推进 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/126 |
| #125 | hft-deep-factor-research: agent 在 Phase 2/3 用 second-grid r_N 代替主口径 bar-grid ret_lag0_next{H}（ob-95 观察） | OPEN | 流程 bug：agent 在 Phase 2/3 误用 second-grid 替代 bar-grid，导致主口径偏移；需修 skill | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/125 |

### 5. Target / 方法论变化

> 本期 target_and_workflow.md 刚由用户手工初始化（2026-05-25），无历史变更。

**本期已落地的 skill 改进**：

- `hft-analyzer2-standard-report` SKILL.md：新增 **"持久化产出"段**——所有报告核心文件 + LGBM 模型 + IC parquet 必须用 `cp -L` 物理拷贝到 HFTPool 下，禁止 symlink；豁免 cache/ 和 memmap/。**理由**：2026-04-23 `/data/db/hft/analyzer2/` 清理导致 FA20-FA27 的 16 个软链报告 dangling；2026 年某次 `/data/db/hft/model_output/` 清理导致 benchmark0323 model.txt 丢失
- `hft-benchmark-refresh` SKILL.md（本期新建）：内置 **Step 6 物理拷贝规则**——LGBM 模型 + IC parquet + feature_importance + metadata.json 必须落到 `HFTPool/pool/benchmark{date}/saved_model/v1{,_top100}/`；验证 `find saved_model -type l` 必须返回空

**已知但本期不修的方法论 gap**：

- issue #125 指出 agent 在 Phase 2/3 误用 second-grid 替代 bar-grid 主口径——这是 `hft-deep-factor-research` skill 的 bug，未来需修 skill 而非 target 文件
- issue #126 指出 SDK 层 L1-L10 tick snapshot 缺失阻塞 ob_research #101——这是 infra 限制，需 lgj 推进
- FA12 / FA21 / FA23 命名前缀混乱——建议在 Refresh #1 之前建立命名约束

### 6. 本期观察到的模式 / 待关注方向

1. **Refresh #1 触发条件已满足，立即触发**：累计 171 个 post-Refresh #0 新因子（FA26/27/28），建议下一步直接跑 `/aef-hft-benchmark-refresh` 启动。**Refresh #1 必须**：
   - 沿用 benchmark0323 的 LGBM cfg 严格可比
   - 默认 Top 100（与 0323 一致）
   - 使用 saved_model 物理拷贝规则（新 skill 强制）
   - 是否纳入 FA15 重评：本期建议**纳入**，因为现在主口径已是 next100（与 FA15 优势 horizon 一致）

2. **下一轮 deep-research 的对标基线 已锁定**：
   - LGBM 层目标：valid daily RankIC mean **0.1123**、Top0.1% net (h100) **25.8 bps**、Top0.01% net **30.7 bps**
   - 新 SOTA 必须显著超越这三个数（不只是 RankIC 单一数字）
   - 单因子层：进 Top 50 需 \|valid RankIC\| ≥ 0.03

3. **数据持久化规则已闭环**（本期）：
   - skill 已强制物理拷贝
   - benchmark0323 的丢失模型文件已重跑恢复并物理保存
   - 未来 Refresh #1+ 不会再次踩这个坑

4. **FA15 历史遗留已澄清**：归因 = CONDITIONAL pass（gain 1.75% + horizon 不匹配）。**建议在 Refresh #1 中评估是否纳入**——主 label 已切到 next100，与 FA15 优势 horizon 一致，可能改善

5. **命名前缀混乱（FA12/21/23）**：低优先但需要在 Refresh #1 之前清理。**重跑期间发现 FA12 factor_pool 已不在 disk**（仅 cache 残留列），这增加了清理复杂度——建议先弄清楚 FA12 的源数据是否还能找回

6. **Session #11/#76 重复 + #70 缺号**：维持现状（重新编号会破坏 git history 和 factor_list 引用）

### 7. 深度分析报告

> 本期未触发定向深度分析（Bootstrap 以全量追认 + SOTA 基线锚定 + LGBM 重跑修复为主）。
>
> 后续如需定向分析可另 `/aef-hft-meta-review "<direction>"` 触发，例如：
> - `/aef-hft-meta-review "Refresh #1 decision"` — 评估是否触发 Refresh #1 + 应包含哪些 FA
> - `/aef-hft-meta-review "FA12 FA21 FA23 命名前缀清理"` — 命名归因实验
> - `/aef-hft-meta-review "ob_research 编号清理"` — 重复/缺号 session 处理建议
