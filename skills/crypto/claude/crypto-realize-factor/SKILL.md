---
name: crypto-realize-factor
description: "根据 FA*_factor_list.md 文档实现因子的完整工程流程：C++ 实现 → Code Review → 性能优化 → Performance Review → Smoke Test → 1 个月强验证 → 刷全历史 → Analyzer 报告 → 交付。调用格式：/crypto-realize-factor /path/to/FA03_factor_list.md"
metadata:
  short-description: "按 factor_list 文档实现因子全流程"
  argument-hint: "[factor_list.md 路径]"
---

# 因子工程实现（Crypto Realize Factor by Doc）

> 从 `FA*_factor_list.md` 出发，完成 C++ 实现、多轮审查、验证、刷全历史、Analyzer 报告、交付的完整工程流程。

## 0. 参数解析与初始化

### 0.1 解析输入

输入：factor_list 文件路径（如 `/home/cken/crypto_world/zebra_pool/docs/FA03_factor_list.md`）

从路径中解析：

- `FA_ID`：从文件名提取（如 `FA03`）
- `fa_prefix`：小写版本（如 `fa03_`）

```bash
DOC_PATH="$1"  # 用户提供的 factor_list 路径
FA_ID=$(basename "$DOC_PATH" | sed 's/_factor_list\.md//')   # e.g. FA03
fa_prefix=$(echo "$FA_ID" | tr 'A-Z' 'a-z')_                # e.g. fa03_
fa_lower=$(echo "$FA_ID" | tr 'A-Z' 'a-z')                  # e.g. fa03

# 所有路径统一使用 fa_lower (e.g. fa03)
WORKSPACE="/home/cken/crypto_world/zebra_pool/${fa_lower}"
DATA_OUT="/data/db/crypto/futures/world/world_pool/${fa_lower}"
ANALYZER_OUT="/data/db/crypto/analyzer/${fa_lower}/${fa_lower}_v1"
ANALYZER_MERGED="/data/db/crypto/analyzer/${fa_lower}/${fa_lower}_merged_baseline69"
```

### 0.2 读取 factor_list 文档

**立即完整阅读** `$DOC_PATH`，提取：
- 因子总数（`FACTOR_COUNT`）
- 因子前缀（确认与解析一致）
- 溯源研究报告路径
- 验证检查项（供 Step 2 使用）
- 所有因子名列表

### 0.3 读取工程文档（Hard Gate）

**必须通读以下文档，不得凭记忆执行：**
- `/home/cken/crypto_world/zebra/docs/crypto_factor_workflow.md` — 因子工程硬规则
- `/home/cken/crypto_world/zebra/docs/研究员使用手册.md` — 框架 API（§7 AggTrans, §8 OrderBook）
- Skill `crypto-analyzer-standard-report` — Analyzer 调用规范（Step 3 使用）

通读后复述硬规则：
- Join Key = `(symbol, bar_id, close_time_ms)`，三列必须为输出前三列
- `close_time_ms` = UTC epoch millisecond（int64）
- `bar_id` = int32，每 UTC 日重置为 0，日内严格单调递增
- `symbol` = 大写 Binance 永续合约代码（如 `BTCUSDT`）
- AmountBar 采样：OnAggTrans() 计算，OnBarClose() 输出一行 + reset bar 内累计量
- 动态阈值：~28800 bars/day，来自 `--threshold-dir`，禁止硬编码
- Chunk 模式：Agent 跨日存活，EMA/滚动状态禁止在 OnDayStart() 重置
- OB 访问：`RequiresOrderBook() = true` + `ctx.HasBook()` guard
- 禁止输出 NaN/Inf，使用 schema default

### 0.4 初始化工程目录

使用 Skill `crypto-zebra-factor-write` 的 §0 规范：

```bash
# 从 factor_template 复制工作区
cp -r /home/cken/crypto_world/zebra_pool/factor_template \
      /home/cken/crypto_world/zebra_pool/${fa_lower}

# 确保目录结构
mkdir -p "${WORKSPACE}/code/build" "${WORKSPACE}/report"
```

重命名：
- `src/factor_agent.hpp` -> `src/${fa_lower}_agent.hpp`
- `src/factor_main.cpp` -> `src/${fa_lower}_main.cpp`
- Agent 类名 = `${FA_ID}FactorAgent`（如 `FA03FactorAgent`）
- `factor_group_name()` 返回 `"${fa_lower}"`（如 `"fa03"`）
- `CMakeLists.txt`：工程名 = `${fa_lower}_factor`，二进制名 = `run_${fa_lower}_factor`

写入 `[START]` 到 `${WORKSPACE}/report/research_log.md`。

---

## 1. 团队角色

### 执行角色

