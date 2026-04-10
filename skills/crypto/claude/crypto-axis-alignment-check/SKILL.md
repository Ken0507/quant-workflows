---
name: crypto-axis-alignment-check
description: "检查因子输出与 f001 baseline 的 Join 轴对齐与 bar 覆盖情况。用于 smoke test 后、大规模刷数前的验证。检查 3-5 天全 symbol 数据，要求 join 成功率与 bar 覆盖率均 >= 99.9%，无重复 bar。"
metadata:
  short-description: "因子轴对齐检查"
  argument-hint: "[factor_root] [factor_sub] [dates]"
---

# Crypto 因子轴对齐检查

> 验证新因子集输出与 f001 baseline 在 `(symbol, bar_id, close_time_ms)` 三元组上的严格对齐。

## 0. 背景

Zebra 框架保证：**相同 threshold + 相同 trade 数据 = 相同 bar grid**。只要新因子集和 f001 使用相同的动态阈值文件，它们的 `(symbol, bar_id, close_time_ms)` 应该严格一一对应。

本检查验证这一不变量。如果不通过，说明新因子的 bar 构建配置有问题（如 threshold 不同、bar builder 参数不同、数据源不同）。

## 1. 前置条件

- f001 baseline 已为目标日期刷完：`/data/db/crypto/futures/world/world_pool/f001/{YYYY-MM-DD}/base30_v1/{SYMBOL}.parquet`
- 新因子集已刷完 smoke test 日期（至少 3-5 天，建议覆盖 7 个 symbol）

## 2. 执行

```bash
cd /home/cken/crypto_world/zebra

python scripts/axis_alignment_check.py \
    --factor-root /data/db/crypto/futures/world/world_pool/${fa_lower} \
    --factor-sub ${fa_lower}_v1 \
    --f001-root /data/db/crypto/futures/world/world_pool/f001 \
    --f001-sub base30_v1 \
    --dates 2026-01-15,2026-01-16,2026-01-17 \
    --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT
```

## 3. 通过标准

| 指标 | 阈值 | 含义 |
|------|------|------|
| `join_ratio` | >= 99.9% | 新因子的每行在 f001 中都能找到匹配 |
| `bar_coverage` | >= 99.9% | f001 的每根 bar 在新因子中都有对应行 |
| `dup_cnt` | == 0 | 新因子中无重复的 `(symbol, bar_id)` |

**所有 (date, symbol) 组合都必须 PASS。** 任何一个 FAIL 都应排查。

## 4. 常见失败原因

| 现象 | 可能原因 | 排查 |
|------|---------|------|
| join_ratio < 100% 但 > 99% | 新因子多了几行 f001 没有的 bar | 检查 is_day_boundary 行为是否一致 |
| bar_coverage < 100% 但 > 99% | 新因子少了几根 bar（可能漏输出） | 检查 OnBarClose 是否对所有 bar 都写了 AddRowFast |
| join_ratio = 0% | threshold 或数据源完全不匹配 | 检查 --threshold-dir 参数是否一致 |
| dup_cnt > 0 | Agent 在同一个 bar 里多次调用 AddRowFast | 检查 OnBarClose 逻辑 |
| MISSING_FACTOR | 新因子未刷该日期/symbol | 先刷因子 |
| MISSING_F001 | f001 未刷该日期/symbol | 先刷 f001 |

## 5. 注意事项

- **per-day bar reset**：bar_id 每天从 0 重置，每天最后一根 bar 为 partial（`is_day_boundary=true`）。只要新因子和 f001 都使用 per-day reset，这根 partial bar 也会对齐。
- **chunk 模式不影响 bar grid**：chunk 模式只影响 Agent 状态持久化，bar builder 仍然 per-day reset。因此不同 chunk 划分产出的 bar grid 是一致的。
- **检查天数**：建议 3-5 天，覆盖工作日/周末、活跃/平静市场。不需要全量检查——bar grid 的确定性保证了：3 天全 PASS = 全量 PASS。
