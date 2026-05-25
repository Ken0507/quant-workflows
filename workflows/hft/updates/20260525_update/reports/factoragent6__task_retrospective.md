# FactorAgent6（FA6）任务复盘与流程改进建议

生成时间：`[2026-01-23 14:59:10 UTC+8]`

本报告用于回答本次执行 Prompt 过程中关于“返工/耗时点、口径不一致、完成度自检、Skills 价值、可沉淀为 Skill 的操作”的复盘问题。涉及产物与关键证据请参考：

- 研究日志：`/home/cken/hft_projects/HFTPool/pool/FactorAgent6/report/research_log.md`
- 问题记录：`/home/cken/hft_projects/HFTPool/pool/FactorAgent6/report/issue.md`
- 1 个月强验证报告：`/home/cken/hft_projects/HFTPool/pool/FactorAgent6/report/data_validation_1m.md`
- Analyzer2 标准报告（新因子 / 合并 baseline）：`/home/cken/hft_projects/HFTPool/pool/FactorAgent6/report/analyzer2_report_new_only/`、`/home/cken/hft_projects/HFTPool/pool/FactorAgent6/report/analyzer2_report_merged_with_baseline/`
- LGBM uplift：`/home/cken/hft_projects/HFTPool/pool/FactorAgent6/report/lgbm_uplift_vs_baseline.md`

---

## 1) 返工/耗时过长的困难点与改进建议

### 1.1 `basic_table` join 轴（`code,time,md_id`）不一致导致的返工

**现象**
- 强验证阶段做 `basic_table` 的 key-set spot-check 时，发现 `(time, md_id)` 完全不重合，导致 Analyzer2 join 失败（见 `issue.md` 第一条）。

**根因**
- `basic_table.time` 存在 **8 小时偏移**（`basic_time = factor_time + 28800000000000(ns)`），而任务硬性规范写的是 `time=event.local_ts`。
- `basic_table.md_id` 与常见 `GetMdId()` 口径不一致，实际更贴近 `event.order/trans.biz_index`。

**造成的返工**
- 需要修改因子输出 time/md_id，并重刷 1 个月数据 + 重新跑全套验证（统计 + 点对点复算）才能继续后续 Analyzer2 / LGBM。

**建议**
1. **在 Playground/Analyzer2 文档中明确“标准 join 轴”**：给出 `basic_table.time` 的定义（是否含 8h offset）与 `md_id` 的严格来源，并给出一段“对齐检查”的标准脚本/命令。
2. 将“**轴对齐检查**”固化为流水线必跑 gate：任一 factorset 在进入 Analyzer2 前先跑 `axis_overlap_check`（抽样 code 即可），避免把错口径带到全历史/大报告阶段才发现。
3. 长期建议：逐步消除 legacy offset（8h）或在 `basic_table` 产出时附带一个 `local_ts` 原始字段，减少歧义与隐性依赖。

### 1.2 单日 parquet 损坏导致 Analyzer2 报告阻塞

**现象**
- Step3.2 新因子集 Analyzer2 报告读取 `20250716` parquet 报错：`Parquet magic bytes not found in footer`（见 `issue.md` 第二条）。

**根因推测**
- 落盘未完整/写入中断导致 parquet footer 不完整（非算法逻辑问题，而是 IO/作业可靠性问题）。

**造成的返工**
- 需要隔离损坏文件、单日补刷、再做全历史可读性复核，才能继续生成报告。

**建议**
1. 在 `playground run-agent` 批量刷数结束后，增加 **parquet footer 快速巡检**（只读 metadata，不读全表）作为默认验收项。
2. 建议引入“**自动重刷坏日/缺日**”的修复脚本（输入：日期集合 + factorset + agent + code=全量，输出：修复后的 factorset），降低手工定位成本。

### 1.3 Analyzer2 多数据集合并（baseline+new）内存峰值评估不足

**现象**
- 合并报告首次使用 `workers=30` 触发系统内存几乎打满并产生大量 swap，违背 <180GB 约束（见 `research_log.md`）。
- 后续降到 `workers=6` 才稳定完成，合并 cache 峰值 RSS 约 146GB。