| 角色 | 核心职责 | 活跃阶段 |
|------|---------|---------|
| **PM（主进程）** | 流程调度、任务分派、验收子结果、记录日志。读取并持续对照本 Skill 流程。 | 全程 |
| **Quant Developer (QD)** | C++ 因子实现。严格按 factor_list 定义编码，不得自行改写。 | Step 2.1 |
| **Quant Researcher (QR)** | 数据验证、统计分析、报告生成。 | Step 2.5-2.6, Step 3, Step 4 |
| **Performance Optimizer (PO)** | 在口径不变前提下优化性能（修改代码），目标 TBD（越快越好）。 | Step 2.3 |

### 审查角色（只读，不修改代码，只产出审查意见）

| 角色 | 核心职责 | 触发时机 |
|------|---------|---------|
| **Code Reviewer** | 逐因子对照 factor_list 定义审查 C++ 实现的七要素一致性 | Step 2.2（QD 完成后） |
| **Performance Reviewer** | 审查 PO 改动的口径一致性 + 性能有效性 | Step 2.4（PO 完成后） |
| **Task Compliance Monitor** | 对照本 Skill 流程检查每个 Step 是否被严格执行 | 每个 Step 边界 |

### 核心原则

- **执行者和审查者必须分离**：QD 写的代码由 Code Reviewer 审查，PO 改的代码由 Performance Reviewer 审查。不允许自审。
- **审查角色只产出意见**：发现问题后，审查角色输出报告，由 PM 安排对应执行角色修正。
- **不通过 = 迭代**：任何审查不通过，执行角色修正后必须重新提交审查，直到通过。

---

## 2. Step 1：因子实现 + 审查 + 性能优化

### 2.1 因子实现（QD 执行）

使用 Skill `crypto-zebra-factor-write`。

- 严格按 `$DOC_PATH` 的因子定义实现，**不得按自己理解改写**
- 如有疑问：查阅 factor_list 中的溯源研究报告路径；仍不明确 -> 写入 `${WORKSPACE}/issue.md`
- 所有输出列名以 `${fa_prefix}` 开头（如 `fa03_`）
- 继承 `factor_template` 的 Agent 模式：OnAggTrans() 计算 + OnBarClose() 输出
- ColumnHandle 在 OnInit() 中预取，热路径禁止字符串查找
- OB 因子必须 guard `ctx.HasBook()`，缺失时输出 schema default

**PM 验收**：编译通过、因子列数 = `FACTOR_COUNT`、列名前缀正确。

### 2.2 Code Review Gate（Code Reviewer，独立 subagent）

同时阅读 (1) factor_list (2) C++ 实现代码。

**逐因子检查七要素一致性**：

| 检查项 | 方法 |
|--------|------|
| 触发事件 | OnAggTrans 中的条件是否与定义匹配？ |
| 输入变量 | AggTrans 字段引用是否正确？OB 字段是否 guard？ |
| 计算公式 | 代码逻辑是否与数学公式逐行等价？ |
| 参数值 | halflife/window/threshold 硬编码值是否与定义一致？ |
| 状态管理 | 初始值、bar-reset（OnBarClose 末尾）行为是否正确？跨日状态是否保留？ |
| 输出范围 | clamp/guard 是否保证值域？无 NaN/Inf？ |
| 边界条件 | 除零、OB 缺失、首 bar 冷启动、amount overshoot 处理是否匹配？ |

**产出**：`${WORKSPACE}/report/code_review_report.md`（通过 / 不通过 + 逐因子检查结果）

**不通过 -> QD 修正 -> Code Reviewer 重审，迭代直到通过。**

### 2.3 性能优化（PO，独立 subagent）

Code Review 通过后触发。

**PO 阅读通过审查的代码，在不改变任何因子计算逻辑的前提下优化**：
- 识别跨因子共用数据结构（EMA、滑窗、snap 读取）并提取复用
- 内存布局优化（cache-friendly struct layout）
- 热路径无分支、减少不必要的除法/开方
- 产出优化后代码 + benchmark 数据（优化前/后每 tick 耗时）

**性能目标**：TBD（参考值，能更快必须更快）。
**Benchmark 方法**：单 symbol 单日运行，总耗时 / 总 AggTrans 数。

### 2.4 Performance Review Gate（Performance Reviewer，独立 subagent）

PO 完成后触发。

| 检查项 | 方法 |
|--------|------|
| **口径一致性** | 同一输入数据，运行优化前/后代码，逐行 diff 输出 parquet，max_rel_err < 1e-10 |
| **性能验证** | 独立跑 benchmark 确认 PO 数据真实 |
| **代码安全** | 检查优化是否引入 edge case（整数溢出、浮点精度） |

**产出**：`${WORKSPACE}/report/perf_review_report.md`

**不通过 -> PO 修正 -> Performance Reviewer 重审，迭代直到通过。**

### 2.5 Smoke Test（QR 执行）

