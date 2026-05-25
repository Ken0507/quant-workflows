---
name: hft-meta-review
description: "周期性对 HFT 投研工作做 meta review：读取 target_and_workflow / sota_snapshot / research_updates 三份基础文档，在可预测路径（HFTPool/ob_research / factor_agent_docs / pool / /data/db/hft/analyzer2 / model_output）下扫描自上次 update 以来的新增产出，生成阶段性总结并询问用户是否更新 sota_snapshot 和 research_updates。支持可选 direction 参数做定向深度分析。范围严格限定在 Layer 1（LGBM 信号质量），不维护 Layer 2 回测与 Layer 3 实盘。"
metadata:
  short-description: "定期 meta-review HFT 投研产出，生成阶段总结并更新 sota + updates（Layer 1 only）"
  argument-hint: "[direction | since-date] (可选)"
---

# HFT 投研 Meta Review

> 本 Skill 是整个 HFT 可转债高频投研工作的**自省层**。它不做新研究、不写代码，只做三件事：
> 1. **读**：吃进 `target_and_workflow.md` / `sota_snapshot.md` / `research_updates.md`
> 2. **扫**：在可预测路径下扫描自 `since` 以来的 delta（session / FA / realize / analyzer / benchmark refresh / ad-hoc 课题报告 / 相关 GitHub issues / signal backtest 报告）
> 3. **总结 + 问**：按 `research_updates.md` 条目模板产出结构化总结 → 询问用户是否落盘
>
> **范围红线**：本 skill 只追踪 **Layer 1（LGBM 信号质量）**。Layer 2（SignalReplay 回测）与 Layer 3（实盘 PnL）的 SOTA 演进各自独立追踪，本 skill 不写入 sota_snapshot。如果用户要追踪 Layer 2/3，应先在 target_and_workflow.md 扩展 SOTA 范围声明。
>
> 定向深度分析（blocking 模式 / 流程缺陷 / 方向 gap 等）当前为**可选**分支，只在用户显式传入 direction 时执行。

---

## 0. 参数解析

**调用形式**：
- `/hft-meta-review` — 无参数，默认 `since` = research_updates.md 最上面一条的日期
- `/hft-meta-review 2026-03-01` — 从指定日期开始（匹配 `YYYY-MM-DD` 正则）
- `/hft-meta-review "focus on post-refresh FA accumulation"` — 带定向方向文本

**解析逻辑**：
1. 参数像 `YYYY-MM-DD` → 作为 `since`
2. 否则 → 作为 `direction`，`since` 按 research_updates 顶部条目取
3. research_updates 仍是 Initial State 占位（未跑过） → 进入 **Bootstrap 首次运行流程**（见 §1.0）

---

## 1. 固定流程（每次运行都执行）

### Step 0: Bootstrap 首次运行检测

读取 `research_updates.md`。如果文件内容包含 `## [待首次 meta-review 运行] Initial State` 占位段，则进入 **Bootstrap 模式**：

- `since = "bootstrap"`（全量扫描所有路径）
- sota_snapshot 已经由用户手工初始化（基于 `HFTPool/pool/benchmark0323/`），**视为 benchmark refresh #0**
- sota_snapshot 元数据 "最后一次 benchmark refresh 日期" = 2025-03-23（benchmark0323 锁定日，**不**改为今日）
- Step 3 生成的条目是 **Update #1**；Step 5 落盘时**替换**掉 Initial State 占位段（不是追加在其上方）
- Update #1 的 §2 SOTA 提升量段写"首次 bootstrap，无上期对比，本期为 SOTA 基线（Refresh #0 = benchmark0323_top100）"

非 Bootstrap 模式则按 Step 1 正常流程。

### Step 1: 读三份基础文档

**强制完整阅读**（不得凭记忆）：

```
/home/cken/crypto_world/quant-workflows/workflows/hft/target_and_workflow.md
/home/cken/crypto_world/quant-workflows/workflows/hft/sota_snapshot.md
/home/cken/crypto_world/quant-workflows/workflows/hft/research_updates.md
```

从三份文档提取到工作笔记：

