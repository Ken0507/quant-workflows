---
name: hft-benchmark-refresh
description: "执行 HFT 投研的 Stage R Benchmark Refresh：把当前 baseline + 累积的新 FA 合并跑一次 LGBM，选取 gain Top N（默认 N=100）作为新一代 benchmark。模板来源 HFTPool/pool/benchmark0323/run_benchmark.py + run_top100.py。产出 HFTPool/pool/benchmark{YYYYMMDD}/ 标准目录，含 run_benchmark.py + run_top100.py + report/ + report_top100/。这是 sota_snapshot 更新的实质触发点，下一次 /hft-meta-review 会检测并把新 benchmark 写入 SOTA 指针。"
---
# HFT Benchmark Refresh

> **本 Skill 是 sota_snapshot 演进的"实质触发点"**：把当前 benchmark + post-Refresh 累积 FA 一起跑 LGBM、选 Top N、生成下一代 benchmark 目录。然后 `/hft-meta-review` 在下一次扫描中会自动检测到新目录并更新 SOTA 指针。
>
> 本 Skill **不**自动修改 `workflows/hft/sota_snapshot.md`——这是 `/hft-meta-review` 的职责，避免两个 skill 同时改同一份文件。
>
> **资源警告**：本 skill 启动后会跑数小时（cache build + LGBM 训练），内存峰值可能 300 ~ 450 GB（取决于 FA 数量和总 signal 数）。**用户启动前必须明确确认**。

---

## 0. 参数解析

**调用形式**：

- `/hft-benchmark-refresh` — 无参数，使用 default 模式
- `/hft-benchmark-refresh 20260601` — 指定 benchmark 日期标签
- `/hft-benchmark-refresh 20260601 default` — 显式 default 数据集
- `/hft-benchmark-refresh 20260601 default 150` — Top 150 而非 100
- `/hft-benchmark-refresh 20260601 "baseline_150_new,fa12,fa16,fa20-28"` — 显式数据集列表

**默认行为（default 模式）**：

1. 读 `workflows/hft/sota_snapshot.md` 找出"当前 SOTA 因子集"（如 benchmark0323_top100 = baseline_150_new + FA12/16/20-25）
2. 再扫 `HFTPool/pool/FA*/` 中**晚于上次 benchmark 锁定日**的目录（即 post-Refresh 累积 FA）
3. 合并两组作为新一代 `DATASETS_DEF`

**默认 Top N**：100（与 benchmark0323 一致）

**默认日期标签**：今日 UTC+8 `date '+%Y%m%d'`

---

## 1. 固定流程

### Step 1: 读 sota_snapshot + 扫累积 FA

强制完整阅读：

```
/home/cken/crypto_world/quant-workflows/workflows/hft/sota_snapshot.md
```

从 §1.1 "因子集构成" 表提取：

- 当前 SOTA 模型对应的 DATASETS_DEF（哪些 author / factor_set_name 入了上次 benchmark）
- 上次 benchmark 锁定日期（用于"post-Refresh 累积"分界线）

然后扫 `HFTPool/pool/FA*/`，列出 mtime > 上次锁定日 的目录，每个补充：

- factor_set 路径：`/data/db/hft/factor_pool/debug/fa{N}/fa{N}_factor_v1/`（按命名约定）
- 实测因子列数（首日 parquet 的 schema）：

```python
import pyarrow.parquet as pq
META_COLS = {'code', 'time', 'bar_id', 'exchange_ts', 'md_id'}
schema = pq.read_schema(parquet_path)
n_signals = len([c for c in schema.names if c not in META_COLS])
```

### Step 2: 预算估算 + 用户确认

向用户展示**资源预算清单**：

