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
