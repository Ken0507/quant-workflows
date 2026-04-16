# Meta Review 2026-04-17

## 覆盖区间

- **since**: bootstrap（首次运行，全量扫描）
- 上次 update 编号: —
- 本次编号候选: **#1**（Bootstrap）
- 用户预设决策：
  - SOTA 模型 = **FI top100 (fa1+fa2, 100 features)**，模型路径 `/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/`
  - FA3 列入 §1.1 因子集清单（114 已落地因子），但**不**进入当前 SOTA 模型（issue #114 双层失效归因结论）
  - §1.3 回测结果 `_待填_`（用户稍后补）
  - 主 ad-hoc 报告 = `/home/cken/crypto_world/research/ic_fa123/REPORT.md` (2026-04-17)

## 扫描结果摘要

- 新增 session: 64（Bootstrap 全量）
- 新增 FA: 3（FA1 / FA2 / FA3）
- 新增 realize: 3（fa1 / fa2 / fa3，外加 baseline f001 / f002 / f001_f002_merged）
- 新增 analyzer run: 4 大类（`fa1` / `fa2` / `fa3` / `fa3_tuning_stage1`），其中 `fa3_tuning_stage1` 含 28 个子实验（stage1-stage2 系列 + FI top100/150 + corr71/151 等）
- 检测到 benchmark refresh: **否**（无 `benchmark_*` 目录）。按 Bootstrap 规则：**把 `fa3_tuning_stage1/fi_top100_mdil100k/` 视作 benchmark refresh #0**（用户选定）
- 候选 ad-hoc 报告: **7 份**（见下）
- 相关 GitHub issues 候选: 4 个高度相关 + 2 个跨 label 相关（见下）
- 新增 signal backtest 报告: **0**（`zebra/bt_output/` 存在但用户指示本期留 `_待填_`）

---

## 候选 research_updates 新条目

### [2026-04-17] Update #1（Bootstrap）

**时间区间**：Bootstrap（历史全量） → 2026-04-17
**子目录**：[`updates/20260417_update/`](updates/20260417_update/)

#### 1. 本期产出概览（聚合计数）

| 类别 | 新增 | 明细 |
|------|------|------|
| research session | 64 | `crypto_ob_research/1-*` ~ `64-*`（`10_zh` / `11_zh` 为翻译副本；`#23` 与 `#21` 同主题重复） |
| factor list (FA) | 3 | FA1（来源 #1-20）/ FA2（来源 #21-34）/ FA3（来源 #35-51） |
| realized pool | 3 | fa1 (123 因子) / fa2 (75 因子) / fa3 (114 因子) + baseline f001 (30) / f002 (39) / f001_f002_merged |
| analyzer run | 4 目录（含 28 个 tuning 子实验） | `fa1` / `fa2` / `fa3` / `fa3_tuning_stage1/{stage1,stage1b~g,stage2a~h,h100clip_R1~R7,h400rank_*,fair_*,corr*,fa12_plus_fa3_*,fi_top*}` |
| benchmark refresh | **是（#0，Bootstrap 视为基线）** | `/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/` |
| ad-hoc 课题报告 | 7 份候选 | 见 §3 |
| 相关 issue | 4-6 个 | 见 §4 |

#### 2. SOTA 提升量

> 本期为 **Bootstrap #1**，无上期对比。以下为首次 SOTA 基线（FI top100 模型）：

| 指标 | 本期值 | 备注 |
|------|--------|------|
| 已落地因子总数（§1.1 合计） | 381 | f001(30) + f002(39) + fa1(123) + fa2(75) + fa3(114) |
| SOTA 模型输入特征数 | 100 | FI top100 subset（从 fa1+fa2 198 特征按 LGBM gain 选 Top 100） |
| Train RankIC | 0.0635 | h100 clip, ret_lag0_next100 |
| **Valid RankIC** | **0.0427** | 42 天 valid (2025-12-16 ~ 2026-01-26) |
| gap (RankIC) | 0.0208 | — |
| trees | 80 | early stopping 未触发（full run） |
| 回测 Sharpe / MaxDD | **_待填_** | 用户稍后补 |