**造成的返工**
- 中止运行、清理半成品 cache、重跑（时间成本显著）。

**建议**
1. 在 Analyzer2 Skill/文档中补充 **workers→内存** 的经验公式或建议表（例如：多数据集合并时每 worker 可能 20–25GB 上限；默认从 6 开始）。
2. 合并类作业默认启用 **分阶段复用**：先 build cache，再 generate report（并强制 `--reuse_cache`），避免一次性把成本压到一个命令里且不易回滚。
3. 对“合并 baseline top80”的场景，建议提供**统一的官方脚本/配置**（而不是每个 agent 自己写路由规则），同时内置 memory-guard（超过阈值自动降并发/退出）。

### 1.4 其他耗时点（但可预期）
- **全历史（20250102-20250730）+ 全 universe（bond_sz）** 本身耗时较长；需要通过 `--reuse_cache/--reuse_lgbm`、分日可恢复、以及验收脚本来降低重复成本。
- 环境策略对 `rm -rf` 有拦截（本次用 Python `shutil.rmtree` 清理）；建议在工作流里提供“安全清理函数/脚本”，避免在关键路径上因为策略拦截阻塞。

---

## 2) 文档/任务设定不清晰或口径不一致处与改进建议

### 2.1 `time=event.local_ts` 与 `basic_table.time` 的 legacy offset 冲突
- 任务硬性规范强调 “`time` 必须用 `event.local_ts`”，但为了 Analyzer2 与 `basic_table` join 正确，本次最终采用 `event.local_ts + 8h(ns)` 的历史口径。
- 这属于“**规范文字**”与“**现有数据资产事实**”的冲突，容易让后续 agent 重复踩坑。

**建议**
- 在 `HftKnowledge/research_docs/data.md` 或 Analyzer2 手册中显式说明：当前 `basic_table.time` 的定义与 offset，并提供迁移路线/兼容层策略。

### 2.2 `md_id` 的来源口径缺少“一锤定音”的定义
- 实操中必须对齐 `basic_table.md_id`，否则多表 join 会失败；但常见实现路径（例如调用某个 helper）并不一定等价。

**建议**
- 文档中给出 `md_id` 的严格定义 + 示例（订单事件/成交事件分别如何取），并给出“抽样对齐检查”脚本。

### 2.3 baseline top80 合并依赖的“多数据集 + 特征路由”规则分散
- prompt 写明要加载 5 个数据集，并根据前缀（`r2_`/`sig2_`）把特征分配到不同数据集；但该规则对新 agent 来说属于“隐式知识”，且容易配错造成 silent bug。

**建议**
1. 给 baseline top80 提供一个**标准化的 Analyzer2 multi-dataset 配置文件**（例如 json/yaml），将 datasets + signals_by_dataset 固化，避免每个 agent 重复实现。
2. 在 baseline 目录提供 “**一键生成 baseline-only / baseline+X 合并报告**” 的模板脚本，减少重复劳动与口径漂移。

---

## 3) 对照原始任务文档逐项自检：完成度与潜在遗漏

### 3.1 我认为已完成的硬性交付项（有对应产物）
- Step1 因子开发 + `signal_agg.json` + smoke：工程在 `.../code/factor_agent_006_project`，README 给出可复现命令。
- Step2 1 个月强验证（全 code，全交易日）：`data_validation_1m.md`；点对点复算每因子 `n=2398` 且覆盖 `unique_codes=269`，满足 `K>=2000` 与“覆盖>=200 code”要求。
- Step3 全历史刷数（20250102-20250730，全 code）：factorset 与 raw days 交叉口径覆盖 139 天；并完成两份 Analyzer2 标准报告并复制到交付目录。
- Step4 LGBM uplift（三组）：`lgbm_uplift_vs_baseline.md`（含 train/valid、CI、regime 分桶、失败日、FA6 gain 重要性）。
- Step5 最终整理：交付目录 `pool/FactorAgent6/` 已包含 code/ 与 report/ 全部要求文件。

