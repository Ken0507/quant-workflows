# 任务：修复 basic_table join 轴口径问题

## 问题背景

FactorAgent6 在 Step2 强验证时发现：按文档写出的因子无法与 `basic_table` join。

**根因**：
1. `basic_table.time` 实际是 `event.local_ts + 8h(ns)`，而文档说 `time = event.local_ts`
2. `basic_table.md_id` 实际是 `biz_index`，而文档示例用 `GetMdId()`（优先seq）

**影响范围**：所有按文档/Skill 写因子的 agent 都会踩这个坑，导致返工。

---

## 修复方案评估

### 方案A：修改文档（保持 basic_table 不变）

**优点**：
- 不需要重刷 basic_table 数据
- 不影响已有的下游数据集

**缺点**：
- 维护"历史包袱"，新研究员容易困惑
- `kLegacyLocalTsOffsetNs` 命名暗示这是应该被修正的历史口径
- 与 SDK 模板不一致

**工作量**：约1小时（修改文档）

### 方案B：修改 basic_table 代码 + 重刷数据（推荐）

**优点**：
- 消除历史包袱，文档与实现一致
- 与 SDK 模板一致
- 长期维护成本更低

**缺点**：
- 需要重刷 basic_table 全历史数据
- 可能影响已有的下游数据集（如 baseline top80 的因子集）

**工作量**：约 2-4 小时（代码修改 + 重刷 + 验证）

---

## 执行方案：方案A（已确认）

**决策时间**：2026-01-23
**决策结果**：选择方案A - 修改文档，暂不修正 basic_table

考虑到：
1. 目前有多个 Agent 的因子已经按历史口径刷入
2. baseline top80 依赖这些数据
3. 重刷成本较高
4. Analyzer2 已有智能对齐机制，能自动处理时间轴差异

**当前执行**：方案A - 修改文档，明确推荐使用 `GetMdId()` 和 `local_ts`
**方案B（统一修正 basic_table）**：后续由用户另行安排时间统一修复

---

## 任务清单（方案A - 短期修复）

**执行状态**：2026-01-23 已完成

| Task | 状态 | 说明 |
|------|------|------|
| Task 1 | ✅ 完成 | 在 data.md 新增第 8 章「与 basic_table 的 Join 轴对齐」 |
| Task 2 | ✅ 完成 | 在 factor_workflow.md 添加轴对齐说明 |
| Task 3 | ✅ 完成 | 更新 hft-playground-factor-write SKILL.md |
| Task 4 | ✅ 完成 | 更新 FA7/FA8/FA_prompt_v3 Prompt 模板 |
| Task 5 | ✅ 完成 | 新增 `hft-axis-alignment-check` Skill（独立检查工具） |
| 额外 | ✅ 完成 | 更新 hft-analyzer2-standard-report SKILL.md 添加内存估算 |
| 额外 | ✅ 完成 | 更新 analyzer_user_manual.md 添加 workers 与内存估算指导 |

---

### Task 1: 修改 data.md

**文件**：`/home/cken/hft_projects/HftKnowledge/research_docs/data.md`

**修改内容**：

1. 在"7) 常见坑"章节后新增章节：

```markdown
## 8) 与 basic_table 的 Join 轴对齐（关键！必读）

Analyzer2 的核心分析依赖 `(code, time, md_id)` 三个字段与 basic_table join。**如果你的因子输出与 basic_table 不对齐，所有分析结果将不可用或严重失真。**

### 8.1 当前 basic_table 口径（历史遗留，必须遵守）

| 字段 | 定义 | 说明 |
|------|------|------|
| `time` | `event.local_ts + 28800000000000(ns)` | 加了8小时偏移（历史遗留） |
| `md_id` | `event.order/trans.biz_index` | 直接使用 biz_index，不是 GetMdId() |

### 8.2 你的因子必须这样写

```cpp
// 常量定义
static constexpr int64_t kLegacyLocalTsOffsetNs = 28800000000000LL;  // 8h in ns

// 在 OnMarketEvent 中
void OnMarketEvent(const hft::MarketEvent& event) override {
    // time: 必须加偏移
    const int64_t time = event.local_ts + kLegacyLocalTsOffsetNs;

    // md_id: 必须用 biz_index
    int64_t md_id = 0;
    if (event.order) md_id = event.order->biz_index;
    else if (event.trans) md_id = event.trans->biz_index;

    // 输出
    store_.AddRow(event.code, time, ..., i64_cols, ...);
}
```

### 8.3 轴对齐检查（强制 gate）

**在 Step1 smoke test 后、大规模刷数前，必须做一次轴对齐检查**：

```python
import pandas as pd

