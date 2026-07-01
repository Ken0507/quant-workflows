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

**注**：当前部署服务器 `localhost:2223`（新服务器 192.168.10.215）。旧服务器 .190 端口 2222 已废弃。

## 部署流程

### 0) 备份当前生产目录（默认执行）

重 deploy 前对当前 `cken_strategy_*/` 目录做 tar 备份，作为快速回滚的安全网。仅在用户明确说"跳过 backup"时省略。

```bash
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'mkdir -p ~/backups && \
   tar czf ~/backups/<project_name>_before_redeploy_$(date +%Y%m%d_%H%M).tar.gz \
   -C /home/userlgj/app/strategy <project_name> && \
   ls -lh ~/backups/<project_name>_*.tar.gz | tail -3'
```

回滚方式（出问题时）：

```bash
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'cd /home/userlgj/app/strategy && \
   mv <project_name> <project_name>_broken && \
   tar xzf ~/backups/<project_name>_before_redeploy_<timestamp>.tar.gz'
```

### 1) 确认部署参数

与用户确认以下信息：

| 参数 | 示例 | 说明 |
|------|------|------|
| 项目目录 | `HFTPool/pool/baseline/baseline_20260129_150/live_v2` | 包含 CMakeLists.txt 的本地项目 |
| target 名 | `baseline_150_trader_online` | CMakeLists.txt 中的 online 目标 |
| 生产 dir 名 | `cken_strategy_live_v2` | 交易机上 `/home/userlgj/app/strategy/<这个>/` |
| code list 文件 | `prod_run/tiny_code_list.txt` | 交易标的列表（每行一个 code，逗号会被 `paste -sd,` 拼起来）|
| 是否全量 build | **默认是** | 默认全量 build（清除 build_prod 缓存）；仅用户明确指定时才用 `--no-build` 复用缓存 |

### 2) 如有运行中进程，先停止