使用 Skill `crypto-zebra-factor-write` §3（Smoke Test 规范）：

```bash
cd ${WORKSPACE}/code
mkdir -p build && cd build
scl enable gcc-toolset-12 'cmake .. && make -j8'

# 单 symbol 单日 smoke test
./run_${fa_lower}_factor \
  --symbol BTCUSDT --date 2025-01-15 \
  --threshold-dir /data/db/crypto/futures/world/bod_data/daily_thres_28800 \
  --output_dir ${WORKSPACE}/code/output/dev/smoke_test
```

**验收**：输出落盘、列数正确、无 NaN/Inf、join key 三列完整。

### 2.6 轴对齐检查（QR 执行，使用 Skill `crypto-axis-alignment-check`）

刷 3-5 天全 symbol 后，验证新因子输出与 `basic_table` anchor 的 bar grid 严格对齐（issue #119 之后 anchor 已从 f001 切换为 basic_table）：

```bash
python /home/cken/crypto_world/zebra/scripts/axis_alignment_check.py \
    --factor-root ${WORKSPACE}/code/output/dev/smoke_test \
    --factor-sub ${fa_lower}_v1 \
    --anchor-root /data/db/crypto/futures/world/world_pool/basic_table \
    --anchor-sub basic_table \
    --dates 2026-01-15,2026-01-16,2026-01-17 \
    --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT
```

**通过标准**：
- `join_ratio >= 99.9%` 且 `bar_coverage >= 99.9%`
- `dup_cnt = 0`

**不通过 -> 排查 threshold 配置、bar builder 参数、OnBarClose 输出逻辑。**

**Task Compliance Monitor 检查 Step 1 全部子步骤后 -> 进入 Step 2。**

---

## 3. Step 2：1 个月强验证

### 3.1 批量刷数（QR 执行）

使用 Skill `crypto-zebra-factor-batch-run`：
- 日期范围：`2025-07-01` 至 `2025-07-31`（可用数据范围内的首月）
- Universe：`BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT`
- 输出：`$DATA_OUT`
- `--chunk-days 0`（整段为一个 chunk，推荐用于生产）
- **在 research_log.md 记录运行参数与时间**

### 3.2 六类强验证（QR 执行，可并行 subagent）

**A) 数值健康**：全列 count/mean/std/min/max/分位数/NaN/Inf。NaN/Inf 必须为 0。

**B) 点对点复算**：每因子 >= 2000 点（跨多日、>= 4 symbol），独立复算路径对比。

**C) 不变量/边界检查**：

> 由独立 SubAgent 阅读 factor_list 验证检查项，生成验证脚本并执行。SubAgent 同时审查验证项是否有遗漏的边界条件，如有则补充。

**D) 口径一致性专项**：
- `close_time_ms` = UTC epoch millisecond
- `(symbol, bar_id, close_time_ms)` join key 完整性
- AmountBar 采样口径：OnBarClose() 每 bar 恰好一行
- 与 `basic_table` anchor join ratio >= 99.9%（issue #119 之后 anchor 从 f001 迁到 basic_table）
- 跨日状态连续性（chunk 模式下 EMA 不在日界重置）

**E) 单元测试**：覆盖 OB 缺失（HasBook=false）、零成交量、极端 spread、首 bar 冷启动、amount overshoot。

**F) 验证报告（中文）**：输出到 `${WORKSPACE}/report/data_validation_1m.md`。

**验证不通过 -> QD 修 bug -> QR 重新验证，迭代直到通过。**

**Task Compliance Monitor 检查 Step 2 后 -> 进入 Step 3。**

---

## 4. Step 3：刷全历史 + Analyzer 报告

### 4.1 全历史刷取（QR 执行）

使用 Skill `crypto-zebra-factor-batch-run`：
- 日期范围：`2025-07-01` 至 `2026-02-09`（全部可用数据，保留 02-10 作为 holdout）
- Universe：`BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT`
- 输出：`$DATA_OUT`
- `--chunk-days 0`
- `--skip_existing`（跳过 Step 2 已刷的数据）

### 4.2 报告 #1：仅新因子集（QR 执行）

使用 Skill `crypto-analyzer-standard-report` §1：
- 数据源：`/data/db/crypto/futures/world/world_pool/${fa_lower}`
- 日期范围：`--start-date 2025-07-01 --end-date 2026-02-09`
- 输出：`$ANALYZER_OUT`
- Train/Valid 分割：按时间顺序 80/20（~2025-07-01~2025-12-14 train / ~2025-12-15~2026-02-09 valid）
- 报告包含：IC/ICIR、因子分布、相关性矩阵、LightGBM 重要性
- **Label 口径（issue #119 后默认且唯一）**：mid-to-mid forward return（mid 来自 `basic_table.mid`），close-to-close 路径已硬下线
- **扣费口径**：净收益使用 `basic_table.spread_bps` 的 per-bar realtime spread（full spread, ask - bid）+ fee，不再使用硬编码 per-symbol spread 常数
- **anchor 依赖**：analyzer 会 inner join `basic_table`，所有分析日期 × symbol 的 basic_table 必须齐全

