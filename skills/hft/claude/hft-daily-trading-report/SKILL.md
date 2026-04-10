---
name: hft-daily-trading-report
description: "每日盘后从交易机拉取 Benchmark100Trader 实盘数据，归档日志，运行分析并生成包含图表的每日交易报告。适用于收盘后执行，生成报告到 /home/cken/hft_projects/daily_trading_report/{yyyymmdd}/。"
argument-hint: "[date: YYYYMMDD, 默认=今天]"
disable-model-invocation: true
---

# HFT 每日交易报告生成

## 概述

盘后自动化流程：从交易机拉取当日实盘数据，归档策略日志，运行全量分析，生成包含图表和 Markdown 报告的每日交易报告。

## 安全红线（必须遵守）

1. **严禁删除交易机上的任何数据文件**，归档日志使用 `cp` 而非 `mv`。
2. **严禁修改交易机上非 `cken_strategy_*` 目录的任何内容**。
3. 本地临时数据写入 `/data/db/hft/temp/`，**不要写入 `/tmp`**。
4. 如果报告目录已存在，先确认用户是否覆盖。

## 参数

- `$ARGUMENTS`: 交易日期，格式 `YYYYMMDD`。为空时默认使用当天日期。
- 日期确定方式: `DATE=${ARGUMENTS:-$(date +%Y%m%d)}`

## 前置检查

在开始前逐项确认：

```bash
which sshpass                          # sshpass 已安装
sshpass -p 'quant4free' ssh -o StrictHostKeyChecking=no -p 2222 userlgj@localhost 'echo OK'  # SSH 可连
ls /data/db/hft/live_data/             # 本地存储路径可用
```

如果 SSH 连接失败，提示用户检查交易机是否在线及 SSH 隧道是否已建立。

## 连接信息

```
交易机: sshpass -p 'quant4free' ssh -o StrictHostKeyChecking=no -p 2222 userlgj@localhost
SCP:    sshpass -p 'quant4free' scp -o StrictHostKeyChecking=no -P 2222
```

凭据来源: `~/.hft/credentials.env`（密码 = `quant4free`）

## 路径约定

| 用途 | 交易机路径 | 本地路径 |
|------|-----------|---------|
| 策略日志（运行时） | `/home/userlgj/app/strategy/cken_benchmark0323_v0/log/strategy.log` | — |
| 策略日志（归档后） | `/home/userlgj/app/strategy/cken_benchmark0323_v0/log/{YYYYMMDD}.log` | `/data/db/hft/live_data/{YYYYMMDD}/strategy_log_final.out` |
| Session CSV | `/home/userlgj/hft_deploy/trading_logs/{YYYYMMDD}/session_*_Benchmark100Trader.csv` | `/data/db/hft/live_data/{YYYYMMDD}/` |
| Orders CSV | `/home/userlgj/hft_deploy/trading_data/orders_{YYYYMMDD}.csv` | `/data/db/hft/live_data/{YYYYMMDD}/` |
| Trades CSV | `/home/userlgj/hft_deploy/trading_data/trades_{YYYYMMDD}.csv` | `/data/db/hft/live_data/{YYYYMMDD}/` |
| 报告输出 | — | `/home/cken/hft_projects/daily_trading_report/{YYYYMMDD}/` |

## 执行步骤

### Step 1: 确定日期并创建本地目录

```bash
DATE=<YYYYMMDD>  # 从参数获取或默认今天
mkdir -p /data/db/hft/live_data/${DATE}
mkdir -p /home/cken/hft_projects/daily_trading_report/${DATE}
```

### Step 2: 归档交易机上的策略日志

将交易机上的 `strategy.log` 重命名归档为 `{YYYYMMDD}.log`，防止被下次交易覆盖：

```bash
# 检查 strategy.log 是否存在且包含当天数据
SSH_CMD="sshpass -p 'quant4free' ssh -o StrictHostKeyChecking=no -p 2222 userlgj@localhost"
$SSH_CMD "head -5 /home/userlgj/app/strategy/cken_benchmark0323_v0/log/strategy.log"

# 归档: 复制为 YYYYMMDD.log（保留原文件以防策略仍在运行）
$SSH_CMD "cp /home/userlgj/app/strategy/cken_benchmark0323_v0/log/strategy.log \
             /home/userlgj/app/strategy/cken_benchmark0323_v0/log/${DATE}.log"
```

