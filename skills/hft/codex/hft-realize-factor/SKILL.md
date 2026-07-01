---
name: hft-realize-factor
description: "根据 FA*_factor_list.md 文档实现因子的完整工程流程：C++ 实现 → Code Review → 性能优化 → Performance Review → Smoke Test → 轴对齐 → 1 个月强验证 → 刷全历史 → Analyzer2 报告 → 交付。调用格式：/hft-realize-factor /path/to/FA20_factor_list.md"
---
# 因子工程实现（Realize Factor by Doc）

> 从 `FA*_factor_list.md` 出发，完成 C++ 实现、多轮审查、验证、刷全历史、Analyzer2 报告、交付的完整工程流程。

## 0. 参数解析与初始化

### 0.1 解析输入

输入：factor_list 文件路径（如 `/home/cken/hft_projects/HFTPool/factor_agent_docs/FA20_factor_list.md`）

从路径中解析：
- `FA_ID`：从文件名提取（如 `FA20`）
- `fa_prefix`：小写版本（如 `fa20_`）

```bash
DOC_PATH="$1"  # 用户提供的 factor_list 路径
FA_ID=$(basename "$DOC_PATH" | sed 's/_factor_list\.md//')   # e.g. FA20
fa_prefix=$(echo "$FA_ID" | tr 'A-Z' 'a-z')_                # e.g. fa20_
fa_lower=$(echo "$FA_ID" | tr 'A-Z' 'a-z')                  # e.g. fa20

WORKSPACE="/home/cken/hft_projects/HFTPool/workspace/${FA_ID}"
DELIVERY="/home/cken/hft_projects/HFTPool/pool/${FA_ID}"
DATA_OUT="/data/db/hft/factor_pool/debug/${fa_lower}/${fa_lower}_factor_v1"
ANALYZER_OUT="/data/db/hft/analyzer2/${fa_lower}/${fa_lower}_factor_v1/v1"
ANALYZER_MERGED="/data/db/hft/analyzer2/${fa_lower}/${fa_lower}_merged_benchmark0323_top100/v1"
```

### 0.2 读取 factor_list 文档

**立即完整阅读** `$DOC_PATH`，提取：
- 因子总数（`FACTOR_COUNT`）
- 因子前缀（确认与解析一致）
- §0 溯源研究报告路径
- §8 验证检查项（供 Step 2 使用）
- 所有因子名列表

### 0.3 读取工程文档（Hard Gate）

**必须通读以下文档，不得凭记忆执行：**
- `/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md`
- `/home/cken/hft_projects/HftKnowledge/research_docs/data.md`
- `/home/cken/hft_projects/HftKnowledge/research_docs/analyzer_user_manual.md`

通读后复述硬规则：
- `time` = `event.local_ts`
- `md_id` = `biz_index`（禁止 `GetMdId()`）
- 价格 = 整型缩放价 / `PRICE_SCALE=1000`
- `bar_aggtrans_time_1` 采样：`is_continuous && is_session_end`，每 bar 仅 1 行
- bar 内累计量在 C++ Agent 内维护，禁止 `signal_agg.json`

### 0.4 初始化工程目录

使用 Skill `hft-playground-factor-write` 的 Step 0 规范：

```bash
source /opt/rh/gcc-toolset-12/enable
source /data/share/dev/hft/setup_sdk.sh

mkdir -p "${WORKSPACE}/code" "${WORKSPACE}/report"
cp /home/cken/hft_projects/HFTPool/factor_example/CMakeLists.txt "${WORKSPACE}/code/"
cp -r /home/cken/hft_projects/HFTPool/factor_example/src/ "${WORKSPACE}/code/src/"
touch "${WORKSPACE}/research_log.md"
```

重命名：
- `src/factor_example.hpp` → `src/${fa_lower}_agent.hpp`
- `src/factor_example_main.cpp` → `src/${fa_lower}_agent_main.cpp`（Agent 类名 = `${FA_ID}FactorAgent`，注册名 = `"${fa_lower}_factor"`）
- `CMakeLists.txt`：工程名 = `${fa_lower}_factor`，二进制名 = `run_${fa_lower}_factor`
- **`src/aggtrans_time_cutter.hpp` 禁止修改**

写入 `[START]` 到 research_log.md。

---

## 1. 团队角色

### 执行角色

| 角色 | 核心职责 | 活跃阶段 |
|------|---------|---------|
| **PM（主进程）** | 流程调度、任务分派、验收子结果、记录日志。读取并持续对照本 Skill 流程。 | 全程 |
| **Quant Developer (QD)** | C++ 因子实现。严格按 factor_list 定义编码，不得自行改写。 | Step 2.1 |
| **Quant Researcher (QR)** | 数据验证、统计分析、报告生成。 | Step 2.5-2.6, Step 3, Step 4 |
| **Performance Optimizer (PO)** | 在口径不变前提下优化性能（修改代码），目标 ≤10us/tick（越快越好）。 | Step 2.3 |

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

使用 Skill `hft-playground-factor-write`。

