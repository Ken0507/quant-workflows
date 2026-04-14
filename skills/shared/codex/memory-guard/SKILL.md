---
name: memory-guard
description: "启动内存守护进程，周期性监控 agent 自己启动的所有后代进程的总 RSS。一旦超过阈值（默认 400 GB），立即 SIGKILL 这些后代进程，避免拖垮整机。典型用例：跑大规模 parquet / polars / duckdb / torch 任务前设一道保险。"
---

# Memory Guard

## 用途

在执行可能吃大内存的任务前（大规模 parquet 扫描、polars groupby、duckdb 查询、torch 训练、并行回测 …），启动一个独立的 watchdog 守护进程。

Watchdog 做一件事：**每隔 N 秒扫描 agent 自己启动的所有后代进程的 VmRSS 总和，一旦超阈值，就把这些后代全部 `kill -9`。**

设计原则：
- **只杀 agent 自己启动的进程**：通过爬 `/proc/<pid>/stat` 的 PPID 链，定位到 Codex 主进程，然后 BFS 遍历它的所有后代作为「受管集合」。不在这个集合里的进程（用户自己开的 tmux、其他 session 的任务）一概不动。
- **永远不杀 root（Codex 主进程）本身**，也不杀守护自己。
- **仅在 Linux 下工作**（依赖 `/proc`、`pgrep -P`）。

## 何时使用本 skill

**必须启动** memory guard 的场景：
- 需要加载 > 50 GB parquet 到 polars / pandas
- duckdb / pyarrow 扫大批文件，不确定 group 大小
- 并行跑 subagent，每个 subagent 自己还会 fork 重活
- 任何「代码跑崩过整机」有过前科的任务

**不需要**的场景：
- 纯文本编辑、git 操作
- 预期内存占用 < 10 GB 的常规分析
- 只读代码的探索

## 使用方法

所有命令都通过 `bash memory_guard.sh <cmd>` 运行。脚本路径：

```
skills/shared/codex/memory-guard/memory_guard.sh
```

### 启动（默认 400 GB 阈值）

```bash
bash skills/shared/codex/memory-guard/memory_guard.sh start
```

输出示例：

```
memory-guard started pid=12345 root=6789 threshold=400G interval=5s tag=default
log: /tmp/memory-guard-cken-default.log
```

### 自定义阈值和轮询间隔

```bash
bash skills/shared/codex/memory-guard/memory_guard.sh start \
    --threshold 300 \
    --interval 3
```

### 显式指定要监控的根 PID

默认脚本会从当前 shell 往上爬，找到最近的 `comm` 为 `codex` 的祖先作为 root。若自动识别失败或你想手动绑定（例如监控某个特定 worker PID 的子树），用 `--root-pid`：

```bash
bash skills/shared/codex/memory-guard/memory_guard.sh start --root-pid 6789
```

### 多实例共存（tag）

不同任务想并行开多个 guard（比如一个盯 torch，一个盯 duckdb），用 `--tag` 区分：

```bash
bash .../memory_guard.sh start --tag torch --threshold 200
bash .../memory_guard.sh start --tag duck  --threshold 400
```

### 查看状态

```bash
bash skills/shared/codex/memory-guard/memory_guard.sh status
```

输出包含 pid、tag 以及日志末尾 10 行。

### 一次性检查（不启动守护）

想先看当前 agent 后代进程到底占了多少内存、有哪些大头，不想启动守护：

```bash
bash skills/shared/codex/memory-guard/memory_guard.sh check
```

示例输出：

```
root_pid=6789 total_rss=12.34G threshold=400G
--- top descendants (rss_kb pid comm) ---
8123456 99887 python
 512000 99912 duckdb
  64000 99920 bash
```

### 停止

```bash
bash skills/shared/codex/memory-guard/memory_guard.sh stop
```

如果开了多个 tag，记得也带 `--tag NAME` 停对应的那个。

## 推荐工作流

1. **任务开始前**：用 `check` 先看一眼当前 baseline，确认阈值合理。
2. **启动 guard**：`start` 带上合适的 `--threshold`。不确定就默认 400 GB。
3. **干活**：跑你的大任务。
4. **中途观察**：偶尔 `status` 看下日志，尤其在任务看起来卡顿时——可能 guard 已经触发 kill。
5. **任务结束**：`stop` 关掉守护。

## 日志

日志写到 `/tmp/memory-guard-${USER}-${TAG}.log`，每次 `start` 会清空。包含：
- 启动参数
- 每次触发 kill 的总 RSS、阈值、被杀进程列表（pid + comm + rss_kb）
- 守护退出原因（root 进程消失 / 被 SIGTERM）

用 `status` 命令可以直接看尾部 10 行。想看完整日志：

```bash
tail -f /tmp/memory-guard-${USER}-default.log
```

## 工作原理（简述）

1. `cmd_start` 把自己重新以 `setsid nohup` 方式后台运行，写 pidfile 到 `/tmp/memory-guard-${USER}-${TAG}.pid`。
2. 守护循环：
   - `kill -0 $ROOT_PID` 检查 root 还活着，否则退出。
   - BFS 遍历 `pgrep -P <pid>` 收集所有后代。
   - 对每个后代读 `/proc/<pid>/status` 的 `VmRSS`，累加。
   - 总和 > 阈值 → 按 RSS 降序 `kill -9` 所有后代（root 与守护自身已排除）。
3. 被 `setsid` 脱离后，守护被 init 收养，不再处于 root 的后代树里，因此守护自己不会被自己误杀。

## 注意事项

1. **粗暴 SIGKILL，无清理机会**：触发时不会给进程 cleanup 窗口，写盘中的数据可能损坏。阈值务必留余量，不要指望 guard 帮你救普通 OOM。
2. **会同时杀掉所有后代**，而不是只杀最大的那个——因为大任务常常是多进程协作，杀单个可能留下僵局。
3. **仅 Linux**：依赖 `/proc` 和 `pgrep -P`。macOS 需要改写 `get_descendants` 与 `rss_kb_of`。
4. **阈值含义是聚合 RSS**，不是单进程。注意多 worker 叠加。
5. **不覆盖 swap**：只看 `VmRSS`。若系统启用了大量 swap 且任务被换出，可能不触发。需要时改读 `VmSwap` 并叠加。
6. **root 自动识别不保证正确**：爬到第一个 `comm=codex` 的祖先就停。如果你在 tmux 里跑且祖先链很长，建议显式 `--root-pid`。先用 `check` 确认 root 找对了。
7. **一个 tag 只能有一个实例**：重复 `start` 同 tag 会报 "already running"。

## 快速复制粘贴片段

```bash
# 默认保险：400G 阈值，5s 轮询
bash skills/shared/codex/memory-guard/memory_guard.sh start

# 看一眼当前占用
bash skills/shared/codex/memory-guard/memory_guard.sh check

# 紧凑点的阈值
bash skills/shared/codex/memory-guard/memory_guard.sh start --threshold 200 --interval 3

# 关掉
bash skills/shared/codex/memory-guard/memory_guard.sh stop
```