```
=== Benchmark Refresh 预算 ===

新 benchmark 日期: 20260601
数据集列表（DATASETS_DEF）：
  1. ("debug", "baseline", "baseline_150_new", None)    150 signals
  2. ("debug", "cken",     "fa12_factor_v1",   None)     59 signals
  3. ("debug", "fa16",     "fa16_factor_v1",   None)     64 signals
  4. ("debug", "fa20",     "fa20_factor_v1",   None)     22 signals
  ...
  N. ("debug", "fa28",     "fa28_factor_v1",   None)     56 signals

总 signal 数: 660（示例）
日期范围: 20250102 ~ 20250730 (标准提交集, 139 天)
Universe: bond_sz (190 codes)

预估峰值内存: ~370 GB
  公式: cache_workers (10) × (20 + 0.2 × n_signals) = 10 × (20 + 132) ≈ 1520 GB worst-case
  但 reuse_cache 模式下大部分 dataset 已有 cache，实际增量 << worst-case
  保守阈值: 设为 450 GB（同 benchmark0323）

预估运行时间:
  Phase 1 (Build multi-dataset cache):  ~30-60 min（reuse_cache=True，新增 FA cache）
  Phase 2 (Full report + LGBM):         ~45-90 min（n_signals 较大时 LGBM 更慢）
  Phase 3 (Top N report):               ~30-45 min（features 缩到 100）
  总计: ~2-4 小时

产出目录:
  HFTPool/pool/benchmark20260601/
    ├── run_benchmark.py             （本 skill 生成）
    ├── run_top100.py                （本 skill 生成）
    ├── report/                       （Phase 2 产出）
    └── report_top100/                （Phase 3 产出）

模型输出:
  /data/db/hft/model_output/cken/benchmark20260601/v1/         （Phase 2）
  /data/db/hft/model_output/cken/benchmark20260601/v1_top100/  （Phase 3）

=== 确认问题 ===

1. DATASETS_DEF 列表 OK 吗？要不要加 / 删 / 改前缀？
2. Top N = 100 OK 吗？还是要 150 / 80？
3. 日期范围 20250102-20250730 OK 吗？（默认标准提交集；某些场景可能要拓展到更新的 holdout 解锁日）
4. 现在 /data/db/hft 磁盘可用空间足够吗？（cache + memmap 估计 ~50 GB / dataset，需手动 df -h 确认）
5. 内存阈值 450 GB OK 吗？要不要调整？

启动 Refresh 请明确回 "确认启动"。任何犹豫请回 "暂停"。
```

⚠️ **硬性规则**：未得到用户明确"确认启动"之前，**不得**创建任何文件、不得调用 Bash 启动 python 进程。

### Step 3: 生成 run_benchmark.py + run_top100.py

基于 `HFTPool/pool/benchmark0323/run_benchmark.py + run_top100.py` 模板，**替换以下字段**：

| 字段 | benchmark0323 旧值 | 本次新值 |
|------|---------|---------|
| `REPORT_DIR` | `HFTPool/pool/benchmark0323/report` | `HFTPool/pool/benchmark{date}/report` |
| `MODEL_DIR` | `/data/db/hft/model_output/cken/benchmark0323/v1` | `/data/db/hft/model_output/cken/benchmark{date}/v1` |
| `DATASETS_DEF` | 9 个（baseline + FA12/16/20-25） | 用户在 Step 2 确认的列表 |
| `START_DATE` / `END_DATE` | `20250102` / `20250730` | 用户在 Step 2 确认的范围 |
| `LGBM seed` | 20260323 | `2026{MMDD}`（本次锁定日的 mmdd 数字，避免不同代用同 seed） |
| 其它（learning_rate, num_leaves, ...） | 保持 benchmark0323 一致 | 同左 |

`run_top100.py` 的 `MODEL_DIR` 改为 `/data/db/hft/model_output/cken/benchmark{date}/v1_top100/`，`REPORT_DIR` 改为 `HFTPool/pool/benchmark{date}/report_top100/`，且其中加载 feature_importance 的路径改为 `/data/db/hft/model_output/cken/benchmark{date}/v1/feature_importance_gain.parquet`。

**保留 benchmark0323 的关键设计**：

- bar 模式 + `bar_col=bar_aggtrans_time_1`
- 18 个 horizon: `[1, 2, 3, 4, 5, 7, 10, 13, 16, 20, 25, 30, 40, 50, 75, 100, 150, 200]`，main = `ret_lag0_next100`
- `downsample_stride=1`（团队统一口径）
- `LGBM`: lr 0.1 / num_leaves 32 / min_data_in_leaf 10000 / num_boost_round 50（与 0323 严格一致以保证可比性；如要改超参，须先与用户确认）
- 内存守护线程（450 GB 阈值，10s 检查间隔，超阈值 SIGKILL 进程组）
- `reuse_cache=True`（已有 dataset 的 cache 复用）
- `discover_signals()` 函数原样保留

**创建目录**：

```bash
mkdir -p /home/cken/hft_projects/HFTPool/pool/benchmark{date}/
```

然后编辑/写入两份 .py 文件。

### Step 4: 启动 Phase 2（合并跑全池 LGBM）

