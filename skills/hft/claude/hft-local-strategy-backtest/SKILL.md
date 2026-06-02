---
name: hft-local-strategy-backtest
description: "在 cken 工作站本机用纯 BacktestRunner 离线回测 live 策略（baseline_150 / score_maker），不连 broker、零实盘风险。适用于研究验证、SDK fix 验证、日报 sim 侧复跑等场景。内置回测二进制安全闸：严禁用 *_trader_online 跑回测。"
metadata:
  short-description: "本机离线回测 live 策略（含二进制安全闸）"
  argument-hint: "[策略名] [YYYYMMDD 或日期区间]"
---

# Local Strategy Backtest Skill

在 cken 工作站**本机**离线回测 live 策略。本机 broker 网关不可达，是天然兜底；但**二进制选错仍可能发起非预期 broker 连接**（已发生过一次，违反实盘红线），因此本 skill 的安全闸为强制步骤。

## ⚠️ 安全红线：二进制选择（先读这张表）

| 策略 | ✅ 回测用 | ❌ 严禁用于回测 |
|---|---|---|
| baseline_150 | `run_baseline_150_trader`（`baseline_150_trader_main.cpp` = 纯 `BacktestRunner::Run()`，源码无 broker 路径） | `baseline_150_trader_online`（online-only，**忽略 `--backtest`、必连实盘 broker**） |
| score_maker | `score_maker_online` **加 `--backtest`**（它本身是 DualRunner，支持双模） | 不带 `--backtest` 裸跑（会走 online 路径） |

- `baseline_150_trader_dual` 也是 DualRunner，但确认是新 build 才可用（交易机上那份是 2026-03-11 旧 build，缺 `exit_sell_discount_bps`）。
- `playground remote-backtest <target>` 的 target 只能指 DualRunner 二进制，不能指 baseline 的 `_online`。

## Prerequisites

1. SDK 环境（每个新 shell）：
   ```bash
   export HFT_SDK_ROOT=/data/share/dev/hft
   source /opt/rh/gcc-toolset-12/enable
   source /data/share/dev/hft/setup_sdk.sh
   ```
2. 行情数据完整：`/data/share/dev/hft/data/market_data_parquet/{order,transaction}/<date>/` 每侧 slices ≥ 45（不足先跑 `/hft-sync-market-data`）。
3. 回测二进制存在；缺失时重编：
   ```bash
   cd /home/cken/hft_projects/HFTPool/pool/baseline/baseline_20260129_150/live_v2
   cmake --build build --target run_baseline_150_trader -j8
   ```

## Workflow

### Step 1: 跑回测（baseline_150 canonical 调用）

参数**对齐 live `run.sh`**（11 个交易参数），研究默认 `--latency_ms 100`（有意保守，不要调向实盘真值"对齐"）、`--fee_ratio 0.00015`。参考实现：`HFTPool/tasks/daily_report/cken_daily_report.sh`（Step 2 段）。

```bash
ulimit -c 0   # 已知退出段 segfault，防 core 堆积
export LD_LIBRARY_PATH="/data/share/dev/hft/lib:${LD_LIBRARY_PATH:-}"
"$BINARY" --date <YYYYMMDD> --data_path /data/share/dev/hft/data/market_data_parquet \
    --output_dir <SIM_OUT> --code <codes，与 live run.sh 一致> \
    <live 交易参数...> \
    --decision_on_update_only=true --latency_ms 100.0 --fee_ratio 0.00015 --split \
    > "$LOG_FILE" 2>&1 || true   # 兜住已知 shutdown segfault（rc=139/134）
```

输出目录约定：`/data/db/hft/` 下自建工作目录（临时数据放 `/data/db/hft/temp/`），**禁止 /tmp**。

### Step 2: 安全 grep 闸（强制，启动后立即执行）

```bash
# 危险签名——出现任意一个 → 立即 pkill 该进程并停止，向用户报告
grep -E "OnlineRunner|TraderApi|Connecting to broker" "$LOG_FILE"

# 安全签名——必须出现（纯回测）
grep -E "\[BacktestRunner\]|\[DualRunner\] BACKTEST mode" "$LOG_FILE"
grep -E "Using Parquet loader|balance=10000000" "$LOG_FILE"
```

长回测（多日期批量）建议先单日 dry-run 过闸，再批量。

### Step 3: 退出码与产物验证

- 已知问题：`Backtest finished` 后 DualRunner teardown segfault（rc=139/134），**产物已写完，不影响结果**。
- 验证产物存在且非空：
  ```
  <SIM_OUT>/matcher/backtest_entrust_all.parquet
  <SIM_OUT>/matcher/backtest_trade_all.parquet
  <SIM_OUT>/matcher/backtest_stats_all.parquet
  ```
  （含 md_id / exch_ts / local_ts / bid1 / ask1 / pos / pnl 等列。）

## 与其他回测 skill 的分工

- 本 skill：**本机、策略二进制级**回测（live 策略行为复现 / SDK fix 验证 / 日报 sim 侧）。
- `/hft-remote-backtest`：交易机上 DualRunner 回测（需要生产参数或交易机独有数据时）。
- `/hft-playground-signalreplay-backtest`：Analyzer2 SignalPack 信号回放（因子/信号研究）。

## 背景

2026-06-01 曾误用 `baseline_150_trader_online` 跑回测，开了非预期 broker 连接进程（即时 kill、0 下单）。本 skill 将二进制选择规则与 grep 闸固化为强制流程。相关记录见 hft-sdk-issues 对应 issue。
