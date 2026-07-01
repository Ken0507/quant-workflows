---
name: crypto-zebra-factor-batch-run
description: "使用 Zebra batch_runner 批量刷因子数据。处理编译验证、日期范围、chunk 配置、L2 数据、输出路径、manifest 管理。调用前需要已通过 crypto-zebra-factor-write 的 smoke test。"
---
# Zebra 批量因子生成

## 0. 前置检查

在执行批量刷因子之前，必须完成以下验证：

1. **Binary 存在且可执行**
   ```bash
   BINARY="/home/cken/crypto_world/zebra_pool/${fa_lower}/code/build/batch_runner"
   test -x "$BINARY" || { echo "ERROR: binary not found or not executable: $BINARY"; exit 1; }
   ```

2. **Smoke test 已通过**
   - 确认之前已通过 `crypto-zebra-factor-write` skill 中的 smoke test（单 symbol 单天运行 + schema 验证）。
   - 如果不确定，先对 BTCUSDT 单天跑一次确认输出无误：
     ```bash
     $BINARY --symbol BTCUSDT --date 2024-06-01 \
         --threshold-dir /data/db/crypto/futures/world/bod_data/daily_thres_28800 \
         --output_dir /tmp/smoke_${fa_lower} \
         --l2-root /data/db/crypto/futures/tardis/binance-futures/incremental_book_L2
     ```

3. **Threshold 文件覆盖日期范围**
   - threshold 目录：`/data/db/crypto/futures/world/bod_data/daily_thres_28800`
   - 检查 start_date 和 end_date 对应的 threshold 文件均存在：
     ```bash
     THRES_DIR="/data/db/crypto/futures/world/bod_data/daily_thres_28800"
     ls "$THRES_DIR/${start_date}.parquet" "$THRES_DIR/${end_date}.parquet"
     ```
   - 如果缺失会导致 batch_runner 报错退出（`threshold_missing_policy = "error"`）。

---

## 1. 批量执行（推荐：并行 launcher）

生产刷因子默认使用 `parallel_batch_runner.py`——它把 `(symbol × 日期窗口)` 按权重分片后并发拉起多个 `batch_runner` 子进程，整体比单进程快 N 倍（N ≈ workers）。

### 1.1 命令模板（并行）

```bash
python /home/cken/crypto_world/zebra/tools/parallel_batch_runner.py \
    --binary /home/cken/crypto_world/zebra_pool/${fa_lower}/code/build/batch_runner \
    --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT \
    --start_date ${start_date} \
    --end_date ${end_date} \
    --threshold-dir /data/db/crypto/futures/world/bod_data/daily_thres_28800 \
    --output_dir /data/db/crypto/futures/world/world_pool/${fa_lower} \
    --l2-root /data/db/crypto/futures/tardis/binance-futures/incremental_book_L2 \
    --chunk-days ${chunk_days} \
    --workers 30 \
    --skip_existing \
    --manifest /data/db/crypto/futures/world/world_pool/${fa_lower}/manifest.json
```

### 1.2 分片策略（重要）

- **分片单元**：`(symbol, 连续日期子窗口)`。每个分片对应一个独立的 `batch_runner` 子进程。
- **权重**：每个 symbol 的权重 = 日期范围内 `{data_root}/{symbol}/{symbol}-trades-{date}.feather` 文件总大小。
- **分配算法**：初始每个 symbol 分到 1 片；剩余 `workers - N_symbols` 个 slot 按贪心分配——每轮挑当前 `weight/k` 最大的 symbol 增加一片。所以**权重大的 symbol（如 BTCUSDT / ETHUSDT）会被切得更多**，小币可能只保留 1 片。
- **日期切分**：每个 symbol 的日期范围按最终 `k` 均分成连续子窗口（余数优先分给前面几段）。
- **示例**：7 symbols + `--workers 30`，BTC 权重远大于其他：BTC 可能被切成 ~14 片、ETH ~7 片、其余各 1–3 片，总片数 = 30。
- **Chunk 状态**：每个分片是独立子进程，agent 状态不跨分片持久化。即如果你传了 `--chunk-days 30`，每个子进程内部仍按 30 天一个 chunk 运行；但分片与分片之间 EMA / rolling 会冷启动。对性能敏感的 EMA 因子，建议 `chunk_days` 保持一致或把窗口设小一点接受冷启动代价。

### 1.3 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--binary` | `batch_runner` 可执行文件路径（必须） | 无默认 |
| `--symbols` | 7 个标准 universe，逗号分隔 | 全部 7 个 |
| `--start_date` / `--end_date` | 日期范围 YYYY-MM-DD | 通常 `2024-01-01` ~ `2026-03-31` |
| `--threshold-dir` | 动态阈值目录（必须） | 无默认 |
| `--output_dir` | 输出根目录 | `world_pool/${fa_lower}` |
| `--l2-root` | L2 订单簿数据根目录 | 可选（纯 trade 因子可省略） |
| `--chunk-days` | 透传给每个子进程的 chunk 天数 | `0` |
| `--workers` | 并发子进程数（分片总数） | `30` |
| `--data_root` | Trade 数据根目录（用于权重估算 + 透传给子进程） | `/data/db/crypto/futures/binance_histroy/raw/trades` |
| `--skip_existing` | 透传 | 建议始终启用 |
| `--manifest` | 合并后 manifest 路径 | 可选 |
| `--log-dir` | 每个分片的日志目录 | `<output_dir>/parallel_logs` |

