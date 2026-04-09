---
name: hft-playground-factor-write
description: 当用户要用 Playground 编写/新增/修改 Agent 因子（编辑 src/*.hpp / *_main.cpp，使用 MarketEvent + OrderBook + DataStore 输出 parquet，并按团队统一口径做 bar_last 采样落盘）时使用；开始写代码前必须先阅读 /home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md 和 /home/cken/hft_projects/HftKnowledge/research_docs/data.md，并以文档口径为准。
---

# HFT Playground 写因子（Agent 因子开发范式）

## 强制前置阅读（Hard Gate）

### 文档优先级（最高）

- **以 `factor_workflow.md` + `data.md` 为唯一准则**：本 skill 仅做导航与检查清单；任何 schema/字段口径/事件流假设与文档不一致时，一律以文档为准。  
- **严格按文档步骤顺序执行**：不得跳过文档要求的编译/小样本验证/刷取验收；不得"凭经验"依赖 SNAPSHOT 或引入不稳定 schema。  
- **改代码前先对照文档定位**：在开始改代码/给出补丁前，先指出对应的文档章节/小节（标题即可），再按文档给出实现与验证步骤。  

1) 打开并通读：
   - `/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md`
   - `/home/cken/hft_projects/HftKnowledge/research_docs/data.md`
2) 在开始改代码前，先用要点复述下列硬规则，并让用户确认：
   - 输出时间轴统一用 `event.local_ts`（Parquet 的 `time`，与 basic_table 同口径）
   - 当前共享数据源回放流通常只含 `ORDER/TRADE`（`snap/` 分区为空/不保证提供）；因子逻辑不要强依赖 `SNAPSHOT`/`event.snap`，如遇 `SNAPSHOT` 建议显式跳过/兜底
   - 盘口/深度通过 `OrderBook`（逐事件重构）获取；需要 10 档用 `GetSnapshot()`
   - 价格是整型缩放价：`PRICE_SCALE=1000`；需要除以 `1000.0` 还原
   - schema 必须稳定：每行同名同类型列；缺失填默认值；禁止输出 NaN/Inf
   - `md_id` Join 轴统一用 `biz_index`（order/trans；必须与 basic_table.md_id 同口径；不要用 `GetMdId()/seq`）
   - Schema Gate（硬性）：parquet 必含 `code,time,md_id`；数值列不得出现 NaN/Inf；`md_id!=-1` 子集上 `(code,time,md_id)` 必须唯一
   - 采样落盘（团队统一口径）：每个 `bar_aggtrans_time_1`（aggtrans_1）仅输出 1 行（同一 bar 内取最后一条；过滤只按 `is_continuous && is_session_end`）；不再维护 `signal_agg.json`
   - 若需要量类/累计量（原 amount/sum）：必须在 C++ Agent 内按 bar 自行维护累加器，并在采样点输出（允许 bar-reset）
   - **轴对齐 Gate（强制）**：Step1 smoke test 后必须做 3-5 天全 code（约定：全 code == `bond_sz`）的轴对齐检查（Join 轴为 `(code,time,md_id)`），join 成功率与 bar 覆盖率均 >= 99.9% 才算通过（建议直接用 `hft-axis-alignment-check`）
3) 若无法访问上述文档：停止并提示用户先提供文档内容或修复路径。  

## Step 0：新因子工程必须从 factor_example 拷贝（强制）

**任何新因子集开发，在写第一行代码前，必须先将 `factor_example` 拷贝为新工程目录：**

```bash
# 1. 确定新工程目标路径（示例）
NEW_FACTOR_DIR=/home/cken/hft_projects/HFTPool/pool/<factor_set_name>/code

# 2. 拷贝模板（只拷贝 src/ 和 CMakeLists.txt；build/ 不复制）
mkdir -p "$NEW_FACTOR_DIR"
cp /home/cken/hft_projects/HFTPool/factor_example/CMakeLists.txt "$NEW_FACTOR_DIR/"
cp -r /home/cken/hft_projects/HFTPool/factor_example/src/ "$NEW_FACTOR_DIR/src/"
```

**必须保留的文件：**

| 文件 | 说明 |
|------|------|
| `src/aggtrans_time_cutter.hpp` | bar 定义权威口径（与 basic_table_v3 完全一致），**禁止修改** |
| `src/factor_example.hpp` | 采样落盘模板（bar_last + CodeState + FlushBarIfAny），在此基础上扩展 |
| `src/factor_example_main.cpp` | runner，仅修改 Agent 类名 |
| `CMakeLists.txt` | 构建配置，仅修改工程名 |

**理由**：`aggtrans_time_cutter.hpp` 是 basic_table_v3 的原样拷贝，确保 bar ID 口径严格一致（否则 bar_coverage 检查必然失败）；`factor_example.hpp` 已实现正确的 `is_continuous && is_session_end` gating + bar 边界检测 + bar-reset 模式，直接扩展比从零写更安全。

---

## 最小范式（以 data.md 为准）

- 生命周期分工：
  - `OnInit()`：`ctx->RegisterDataStore("<table_name>", &store_)`
  - `OnMarketEvent()`：读取 `event` + `book` 计算信号；`store_.AddRow(code, event.local_ts, ...)`
  - `OnFinish()`：`store_.Flush("<table_name>")`

- 获取 book（已应用当前事件后的最新状态）：  

```cpp
auto* ctx = GetContext();
auto* book = ctx ? ctx->GetOrderBook(event.code) : nullptr;
if (!book) return;
```

- 事件分支模板：只处理 `ORDER/TRADE`，并检查对应指针非空（禁止写 `SNAPSHOT` 分支）。  

- 输出表硬约束：  
  - 必有 `code`（string）与 `time`（int64）  
  - 必有 `md_id`（int64；Join 轴口径为 `biz_index`）  
  - 列顺序不稳定：下游永远按列名读  

## 采样落盘（团队统一口径：替代 signal_agg.json）

- **不再维护/提交 `signal_agg.json`**：采样逻辑在 Agent 内实现并保证口径一致。
- bar 定义：必须与 `basic_table_v3` 的 `bar_aggtrans_time_1` 完全一致（`aggtrans_time_cutter.hpp` 已随 `factor_example` 一同拷贝，直接使用）。
- 采样点：
  - 仅在 `is_continuous && is_session_end` 的事件上更新 pending；
  - 同一 bar 内取最后一条（trade / order 均可能）；
  - bar 切换时 flush 上一根 bar；`OnFinish()` flush 最后一根 bar。
- 新工程必须从 `HFTPool/factor_example/` 拷贝模板（见上方 Step 0，为强制步骤）。

### 编译提示（重要）

SDK 使用 gcc-toolset-12（libstdc++12）；Agent 工程若用系统 gcc 8 编译，运行时可能在 ParquetLoader 处 SIGSEGV（STL ABI 不一致）。编译前必须：

```bash
source /opt/rh/gcc-toolset-12/enable
source /data/share/dev/hft/setup_sdk.sh
```

## 与编译/验证/刷取的衔接

- 编译、单日验证、日期范围批量刷取与刷后验收：严格按 `factor_workflow.md` 执行（也可使用 `hft-playground-factor-batch-run` skill）。  
