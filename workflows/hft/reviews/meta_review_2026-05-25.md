# HFT Meta Review 2026-05-25

## 覆盖区间

- `since`: **bootstrap**（首次运行，全量扫描）
- 上次 update 编号: —（无）
- 本次编号候选: **#1**
- 模式: **Bootstrap**

## 扫描结果摘要

- 总 research session 目录: **112**（distinct numbers = 110；#11 / #76 各有两个目录，#70 缺号）
- 已完成 session（有 factor_definition.md）: **107**
- 中断 session（无 factor_definition.md）: **4**（#2 fa17_part1, #14 unreasonable_orders, #47 order_lifecycle_deep, #107 bilateral_depth_signature）
- Phase gate verdict 分布（基于 105 个有 quality_review.md 的 session 末段文本扫描）: **CONDITIONAL 38 / PASS 31 / FAIL 6 / 其它 30**（未能解析的部分用 "其它" 兜底）
- 已编译 FA（factor_list.md）: **21**（FA6-12, FA15-28，跳号 13/14）
- 已 realize FA（pool/FA{N}/）: **12**（FA12, 15, 16, 20-28）
- 已编译但未独立 realize: **9**（FA6/7/8/9/10/11 已折叠进 baseline_150_new；FA17/18/19 未折叠路径待复核）
- 新 analyzer run: 全量扫描，FA28 merged_benchmark0323_top100/v1 是最新（2026-05-02）；FA26/FA27 的 merged analyzer 输出**符号链接已断**（`/data/db/hft/analyzer2/fa26/` 与 `fa27/` 不存在，模型 parquet 仅 FA28 一组保留）
- 检测到 benchmark refresh: **yes（仅 1 个）**——`pool/benchmark0323/`，但纯 SOTA 模型 `model_output/cken/benchmark0323/v1{,_top100}/` 已被清理（仅余 FA28-merged 的 v1）
- 候选 ad-hoc 报告: **39 份**（已扫描，按 mtime 倒序）
- 相关 GitHub issues 候选: **2 份 HFT 相关**（从 23 个 `project:quant_trading` issue 中过滤；详见 §4）
- 新增 signal backtest 报告: **0**（`HFTPool/backtest/` 不存在；`HFTPool/pool/FA*/backtest*/` 不存在；Layer 2 暂无产出）
- 编号健康报告:
  - 重复编号: #11 (`event_dominance` + `psychological_levels`)、#76 (`frequency_domain_heartbeat` + `lob_queue_survival`) — 4 个目录都有 factor_definition.md
  - 缺号: #70（无目录）
  - 中断（无 factor_definition.md）: #2, #14, #47, #107

---

## 候选 research_updates 新条目

（以下内容可直接用于 research_updates.md 替换 Initial State 占位段）

````markdown
## [2026-05-25] Update #1 — Bootstrap

**时间区间**：bootstrap → 2026-05-25
**子目录**：[`updates/20260525_update/`](updates/20260525_update/)

> Bootstrap 模式首次运行。SOTA 基线锚定为 **Refresh #0 = `pool/benchmark0323/`**（锁定 2025-03-23）。本期不存在"上期对比"，只追认当前状态并产出累计快照。

### 1. 本期产出概览（聚合计数）

| 类别 | 累计 | 明细 |
|------|-----:|------|
| research session（目录） | 112 | 编号 1-111；#11 / #76 重复，#70 缺号 |
| 已完成 session（有 factor_definition.md） | 107 | — |
| 中断 session（无 factor_definition.md） | 4 | #2 fa17_part1, #14 unreasonable_orders, #47 order_lifecycle_deep, #107 bilateral_depth_signature |
| factor list (FA) 已编译 | 21 | FA6-FA12, FA15-FA28（跳 13/14） |
| realized pool | 12 | FA12, FA15, FA16, FA20, FA21, FA22, FA23, FA24, FA25, FA26, FA27, FA28 |
| analyzer run | 多组 | benchmark0323/report + report_top100；FA*/report/analyzer2_*（部分 symlink 已断） |
| benchmark refresh | 1 | **Refresh #0 = `pool/benchmark0323/`**（2025-03-23 锁定） |
| ad-hoc 课题报告 | 39 候选 | 详见 §3，本期选 5 份核心收录（FA15/FA28 issue + FA15 量化 addendum） |
| signal backtest 报告 | 0 | `HFTPool/backtest/` 不存在；Layer 2 暂无产出 |
| 相关 issue | 2 | 见 §4 |

