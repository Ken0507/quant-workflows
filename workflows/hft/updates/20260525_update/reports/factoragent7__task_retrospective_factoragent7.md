# FactorAgent7（FA7）任务复盘与流程改进建议（归档到 FactorAgent6/report）

生成时间：`[2026-01-24 16:38:53 UTC+8]`

本报告基于 FactorAgent7（FA7）全流程交付过程进行复盘，重点回答“返工/耗时点、口径不一致、完成度自检、Skills 价值、可沉淀为 Skill 的操作”。关键证据与产物可参考：

- 研究日志：`/home/cken/hft_projects/HFTPool/pool/FactorAgent7/report/research_log.md`
- 问题记录：`/home/cken/hft_projects/HFTPool/pool/FactorAgent7/report/issue.md`
- 1 个月强验证报告：`/home/cken/hft_projects/HFTPool/pool/FactorAgent7/report/data_validation_1m.md`
- Analyzer2 标准报告（新因子 / 合并 baseline）：`/home/cken/hft_projects/HFTPool/pool/FactorAgent7/report/analyzer2_report_new_only/`、`/home/cken/hft_projects/HFTPool/pool/FactorAgent7/report/analyzer2_report_merged_with_baseline/`
- LGBM uplift：`/home/cken/hft_projects/HFTPool/pool/FactorAgent7/report/lgbm_uplift_vs_baseline.md`

---

## 1) 返工/耗时过长的困难点与改进建议

### 1.1 `GetSnapshot()` 深档缺失/脏值导致极端值 → 强验证返工

**现象**
- 月度强验证（`20250102-20250127` 全 code 全量）发现极少数 tick 出现离谱极值：例如 `fa7_micro_gap_bps_3` max 达 1e14 bps（详见 `FactorAgent7/report/issue.md` 第一条）。

**根因**
- `GetSnapshot()` 在深档缺失/未填充时可能出现“残留垃圾值”，若直接拿来算 micro/queue/eff_gap 等 bps，会在分母很小或 mid 异常时放大为极端值。

**造成的返工**
- 必须回到 Step1 修复实现（改为从 full_book 提取 TopK，并对有效档位做显式校验），然后重刷 1 个月并重做强验证（统计 + 点对点复算 + 单测）。

**建议**
1. 在 `data.md` 中把“Snapshot 深档脏值风险”升级为醒目高风险提示，并给出标准防护模式（有效性判断/回退策略/对缺档输出确定值）。
2. 在 Playground 因子模板或工具库中提供可复用 helper：`ExtractTopKFromFullBookSafe()` + `IsLevelValid()`，减少每个 agent 自己写边界判断导致的不一致与漏判。

### 1.2 全历史刷数作业不稳定：中断/缺日/坏 parquet → 分段补刷与反复验收

**现象**
- 全历史（`20250102-20250730`）批量刷数出现 BatchRunner 非 0 退出码、缺失日期目录、以及单日 parquet footer 损坏等问题（详见 `FactorAgent7/report/issue.md` 中 Step3 多条）。

**根因推测**
- 单日资源开销差异巨大（同样是 `bond_sz` 全 universe，某些日单进程 RSS 可从 ~3GB 跳到 ~19GB 甚至 ~27GB），导致“按少量样本估算 workers”的策略偏乐观；叠加 IO/落盘中断，容易形成坏 parquet 或空目录。

**造成的返工**
- 需要改为“分段日期范围 + 降并发 + 每段验收 + 定点补刷坏日/缺日”，并且加入“识别 corrupted parquet”的验收脚本，才能保证全历史完整性。

**建议**
1. 把“factor_pool 完整性验收”固化为批量刷数的默认 gate：missing_days=0、corrupted_days=0、schema_mismatch_days=0、NaN/Inf=0（只要有一项不满足就自动生成补刷清单）。
2. BatchRunner 建议支持“断点续跑/失败重试”：按日粒度持久化失败原因，提供 `--resume` 或 `--retry-failed-days`，避免手工定位与重刷。
3. 规范要求：全历史刷数必须将 stdout/stderr 重定向落盘（或框架默认落盘），否则“失败原因不可回溯”会显著放大返工成本。

### 1.3 Analyzer2 资源估算偏差：workers 多次下调 → 返工与等待

**现象**
- Analyzer2 标准报告阶段，按初始估算启动 `workers=20`，实测 RSS 合计远超 180GB；后续多次中止并降并发（详见 `FactorAgent7/report/issue.md` 中 Step3 相关条目）。

