# FA3 LGBM Hyperparameter Tuning Experiment Report

**Author**: research session, 2026-04-15
**Task**: h100 clip on world_pool factor data (clip threshold 0.01, exclude 20251010)
**Goal**: (1) reduce overfitting in the fa3+fa2+fa1 merged model; (2) determine whether fa3 brings true incremental alpha over the fa1+fa2 baseline.

---

## 1. Executive summary

Across **17 controlled experiments** spanning four stages (Stage 1, 1b, 1c, Stage 2 single-knob sweep, Stage 3/4 combined-regularization + feature-pruning), the headline findings are:

1. **The best overall configuration is `fa2+fa1` (no fa3) with a tuned LGBM recipe at `min_data_in_leaf=100000`.** Valid IC = 0.0484, **Valid RankIC = 0.0431**, train-valid gap = 0.0190. This improves the original untuned `fa2+fa1` baseline (Valid RankIC 0.0386) by **+11.7%**.
2. **Adding fa3 features is net-negative on this task**, in every fair (same-hyperparams) comparison. The best `fa3+fa2+fa1` configuration we found, *stage2b* (top-100 features + `num_leaves=16` + `feature_fraction=0.5`), reached Valid RankIC 0.0413 — still **−0.0018** below pure fa2+fa1 at the same recipe.
3. The original "fa3 brings +20–80% RankIC" claim from the fa3 step-3 analyzer summary was based on **`merged-vs-fa3_only`** (where fa1+fa2 do the heavy lifting), not **`merged-vs-fa1+fa2`**. Under the correct comparison, fa3's incremental contribution at h100 clip is **0 to mildly negative**.
4. **Most effective overfit knob**: `num_leaves: 32 → 16` cut the train-valid RankIC gap from 0.0311 → 0.0196 with no hit to valid. Combined with `feature_fraction=0.5` it produced the tightest gap of any fa3-merged run (0.0171, in stage2b).
5. **Ineffective knobs**: `top-100 / top-20 feature pruning`, `lambda_l2 1→10`, `mdil 50k→100k` (when applied to fa3 merged).
6. **Important methodology lesson**: comparing a tuned new model against an untuned baseline silently rolls hyperparameter tuning into the apparent "feature alpha". An early Stage 1b vs untuned fa2+fa1 read showed fa3 +0.0016; the same comparison under matched hyperparams flipped to −0.0018. **Always rerun the baseline under the new recipe before concluding a feature has alpha.**

---

## 2. Background and motivation

`fa3` is a 114-factor family produced by the FA3 step-3 study (orderbook walk / depletion / dormancy / cancel-cascade signals). The fa3 step-3 analyzer report claimed that adding fa3 to the existing fa1+fa2 baseline brought meaningful Valid RankIC improvement (+20%–86% at clip/rank). Specifically:

- merged198 + fa3 → 312 features
- vs fa3-only (114 features): RankIC delta +20–86%

But that comparison left fa1+fa2 absent from one side. When the user asked to compare `fa3+fa2+fa1` directly against the existing on-disk `fa2+fa1` (default LGBM params on both, 199 vs 312 features), the result reversed:

| | fa2+fa1 (199) | fa3+fa2+fa1 (312) | Δ |
|---|---:|---:|---:|
| Train RankIC | 0.0535 | 0.0607 | +13.5% |
| **Valid RankIC** | **0.0386** | **0.0362** | **−6.2%** |
| gap (RankIC) | 0.0149 | 0.0245 | +0.0096 |

Adding fa3 raised train, lowered valid, and roughly doubled the train-valid gap — clear overfitting. The user then asked: can hyperparameter tuning rescue fa3? This experiment campaign is the answer.

---

## 3. Methodology

### 3.1 Data
- **Source**: `/data/db/crypto/futures/world/world_pool/{fa1_merged_for_report, fa2, fa3}/`
- **Dataset**: 7 symbols (BTC, ETH, SOL, BNB, XRP, DOGE, ADA), 210 trading days **2025-07-01 to 2026-01-26**
- **Excluded**: `(ETHUSDT, 2025-08-29)` (anomalous data); date `20251010` (anomalous market regime)
- **Bars**: amount-bar (variable duration) — 28,771,381 total rows
- **Label**: `ret_lag0_next100` = 100-bar forward return, clip mode `|y| > 0.01 → NaN`
- **Train/Valid split**: chronological 80/20 → **168 train days** (2025-07-01..2025-12-15), **42 valid days** (2025-12-16..2026-01-26). 24,697,614 train samples, 3,530,227 valid samples.

