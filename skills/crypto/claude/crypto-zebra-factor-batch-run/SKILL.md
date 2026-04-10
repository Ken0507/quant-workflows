---
name: crypto-zebra-factor-batch-run
description: "使用 Zebra batch_runner 批量刷因子数据。处理编译验证、日期范围、chunk 配置、L2 数据、输出路径、manifest 管理。调用前需要已通过 crypto-zebra-factor-write 的 smoke test。"
metadata:
  short-description: "Zebra 批量因子生成"
  argument-hint: "[binary_path] [date_range] [output_dir]"
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

## 1. 批量执行

### 1.1 命令模板

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

### 1.2 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--symbols` | 7 个标准 universe，逗号分隔 | 全部 7 个 |
| `--start_date` | 起始日期 YYYY-MM-DD | 通常 `2024-01-01` |
| `--end_date` | 结束日期 YYYY-MM-DD | 通常 `2026-03-31` |
| `--threshold-dir` | 动态阈值目录（必须） | 无默认，必填 |
| `--output_dir` | 输出根目录 | `world_pool/${fa_lower}` |
| `--l2-root` | L2 订单簿数据根目录 | Tardis 路径 |
| `--chunk-days` | 每个 chunk 的天数 | `0`（整个范围一个 chunk） |
| `--skip_existing` | 跳过已有输出的天 | 建议始终启用 |
| `--manifest` | manifest 文件路径（断点续跑） | 可选 |

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

使用 `--manifest` 参数：
```bash
# 首次运行
./batch_runner ... --manifest /data/db/crypto/futures/world/world_pool/${fa_lower}/manifest.json

# 中断后续跑（manifest 记录已完成的 date-symbol 对）
./batch_runner ... --manifest /data/db/crypto/futures/world/world_pool/${fa_lower}/manifest.json --skip_existing
```

Manifest 文件记录每个 (date, symbol) 的完成状态，配合 `--skip_existing` 实现高效续跑。