**注意**: 使用 `cp` 而非 `mv`，避免策略进程仍在写入时丢失文件句柄。确认策略已停止后可改用 `mv`。

### Step 3: 拉取全部数据文件到本地

```bash
SCP_CMD="sshpass -p 'quant4free' scp -o StrictHostKeyChecking=no -P 2222"

# 1. 策略日志
$SCP_CMD userlgj@localhost:/home/userlgj/app/strategy/cken_benchmark0323_v0/log/${DATE}.log \
         /data/db/hft/live_data/${DATE}/strategy_log_final.out

# 2. Session CSV（文件名含动态 session_id，用通配符）
$SCP_CMD "userlgj@localhost:/home/userlgj/hft_deploy/trading_logs/${DATE}/session_*_Benchmark100Trader.csv" \
         /data/db/hft/live_data/${DATE}/

# 3. Orders CSV
$SCP_CMD userlgj@localhost:/home/userlgj/hft_deploy/trading_data/orders_${DATE}.csv \
         /data/db/hft/live_data/${DATE}/

# 4. Trades CSV
$SCP_CMD userlgj@localhost:/home/userlgj/hft_deploy/trading_data/trades_${DATE}.csv \
         /data/db/hft/live_data/${DATE}/
```

拉取后验证：

```bash
ls -la /data/db/hft/live_data/${DATE}/
wc -l /data/db/hft/live_data/${DATE}/*
```

**预期文件**:
- `strategy_log_final.out` (策略日志, 通常 1000-5000 行)
- `session_*_Benchmark100Trader.csv` (事件流, 纳秒级时间戳)
- `orders_${DATE}.csv` (全账户订单)
- `trades_${DATE}.csv` (全账户成交, 可能为空)

如果任何文件缺失或为空，向用户报告并继续处理已有数据。

### Step 4: 快速预览数据

在编写报告脚本前，先做数据预览以了解当天情况：

```bash
# 日志时间范围
head -3 /data/db/hft/live_data/${DATE}/strategy_log_final.out
tail -5 /data/db/hft/live_data/${DATE}/strategy_log_final.out

# 信号/成交/错误计数
grep -c "Benchmark100Trader" /data/db/hft/live_data/${DATE}/strategy_log_final.out
grep -c "TRADE_EXECUTION" /data/db/hft/live_data/${DATE}/strategy_log_final.out
grep -c "资金不足" /data/db/hft/live_data/${DATE}/strategy_log_final.out

# Session CSV 行数
wc -l /data/db/hft/live_data/${DATE}/session_*_Benchmark100Trader.csv
```

### Step 5: 编写并运行报告生成脚本

参考已有报告生成脚本的模式（如 `/data/db/hft/temp/generate_daily_report.py`），编写当天的报告生成脚本。脚本保存到报告输出目录。

**数据源优先级**:
1. **Session CSV** (主数据源): 纳秒级时间戳，精确订单生命周期
2. **strategy_log_final.out**: 策略信号（含 `lat_us` 信号新鲜度）、拒单原因、错误详情
3. **orders CSV**: 全账户订单视图（含 lgj 策略）

**策略信号日志格式**:
```
[Benchmark100Trader] ENTRY,MAKER,CODE,ref=xxx,vol=10,px=xxx.xxx,ask=xxx.xxx,score=xx.xx,thr=10.0,lat_us=xxx
[Benchmark100Trader] EXIT,MARKET,CODE,ref=xxx,vol=10,px=xxx.xxx,score=xx.xx,thr=-5.0,lat_us=xxx
```

关键字段:
- `score`: 信号得分 (bps)
- `lat_us`: **信号新鲜度** — 信号时间戳与下单指令发出时刻的时间差（微秒），反映信号从产生到执行的延迟

**B150 与 lgj 成交分离**:
- 优先使用 session CSV 的 `strategy_id` 列区分
- 若 `strategy_id` 不可用，根据 `ORDER_SUBMIT` 中的 `(order_ref, security_id)` 与 `TRADE_REPORT` 交叉匹配

**脚本输出** (保存到 `/home/cken/hft_projects/daily_trading_report/{YYYYMMDD}/`):

