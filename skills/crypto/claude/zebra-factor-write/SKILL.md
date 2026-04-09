---
name: crypto-zebra-factor-write
description: "按 FA*_factor_list.md 文档在 Zebra 框架中实现 C++ 因子 Agent。处理工作目录初始化（从 factor_template 复制）、Agent 编码（trade-only + OrderBook 因子）、编译、smoke test。"
metadata:
  short-description: "Zebra C++ 因子 Agent 实现"
  argument-hint: "[factor_list.md 路径]"
---

# Zebra C++ 因子 Agent 实现

> 从 `FA*_factor_list.md` 出发，在 Zebra 框架中完成 C++ 因子 Agent 的工作目录初始化、编码、编译、smoke test。

---

## 0. 参数解析与初始化

### 0.1 解析输入

输入：factor_list 文件路径（如 `zebra_pool/factor_agent_docs/FA03_factor_list.md`）

```bash
DOC_PATH="$1"
FA_ID=$(basename "$DOC_PATH" | sed 's/_factor_list\.md//')   # e.g. FA03
fa_prefix=$(echo "$FA_ID" | tr 'A-Z' 'a-z')_                # e.g. fa03_
fa_lower=$(echo "$FA_ID" | tr 'A-Z' 'a-z')                  # e.g. fa03
WORKSPACE="/home/cken/crypto_world/zebra_pool/${fa_lower}"
```

### 0.2 读取 factor_list 文档

**立即完整阅读** `$DOC_PATH`，提取：
- 因子总数（`FACTOR_COUNT`）
- 因子前缀（确认与解析一致）
- 所有因子名列表
- 因子类别（trade-only / OB snapshot / L2 event / mixed）
- 如有 §0 溯源路径 → 记下，遇到疑问时回溯原始研究报告

### 0.3 读取工程文档（Hard Gate）

**编码前必须通读以下文档，不得凭记忆执行：**

1. `/home/cken/crypto_world/zebra/docs/crypto_factor_workflow.md` — 全文通读
2. `/home/cken/crypto_world/zebra/docs/研究员使用手册.md` — 重点 §7（AggTrans 字段）、§8（OrderBook API）

通读后复述关键硬规则：
- Join key = `(symbol, bar_id, close_time_ms)`，前三列由框架写入
- `factor_group_name()` = 分配的因子集 ID（如 `${fa_lower}_v1`）
- 所有列名 `${fa_prefix}_xxx`，纯 ASCII 小写 + 数字 + 下划线
- `OnAggTrans` 做计算，`OnBarClose` 只做落盘 + reset
- Chunk 模式：EMA/rolling 状态**不在** `OnDayStart` 重置；仅 bar 内累计量在 `OnBarClose` 末尾重置
- OB 访问前必须 `ctx.HasBook()` 守卫
- 禁止输出 NaN/Inf，使用 schema default
- 使用 `AddRowFast` + 预取 `ColumnHandle`

### 0.4 初始化工作目录

```bash
cp -r /home/cken/crypto_world/zebra_pool/factor_template \
      /home/cken/crypto_world/zebra_pool/${fa_lower}/code
```

目录结构：
```
zebra_pool/${fa_lower}/
├── code/           # C++ 源码（从 factor_template 复制）
│   ├── CMakeLists.txt
│   ├── src/
│   │   ├── factor_agent.hpp  → 重命名为 ${fa_lower}_agent.hpp
│   │   └── factor_main.cpp   → 重命名为 ${fa_lower}_main.cpp
│   └── build/
└── report/         # Analyzer 输出（后续生成）
```

### 0.5 重命名

1. **源文件**：
   - `src/factor_agent.hpp` → `src/${fa_lower}_agent.hpp`
   - `src/factor_main.cpp` → `src/${fa_lower}_main.cpp`

2. **Agent 类**（在 `${fa_lower}_agent.hpp` 中）：
   - 类名：`TemplateFactorAgent` → `${FA_ID}FactorAgent`
   - `name()` 返回 `"${FA_ID}FactorAgent"`
   - `factor_group_name()` 返回 `"${fa_lower}_v1"`

3. **Main 文件**（在 `${fa_lower}_main.cpp` 中）：
   - `#include "factor_agent.hpp"` → `#include "${fa_lower}_agent.hpp"`
   - `TemplateFactorAgent` → `${FA_ID}FactorAgent`

4. **CMakeLists.txt**：
   - `project(template_factor ...)` → `project(${fa_lower}_factor ...)`
   - `run_template_factor` → `run_${fa_lower}_factor`（所有出现处）
   - `src/factor_main.cpp` → `src/${fa_lower}_main.cpp`

---

## 1. 因子实现规范

### 1.1 因子分类与实现模式

读取 factor_list §3 因子定义，按类型实现：

**Trade-only 因子**（不需要 OB）：
- `RequiresOrderBook()` 返回 `false`（默认）
- 在 `OnAggTrans` 中累积 bar 内状态（buy/sell amount、trade count、price impact 等）
- 在 `OnBarClose` 中读取累积状态 → 计算最终因子值 → `AddRowFast` → `ResetBarState`