- 从 target_and_workflow：研究流程全貌、当前数据资产、方法论原则、状态追踪单位定义、Stage R benchmark refresh 触发规则、**SOTA 范围红线（只到 Layer 1）**
- 从 sota_snapshot：当前 SOTA 因子集构成、LGBM 指标、累计管线状态、最后一次 benchmark refresh 日期、元数据中的最大编号（session/FA/realize）
- 从 research_updates：上次 update 日期（`since`）、上次 update 时的 session/FA/realize 最大编号（用于 delta 起点）

### Step 2: 扫描 delta

**扫描范围严格限定在以下可预测路径**，不做 hft_projects 全盘扫描：

```
/home/cken/hft_projects/HFTPool/ob_research/        — deep factor research session
/home/cken/hft_projects/HFTPool/factor_agent_docs/  — FA 因子集文档
/home/cken/hft_projects/HFTPool/pool/               — realize 工程 + ad-hoc 实验报告 + benchmark{YYYYMMDD}/
/home/cken/hft_projects/HFTPool/backtest/           — signal backtest 报告（如存在）
/data/db/hft/analyzer2/                             — Analyzer2 LGBM 报告
/data/db/hft/model_output/                          — LGBM 模型 + memmap + IC parquet
/data/db/hft/factor_pool/                           — 已落地因子 parquet
```

以下 9 个子扫描**可派 SubAgent 并行**（主进程只做汇总）：

#### 2.1 Research session delta

路径：`/home/cken/hft_projects/HFTPool/ob_research/{N}-{topic}/`

筛选：目录编号 > 上次 update 的 session 最大编号 **或** 其 `research_log.md` mtime > `since`

每个新 session 收集：
- 编号 + topic
- 是否存在 `factor_definition.md`（决定完成/未完成/中断状态）
- `research_report.md` §5 最终因子数量（如可解析）
- `quality_review.md` 最终 Phase gate 状态（PASS / CONDITIONAL / FAIL / INTERRUPTED）
- 核心发现摘要（从 research_report.md §0-§1 提取 2-3 句）

**HFT 特有的编号清理**：扫描完毕后，附带产出"编号健康报告"：
- 重复编号目录列表（如 #11 / #76）
- 缺号列表（如 #70）
- 中断 session 列表

仅当用户在 Step 4 显式要求时把这些写进 §3 ad-hoc 收录。

#### 2.2 FA 因子集 delta

路径：`/home/cken/hft_projects/HFTPool/factor_agent_docs/FA*_factor_list.md`

筛选：FA 编号 > 上次 update 的 FA 最大编号

每个新 FA 收集：
- FA 编号 + 来源研究编号列表（从 §0 概述 / "来源研究" 段提取）
- 因子总数（从 factor_list.md §6 因子完整清单 / §0 总表提取；备份方案：从对应 realize 后的 parquet schema 实读）
- 是否存在 `FA{N}_warning_factors.md` 或同类合规分级文件（如有）
- 是否已被 realize（查 `HFTPool/pool/FA{N}/` 是否存在）
- 是否存在 `FA{N}_prompt.md` / `FA{N}_task.md`

**HFT 特有**：注意 FA 编号有历史跳号（13、14 不存在）和命名前缀混乱（FA12/21/23）。新 FA 出现时检查是否沿用 `fa{N}_` 前缀，无前缀时在 §3 §6 提示。

#### 2.3 Realize pool delta

路径：`/home/cken/hft_projects/HFTPool/pool/FA*/`

筛选：FA 编号 > 上次 update 的 realize 最大编号 **或** `report/` 下有 mtime > `since` 的新文件

每个新 pool 收集：
- FA 编号
- 工程状态（smoke_test / 1m 验证 / 全历史刷数 / analyzer 报告齐全）— 从 `report/research_log.md` 和 `code/build/` 目录内容判断
- 实际落地因子数 vs factor_list 定义数（对比）—— factor 数从 `/data/db/hft/factor_pool/debug/fa{N}/fa{N}_factor_v1/{first_date}/fa{N}_factor/fa{N}_factor.parquet` 的 schema 实读
- code review / perf review 是否都通过（查 `report/code_review_report.md` / `perf_review_report.md`）
- 是否产出了 merged_benchmark0323_top100 / merged_baseline150 报告

#### 2.4 Analyzer run delta