### 2. SOTA 提升量

> 首次 Bootstrap，无上期对比。本期为 **SOTA 基线（Refresh #0 = benchmark0323_top100）**。

**SOTA 模型锚点（实测）**：

- 报告：`HFTPool/pool/benchmark0323/report_top100/report.md`
- DATASETS_DEF: `baseline_150_new + FA12 + FA16 + FA20-FA25`（9 个 dataset，410 候选 → top100）
- 标准提交集：20250102-20250730（139 天）
- Train/Valid 切分：111 / 28 天（chronological 80/20）
- 样本数：n_train 81,763,385 / n_valid 23,030,246
- Universe: bond_sz 190 codes
- Sampling: bar 模式 + `bar_col=bar_aggtrans_time_1`
- 主 Label: `ret_lag0_next100`（horizon=100 bars, mid, within_session）
- LGBM cfg: lr 0.1 / num_leaves 32 / min_data_in_leaf 10000 / num_boost_round 50 / seed 20260323

**Layer 1 指标实测**（实测自 `report_top100/daily_ic.parquet`，100 个 top 因子）：

| 指标 | Train (111 天) | Valid (28 天) |
|------|------:|------:|
| 100 因子日均 cross-signal RankIC | 0.0101 | 0.0085 |
| 100% 正向日数 | 111/111 | 28/28 |
| 100 因子 \|valid RankIC\| 均值 / 中位 | — | 0.0224 / 0.0196 |
| 因子数 \|valid RankIC\| ≥ 0.03 / 0.04 / 0.05 | — | 32 / 18 / 7 |

⚠️ **纯 benchmark0323_top100 LGBM 模型文件已被清理**（`/data/db/hft/model_output/cken/benchmark0323/v1_top100/` 不存在），LGBM 层精确 IC / RankIC / RICIR / Top0.1% net bps 等指标仅存于 PNG 图（`report_top100/img/lgbm_*.png`）。最近可用代理：`model_output/fa28/fa28_merged_benchmark0323_top100/v1/`（含 100 SOTA + 56 FA28 = 156 features）train RankIC ≈ 0.1346 / valid RankIC ≈ 0.1193——**这含 FA28，非纯 SOTA**。

**Top 10 单因子（按 \|valid RankIC\|）**：

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

**累计待合并 FA 数**：**3-4 个**——FA26 / FA27 / FA28 已完成 post-Refresh #0 累积；FA15 可选回填评估。按 target_and_workflow.md §2 Stage R 规则（每 2-3 个新 FA 触发一次 refresh），**已具备触发 Refresh #1 的条件**。

### 3. 收录的 ad-hoc 课题研究报告

> Bootstrap 期共扫到 39 份候选，本期仅收录 5 份核心证据级报告——其它由 `pool/FA*/report/issue.md` 等就地维护、不冗余复制。
> 收录原则：（a）解释当前 SOTA 决策的关键复盘；（b）FA15 未入 benchmark0323 的归因证据；（c）FA28 工程迭代记录（最新 FA）。

#### 3.1 FA15 质量复盘补充量化证据（Codex Addendum）
- **原路径**：`HFTPool/pool/FA15/report/fa15_addendum_quant_evidence_codex_20260221.md`
- **本地副本**：[`updates/20260525_update/reports/fa15_addendum_quant_evidence_codex_20260221.md`](updates/20260525_update/reports/fa15_addendum_quant_evidence_codex_20260221.md)
- **研究方向**：为主报告补充可复现的量化证据，含分日 RankIC 统计、流动性分桶条件效应、E 组买侧因子方向反转分析
- **核心结论**：FA15 整体预测能力偏弱（35 因子 merged LGBM gain 1.75%），但 B 组（价格整数偏好）和 G 组（联合整数特征）在 h100+ horizon 上信号显著增强；E 组买侧因子方向与设计预期相反（t=-11.83）