```bash
cd /home/cken/hft_projects/HFTPool/pool/benchmark{date}
source /data/share/dev/hft/setup_sdk.sh
nohup python run_benchmark.py > run_benchmark.log 2>&1 &
BENCH_PID=$!
echo "PID: $BENCH_PID"
```

用长运行 shell 会话启动上述命令，记录 session id / PID，然后立即向用户报告 PID。

**监控**：

```bash
# 每 10 分钟检查一次进度（用户可手动）
tail -50 /home/cken/hft_projects/HFTPool/pool/benchmark{date}/run_benchmark.log
```

完成判定：

- 出现 "全部完成" / "STEP 3 LGBM 完成" 字样
- `report/report.md` 文件已生成
- `model_output/cken/benchmark{date}/v1/feature_importance_gain.parquet` 已生成

**失败处理**：

- 内存超阈值 → 用户决定是否降 `CACHE_WORKERS` 或拆分 dataset 重跑
- LGBM segfault → 降 `LGBM_N_JOBS`（参考 FA28 merged 报告"已知限制"中的经验）
- 磁盘满 → 暂停并清理 cache（注意不要清掉别人的）

### Step 5: 启动 Phase 3（Top N 选择 + 独立报告）

Phase 2 完成后再起 Phase 3（**不能并行**，因为 Phase 3 要读 Phase 2 的 `feature_importance_gain.parquet`）：

```bash
cd /home/cken/hft_projects/HFTPool/pool/benchmark{date}
nohup python run_top100.py > run_top100.log 2>&1 &
TOP_PID=$!
echo "PID: $TOP_PID"
```

完成判定：

- `report_top100/report.md` 已生成
- `report_top100/metadata.json` 中 `signals` 长度 = Top N

### Step 6: 物理复制 LGBM 模型 + IC parquet 到 HFTPool（**强制**）

Phase 2/3 完成后，**必须**把 `model_output/cken/benchmark{date}/v1{,_top100}/` 中的核心 LGBM 产物物理拷贝到 `HFTPool/pool/benchmark{date}/saved_model/v1{,_top100}/`，以防 `/data/db/hft/model_output/` 被自动清理（**历史事故**：benchmark0323 的 `model_output/cken/benchmark0323/v1{,_top100}/` 在 2026 年某次清理中丢失，导致纯 SOTA 模型不可用，只剩 FA28-merged 的代理）。

```bash
# Phase 2 模型物理拷贝（全池 410 LGBM）
SAVED2="/home/cken/hft_projects/HFTPool/pool/benchmark{date}/saved_model/v1"
mkdir -p "$SAVED2"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1/model.txt                          "$SAVED2/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1/lgbm_daily_ic_train.parquet        "$SAVED2/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1/lgbm_daily_ic_valid.parquet        "$SAVED2/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1/lgbm_daily_ic.parquet              "$SAVED2/" 2>/dev/null
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1/feature_importance_gain.parquet    "$SAVED2/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1/metadata.json                      "$SAVED2/" 2>/dev/null

# Phase 3 模型物理拷贝（top100 LGBM）
SAVED3="/home/cken/hft_projects/HFTPool/pool/benchmark{date}/saved_model/v1_top100"
mkdir -p "$SAVED3"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1_top100/model.txt                         "$SAVED3/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1_top100/lgbm_daily_ic_train.parquet       "$SAVED3/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1_top100/lgbm_daily_ic_valid.parquet       "$SAVED3/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1_top100/lgbm_daily_ic.parquet             "$SAVED3/" 2>/dev/null
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1_top100/feature_importance_gain.parquet   "$SAVED3/"
cp -L /data/db/hft/model_output/cken/benchmark{date}/v1_top100/metadata.json                     "$SAVED3/" 2>/dev/null

# 验证 saved_model 下不含 symlink
if find "$SAVED2" "$SAVED3" -type l | grep -q .; then
  echo "ERROR: symlink detected in saved_model; must copy physically" >&2
  exit 1
fi
```

**禁止**：在 `saved_model/` 下创建任何 symlink。`memmap/` 不在拷贝范围（太大，可重生）。

### Step 7: 验收 + 总结报告

向用户输出**验收清单**：

