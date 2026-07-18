---
name: hft-analyzer2-standard-report
description: "使用 HftAnalyzer2 v3 生成正式标准报告，并显式区分单原始因子评价（single_factor）、多个因子训练 LGBM（train_lgbm）、已有单个 LGBM 评价（existing_lgbm）；也用于多个 factor_set 合并 cache 后按上述模式出报告。执行前必须通读 analyzer_user_manual.md。"
---

# HFT Analyzer2 标准报告

## Hard Gate：先读唯一口径文档

开始任何命令、脚本或报告生成前，完整阅读：

`/home/cken/hft_projects/HftKnowledge/research_docs/analyzer_user_manual.md`

若无法读取，停止执行。Skill 只负责路由和验收；参数、数据语义与文档冲突时，以手册为准。

执行前向用户复述并确认以下口径：

- 正式结论至少使用 3 个月；团队标准提交集为 `20250102-20250730`（139 日）。
- 全市场固定 `bond_sz`；Join key 固定 `(code,time,md_id)`，其中 `time=local_ts`、`md_id=biz_index`。
- `exchange_ts` 用于连续交易过滤、场景窗口，以及 phys20 的执行时钟/entry lookup；不能替代 Join key。
- v3 固定 `bar_aggtrans_time_1`、downsample=1、baseline 主 label=`ret_lag0_next100`，phys20 只评价、不进入训练 target。
- Schema Gate、3–5 日轴对齐 Gate（join 与 bar coverage 均 ≥99.9%）和 keep_ratio≥99% 均必须通过。
- Group cuts 在同一 `stage × segment` 内由 baseline/phys20 共用；phys20 净收益扣 `phys20_entry_spread_bps`。
- `/data/db/hft/analyzer2` 与 `/data/db/hft/model_output` 是缓存；长期报告和模型必须物理复制进 HFTPool，禁止 symlink。

## 第一步：显式选择 report_mode

报告对象与数据源数量是两个正交维度。先选择对象模式，再决定单数据集或多数据集合并。

| 模式 | 何时使用 | 必须行为 | 禁止行为 |
|---|---|---|---|
| `single_factor` | 评价恰好 1 个原始 factor signal | 只输出 `stage=all` 的 factor 场景评价 | 不训练 LGBM；不生成 LGBM 区块或 `lgbm_*` metrics |
| `train_lgbm` | 至少 2 个原始 factors 训练新模型 | 因子 overview/Top5 + LGBM train/valid 完整评价 | phys20 不得成为训练 target |
| `existing_lgbm` | 评价一个已经训练好的 LGBM | 从只读模型 metadata 恢复 features 与 train/valid；报告只保留 LGBM 评价 | 不得把 prediction 再画成“单因子”；不得修改源模型目录 |

所有 v3 调用都显式传 `report_mode`，不要靠 signal 数量猜模型 provenance。v2 暂只允许 `train_lgbm`。

`existing_lgbm_dir` 与 `reuse_lgbm` 不同：

- `existing_lgbm_dir`：外部只读源模型，供 `existing_lgbm` 使用。
- `reuse_lgbm`：复用当前报告版本自己的训练产物，只用于 `train_lgbm` 重跑。
- 两者不得同时传。

## 第二步：选择数据入口

- 单个 factor_set：CLI `python -m HftAnalyzer2 report-standard`。
- 多个 factor_set：Python 先 `build_multi_dataset_cache`，再 `generate_standard_report(reuse_cache=True)`。
- 已物化的 prediction-only 专项：可使用项目内受版本控制的 runner，但最终必须调用 v3 writer 且指定 `existing_lgbm`；禁止再构造一份 `stage=all` factor_results。

## 三种模式的最小命令

以下省略了已确认的 dataset、日期、资源和输出参数；补齐时严格按手册第 5 章顺序。

### 单原始因子

```bash
python -m HftAnalyzer2 report-standard \
  ... \
  --signals <one_raw_factor> \
  --report_mode single_factor
```

验收：场景评价对象只有一个原始 factor signal，四个 `segment × label_variant` block 均展示该 signal；完整配置、Axis Gate、Coverage、Corr、诊断和 legacy 入口仍保留；无 LGBM 训练信息、Feature Importance、LGBM 场景区块或 `lgbm_*` 表。