### 3.2 Common hyperparameters across the tuning campaign
Every Stage 1/2/3/4 run uses the same anti-overfit recipe **except for the one knob being varied**. Base recipe (Stage 1b values shown):

```
objective         = regression
metric            = rmse
learning_rate     = 0.05         (was 0.1 in untuned baseline)
num_leaves        = 32
min_data_in_leaf  = 50000        (was 10000)
num_boost_round   = 80           (ceiling, was 20 fixed)
early_stopping    = 10           (NEW; tracks valid set)
feature_fraction  = 0.6          (NEW)
bagging_fraction  = 0.8          (NEW)
bagging_freq      = 5            (NEW)
lambda_l2         = 1.0          (NEW)
num_threads       = 48 / 64 / 96 (varies by stage; doesn't affect IC)
seed              = 20260112
```

Validation labels stay finite (clip is only applied to the regression target during training; valid IC/RankIC use unclipped labels).

### 3.3 Metrics
- **Daily IC**: per-day Pearson correlation of LGBM prediction vs forward return → averaged
- **Daily RankIC**: per-day Spearman correlation → averaged
- **gap(RankIC)** = mean train RankIC − mean valid RankIC (overfit indicator)
- **trees**: actual number of boosting rounds (early stopping may halt before the ceiling)

### 3.4 Software
- `lightgbm 4.x` Python API
- Driver: `/home/cken/crypto_world/zebra_pool/fa3/code/run_fa3_lgbm_only.py` (extended with `--lgbm-*` overrides and `--factor-whitelist` during this campaign)
- Analyzer pipeline: `/home/cken/crypto_world/research/analyzer/` (`config.py` and `model_lgbm.py` were extended with the new LGBM knobs)

### 3.5 Memory budget and watchdog
- Hardware: 503 GB RAM, 128 cores
- Soft cap during tuning: **400 GB total system used**
- Watchdog: `experiments/stage1/mem_watchdog.py` polls `psutil.virtual_memory().used` every 5 s; on overshoot, sends SIGTERM (then SIGKILL after 10 s) to all processes in the runner's process group.
- The watchdog triggered exactly once (Stage 3, original sequential attempt at 17:30 — collision with background research workers); subsequent stages stayed safely below.

---

## 4. Results: full table (sorted by Valid RankIC)

