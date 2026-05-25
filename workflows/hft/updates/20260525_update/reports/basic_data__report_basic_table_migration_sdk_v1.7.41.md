# basic_table 新框架兼容性验证报告（SDK v1.7.41）

## 0. 目标
- 目标：确认 `/home/cken/hft_projects/HFTPool/pool/basic_data` 的 `basic_table` 工程在新版 Playground/SDK 下可编译可运行，并且刷出的底表数据与服务器已存在基准产物**数据完全一致**（逐列逐行一致，NaN 视为相等）。
- 基准产物（debug）：`/data/db/hft/factor_pool/debug/basic_data/basic_table/<YYYYMMDD>/TickFeatureAgent/basic_table_basic_table.parquet`

## 1. 基准产物的“事实口径”（用于对齐）
从历史刷取日志可直接确认：
- 使用的原始数据根目录为 `/data/share/dev/hft/data`
- Loader 为 CSV（`LoadCSV`，自动识别 `SPLIT_DATE`）

证据（节选）：
- 日志：`/home/cken/hft_projects/hft_tools/logs/extract_debug_basic_data_basic_table_20250102.log`
- 其中包含：
  - `Data Path: /data/share/dev/hft/data`
  - `Loading specific codes via LoadCSV...`
  - `Auto-detected CSV Format: SPLIT_DATE`

因此本次对齐与比对均使用相同的输入数据路径与 CSV Loader。

## 2. 新 SDK 不兼容点与修复
### 2.1 DataStore::AddRow 接口变更导致无法编译
现象：新版 SDK 下编译失败，原因是 `DataStore::AddRow` 由旧版 4 个 typed-map 参数升级为 8 个 typed-map 参数（int8/int16/int32/int64/uint32/float/double/string）。

修复：
- `HFTPool/pool/basic_data/code/basic_table/tick_feature_agent.hpp`：补齐 `i8/i16/i32/f32` 四类 map，并改为调用新版 `AddRow(...)` 签名。

### 2.2 run-agent/BatchRunner 传入 `--loader=parquet`，旧 binary 不识别
修复：
- `HFTPool/pool/basic_data/code/basic_table/run_tick_feature.cpp`：新增 `--loader` 参数（`parquet|csv`），并按 loader 分支调用 `LoadParquet()`/`LoadCSV()`/`LoadAllCSV()`。

### 2.3 time 字段与历史基准相差 8 小时（需要保持历史兼容）
现象：在新版 SDK 下，`MarketEvent.local_ts` 相比历史基准产物的 `time` 列**整体早 8 小时**（差值恒为 `28800000000000` ns）。

修复（保持与历史基准产物一致）：
- `HFTPool/pool/basic_data/code/basic_table/tick_feature_agent.hpp`：写入 `time` 时加上固定偏移 `kLegacyLocalTsOffsetNs=28800000000000`（ns）。

说明：该修复是为了保证与既有服务器产物完全一致；若未来希望把 `time` 纠正为新版 SDK 的 `local_ts` 口径，需要作为“破坏性变更”单独排期并同步下游。

## 3. 复现/比对方法
### 3.1 编译（新版 Playground/SDK）
```bash
cd /home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table
source /data/share/dev/hft/setup_sdk.sh
/data/share/dev/hft/bin/playground build -j 8
```

### 3.2 抽样刷取（避免覆盖基准产物）
- 使用同一组 universe code（269 个，可从日志中提取）。
- 输出到 TEST 目录（本次落盘 root 见第 5 节）。

示例（单日）：
```bash
BIN=/home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table/build/run_tick_feature
$BIN --date=20250102 --data_path=/data/share/dev/hft/data --loader=csv --code="<269 codes>" --output_dir "<TEST_ROOT>/20250102"
```

### 3.3 精确比对（逐列逐行 + NaN 视为相等）
比对脚本：
- `HFTPool/pool/basic_data/code/scripts/compare_parquet_exact.py`

示例：
```bash
python3 /home/cken/hft_projects/HFTPool/pool/basic_data/code/scripts/compare_parquet_exact.py \
  --left  /data/db/hft/factor_pool/debug/basic_data/basic_table/20250102/TickFeatureAgent/basic_table_basic_table.parquet \
  --right /data/db/hft/factor_pool/debug/TEST/<TEST_ROOT>/20250102/TickFeatureAgent/basic_table_basic_table.parquet \
  --out_json /home/cken/hft_projects/HFTPool/pool/basic_data/report/compare_20250102_*.json
```

## 4. 抽样结果（全部 PASS）
本次抽样选择：年初/年中/年末各取若干交易日，覆盖不同数据规模。

统一的 TEST 落盘 root：
- `/data/db/hft/factor_pool/debug/TEST/basic_table_migration_sdk_v1.7.41_20260113_001815`

| date | baseline rows | new rows | result | evidence(json) |
| --- | ---: | ---: | --- | --- |
| 20250102 | 12,304,263 | 12,304,263 | PASS | `HFTPool/pool/basic_data/report/compare_20250102_old_vs_new_sdk_v1.7.41.json` |
| 20250515 | 15,258,838 | 15,258,838 | PASS | `HFTPool/pool/basic_data/report/compare_20250515_old_vs_new_sdk_v1.7.41.json` |
| 20250701 | 15,696,090 | 15,696,090 | PASS | `HFTPool/pool/basic_data/report/compare_20250701_old_vs_new_sdk_v1.7.41.json` |
| 20251215 | 9,774,797 | 9,774,797 | PASS | `HFTPool/pool/basic_data/report/compare_20251215_old_vs_new_sdk_v1.7.41.json` |

## 5. 本次生成产物位置（TEST）
- 产物 root：`/data/db/hft/factor_pool/debug/TEST/basic_table_migration_sdk_v1.7.41_20260113_001815`
- 单日文件示例：`/data/db/hft/factor_pool/debug/TEST/basic_table_migration_sdk_v1.7.41_20260113_001815/20250102/TickFeatureAgent/basic_table_basic_table.parquet`