路径：`/data/db/hft/analyzer2/{author}/{factor_set_name}/v{N}/` 及其子目录

筛选：子目录 mtime > `since`

每个新报告收集：
- 标签（如 `fa28_merged_benchmark0323_top100/v1`）
- 关键指标（**优先读结构化输出**）：
  - 先尝试 `metadata.json` / `signal_summary.parquet` / `signal_rank_table.parquet` / `daily_ic.parquet`
  - 单因子层：mean Rank IC（train/valid 各算）、top0.1% / top0.01% return（valid）
  - LGBM 层：从 `model_output/{matching_path}/lgbm_daily_ic_{train,valid}.parquet` 实读 mean IC / RankIC；从 `feature_importance_gain.parquet` 实读 top 10 gain ratio
- ⚠️ 如果无法自动提取，**标记 "需用户手工补充"，不得臆造数字**
- 报告路径（绝对路径供 sota_snapshot §1.2 引用）

**实读模板（HFT 专属）**：

```python
# 单因子 IC summary
import pandas as pd
from pathlib import Path
report_dir = Path('/data/db/hft/analyzer2/.../v1')
sig = pd.read_parquet(report_dir/'signal_summary.parquet')  # mean_rank_ic, top0p1_ret_bps, etc.

# LGBM IC summary (in model_output)
mout = Path('/data/db/hft/model_output/.../v1')
train_ic = pd.read_parquet(mout/'lgbm_daily_ic_train.parquet')  # cols: ds, ic, rank_ic
valid_ic = pd.read_parquet(mout/'lgbm_daily_ic_valid.parquet')
train_ric = train_ic['rank_ic'].mean()
valid_ric = valid_ic['rank_ic'].mean()
fi = pd.read_parquet(mout/'feature_importance_gain.parquet')  # cols: feature, gain
```

#### 2.5 Benchmark refresh 检测

扫描范围：
- `/home/cken/hft_projects/HFTPool/pool/benchmark*/` 新出现的目录（命名约定 `benchmark{YYYYMMDD}/`）
- 含 `run_benchmark.py` + `run_top100.py` + `report/` + `report_top100/`
- `/data/db/hft/model_output/` 下新出现的 `benchmark*` 子目录

每个检测到的 benchmark 收集：
- benchmark 目录路径 + 日期标签
- 合并的 FA 列表（从 `run_benchmark.py` 的 `DATASETS_DEF` 提取）
- LGBM 模型路径
- Top N 报告路径
- 是否为"真 refresh"（含 Top N 选择，即 `report_top100/` 存在）还是"merged run"（仅 `report/` 没 top100 选择）
- 与上一代 benchmark 的对比表（factor pool 总数、SOTA 100 重叠率、LGBM valid RankIC 变化、Top 10 features 进出名单）

**HFT 已知历史**：
- `pool/benchmark0323/` = Refresh #0（2025-03-23，baseline_150_new + FA12/16/20-25）

如检测到新 benchmark → 触发 sota_snapshot §1 的指针更新候选；如无 → sota_snapshot §1 保留上次值。

#### 2.6 Ad-hoc 课题报告扫描

**限定扫描路径**（只扫这几个可预测位置）：

```
/home/cken/hft_projects/HFTPool/pool/FA*/experiments/**/*.md
/home/cken/hft_projects/HFTPool/pool/FA*/analysis*/*.md
/home/cken/hft_projects/HFTPool/pool/FA*/report/*.md
/home/cken/hft_projects/HFTPool/pool/FA*/issue.md
/home/cken/hft_projects/HFTPool/pool/benchmark*/experiments/**/*.md
/home/cken/hft_projects/HFTPool/ob_research/*/experiments/**/*.md
/home/cken/hft_projects/HFTPool/ob_research/*/analysis*/*.md
```

筛选：
- mtime > `since`
- **排除 skill 固定产出文件名**：`research_report.md` / `research_log.md` / `factor_definition.md` / `quality_review.md` / `code_review_report.md` / `perf_review_report.md` / `data_validation_1m.md` / `axis_alignment_report.md` / `full_history_sweep.md` / `analyzer2_merged_summary.md` / `analyzer2_new_only_summary.md` / `README.md`
- 保留 ad-hoc 命名模式：`REPORT.md` / `analysis*.md` / `failure_analysis*.md` / `postmortem*.md` / `*_report_codex_*.md` / `addendum*.md` / `issue.md` / `iteration_plan*.md` 等

