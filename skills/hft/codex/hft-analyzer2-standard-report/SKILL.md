---
name: hft-analyzer2-standard-report
description: "当用户要用 HftAnalyzer2 生成“标准报告”（CLI: python -m HftAnalyzer2 report-standard；Python: generate_standard_report）或要把多个 factor_set/数据集合并后出一份 baseline 标准报告（build_multi_dataset_cache + generate_standard_report）时使用；开始任何可执行步骤前必须先阅读 /home/cken/hft_projects/HftKnowledge/research_docs/analyzer_user_manual.md 并严格按文档口径执行。"
---

# HFT Analyzer2 标准报告（单数据集 & 多数据集合并）

## 强制前置阅读（Hard Gate）

### 文档优先级（最高）

- **以 `analyzer_user_manual.md` 为唯一准则**：本 skill 仅做导航与检查清单；任何细节/参数/路径/口径与文档不一致时，一律以文档为准。  
- **严格按文档步骤顺序执行**：不得跳步、不得"凭经验补全"。若用户要求跳过文档硬门槛，必须明确拒绝并说明风险。  
- **给命令前先对照文档定位**：在输出可执行命令/脚本/路径/参数前，先指出对应的文档章节/小节（标题即可），再按文档顺序给出步骤。  

1) 打开并通读：`/home/cken/hft_projects/HftKnowledge/research_docs/analyzer_user_manual.md`  
2) 在给出任何“可执行命令/脚本/路径/参数”前，先用 5–10 条要点复述并让用户确认（以文档为准）：  
   - 正式交付优先用 **标准报告模式**：`report-standard` / `generate_standard_report`  
   - 想下结论建议至少 **3 个月以上**数据；少量天数只用于跑通链路  
   - 全 code 约定：一律指 `bond_sz`（以 `/data/share/dev/hft/config/universe_bond_sz.txt` 为准）；Analyzer2 的 base_rows/keep_ratio 也按该 universe 过滤 basic_table（避免 basic_table 含额外 code 导致 keep_ratio 虚假失败）  
   - Join 轴口径（强制）：`(code,time,md_id)`，其中 `time=local_ts`，`md_id=biz_index`；`exchange_ts` 仅用于交易时段过滤/诊断  
   - 因子侧准入（强制）：必须过 **Schema Gate**（必含 `code,time,md_id`；无 NaN/Inf；`md_id!=-1` 子集 key 唯一）与 **轴对齐 Gate**（建议用 `hft-axis-alignment-check`，3–5 天全 `bond_sz`，join 成功率与 bar 覆盖率均 ≥99.9%）  
   - 标准输出目录规范：  
     - 报告根目录：`/data/db/hft/analyzer2/{report_author}/{report_name}/{report_version}`  
     - 模型根目录：`/data/db/hft/model_output/{report_author}/{lgbm_name}/{lgbm_version}`（默认 `lgbm_name==report_name`）  
   - Analyzer2 默认**拒绝覆盖**既有产物：优先换 `report_version`/`lgbm_version`；或用 `--reuse_cache/--reuse_lgbm`  
   - 采样模式：`tick` vs `bar` 含义不同；`bar` 需 `bar_col`；团队统一口径下不再使用 `sum_signals/sum_cols` 做区间求和（sum 请在 Agent 内完成并输出）  
   - 多数据集标准报告：先 `build_multi_dataset_cache` 拼统一样本轴 cache，再 `generate_standard_report(reuse_cache=True)`  
   - 多数据集合并的样本门槛（强制）：`keep_ratio >= 99%`（hard filter 后样本/Join 前 base 样本）；低于阈值默认视为对齐/覆盖失败，不建议继续回测/汇报  
3) 若无法访问/读取该文档：停止并提示用户先提供文档内容或修复路径。  

## 入口选择（决策树）

- **单数据集标准报告**（一个 `stage/author/factor_set_name`）：用 CLI `python -m HftAnalyzer2 report-standard ...`  
- **多数据集合并 baseline 标准报告**（多个 `factor_set_name` 拼一起）：用 Python  
  1) `build_multi_dataset_cache`  
  2) `generate_standard_report(reuse_cache=True)`  

## 必须向用户确认的参数（缺一不可）

