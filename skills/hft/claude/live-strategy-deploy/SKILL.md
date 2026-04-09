---
name: hft-live-strategy-deploy
description: "将 TradingAgent 实盘策略部署到交易机。包括 playground deploy（Docker 编译 + SCP 上传）、上传带交易参数的 prod_run/run.sh、验证部署结果。适用于首次部署、重新部署、代码更新后的重新上线等场景。执行前必须确认用户授权。"
---

# HFT 实盘策略部署

## 安全红线（必须遵守）

1. **每一步操作必须经用户确认后执行**，不得自行决定部署、停止或启动策略。
2. **严禁修改交易机上非 `cken_strategy_*` 目录的任何内容**。
3. **严禁从其他用户目录复制文件**，遇到权限问题必须向用户报告。
4. 如果交易机上有策略进程正在运行，必须先确认用户同意停止后才能继续。

## 前置检查

在部署前，逐项确认：

```bash
source /data/share/dev/hft/setup_sdk.sh
playground --help                    # playground 可用
cat ~/.hft/credentials.env           # 凭据已配置
docker images | grep hx_build_env   # Docker 镜像存在
```

## 部署流程

### 1) 确认部署参数

与用户确认以下信息：

| 参数 | 示例 | 说明 |
|------|------|------|
| 项目目录 | `HFTPool/pool/benchmark0323/live_v0` | 包含 CMakeLists.txt 的本地项目 |
| target 名 | `benchmark_100_trader_online` | CMakeLists.txt 中的 online 目标 |
| code list 文件 | `prod_run/tiny_code_list.txt` | 交易标的列表 |
| 是否全量 build | **默认是** | 默认全量 build（清除 build_prod 缓存）；仅用户明确指定时才用 `--no-build` 复用缓存 |

### 2) 如有运行中进程，先停止

```bash
# 检查是否有进程在跑
sshpass -p '<pass>' ssh -p 2222 userlgj@localhost \
  'pgrep -fa benchmark_100_trader_online'

# 确认是 cken 的策略（检查 exe 路径含 cken_strategy_）
sshpass -p '<pass>' ssh -p 2222 userlgj@localhost \
  'ls -la /proc/<PID>/exe'

# 用户确认后才能停止
sshpass -p '<pass>' ssh -p 2222 userlgj@localhost \
  'kill <PID>; sleep 2; kill -0 <PID> 2>/dev/null && kill -9 <PID>'
```

### 3) 执行 playground deploy

**默认执行全量 build**（除非用户明确说"复用缓存"/"不重新 build"/"--no-build"）：

```bash
cd <项目目录>
rm -rf build_prod    # 默认清除缓存，确保全量 build
source /data/share/dev/hft/setup_sdk.sh
CODES=$(paste -sd, <code_list_file>)
playground deploy <target> --codes "$CODES"
```

如果用户明确指定跳过 build，则保留 build_prod 缓存并加 `--no-build`：

```bash
cd <项目目录>
# 不删除 build_prod
source /data/share/dev/hft/setup_sdk.sh
CODES=$(paste -sd, <code_list_file>)
playground deploy <target> --codes "$CODES" --no-build
```

关键检查点（playground 12 步流程）：
- ✓ SSH tunnel active
- ✓ Docker build successful
- ✓ Binary MD5 verified
- ✓ SDK libs copied (含 TORA 库)
- ✓ Config copied
- ✓ run.sh generated

### 4) 上传 prod_run/run.sh（覆盖 playground 生成的版本）

playground 生成的 run.sh 仅包含 `--code`，不包含交易参数。必须用 `prod_run/run.sh` 覆盖：

```bash
sshpass -p '<pass>' scp -P 2222 \
  prod_run/run.sh \
  userlgj@localhost:/home/userlgj/app/strategy/<project_name>/run.sh
```

**注意**：`prod_run/run.sh` 中的 CODES 必须与 playground deploy 使用的 code list 一致。如果 code list 有变更，先更新 `prod_run/run.sh` 再上传。

### 5) 验证

```bash
# 验证 run.sh 内容（检查交易参数完整性）
sshpass -p '<pass>' ssh -p 2222 userlgj@localhost \
  'cat /home/userlgj/app/strategy/<project_name>/run.sh'

# 验证目录结构
sshpass -p '<pass>' ssh -p 2222 userlgj@localhost \
  'ls -lh /home/userlgj/app/strategy/<project_name>/'

# 验证 lib 完整性（必须包含以下 .so）
# SDK: libagent_core, libagent_io_parquet, libagent_offline, libagent_online, liborderbook
# TORA: libtraderapi, liblev2mdapi, libxmdapi, libxfastmdapi
sshpass -p '<pass>' ssh -p 2222 userlgj@localhost \
  'ls -lh /home/userlgj/app/strategy/<project_name>/lib/'
```

## 运维操作（仅在用户要求时执行）

### 盘前冷启动

```bash
bash run.sh        # 不加 --recover，FLAGS_recover 默认 false
```

### 盘中热重启

```bash
bash run.sh --recover    # 从 LMDB 恢复 OrderBook 状态
```

### crontab 管理

当前 crontab 配置（交易机 userlgj 用户）：

```cron
# cken_benchmark0323_v0
10 9  * * 1-5  /home/userlgj/app/strategy/cken_benchmark0323_v0/start_strategy.sh >> /home/userlgj/app/strategy/cken_benchmark0323_v0/log/cron.log 2>&1
05 15 * * 1-5  /home/userlgj/app/strategy/cken_benchmark0323_v0/stop_strategy.sh  >> /home/userlgj/app/strategy/cken_benchmark0323_v0/log/cron.log 2>&1
```

修改 crontab 前必须：
1. 先 `crontab -l` 查看当前内容
2. 备份当前 crontab（在交易机上：`crontab -l > ~/cron_backup_$(date +%Y%m%d).txt`）
3. **严禁修改 lgj 及其他已有 crontab 条目**，仅追加/修改 `cken_strategy_*` 相关条目
4. 修改后用 `crontab -l` 验证

## 交易参数参考

当前 `prod_run/run.sh` 中的交易参数（以 benchmark_100 为例）：

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `--score_open_bps` | double | 7.0 | 开仓阈值 |
| `--score_open_market_bps` | double | 20.0 | MARKET 入场阈值 |
| `--score_hold_bps` | double | -2.0 | 持仓阈值 |
| `--score_hysteresis_bps` | double | 4.0 | 滞回阈值 |
| `--target_vol` | int32 | 10 | 目标仓位量 |
| `--cancel_reduce_scheme` | string | BE | 撤单方案 |
| `--cancel_confirm_bars` | int32 | 5 | B scheme 确认 bars |
| `--cancel_immediate_bps` | double | -1.0 | B scheme 立即撤单 |
| `--old_order_age_bars` | int32 | 3 | E scheme 老单年龄 |
| `--lmdb_path` | string | /home/userlgj/orderbook_dump | LMDB 恢复路径 |

**注意 gflags 类型**：`DEFINE_double` 必须用浮点值（`7.0` 而非 `7`），`DEFINE_int32` 用整数。

## 检查清单

- [ ] 用户已确认授权部署
- [ ] `playground deploy` 12 步全部通过
- [ ] `prod_run/run.sh` 已上传（交易参数完整、code list 一致）
- [ ] 交易机目录结构正确（binary + lib/ + config/ + run.sh）
- [ ] lib/ 包含全部 SDK 库 + TORA 库（详见验证步骤中的库列表）