每个候选报告收集：
- 绝对路径
- 文件 mtime
- 所属 FA / 研究编号（从路径推断）
- 文件首 20-30 行预览（用于 Step 4 让用户判断是否保留）

**这只是候选列表**，最终保留哪些由用户在 Step 4 勾选。

#### 2.7 GitHub issues 扫描

执行：

```bash
gh issue list \
  --repo ligenjian001-ai/hft-sdk-issues \
  --label "project:quant_trading" \
  --search "updated:>={since}" \
  --state all \
  --limit 30 \
  --json number,title,state,labels,updatedAt,url
```

收集每个 issue：
- 编号 / 标题 / 状态 / 更新时间 / URL / labels
- 简短摘要：从 `gh issue view {N} --comments` 的最新 comment 或正文提取 1-2 句作为"最新进展/结论"

**这同样是候选列表**，最终保留哪些由用户在 Step 4 勾选（避免拉进无关 issue）。

**HFT 特殊**：如果 hft-sdk-issues 中既有 crypto 也有 HFT issue，注意通过 label / 标题关键词区分（HFT 相关常含 `bond_sz` / `playground` / `benchmark0323` / `realize` / `analyzer2` / `Benchmark100Trader` 等关键词）。

#### 2.8 Signal backtest 报告扫描

路径：
- `/home/cken/hft_projects/HFTPool/backtest/`（如存在）
- `/home/cken/hft_projects/HFTPool/pool/FA*/backtest*/`（如存在）
- playground batch-backtest 的默认产出路径（参考 `HftAnalyzer2/docs/howto_playground_backtest_signalreplay_zh.md`）

筛选：mtime > `since`

每个报告收集：
- 报告路径
- train/valid × (Sharpe / MaxDD / Total Net / Turnover) — 优先读 `report.md` 顶部表格或 `metrics.csv`
- 回测参数（交易模式 maker/taker、手续费、滑点、持仓约束、信号阈值）
- ⚠️ 无法自动提取时同样标记"需用户手工补充"

> ⚠️ **范围红线提醒**：signal backtest 是 **Layer 2** 产物，**不写入 sota_snapshot.md §1.3**。本子扫描产出仅写入 research_updates §1 聚合计数 + §3 ad-hoc（如果用户勾选完整报告收录）。如未来用户决定扩展 SOTA 范围到 Layer 2，需先改 target_and_workflow.md 再改本 skill。

#### 2.9 Factor pool 实读校验

路径：`/data/db/hft/factor_pool/{stage}/{author}/{factor_set_name}/{first_date}/{factor_set_name}/{factor_set_name}.parquet`

对每个本期新增的 FA / 已落地 FA，读取首日 parquet 的 schema 计算 signal 列数：

```python
import pyarrow.parquet as pq
META_COLS = {'code', 'time', 'bar_id', 'exchange_ts', 'md_id', 'timestamp'}
schema = pq.read_schema(parquet_path)
n_signals = len([c for c in schema.names if c not in META_COLS])
```

这是 §2.2 / §2.3 的因子计数的**权威来源**（不依赖 factor_list.md 中的表格数）。

### Step 3: 生成结构化总结（严格对齐 research_updates 模板）

本 Step 产出一份 markdown，**结构必须与 `research_updates.md` 的条目 7 节模板一一对应**，这样 Step 5 追加时可以直接整段塞入。

落盘路径：`/home/cken/crypto_world/quant-workflows/workflows/hft/reviews/meta_review_{YYYY-MM-DD}.md`（目录不存在则 mkdir -p）

内容结构：