- 严格按 `$DOC_PATH` 的 §3 因子定义实现，**不得按自己理解改写**
- 如有疑问：查阅 factor_list §0 中的溯源研究报告路径；仍不明确 → 写入 `${WORKSPACE}/issue.md`
- 所有输出列名以 `${fa_prefix}` 开头
- 继承 `factor_example.hpp` 的 `CodeState + PendingRow + FlushBarIfAny` 模式

**PM 验收**：编译通过、因子列数 = `FACTOR_COUNT`、列名前缀正确。

### 2.2 Code Review Gate（Code Reviewer，独立 subagent）

同时阅读 (1) factor_list (2) C++ 实现代码。

**逐因子检查七要素一致性**：

| 检查项 | 方法 |
|--------|------|
| 触发事件 | if 条件（event.type, side, price>0 guard）是否与定义匹配？ |
| 输入变量 | 字段引用是否正确？prev_snap vs current snap？ |
| 计算公式 | 代码逻辑是否与数学公式逐行等价？ |
| 参数值 | halflife/window/threshold 硬编码值是否与定义一致？ |
| 状态管理 | 初始值、bar-reset 行为是否正确？ |
| 输出范围 | clamp/guard 是否保证值域？ |
| 边界条件 | 除零、空盘口、首 bar 处理是否匹配？ |

**产出**：`${WORKSPACE}/report/code_review_report.md`（通过 / 不通过 + 逐因子检查结果）

**不通过 → QD 修正 → Code Reviewer 重审，迭代直到通过。**

### 2.3 性能优化（PO，独立 subagent）

Code Review 通过后触发。

**PO 阅读通过审查的代码，在不改变任何因子计算逻辑的前提下优化**：
- 识别跨因子共用数据结构（EMA、滑窗、snap 读取）并提取复用
- 内存布局优化（cache-friendly struct layout）
- 热路径无分支、减少不必要的除法/开方
- 产出优化后代码 + benchmark 数据（优化前/后每 tick 耗时）

**性能目标**：≤ 10us/tick（参考值，能更快必须更快）。
**Benchmark 方法**：单 code 单日运行，总耗时 / 总事件数。

### 2.4 Performance Review Gate（Performance Reviewer，独立 subagent）

PO 完成后触发。

| 检查项 | 方法 |
|--------|------|
| **口径一致性** | 同一输入数据，运行优化前/后代码，逐行 diff 输出 parquet，max_rel_err < 1e-10 |
| **性能验证** | 独立跑 benchmark 确认 PO 数据真实 |
| **代码安全** | 检查优化是否引入 edge case（整数溢出、浮点精度） |

**产出**：`${WORKSPACE}/report/perf_review_report.md`

**不通过 → PO 修正 → Performance Reviewer 重审，迭代直到通过。**

### 2.5 Smoke Test（QR 执行）

```bash
cd ${WORKSPACE}/code
playground build -j 8
playground run-agent \
  --agent ./build/run_${fa_lower}_factor \
  --date 20250102-20250102 --code 127089 \
  --data-path "$HFT_DATA_ROOT" \
  --output-dir output/dev/20250102_127089
```

**验收**：输出落盘、列数正确、无 NaN/Inf、每 tick ≤ 10us。

### 2.6 轴对齐检查（QR 执行，使用 Skill `hft-axis-alignment-check`）

刷 3-5 天全 code（bond_sz）后检查：
- `join_ratio >= 99.9%` 且 `bar_coverage >= 99.9%`
- `dup_cnt = 0`

**Task Compliance Monitor 检查 Step 1 全部子步骤后 → 进入 Step 2。**

---

## 3. Step 2：1 个月强验证

### 3.1 批量刷数（QR 执行）

使用 Skill `hft-playground-factor-batch-run`：
- 日期范围：`20250102-20250131`
- Universe：`bond_sz`
- 输出：`$DATA_OUT`
- **在 research_log.md 记录内存估算与 workers**（硬上限 180GB）

### 3.2 六类强验证（QR 执行，可并行 subagent）

**A) 数值健康**：全列 count/mean/std/min/max/分位数/NaN/Inf。NaN/Inf 必须为 0。

**B) 点对点复算**：每因子 ≥2000 点（跨多日、≥200 code），独立复算路径对比。

**C) 不变量/边界检查**：

> **⚠️ 由独立 SubAgent 阅读 factor_list §8 验证检查项**，生成验证脚本并执行。SubAgent 同时审查 §8 是否有遗漏的边界条件，如有则补充。

**D) 口径一致性专项**：time=local_ts、md_id=biz_index、PRICE_SCALE=1000、采样口径与定义一致。

**E) 单元测试**：覆盖空簿/0量/极端spread/午休gap/时间回退。

**F) 验证报告（中文）**：输出到 `${WORKSPACE}/report/data_validation_1m.md`。

**验证不通过 → QD 修 bug → QR 重新验证，迭代直到通过。**

**Task Compliance Monitor 检查 Step 2 后 → 进入 Step 3。**

---

## 4. Step 3：刷全历史 + Analyzer2 报告