### 多因子训练 LGBM

```bash
python -m HftAnalyzer2 report-standard \
  ... \
  --signals <factor_a,factor_b,...> \
  --report_mode train_lgbm
```

验收：至少两个 features；新 `model.txt`、metadata、gain Top50 存在；train/valid 都非空。

### 已有单个 LGBM

若用户说“当前 SOTA”但没有给模型路径，先读取
`/home/cken/hft_projects/quant-workflows/workflows/hft/sota_snapshot.md` 解析当前指针；若指针不唯一或与用户指定版本冲突，停止并请用户确认，不得按目录时间猜测。用户只说“139 日”时也必须确认具体交易日集合；只有明确采用团队标准提交集时才使用 `20250102-20250730`。

先读 `<existing_lgbm_dir>/metadata.json`，按 `features` 原顺序填写 signals，并记录运行前的 `model.txt/metadata.json` hash 与 mtime。执行前做已有模型兼容性 Gate：

- metadata 的 `target/features/train_days/valid_days` 是必填硬门槛；target 必须是 baseline H100，而非 phys20。
- sampling/bar_col/downsample/Analyzer2/template version 若在 metadata 中存在，必须与本次 v3 口径兼容；若缺失，必须从受版本控制的 runner、原报告 metadata、cache manifest 或用户显式输入恢复并记录，不能猜测；最终无法证明兼容时停止。
- booster 内部 feature 数量、名称与顺序必须和 metadata.features 完全一致。
- metadata 必须足以恢复每个 feature 的数据来源；多 factor_set 若缺 DatasetSpec、prefix 或原始列映射，停止并要求显式提供，禁止只凭最终列名反推。
- train/valid 必须非空、互斥，并精确覆盖本次报告日期。若用户要求 metadata 之外的新 holdout/test 日期，当前模式不支持，必须 fail fast，不能静默归入 valid。
- 恢复并记录训练样本过滤条件；例如模型只在 `exchange_ts>=09:35` 训练时，opening 必须标明为训练窗外诊断，不能只靠 train/valid 日期推断。

```bash
python -m HftAnalyzer2 report-standard \
  ... \
  --signals <metadata.features in exact order> \
  --report_mode existing_lgbm \
  --existing_lgbm_dir /data/db/hft/model_output/<author>/<name>/<version>
```

验收：源模型 hash/mtime 前后不变；metadata 的 train/valid 非空、互斥且恰好覆盖报告日期；正文没有“单因子评价”；展示模型级 gain Feature Importance，但不得把单棵树或单个 prediction 冒充单因子分析。

## 多数据集合并（仅改变数据入口）

两个步骤必须复用同一组 `labels`、`sampling`、`factor_agg` 和 `scenario`。下面是参数骨架；DatasetSpec、路径和 LGBM 参数的完整初始化以手册第 6.2 节为准：

```python
from HftAnalyzer2 import AnalyzerConfig, FactorAggSpec, HftAnalyzer2, LabelSpec, LgbmConfig, SamplingSpec, ScenarioReportSpec

an = HftAnalyzer2(
    config=AnalyzerConfig(
        downsample_stride=1,
        io_workers=1,
        quantile_cut_mode="exact",
    ),
    verbose=True,
)

canonical_horizons = [1, 2, 3, 4, 5, 7, 10, 13, 16, 20, 25, 30, 40, 50, 75, 100, 150, 200]
labels = [
    LabelSpec("ret_lag0_next100", 0, 100),
    *[LabelSpec(f"ret_lag0_next{h}", 0, h) for h in canonical_horizons if h != 100],
]
sampling = SamplingSpec(mode="bar", bar_col="bar_aggtrans_time_1")
factor_agg = FactorAggSpec(sum_cols=())
scenario = ScenarioReportSpec()
selected_mode = "train_lgbm"  # 或 single_factor / existing_lgbm
existing_model = None          # existing_lgbm 时填写只读模型目录
signal_mapping = {
    d.name: {s: f"{d.prefix or ''}{s}" for s in signals_by_dataset[d.name]}
    for d in datasets
}
signals_out = [
    signal_mapping[d.name][s]
    for d in datasets
    for s in signals_by_dataset[d.name]
]

dates, coverage = an.build_multi_dataset_cache(
    ...,
    labels=labels,
    sampling=sampling,
    factor_agg=factor_agg,
    scenario_report=scenario,
    date_mode="intersection",
    reuse_cache=False,
)

manifest_path = report_dir / "cache" / "manifest_v3.json"
assert manifest_path.is_file()

report_md = an.generate_standard_report(
    ...,
    signals=signals_out,
    labels=labels,
    sampling=sampling,
    factor_agg=factor_agg,
    scenario_report=scenario,
    report_mode=selected_mode,
    existing_lgbm_dir=existing_model,
    reuse_cache=True,
    reuse_lgbm=False,
    coverage_pct_by_signal=coverage,
    lgbm_cfg=LgbmConfig(...),
    lgbm_name=lgbm_name,
    lgbm_version=lgbm_version,
    extra_meta={
        "multi_datasets": [d.__dict__ for d in datasets],
        "signals_by_dataset": signals_by_dataset,
        "signal_mapping": signal_mapping,
        "resolved_dates": dates,
        "date_mode": "intersection",
    },
)
```