```markdown
# HFT Meta Review {YYYY-MM-DD}

## 覆盖区间
- since: {日期}
- 上次 update 编号: #{N}
- 本次编号候选: #{N+1}

## 扫描结果摘要（供后续 Step 4 展示用）
- 新增 session: {count}
- 新增 FA: {count}
- 新增 realize: {count}
- 新增 analyzer run: {count}
- 检测到 benchmark refresh: {yes/no}
- 候选 ad-hoc 报告: {count}
- 相关 GitHub issues 候选: {count}
- 新增 signal backtest 报告: {count}（Layer 2，仅聚合计数不写 sota）
- 编号健康报告: 重复 {N1, N2, ...} / 缺号 {N3, ...}

---

## 候选 research_updates 新条目（严格对齐模板）

（以下内容可直接用于 research_updates.md 追加）

### [YYYY-MM-DD] Update #{N+1}

**时间区间**：{since} → {今日}
**子目录**：[`updates/{yyyymmdd}_update/`](updates/{yyyymmdd}_update/)

#### 1. 本期产出概览（聚合计数）
| 类别 | 新增 | 明细 |
| ... |

#### 2. SOTA 提升量
{根据是否有新 benchmark refresh 二选一写法；Bootstrap 模式写"首次 bootstrap，无上期对比，本期为 SOTA 基线（Refresh #0 = benchmark0323_top100）"；若本期无 refresh，明确写"未触发 benchmark refresh，累计待合并 FA 数 = X"}

#### 3. 收录的 ad-hoc 课题研究报告
{逐份写：原路径 + 本地副本占位路径 + 研究方向 + 核心结论}
{或 "本期无 ad-hoc 报告"}

#### 4. 相关 Project Issues
{逐行表：# / 标题 / 状态 / 一句话 / 链接}
{或 "本期内无相关 issue 更新"}

#### 5. Target / 方法论变化
{从扫描中是否发现需要调整的迹象；若无则写 "本期 target 与方法论无变化"}

#### 6. 本期观察到的模式 / 待关注方向
{初步观察，供后续 meta-review 聚合到 sota_snapshot §3；HFT 特有：post-Refresh #0 FA 累积量是否够触发 Refresh #1}

#### 7. 深度分析报告
{若本期未做定向分析则写 "本期未触发定向深度分析（当前为可选项）"}

---

## 候选 sota_snapshot 更新 diff

| 字段 | 原值 | 新值 | 依据 |
| 已落地因子总数 | ... | ... | ... |
| §1.1 因子集构成 | ... | ... | ... |
| §1.2 LGBM SOTA 指标 | ... | ... | ... |
| §1.3 回测结果 | — | — | （Layer 2，不维护） |
| §2 累计管线状态 | ... | ... | ... |
| §3 开放研究方向 | ... | ... | ... |

---

## 观察到的问题 / 建议（非落盘内容，仅供用户参考）
- {反复出现的阻塞模式}
- {post-Refresh #0 累积 FA 数 / 是否建议触发 Refresh #1}
- {命名前缀混乱 / 编号冲突的清理建议}
- {LGBM 模型文件清理风险（如 benchmark0323 SOTA 模型已丢）}
```

### Step 4: 用户确认询问（5 个独立问题）

**向用户展示**：Step 3 产出的总结核心要点 + 候选 SOTA diff + 候选 Update 条目 + ad-hoc 候选列表（带预览）+ issues 候选列表。

**然后按顺序问 5 个独立问题**（每个都要明确 yes / no / edit）：

1. **SOTA snapshot 更新**
   > "要把上述候选 sota_snapshot diff 落盘吗？(yes / no / 我先改几处再落)"

2. **research_updates 追加新条目**
   > "要把上述草拟的 Update #{N+1} 追加到 research_updates.md 顶部吗？(yes / no / 我先改几处)"

3. **Ad-hoc 报告收录**
   > 展示候选报告列表（路径 + mtime + 预览），询问：
   > "要保留哪些报告复制到 `updates/{yyyymmdd}_update/reports/`？请勾选编号（或 all / none / 指定子集）"

4. **GitHub issues 收录**
   > 展示候选 issue 列表（# + 标题 + 状态 + 更新时间 + 摘要），询问：
   > "要保留哪些 issue 写入 Update 条目 §4？请勾选编号（或 all / none / 指定子集）"

5. **target_and_workflow 调整建议**
   > "本次总结是否建议调整 target 或流程？"（**只提建议，不修改文件**；建议由用户手工编辑 target_and_workflow.md）

⚠️ **硬性规则**：未得到用户对问题 1-4 的明确 yes（或勾选）之前，**不得执行 Step 5 的任何文件创建/修改操作**。问题 5 的回答仅作为参考，skill 不对 target_and_workflow 做任何写操作。

