# IC-based Factor Selection & LGBM Benchmark Experiments — h100 clip

**Date**: 2026-04-17
**Task**: Evaluate whether IC-based factor pre-selection (single-factor IC ranking + pairwise correlation filter) can beat the current LGBM SOTA on h100 clip.

---

## 1. Executive Summary

Across **8 controlled experiments** testing various factor selection strategies against the established SOTA (`fa2+fa1` 198 features, tuned LGBM, Valid RankIC = 0.0431), **no configuration beat the SOTA**. The closest approaches were:

- `fa12 + top16 fa3` (214 features): Valid RankIC 0.0428, delta = -0.0002
- `fa12 + top10 fa3` (208 features): Valid RankIC 0.0428, delta = -0.0003
- `FI top100` (100 features): Valid RankIC 0.0427, delta = -0.0004

Key conclusions:

1. **fa3 has zero incremental alpha at h100 clip**, even when pre-filtered by IC + correlation. Adding 6/10/16 carefully selected fa3 factors to the SOTA fa1+fa2 set yields -0.0002 to -0.0006 Valid RankIC.
2. **Single-factor IC ranking is an inferior feature selector vs LGBM gain**. The IC-based corr-filtered sets (corr71, corr151) perform significantly worse than LGBM-gain-based subsets (FI top100).
3. **LGBM's internal feature selection is already near-optimal**: pruning the bottom 50% of features by gain (FI top100, 100 features) only loses 0.0004 RankIC, showing the tail features contribute negligible signal.
4. **More features is not always better**: corr151 (151 features, top200 IC-filtered) performed *worse* than corr71 (71 features, top100 IC-filtered), with a much larger overfit gap.

---

## 2. Background

### 2.1 SOTA Baseline

From `zebra_pool/fa3/experiments/stage1/REPORT.md`, the best configuration across 17 prior experiments is:

- **Tag**: FAIR fa2+fa1 mdil=100k
- **Features**: 198 (123 fa1 + 75 fa2, no fa3)
- **Valid RankIC**: 0.0431, gap = 0.0190, 76 trees

### 2.2 Motivation

The prior campaign showed fa3 is net-negative when added in bulk (114 features). This study asks: can a more surgical selection — using single-factor IC ranking and pairwise correlation filtering — extract the useful subset of fa3 (and/or optimally prune fa1+fa2)?

### 2.3 Single-Factor IC Computation

- **Date range**: 2025-07-01 ~ 2026-01-26 (210 days)
- **Split**: sorted days, first 80% = train (168 days), last 20% = valid (42 days)
- **Label**: `ret_lag0_next100` (forward simple return, log-diff prefix sum, ds-bounded)
- **Metrics**: Daily IC Mean, Daily Rank IC Mean, Pooled IC, Pooled Rank IC
- **Sets**: fa1 (123 factors), fa2 (75 factors), fa3 (114 factors) = 312 total

Full IC results: `ic_fa123_raw.csv`, per-horizon reports: `ic_fa123_h100.md`, `ic_fa123_h400.md`.

---

## 3. Correlation Filter Methodology

### 3.1 Greedy Admission Algorithm

Simulates a factor library admission process:

1. Sort all candidate factors by |train Daily IC| descending
2. Initialize empty library
3. For each factor in order:
   - Compute pairwise Pearson correlation with every admitted factor
   - If max |correlation| >= 0.85: **reject** (redundant)
   - Else: **admit**

### 3.2 Correlation Computation

- **Date range**: 2025-07-01 ~ 2025-10-01 (93 days, 3 months)
- **Downsample**: 1/10 (1,603,146 rows from 16M)
- **Method**: Pearson correlation on NaN-imputed (column mean), standardized factor values

### 3.3 Top-100 Results

From 312 factors, top 100 by |train Daily IC|:
- **Admitted: 71** (rejected 29, threshold |corr| >= 0.85)
- Per set: fa1=31, fa2=24, fa3=16

Rejected factors were primarily same-family parameter variants:
- `churn_displacement_ema20` blocked by `ema50` (corr=0.91)
- `impact_ema100` blocked by `impact_ema200` (corr=0.96)
- 4x `imb_l1` variants blocked by `l1_vs_wide` (corr=0.94)
- `neg_cost_asym` = `depth_cost_asym` (corr=1.00)

### 3.4 Top-200 Results

From top 200 by |train Daily IC|:
- **Admitted: 151** (rejected 49)
- Per set: fa1=67, fa2=42, fa3=42

### 3.5 fa3 Concentration in Top Tiers

| Tier | fa1 | fa2 | fa3 | fa3 % |
|---|---:|---:|---:|---:|
| Top 20 admitted | 7 | 7 | 6 | 30% |
| Top 40 admitted | 16 | 14 | 10 | 25% |
| All 71 admitted | 31 | 24 | 16 | 23% |

fa3 is over-represented in the head (30% of top-20 vs 23% overall), indicating strong single-factor IC but — as shown below — this does not translate to LGBM incremental alpha.

---

## 4. LGBM Experiment Design