使用 `date_mode=intersection`；每个 DatasetSpec 设置 prefix；`signals_by_dataset` 的 key 必须等于 DatasetSpec.name。禁止 `sum_cols`。cache 构建后必须读取并核验 `manifest_v3.json` 的 config、labels、signals、resolved dates 和 source identity；`extra_meta` 必须记录 DatasetSpec、原始 signals、原始→prefix 列映射及实际 resolved dates。`generate_standard_report` 所需的 dummy DatasetSpec 只是 cache API 适配器，不能被解释为真实数据来源。`report_version` 和两种 LGBM 模式的 `lgbm_version` 必须是新的唯一版本；新训练固定 `reuse_lgbm=False`。多数据集入口与报告对象正交：`single_factor` 合并后恰好一个 signal；`train_lgbm` 至少两个；`existing_lgbm` 还须传只读模型目录，并按模型 features 原顺序组装 signals。

## 资源配置

正式长窗先用 `io_workers=1`；提高前在独占资源上实测。大规模 parquet/LGBM 任务先启用 `memory-guard`，总 RSS 硬上限 400GB。workers 估算与推荐值以手册第 11.1 节为准，不在 skill 中复制易漂移的旧数值。

## 强制报告验收矩阵

不能只检查 `img/` 非空。逐个检查机器表有行、Markdown 有引用、引用文件存在。

### 场景 × label 完整性

- 所有模式：`opening`、`intraday` × `baseline`、`phys20`。
- 两种 LGBM 模式：上述维度再乘 `train`、`valid`，两者均非空。
- window 诊断保留 `am_open/am_intraday/pm_reopen/pm_intraday/closing_diag`。

### 每个场景必须出现

| 指标 | 图形 |
|---|---|
| Daily IC / RankIC + cumsum | 折线图 |
| Grouped Return | 柱状图 |
| Net Grouped Return | 柱状图 |
| IC / RankIC Decay | 折线图 |
| Price Path（全 horizons） | 折线图 |
| Top0.1% / Top0.01% TS + cumsum（LGBM） | 折线图 |

报告正文必须直接展示 phys20 与 intraday 的 Grouped/Net/Decay/Price Path 图片，但沿用历史标准，不在图片前重复展开这些图的原始数值表。完整数值必须保存在 `metrics/`，且对应机器表非空。

机器表至少检查 `daily_ic/grouped_return/net_grouped_return/ic_decay/price_path/top_group_ts`；LGBM 使用对应 `lgbm_*`。维度必须包含适用的 `aggregation_level/segment/window_id/label_variant/stage/n_obs/n_days`。因子评价固定 `stage=all`，只有两种 LGBM 模式要求 train/valid。`group_quantiles` 必须等于手册/`DEFAULT_GROUP_QUANTILES`，图和表按 `bucket_id` 排序。Price Path 的 baseline horizon 集必须精确等于本 skill 的 `canonical_horizons`，phys20 与其逐一对应；当前运行时只校验 baseline/phys20 成对，不能把“程序未报错”当作全 horizons 验收。

