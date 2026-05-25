# FA26 Known Issues

## Confirmed Redundancy: tte_ofi_wide == rgi_wide_std

- **Status**: ACKNOWLEDGED (not a code bug)
- **Description**: Both factors have mathematically identical definitions: `EMA(ofi * I(spread_ema > 5.0), hl=100)`. This was predicted in §9 of the factor list ("rgi_wide_std vs tte_ofi_wide: 高相关"). Now confirmed at Pearson r=1.000000 across 18 trading days.
- **Impact**: 82 factors → 81 independent factors (+ 5 R-class placeholders → 76 effective)
- **Action**: Keep both in output as defined. Downstream Analyzer2 corr heatmap will flag this.

## Sparsity Calibration Differences

- `ss_dir_hl25`: 72.6% zero (expected 98.3%). Likely due to epsilon=1e-8 allowing small EMA values to trigger same-sign detection. Research may have used a larger epsilon.
- `twmr_edge_flip_seed`: 41.0% nonzero (expected 1.84%). The wider gate `(dir_local != 0 && dir_time != 0)` is intentionally less restrictive than seed_conversion's flip_flag.
- `tte_div_ret_aggr`: 65.9% nonzero (expected 30-50%). Warmup=10 is easily satisfied at bar-level sampling.

## R-class Placeholders (5 factors output 0.0)

- mt63_cancel_reprice_ratio, mt63_pre_sweep_cancel_accel, mt63_cancel_adjusted_response, mt63_directional_cancel_intensity, post_absorption_cancel_imb
- These have "R 类草案" status with insufficient seven-element definitions.
