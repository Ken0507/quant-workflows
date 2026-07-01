---
name: hft-remote-backtest
description: "在交易机上使用 DualRunner 二进制运行回测，并将结果同步回本地分析。适用于需要用生产参数对单、验证策略行为或利用交易机独有数据的场景。"
---
# Remote Backtest Skill

在交易机上使用 DualRunner 二进制运行回测，并将结果同步回本地分析。适用于需要用**生产参数**对单子、验证策略行为、或利用交易机独有数据的场景。

## Prerequisites

1. SSH 隧道可用：`localhost:2223` → 交易机
2. `~/.hft/credentials.env` 包含 `HFT_TRADING_PASS`
3. 策略项目有 DualRunner 入口（`*_dual.cpp`，使用 `hft::DualRun<>`）
4. SDK 环境已配置（`/data/share/dev/hft`）

## Workflow

### Step 0: 检查 SSH 隧道

```bash
source ~/.hft/credentials.env
sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p 2223 userlgj@localhost "echo SSH_OK"
```

如果失败，使用 `/hft-vpn-tunnel-restore` skill 恢复隧道。

### Step 1: Docker 交叉编译

DualRunner 二进制需要链接 `agent_online` + `agent_offline`，必须用 Docker 交叉编译以匹配交易机 ABI。

```bash
cd <project_dir>  # 含 CMakeLists.txt 的项目目录
export HFT_SDK_ROOT=/data/share/dev/hft
source /data/share/dev/hft/setup_sdk.sh

# Docker 交叉编译（产出在 build_prod/）
HFT_SDK_ROOT=/data/share/dev/hft bash ~/hft_build/scripts/envs/sdk/build_external.sh . <dual_target_name>
```

验证：`ls -lh build_prod/<dual_target_name>` 应为 4-5MB ELF 二进制。

### Step 2: 部署到交易机

```bash
export HFT_SDK_ROOT=/data/share/dev/hft
source /data/share/dev/hft/setup_sdk.sh

playground deploy <dual_target_name> --no-build
```

这会：
- SCP 二进制到 `/home/userlgj/app/strategy/<project_name>/<dual_target_name>`
- 复制 `lib_trading/*.so` 到 `lib/`
- 复制 config 模板到 `config/`
- 验证 MD5

**注意**：`playground deploy` 自动检测 `build_prod/` 目录下的二进制。必须设置 `HFT_SDK_ROOT=/data/share/dev/hft` 以确保使用 `lib_trading/` 中的 `.so`。

### Step 3: 在交易机上运行回测

**注意**：`playground remote-backtest` 在密码认证环境下有 bug（Issue #26），需要手动执行。

```bash
source ~/.hft/credentials.env

REMOTE_BIN="/home/userlgj/app/strategy/<project_name>/<dual_target_name>"
REMOTE_OUT="/tmp/remote_backtest/<date>"
DATA_PATH="/home/userlgj/market_data_parquet"

# 验证二进制
sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -p 2223 userlgj@localhost \
  "test -x $REMOTE_BIN && echo BINARY_OK"

# 创建输出目录
sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -p 2223 userlgj@localhost \
  "rm -rf /tmp/remote_backtest && mkdir -p $REMOTE_OUT"

# 运行回测
sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -p 2223 userlgj@localhost \
  "cd $(dirname $REMOTE_BIN) && \
   export LD_LIBRARY_PATH=\$PWD/lib:\$LD_LIBRARY_PATH && \
   ./<dual_target_name> --backtest \
     --date <YYYYMMDD> --code <code_or_codes> \
     --data_path $DATA_PATH \
     --output_dir $REMOTE_OUT \
     --latency_ms 100 --parquet \
     <additional_flags> \
     2>&1"
```

常用 additional_flags（生产参数示例）：
```
--score_open_bps 7.0 --score_open_market_bps 20.0
--score_hysteresis_bps 4.0 --cancel_reduce_scheme BE
--cancel_confirm_bars 5 --exit_reprice_tolerance_bps 5.0
```

