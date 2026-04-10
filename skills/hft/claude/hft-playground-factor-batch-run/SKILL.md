---
name: hft-playground-factor-batch-run
description: 当用户想用 Playground 批量刷因子/刷入 factor_pool（playground run-agent、日期范围、workers、debug/production、output-dir、复跑/清理、刷取后验收）时使用；开始任何操作前必须先阅读 /home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md 并严格按其环境与运行步骤执行。
---

# HFT Playground 批量刷因子（run-agent → factor_pool）

## 强制前置阅读（Hard Gate）

### 文档优先级（最高）

- **以 `factor_workflow.md` 为唯一准则**：本 skill 仅做导航与检查清单；任何细节/参数/路径与文档不一致时，一律以文档为准。  
- **严格按文档步骤顺序执行**：不得跳过"小样本验证"等硬门槛；不得"凭经验"改参数名/目录结构。  
- **给命令前先对照文档定位**：在输出可执行命令/路径/参数前，先指出对应的文档章节/小节（标题即可），再按文档顺序给出步骤。  

1) 打开并通读：`/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md`  
2) 在给出任何“可执行命令/路径/参数”前，先用 5–10 条要点复述以下内容，并让用户确认：  
   - 禁止修改/写入：`/data/share/dev/hft/`；`hft_tools` 已废弃禁止使用  
   - Playground 帮助参数是 `--help`（不是 `-h`）  
   - `factor_pool` 只放数据产物（parquet），不放笔记/报告  
   - 必须先做小样本验证（Schema Gate），再做轴对齐 Gate（`hft-axis-alignment-check`），最后才允许日期范围批量刷取  
3) 若无法访问/读取该文档：停止并提示用户先提供文档内容或修复路径。  

## 向用户确认的关键信息（缺一不可）

- `AGENT_NAME`：workspace 名称（用于项目目录）
- `PROJECT_DIR`：Playground 工程根目录（含 `playground build` 产物）
- `ENV`：`debug` 或 `production`
- `AUTHOR`：由任务文档（task spec）指定的标识名（通常为因子集/Agent 名称，如 `fa15`），禁止默认使用 Unix 用户名
- `FACTOR_SET_NAME`：版本化且不可变（逻辑/参数改动就换新名）
- `DATE_RANGE`：例如 `20250102-20250131`
- `UNIVERSE`：全 code 固定为 `bond_sz`（统一口径：使用 `--universe bond_sz`；不要把 `bond_sz` 写进 `--code`）
- `CODE`：仅在“明确刷子集/单标的”时使用（逗号分隔列表，如 `127102,127103`）
- `WORKERS`：显式设置（建议先 5–10；若资源充足再上调）

## 标准流程（严格按 workflow）

### 1) 环境初始化（每个新 shell 必做）

```bash
source /opt/rh/gcc-toolset-12/enable
source /data/share/dev/hft/setup_sdk.sh
playground --help
echo "HFT_SDK_ROOT=$HFT_SDK_ROOT"
echo "HFT_DATA_ROOT=$HFT_DATA_ROOT"
```

首次在本机跑“全 code（bond_sz）”建议补齐 universe 配置（只需一次）：

```bash
mkdir -p ~/.local/opt/hft_sdk/config
cp -f /data/share/dev/hft/config/universe_bond_sz.txt ~/.local/opt/hft_sdk/config/
```

### 2) 编译（若已有二进制也建议确认一次）

在 `PROJECT_DIR`：

```bash
playground build -j 8
ls -la ./build
```

### 3) 小样本验证（强制步骤）

先单日单标的跑通并落到本地目录（不要直接刷 `factor_pool`）：

```bash
RUN_BIN=./build/run_<your_agent_bin>
DATE=20250102
CODE=127102

playground run-agent \
  --agent "$RUN_BIN" \
  --date "$DATE" \
  --code "$CODE" \
  --data-path "$HFT_DATA_ROOT" \
  --output-dir "output/dev/${DATE}_${CODE}"
```

快速检查（schema + NaN/Inf + 必备列）：

```bash
python3 - <<'PY'
import pathlib
import numpy as np
import pandas as pd

root = pathlib.Path("output/dev")
paths = sorted(root.rglob("*.parquet"))
assert paths, f"no parquet under {root}"

df = pd.read_parquet(paths[0])
need = {"code", "time", "md_id"}
miss = need - set(df.columns)
assert not miss, f"missing columns: {sorted(miss)}"

num = df.select_dtypes(include=["number"])
assert not num.isna().to_numpy().any(), "has NaN"
assert np.isfinite(num.to_numpy()).all(), "has Inf"

# (code,time,md_id) 唯一性：md_id=-1 视为占位，不纳入唯一性判断
key = df.loc[df["md_id"] != -1, ["code", "time", "md_id"]]
dup = key.duplicated(keep=False)
dup_cnt = int(dup.sum())
assert dup_cnt == 0, f"duplicate (code,time,md_id) excluding md_id=-1: {dup_cnt}"
print("OK:", paths[0], "shape=", df.shape)
PY
```

### 3.5 轴对齐 Gate（强制步骤）

在 3) 小样本验证通过后、刷日期范围全量前，必须做轴对齐检查（3–5 天全 code，join 成功率与 bar 覆盖率均 ≥ 99.9%）：

- 推荐直接使用现成 skill：`hft-axis-alignment-check`
- Join 轴口径：`time=local_ts`，`md_id=biz_index`

### 4) 日期范围批量刷取到 factor_pool

按 workflow 的固定落盘约定：

`/data/db/hft/factor_pool/{debug|production}/{author}/{factor_set_name}/{YYYYMMDD}/{AgentName}/*.parquet`

其中 `{AgentName}` 通常是你的 Agent/Context 名称（常见为 C++ Agent 类名；以实际输出目录为准）。

示例（debug）：

```bash
RUN_BIN=./build/run_<your_agent_bin>
ENV=debug
AUTHOR=<your_name>
FACTOR_SET_NAME=<factor_set_name>
DATE_RANGE=20250102-20250131

playground run-agent \
  --agent "$RUN_BIN" \
  --date "$DATE_RANGE" \
  --universe bond_sz \
  --data-path "$HFT_DATA_ROOT" \
  --output-dir "/data/db/hft/factor_pool/${ENV}/${AUTHOR}/${FACTOR_SET_NAME}" \
  --workers 8
```

复跑策略：优先换新的 `FACTOR_SET_NAME`；若必须复跑同一路径，先清理对应 `{YYYYMMDD}` 目录再重跑（避免误覆盖/混写）。

### 5) 刷取后的最小验收

对每个 `{YYYYMMDD}`：
- 至少一个 `*.parquet` 且行数 > 0
- 必含 `code,time,md_id`
- 你的 signal 列：`nan_ratio=0` 且 `inf_ratio=0`

更完整验收/报告以 `factor_workflow.md` 与 ResearchDoc 为准。
