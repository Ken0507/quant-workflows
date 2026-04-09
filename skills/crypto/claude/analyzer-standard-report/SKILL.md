---
name: crypto-analyzer-standard-report
description: "使用 crypto analyzer 生成标准化 LGBM 因子分析报告。默认跑 LGBM-only 模式（clip + rank 两份），剔除 20251010 数据。可选跑完整单因子分析或 merged baseline 报告。"
metadata:
  short-description: "Crypto 因子分析报告"
  argument-hint: "[data_root] [subfolder] [output_base]"
---

# Crypto 因子分析报告

## 0. 前置条件

1. **因子数据已刷完**
   - 输出目录 `/data/db/crypto/futures/world/world_pool/${fa_lower}/` 下每天每 symbol 的 parquet 齐全。
   - 已通过 `crypto-zebra-factor-batch-run` 的输出验证。

2. **Python 环境**
   - 工作目录：`/home/cken/crypto_world/research/analyzer`
   - 依赖：pandas, pyarrow, lightgbm, matplotlib, numpy（已预装）。

3. **日期范围**
   - 默认：`2025-07-01` ~ `2026-01-26`（210 天）
   - Train/Valid 自动 80/20 切分

4. **数据纪律：20251010 必须剔除**
   - 2025-10-10 存在极端行情，会严重污染 LGBM 训练。
   - `run_lgbm_only.py` 的 `--exclude-dates 20251010` 参数已实现此功能。

---

## 1. 默认模式：LGBM-Only（clip + rank 两份报告）

默认情况下，对每个因子集同时生成 **两份** LGBM-only 报告：

| 报告 | Label 处理 | 说明 |
|------|-----------|------|
| **clip** | `--label-mode clip --clip-threshold 0.01 --exclude-dates 20251010` | 删除极端 label + 剔除 10/10 |
| **rank** | `--label-mode rank --exclude-dates 20251010` | Rank transform per (sym,day) + 剔除 10/10 |

### 1.1 命令

```bash
cd /home/cken/crypto_world/research/analyzer

# Report A: clip + exclude 10/10
python run_lgbm_only.py \
    --data-root /data/db/crypto/futures/world/world_pool/${fa_lower}_merged_for_report \
    --subfolder ${fa_lower}_full \
    --dataset-name "${fa_lower}_clip001" \
    --output-dir /data/db/crypto/analyzer/${fa_lower}/${fa_lower}_clip001 \
    --start-date 2025-07-01 --end-date 2026-01-26 \
    --label-mode clip --clip-threshold 0.01 --exclude-dates 20251010

# Report B: rank + exclude 10/10
python run_lgbm_only.py \
    --data-root /data/db/crypto/futures/world/world_pool/${fa_lower}_merged_for_report \
    --subfolder ${fa_lower}_full \
    --dataset-name "${fa_lower}_rank" \
    --output-dir /data/db/crypto/analyzer/${fa_lower}/${fa_lower}_rank \
    --start-date 2025-07-01 --end-date 2026-01-26 \
    --label-mode rank --exclude-dates 20251010
```

**两份报告可以并行跑**（每份约 35GB 内存，合计 ~70GB）。

### 1.2 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data-root` | 因子数据根目录 | 必填 |
| `--subfolder` | parquet 子目录名 | 必填 |
| `--dataset-name` | 报告显示名 | 从 subfolder 派生 |
| `--output-dir` | 报告输出目录 | 必填 |
| `--start-date` | 起始日期 | `2025-07-01` |
| `--end-date` | 截止日期 | `2026-01-26` |
| `--label-mode` | Label 处理：`raw`/`clip`/`rank` | `raw` |
| `--clip-threshold` | clip 模式的阈值 | `0.01` |
| `--exclude-dates` | 剔除的日期（YYYYMMDD） | 无 |
| `--symbols` | 逗号分隔 symbol 列表 | 全部 7 个 |
| `--main-horizon` | 主预测 horizon（bar 数） | `100` |
| `--downsample` | 下采样步长 | `1` |

### 1.3 输出格式

报告格式与标准分析报告一致（§1 Configuration → §2 Sample Overview → §7 LightGBM），跳过 §3-6 单因子部分。