### 1.4 输出产物

- **日志**：每个分片一个 `{symbol}_{idx:04d}.log`，默认落在 `<output_dir>/parallel_logs/` 下。第一行是完整命令行，后面是子进程 stdout+stderr 合流。
- **Manifest**：
  - 每个分片自己的 manifest 落在 `<manifest>.shards/{symbol}_{idx:04d}.json`。
  - launcher 最后合并所有子 manifest 到 `--manifest` 指定的路径（entries 拼接、statistics 累加）。
- **控制台输出**：启动时打印分片分配表（每个 symbol 几片 + 权重），运行时每个分片完成打印 `[i/N] symbol start..end OK/FAIL elapsed`，结束打印汇总和失败分片列表。

### 1.5 回退：单进程直接调用 batch_runner

仅用于调试 / smoke test / 只跑单 symbol 单天。生产刷全历史请用并行 launcher。

```bash
/home/cken/crypto_world/zebra_pool/${fa_lower}/code/build/batch_runner \
    --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT \
    --start_date ${start_date} \
    --end_date ${end_date} \
    --threshold-dir /data/db/crypto/futures/world/bod_data/daily_thres_28800 \
    --output_dir /data/db/crypto/futures/world/world_pool/${fa_lower} \
    --l2-root /data/db/crypto/futures/tardis/binance-futures/incremental_book_L2 \
    --chunk-days ${chunk_days} \
    --skip_existing \
    --manifest /data/db/crypto/futures/world/world_pool/${fa_lower}/manifest.json
```

此模式下是单进程串行：外层遍历 symbols、内层遍历 dates。完整覆盖 7 × 820 天约需要 N 小时（以具体因子复杂度为准）。

### 1.3 chunk-days 建议

- **默认 `--chunk-days 0`**：整个日期范围作为一个 chunk。推荐用于生产刷因子，因为 EMA / rolling 状态跨天连续，不会有冷启动。
- **日期范围 > 60 天且内存紧张**：考虑 `--chunk-days 30`。每 30 天一个 chunk，chunk 边界处有 EMA 冷启动代价（前几个 bar 数据不准确，可接受）。
- **调试**：`--chunk-days 7` 或 `--chunk-days 15`，快速验证跨天逻辑。

### 1.4 输出路径规范

输出落地到：
```
/data/db/crypto/futures/world/world_pool/${fa_lower}/
└── {YYYY-MM-DD}/
    └── {factor_group_name}/
        ├── BTCUSDT.parquet
        ├── ETHUSDT.parquet
        ├── SOLUSDT.parquet
        ├── BNBUSDT.parquet
        ├── XRPUSDT.parquet
        ├── DOGEUSDT.parquet
        └── ADAUSDT.parquet
```

其中 `{factor_group_name}` 等于 Agent 的 `factor_group_name()` 返回值（即 `${fa_lower}` 本身，如 `fa03`）。

### 1.5 L2 数据

- `--l2-root` 仅在 Agent 实现了 `RequiresOrderBook() == true` 时需要。
- 如果全部 Agent 都是纯 trade 因子，可以省略 `--l2-root`。
- L2 数据覆盖范围有限（Tardis 数据），超出范围的天 Agent 须通过 `ctx.HasBook()` 守卫处理缺失。

---

## 2. 输出验证

批量刷因子完成后，执行以下验证：

### 2.1 文件完整性

检查每天每个 symbol 的 parquet 文件存在：

```python
import os
from datetime import datetime, timedelta

fa_id = "${fa_lower}"
factor_group = "${fa_lower}"  # factor_group_name() 返回值
output_root = f"/data/db/crypto/futures/world/world_pool/{fa_id}"
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]

start = datetime.strptime("${start_date}", "%Y-%m-%d")
end = datetime.strptime("${end_date}", "%Y-%m-%d")
d = start
missing = []
while d <= end:
    ds = d.strftime("%Y-%m-%d")
    for sym in symbols:
        path = os.path.join(output_root, ds, factor_group, f"{sym}.parquet")
        if not os.path.exists(path):
            missing.append(f"{ds}/{sym}")
    d += timedelta(days=1)

if missing:
    print(f"MISSING {len(missing)} files:")
    for m in missing[:20]:
        print(f"  {m}")
else:
    print("All files present.")
```

### 2.2 行数检查

确认每个 parquet 文件行数 > 0：

```python
import pyarrow.parquet as pq
empty_files = []
for ds_sym_path in all_paths:  # 遍历所有输出文件
    meta = pq.read_metadata(ds_sym_path)
    if meta.num_rows == 0:
        empty_files.append(ds_sym_path)
```

目标每天每 symbol 约 28,800 bars（动态阈值控制）。偏差 +-10% 正常。

