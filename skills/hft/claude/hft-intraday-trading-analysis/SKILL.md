---
name: hft-intraday-trading-analysis
description: "盘中从交易机拉取 Benchmark100Trader 实时日志和 Session CSV，运行轻量分析脚本，输出 Roundtrip 明细、PnL、撤单率、信号 Score 和延迟统计。适用于交易时段内快速了解策略运行状态。"
argument-hint: "[date: YYYYMMDD, 默认=今天]"
---

# HFT 盘中交易分析

## 概述

盘中实时分析流程：从交易机拉取当前 strategy.log 和 session CSV，运行 `analyze_intraday.py` 脚本，将脚本输出的全部数据用 Markdown 格式整理后展示给用户。不归档日志、不生成图表、不写入报告文件。

与 `hft-daily-trading-report` 的区别：
- **本 skill**: 盘中使用，只读拉取，轻量文本输出
- **daily report**: 盘后使用，归档日志，生成 8 张图表和完整 Markdown 报告

## 安全红线（必须遵守）

1. **严禁修改交易机上的任何文件**，本 skill 为纯只读操作。
2. **严禁归档或移动交易机上的日志**（盘中策略仍在运行）。
3. **严禁修改交易机上非 `cken_strategy_*` 目录的任何内容**。
4. 本地临时数据写入 `/data/db/hft/temp/`，**不要写入 `/tmp`**。

## 参数

- `$ARGUMENTS`: 交易日期，格式 `YYYYMMDD`。为空时默认使用当天日期。
- 日期确定方式: `DATE=${ARGUMENTS:-$(date +%Y%m%d)}`

## 连接信息

```
交易机: sshpass -p 'quant4free' ssh -o StrictHostKeyChecking=no -p 2222 userlgj@localhost
SCP:    sshpass -p 'quant4free' scp -o StrictHostKeyChecking=no -P 2222
```

凭据来源: `~/.hft/credentials.env`（密码 = `quant4free`）

## 路径约定

| 用途 | 交易机路径 | 本地路径 |
|------|-----------|---------|
| 策略日志（运行时） | `/home/userlgj/app/strategy/cken_benchmark0323_v0/log/strategy.log` | `/data/db/hft/temp/strategy_log_{DATE}.log` |
| Session CSV | `/home/userlgj/hft_deploy/trading_logs/{DATE}/session_*_Benchmark100Trader.csv` | `/data/db/hft/temp/trading_csv_{DATE}.csv` |

## 执行步骤

### Step 1: 确定日期

```bash
DATE=${ARGUMENTS:-$(date +%Y%m%d)}
```

### Step 2: 检查 SSH 连接

```bash
sshpass -p 'quant4free' ssh -o StrictHostKeyChecking=no -p 2222 userlgj@localhost 'echo OK'
```

如果 SSH 连接失败，提示用户检查交易机是否在线及 SSH 隧道是否已建立。可建议使用 `/hft-vpn-tunnel-restore` skill 恢复隧道。

### Step 3: 拉取数据文件到本地

```bash
SCP_CMD="sshpass -p 'quant4free' scp -o StrictHostKeyChecking=no -P 2222"

# 1. 策略日志（当前运行中的 strategy.log）
$SCP_CMD userlgj@localhost:/home/userlgj/app/strategy/cken_benchmark0323_v0/log/strategy.log \
         /data/db/hft/temp/strategy_log_${DATE}.log

# 2. Session CSV（文件名含动态 session_id，用通配符）
$SCP_CMD "userlgj@localhost:/home/userlgj/hft_deploy/trading_logs/${DATE}/session_*_Benchmark100Trader.csv" \
         /data/db/hft/temp/trading_csv_${DATE}.csv
```

拉取后验证文件存在且非空：

```bash
ls -la /data/db/hft/temp/strategy_log_${DATE}.log /data/db/hft/temp/trading_csv_${DATE}.csv
wc -l /data/db/hft/temp/strategy_log_${DATE}.log /data/db/hft/temp/trading_csv_${DATE}.csv
```

