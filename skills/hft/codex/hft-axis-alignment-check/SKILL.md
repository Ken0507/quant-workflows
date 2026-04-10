---
name: hft-axis-alignment-check
description: "当用户要检查因子输出与 basic_table 的 Join 轴与 bar 覆盖情况时使用；用于 smoke test 后、大规模刷数前的验证；检查 3-5 天全 code 数据，要求 join 成功率与 bar 覆盖率均 >= 99.9%。"
---

# HFT 轴对齐检查（Factor ↔ basic_table Join 验证）

## 适用场景

- Step1 smoke test 通过后、大规模刷数前
- 新因子开发完成后的验证
- 排查 Analyzer2 join ratio 异常问题

## 强制前置阅读

1) 打开并通读：`/home/cken/hft_projects/HftKnowledge/research_docs/data.md` 第 8 章「与 basic_table 的 Join 轴对齐」
2) 确认因子代码使用了正确的轴定义：
   - `time = event.local_ts`（必须与 basic_table 同口径）
   - `md_id = biz_index`（order/trans，必须与 basic_table.md_id 同口径）

## 检查要求

| 项目 | 要求 |
|------|------|
| 数据范围 | 3-5 天全 code 数据（约定：全 code == `bond_sz`） |
| Join 成功率阈值 | >= 99.9%（Factor 行能 join 到 basic_table） |
| Bar 覆盖率阈值 | >= 99.9%（每个 `(code, bar_aggtrans_time_1)` 必须恰好 1 行） |
| 检查维度 | `(code, time, md_id)` Join + `bar_aggtrans_time_1` 覆盖/去重 |

## 必须向用户确认的参数

- 因子输出路径：`factor_root`（例如 `/data/db/hft/factor_pool/debug/Agent1/my_factor_set`）
- 检查日期列表：`dates`（例如 `["20250102", "20250103", "20250106"]`）
- basic_table 路径：默认 `/data/db/hft/factor_pool/debug/basic_data/basic_table`

## 检查脚本（Python，推荐按日跑，内存更稳）