- 数据集：`stage`、`author`、`factor_set_name`、`start_date`、`end_date`
- universe：全 code 固定为 `bond_sz`（如需自定义，需明确 `--universe/--universe_file`）
- signals：明确列名列表（CLI 用逗号分隔字符串）
- 采样：`sample_mode=tick|bar`；若 `bar`：`bar_col`（团队统一口径：`sum_signals/sum_cols` 需为空）
- 资源：`workers`、`downsample`（tick 常见 ds20；bar 常见 ds1）、`quantile_cut_mode`
- 报告落盘：`report_author`、`report_name`、`report_version`（建议版本化且不可变）
- 重跑策略：是否 `reuse_cache`/`reuse_lgbm`，或直接换新版本号

## workers 与内存估算（重要，避免 OOM）

`workers` 参数控制按日并行构建 cache 的进程数。内存使用与 workers 和因子数量都有关，详见 `analyzer_user_manual.md` 第 11.1 节。

**快速参考**：
```
单数据集峰值内存 ≈ workers × (8 + 0.1 × num_signals) GB
多数据集合并峰值内存 ≈ workers × (20 + 0.2 × total_signals) GB
```

| 场景 | 因子数量 | 推荐 workers |
|------|---------|-------------|
| 单数据集，≤30 signals | ≤30 | 12-15 |
| 单数据集，30-60 signals | 30-60 | 10-12 |
| 单数据集，60-100 signals | 60-100 | 8-10 |
| 多数据集合并，≤50 signals | ≤50 | 6-8 |
| 多数据集合并，50-100 signals | 50-100 | 4-6 |
| 多数据集合并，>100 signals | >100 | 3-4 |

**硬上限**：以机器总内存与任务约束为准；建议峰值控制在总内存的 85%–90% 以内，并为其他服务/进程留出裕度。  

### 额外说明

- bar 模式 `last_valid` 聚合已做加速优化；如需回滚旧实现用于排查/对齐，可设置环境变量：`HFT_ANALYZER2_LAST_VALID_IMPL=legacy`（口径不变，仅性能差异）。
- 标准报告 `corr_heatmap` 默认采样上限可通过 `AnalyzerConfig.corr_heatmap_max_rows` 控制（默认 500,000；样本更少但更快、占用更低）。
- **内存统计口径**：评估/验收时只统计“本次启动的 Analyzer 进程树 RSS（主进程 + 子进程）”；不要用“系统 used 内存”做评估（会混入其他人进程）。
- 若你需要“数值完全可复现”的回归对比，建议使用 `quantile_cut_mode=exact`（`sample` 为近似采样，且在极端情况下可能受 cache 行顺序影响）。

## 单数据集：一条命令生成标准报告（CLI）

在仓库目录执行（按文档示例替换占位符）：

```bash
cd /home/cken/hft_projects/HftAnalyzer2

python -m HftAnalyzer2 report-standard \
  --stage <debug|production> \
  --author <factor_author> \
  --factor_set_name <factor_set_name> \
  --universe bond_sz \
  --start_date <YYYYMMDD> \
  --end_date <YYYYMMDD> \
  --signals sig_a,sig_b,sig_c \
  --downsample 20 \
  --workers 30 \
  --quantile_cut_mode exact \
  --with_profiling \
  --report_author <your_name> \
  --report_name <report_name> \
  --report_version <version>
```

要点（其余严格看文档）：  
- 默认只输出 **IC Top5** 的单因子详细图；全量单因子图需 `--detailed_single_factor`（非“标准报告”交付时谨慎使用）  
- 命令结束会打印 JSON：`report_md / report_dir / model_output_dir`  

### Bar 模式（CLI）

```bash
python -m HftAnalyzer2 report-standard \
  --stage <debug|production> \
  --author <factor_author> \
  --factor_set_name <factor_set_name> \
  --universe bond_sz \
  --start_date <YYYYMMDD> \
  --end_date <YYYYMMDD> \
  --signals sig_a,sig_b,sig_c \
  --sample_mode bar \
  --bar_col bar_aggtrans_time_1 \
  --workers 30 \
  --with_profiling \
  --report_author <your_name> \
  --report_name <report_name> \
  --report_version <version>
```

## 重跑策略（禁止覆盖既有目录）