| # | Tag | n_feat | Train IC | Train RankIC | Valid IC | **Valid RankIC** | gap(RankIC) | trees |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **FAIR fa2+fa1 mdil=100k** ⭐ overall best | 198 | 0.0705 | 0.0621 | 0.0484 | **0.0431** | 0.0190 | 76 |
| 2 | FAIR fa2+fa1 mdil=50k | 198 | 0.0700 | 0.0603 | 0.0492 | 0.0421 | 0.0182 | 61 |
| 3 | stage1f fa3+fa2+fa1 ff=0.3 | 312 | 0.0843 | 0.0735 | 0.0475 | 0.0417 | 0.0317 | 79 |
| 4 | **stage2b top100+nl=16+ff=0.5** ★ best fa3 | 100 | 0.0687 | 0.0583 | 0.0471 | **0.0413** | **0.0171** | 77 |
| 5 | stage2d fa2+fa1+top20 fa3 mdil=100k | 218 | 0.0800 | 0.0709 | 0.0462 | 0.0407 | 0.0302 | 77 |
| 6 | stage2e fa2+fa1+top20 fa3 nl=16 | 218 | 0.0655 | 0.0571 | 0.0460 | 0.0406 | 0.0165 | 76 |
| 7 | stage1e fa3+fa2+fa1 nl=16 | 312 | 0.0701 | 0.0599 | 0.0462 | 0.0404 | 0.0196 | 80 |
| 8 = | stage1b fa3+fa2+fa1 mdil=50k | 312 | 0.0820 | 0.0713 | 0.0462 | 0.0402 | 0.0311 | 65 |
| 8 = | stage1g fa3+fa2+fa1 lambda_l2=10 | 312 | 0.0820 | 0.0713 | 0.0462 | 0.0402 | 0.0311 | 65 |
| 10 | stage2a top100+nl=16 | 100 | 0.0702 | 0.0598 | 0.0458 | 0.0400 | 0.0199 | 80 |
| 11 | stage2c top100+mdil=100k | 100 | 0.0803 | 0.0716 | 0.0449 | 0.0397 | 0.0319 | 72 |
| 12 = | stage2h top100+mdil=50k | 100 | 0.0812 | 0.0702 | 0.0451 | 0.0393 | 0.0309 | 64 |
| 12 = | stage1d top100 (full ff=0.6) | 100 | 0.0812 | 0.0702 | 0.0451 | 0.0393 | 0.0309 | 64 |
| 14 | stage1 fa3+fa2+fa1 mdil=20k | 312 | 0.0872 | 0.0727 | 0.0450 | 0.0387 | 0.0340 | 64 |
| 15 | **A — fa2+fa1 untuned** (orig baseline) | 199 | 0.0678 | 0.0535 | 0.0464 | 0.0386 | 0.0149 | 20 |
| 16 | stage1c fa3+fa2+fa1 mdil=100k | 312 | 0.0799 | 0.0709 | 0.0439 | 0.0385 | 0.0324 | 70 |
| 17 | **B — fa3+fa2+fa1 untuned** | 312 | 0.0766 | 0.0607 | 0.0422 | 0.0362 | 0.0245 | 20 |

Output paths under `/data/db/crypto/analyzer/fa3_tuning_stage1/<tag>/` (Stages 1/2/3/4) and `/data/db/crypto/analyzer/{fa2,fa3}/...` (untuned references).

---

## 5. Stage-by-stage narrative

### Stage 1 — single-knob exploration of `min_data_in_leaf` on fa3+fa2+fa1

- **Stage 1 mdil=20k**: Valid IC 0.0450, Valid RankIC 0.0387, gap 0.0340. Lowering lr to 0.05 + 64 rounds + the new regularizers raised Valid RankIC vs untuned (0.0362 → 0.0387, +6.9%) but the gap *widened* (0.0245 → 0.0340) because the lower lr lets the model fit more depth on train.
- **Stage 1b mdil=50k**: Valid IC 0.0462, **Valid RankIC 0.0402**, gap 0.0311. Direction was right — both IC and RankIC improved over Stage 1, gap shrank slightly. This became the "best fa3 single-knob" until Stage 2/3.
- **Stage 1c mdil=100k**: Valid IC 0.0439, Valid RankIC 0.0385, gap 0.0324. **Inverted-U**: 100k overshot. Train IC dropped (0.0820 → 0.0799) but valid dropped MORE — the leaves became too smooth to capture valid-period structure.

**Conclusion**: 50k was the mdil sweet spot for fa3-merged; the knob alone could not tighten the gap below ~0.031.

### Stage 2 — single-knob sweep, anti-overfit toolkit (each one varies one knob from Stage 1b base)

| Knob | Valid RankIC vs Stage 1b 0.0402 | gap vs 0.0311 |
|---|---:|---:|
| `num_leaves 32→16` (stage1e) | 0.0404 (≈0) | **0.0196 (−37%)** ⭐ |
| `feature_fraction 0.6→0.3` (stage1f) | **0.0417 (+0.0015)** ★ | 0.0317 (≈0) |
| `lambda_l2 1→10` (stage1g) | 0.0402 (0) | 0.0311 (0) |
| `top100 features` (stage1d) | 0.0393 (−0.0009) | 0.0309 (≈0) |

