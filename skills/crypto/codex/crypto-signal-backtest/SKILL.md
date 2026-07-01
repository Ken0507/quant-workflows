---
name: crypto-signal-backtest
description: "从 Analyzer LGBM 模型导出信号 → 并行回测 → 综合分析报告（train/valid、maker/taker、持仓分布）"
---
# Crypto Signal Backtest Skill

## 触发条件

用户要求对因子分析报告（Analyzer LGBM 模型）进行信号回放回测，并产出回测报告。

典型调用方式：
```
/crypto-signal-backtest /data/db/crypto/analyzer/fa1/fa1_v2_lgbm_only
```

参数：`<analyzer_report_dir>` — 包含 `lgbm_model.txt` 和 `lgbm_train_info.json` 的目录。

## 输入要求

### Analyzer Report 目录（必须存在）
- `lgbm_model.txt` — 训练好的 LightGBM 模型
- `lgbm_train_info.json` — 包含 features 列表、train_days、valid_days、params
- `report.md` — 用于提取元信息（data_root、subfolder、日期范围）

### 因子数据
- 路径从 `report.md` 的 Run Summary 中提取 `data_root` 和 `subfolder`
- 格式：`{data_root}/{date}/{subfolder}/{symbol}.parquet`

### 交易数据（系统默认）
- `/data/db/crypto/futures/binance_histroy/raw/trades/{symbol}/{symbol}-trades-{date}.feather`

## 执行步骤

### Phase 1: 解析参数

从 `<analyzer_report_dir>/report.md` 和 `lgbm_train_info.json` 提取：
- `data_root`, `subfolder` — 因子数据路径
- `start_date`, `end_date` — 回测日期范围
- `symbols` — 品种列表
- `train_days`, `valid_days` — 用于 train/valid 切分
- `features` — 特征列表

派生：
- `train_end` = train_days 最后一天（YYYY-MM-DD 格式）
- `valid_start` = valid_days 第一天（YYYY-MM-DD 格式）
- `report_name` = analyzer_report_dir 的最后两级路径（如 `fa1/fa1_v2_lgbm_only`）

### Phase 2: 导出信号

```bash
python /home/cken/crypto_world/zebra/scripts/export_signals_from_model.py \
  --model-dir <analyzer_report_dir> \
  --factor-root <data_root> \
  --subfolder <subfolder> \
  --output /home/cken/crypto_world/zebra/bt_signals/<signal_name> \
  --start <start_date> --end <end_date> \
  --symbols <symbols...>
```

其中 `signal_name` 从 report_name 派生（如 `fa1_v2_lgbm`）。

**验证**：检查输出目录非空，文件数 = n_days × n_symbols。

**必须排除 20251010**：信号导出完成后，删除 2025-10-10 目录（该日极端行情会严重污染回测结果）：
```bash
rm -rf /home/cken/crypto_world/zebra/bt_signals/<signal_name>/2025-10-10
```

### Phase 3: 编写回测脚本

在 `/home/cken/crypto_world/zebra/scripts/` 下创建运行脚本。

**必须参数化的配置（由用户确认或使用默认值）：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enable_long` | True | 是否开启多头 |
| `enable_short` | True | 是否开启空头 |
| `open_long_bps` | 5.0 | 开多阈值 |
| `close_long_bps` | 0.0 | 平多阈值 |
| `open_short_bps` | -5.0 | 开空阈值 |
| `close_short_bps` | 0.0 | 平空阈值 |
| `market_long_bps` | 15.0 | Taker 开多阈值 |
| `market_short_bps` | -15.0 | Taker 开空阈值 |
| `hysteresis_bps` | 3.0 | 撤单迟滞 |
| `latency_ms` | 50 | 延迟 |
| `notional_usdt` | 1000.0 | 每笔名义价值 |
| `use_maker_entry` | True | 入场用 maker |
| `use_maker_exit` | True | 出场用 maker |

输出目录：`/home/cken/crypto_world/zebra/bt_output/<bt_name>`

脚本使用 multiprocessing 并行跑 7 个 symbol。

### Phase 4: 运行回测

```bash
python /home/cken/crypto_world/zebra/scripts/<run_script>.py
```

**监控**：
- 使用 `ps aux | grep <script>` 监控进程
- 使用 `ls <output_dir>/ | grep stats` 监控完成的 symbol
- BTC 最慢（~55 min for 210 days），总计约 60 min

**等待所有 symbol 完成后继续。**

### Phase 5: 生成分析报告

```bash
python /home/cken/crypto_world/zebra/scripts/generate_bt_analysis.py \
  --output-dir <bt_output_dir> \
  --train-end <train_end> \
  --valid-start <valid_start> \
  --symbols <symbols...> \
  --title "<report_title>"