- 推荐：任何改动都换新的 `report_version`（以及需要时换 `lgbm_version`）  
- 复用 cache：`--reuse_cache`  
- 复用 LGBM：`--reuse_lgbm`（要求 `{model_output_dir}/model.txt` 已存在）  

## 多数据集合并 baseline：cache → 标准报告（Python）

核心约定（非常容易踩坑）：  
- `signals_by_dataset` 的 key **必须等于** `DatasetSpec.name`  
- 强烈建议每个数据集都设置 `prefix`，否则同名 signal 冲突会报错  
- `date_mode` 推荐 `intersection`（只跑所有数据集共有交易日）；`union` 会引入更多缺失  

最小骨架（按文档 6 章示例补齐字段/参数）：

```python
from pathlib import Path
from HftAnalyzer2 import (
    HftAnalyzer2, AnalyzerConfig,
    DatasetSpec, FactorAggSpec, LabelSpec, SamplingSpec, LgbmConfig,
)

cfg = AnalyzerConfig(downsample_stride=20, workers=30, quantile_cut_mode="exact")
an = HftAnalyzer2(config=cfg, verbose=True)

datasets = [
    DatasetSpec(name="Agent1/ds1", stage="debug", author="Agent1", factor_set_name="ds1", prefix="a1_ds1__"),
    DatasetSpec(name="Agent2/ds2", stage="debug", author="Agent2", factor_set_name="ds2", prefix="a2_ds2__"),
]
signals_by_dataset = {
    "Agent1/ds1": ["sig_a", "sig_b"],
    "Agent2/ds2": ["sig_c"],
}

labels = [LabelSpec(name="ret_lag10_next100", lag=10, horizon=100)]
sampling = SamplingSpec(mode="tick")  # bar: SamplingSpec(mode="bar", bar_col="bar_aggtrans_time_1")
factor_agg = FactorAggSpec(sum_cols=())  # 团队统一口径：sum_cols 必须为空（sum 在 Agent 内完成）

report_author = "<your_name>"
report_name = "<merge_report_name>"
report_version = "<v1>"
report_dir = Path(f"/data/db/hft/analyzer2/{report_author}/{report_name}/{report_version}")

# 1) 多数据集拼 cache（落到 report_dir/cache）
dates, coverage = an.build_multi_dataset_cache(
    datasets=datasets,
    signals_by_dataset=signals_by_dataset,
    start_date="<YYYYMMDD>",
    end_date="<YYYYMMDD>",
    labels=labels,
    sampling=sampling,
    factor_agg=factor_agg,
    cache_dir=report_dir / "cache",
    error_dir=report_dir / "error_reports",
    date_mode="intersection",
    reuse_cache=False,
    workers=30,
)

# 2) cache 的真实列名 = prefix + 原 signal
signals_out = [f\"{(d.prefix or '')}{s}\" for d in datasets for s in signals_by_dataset[d.name]]

# 3) dummy dataset + 复用 cache 生成标准报告
dummy = DatasetSpec(name="MULTI/merge", stage="debug", author="MULTI", factor_set_name="merge")
report_md = an.generate_standard_report(
    dataset=dummy,
    start_date="<YYYYMMDD>",
    end_date="<YYYYMMDD>",
    signals=signals_out,
    labels=labels,
    sampling=sampling,
    factor_agg=factor_agg,
    report_author=report_author,
    report_name=report_name,
    report_version=report_version,
    lgbm_cfg=LgbmConfig(num_boost_round=20, n_jobs=40),
    with_profiling=True,
    reuse_cache=True,
    coverage_pct_by_signal=coverage,
    extra_meta={"multi_datasets": [d.__dict__ for d in datasets], "date_mode": "intersection"},
)
print(report_md)
```

合并后样本数可能明显变少：signals 越多越容易被稀释；先看 `sample_overview.parquet` 与 `coverage.parquet` 再下结论（细节见文档）。

## 产物验收（最小）

- `report_dir/report.md` 存在，且 `report_dir/img/` 有图片  
- `report_dir/metadata.json`、`report_dir/signal_rank_table.parquet`、`report_dir/coverage.parquet` 存在  
- 若开启 LGBM：`model_output_dir/model.txt` 存在  
- 其余产物解释与字段口径：严格以 `analyzer_user_manual.md` 为准  