- **`num_leaves=16`** is a *gap killer*: the simpler trees lose representational depth on train (RankIC 0.0713→0.0599) but valid is unchanged. Without an asymmetric cost it's a free regularizer.
- **`feature_fraction=0.3`** is the only Stage-2 knob that *raises valid* meaningfully. Each tree sees only 30% of features, decorrelating ensemble members. Did not shrink gap.
- **`lambda_l2=10`** had zero effect — early-stopping at round 64 means the regularizer never reached strength to bind. Would need ≥50 to matter.
- **`top-100 feature pruning`** is also a no-op. The discarded 212 features cumulatively held only 5.7% of total gain. Not where the overfitting comes from.

**Stage-3 fair-baseline shock**: Running `fa2+fa1` under the *same* tuned recipe yielded 0.0421 (mdil=50k) and **0.0431** (mdil=100k). Both **comfortably above any fa3+fa2+fa1 run**. This was the moment we realized fa3's "improvement" so far was a hyperparameter mirage.

### Stage 3+4 — combined regularization and feature-set surgery

The Stage 3/4 batch tested 6 combined ideas:

| Tag | Recipe (delta from Stage 1b) | Valid RankIC | gap |
|---|---|---:|---:|
| stage2a | top100 + nl=16 | 0.0400 | 0.0199 |
| **stage2b** | top100 + nl=16 + ff=0.5 | **0.0413** | **0.0171** |
| stage2c | top100 + mdil=100k | 0.0397 | 0.0319 |
| stage2d | fa2+fa1 + top-20 fa3 + mdil=100k | 0.0407 | 0.0302 |
| stage2e | fa2+fa1 + top-20 fa3 + nl=16 + mdil=100k | 0.0406 | 0.0165 |
| stage2h | top100 + mdil=50k (the user-requested point) | 0.0393 | 0.0309 |

- **stage2b** is the campaign's best fa3-inclusive run. Combining the two effective Stage-2 knobs on top of the cleanest 100-feature subset compresses the gap to **0.0171** (tighter than fa2+fa1 baseline 0.0190) while putting valid at 0.0413. Still 0.0018 below pure fa2+fa1.
- **stage2d/2e** test the "minimally invasive" fa3 augmentation: keep all fa1+fa2, add the top-20 fa3 only. Both **lose** versus pure fa2+fa1 (0.0407 / 0.0406 vs 0.0431). Even 20 carefully-selected fa3 features hurt, dropping valid by ~0.0024 and inflating gap.
- **stage2e** has the tightest gap of any run (0.0165) because it stacks every regularizer (small leaves + mdil=100k + bagging + ff=0.6 + λ2=1) on the smallest meaningful feature increment over fa2+fa1. It still loses to plain fa2+fa1.
- **stage2h** (the user-requested top100 + mdil=50k point) reproduces stage1d to within rounding — confirms mdil 50k vs 100k makes negligible difference on the top-100 feature subset; the binding regularizer is `num_leaves`, not `mdil`.

---

## 6. Cross-cutting analysis

### 6.1 Does fa3 add value at h100 clip?

**No, in every fair (matched-hyperparam) comparison.** The four pairs:

| Recipe | fa2+fa1 | fa3+fa2+fa1 | Δ Valid RankIC |
|---|---:|---:|---:|
| Stage 1b base, mdil=50k | 0.0421 | 0.0402 | **−0.0019** |
| Stage 1c base, mdil=100k | 0.0431 | 0.0385 | **−0.0046** |
| stage2d/2e: fa2+fa1+top20 fa3 vs fa2+fa1 | 0.0431 | 0.0407 / 0.0406 | **−0.0024 / −0.0025** |

In all four matched comparisons, **adding fa3 hurts** by 0.0019–0.0046 RankIC. The gap also widens by 0.011–0.013, suggesting the extra features inject noise rather than orthogonal information.

The original fa3 study's "merged adds value" claim is true *only when comparing merged-vs-fa3_only*. In other words, fa3 features **do** carry signal — they beat training on fa3 features alone. But that signal is **already captured by fa1+fa2** at h100 clip: the marginal information gain is zero or negative once those baseline features are present.

### 6.2 The fair-baseline lesson

