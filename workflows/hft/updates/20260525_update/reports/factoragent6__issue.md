# FactorAgent6 Issue 记录

（按要求：若流程中出现阻塞/不确定点，记录时间(UTC+8)、问题、影响范围与临时处理。）

[2026-01-23 03:55:35 UTC+8]
- 问题：强验证 axis spot-check 发现与 `basic_table` 的 `(time,md_id)` key-set 完全不重合；抽样确认 `basic_table.time = factor.time + 28800000000000(ns)`（8 小时偏移）。
- 影响范围：若不修正 time 轴，将导致 Analyzer2 / basic_table join 失败（coverage/IC/LGBM 等分析不可用或严重失真）。
- 临时处理：将因子输出 `time` 改为 `event.local_ts + 28800000000000`（仍以 local_ts 为基准，保持与历史 basic_table 口径一致），并重刷 1 个月验证数据与重跑 validate/p2p。

[2026-01-23 05:36:56 UTC+8]
- 问题：Step3.2 生成 Analyzer2 新因子集报告时，读取 factorset `factor_agent_006` 的 `20250716` 因子 parquet 报错：`Parquet magic bytes not found in footer`（文件损坏/非 parquet）。
- 影响范围：Analyzer2 cache 构建失败，导致 Step3.2 报告无法产出；同时提示全历史 factorset 中存在潜在“落盘未完整”的风险。
- 临时处理：
  - 删除损坏日目录：`/data/db/hft/factor_pool/debug/FactorAgent6/factor_agent_006/20250716`
  - 使用 Playground 对 `20250716` 单日做补刷并复核 parquet 可读性
  - 复用已生成的 Analyzer2 cache（`--reuse_cache`）重跑 Step3.2 标准报告
