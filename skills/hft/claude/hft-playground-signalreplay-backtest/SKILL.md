---
name: hft-playground-signalreplay-backtest
description: 使用 Playground 的 batch-backtest 调用 HftAnalyzer2 的 SignalReplay 策略，将 Analyzer2 导出的 SignalPack（bar_ffill 或 tick_predict）进行信号回放回测。⚠️ 仅限**信号相对比较**（同引擎比较多个信号强弱）；**绝对 PnL 结论一律禁止用本 skill**——必须改用 live_v2 trader 的信号注入模式（--inject_signal_pack_dir，见 #179），且 HftAnalyzer2 v20260712.1 之前的所有 SignalReplay 结果因堆仓 bug 作废。必须严格以 /home/cken/hft_projects/HftAnalyzer2/docs/howto_playground_backtest_signalreplay_zh.md 为唯一口径并按其流程执行（如与本 Skill 冲突，以文档为准）。
---

# Playground + SignalReplay：批量回测（按文档执行）

## ⚠️ 适用范围红线（2026-07-12，#179 定稿）

- **本 skill 的产出只允许用于"信号相对比较"**（同一引擎下比较多个信号/多组参数的相对强弱）。**任何绝对 PnL / 赚不赚钱的结论禁止引用本 skill 的数字**——SignalReplay 是简化执行层，实测比生产 trader 系统性乐观（缺 BE 平仓、撤单龄、退出 reprice 等机制）。
- 绝对 PnL 评估的唯一合法仪器：**live_v2 trader 信号注入模式**（`run_baseline_150_trader --inject_signal_pack_dir <pack>`，HFTPool commit e68320a；执行语义 = #171 实盘对账验证过的生产机器）。
- **HftAnalyzer2 v20260712.1 之前的所有 SignalReplay 历史结果作废**（堆仓 bug：单 code 持仓可叠数百张）。引用任何历史回测前先核对版本。
- 任何新回放/策略 agent 的数字被引用前，必须通过 howto §6.7 的"同信号双引擎对照"验收。

## 强制原则（必须遵守）

1) 执行任何命令前，先打开并通读文档：`/home/cken/hft_projects/HftAnalyzer2/docs/howto_playground_backtest_signalreplay_zh.md`（重点 §6.6 仓位语义 / §6.7 验收纪律）  
2) 本 Skill 只提供“操作框架/检查清单”；若与文档口径不一致，以文档为准并同步更新本 Skill  
3) 所有回测产物输出到**新目录**（避免覆盖既有回测结果）  
4) 每次实验记录 UTC+8 时间戳（建议写到研究目录 `research_log.md`）  

## 工作流（推荐走脚本口径）

### 1) 确认输入与口径（从文档中抄，不要凭记忆）

- 确认 `signal_pack_dir`（bar_ffill / tick_predict 对应不同目录）
- 确认日期区间（`start_date/end_date`）
- 确认 universe：使用 `--universe bond_sz`（全市场）
- 确认 workers：默认用 **30**（如需调整，先看文档对 RSS/峰值内存的提示）

### 2) 环境准备（必须）

```bash
source /data/share/dev/hft/setup_sdk.sh
which playground
```

### 3) 一键回测（首选）

按文档第 5 节使用仓库脚本（包含 build + RSS guard + batch-backtest）：

- `cd /home/cken/hft_projects/HftAnalyzer2/playground_projects/signal_replay`
- 按需设置环境变量：`BAR_FFILL_DIR` / `TICK_PRED_DIR` / `OUT_ROOT`
- 运行：`bash run_batch_backtest.sh {bar_ffill|tick_predict|both} <start_date> <end_date> 30`

### 4) 自检与交付（必须）

- 检查输出目录包含：`report.md`、`metrics.csv`、`dashboard.png`、`rss_guard_profile.json`
- 如需快速统计 `no_trade_days`、总收益、总手续费，运行：

```bash
python /home/cken/.codex/skills/hft-playground-signalreplay-backtest/scripts/verify_backtest_output.py /path/to/output_dir
```

## 参数扫参（需要改 pass-through 时）

当需要扫 `--score_open_bps` / `--score_open_market_bps` / `--score_hold_bps` 等策略参数时：

1) 优先使用文档第 6 节“手动命令模板”，在 `--pass-through` 里追加需要扫的参数  
2) 每组参数独立输出到一个新目录，并保留 `rss_guard_profile.json` 作为可复现凭据  

常见示例：双阈值开仓（thres1 用原 LIMIT，thres2 改 MARKET）：

- 追加到 `--pass-through`：`--score_open_bps=7 --score_open_market_bps=20 --score_hold_bps=-2`
- 默认 `--score_open_market_bps=0`：不开启 MARKET 开仓，保持旧行为（务必以文档口径为准）

## 资源

- `scripts/verify_backtest_output.py`：检查产物完整性并打印 metrics 汇总（Net=Gross-Fee）
- `references/paths.md`：关键路径速查（文档/脚本/工具）