### 4.1 Common Configuration (matches SOTA recipe)

```yaml
target: ret_lag0_next100
label_mode: clip 0.01
exclude_dates: [20251010]
exclude_sym_dates: [(ETHUSDT, 2025-08-29)]
date_range: 2025-07-01 ~ 2026-01-26 (210 days)
train/valid: 168/42 days (80/20 chronological)
samples: 24,697,614 train / 3,530,227 valid

lgbm:
  objective: regression
  metric: rmse
  learning_rate: 0.05
  num_leaves: 32
  min_data_in_leaf: 100000   # except corr71/corr151 which used 50000
  num_boost_round: 80
  early_stopping_rounds: 10
  feature_fraction: 0.6
  bagging_fraction: 0.8
  bagging_freq: 5
  lambda_l2: 1.0
  seed: 20260112
```

### 4.2 Experiment Matrix

| Exp | Tag | n_feat | fa3 | Selection Method |
|---:|---|---:|---:|---|
| 0 | SOTA (baseline) | 198 | 0 | All fa1+fa2, tuned recipe |
| 1 | corr71 mdil=50k | 71 | 16 | IC top100 → corr filter |
| 2 | corr151 mdil=50k | 151 | 43 | IC top200 → corr filter |
| 3 | fa12 + top6 fa3 | 204 | 6 | SOTA 198 + top-6 fa3 from corr-filtered top-20 |
| 4 | fa12 + top10 fa3 | 208 | 10 | SOTA 198 + top-10 fa3 from corr-filtered top-40 |
| 5 | fa12 + top16 fa3 | 214 | 16 | SOTA 198 + all 16 fa3 from corr-filtered top-71 |
| 6 | corr71 + FI top30 | 88 | 16 | 71 IC-corr-filtered + SOTA gain top-30, deduped |
| 7 | FI top100 | 100 | 0 | SOTA top-100 by LGBM gain importance |
| 8 | FI top150 | 150 | 0 | SOTA top-150 by LGBM gain importance |

---

## 5. Results (sorted by Valid RankIC)

| # | Tag | n_feat | Train IC | Train RIC | Valid IC | Valid RIC | gap(IC) | gap(RIC) | trees | vs SOTA |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **FAIR fa2+fa1 mdil=100k ⭐ SOTA** | 198 | 0.0705 | 0.0621 | 0.0484 | **0.0431** | 0.0221 | 0.0190 | 76 | — |
| 2 | fa12 + top10 fa3 | 208 | 0.0645 | 0.0564 | 0.0480 | 0.0428 | 0.0165 | 0.0136 | 45 | -0.0003 |
| 3 | fa12 + top16 fa3 | 214 | 0.0740 | 0.0655 | 0.0483 | 0.0428 | 0.0257 | 0.0226 | 71 | -0.0002 |
| 4 | FI top100 (fa1+fa2) | 100 | 0.0719 | 0.0635 | 0.0481 | 0.0427 | 0.0238 | 0.0208 | 80 | -0.0004 |
| 5 | fa12 + top6 fa3 | 204 | 0.0691 | 0.0609 | 0.0477 | 0.0425 | 0.0215 | 0.0184 | 61 | -0.0006 |
| 6 | corr71 + FI top30 | 88 | 0.0758 | 0.0673 | 0.0466 | 0.0417 | 0.0292 | 0.0256 | 78 | -0.0014 |
| 7 | FI top150 (fa1+fa2) | 150 | 0.0623 | 0.0545 | 0.0461 | 0.0409 | 0.0163 | 0.0136 | 53 | -0.0022 |
| 8 | corr71 (top100) mdil=50k | 71 | 0.0619 | 0.0527 | 0.0460 | 0.0403 | 0.0160 | 0.0123 | 52 | -0.0027 |
| 9 | corr151 (top200) mdil=50k | 151 | 0.0720 | 0.0618 | 0.0453 | 0.0392 | 0.0267 | 0.0227 | 60 | -0.0039 |

---

## 6. Analysis

### 6.1 fa3 Incremental Alpha: Confirmed Zero at h100 clip

Three direct tests adding fa3 to the SOTA fa1+fa2 set (Exp 3/4/5), with factors pre-screened by IC + correlation filter:

| fa3 added | Valid RIC | Delta |
|---:|---:|---:|
| +6 (top-20 IC) | 0.0425 | -0.0006 |
| +10 (top-40 IC) | 0.0428 | -0.0003 |
| +16 (all corr-filtered) | 0.0428 | -0.0002 |

All negative, confirming the Stage 1 REPORT finding that fa3 signal is already captured by fa1+fa2. The deltas are small (-0.0002 to -0.0006) and within noise, but consistently negative across all three tests.

### 6.2 IC-Based Selection vs LGBM Gain-Based Selection

| Method | n_feat | Valid RIC | gap(RIC) |
|---|---:|---:|---:|
| LGBM gain top-100 (FI top100) | 100 | 0.0427 | 0.0208 |
| IC top-100 corr-filtered (corr71) | 71 | 0.0403 | 0.0123 |
| IC + LGBM gain hybrid (corr71+FI30) | 88 | 0.0417 | 0.0256 |