报告文件:
- `report_{YYYYMMDD}.md` — 主报告 Markdown
- `roundtrip_detail_{YYYYMMDD}.md` — Roundtrip 生命周期明细

图表文件 (8 张 PNG):
- `dashboard.png` — 6 面板总览
- `chart_cumulative_pnl.png` — 累计 PnL 曲线
- `chart_pnl_by_code.png` — 各标的 PnL 柱状图
- `chart_roundtrip_waterfall.png` — Roundtrip 瀑布图
- `chart_holding_time.png` — 持仓时间分布
- `chart_latency.png` — 延迟分布 (Submit→ACK / Submit→Accepted / Submit→Fill)
- `chart_fill_timeline.png` — 成交时间轴
- `chart_order_by_code.png` — 各标的订单结果 (成交/撤单/拒单)

脚本文件:
- `generate_report.py` — 报告生成脚本（保留以便复现）
- `generate_roundtrip_detail.py` — 明细报告生成脚本

### Step 6: 报告内容要求

主报告 (`report_{YYYYMMDD}.md`) 必须包含以下章节:

```
# Benchmark100Trader 实盘日报 — {YYYY-MM-DD}

> 元数据: 生成时间, 策略, 账户, 初始余额
> 数据文件表（路径 + 大小）

## 一、交易概览        （Dashboard 图 + 核心指标表）
## 二、信号分布        （信号类型 + 各标的分布, 含 order-by-code 图）
## 三、全部成交明细    （B150 + lgj, 含 fill timeline 图）
## 四、Roundtrip 分析  （逐笔明细 + 各标的汇总, 含 waterfall + pnl-by-code 图）
## 五、盈亏统计        （含 cumulative PnL 图）
## 六、持仓时间分析    （含 holding time 图）
## 七、延迟分析
###  7.1 订单延迟      （含 latency 图, 基于 session CSV 纳秒时间戳: Submit→ACK / Submit→Accepted / Submit→Fill）
###  7.2 信号新鲜度    （基于策略日志 lat_us 字段, 详见下方说明）
## 八、全账户订单概览  （orders CSV 统计）
## 九、分析结论与改进建议（含与前日对比）
## 十、错误分析        （资金不足分布 + 错误分类）
## 附录              （数据文件路径, 策略参数, Universe）
```

**§7.2 信号新鲜度 (lat_us) 必须包含**:

从策略日志的 `lat_us` 字段提取信号新鲜度（信号时间戳与下单指令发出时刻的时间差，微秒）。

1. **总体统计表**: 按 ENTRY / EXIT / ALL 分组，给出样本数、最小、中位、平均、P95、最大
2. **各标的新鲜度**: 按 Code 分组，给出每个标的的信号数、中位/平均/最大 lat_us
3. **成交 vs 撤单对比**: 对比成交订单和撤单订单对应信号的 lat_us 分布（中位、平均），分析信号新鲜度对成交率的影响
4. **异常值列表**: 列出 lat_us > 1000us（即 >1ms）的信号详情（时间、类型、Code、lat_us、score）

Roundtrip 明细报告 (`roundtrip_detail_{YYYYMMDD}.md`) 必须包含:

```
# 汇总表（含入场 lat_us、出场 lat_us 列）
# 每个 RT:
  - 概要（信号类型, 方向, 持仓时间）
  - 入场（所有尝试: 信号→下单→拒单/确认→撤单/成交，信号行显示 score 和 lat_us）
  - 出场（所有尝试: 信号→下单→撤单/成交, 包括失败尝试，信号行显示 score 和 lat_us）
  - 小结（入场价, 出场价, 滑点, 持仓时间, PnL, 信号新鲜度, 信号得分）
# 未平仓头寸（如有）
```

### Step 7: 验证并报告

生成完成后：

1. 验证所有文件存在:
```bash
ls -la /home/cken/hft_projects/daily_trading_report/${DATE}/
```

2. 检查图表是否正确生成（文件大小 > 10KB）

3. 向用户汇报:
   - 数据拉取是否成功（缺失文件?）
   - 核心指标: Roundtrip 数、总 PnL、胜率、成交率
   - 异常情况: 未平仓头寸、大量拒单、系统错误等
   - 与前一交易日的对比（如有历史数据）

## 策略参数参考