#### 3.2 FA15 质量复盘与迭代计划（主报告）
- **原路径**：`HFTPool/pool/FA15/report/fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md`
- **本地副本**：[`updates/20260525_update/reports/fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md`](updates/20260525_update/reports/fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md)
- **研究方向**：FA15 整体诊断 + 后续改进 plan
- **核心结论**：FA15 因评估 horizon 不匹配 + 35 因子中 11 对高相关冗余 + 5/35 因子在 merged 模型中贡献 ≤ 1.75% gain，被判定为"CONDITIONAL pass，不进 benchmark"。**这是 FA15 未入 benchmark0323 的根因**

#### 3.3 FA15 Issue Log
- **原路径**：`HFTPool/pool/FA15/report/issue.md`
- **本地副本**：[`updates/20260525_update/reports/fa15_issue.md`](updates/20260525_update/reports/fa15_issue.md)
- **研究方向**：FA15 实现期遇到的 nice number 定义口径问题
- **核心结论**：根据权威规格（FA15_factor_list.md）确认实现口径无需修改；issue 已 closed

#### 3.4 FA28 Issue Log（最新 FA）
- **原路径**：`HFTPool/pool/FA28/report/issue.md`
- **本地副本**：[`updates/20260525_update/reports/fa28_issue.md`](updates/20260525_update/reports/fa28_issue.md)
- **研究方向**：FA28 工程迭代过程中的时区根因修复、负值处理、garbage md_id 清理
- **核心结论**：3 轮迭代修复后，FA28 工程交付完成（Iter-3 最新状态 2026-05-01）

#### 3.5 FA26 Known Issues
- **原路径**：`HFTPool/pool/FA26/report/issue.md`
- **本地副本**：[`updates/20260525_update/reports/fa26_issue.md`](updates/20260525_update/reports/fa26_issue.md)
- **研究方向**：FA26 已确认的因子冗余（tte_ofi_wide ↔ rgi_wide_std r=1.000）、稀疏度校准、R-class 占位符
- **核心结论**：5 个因子输出 0.0 的 R-class 草案因子标记为 known issue；其它正常落地