```
=== Benchmark Refresh {date} 验收 ===

Phase 2 (Full pool):
  ✅ Cache built: {n_days} days
  ✅ Report: HFTPool/pool/benchmark{date}/report/report.md
  ✅ Model: /data/db/hft/model_output/cken/benchmark{date}/v1/model.txt
  ✅ Feature importance: {model_dir}/feature_importance_gain.parquet
  ✅ LGBM Train mean RankIC: {train_ric:.4f}  (from lgbm_daily_ic_train.parquet)
  ✅ LGBM Valid mean RankIC: {valid_ric:.4f}  (from lgbm_daily_ic_valid.parquet)
  ✅ Total signals: {n_total}

Phase 3 (Top {N}):
  ✅ Report: HFTPool/pool/benchmark{date}/report_top100/report.md
  ✅ Model: /data/db/hft/model_output/cken/benchmark{date}/v1_top100/model.txt
  ✅ Top {N} signals: report_top100/metadata.json["signals"]
  ✅ LGBM Train mean RankIC (top {N}): {train_ric_top:.4f}
  ✅ LGBM Valid mean RankIC (top {N}): {valid_ric_top:.4f}

=== 与上一代 benchmark 的对比 ===

旧 benchmark: {old_path}
新 benchmark: HFTPool/pool/benchmark{date}/

|              | 旧 ({old_date}) | 新 ({date}) | 变化 |
| 总 signal 数 |      {old_n}    |    {new_n}  | {delta} |
| Top {N} valid RankIC |  {old_ric}  | {new_ric}   | {delta_ric} |
| Top {N} 重叠率        |       —     |     {pct}%  | — |
| 新进 Top {N} (Top 进入) |       —     |  {entered}  | — |
| 旧出 Top {N} (旧因子退出) |       —     | {exited}    | — |

=== 下一步 ===

1. 运行 /hft-meta-review 把本次 Refresh 写入 sota_snapshot
   /hft-meta-review {date}

2. （可选）跑 SignalReplay 回测验证 Layer 2 改善
   /hft-playground-signalreplay-backtest

3. （可选）触发下一轮 deep-factor-research 用新 benchmark 作为对照
```

**对比表数据来源**：

- 旧 benchmark valid RankIC：从 sota_snapshot.md §1.2 读取，或从旧 `lgbm_daily_ic_valid.parquet` 计算（如果模型文件还在）
- Top N 重叠率：`len(set(new_top_n) & set(old_top_n)) / N`
- 进出名单：`set(new) - set(old)` / `set(old) - set(new)`

---

## 2. 硬性规则

1. **用户启动确认**：Step 2 的"确认启动"是不可省略的门槛。除非用户明确说"启动"，否则不得创建 .py 文件、不得启动 python 进程
2. **不修改 sota_snapshot.md**：本 skill 只产出 `HFTPool/pool/benchmark{date}/`，不动 `workflows/hft/sota_snapshot.md`。SOTA 指针更新由 `/hft-meta-review` 负责
3. **保留 benchmark0323 的可复现性**：本 skill 生成的 run_benchmark.py / run_top100.py 必须保留**所有**关键参数与 benchmark0323 一致（除日期 / DATASETS_DEF / seed 外），以保证逐代对照的科学性。如要改 LGBM 超参（learning_rate、num_leaves...），必须先与用户确认并在新 benchmark 目录里加 `CHANGELOG.md` 解释
4. **内存与磁盘安全**：
   - 内存阈值默认 450 GB，与 benchmark0323 一致；如降低请明确告知用户
   - 磁盘检查：`df -h /data` 必须 > 100 GB 可用
   - 不**清理**任何已有的 cache（reuse_cache=True 即可复用）
5. **失败 / 中断处理**：Phase 2 / Phase 3 失败时**不要**自动重跑——先把 log 给用户看，让用户决定降并发还是修参数。失败后未生成的目录不要遗留半成品，删 `report_top100/` 等
5b. **物理拷贝硬性规则**：Step 6 不可省略。LGBM 模型 + IC parquet + feature_importance 必须物理拷贝到 `HFTPool/pool/benchmark{date}/saved_model/`。验证命令：`find saved_model/ -type l` 必须返回空。**历史事故**：benchmark0323 的 model.txt 在 2026 年某次 `/data/db/hft/model_output/` 清理中丢失，导致纯 SOTA LGBM 模型不可用、IC parquet 不可读，只能依赖 PNG 视觉估算或重跑。**任何新 Refresh 必须避免这个陷阱**
6. **不动 lgj 的目录**：`/home/userlgj/` 路径下不读不写（与 HFTPool/项目说明文件 实盘红线一致）
7. **不动 sota_archive / reviews / updates**：这是 `/hft-meta-review` 的工作区，本 skill 不写
8. **诚实报告对比数字**：Step 6 的对比表如果某些数字无法读取（如旧 benchmark model.txt 已被清理 —— 这是 benchmark0323 现状），明确写"已清理，无法对比"，不臆造数字
9. **不上交易机**：本 skill 不调用 ssh / sshpass / 不访问交易机 192.168.10.215