### 历史展示兼容性

除所选模式明确要求增删的评价对象区块外，其他标准报告章节与格式必须保持历史口径：

- 配置区展示完整 JSON，不得压缩成会混淆 dataset、prediction signal 与 model features 的简表；metadata 显式记录 `report_mode`。
- 场景章节前依次保留 Axis Alignment Gate、Coverage、全局 Corr Heatmap、完整 LGBM train/valid metadata（exact dates、样本量、features、params）和 gain Feature Importance。
- 阅读顺序保持“开盘 baseline→phys20，盘中 baseline→phys20，window/尾盘诊断，overall+baseline 兼容入口”。
- `existing_lgbm` 只删除重复的 factor summary/detail/图片/机器表；全局 Corr、模型信息、importance、诊断和兼容入口不得随之删除。
- `report_legacy_v2.md` 与根目录 legacy parquet 保持 overall+baseline 历史 schema；train/valid 场景数据继续放在 `metrics/lgbm_*`。

### Reference 差分回归 Gate

只有修改报告模式、模板或 writer 实现时，才执行本节；常规使用既有稳定实现生成新报告不要求逐字节 reference diff。实施修改时先指定最后一份已接受报告作为 reference。允许差异只能来自用户明确要求；本次允许项是三模式分流与 existing 去重、LGBM Grouped/Net 折线改柱状、补齐 phys20/intraday 产物，以及正文移除 Grouped/Net/Decay/Price Path plot-data 数值表。

- 非 allowlist 的 metrics 和根 legacy 表必须逐字节一致，或通过 schema + 数值完全一致验证。
- 非 allowlist 图片必须逐字节一致；所有图片尺寸保持一致。
- metadata 的数据范围、sampling、labels、cuts、成本与 train/valid 口径必须一致；只允许新增明确的 mode/provenance 字段和动态输出路径。
- 源模型 hash/mtime 必须不变。出现任何其他差异立即停止并解释，禁止顺手压缩 metadata、删除全局章节或“优化展示”。

### 模式互斥验收

- `single_factor`：四个场景-label block 的评价对象均为同一个原始 factor；保留历史全局章节，无 LGBM 区块、模型、Feature Importance、`lgbm_*`。
- `train_lgbm`：因子 overview 与 LGBM 均有；模型 target 是 baseline H100；gain Top50 为横向柱状图。
- `existing_lgbm`：只有 LGBM train/valid 场景区块，无 factor summary/detail、factor 图片或 factor metrics；全局 Corr Heatmap 仍按历史标准保留，但不视为单因子区块；展示源模型的 gain Feature Importance；源模型不变。

### phys20 额外验收

- Grouped、Net Grouped、Price Path 在 opening/intraday 下均非空；两种 LGBM 模式再要求 train/valid 均非空。
- baseline/phys20 在同一 stage × segment 共用 cuts。
- 净收益扣执行时点 spread；`evaluation_only=true`。
- Price Path horizons 与 baseline 完整一致。

## 持久化交付

报告、metadata、图片、根表、`metrics/`、profiling、复现 runner 和模型/importance（适用时）使用 `cp -L` 物理复制进对应 HFTPool 目录。两种 LGBM 模式都必须把 `model.txt`、模型 `metadata.json` 和 importance 物理快照到 `saved_model/` 并校验 hash；模型 metadata 不自带完整 sampling/DatasetSpec/source mapping，复现必须联合报告 metadata、cache manifest 与受版本控制 runner。禁止复制 `cache/*.parquet` 和 `memmap/`，但必须把权威 `cache/manifest_v3.json` 单独 `cp -L` 到 `provenance/cache_manifest_v3.json`，校验 SHA256，并在持久化 metadata 记录相对路径、hash 与原始来源；rerender 报告应快照其明确的 source report manifest，不能重建或猜测。找不到权威 manifest 时停止交付。`existing_lgbm` 还必须在报告 metadata 记录只读源路径与 hash，只允许从源目录读取，绝不能回写。复制后执行 `find <persist_dir> -type l`，结果必须为空；解析 `report.md` 的全部图片引用并确认文件存在。