# 读取你的因子输出
factor = pd.read_parquet("<your_factor>/20250102/Agent/*.parquet")

# 读取 basic_table
basic = pd.read_parquet(
    "/data/db/hft/factor_pool/debug/basic_data/basic_table/20250102/TickFeatureAgent/basic_table_basic_table.parquet"
)

# 计算 overlap
overlap = pd.merge(
    factor[["code","time","md_id"]],
    basic[["code","time","md_id"]],
    how="inner"
)

ratio = len(overlap) / len(factor) if len(factor) > 0 else 0
print(f"factor rows: {len(factor)}")
print(f"basic rows: {len(basic)}")
print(f"overlap rows: {len(overlap)}")
print(f"overlap ratio: {ratio:.6f}")

# 阈值检查
assert ratio >= 0.999, f"Axis alignment failed! overlap ratio = {ratio:.6f} < 0.999"
print("✓ Axis alignment check PASSED")
```

如果 overlap ratio < 0.999，**停止并检查 time/md_id 的定义**。
```

2. 修改第29行原有说明，添加警告：

原文：
```
时间轴只用 `event.local_ts`
```

改为：
```
时间轴基于 `event.local_ts`，但 **注意**：为与 basic_table 对齐，实际输出需要加 8h 偏移，见第 8 章。
```

3. 修改第62-65行 md_id 示例代码：

原代码：
```cpp
int64_t md_id = 0;
if (event.order) md_id = event.order->GetMdId();
else if (event.trans) md_id = event.trans->GetMdId();
```

改为：
```cpp
// md_id: 必须用 biz_index 以与 basic_table 对齐
int64_t md_id = 0;
if (event.order) md_id = event.order->biz_index;
else if (event.trans) md_id = event.trans->biz_index;
```

---

### Task 2: 修改 factor_workflow.md

**文件**：`/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md`

**修改内容**：

在 "3.1 时间轴：统一用 `event.local_ts`" 后添加警告：

```markdown
> ⚠️ **重要**：虽然回放驱动用 local_ts，但 basic_table 的 `time` 字段实际是 `local_ts + 8h(ns)`（历史遗留口径）。
> 为保证 Analyzer2 join 正确，你的因子输出必须加偏移：`time = event.local_ts + 28800000000000LL`。
> 详见 `data.md` 第 8 章"与 basic_table 的 Join 轴对齐"。
```

---

### Task 3: 修改 Skills

**文件1**：`/home/cken/.codex/skills/hft-playground-factor-write/SKILL.md`

**修改内容**：

将第21行：
```
- 输出时间轴统一用 `event.local_ts`（Parquet 的 `time`）
```

改为：
```
- 输出时间轴需与 basic_table 对齐：`time = event.local_ts + 28800000000000(ns)`（注意：不是纯 local_ts，详见 data.md 第8章）
```

将第25行：
```
- `md_id` 统一用 `GetMdId()`（order/trans，跨表口径更一致；不保证全局唯一主键）
```

改为：
```
- `md_id` 需与 basic_table 对齐：使用 `event.order/trans.biz_index`（不是 GetMdId()，详见 data.md 第8章）
```

---

### Task 4: 修改 Agent Prompt 模板

**文件**：`/home/cken/hft_projects/HFTPool/factor_agent_docs/` 下的 prompt 模板

**建议在"硬性规范"章节添加**：

```markdown
- **轴对齐（与 basic_table）**：
  - `time = event.local_ts + 28800000000000(ns)`（必须加8小时偏移）
  - `md_id = event.order/trans.biz_index`（不是 GetMdId()）
  - Step1 smoke test 后必须做轴对齐检查（overlap ratio >= 0.999）
```

---

### Task 5: 添加轴对齐检查脚本（可选但推荐）

**新建文件**：`/home/cken/hft_projects/HFTPool/scripts/check_axis_alignment.py`