**OB snapshot 因子**（bar close 时读 OB）：
- `RequiresOrderBook()` 返回 `true`
- `OnBarClose` 中 `ctx.HasBook()` 守卫后调用 `ctx.GetBook()` 读取 OB
- 使用内置原语：`depth_imbalance_levels(n)`、`depth_imbalance_bps(r)`、`vwap_buy(n)`、`cost_buy_bps(n)`、`cost_asymmetry_bps(n)`、`side_depth_bps(side,i,o)`、`cog_signed_bps(i,o)`、`depth_entropy(n)`、`l1_concentration(n)` 等
- **禁止**自行遍历档位实现已有内置原语的等价计算

**L2 event 因子**（需要逐次 L2 更新）：
- `RequiresBookUpdates()` 返回 `true`（隐含 RequiresOrderBook）
- 在 `OnBookUpdate(update, ctx)` 中累积 L2 flow：`update.side`、`update.price`、`update.new_amount`、`update.old_amount`
- 在 `OnBarClose` 中输出累积值

**Mixed Agent**（同一 Agent 内混合 trade + OB 因子）：
- 合并上述模式，`OnAggTrans` 处理 trade 逻辑，`OnBarClose` 同时输出 trade 和 OB 因子

### 1.2 命名与 Schema

- 所有因子列名：`${fa_prefix}_xxx`（如 `fa03_dimb_l20`）
- `DeclareSchema()` 返回固定列列表，跨天/跨币种不变
- 列类型统一用 `ColumnDef::Double("name", 0.0)`
- 在 `OnInit` 中用 `GetDataStore()->GetColumnHandle("name")` 预取所有句柄

### 1.3 状态管理

**必须显式列出所有状态变量**，标注：
- 初始值
- 跨 bar 还是 bar 内
- 重置时机

| 类别 | 示例 | 重置时机 |
|------|------|----------|
| Bar 内累计量 | `bar_buy_amount_`, `bar_trade_count_` | `OnBarClose` 末尾（`ResetBarState()`） |
| 跨 bar 滚动状态 | EMA、deque rolling buffer | **不重置**（chunk 模式下跨日延续） |
| 诊断计数 | `bar_count_` | 可选在 `OnDayStart` 重置（仅日志用途） |

**关键**：`OnDayStart` 中**不得**重置 EMA、rolling buffer 等跨 bar 状态。Crypto 24h 连续交易，日切是文件分割边界，不是交易时段边界。参见 `crypto_factor_workflow.md §4`。

### 1.4 疑问处理

- 因子定义不明确 → 查阅 factor_list §0 溯源路径中的原始 `research_report.md`
- 仍不明确 → 写入 `${WORKSPACE}/issue.md`，标注因子名 + 疑问 + 暂定处理方式

---

## 2. 编译

```bash
cd /home/cken/crypto_world/zebra_pool/${fa_lower}/code
mkdir -p build && cd build
scl enable gcc-toolset-12 'cmake .. -DZEBRA_ROOT=/home/cken/crypto_world/zebra && make -j8'
```

验收：编译无 error，生成 `build/run_${fa_lower}_factor` 可执行文件。

---

## 3. Smoke Test

### 3.1 单日单币种运行

```bash
cd /home/cken/crypto_world/zebra_pool/${fa_lower}/code
./build/run_${fa_lower}_factor \
    --symbol BTCUSDT \
    --date 2026-01-15 \
    --threshold-dir /data/db/crypto/futures/world/bod_data/daily_thres_28800 \
    --output_dir output/smoke_test
```

如果 Agent 包含 OB 因子，追加：
```bash
    --l2-root /data/db/crypto/futures/tardis/binance-futures/incremental_book_L2
```

### 3.2 验收检查

用 Python 读取输出 parquet，逐项检查：

| 检查项 | 预期 |
|--------|------|
| 输出文件存在 | `output/smoke_test/2026-01-15/${fa_lower}_v1/BTCUSDT.parquet` |
| 因子列数 | = `FACTOR_COUNT`（不含 symbol/bar_id/close_time_ms） |
| 列名前缀 | 全部以 `${fa_prefix}_` 开头 |
| NaN/Inf | 全部为 0 |
| bar_id | 从 0 开始，单调递增 |
| close_time_ms | 单调递增 |
| 因子值范围 | 无明显异常（全 0、全相同、极端值） |
| OB 因子列 | 非全零（确认 OB 数据加载成功） |

---

## 4. 禁止项

严格遵守 `crypto_factor_workflow.md §10` 中列出的 13 条禁止项。核心禁令：

- 禁止修改 `zebra/` 下的框架代码
- 禁止硬编码阈值
- 禁止在 `OnDayStart` 重置 EMA/rolling 状态
- 禁止输出 NaN/Inf
- 禁止在 `OnAggTrans` 中调用 `AddRowFast` 或做 I/O
- 禁止跳过 `ctx.HasBook()` 守卫
- 禁止使用不以 `${fa_prefix}_` 开头的列名
- 禁止跨天/跨币种输出不同 schema
- 禁止自行实现已有内置 OB 原语的等价计算

完整列表见 `/home/cken/crypto_world/zebra/docs/crypto_factor_workflow.md` §10。
