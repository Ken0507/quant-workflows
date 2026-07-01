---
name: hft-sync-market-data
description: "从交易机同步 bond_sz 行情数据（order + transaction parquet）到工作站 /data/share/dev/hft/data/market_data_parquet/。支持全量增量同步、单日同步、日期范围同步。同步完成后自动验证数据完整性。"
---
# 行情数据同步（交易机 → 工作站）

## 概述

将交易机上的 bond_sz 行情 parquet 数据（order + transaction）同步到工作站共享路径。

| 项目 | 值 |
|------|-----|
| 同步脚本 | `/home/cken/hft_projects/HFTPool/tasks/data_sync/sync_market_data.sh` |
| 远程源 | `userlgj@localhost:2222:/home/userlgj/market_data_parquet/` |
| 本地目标 | `/data/share/dev/hft/data/market_data_parquet/{order,transaction}/{YYYYMMDD}/` |
| 市场 | bond_sz |
| 数据类型 | order, transaction |
| 默认起始日期 | 自动检测本地已有数据的最新日期（如本地为空则回退到 20260108） |

## 执行流程

### 1) 确认同步参数

根据用户输入确定同步模式：

| 模式 | 用户输入 | 命令 |
|------|---------|------|
| 全量增量 | 无参数 或 "同步最新" | `bash sync_market_data.sh`（自动从本地最新日期开始） |
| 单日 | 一个日期，如 "同步20260213" | `bash sync_market_data.sh 20260213` |
| 日期范围 | 两个日期，如 "同步0210到0213" | `bash sync_market_data.sh 20260210 20260213` |

### 2) 前置检查

在运行脚本前，手动确认 SSH 隧道可达（脚本内部也会检查，但提前确认可避免等待超时）：

```bash
source ~/.hft/credentials.env
sshpass -p "$HFT_TRADING_PASS" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -p 2222 userlgj@localhost "echo ok"
```

如果失败，提示用户联系 lgj 检查 SSH 隧道。

### 3) 执行同步

由于数据量可能较大（全量同步约 10G+），**必须以后台方式运行**：

```bash
bash /home/cken/hft_projects/HFTPool/tasks/data_sync/sync_market_data.sh [参数] 2>&1
```

用长运行 shell 会话启动并记录 session id / PID，保持同步进程后台运行，后续通过日志尾部监控进度。

### 4) 监控进度

定期检查输出文件末尾，向用户报告进度：
- 当前正在同步的数据类型（order / transaction）
- 日期进度（如 [15/25]）
- 传输速度

### 5) 处理失败

如果同步因 SSH 断开等原因中途失败：

1. 读取输出文件末尾，确认失败的日期列表
2. 确认 SSH 隧道已恢复
3. 使用日期范围模式重新同步失败的日期段，例如：
   ```bash
   bash /home/cken/hft_projects/HFTPool/tasks/data_sync/sync_market_data.sh 20260206 20260213
   ```
   rsync 是增量的，已完成的文件会自动跳过。

4. 如果反复失败（3 次以上），停止重试并报告用户

### 6) 验证数据完整性

同步完成后（exit code 0），**必须验证**：

```bash
# 检查每个日期目录的文件数（正常应为 47-59 个 bond_sz_*.parquet 文件）
for dtype in order transaction; do
    echo "=== ${dtype} ==="
    for d in /data/share/dev/hft/data/market_data_parquet/${dtype}/YYYYMMDD*/; do
        echo "$(basename $d): $(ls "$d"/bond_sz_*.parquet 2>/dev/null | wc -l) files"
    done
done

# 检查总大小
du -sh /data/share/dev/hft/data/market_data_parquet/order/ \
      /data/share/dev/hft/data/market_data_parquet/transaction/
```

验证标准：
- 每个交易日的 order 和 transaction 目录都应存在
- 每天应有 47-59 个 `bond_sz_*.parquet` 文件（交易时段切片）
- 文件数异常偏少（如 < 40）需告警

### 7) 报告结果

向用户汇报：
- 同步的日期范围和天数
- order / transaction 各自的总大小
- 是否有失败或数据异常

## 权限说明

- 目标路径 `/data/share/dev/hft/data/market_data_parquet/` 的 owner 为 `lgj:lgj`
- cken 已加入 lgj 组，且目录已设置 `g+w`
- 如果遇到 Permission denied，需要用 sudo 重新设置权限：
  ```bash
  sudo chmod -R g+w /data/share/dev/hft/data/market_data_parquet/
  ```

## 脚本配置修改

如需修改同步范围（如增加新市场或数据类型），编辑脚本中的配置区：

```bash
# 文件: /home/cken/hft_projects/HFTPool/tasks/data_sync/sync_market_data.sh

DATA_TYPES=("order" "transaction")     # 数据类型
MARKET_PATTERN="bond_sz_*.parquet"     # 市场过滤
FALLBACK_START_DATE="20260108"         # 本地为空时的回退起始日期（自动检测优先）
```

## 注意事项

1. SSH 隧道（port 2222）由基础设施维护，不稳定时联系 lgj
2. 传输速度约 400-500 KB/s，全量同步（25+ 天 x 2 类型）耗时较长
3. 工作站磁盘已使用 95%+，定期关注 `df -h /data` 可用空间
4. 脚本使用 `sshpass -e`（环境变量方式）传递密码，避免 ps 泄漏