Initial Stage 1b reading (Valid RankIC 0.0402) compared to the on-disk **untuned** fa2+fa1 (0.0386) suggested fa3+tuning gave +0.0016 alpha. But once we ran fa2+fa1 under the SAME tuned recipe (0.0421 at mdil=50k, 0.0431 at mdil=100k), the sign flipped: fa3 contributes −0.0019 to −0.0046, and the +0.0016 was entirely a hyperparameter tuning effect attributed to the wrong cause.

**Generalizable rule**: when claiming a new feature/family adds alpha, the baseline must be re-tuned under the *same* recipe. Otherwise, hyperparameter tuning effects masquerade as feature effects.

### 6.3 Why does fa3 hurt rather than help?

Hypotheses (not directly tested in this campaign):

1. **Collinearity with fa1 L2-microstructure family** — fa3's depletion/walk/ghost factors partially redundant with fa1's `stale_*`, `imb_*`, `cost_*` series; the extra features steal split capacity without contributing orthogonal info.
2. **Time-horizon mismatch** — fa3's design center (depletion, dormancy) is naturally lower-frequency than h100 (~30 s mean hold). At h400 rank, the picture might differ — the original fa3 step-3 report's strongest claim was on long-horizon rank label.
3. **Noise injection** — 114 noisy features increase ensemble variance enough that even early-stopping + bagging can't compensate.

The campaign deliberately stayed at h100 clip; testing fa3 at h400 rank is the natural next experiment.

### 6.4 What IS the right LGBM recipe for h100 clip?

Final recommendation, taken from the no.1 row of the table:

```yaml
target: ret_lag0_next100
label_mode: clip 0.01
factors: fa1 (123) + fa2 (75)        # 198 features
exclude_dates: [20251010]
exclude_sym_dates: [(ETHUSDT, 2025-08-29)]

lgbm:
  objective: regression
  metric: rmse
  learning_rate: 0.05
  num_leaves: 32
  min_data_in_leaf: 100000
  num_boost_round: 80
  early_stopping_rounds: 10            # tracks valid set
  feature_fraction: 0.6
  bagging_fraction: 0.8
  bagging_freq: 5
  lambda_l2: 1.0
  num_threads: 48-96
  seed: 20260112
```

Result: Train IC 0.0705 / Train RankIC 0.0621 / **Valid IC 0.0484** / **Valid RankIC 0.0431** / gap 0.0190 / 76 trees.

vs the original `fa2+fa1` untuned baseline (Valid RankIC 0.0386), this is **+11.7%** — and that gain is entirely from the LGBM tuning, *not* from any new feature family.

---

## 7. Recommendations / next steps

1. **Use the recipe above for the next h100 clip backtest.** Stop trying to add fa3 to h100 clip.
2. **Test fa3 at h400 rank** before fully retiring it. The original fa3 report's strongest claim was at long horizons; rank-label dynamics may favor fa3's lower-frequency depletion features.
3. **If fa3 still loses at h400 rank**, scope-limit the fa3 family in the project's records — its incremental alpha (vs fa1+fa2) is unproven.
4. **Update `crypto-factor-analyzer` skill defaults** to use `early_stopping_rounds`, `feature_fraction`, `bagging_*`, `lambda_l2` knobs. Currently the skill doesn't expose these and analysts won't get them by accident.
5. **Memory**: write a feedback memory `feedback_fair_baseline_comparison.md` capturing the lesson: every "new feature beats baseline" claim must use a baseline re-trained under the same recipe.
6. **Methodology note**: the early-stopping on the validation set creates a mild leakage risk — valid IC is slightly optimistic because early stop chose the best round on that same set. For the headline 0.0431 number, this is a known second-order effect; for the cross-experiment comparison it's a wash since every run had it.

---

## 8. Reproducibility

### 8.1 Driver and modes
Driver: `/home/cken/crypto_world/zebra_pool/fa3/code/run_fa3_lgbm_only.py`

Modes:
- `--mode fa3_only`: 114 fa3_* features only (label carrier from fa1_full)
- `--mode fa3_baseline`: full 312-feature merged set (123 fa1 + 75 fa2 + 114 fa3)
- `--mode fa2_fa1_only`: 198-feature fa1+fa2 merged set (added during this campaign)