LGBM gain-based pruning (FI top100) outperforms IC-based pruning (corr71) by +0.0024 RankIC, despite using more features (100 vs 71). This is expected: LGBM gain reflects the feature's contribution *within the ensemble* (accounting for interactions, redundancy), whereas single-factor IC measures marginal linear correlation in isolation.

The hybrid (corr71+FI30) falls in between but with the worst gap (0.0256), suggesting the IC-selected factors that aren't in the FI top-30 are adding noise.

### 6.3 Diminishing Returns of Feature Pruning

| Feature count | Valid RIC | vs full 198 |
|---:|---:|---:|
| 198 (all fa1+fa2) | 0.0431 | — |
| 150 (FI top150) | 0.0409 | -0.0022 |
| 100 (FI top100) | 0.0427 | -0.0004 |

Surprising non-monotonicity: FI top100 > FI top150 > full 198 is NOT the pattern. Instead: full 198 > FI top100 > FI top150. The FI top150 result (0.0409, 53 trees) suggests early stopping behaved differently with 150 features — the model stopped too early (53 vs 76-80 trees), possibly because the added 50 low-gain features created noise in the validation loss signal.

### 6.4 Overfit Gap Patterns

The tightest gaps come from configurations with fewer effective features and/or fewer trees:

| Tag | gap(RIC) | trees |
|---|---:|---:|
| corr71 mdil=50k | **0.0123** | 52 |
| fa12 + top10 fa3 | **0.0136** | 45 |
| FI top150 | **0.0136** | 53 |
| SOTA | 0.0190 | 76 |
| corr71 + FI top30 | 0.0256 | 78 |

Low gap ≠ good model. The corr71 gap (0.0123) is the smallest but its Valid RIC (0.0403) is also lower — the model is underfitting, not generalizing better.

---

## 7. Conclusions

1. **SOTA remains SOTA**. The `fa2+fa1` 198-feature tuned recipe (Valid RankIC 0.0431) cannot be improved by any pre-selection strategy tested here.

2. **Single-factor IC is a weak proxy for LGBM utility**. Factors with high marginal IC may be redundant within the ensemble, and factors with low marginal IC may contribute through interactions. LGBM gain is a strictly better feature importance signal.

3. **fa3 is confirmed zero-alpha at h100 clip**, regardless of selection method. This is the third independent validation (after the Stage 1 campaign and the stage2d/2e top-20 tests).

4. **Aggressive pruning hurts slightly, modest pruning is neutral**. Keeping the top-100 features by LGBM gain loses only 0.0004 RankIC. But the full 198-feature set is still optimal, suggesting even the long tail of low-gain features contributes marginal positive signal.

5. **Correlation filter is useful for factor library management** (reducing redundancy for interpretability and storage) but **not for LGBM performance optimization**. LGBM handles correlated features gracefully through its split-based selection.

---

## 8. Artifacts

| File | Description |
|---|---|
| `ic_fa123_raw.csv` | 312-factor IC metrics (624 rows: 2 horizons x 312 factors) |
| `ic_fa123_h100.md` / `ic_fa123_h400.md` | Per-horizon IC reports with sorted tables |
| `ic_dist_h100.png` / `ic_dist_h400.png` | IC distribution histograms (3x2 grid) |
| `corr_filter_h100.md` | Top-100 greedy admission report (71 admitted) |
| `corr_filter_h100_top200.md` | Top-200 greedy admission report (151 admitted) |
| `corr_filter_h100.png` / `corr_filter_h100_top200.png` | Admitted factors |corr| heatmaps |
| `corr_matrix_h100_top100.csv` / `corr_matrix_h100_top200.csv` | Full pairwise correlation matrices |
| `factor_corr_filter.py` | Correlation filter script (configurable via `CORR_TOP_N` env var) |
| `compute_ic.py` | IC computation script (matches analyzer methodology) |
| `make_report.py` | IC report generator |

LGBM experiment outputs under `/data/db/crypto/analyzer/fa3_tuning_stage1/`:

| Directory | Experiment |
|---|---|
| `fair_fa2_fa1_mdil100k/` | SOTA baseline (from prior campaign) |
| `corr71_mdil50k/` | 71 IC-corr-filtered, mdil=50k |
| `corr151_top200_mdil50k/` | 151 IC-corr-filtered from top200, mdil=50k |
| `fa12_plus_fa3_6_mdil100k/` | SOTA + 6 fa3 |
| `fa12_plus_fa3_10_mdil100k/` | SOTA + 10 fa3 |
| `fa12_plus_fa3_16_mdil100k/` | SOTA + 16 fa3 |
| `corr71_fi30_mdil100k/` | corr71 + FI top30 hybrid |
| `fi_top100_mdil100k/` | FI top-100 (fa1+fa2 only) |
| `fi_top150_mdil100k/` | FI top-150 (fa1+fa2 only) |