### 2.3 Schema 一致性

确认所有天所有 symbol 的列名完全一致：

```python
import pyarrow.parquet as pq
schemas = set()
for path in all_paths:
    schema = pq.read_schema(path)
    col_names = tuple(schema.names)
    schemas.add(col_names)

assert len(schemas) == 1, f"Schema mismatch! Found {len(schemas)} distinct schemas"
print(f"Uniform schema: {len(schemas[0])} columns")
```

列名必须以 `${fa_prefix}_` 开头（除 `symbol`, `bar_id`, `close_time_ms` 外）。

### 2.4 轴对齐验证（与 basic_table anchor 对齐）

factor parquet 产出后，必须通过 `axis_alignment_check.py` 验证与 **`basic_table` anchor** 的对齐（issue #119 之后 factor pool 对齐基准从 f001 切换为 basic_table）：

```bash
python /home/cken/crypto_world/zebra/scripts/axis_alignment_check.py \
    --factor-root /data/db/crypto/futures/world/world_pool/${fa_lower} \
    --factor-sub ${fa_lower}_v1 \
    --anchor-root /data/db/crypto/futures/world/world_pool/basic_table \
    --anchor-sub basic_table \
    --dates <3-5 日的逗号分隔列表> \
    --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT
```

通过标准：`join_ratio >= 99.9%`、`bar_coverage >= 99.9%`、`dup_cnt == 0`。详见 `crypto-axis-alignment-check` skill。

---

## 3. 常见问题处理

### 3.1 Threshold Missing

**现象**：`Error: threshold file not found for date YYYY-MM-DD`

**原因**：`--threshold-dir` 下缺少对应日期的 threshold 文件。

**解决**：
1. 确认 threshold 目录覆盖了完整日期范围。
2. 如果是新增日期，需要先运行 threshold 生成脚本。
3. batch_runner 的 `threshold_missing_policy = "error"`，不会 fallback。

### 3.2 L2 Data Missing

**现象**：Agent 输出 OB 类因子全为 0.0（默认值）。

**原因**：`--l2-root` 下对应日期/symbol 的 L2 CSV.gz 文件缺失。

**解决**：
1. 确认 Tardis 数据已下载到 `--l2-root` 路径。
2. Agent 代码中应有 `ctx.HasBook()` 守卫，缺失 L2 时输出 schema 默认值（通常 0.0）。
3. 如果大面积缺失 L2，检查 xlx 远程机的 Tardis 同步状态。

### 3.3 OOM (Out of Memory)

**现象**：进程被 OOM killer 终止，或 `std::bad_alloc`。

**原因**：`--chunk-days 0` 时整个日期范围的状态驻留内存。

**解决**：
1. 改用 `--chunk-days 30`（或更小值）分段运行。
2. 配合 `--skip_existing` 和 `--manifest` 实现断点续跑。
3. 检查 Agent 是否有内存泄漏（deque 无上限增长等）。

### 3.4 断点续跑

并行 launcher 完全支持续跑：每次启动会重新生成分片，但每个子进程透传 `--skip_existing`，已有输出的 (symbol, date) 会被跳过。

```bash
# 首次运行
python .../parallel_batch_runner.py ... --workers 30 --skip_existing \
    --manifest /data/db/crypto/futures/world/world_pool/${fa_lower}/manifest.json

# 中断后直接同一条命令再跑一次即可：已完成的 (symbol, date) 自动跳过
python .../parallel_batch_runner.py ... --workers 30 --skip_existing \
    --manifest /data/db/crypto/futures/world/world_pool/${fa_lower}/manifest.json
```

注意：合并 manifest 在每次运行结束时从子分片 manifest 重新生成，所以多次运行后的合并 manifest 只包含**最后一次运行**各分片的 entries。如果你需要完整历史，用 `find <output_dir> -name '*.parquet'` 直接枚举文件。

### 3.5 并行 launcher 内存 OOM

**现象**：多个分片同时跑，整机内存爆掉。

**原因**：30 个子进程同时加载 trade + L2，单进程内存 × 30。

**解决**：
1. 降低 `--workers`（例如 15 或 10）。
2. 降低 `--chunk-days`（例如 7），让每个子进程内部 chunk 更小。
3. 只跑部分 symbols：分多批运行。

---

## 4. Changes after issue #119 (2026-04-19)

- **对齐基准从 f001 切换为 basic_table**：factor parquet 产出后的轴对齐验证使用 `axis_alignment_check.py --anchor-root /data/db/crypto/futures/world/world_pool/basic_table --anchor-sub basic_table`，不再以 `f001` 为对齐基准。
- **`--anchor-root` / `--anchor-sub` 为新主参数**：原 `--f001-root` / `--f001-sub` 仅为向下兼容保留（会发 DeprecationWarning），新任务一律使用 `--anchor-root`。
- **basic_table 前置依赖**：执行刷因子本身不依赖 basic_table，但刷完后的 §2.4 轴对齐验证需要 `basic_table` 已覆盖相同日期 × symbol。如果 basic_table 尚未刷全，应先补 basic_table 再做对齐检查。