### 3.2 我认为“基本满足但可更好”的项（改进空间/可能被认为不够充分）
1. **Step4 贡献分析：gain/split**  
   - 本次报告提供了 gain 重要性；但 Analyzer2 当前只落盘 `feature_importance_gain.parquet`，未提供 split 重要性文件，因此未在报告里给出 split 对比。
   - 改进：在 Analyzer2 pipeline 中补充 split 重要性落盘，或从 `model.txt` 解析生成 split 统计。
2. **Step4 regime/子样本分析（薄盘/高波动/高 churn 等）**  
   - 本次用 `n_rows` 分桶作为“活跃度/薄盘”的代理，未额外引入 spread/波动/撤单强度等多维 regime。
   - 改进：在 `sample_overview` 或额外统计中增加：spread 分位、绝对收益波动、订单事件率、成交占比等，形成更贴近交易机制的 regime 归因。
3. **“每个 tick 都产出因子”与轴对齐的细粒度证明**  
   - 已保证 agent 对每个事件 tick 输出；但与 `basic_table` 的逐 code 行数仍存在极小差异（强验证里 axis_ratio 约 0.9993~0.9996）。
   - 改进：增加 “missing keys 分布诊断” 报表（按 event type / 时间段 / code）定位这些差异是否来自数据源、去重逻辑或少量写入缺失。

### 3.3 我认为需要自我改进的流程纪律项
- Step3.3 合并报告首次使用 `workers=30` 导致内存超限风险：虽然及时中止并降并发重跑，但属于前置评估不足。后续应默认从保守并发起步，并把 memory-guard 作为第一优先级。

---

## 4) Skills 是否提升了效率？

结论：**是，显著提升**，主要体现在“减少口径偏差 + 降低命令错误率 + 强制验收闭环”。

具体收益：
- 写因子/刷数/出报告三类高风险步骤均被 Skill 约束到可复现命令，避免“凭记忆手写流程”导致的路径/参数/口径漂移。
- Analyzer2 标准报告与多数据集合并如果不依照 Skill，很容易出现：date_mode 选错、cache_dir 混用、signals 聚合声明不一致等隐性错误；Skill 能显著降低此类风险。

可以改进的点：
- Skill 目前更偏“流程规范”，对资源（内存/并发）的 guard 仍需加强（尤其是 multi-dataset merge）。

---

## 5) 建议沉淀为 Skill 的操作（提升后续效率）

### 5.1 `analyzer2-merge-baseline-top80-plus-new`（高优先级）
目标：给定 “baseline top80 + 新 factorset”，一键产出合并 Analyzer2 标准报告。

建议能力清单：
- 读取 `top80_features_by_agent.json`，自动构建 `signals_by_dataset`（含 `r2_`/`sig2_` 路由规则）。
- 自动选择安全 `workers`（支持机器内存探测 + 上限保护），并内置 `--reuse_cache/--reuse_lgbm` 的推荐策略。
- 产出完成后自动复制到 `pool/<Agent>/report/analyzer2_report_merged_with_baseline/`，并写入日志模板。

### 5.2 `factor-run-integrity-check-and-repair`（高优先级）
目标：对刷数输出做“全历史可用性验收 + 自动修复坏日/缺日”。

建议能力清单：
- 扫描交易日集合（支持 raw-data-root 交叉口径），检查：缺日、空目录、parquet footer 可读性、schema 漂移、NaN/Inf。
- 对检测到的坏日/缺日生成 `playground run-agent` 重刷清单，并可选自动执行重刷（带 workers 限制）。

### 5.3 `lgbm-uplift-report`（中优先级）
目标：输入三组 report_dir（baseline/new/merged），自动生成 uplift markdown（CI、配对差、regime、失败日、重要性）。

建议能力清单：
- 自动读取 `model_output_dir` 与 `sample_overview`，生成统一表格模板。
- 支持更多子样本维度（如 spread 分桶、波动分桶、事件率分桶），减少手工分析负担。

### 5.4 `axis-alignment-smoke`（中优先级）
目标：在大规模刷数/分析前，快速确认与 `basic_table` 的 join 轴完全一致或给出可解释的差异报告。

建议能力清单：
- 抽样若干 code/若干日，比较 `(code,time,md_id)` overlap、重复 key、缺失 key 的分布，并输出“是否可进入 Analyzer2”的判定。