| 参数 | 值 | 说明 |
|------|-----|------|
| score_open_bps | 7.0 | 开仓阈值 |
| score_open_market_bps | 20.0 | MARKET 入场阈值 |
| score_hold_bps | -2.0 | 持仓阈值 |
| score_hysteresis_bps | 4.0 | 滞回阈值 |
| target_vol | 10 | 目标仓位量 |
| cancel_reduce_scheme | BE | 撤单方案 |
| cancel_confirm_bars | 5 | B scheme 确认 bars |
| cancel_immediate_bps | -1.0 | B scheme 立即撤单 |
| old_order_age_bars | 3 | E scheme 老单年龄 |

## 账户信息

| 项目 | 值 |
|------|-----|
| 交易账户 | 305000033735 |
| 股东号 | 0377353093 |
| Universe | 127037, 123131, 127076, 127053, 123239, 123129, 123209, 123237, 127095, 123080 |

## 历史报告参考

已生成的历史报告可作为格式和内容参考:
- 2026-02-10: `/home/cken/hft_projects/daily_trading_report/20260210/`
- 2026-02-11: `/home/cken/hft_projects/daily_trading_report/20260211/`
- 2026-02-24: `/home/cken/hft_projects/daily_trading_report/20260224/`

对应的报告生成脚本（**优先参考最新日期的脚本**）:
- `/home/cken/hft_projects/daily_trading_report/20260224/generate_report.py` （含信号新鲜度分析）
- `/home/cken/hft_projects/daily_trading_report/20260224/generate_roundtrip_detail.py` （含 lat_us / score）

生成新日期报告时，应参考最近一天的脚本并适配当天数据特征（如新的错误类型、不同的 B150/lgj 分离方式等）。

## 边界情况处理

| 情况 | 检测方法 | 处理 |
|------|---------|------|
| 策略当天未运行 | `strategy.log` 不含目标日期的时间戳 | 向用户报告"策略未运行"，跳过报告生成 |
| Session CSV 不存在 | SSH 检查 `ls` 目标目录 | 仅基于策略日志生成简化报告，标注"无 session 数据" |
| 非交易日（周末/节假日） | 无策略日志或日志为空 | 向用户报告"非交易日" |
| 已有归档日志 `{DATE}.log` | SSH 检查 `test -f` | 跳过归档步骤，直接拉取已归档文件 |
| 报告目录已存在 | `ls` 本地目录 | 询问用户是否覆盖 |
| Trades CSV 为空（仅 header） | `wc -l` ≤ 1 | 正常继续，跳过成交文件分析 |
| 零成交/零 roundtrip | 分析脚本检测 | 生成报告但标注"当日无完成 roundtrip"，避免除零错误 |

## 注意事项

1. **数据安全**: 使用 `cp` 归档交易机日志，不要 `mv`（防止策略进程仍在写入）
2. **临时文件**: 所有临时数据写入 `/data/db/hft/temp/`，不要写入 `/tmp`
3. **内存限制**: matplotlib 生成图表时注意内存，总内存占用不超过 180GB
4. **时区**: 所有时间使用 UTC+8
5. **语言**: 报告内容使用中文，代码注释使用英文
6. **编码**: 读取日志文件时使用 `encoding='utf-8', errors='replace'`（日志可能含非 UTF-8 字节）

## 完成检查清单

- [ ] SSH 连接成功，数据已拉取
- [ ] 交易机日志已归档为 `{YYYYMMDD}.log`
- [ ] 本地 `/data/db/hft/live_data/{YYYYMMDD}/` 包含所有可用数据文件
- [ ] 8 张图表均已生成且文件大小 > 10KB
- [ ] `report_{YYYYMMDD}.md` 包含全部 10 个章节 + 附录
- [ ] `report_{YYYYMMDD}.md` §7.2 信号新鲜度 (lat_us) 包含：总体统计表、各标的分组、成交vs撤单对比、异常值列表
- [ ] `roundtrip_detail_{YYYYMMDD}.md` 包含所有 RT 明细
- [ ] `roundtrip_detail_{YYYYMMDD}.md` 汇总表含入场/出场 lat_us 列，每个 RT 信号行显示 score + lat_us，小结含信号新鲜度
- [ ] 核心指标无异常（PnL、胜率、成交率均为有效数值）
- [ ] 已向用户汇报核心指标和异常情况