```python
import pandas as pd
from pathlib import Path
from glob import glob

# === 用户配置 ===
factor_root = "<your_factor_root>"  # 例如 /data/db/hft/factor_pool/debug/Agent1/my_factor_set
dates = ["20250102", "20250103", "20250106"]  # 3-5 天
basic_root = "/data/db/hft/factor_pool/debug/basic_data/basic_table"
BAR_COL = "bar_aggtrans_time_1"
UNIVERSE_FILE = "/data/share/dev/hft/config/universe_bond_sz.txt"  # 约定：全 code == bond_sz

THRESH_JOIN = 0.999
THRESH_BAR_COVERAGE = 0.999

def list_factor_files(date: str):
    pattern = f"{factor_root}/{date}/*/*.parquet"
    return sorted(glob(pattern))

def read_factor_keys(files):
    # bar-sampled 因子：通常 rows 更少；只读 Join Key（如果你额外输出了 bar_id，也可以一并读出来做一致性检查）
    cols = ["code", "time", "md_id"]
    return pd.concat([pd.read_parquet(f, columns=cols) for f in files], ignore_index=True)

def read_basic_table(date: str):
    # basic_table 通常是单文件：.../TickFeatureAgent/basic_table_basic_table.parquet
    pattern = f"{basic_root}/{date}/TickFeatureAgent/*.parquet"
    files = sorted(glob(pattern))
    if not files:
        raise FileNotFoundError(f"No basic_table parquet found: {pattern}")
    df = pd.read_parquet(files[0], columns=["code", "time", "md_id", BAR_COL])
    # 约定：全 code == bond_sz（避免 basic_table 含额外 code 导致 bar_coverage 虚假失败）
    codes = [ln.strip() for ln in Path(UNIVERSE_FILE).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]
    df = df[df["code"].astype(str).isin(set(codes))].copy()
    return df

def run_one_day(date: str):
    factor_files = list_factor_files(date)
    if not factor_files:
        raise FileNotFoundError(f"No factor parquet found: {factor_root}/{date}")

    factor = read_factor_keys(factor_files)
    basic = read_basic_table(date)

    # md_id=-1 视为占位：不参与 Join/对齐统计
    factor = factor[factor["md_id"] != -1].copy()
    basic = basic[basic["md_id"] != -1].copy()

    factor_unique = factor[["code", "time", "md_id"]].drop_duplicates()

    # Join factor -> basic_table，拿到 bar_id
    joined = factor_unique.merge(basic[["code", "time", "md_id", BAR_COL]], how="left", on=["code", "time", "md_id"])

    join_ok = joined[BAR_COL].notna().sum()
    join_ratio = (join_ok / len(factor_unique)) if len(factor_unique) > 0 else 0.0

    # bar_id 必须是有效值（>=0），否则说明你没有按 gated 条件输出，或 bar 口径不一致
    joined_valid = joined[joined[BAR_COL].ge(0)].copy()

    # Bar 覆盖：basic_table 里所有有效 bar（unique (code,bar_id)）都应该在 factor 里出现且仅 1 行
    expected_bars = basic[basic[BAR_COL].ge(0)][["code", BAR_COL]].drop_duplicates()
    actual_bars = joined_valid[["code", BAR_COL]].drop_duplicates()

    bar_coverage = (len(actual_bars) / len(expected_bars)) if len(expected_bars) > 0 else 0.0

    dup_cnt = (
        joined_valid.groupby(["code", BAR_COL]).size().gt(1).sum()
        if len(joined_valid) > 0 else 0
    )

    print(f"\n=== {date} ===")
    print(f"Factor unique rows: {len(factor_unique):,}")
    print(f"Join ok rows: {join_ok:,} / {len(factor_unique):,} (join_ratio={join_ratio:.6f})")
    print(f"Expected bars (basic_table): {len(expected_bars):,}")
    print(f"Actual bars (factor): {len(actual_bars):,} (bar_coverage={bar_coverage:.6f})")
    print(f"Duplicate (code,bar_id) in factor: {dup_cnt:,}")

    if join_ratio < THRESH_JOIN:
        bad = joined[joined[BAR_COL].isna()].head(20)
        print("\n❌ FAILED: join_ratio too low. Sample missing joins:")
        print(bad.to_string(index=False))
        raise AssertionError(f"join_ratio={join_ratio:.6f} < {THRESH_JOIN}")

    if bar_coverage < THRESH_BAR_COVERAGE:
        miss = expected_bars.merge(actual_bars, how="left", indicator=True).query("_merge=='left_only'").head(20)
        print("\n❌ FAILED: bar_coverage too low. Sample missing (code,bar_id):")
        print(miss.to_string(index=False))
        raise AssertionError(f"bar_coverage={bar_coverage:.6f} < {THRESH_BAR_COVERAGE}")

    if dup_cnt > 0:
        print("\n❌ FAILED: duplicated (code,bar_id) detected in factor output.")
        raise AssertionError(f"dup_cnt={dup_cnt} > 0")

    print("✅ PASSED")

for d in dates:
    run_one_day(d)

print("\n轴对齐 + bar 覆盖检查通过，可以进行大规模刷数。")
```

## 检查流程

1. **确认因子输出存在**：检查 `factor_root/{date}/` 目录下有 parquet 文件
2. **运行检查脚本**：使用上述 Python 脚本
3. **分析结果**：
   - ✅ PASSED：join 成功率与 bar 覆盖率均通过，可以进行大规模刷数
   - ❌ FAILED：优先检查 `time/md_id` 口径、gated 条件、以及 `bar_aggtrans_time_1` 计算是否与 basic_table_v3 一致

## 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| join_ratio < 99.9% | time/md_id 口径错误或输出被过滤 | 检查 `time=event.local_ts`、`md_id=biz_index`，以及是否在采样点输出 |
| bar_coverage < 99.9% | 采样点不一致 / bar 切分不一致 | 确认 `AggTransTimeCutter` 与 basic_table_v3 完全一致，且采样规则是 “bar_last + is_continuous&&is_session_end” |
| (code,bar_id) 有重复 | 同一 bar 输出多行 | 按 bar 切换 flush 时输出；同一 bar 仅保留最后一条 |
| 找不到 factor 文件 | 路径错误或未刷数 | 确认 factor_root 路径和日期 |
| basic_table 文件缺失 | basic_table 未刷该日期 | 检查 basic_table 是否包含所需日期 |

## 与其他 Skill 的关系

- **hft-playground-factor-write**：因子开发时需要使用正确的 md_id 定义
- **hft-playground-factor-batch-run**：smoke test 后、大规模刷数前调用本 skill
- **hft-analyzer2-standard-report**：若 join ratio 异常，可用本 skill 诊断

## 注意事项

- 本检查按 `(code, time, md_id)` 直接验证 Join 轴；这是 Analyzer2 下游分析的必要条件
- 3-5 天数据足以发现系统性问题，无需全量数据
- 若 `join_ratio` / `bar_coverage` 介于 99.0%-99.9%，建议人工分析 missing pairs / missing bars 再决定是否继续