如果任一文件缺失（如策略当天未运行或 CSV 尚未生成），向用户报告并尽量用已有数据继续。

### Step 4: 运行分析脚本

```bash
python3 /home/cken/.claude/skills/hft-intraday-trading-analysis/scripts/analyze_intraday.py \
    --log /data/db/hft/temp/strategy_log_${DATE}.log \
    --csv /data/db/hft/temp/trading_csv_${DATE}.csv \
    --date ${DATE}
```

脚本输出 7 个章节的文本报告：
1. 基本概况（策略参数、交易窗口、初始余额、事件计数）
2. PnL 汇总（总 PnL、胜率、各代码 PnL、未平仓头寸）
3. Roundtrip 逐笔明细（entry score、延迟、持仓时间、PnL bps）
4. 撤单率分析（ENTRY/EXIT 分别统计、各代码细分、撤单原因分布、EXIT_REPRICE）
5. 信号 Score 分析（分布统计、成交 vs 撤单对比、score vs PnL 关联）
6. 延迟分析（决策延迟 percentile、下单链路延迟、各代码细分、成交订单完整链路）
7. 各代码活跃度汇总

### Step 5: 用 Markdown 格式整理并输出完整结果

将脚本输出的全部数据用 Markdown 重新排版后展示给用户。**数据完整性是第一优先级，不得省略任何章节或数据行。**

具体格式要求：

1. **全部 7 个章节必须完整展示**，每个章节用 `##` 标题分隔。
2. **表格化数据**: 将脚本中的对齐文本转为 Markdown 表格，提升可读性。例如：
   - Roundtrip 逐笔明细 → 表格（列: 代码, RT#, BUY价/时间, SELL价/时间, PnL, bps, 持仓时间, score, entry延迟, exit延迟, 结果）
   - 各代码撤单率 → 表格（列: 代码, 下单, 成交, 撤单, 撤单率）
   - 延迟 percentile → 表格（列: 指标, Min, P25, P50, P75, P90, P99, Max, Mean）
   - 成交订单完整链路 → 表格（列: ref, 代码, 方向, submit→ack, submit→accepted, submit→fill）
   - 各代码活跃度 → 表格
   - score vs PnL → 表格
3. **不得省略或摘要**: 每个 Roundtrip、每个代码的撤单率、每个 percentile 值、每条成交链路都必须展示。
4. **异常提醒放在最后**: 全部数据展示完毕后，在末尾用 `## 异常提醒` 章节补充分析（如未平仓头寸、高撤单率代码、异常延迟、大亏单等）。

## UNKNOWN 成交说明

日志中可能出现 `FILL,UNKNOWN,ref=0` 的成交记录。这些是同账户 ScoreMaker 策略的成交（通常为 security_id=127070），不属于 Benchmark100Trader，在分析中已自动分离（归入 `unknown_fills`）。

## 边界情况处理

| 情况 | 检测方法 | 处理 |
|------|---------|------|
| 策略当天未运行 | `strategy.log` 不含目标日期的时间戳 | 向用户报告"策略未运行" |
| Session CSV 不存在 | SCP 失败 | 仅基于策略日志分析，跳过 CSV 延迟章节 |
| 非交易日 | 无策略日志或日志为空 | 向用户报告"非交易日" |
| SSH 隧道断开 | SSH 连接失败 | 建议使用 `/hft-vpn-tunnel-restore` |
| 零成交 | 分析脚本检测 | 正常输出，标注"暂无完成的 Roundtrip" |

## 注意事项

1. **纯只读操作**: 不归档、不修改、不删除交易机上任何文件
2. **临时文件**: 所有数据写入 `/data/db/hft/temp/`，不要写入 `/tmp`
3. **编码**: 读取日志文件时使用 `encoding='utf-8', errors='replace'`（日志可能含非 UTF-8 字节）
4. **时区**: 所有时间为 UTC+8
5. **可重复拉取**: 盘中可多次执行以获取最新数据，新数据会覆盖 temp 目录中的旧文件