### 4.3 报告 #2：新因子集 + baseline 合并（QR 执行）

使用 Skill `crypto-analyzer-standard-report` §2：
- 合并：新因子集 + f001(30) + f002(39) baseline
- 日期范围：`--start-date 2025-07-01 --end-date 2026-02-09`
- 合并方式：在 `(symbol, bar_id, close_time_ms)` join key 上 merge，**禁止手工拼接**
- 输出：`$ANALYZER_MERGED`
- Train/Valid 分割：同 §4.2（80/20 按时间顺序）
- 摘要必须明确"相对 f001+f002 baseline（69 因子）的增量变化"

**Task Compliance Monitor 检查 Step 3 后 -> 进入 Step 4。**

---

## 5. Step 4：最终交付

### 5.1 组装交付目录（PM 执行）

```
${DELIVERY}/
├── code/
│   ├── src/${fa_lower}_agent.hpp
│   ├── src/${fa_lower}_main.cpp
│   ├── CMakeLists.txt
│   └── README.md（中文，可复现命令，标注 Skill 名称）
└── report/
    ├── research_log.md
    ├── data_validation_1m.md
    ├── code_review_report.md
    ├── perf_review_report.md
    ├── analyzer_new_only/ → link to $ANALYZER_OUT
    └── analyzer_merged_baseline69/ → link to $ANALYZER_MERGED
```

```bash
# 创建 symlink
ln -sfn "$ANALYZER_OUT" "${DELIVERY}/report/analyzer_new_only"
ln -sfn "$ANALYZER_MERGED" "${DELIVERY}/report/analyzer_merged_baseline69"
```

### 5.2 最终合规检查（Task Compliance Monitor）

检查全部 Step 完成、全部审查报告存在且通过、交付目录完整。

---

## 6. Skills 调用规范

| 操作 | 使用的 Skill |
|------|-------------|
| 编写/修改因子代码 | `crypto-zebra-factor-write` |
| 批量刷因子 | `crypto-zebra-factor-batch-run` |
| 轴对齐检查 | `crypto-axis-alignment-check` |
| Analyzer 标准报告 | `crypto-analyzer-standard-report` |

每次调用 Skill 前，在 research_log.md 记录 Skill 名称、目的、UTC+8 时间戳。

---

## 7. 硬性规范

> **不在此重复 `crypto_factor_workflow.md` 的全部规则。** 本节仅列出流程层面的硬性要求。实现层面的硬规则以 `crypto_factor_workflow.md` 为唯一权威来源。

- **因子命名**：所有列以 `${fa_prefix}` 开头（如 `fa03_`），纯 ASCII 小写 + 数字 + 下划线
- **Join Key**：`(symbol, bar_id, close_time_ms)` 必须为输出前三列，格式严格按 workflow §1
- **采样口径**：OnAggTrans() 计算，OnBarClose() 输出恰好一行 via `AddRowFast()`
- **Chunk 模式**：EMA/滚动状态禁止在 OnDayStart() 重置（crypto 24h 连续交易）
- **Schema 稳定**：跨天跨 symbol 列名/类型不变，无 NaN/Inf
- **OB guard**：使用 `ctx.GetBook()` 前必须 `ctx.HasBook()` 检查
- **审查独立性**：Code Reviewer / Performance Reviewer / Task Compliance Monitor 不参与实现，只产出意见
- **禁止中途对话**：问题写入 `${WORKSPACE}/issue.md`
- **持续对照本文件**：每个 Step 完成后重读本 Skill 核对

---

## 8. Changes after issue #119 (2026-04-19)

- **Step 2.6 轴对齐**：anchor 从 `f001` 切换为 `basic_table`，脚本参数改为 `--anchor-root` / `--anchor-sub`（默认指向 `basic_table`）。原 `--f001-root` / `--f001-sub` 仅为兼容旧流水线保留，调用会发 DeprecationWarning。
- **Step 2 强验证 D 项口径一致性**：与 anchor 的 join ratio 目标从"与 f001"改为"与 basic_table"。
- **Step 3 Analyzer 报告**：默认（且唯一）label 口径是 mid-to-mid（basic_table.mid），close-to-close 路径已硬下线；扣费使用 basic_table 提供的 per-bar realtime spread，不再用硬编码 per-symbol 常数。
- **basic_table 强依赖**：analyzer 阶段所有日期 × symbol 的 `basic_table` 必须齐全，缺失即 load 失败。在进入 Step 3 之前 QR 应自行检查 basic_table 覆盖度。