### Step 5: 落盘操作（用户同意后）

**前置目录创建**（不存在则 mkdir -p）：

- `/home/cken/crypto_world/quant-workflows/workflows/hft/updates/`
- `/home/cken/crypto_world/quant-workflows/workflows/hft/updates/{yyyymmdd}_update/reports/`
- `/home/cken/crypto_world/quant-workflows/workflows/hft/sota_archive/`
- `/home/cken/crypto_world/quant-workflows/workflows/hft/reviews/`

**5.1 复制用户勾选的 ad-hoc 报告**

对每份勾选的报告：

```bash
# 文件名加来源前缀防冲突，如 fa28_merged_summary_REPORT.md
cp "{原路径}" "/home/cken/crypto_world/quant-workflows/workflows/hft/updates/{yyyymmdd}_update/reports/{来源前缀}_{basename}"
```

在即将追加的 Update 条目 §3 中更新"本地副本"字段为实际路径。

**5.2 SOTA 更新（若用户 yes）**

```bash
# 1. 归档旧版本
old_date=$(grep -E "^- \*\*本次 snapshot 日期\*\*" /home/cken/crypto_world/quant-workflows/workflows/hft/sota_snapshot.md | grep -oE "20[0-9]{2}-[0-9]{2}-[0-9]{2}" | head -1)
cp /home/cken/crypto_world/quant-workflows/workflows/hft/sota_snapshot.md \
   /home/cken/crypto_world/quant-workflows/workflows/hft/sota_archive/sota_snapshot_${old_date}.md

# 2. 用 Write 工具覆盖 sota_snapshot.md（基于 Step 3 的候选 diff，应用到模板产出完整新版本）
```

**5.3 research_updates 追加（若用户 yes）**

- **非 Bootstrap**：用 Edit 工具在 `<!-- meta-review skill 在此行下方追加新条目，保持最新在上 -->` 注释**正下方**插入新条目（保持最新在上）
- **Bootstrap 模式**：用 Edit 工具**整段替换** `## [待首次 meta-review 运行] Initial State` ... 末尾占位段，替换为 Update #1 的完整内容

**5.4 meta_review 报告落盘**

Step 3 产出的 markdown 无论用户对问题 1-4 的回答如何，都已落盘到 `reviews/meta_review_{date}.md`。它是本次 meta-review 的完整记录，方便后续追溯。

**5.5 落盘后摘要**

向用户汇报：
- 已创建/更新的文件列表 + 路径
- 复制的 ad-hoc 报告清单
- 归档的旧 SOTA 路径
- 本次 meta_review 报告路径
- 是否建议触发 Refresh #1（如累计 post-Refresh #0 FA 数 ≥ 2-3）

---

## 2. 可选分支：定向深度分析

如果用户在调用时传入了非日期参数（`direction` 文本），或在 Step 4 之后额外要求聚焦分析，执行以下分支。**本分支默认不执行**——skill 不主动触发。

### 2.1 direction 类型识别

常见 direction 及建议处理：

| direction 关键词 | 分析内容 |
|----------------|---------|
| `blocking pattern` / `阻塞` | 扫最近 N 个 session 的 research_log.md 中 FAIL / INTERRUPTED / issue.md 记录，找反复出现的阻塞模式 |
| `流程缺陷` / `compliance` | 对照 deep_research_workflow.md 的红线要求，统计各 session 的合规率和典型违规点 |
| `因子失效归因` / `命名前缀` | 对指定 FA 的 analyzer 报告 + 来源研究 report 做比对，找"通过 Phase 2/3 筛选但无增量"的系统性缺陷；HFT 特有：FA12/21/23 命名前缀混乱归因 |
| `因子冗余` / `overlap` | 跨 session 对比 factor_definition.md，找微观机制高度相似的因子组 |
| `Refresh #N decision` | 集中评估"是否触发下一次 benchmark refresh"——汇总 post-Refresh #N-1 累积 FA 的 merged analyzer 报告，估算合并后 LGBM IC 改善量 |
| `编号清理` | HFT 特有：扫描 ob_research/ 重复编号 / 缺号 / 中断 session，给出整理建议 |
| 自由文本 | 按用户指令聚焦分析，本 skill 只产出定性观察，不做定量实验 |