**SOTA 模型锚点**：
- 模型目录：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/`
- 模型文件：`lgbm_model.txt`
- 训练信息：`lgbm_train_info.json`
- 日 IC 序列：`lgbm_daily_ic.parquet`
- Top 特征（gain）：`fa1_stale_ema_logmax_50` (9.27%)、`fa2_big_interarrival` (6.76%)、`fa1_ewm_add_imbalance_60s` (4.16%)、`fa1_buy_sell_spread_proxy_ema20` (3.96%)、`fa2_big_share_ema60` (3.71%)

**为什么选 FI top100 而非 full 198**（用户决策）：
- Valid RankIC 差距仅 −0.0004（0.0427 vs 0.0431），统计上不显著
- 更窄的 feature 空间（100 vs 198）对下游 benchmark refresh loop 更友好，后续可定义稳定 Top N 清单
- 更小模型便于可解释性与生产部署

**为什么 FA3 不进 SOTA 模型**（用户决策 + #114 结论）：
- #114 归因 v2 确认 fa3 存在双层失效：26% 冗余（R²≥0.5 与 fa1+fa2 共线）+ 48% 正交无 alpha
- ic_fa123/REPORT.md §6.1 三次独立验证（+6 / +10 / +16 fa3 分别对应 valid RankIC −0.0006 / −0.0003 / −0.0002），全部负向
- 但 fa3 已完成工程落地（114 因子，batch run 已入库），保留在 §1.1 factor 池中供后续研究对照

#### 3. 收录的 ad-hoc 课题研究报告（候选，待用户勾选）

| # | 路径 | mtime | 所属 | 研究方向 | 核心结论（初判） |
|---|------|-------|------|---------|----------------|
| A | `/home/cken/crypto_world/research/ic_fa123/REPORT.md` | 2026-04-17 03:38 | 跨 fa1+fa2+fa3 | **IC-based factor selection vs LGBM gain-based selection（本期 SOTA 决策依据）** | 8 个实验，FI top100 Valid RankIC 0.0427（最接近 full 198 的 0.0431），fa3 分层添加全部 Valid RankIC 负向（−0.0002 ~ −0.0006），IC-corr 预筛劣于 LGBM gain |
| B | `zebra_pool/fa3/experiments/stage1/REPORT.md` | 2026-04-15 23:16 | fa3 | FA3 LGBM hyperparameter tuning 17 实验 | 最优配置 fa2+fa1 mdil=100k Valid RankIC 0.0431（SOTA baseline），fa3 净负向 |
| C | `zebra_pool/fa3/experiments/stage1/FA3_ATTRIBUTION_v2.md` | 2026-04-16 04:51 | fa3 | fa3 失效归因 v2（基于 R²-cut sweep + R²×IC 双 cut） | R3 (R²<0.2) +0.0006，但 R4-R7 沿 IC 轴精选反而单调退化；single-factor IC 轴否证 |
| D | `zebra_pool/fa3/experiments/stage1/issue_114_analysis/FA3_RESEARCH_METHODOLOGY_DIAGNOSIS_V2.md` | 2026-04-17 00:18 | methodology | 深读 5 个研究 log，定位 Phase 0-2 过程缺陷 | SKILL.md 文字未跟上 FK + Studies 53-64 实践的 gap |
| E | `zebra_pool/fa3/experiments/stage1/issue_114_analysis/CODEX_FA3_DISCOVERY_REPORT.md` | 2026-04-17 00:09 | methodology | Codex 独立复核 fa3 failure | 主因在 workflow/skill/methodology 层，非 Zebra 工程 |
| F | `zebra_pool/fa3/experiments/stage1/issue_114_analysis/FA3_PROCESS_DIAGNOSIS.md` | 2026-04-16 05:28 | methodology | v1 诊断（被 v2 superseded） | （可选）作为历史对照 |
| G | `zebra_pool/fa3/report/issue.md` | 2026-04-15 03:33 | fa3 analyzer | Step 3 analyzer 发现的口径问题（baseline 69 路径不存在等） | 工程口径 issue 记录 |

> 建议保留：A（必选，本期主报告）+ B（FA3 tuning 完整实验记录）+ C（归因 v2）+ D（方法论诊断 v2）+ E（Codex 独立复核）。F 可选（v1 superseded）、G 可选（工程 issue）。

#### 4. 相关 Project Issues（候选，待用户勾选）

**高度相关（project:quant_trading）**：

| # | 标题 | 状态 | 一句话 | 链接 |
|---|------|------|--------|------|
| #115 | Crypto 投研 meta-review 文档架构：四件套设计与迭代 | OPEN | 本期四件套设计定稿 + 本次首次 bootstrap 运行 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/115 |
| #114 | Crypto 投研方法论改进：小样本 IC 不可信 + fa3 评估流程漏洞归因 | OPEN | fa3 双层失效归因 v2 + 4 条 hard gate 产出 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/114 |
| #113 | crypto-deep-factor-research skill 框架级改进：预测目标意识 + 编码探索机制 | OPEN | 上游 skill 改动，#114 新 gap 直接关联 SKILL.md 对齐 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/113 |
| #110 | [FEATURE] Crypto Research MCP Server — 加密货币微观结构交互式研究工具 | OPEN | Phase 1/2 观察底座，fa3 Phase 1 深度不足部分归因于此 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/110 |

**跨 label 相关（discussion 但非 project:quant_trading，可选）**：

| # | 标题 | 状态 | 一句话 | 链接 |
|---|------|------|--------|------|
| #112 | [DISCUSSION] 研究工作流 Skill 统一管理仓库设计 | OPEN (ready-to-close) | 四件套承载仓库 `quant-workflows` 起源 | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/112 |
| #111 | [DISCUSSION] 单人研究平台迭代的记录与协同流程设计 | OPEN (ready-to-close) | 与 #115 同层（平台记录协同） | https://github.com/ligenjian001-ai/hft-sdk-issues/issues/111 |

#### 5. Target / 方法论变化

本期 target 与方法论无直接变化，但记录 **待观察的 gap**：
- `target_and_workflow.md` §1.6 已吸收 #113 "时序编码多样性"原则
- **但**按 #114 v2 诊断，SKILL.md 文字仍未跟上 friction_knowledge_base + Studies #53-64 实践（non-blocking，下一轮 meta-review 可深度分析）
- §2 Stage 5 benchmark refresh "每 2-3 个新 FA 一次"规则：**本次 bootstrap 相当于 refresh #0，下一轮在 FA4-FA5 落地后触发 #1**

#### 6. 本期观察到的模式 / 待关注方向

- **FA3 是第一个净负向 FA**：#114 归因指向研究过程缺陷（single-factor IC 做 LGBM selector 不成立）+ SKILL.md 迭代滞后。下一轮 deep-research 之前建议先做 skill 同步。
- **Stage 5 benchmark refresh 尚未形成 repeatable 流程**：本次 bootstrap 以 FI top100 手动决策充当 refresh #0，未走正式"合并新 FA → LGBM 训练 → Top N 选择"闭环。建议在 FA4 落地前补齐一个参照 HFT 的 `run_benchmark.py` / `run_top100.py` 脚本。
- **回测链路脱节**：当前 SOTA 选型基于 Valid RankIC，但 §1.3 回测（maker/taker Sharpe）是北极星指标，本期 `_待填_` 暴露 pipeline gap。下一轮 meta-review 前建议补齐 FI top100 的回测产出。

#### 7. 深度分析报告

本期未触发定向深度分析（Bootstrap 以聚合计数 + SOTA 决策为主）。用户可在本报告落盘后另外 `/crypto-meta-review "..."` 做定向分析。

---

## 候选 sota_snapshot 更新 diff

### Snapshot 元数据
- 本次 snapshot 日期：**2026-04-17**
- 上次 snapshot 日期：—（首次）
- 最后一次 benchmark refresh 日期：**2026-04-17**（Bootstrap #0）
- 研究 session 覆盖到：**#64**
- FA 覆盖到：**FA3**
- realize pool 覆盖到：**fa3**

### §1.1 因子集构成（diff）

| 因子集 | 因子数 | 工程状态 | 来源研究 | 进入 SOTA 模型？ |
|--------|--------|---------|---------|----------------|
| f001 (base30) | 30 | ✅ 已落地（Production） | baseline | 否（bar 元数据层） |
| f002 | 39 | ✅ 已落地（Production） | baseline | 否 |
| fa1 | 123 | ✅ 已落地（210 天 2025-07-01~2026-01-26） | #1-20 | **✅ 部分**（59 个入选 FI top100） |
| fa2 | 75 | ✅ 已落地（210 天 2025-07-01~2026-01-26） | #21-34 | **✅ 部分**（41 个入选 FI top100） |
| fa3 | 114 | ✅ 已落地（210 天 2025-07-01~2026-01-26） | #35-51 | ❌（#114 双层失效结论 + ic_fa123 三次独立验证 Valid RankIC 负向） |
| **合计（factor pool）** | **381** | — | — | — |
| **SOTA 模型输入数** | **100** | FI top100 from fa1+fa2 | — | — |

> 注：FI top100 按 LGBM gain importance 从 full fa1+fa2 (198) 选 Top 100。59 fa1 + 41 fa2 = 100，fa3 因净负向未纳入。

### §1.2 LGBM SOTA 指标（diff）

- Analyzer 报告路径：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/report.md`
- Benchmark 目录：`fa3_tuning_stage1/fi_top100_mdil100k/`（Bootstrap #0，视作第一版 benchmark）
- LGBM 模型路径：`/data/db/crypto/analyzer/fa3_tuning_stage1/fi_top100_mdil100k/lgbm_model.txt`
- Horizon: **next100 (h100)**（Amount bar，约 5 分钟）
- 信号模式: **clip 0.01**（|y| > 0.01 NaN，excl 20251010 + ETHUSDT/2025-08-29）
- Train/Valid 切分: 时间顺序 **168/42 天**（train 2025-07-01 ~ 2025-12-15 / valid 2025-12-16 ~ 2026-01-26）