```
${output_dir}/
├── report.md                    # 标准格式报告
├── lgbm_model.txt               # 训练好的模型（可用于回测信号导出）
├── lgbm_train_info.json         # 训练信息（features, train/valid days, params）
├── lgbm_daily_ic.parquet        # 每日 IC / Rank IC
├── lgbm_feature_importance.parquet
├── lgbm_top0p1_daily.parquet    # Top 0.1% 每日收益
├── lgbm_top0p01_daily.parquet   # Top 0.01% 每日收益
├── sample_overview.parquet
└── img/
    ├── lgbm_feature_importance_gain.png
    ├── lgbm_daily_ic.png
    ├── lgbm_daily_rank_ic.png
    ├── lgbm_{train,valid}_grouped_return.png
    ├── lgbm_{train,valid}_net_grouped_return.png
    ├── lgbm_{train,valid}_ic_decay.png
    ├── lgbm_{train,valid}_price_path.png
    ├── lgbm_top0p{1,01}_{return_ts,return_cumsum,net_return_ts,net_return_cumsum}.png
```

### 1.4 关键评估指标

两份报告出完后对比以下指标：

| 指标 | 含义 | 来源 |
|------|------|------|
| Valid Daily RankIC | 样本外排序能力 | `lgbm_daily_ic.parquet` |
| Train-Valid IC gap | 过拟合程度 | train mean - valid mean |
| Valid Top0.1% net return | 头部信号扣费收益 | `lgbm_top0p1_daily.parquet` |
| Valid Grouped Return 单调性 | alpha 曲线形态 | `lgbm_valid_grouped_return.png` |
| Feature Importance 分布 | 因子贡献集中度 | `lgbm_feature_importance.parquet` |

---

## 2. 可选模式：完整单因子分析

当需要查看每个因子的 IC decay、grouped return 等详细信息时使用。

```bash
cd /home/cken/crypto_world/research/analyzer
python run_report.py \
    --data-root /data/db/crypto/futures/world/world_pool/${fa_lower} \
    --subfolder ${fa_lower}_v1 \
    --output-dir /data/db/crypto/analyzer/${fa_lower}/${fa_lower}_v1_full \
    --start-date 2025-07-01 --end-date 2026-01-26
```

**注意**：完整报告不支持 `--label-mode` / `--exclude-dates`。如需剔除 10/10，需手动在数据中处理。

---

## 3. 可选模式：Merged Baseline 报告

将新因子集与 baseline (f001+f002, 69 因子) 合并分析增量价值。

```bash
cd /home/cken/crypto_world/research/analyzer
python run_merged_report.py \
    --primary-root /data/db/crypto/futures/world/world_pool/${fa_lower} \
    --primary-sub ${fa_lower}_v1 \
    --baseline-root /data/db/crypto/futures/world/world_pool/f001 \
    --baseline-sub base30_v1 \
    --baseline2-root /data/db/crypto/futures/world/world_pool/f002 \
    --baseline2-sub f002_v1 \
    --output-dir /data/db/crypto/analyzer/${fa_lower}/${fa_lower}_merged_baseline69 \
    --dataset-name "${fa_lower}_merged_baseline69" \
    --start-date 2025-07-01 --end-date 2026-01-26
```

### 合并逻辑

1. 先合并 f001 + f002（baseline 69 因子），按 `(bar_id, close_time_ms)` inner join。
2. 再将新因子集的独有列 fold 到合并结果上。
3. `f_ret_1` 等共享列只保留一份。

---

## 4. 典型工作流

```
因子刷完
  ↓
默认模式：run_lgbm_only.py × 2（clip + rank，并行）
  ↓
对比 clip vs rank 的 valid IC、grouped return、top return
  ↓
选优 → 可选：run_merged_report.py（评估增量）
  ↓
可选：/crypto-signal-backtest（信号回测）
  ↓
记录到 research_progress
```

## 5. 禁止操作

1. **不要跳过 `--exclude-dates 20251010`** — 该日极端行情会严重污染训练
2. 不要修改因子数据或 analyzer 源码中的默认参数
3. 报告输出目录使用 `/data/db/crypto/analyzer/${fa_lower}/` 下的子目录，不要放到其他位置