### 2.2 输出路径

产出到 `workflows/hft/reviews/meta_review_{YYYY-MM-DD}_{direction_slug}.md`，与 Step 3 的基础总结并列，**不覆盖 sota_snapshot 或 research_updates**。

如果用户确认，定向分析也可以额外写一份副本到 `updates/{yyyymmdd}_update/summary.md`，这时 Update 条目的 §7 "深度分析报告" 填写该路径；否则 §7 写 "本期未触发定向深度分析"。

### 2.3 边界

- 如果 direction 需要重新跑代码 / 重新跑 analyzer / 访问原始 tick 数据 → **超出本 skill 职责**，应建议用户改用 `/hft-deep-factor-research` 或 `/hft-benchmark-refresh` 或其它 skill
- 本 skill 只做"基于已有产出物的文本级分析"

---

## 3. 硬性规则

1. **只读基础文档**：`target_and_workflow.md` 是只读的，agent 不得修改
2. **严格用户确认**：`sota_snapshot.md` / `research_updates.md` / `updates/{date}_update/` 目录 / ad-hoc 报告副本 / sota_archive 归档等**所有文件创建或修改操作**必须在 Step 4 得到用户对问题 1-4 的明确 yes（或勾选）之后才执行
3. **归档旧版 SOTA**：每次覆盖 sota_snapshot 前必须 cp 到 `sota_archive/sota_snapshot_{old_date}.md`
4. **不做新研究**：本 skill 不触发 analyzer / playground / 不跑代码、不调用其它投研 skill
5. **扫描范围限定**：Step 2 扫描**严格限定在** §2 列出的 7 个根路径下的可预测位置；**不做 hft_projects 全盘扫描**
6. **并行扫描**：Step 2 的 9 个子扫描可派 SubAgent 并行处理，主进程只做汇总
7. **诚实报告**：如果扫描过程中某些信息（analyzer IC / 因子计数 / LGBM 模型路径）无法自动提取，明确标记 "需用户手工补充"，**不得臆造数字**；如发现 model.txt 已被清理（如 benchmark0323/v1_top100/ 现状），明确写在 §3 §6 提示
8. **时间戳用 UTC+8**：所有日期字段使用 `date '+%Y-%m-%d'`（Asia/Shanghai）
9. **Ad-hoc 报告判定严格**：Step 2.6 的筛选必须排除 skill 固定产出文件名（见排除清单），避免把标准报告误收为 ad-hoc
10. **issues 只留链接**：GitHub issues **不做本地快照**，只在 research_updates 条目 §4 中以表格形式记录 #编号 + 标题 + 状态 + 一句话 + URL
11. **SOTA 范围红线**：本 skill 严格只追踪 Layer 1。signal backtest（Layer 2）扫描结果只进 research_updates 聚合计数和 ad-hoc 收录，**不写入 sota_snapshot.md §1.3**；live trading（Layer 3）完全不在扫描范围
12. **实盘安全**：本 skill 不访问交易机，不读取交易机 session CSV，不调用 `/hft-live-strategy-deploy` 或 `/hft-intraday-trading-analysis`；如用户希望追踪实盘进展，应另外约定独立工作流

---

## 4. 交付物

| 文件 | 路径 | 生成条件 |
|------|------|---------|
| meta_review 报告 | `workflows/hft/reviews/meta_review_{date}.md` | 每次运行必产出 |
| 定向分析报告 | `workflows/hft/reviews/meta_review_{date}_{direction}.md` | 仅当提供 direction 时 |
| 更新后的 sota_snapshot | `workflows/hft/sota_snapshot.md` | 仅当用户对问题 1 同意 |
| 归档旧 SOTA | `workflows/hft/sota_archive/sota_snapshot_{old_date}.md` | 仅当更新 sota 时 |
| 更新后的 research_updates | `workflows/hft/research_updates.md` | 仅当用户对问题 2 同意 |
| 新期子目录 | `workflows/hft/updates/{yyyymmdd}_update/` | 仅当用户同意创建（通常与问题 2 同时） |
| 本地 ad-hoc 报告副本 | `workflows/hft/updates/{yyyymmdd}_update/reports/*.md` | 按用户在问题 3 的勾选 |
| 深度分析副本 | `workflows/hft/updates/{yyyymmdd}_update/summary.md` | 仅当做了定向分析且用户同意 |