| 指标 | Train | Valid |
|------|-------|-------|
| IC | 0.0719 | 0.0481 |
| RankIC | 0.0635 | **0.0427** |
| ICIR | _待自动提取_（`lgbm_daily_ic.parquet`） | _待自动提取_ |

> 单因子 Top 10 gain: `fa1_stale_ema_logmax_50` / `fa2_big_interarrival` / `fa1_ewm_add_imbalance_60s` / `fa1_buy_sell_spread_proxy_ema20` / `fa2_big_share_ema60` / `fa1_f12_cancel_dir_momentum_2v10` / `fa2_awsi_side_asym` / `fa1_depth_total_7` / `fa2_large_absorb_100` / `fa1_pen_abs_mean_raw`。完整排名见 analyzer report §7.2。

### §1.3 SOTA 回测结果（diff）

**本期保留 `_待填_`**（用户稍后补）。

- 交易模式 / 手续费 / 滑点 / 持仓约束 / 信号阈值：_待填_
- 完整回测报告路径：_待填_

> 参考可用历史回测：`/home/cken/crypto_world/zebra/bt_output/`（存在但对应 fa2_fa1 h100/h400 clip/rank 旧配置，非 FI top100）。本期用户指示暂不使用这些作为 SOTA 回测锚点。

### §2 研究管线累计状态（diff）