### Step 4: 同步结果到本地

```bash
LOCAL_OUT="/data/db/hft/temp/remote_bt_<suffix>"
mkdir -p $LOCAL_OUT

sshpass -p "$HFT_TRADING_PASS" rsync -avz --progress \
  -e "ssh -o StrictHostKeyChecking=no -p 2223" \
  userlgj@localhost:/tmp/remote_backtest/<date>/ \
  $LOCAL_OUT/
```

### Step 5: 分析结果

回测产出在 `matcher/` 子目录：
- `backtest_trade_<code>.parquet` — 成交明细（含 BUY/SELL/ACK/REJECT/CANCEL 事件）
- `backtest_entrust_<code>.parquet` — 委托明细（含 bid1/ask1 快照）
- `backtest_stats_<code>.parquet` — 分钟级账户快照（PnL/RT/turnover）
- `baseline_150_live_signal_*.parquet` — 信号因子输出

```python
import pyarrow.parquet as pq
trades = pq.read_table(f'{LOCAL_OUT}/matcher/backtest_trade_<code>.parquet').to_pandas()
buys = trades[(trades['event'] == 'TRADE') & (trades['dir'] == 48)]
sells = trades[(trades['event'] == 'TRADE') & (trades['dir'] == 49)]
```

## DualRunner 入口文件模板

创建 `src/<strategy>_dual.cpp`：

```cpp
#include "<strategy>.hpp"
#include <hft/trading_agent/dual_runner.hpp>
#include <gflags/gflags.h>
#include <spdlog/spdlog.h>

// 策略 flags（使用生产默认值）
DEFINE_double(score_open_bps, 7.0, "...");
// ... 其他 flags ...
DEFINE_string(lmdb_path, "/home/userlgj/orderbook_dump", "LMDB path");

int main(int argc, char** argv) {
    return hft::DualRun<hft::YourStrategy>(argc, argv,
        "Usage: ...",
        [](hft::OnlineRunner& runner) {
            runner.WithConfig("config/config.ini", "market_sz")
                  .WithLogLevel(spdlog::level::info)
                  .WithTradingLogger("YourStrategy")
                  .WithLmdbPath(FLAGS_lmdb_path)
                  .WithContextManager()
                  .WithTradingMode(true);
        });
}
```

CMakeLists.txt 追加：

```cmake
add_executable(<strategy>_dual src/<strategy>_dual.cpp)
target_link_directories(<strategy>_dual PRIVATE
    ${HFT_SDK_ROOT}/lib ${HFT_SDK_ROOT}/lib_trading)
target_link_libraries(<strategy>_dual PRIVATE
    trading_agent_lib agent_online agent_offline agent_io_parquet
    agent_core orderbook common_args_lib gflags fmt::fmt spdlog::spdlog pthread dl)
target_link_options(<strategy>_dual PRIVATE "LINKER:--allow-shlib-undefined")
set_target_properties(<strategy>_dual PROPERTIES
    BUILD_RPATH "${HFT_SDK_ROOT}/lib;${HFT_SDK_ROOT}/lib_trading")
```

## Key Notes

- **不影响实盘**：dual 二进制和 online 二进制并存于同一目录，互不干扰
- **`--backtest` 是 DualRunner 开关**：不加时走 OnlineRunner（实盘），加了走 BacktestRunner
- **生产参数对单子**：dual 二进制使用和 online 相同的 flag 默认值，BT 结果可直接和实盘对比
- **交易机数据**：`/home/userlgj/market_data_parquet/` 有 order/transaction/snap，覆盖最近交易日
- **本地临时数据一律放 `/data/db/hft/temp/`**，不要用 `/tmp`
- **`playground remote-backtest`** 在 Issue #26 修复前需要手动 sshpass 执行（Step 3）