> 其它 34 份候选（factor_agent_execution_prompt_template_v2 系列、FA9_factor_list_v2、basic_table v2/v3 对比报告、各 FactorAgent issue 等）**不收录到本期 reports/**，因它们更接近"模板 / 历史中间态"而非"决策证据"。若用户希望追加，可手工拷贝到 `updates/20260525_update/reports/`。

### 4. 相关 Project Issues

> 从 `ligenjian001-ai/hft-sdk-issues` `project:quant_trading` label 中过滤 HFT 投研直接相关的两条。其它 21 个 issue（#67-#122 中绝大多数）属于 crypto 投研或非投研 infra/feature，不收录。

| # | 标题 | 状态 | 一句话（进展/结论） | 链接 |
|---|------|------|-------------------|------|
| #126 | [INFRA] HFT SDK 缺失 tick 级 L1-L10 book snapshot：阻塞 ob_research #101 的 4 个因子实施 | OPEN | ob_research #101 的 4 个深度因子依赖 L1-L10 tick snapshot，当前 SDK 不支持；阻塞实施 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/126 |
| #125 | hft-deep-factor-research: agent 在 Phase 2/3 用 second-grid r_N 代替主口径 bar-grid ret_lag0_next{H}（ob-95 观察） | OPEN | 流程 bug：agent 在 Phase 2/3 误用 second-grid 替代 bar-grid，导致主口径偏移；need skill fix | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/125 |

### 5. Target / 方法论变化

> 本期 target_and_workflow.md 刚由用户手工初始化（2026-05-25），无历史变更。

**已知方法论 gap（不修改 target，仅记录）**：

- issue #125 指出 agent 在 Phase 2/3 误用 second-grid 替代 bar-grid 主口径——这是 `hft-deep-factor-research` skill 的 bug，未来需修 skill 而非 target 文件
- issue #126 指出 SDK 层 L1-L10 tick snapshot 缺失阻塞 ob_research #101 的 4 个因子——这是 infra 限制，需 lgj 推进
- FA12 / FA21 / FA23 的命名前缀混乱（部分 FA 信号无 `fa{N}_` 前缀）——下一次 FA 编译前建议建立命名约束

### 6. 本期观察到的模式 / 待关注方向

1. **Refresh #1 触发条件已满足**：post-Refresh #0 累积 3 个 realized FA（FA26 82 因子 / FA27 33 因子 / FA28 56 因子，合计 171 个新因子），按 §2 Stage R "每 2-3 个新 FA" 规则该触发了。**建议下一步用 `/hft-benchmark-refresh` 启动 Refresh #1**

2. **FA15 是否要在 Refresh #1 中回填**：FA15 已 realize（35 因子）但被 benchmark0323 跳过。归因（见 §3.1 §3.2）是"merged 评估 gain 仅 1.75% + 评估 horizon 不匹配"，但其 B/G 组在 h100+ 上信号增强（next200 0.022-0.033）。Refresh #1 主 label 仍是 next100，FA15 在该 horizon 边际价值依然有限——**建议 Refresh #1 不强行回填 FA15，但可在 §3 开放方向标"如未来扩展到 next200 主口径，FA15 是首选回填候选"**

3. **LGBM 模型文件清理风险**：
   - 纯 benchmark0323_top100 的 LGBM model.txt 已不存在（清理日期未知）——LGBM 层 IC / RICIR / Top0.1% 等只能从 PNG 视觉读或重跑
   - FA26 / FA27 的 merged analyzer 输出也已被清理（symlink 断链）
   - **建议 Refresh #1 启动前先重跑一次 benchmark0323_top100 把 LGBM 指标的 parquet 保留下来作为锚定对照**（耗时 < 1 小时，cache 还在）
   - **保留策略**：未来 benchmark 的 `model_output/.../{v1,v1_topN}/` 目录禁止自动清理，或归档到 `pool/benchmark*/report_top100/saved_model/` 副本

4. **命名前缀混乱**：FA12 (`fa12_*`)、FA21 (`ac_*/buy_*/cancel_*/...`)、FA23 (`ed2_*/ga_*/...`) 命名风格不统一，导致"哪个 FA 贡献了哪些 top100 因子"的归因模糊。建议在 Refresh #1 之前做一次"前缀清理"实验（重命名 / 加 metadata），但不强求——只在 sota_snapshot §3 开放方向标记

5. **Session 编号清理**（低优先）：#11 / #76 都是"两个同号但内容不同的 session"（4 个目录都完成了 factor_definition.md），#70 缺号。**建议保持现状**，因为重新编号会破坏 git history 和已有 FA factor_list 中的 "来源研究" 引用；只在 sota_snapshot §3 标记为"已知历史遗留"

6. **中断 session**（4 个）：#2, #14, #47, #107——其中 #107 `bilateral_depth_signature` 是较新的，可能仍在 Phase 1。**建议低优先**，由用户决定继续 / 关停

7. **FA17 / FA18 / FA19 未独立 realize**：factor_list 已编译但 pool/FA17 等不存在。FA19 在 benchmark0323 全池中有 5 个 fa19_ 信号（折叠路径待复核）。**建议在 §3 开放方向追问**：这三个 FA 是否要走完整 realize 流程，或正式标记为废弃（如果其因子已被后续 FA 替代）

### 7. 深度分析报告

> 本期未触发定向深度分析（Bootstrap 以全量追认 + SOTA 基线锚定为主）。后续如需定向分析可另 `/hft-meta-review "<direction>"` 触发，例如：
> - `/hft-meta-review "Refresh #1 decision"` — 评估是否触发 Refresh #1 + 应包含哪些 FA
> - `/hft-meta-review "FA12 FA21 FA23 命名前缀清理"` — 命名归因实验
````

---

## 候选 sota_snapshot 更新 diff

> Bootstrap 模式下，`sota_snapshot.md` 已经由用户在 2026-05-25 手工初始化为基线。本 meta-review 检查后**建议在落盘前补充 3 处小修正**（其它字段维持不变）：

| 字段 | 原值 | 新值 | 依据 |
|---|---|---|---|
| **§1.1 FA15 来源研究** | 待补充 | 补充为 "ob_research 编号待补充（FA15 factor_list 元数据）" + 加注 `quality_review CONDITIONAL（merged gain 1.75%，evaluator horizon 不匹配）` | `pool/FA15/report/fa15_quality_review.md` §1.1 §1.2 |
| **§1.2 LGBM SOTA 指标缺失说明** | "需用户从 img 核对或重跑" | 补加 "**建议 Refresh #1 启动前先重跑 run_top100.py 把 parquet 形式 IC 保留**——cache 还在，耗时 < 1 小时" | 本 meta-review §6 第 3 条 |
| **§2 已落地 FA realize 总数** | "12 个" | **不变**，但在备注里展开 FA15 已 realize 但未入 SOTA、FA26-28 post-Refresh #0 未入 SOTA | 实测扫描确认 |
| **§3 开放研究方向** | 7 条 | **保留全部 7 条**，但优先级标注调整：第 1 条（Refresh #1）从"重要"上升到"立即触发" | 本 meta-review §6 第 1 条 |

> 其它字段（§1.1 表格、§1.2 单因子 IC top10、§2 累计管线状态等）**不变**——这些是用户在初始化时基于实测填的，与本 meta-review 扫描结果一致。

---

## 观察到的问题 / 建议（非落盘内容，仅供用户参考）

### 立即触发类

1. **Refresh #1 触发条件已满足**：FA26/27/28 累积 171 个新因子，请尽快用 `/hft-benchmark-refresh` 启动。建议参数：
   - 日期标签：`20260526` 或更晚
   - 数据集：默认（baseline_150_new + FA12 + FA16 + FA20-FA28）
   - Top N：100（与 benchmark0323 一致）
   - **启动前先重跑 `pool/benchmark0323/run_top100.py`** 保留纯 SOTA LGBM parquet 作为对照基线
2. **issue #125 / #126 是平台级阻塞**：建议追问 lgj 进度，特别是 #126 阻塞 ob_research #101 的 4 个因子实施

### 中期改进类

3. **LGBM 模型文件保留策略**：自动清理把 benchmark0323 / FA26 / FA27 的 model.txt 都清了——建议在 `hft-benchmark-refresh` skill 里加一条"产物归档"规则，或在 `/data/db/hft/model_output/` 顶层加 README 警告"禁止自动清理"
4. **FA12 / FA21 / FA23 命名前缀清理**：低优先但值得做，避免下次 Refresh 时再被归因模糊困扰

### 低优先类

5. **Session #11 / #76 重复 + #70 缺号**：维持现状，仅在 sota_snapshot §3 备注
6. **FA17 / FA18 / FA19 未独立 realize**：等用户决定是否走 realize 或标记废弃
7. **中断 session #2 / #14 / #47 / #107**：等用户决定

### Skill 自身改进观察

8. 本次 Bootstrap 运行良好。Skill SKILL.md 的扫描清单足够覆盖 HFT 现状，**唯一暴露的盲点是 LGBM 模型文件可能被清理**——下次 meta-review 时应主动验证 `model_output/.../{v1,v1_top100}/model.txt` 是否还在
9. issue #126 / #125 这种 "HFT vs crypto" 混在同一 repo 的过滤逻辑可以再清晰一些（当前依赖关键词手工过滤 23 → 2，建议未来加 label `project:hft_quant_trading` 与 `project:crypto_quant_trading` 区分）