| 类别 | 累计数 | 备注 |
|------|--------|------|
| research session 总数 | 64 | `crypto_ob_research/1-*` ~ `64-*`（含 `10_zh`/`11_zh` 翻译 + `#23` 重复） |
| 完成 session（有 factor_definition.md） | _需 skill 精确统计_（估计 ≥ 50） | 记忆 7 天前 #1-22, #24 完成；#35-51 大部分供 FA3 |
| In-flight session（有 log 无 definition） | _需精确统计_ | |
| Failed / Interrupted session | _需精确统计_ | 记忆：#9 neg / #15 OOS fail / #18 stub / #23 dup |
| factor list (FA) 总数 | 3 | FA1 / FA2 / FA3 |
| realized pool 总数 | 3 | fa1 / fa2 / fa3 |
| benchmark refresh 次数 | **1**（Bootstrap #0） | 首次 |
| 待编译 session 数 | _估 ≥ 10_ | #52-64 未进入 FA |

### §3 开放研究方向 / 待关注模式（初版）

- **Benchmark refresh #1 触发条件**：待 FA4/FA5 落地（当前待编译 session #52-64）
- **FA3 净负向诊断闭环**：#114 产出 4 条 hard gate，下一轮 deep-research 前需把 SKILL.md 文字同步到 FK + Studies 53-64 实践
- **回测 pipeline gap**：FI top100 SOTA 模型未跑 maker/taker 回测，需补齐才能兑现北极星指标
- **Stage 5 repeatable 脚本缺失**：参考 HFT `HFTPool/pool/benchmark0323/` 的 `run_benchmark.py` + `run_top100.py`，为 crypto 侧搭建一份

---

## 观察到的问题 / 建议

- **SKILL.md 对齐 FK + Studies 53-64 实践**：这是 #114 v2 诊断的核心 gap，建议独立开一个 skill 迭代 session（非 meta-review 职责）
- **fi_top100 回测补齐**：SOTA 口径不闭环会让 §1.3 长期 `_待填_`
- **下一轮 meta-review 触发时机**：建议 FA4 落地 + FI top100 回测产出后（预计 2-4 周后）
- **F / G 报告（FA3_PROCESS_DIAGNOSIS.md / fa3/report/issue.md）**：建议不收录（v1 superseded + 工程口径 issue 属 skill 标准产出），但由用户决定