---

## 5. 典型调用示例

```bash
# 例 1：定期自省，无参数
/hft-meta-review
# → since = research_updates 顶部日期 → 扫描 → 产出候选 → 问 5 个问题 → 落盘

# 例 2：首次 Bootstrap（research_updates 仍是 Initial State）
/hft-meta-review
# → 检测到 Bootstrap → since = bootstrap（全量扫描）
# → sota_snapshot 已经手工初始化，本次只追认 + 替换 Initial State 为 Update #1
# → 把 benchmark0323_top100 当作 Refresh #0 锚定基线

# 例 3：指定起始日期
/hft-meta-review 2026-03-01
# → since = 2026-03-01，扫描该日期之后的 delta

# 例 4：带定向方向
/hft-meta-review "Refresh #1 decision: 是否合并 FA26/27/28 重选 top100"
# → 先做基础总结 + 5 问
# → 然后执行定向分析，落盘到 reviews/meta_review_{date}_refresh1_decision.md
# → 给出"该 / 不该 / 还差什么"的定性建议（不跑实际 LGBM——那是 hft-benchmark-refresh 的事）

# 例 5：编号清理定向
/hft-meta-review "ob_research 编号清理"
# → 列出 #11 / #76 重复目录、#70 缺号、所有中断 session
# → 给出重新编号 / 标记废弃的建议
```

---

## 6. 与其它 HFT skill 的协作

- **`/hft-benchmark-refresh`**：本 skill 在 §1 §3 §6 中可能建议"触发 Refresh #N"，但**实际触发** Refresh 是 `/hft-benchmark-refresh` 的职责。本 skill 在下一次运行扫描时检测到新 `pool/benchmark{YYYYMMDD}/` 目录后，正式把它写进 sota_snapshot。
- **`/hft-realize-factor`**：本 skill 不修改 realize 产物；只在下一次扫描时把新 `pool/FA{N}/` 计入 §2.3。
- **`/hft-deep-factor-research`**：本 skill 不修改 ob_research 产物；只在下一次扫描时把新 session 计入 §2.1，并提示编号冲突。
- **`/hft-factor-list-compile`**：本 skill 不修改 factor_agent_docs；只在下一次扫描时把新 FA 计入 §2.2。

---

## 7. HFT 与 crypto 的差异速查

| 维度 | crypto (crypto-meta-review) | HFT (本 skill) |
|------|---------|---------|
| SOTA 范围 | Layer 1 (LGBM IC) + Layer 2 (BT) | **仅 Layer 1**（用户决策，2026-05-25） |
| 数据资产路径 | `/data/db/crypto/...` | `/data/db/hft/...` |
| 研究目录 | `crypto_world/crypto_ob_research/` | `hft_projects/HFTPool/ob_research/` |
| FA 文档目录 | `factor_agent_docs/` (crypto root) | `HFTPool/factor_agent_docs/` |
| Realize 目录 | `zebra_pool/fa{N}/` | `HFTPool/pool/FA{N}/` |
| Analyzer 输出 | `/data/db/crypto/analyzer/` | `/data/db/hft/analyzer2/` |
| LGBM 模型 | analyzer 目录内 `lgbm_model.txt` | `/data/db/hft/model_output/.../model.txt`（独立目录） |
| Benchmark 命名 | `campaign{N}_clean_sota/...` (ad-hoc) | `pool/benchmark{YYYYMMDD}/`（约定路径） |
| Universe | 7 个 U 本位永续合约 | bond_sz 190 codes |
| Bar 模式 | AmountBar（volume clock） | `bar_aggtrans_time_1`（agg trans 时间） |
| Label horizon | next100 ~ next200（~5-10 分钟） | next100（bar 单位，within_session） |
| 主预测口径 | mid-to-mid | mid-to-mid（within_session） |
| GitHub repo (issues) | `ligenjian001-ai/hft-sdk-issues` (label `project:quant_trading`) | 同上（同一 repo，按关键词区分） |
| 实盘 | 暂无 | Benchmark100Trader 在交易机（本 skill 不追踪） |