**根因**
- bar 模式按日读取/拼接/分位切分可能在 worker 内形成较大的中间对象，且不同日期样本量差异导致峰值不可用“单日静态估算”覆盖。

**建议**
1. Analyzer2 增加 `memory_guard`：启动前给出保守估算与建议 workers，并在运行中检测到 RSS 超阈值时自动降并发/暂停排队，而不是继续顶着跑。
2. 多数据集合并（baseline+new）默认从小并发开始（例如 2~6），并提供“经验上限表”（按 signals 数/数据集数/样本量）避免重复踩坑。

### 1.4 Analyzer2 join 轴口径问题：time(+8h) / time_key 推断 / join_keys 选择 → 返工与代码修复

**现象**
- new-only 报告曾出现 `join_rows=0`，每日 cache 为空（详见 `FactorAgent7/report/issue.md` 中 Step3 “time 与 basic_table time +8h”条目）。
- merged 报告曾出现样本塌陷（某些日仅 0~1 行），与 join_keys 过严或 time_key 推断误判有关（详见 issue.md 中 join_keys/time_key 相关条目）。

**根因**
- `basic_table.time` 与因子输出 `time=event.local_ts` 在历史数据资产中存在偏移/单位差异（ns vs ms）等“事实口径”，而任务规范又强调 `time=event.local_ts`，两者若无明确兼容层就会导致 join 失败或 silent sample collapse。
- 多数据集合并时 `md_id` 在不同 factorset 之间不一定一致，作为 join_keys 会放大不一致风险。

**建议**
1. 文档明确“Analyzer2 join 的标准轴”：`time` 的单位、是否存在 +8h legacy offset、`md_id` 的严格来源；并提供最小可复现的 axis-overlap check 脚本。
2. multi-dataset 合并默认 `join_keys=(code,time)`，除非明确保证 `md_id` 跨 factorset 一致；并在报告里输出“每数据集参与 join 的覆盖率”用于定位样本塌陷根因。

### 1.5 IC Decay/Price Path horizons 口径遗漏 → 报告返工重跑

**现象**
- 交付的 Analyzer2 报告最初未按要求生成 IC Decay/Price Path 的固定 horizons 列表，用户指出后重跑修复（见 `FactorAgent7/report/research_log.md` 2026-01-24 00:52:37 起）。

**根因**
- 脚本仅传入主 label `ret_lag0_next20`，未补齐其它 `ret_lag0_next{h}`，导致 curve 相关图只剩单点（与 CLI 默认 bar 口径不一致）。

**建议**
1. 在 Analyzer2 标准报告口径中明确：若要画 IC Decay/Price Path，必须提供一组 horizons labels，并把默认列表写进文档/模板（避免每个 agent 自己猜）。
2. 交付前增加自动验收：检查 `metadata.json` labels 是否包含目标 horizons 集合，以及关键图 `lgbm_train_ic_decay.png`、`lgbm_train_price_path.png` 是否存在。

---

## 2) 文档/任务设定不清晰或口径不一致处与改进建议

### 2.1 `time=event.local_ts`（任务规范） vs `basic_table.time`（数据资产事实）存在隐性冲突
- 任务硬性规范要求 `time=event.local_ts`，但 Analyzer2 的 `basic_table` join 轴在历史资产中可能带有 legacy offset/单位差异；若文档未说明，会导致报告阶段才暴露“join_rows=0”。

**建议**
- 在 `HftKnowledge/research_docs/data.md` 或 Analyzer2 手册中加一节“时间轴与 join 轴事实口径”，并给出迁移/兼容策略（短期 adapter，长期统一字段）。

### 2.2 `md_id` 的定义与跨 factorset 一致性未给出“硬定义”
- 多数据集合并若把 `md_id` 当 join key，会非常依赖跨数据集一致性；但任务文档未明确 `md_id` 的来源/单位/稳定性。

**建议**
- 文档给出 `md_id` 的严格定义（事件类型差异、来源字段、示例），并明确“是否推荐用于合并 join_keys”。

### 2.3 baseline top80 合并规则复杂但缺少“官方配置/脚本”
- baseline top80 需要加载多个数据集并按 json 列表挑选特征；该过程可重复、易错，且每个 agent 自己写路由与前缀会导致口径漂移。

**建议**
- baseline 目录提供统一的“合并配置文件（datasets+signals_by_dataset）+ 一键脚本”，并在 Skill 中直接复用，减少重复造轮子。

### 2.4 Skill 文本中的“用户确认”步骤与任务纪律“禁止对话”存在冲突
- 本次执行纪律要求任务结束前禁止对话/提问，但部分 Skill 流程包含让用户确认参数的步骤。