```

产出：
- `report.md` — 综合报告
- `dashboard.png` — 三面板仪表盘
- `metrics_daily.csv` — 日度指标
- `metrics_codes.csv` — 品种指标
- `roundtrips.csv` — 完整 roundtrip 明细

### Phase 6: 向用户汇报

展示关键结论：
1. **全量汇总**：Net PnL、Net Rate (bps)、Sharpe、MaxDD
2. **Train vs Valid**：是否有 alpha 衰减 / 过拟合
3. **Maker vs Taker**：哪种入场方式更赚钱
4. **持仓时间分布**：短持仓 vs 长持仓的盈利差异
5. **Per-symbol**：哪些品种好/差
6. **风险提示**：cancel rate 是否过高、sub-second RT 占比

## 输出目录结构

```
zebra/bt_output/<bt_name>/
├── report.md              # 综合分析报告
├── dashboard.png          # PnL 曲线 + 仪表盘
├── metrics_daily.csv      # 日度指标
├── metrics_codes.csv      # 品种指标
├── roundtrips.csv         # Roundtrip 明细
├── backtest_trade_*.parquet    # 成交记录
├── backtest_entrust_*.parquet  # 委托记录
└── backtest_stats_*.parquet    # 定期快照
```

## 数据纪律

- 回测日期范围：与 Analyzer 报告一致（通常 2025-07-01 ~ 2026-01-26）
- **必须剔除 20251010**：该日极端行情会严重污染回测结果（Phase 2 导出后立即删除）
- Train/Valid 切分：从 `lgbm_train_info.json` 读取，不硬编码
- 7 symbols：BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT

## 口径一致性（issue #119 之后）

- **Benchmark / fill basis**：与 analyzer 保持一致——**mid-based**。PnL 的参照价是 `basic_table.mid`，与训练时用的 mid-to-mid label 口径匹配。
- **Spread 扣费**：使用 `basic_table.spread_bps` 的 per-bar realtime spread（full spread = ask - bid），不再使用历史硬编码 per-symbol spread 常数。maker/taker 成本模型在此基础上叠加 fee。
- **basic_table 依赖**：回测运行同样需要 `/data/db/crypto/futures/world/world_pool/basic_table/{date}/basic_table/{sym}.parquet` 覆盖回测日期 × 7 symbols，缺失会导致 fill / 结算价失败。
- **不再需要 `--label-basis` 类参数**（analyzer / signal export 上游已下线），回测脚本继承默认 mid 口径即可。

## 关键代码路径

| 文件 | 用途 |
|------|------|
| `zebra/scripts/export_signals_from_model.py` | 从训练好的模型导出信号 |
| `zebra/scripts/generate_bt_analysis.py` | 综合分析报告生成 |
| `zebra/bt/config.py` | 回测配置（含 enable_long/enable_short） |
| `zebra/bt/strategy/signal_triggered.py` | 信号驱动策略 |
| `zebra/bt/runner.py` | 回测主循环 |
| `zebra/bt/reporting/` | 报告生成框架 |

## 禁止操作

1. 不要修改 analyzer 报告目录中的任何文件
2. 不要修改因子数据或交易数据
3. 不要在回测脚本中硬编码日期——从 analyzer 报告中读取
4. 不要跳过 Phase 5 的分析报告直接汇报——必须先生成完整报告

## Changes after issue #119 (2026-04-19)

- **Benchmark / fill basis 切换为 mid**（`basic_table.mid`），与 analyzer 训练时的 mid-to-mid label 一致。原 close-based 回测路径已下线。
- **Spread 扣费切换为 per-bar realtime**（`basic_table.spread_bps`），替代历史硬编码 per-symbol spread 常数。净收益公式与 analyzer 对齐：`net = fwd_mid_ret - spread_bps - fee`。
- **basic_table 强依赖**：回测日期 × 7 symbols 的 `basic_table` 必须齐全，缺失即报错。运行前可用 `ls /data/db/crypto/futures/world/world_pool/basic_table/<date>/basic_table/` 快速验证。
- **`--label-basis` 之类的参数已由上游 analyzer 下线**，信号/回测脚本不再需要该参数。