```bash
# 检查是否有进程在跑
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'pgrep -fa <binary_name>'

# 确认是 cken 的策略（检查 exe 路径含 cken_strategy_）
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'ls -la /proc/<PID>/exe'

# 用户确认后才能停止
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
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

关键检查点（playground 8 步流程）：
- ✓ SSH tunnel active
- ✓ Docker build successful（除非 `--no-build`）
- ✓ Create directory `lib/` + `config/`
- ✓ SCP binary + verify MD5
- ✓ chmod +x binary
- ✓ SCP SDK libs（`/data/share/dev/hft/lib_trading/*.so`，含 `libstdc++.so.6` — N4 加固）
- ✓ Verify `libagent_online.so` MD5
- ✓ SCP config（从 `/data/share/dev/hft/sdk_tools/templates/config/`）
- ✓ Generate `run.sh` with `--codes`（**仅含 codes，不含 trading params——下一步会被覆盖**）

### 4) 上传 prod_run/run.sh（覆盖 playground 生成的版本）

playground 生成的 run.sh 仅包含 `--code`，不包含交易参数。必须用 `prod_run/run.sh` 覆盖：

```bash
sshpass -p '<pass>' scp -P 2223 \
  prod_run/run.sh \
  userlgj@localhost:/home/userlgj/app/strategy/<project_name>/run.sh
```

**注意**：`prod_run/run.sh` 中的 CODES 必须与 playground deploy 使用的 code list 一致。如果 code list 有变更，先更新 `prod_run/run.sh` 再上传。

### 5) 验证

#### 5.1 基础结构（每次都跑）

```bash
# 验证 run.sh 内容（检查交易参数完整性 + CODES 正确）
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'cat /home/userlgj/app/strategy/<project_name>/run.sh'

# 验证目录结构
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'ls -lh /home/userlgj/app/strategy/<project_name>/'

# 验证 lib 完整性（必须包含以下 .so）
# SDK: libagent_core, libagent_io_parquet, libagent_offline, libagent_online, liborderbook
# TORA: libtraderapi, liblev2mdapi, libxmdapi, libxfastmdapi
# 加固: libstdc++.so.6（N4 加固，跟 binary 同一 build）
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'ls -lh /home/userlgj/app/strategy/<project_name>/lib/'
```

#### 5.2 ABI 兼容性（每次都跑）

来自 #150 N4 加固经验：2026-03-16 lgj 那次 ABI mismatch crash 起源于 binary rebuild 但 lib transfer skip。`tool_deploy.sh` 已加 ldd 预检，但 `playground deploy` 没继承——必须在 deploy 后远端验证 0 unresolved symbols：

```bash
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'cd /home/userlgj/app/strategy/<project_name> && \
   LD_LIBRARY_PATH=$PWD/lib ldd ./<binary_name> | grep "not found" || echo "✅ 0 unresolved symbols"'
```

期望输出：`✅ 0 unresolved symbols`（无 "not found"）。如果有 unresolved，禁止启动——回滚 backup 或重新 build。

#### 5.3 Broker 合规（**仅首次 deploy / SDK 重大升级后建议**）

正常 deploy 不需要每次都验证 broker 合规——`/data/share/dev/hft/sdk_tools/templates/config/config.ini` 是 lgj 5-27 commit 修齐的（#127 fix），之后每次 `playground deploy` 都会自动推这份合规 template。

但以下场景建议跑一次额外验证：
- 首次 deploy 或重新部署（长期停后启动）
- SDK 重大升级（`/data/share/dev/hft/` 整体更新）
- broker 端报告 `error_id[258]` / 登录失败

```bash
sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  'grep -E "HXYZ0P99QJ|IPORT=|frontend_address=tcp" \
   /home/userlgj/app/strategy/<project_name>/config/config.ini'
```

期望命中：
- `terminal_info=...@HXYZ0P99QJ`（合规标识）
- `IPORT=`（空值，旧版是 `IPORT=0`）
- `frontend_address=tcp://10.224.124.68:6500`（新合规 broker，旧 broker 是 .237）

#### 5.4 libstdc++.so.6 MD5 兜底（**每次都跑**，playground 已知 bug #153）

`playground deploy` 当前**漏推** `libstdc++.so.6`（详见 hft-sdk-issues #153）：playground 拷贝 lib 时用的 glob 不匹配 `*.so.6` 这种带版本号后缀，所以这个关键 N4 加固 lib 永远是旧版残留。`ldd` 报 0 unresolved 是误导——ldd 不检查具体 GLIBCXX 符号版本是否齐，silent ABI mismatch 风险只在 runtime 暴露。每次 deploy 后必须验证 + 不一致则手工 scp 补齐：

```bash
SOURCE_MD5=$(md5sum /data/share/dev/hft/lib_trading/libstdc++.so.6 | awk '{print $1}')
DEPLOYED_MD5=$(sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
  "md5sum /home/userlgj/app/strategy/<project_name>/lib/libstdc++.so.6 | awk '{print \$1}'")

echo "source:   $SOURCE_MD5"
echo "deployed: $DEPLOYED_MD5"

if [ "$SOURCE_MD5" = "$DEPLOYED_MD5" ]; then
  echo "✅ libstdc++.so.6 MD5 一致"
else
  echo "⚠️  MD5 不一致，手工 scp 补齐 →"
  sshpass -p '<pass>' scp -P 2223 \
    /data/share/dev/hft/lib_trading/libstdc++.so.6 \
    userlgj@localhost:/home/userlgj/app/strategy/<project_name>/lib/libstdc++.so.6
  # 验证修复成功
  sshpass -p '<pass>' ssh -p 2223 userlgj@localhost \
    "md5sum /home/userlgj/app/strategy/<project_name>/lib/libstdc++.so.6"
fi
```

等 #153 在 playground 侧根治后，本步骤会变成 redundant 但无害的 double-check——可保留作为长期兜底。

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

当前 crontab 配置（交易机 userlgj 用户，以 `cken_strategy_live_v2` 为例）：

```cron
# cken_strategy_live_v2
10 9  * * 1-5  /home/userlgj/app/strategy/cken_strategy_live_v2/start_strategy.sh >> /home/userlgj/app/strategy/cken_strategy_live_v2/log/cron.log 2>&1
05 15 * * 1-5  /home/userlgj/app/strategy/cken_strategy_live_v2/stop_strategy.sh  >> /home/userlgj/app/strategy/cken_strategy_live_v2/log/cron.log 2>&1
```

修改 crontab 前必须：
1. 先 `crontab -l` 查看当前内容
2. 备份当前 crontab（在交易机上：`crontab -l > ~/cron_backup_$(date +%Y%m%d).txt`）
3. **严禁修改 lgj 及其他已有 crontab 条目**，仅追加/修改 `cken_strategy_*` 相关条目
4. 修改后用 `crontab -l` 验证

**注**：本地 trading-safety hook 拦截所有 `crontab` 操作（不分读写），所以 cron 修改**必须由用户手动 ssh 执行**，agent 不能自动跑。

## 交易参数参考

当前 `prod_run/run.sh` 中的交易参数（以 baseline_150 prod 实参为例）：

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `--score_open_bps` | double | 10.0 | 开仓阈值 |
| `--score_open_market_bps` | double | 30.0 | MARKET 入场阈值 |
| `--score_hold_bps` | double | -5.0 | 持仓阈值 |
| `--score_hysteresis_bps` | double | 8.0 | 滞回阈值（cancel = 5.0 - 3.0 = 2.0 bps）|
| `--target_vol` | int32 | 10 | 目标仓位量 |
| `--cancel_reduce_scheme` | string | BE | 撤单方案 |
| `--cancel_confirm_bars` | int32 | 5 | B scheme 确认 bars |
| `--cancel_immediate_bps` | double | -3.0 | B scheme 立即撤单 |
| `--old_order_age_bars` | int32 | 3 | E scheme 老单年龄 |
| `--exit_reprice_tolerance_bps` | double | 5.0 | EXIT 重报价容忍 |
| `--exit_sell_discount_bps` | double | 100.0 | EXIT SELL 折价 bps |
| `--lmdb_path` | string | /home/userlgj/orderbook_dump | LMDB 恢复路径 |

**注意**：
- gflags 类型：`DEFINE_double` 必须用浮点值（`10.0` 而非 `10`），`DEFINE_int32` 用整数。
- **源码默认值跟 prod 实参可能不一致**（如 baseline_150 CMakeLists 注释说 default `score_open_bps=7.0`，但 prod 用 `10.0`）。重新部署时**必须以 `prod_run/run.sh` 为准**，不要被源码默认值误导。

## 检查清单

- [ ] 用户已确认授权部署
- [ ] **Step 0 backup 已完成**（`~/backups/<project>_before_redeploy_<date>.tar.gz` 存在）
- [ ] `playground deploy` 8 步全部通过
- [ ] `prod_run/run.sh` 已上传（交易参数完整、code list 一致）
- [ ] 交易机目录结构正确（binary + lib/ + config/ + run.sh）
- [ ] lib/ 包含全部 SDK 库 + TORA 库 + `libstdc++.so.6`（详见验证步骤中的库列表）
- [ ] **ldd 验证 0 unresolved symbols**（每次都查，N4 加固）
- [ ] **libstdc++.so.6 MD5 与 `lib_trading/` source 一致**（每次都查，playground #153 兜底）
- [ ] （首次 / SDK 大升级后）config.ini broker 合规 grep 通过（#127 验证）