---

## 3. 交付物

| 文件 | 路径 | 生成时机 |
|------|------|---------|
| run_benchmark.py | `HFTPool/pool/benchmark{date}/run_benchmark.py` | Step 3（确认启动后立即） |
| run_top100.py | `HFTPool/pool/benchmark{date}/run_top100.py` | Step 3（确认启动后立即） |
| 全池 analyzer 报告 | `HFTPool/pool/benchmark{date}/report/` | Phase 2 完成 |
| 全池 LGBM 模型（工作目录） | `/data/db/hft/model_output/cken/benchmark{date}/v1/` | Phase 2 完成 |
| **全池 LGBM 模型（物理副本）** | `HFTPool/pool/benchmark{date}/saved_model/v1/` | Step 6（强制） |
| Top N analyzer 报告 | `HFTPool/pool/benchmark{date}/report_top100/` | Phase 3 完成 |
| Top N LGBM 模型（工作目录） | `/data/db/hft/model_output/cken/benchmark{date}/v1_top100/` | Phase 3 完成 |
| **Top N LGBM 模型（物理副本）** | `HFTPool/pool/benchmark{date}/saved_model/v1_top100/` | Step 6（强制） |
| benchmark_config.json | `HFTPool/pool/benchmark{date}/report/benchmark_config.json` | Phase 2 自动写出 |
| CHANGELOG.md（可选） | `HFTPool/pool/benchmark{date}/CHANGELOG.md` | 仅当本次改了 LGBM 超参或其它非默认配置 |

---

## 4. 典型调用示例

```bash
# 例 1：默认 Refresh（最常用）
/hft-benchmark-refresh
# → 读 sota_snapshot，自动累积 post-Refresh FA，今日为 date 标签
# → 展示预算，等用户确认
# → 跑 Phase 2 → Phase 3 → 输出验收报告
# → 提示用户接下来跑 /hft-meta-review 把 SOTA 指针切到新 benchmark

# 例 2：指定日期 + Top 150
/hft-benchmark-refresh 20260601 default 150
# → 类似例 1，但 top N = 150

# 例 3：显式数据集列表（绕过自动累积逻辑）
/hft-benchmark-refresh 20260601 "baseline_150_new,fa12,fa15,fa16,fa20-28"
# → 用户手工写出要合并哪些；解析为 DATASETS_DEF
# → 注意：fa15 等历史遗留 FA 也可强制纳入
```

---

## 5. 与其它 skill 的协作

- **`/hft-meta-review`**：本 skill 完成后，用户应立即跑一次 meta-review 把新 benchmark 写进 sota_snapshot。meta-review 在 §2.5 子扫描中会自动检测 `pool/benchmark*/` 新目录
- **`/hft-realize-factor`**：本 skill 假设所有 dataset 已经 realize 完毕（factor_pool/debug/fa{N}/.../parquet 已存在）。如果某个 FA 还没刷完全历史，本 skill 在 `discover_signals` 阶段会失败，应先跑 realize
- **`/hft-playground-signalreplay-backtest`**：Refresh 完成后，可用新 LGBM 模型导出信号做回测验证 Layer 2 改善。但本 skill 不主动触发回测——是否做 Layer 2 验证由用户决定
- **`/hft-deep-factor-research`**：后续的新研究都应以新 benchmark 为对照基线（target_and_workflow.md §2 Stage R 的"回灌"逻辑）

---

## 6. HFT 已知历史

| Refresh # | 日期 | 名称 | 备注 |
|---:|---|---|---|
| #0 | 2025-03-23 | `pool/benchmark0323/` | baseline_150_new + FA12/16/20-25，410 候选 → top100。LGBM model 已被清理（`/data/db/hft/model_output/cken/benchmark0323/v1{,_top100}/` 不在），如要精确逐代对照建议本 skill 第一次运行前重跑 benchmark0323 把模型保留 |
| #1 | _待定_ | `pool/benchmark{?}/` | 候选：合并 baseline + FA12/(FA15?)/FA16/FA20-28，重选 Top 100。决策点：是否纳入 FA15 / 是否升 Top N 到 150 |