### 4.1 全历史刷取（QR 执行）

使用 Skill `hft-playground-factor-batch-run`：
- 日期范围：`20250102-20250730`
- Universe：`bond_sz`
- 输出：`$DATA_OUT`

### 4.2 报告 #1：仅新因子集（QR 执行）

使用 Skill `hft-analyzer2-standard-report`：
- 数据集：stage=debug, author=${fa_lower}, factor_set_name=${fa_lower}_factor_v1
- 评估口径：bar 模式, bar_col=bar_aggtrans_time_1, 主 label=ret_lag0_next100
- 输出：`$ANALYZER_OUT`

### 4.3 报告 #2：新因子集 + benchmark0323_top100 合并（QR 执行）

使用 Skill `hft-analyzer2-standard-report`（多数据集合并）：
- 合并：新因子集 + benchmark0323_top100（`/data/db/hft/factor_pool/debug/benchmark0323/benchmark0323_top100/`）
- 方式：`build_multi_dataset_cache + generate_standard_report`，**禁止手工拼接**
- 输出：`$ANALYZER_MERGED`
- 摘要必须明确"相对 benchmark0323_top100 的增量变化"

**Task Compliance Monitor 检查 Step 3 后 → 进入 Step 4。**

---

## 5. Step 4：最终交付

### 5.1 组装交付目录（PM 执行）

```
${DELIVERY}/
├── code/
│   ├── src/aggtrans_time_cutter.hpp（未修改）
│   ├── src/${fa_lower}_agent.hpp
│   ├── src/${fa_lower}_agent_main.cpp
│   ├── CMakeLists.txt
│   ├── tests/（单元测试）
│   └── README.md（中文，可复现命令，标注 Skill 名称）
└── report/
    ├── research_log.md
    ├── data_validation_1m.md
    ├── code_review_report.md
    ├── perf_review_report.md
    ├── analyzer2_new_only/              # 完整拷贝 $ANALYZER_OUT 内容
    └── analyzer2_merged_benchmark0323_top100/   # 完整拷贝 $ANALYZER_MERGED 内容
```

**严禁使用软链接（symlink）提交 Analyzer2 报告。** 必须用 `cp -rL` 将报告正文（`report.md`、`metadata.json`）、所有图片（`img/`）以及摘要 parquet（`signal_rank_table.parquet` / `daily_ic.parquet` / `signal_summary.parquet` 等）物理拷贝到 `${DELIVERY}/report/analyzer2_*/` 下。

**理由**：`/data/db/hft/analyzer2/` 是共享临时缓存目录，可能被清理；若交付目录采用软链接指向该缓存，缓存清理后交付报告会全部失效（历史事故：2026-04-23 `/data/db/hft/analyzer2` 清理导致 FA20–FA27 的 16 个报告链接全部 dangling，需重刷）。

拷贝命令示例：
```bash
mkdir -p "${DELIVERY}/report/analyzer2_new_only"
cp -rL "${ANALYZER_OUT}/." "${DELIVERY}/report/analyzer2_new_only/"

mkdir -p "${DELIVERY}/report/analyzer2_merged_benchmark0323_top100"
cp -rL "${ANALYZER_MERGED}/." "${DELIVERY}/report/analyzer2_merged_benchmark0323_top100/"

# 验证交付目录不含 symlink
if find "${DELIVERY}/report" -type l | grep -q .; then
  echo "ERROR: symlink detected in delivery; must copy physically" >&2
  exit 1
fi
```

### 5.2 最终合规检查（Task Compliance Monitor）

检查全部 Step 完成、全部审查报告存在且通过、交付目录完整。

---

## 6. Skills 调用规范

| 操作 | 使用的 Skill |
|------|-------------|
| 编写/修改因子代码 | `hft-playground-factor-write` |
| 批量刷因子 | `hft-playground-factor-batch-run` |
| 轴对齐检查 | `hft-axis-alignment-check` |
| Analyzer2 标准报告 | `hft-analyzer2-standard-report` |

每次调用 Skill 前，在 research_log.md 记录 Skill 名称、目的、UTC+8 时间戳。

---

## 7. 硬性规范

- **因子命名**：所有列以 `${fa_prefix}` 开头
- **时间轴**：`time = event.local_ts`
- **md_id**：`biz_index`
- **采样**：`is_continuous && is_session_end`，每 bar 1 行
- **bar 内累计量**：C++ 内维护，禁止 `signal_agg.json`
- **schema 稳定**：跨天列名/类型不变，无 NaN/Inf
- **内存上限 180GB**：先估算再运行
- **审查独立性**：Code Reviewer / Performance Reviewer / Task Compliance Monitor 不参与实现，只产出意见
- **禁止中途对话**：问题写入 `${WORKSPACE}/issue.md`
- **持续对照本文件**：每个 Step 完成后重读本 Skill 核对
- **禁止软链接交付**：`${DELIVERY}/report/` 下不得出现任何 symlink；Analyzer2 报告必须以物理拷贝方式（`cp -rL`）落入交付目录（正文 + img + parquet），避免缓存清理导致 dangling