```python
#!/usr/bin/env python3
"""
轴对齐检查脚本：验证因子输出与 basic_table 的 (code, time, md_id) 对齐情况。
用法：python check_axis_alignment.py <factor_parquet_path>
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

BASIC_TABLE_ROOT = Path("/data/db/hft/factor_pool/debug/basic_data/basic_table")

def main():
    parser = argparse.ArgumentParser(description="Check axis alignment with basic_table")
    parser.add_argument("factor_path", type=Path, help="Path to factor parquet file")
    parser.add_argument("--threshold", type=float, default=0.999, help="Minimum overlap ratio (default: 0.999)")
    args = parser.parse_args()

    # 推断日期
    parts = str(args.factor_path).split("/")
    date_str = None
    for p in parts:
        if len(p) == 8 and p.isdigit():
            date_str = p
            break
    if not date_str:
        print(f"ERROR: Cannot infer date from path: {args.factor_path}")
        return 1

    basic_path = BASIC_TABLE_ROOT / date_str / "TickFeatureAgent" / "basic_table_basic_table.parquet"
    if not basic_path.exists():
        print(f"ERROR: basic_table not found: {basic_path}")
        return 1

    factor = pd.read_parquet(args.factor_path)
    basic = pd.read_parquet(basic_path)

    required_cols = {"code", "time", "md_id"}
    if not required_cols <= set(factor.columns):
        print(f"ERROR: factor missing columns: {required_cols - set(factor.columns)}")
        return 1

    overlap = pd.merge(
        factor[["code", "time", "md_id"]],
        basic[["code", "time", "md_id"]],
        how="inner"
    )

    ratio = len(overlap) / len(factor) if len(factor) > 0 else 0

    print(f"Date: {date_str}")
    print(f"Factor rows: {len(factor)}")
    print(f"Basic rows: {len(basic)}")
    print(f"Overlap rows: {len(overlap)}")
    print(f"Overlap ratio: {ratio:.6f}")

    if ratio >= args.threshold:
        print(f"✓ PASSED (ratio >= {args.threshold})")
        return 0
    else:
        print(f"✗ FAILED (ratio < {args.threshold})")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 任务清单（方案B - 长期修复，可选）

如果决定执行方案B（统一修正 basic_table），需要：

### Task B1: 修改 basic_table 代码

**文件**：`/home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table/tick_feature_agent.hpp`

**修改内容**：

1. 删除或注释第180行的偏移常量：
```cpp
// static constexpr int64_t kLegacyLocalTsOffsetNs = 28800000000000LL;  // REMOVED
```

2. 修改第110行：
```cpp
// 原: const int64_t time = event.local_ts + kLegacyLocalTsOffsetNs;
const int64_t time = event.local_ts;  // 不再加偏移
```

3. 修改 ExtractMdId 函数（第204-207行）：
```cpp
static int64_t ExtractMdId(const hft::MarketEvent &event) {
    if (event.order) return event.order->GetMdId();
    if (event.trans) return event.trans->GetMdId();
    return 0;
}
```

### Task B2: 重刷 basic_table 全历史

```bash
cd /home/cken/hft_projects/HFTPool/pool/basic_data/code
# 备份旧数据
mv /data/db/hft/factor_pool/debug/basic_data/basic_table /data/db/hft/factor_pool/debug/basic_data/basic_table_legacy_20260123
# 重刷
ENV=debug FACTOR_SET_NAME=basic_table START_DATE=20250102 END_DATE=20250730 N_JOBS=48 bash run_all.sh
```

### Task B3: 更新 Analyzer2 兼容层（如需）

检查 Analyzer2 的 `_infer_time_key` 函数是否需要调整。

### Task B4: 通知所有 Agent 重刷因子

需要通知 Agent1-Agent6 等所有已刷数据的 agent 重新刷取（如果他们用了旧口径）。

---

## 验收标准

### 方案A 验收

1. 文档修改已合并
2. 新写的因子能通过轴对齐检查（overlap ratio >= 0.999）
3. 现有 agent（如 FactorAgent6）的因子能正常生成 Analyzer2 报告

### 方案B 验收

1. 代码修改已合并
2. basic_table 重刷完成，QC 通过
3. Analyzer2 能正常 join 新的 basic_table
4. 所有下游 agent 因子重刷完成

---

## 时间估算

- **方案A（短期）**：1-2 小时
- **方案B（长期）**：4-8 小时（含重刷和验证）

---

## 建议执行顺序

1. **立即执行 Task 1-4**（方案A），解决文档与实现不一致的问题
2. 在下一个迭代周期讨论是否执行方案B
3. 如果执行方案B，需要在周末或低峰期进行

---

## 附录：basic_table 关键代码位置

| 文件 | 行号 | 说明 |
|------|------|------|
| tick_feature_agent.hpp | 110 | time 定义 |
| tick_feature_agent.hpp | 180 | 8小时偏移常量 |
| tick_feature_agent.hpp | 204-207 | md_id 定义 |