**建议**
- 为这类强制闭环任务提供 Skill 的“non-interactive 模式”：要求把关键参数写入日志即可，不再卡在“确认”步骤。

---

## 3) 对照原始任务文档逐项自检：完成度与潜在遗漏

### 3.1 我认为已完成的硬性交付项（对应产物齐全）
- Step0 文档通读并对齐：已记录到 `FactorAgent7/report/research_log.md`。
- Step1 因子开发 + `signal_agg.json` + 单测 + smoke：工程与命令在 `FactorAgent7/code/README.md`，smoke 流程在日志中可复现。
- Step2 1 个月强验证（全 code、全交易日）：`FactorAgent7/report/data_validation_1m.md`（含统计、点对点复算、不变量检查、单测、问题闭环）。
- Step3 全历史刷数（`20250102-20250730`、全 code）：通过分段刷数与验收闭环，最终 `expected_days=139` 且 missing/corrupted=0（见 `FactorAgent7/report/factor_pool_check_full_history.json` 与 `research_log.md`）。
- Step3 两份 Analyzer2 标准报告（新因子 / baseline+new 合并）：交付目录分别为  
  `FactorAgent7/report/analyzer2_report_new_only/`、`FactorAgent7/report/analyzer2_report_merged_with_baseline/`，并已修复 IC Decay/Price Path horizons（labels=18）。
- Step4 LGBM uplift（三组对比）：`FactorAgent7/report/lgbm_uplift_vs_baseline.md`（含 train/valid、CI、重要性、regime 分桶与失败日提示）。
- Step5 最终整理：`FactorAgent7/pool` 目录含 code/report/README/脚本齐全，可复现。

### 3.2 我认为存在的“遗漏/不足”（但已在后续修补或仍可改进）
1. **交付前的“horizons 合规验收”缺失**：导致 IC Decay/Price Path horizons 口径遗漏并返工重跑。  
   - 改进：把 horizons 列表作为标准报告配置的一部分，并在交付前自动检查 metadata+关键图。
2. **资源估算与并发策略偏激进**：Analyzer2 初始 workers 设定导致多次中止。  
   - 改进：默认从保守并发起步 + memory_guard + 分阶段复用 cache（先 cache 后 report）。
3. **多数据集合并的 join_keys 经验不足**：md_id 跨数据集一致性不足导致样本塌陷风险。  
   - 改进：文档/工具给出推荐 join_keys，并自动输出每数据集 join 覆盖诊断表。

---

## 4) 使用 Skills 是否提升了工作效率？

结论：**显著提升**（尤其是减少口径漂移与命令错误），但仍有提升空间。

主要收益：
- 将“写因子/批量刷数/标准报告”三类高风险操作约束在可复现流程内，降低路径、参数、输出目录写错的概率。
- 强制要求在日志中记录关键命令与输出，便于复盘与返工定位。

仍可增强的点：
- Skill 更偏流程规范，对“资源守护（内存/并发）”“自动验收与修复（缺日/坏 parquet）”“报告合规检查（horizons/关键图）”覆盖不足，导致返工仍需要手工搭脚本。

---

## 5) 建议沉淀为 Skill 的操作（提升后续效率）

1. **`factor-pool-integrity-check-and-repair`（高优先级）**  
   - 输入：factorset 根目录 + 日期范围 + code universe（bond_sz）  
   - 输出：missing_days/corrupted_days/schema_drift/NaNInf 统计 + 自动生成补刷命令/可选自动执行补刷。

2. **`analyzer2-standard-report-horizons-guard`（高优先级）**  
   - 统一 bar 模式 horizons 默认列表；生成报告前自动补齐 labels；生成后检查 `metadata.json` 与关键图（ic_decay/price_path）。

3. **`analyzer2-merge-baseline-top80-plus-new`（高优先级）**  
   - 读取 baseline 的 `top80_features_by_agent.json`，自动构建 `datasets + signals_by_dataset`；默认 `join_keys=(code,time)`；带 memory_guard 与分阶段 cache→report 的模板。

4. **`analyzer2-artifact-sync`（中优先级）**  
   - 将 `/data/db/hft/analyzer2/...` 的报告产物同步到 `pool/<Agent>/report/...`，默认排除 `cache/memmap/error_reports`，避免手工 copy 漏文件或带入大目录。

5. **`axis-alignment-smoke`（中优先级）**  
   - 抽样若干 code/day，比对 `(code,time,md_id)` overlap，自动检测 time 单位/offset（ns/ms/+8h）并输出诊断结论（可作为进入 Analyzer2 前的 gate）。