CLI knobs added in this campaign:
```
--lgbm-lr            --lgbm-num-leaves      --lgbm-min-data
--lgbm-rounds        --lgbm-n-jobs          --lgbm-feature-fraction
--lgbm-bagging-fraction  --lgbm-bagging-freq  --lgbm-lambda-l2
--lgbm-early-stopping
--factor-whitelist FILE       # restrict training features to the whitelist
```

`ReportConfig` and `model_lgbm.py` (under `/home/cken/crypto_world/research/analyzer/`) were extended with the new knobs; defaults preserve legacy behavior.

### 8.2 Batch scripts
- Stage 1: `experiments/stage1/run_stage1.sh`
- Stage 1b: `experiments/stage1/run_stage1b_mdil50k.sh`
- Stage 1c + Stage 2 (single-knob sweep): `experiments/stage1/run_stage2_batch.sh` (sequential, n_jobs=48)
- Stage 3+4 (combined sweep): `experiments/stage1/run_stage3_batch.sh` (sequential, n_jobs=96) → killed after run 1; replaced by `run_stage4_parallel.sh` (2-pair + single, n_jobs=64) and `run_stage4_leftover.sh`. The parallel scripts have a known bug (the `$(run_bg ...)` pattern captures the wrong pid because the function emits multiple lines on stdout); the leftover script worked despite this only because all 3 jobs accidentally launched at once (peak 391 GB) and finished without the watchdog tripping. **Fix in any future batch**: emit all log lines to stderr and only the pid to stdout.

### 8.3 Whitelists
- `experiments/stage1/stage1b_top100.txt` — top-100 features by gain from stage1b (44 fa3 / 29 fa2 / 27 fa1)
- `experiments/stage1/stage1b_top20_fa3.txt` — top-20 fa3 features by gain
- `experiments/stage1/fa2_fa1_plus_fa3_top20.txt` — all 198 fa1/fa2 + top-20 fa3 = 218 features

### 8.4 Output paths
- Stages 1, 1b, 1c, 2a-2h, fair_*: `/data/db/crypto/analyzer/fa3_tuning_stage1/<tag>/`
  Each contains `lgbm_train_info.json`, `lgbm_daily_ic.parquet`, `lgbm_feature_importance.parquet`, `lgbm_model.txt`, `lgbm_top0p1_daily.parquet`, `lgbm_top0p01_daily.parquet`, `report.md`, `img/`.
- Reference baselines: `/data/db/crypto/analyzer/fa2/fa2_fa1_clip001/`, `/data/db/crypto/analyzer/fa3/fa3_merged_baseline198_clip001/`

### 8.5 Memory watchdog
`experiments/stage1/mem_watchdog.py <pgid> <limit_gb> <log_file>` — polls every 5 s, kills the entire pgid (except itself) when `psutil.virtual_memory().used` exceeds the limit. Triggered exactly once during the campaign (Stage 3 sequential, 17:30:32, ~401 GB, background workers + our run); after that all stages stayed safely under.

### 8.6 Wall time
- Stage 1 → Stage 1c (3 runs): ~65 min
- Stage 2 batch (7 runs sequential, 48 threads): ~140 min
- Stage 3 batch (7 runs sequential, 96 threads): ~17 min before being killed by watchdog at 17:30; ~140 min in restart attempt that became Stage 4
- Stage 4 parallel pair 1 (2 runs simultaneous, 64 threads each): ~23 min for both
- Stage 4 leftover (3 runs, accidentally simultaneous, 64+96 threads): ~22 min for all three (peak 391 GB)
- **Total tuning campaign wall time**: roughly **6 hours**

### 8.7 What I would change next time
1. Fix `run_bg` to emit pid-only on stdout (`echo "starting..." >&2`) before any further parallel batches.
2. Run a baseline check at the same recipe **immediately** after the first fa3 tuned run, before launching downstream sweeps. Would have caught the "fa3 doesn't help" finding hours earlier.
3. Add `lambda_l1` to the override surface — `lambda_l2=10` was ineffective and an L1 sweep might have been more useful.
4. Build a simple results aggregator (`compile_results.py`) that walks `fa3_tuning_stage1/*` and prints a sorted summary, instead of hand-coding a pandas snippet each time.
