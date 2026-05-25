# Correlation Filter (mid-label, h100 top 100)

- Corr date range: 2025-07-01 ~ 2025-10-01 (93 days, 1/10 downsample, 1,601,590 rows)
- Threshold |corr| >= 0.85 reject
- Admission: |train daily IC| descending
- Admitted: 74 / 100  (rejected 26)
- Per set: {'fa1': 35, 'fa2': 27, 'fa3': 11, 'fa4': 1}

## Admitted

| rk | signal | set | tr dIC | va dIC | tr dRIC | va dRIC |
|---:|---|---|---:|---:|---:|---:|
| 1 | `fa3_dist_200` | fa3 | -0.0451 | -0.0981 | -0.0627 | -0.1143 |
| 2 | `fa1_buy_ratio` | fa1 | +0.0423 | +0.0421 | +0.0437 | +0.0432 |
| 3 | `fa2_confirmed_flow_h20` | fa2 | +0.0414 | +0.0408 | +0.0415 | +0.0411 |
| 4 | `fa2_crossover_20_100` | fa2 | +0.0412 | +0.0401 | +0.0372 | +0.0374 |
| 5 | `fa2_ofi_regime_z` | fa2 | +0.0401 | +0.0406 | +0.0414 | +0.0425 |
| 6 | `fa1_stale_log_ratio` | fa1 | +0.0388 | +0.0359 | +0.0404 | +0.0374 |
| 7 | `fa2_isolated_shock_h60` | fa2 | -0.0370 | -0.0381 | -0.0394 | -0.0413 |
| 8 | `fa2_impact_delta_10_100` | fa2 | +0.0367 | +0.0331 | +0.0338 | +0.0344 |
| 9 | `fa2_small_flow_only_h60` | fa2 | +0.0362 | +0.0346 | +0.0399 | +0.0392 |
| 10 | `fa2_flow_momentum` | fa2 | +0.0362 | +0.0350 | +0.0366 | +0.0380 |
| 11 | `fa1_stale_asym_sign` | fa1 | +0.0343 | +0.0304 | +0.0338 | +0.0302 |
| 12 | `fa1_net_active_flow` | fa1 | +0.0332 | +0.0297 | +0.0323 | +0.0292 |
| 13 | `fa1_sell_herf` | fa1 | -0.0321 | -0.0329 | -0.0372 | -0.0381 |
| 14 | `fa1_stale_zscore20` | fa1 | +0.0312 | +0.0291 | +0.0342 | +0.0347 |
| 15 | `fa2_ofi_spread_convex` | fa2 | +0.0310 | +0.0317 | +0.0363 | +0.0370 |
| 16 | `fa2_broad_big_flow_h20` | fa2 | +0.0304 | +0.0306 | +0.0320 | +0.0323 |
| 17 | `fa2_signed_flow_fast` | fa2 | +0.0303 | +0.0267 | +0.0312 | +0.0271 |
| 18 | `fa3_d_imb_ema8` | fa3 | +0.0277 | +0.0291 | +0.0268 | +0.0285 |
| 19 | `fa1_run_composite` | fa1 | -0.0272 | -0.0345 | -0.0153 | -0.0187 |
| 20 | `fa1_l1_vs_wide` | fa1 | +0.0262 | +0.0277 | +0.0266 | +0.0284 |
| 21 | `fa2_imb_3` | fa2 | +0.0262 | +0.0244 | +0.0275 | +0.0255 |
| 22 | `fa2_impact_ema20` | fa2 | +0.0253 | +0.0163 | +0.0239 | +0.0166 |
| 23 | `fa1_imb_1bps` | fa1 | +0.0252 | +0.0243 | +0.0254 | +0.0245 |
| 24 | `fa1_depth_cost_asym` | fa1 | -0.0248 | -0.0239 | -0.0267 | -0.0254 |
| 25 | `fa1_active_buy_ratio` | fa1 | +0.0245 | +0.0202 | +0.0258 | +0.0220 |
| 26 | `fa2_samepx_break_sell` | fa2 | -0.0243 | -0.0233 | -0.0734 | -0.0961 |
| 27 | `fa1_f01_persist_strength` | fa1 | -0.0242 | -0.0328 | -0.0150 | -0.0270 |
| 28 | `fa1_stale_ask_log` | fa1 | +0.0237 | +0.0170 | +0.0327 | +0.0262 |
| 29 | `fa1_max_directional_run_bps` | fa1 | +0.0237 | +0.0222 | +0.0249 | +0.0274 |
| 30 | `fa2_signed_divergence` | fa2 | +0.0237 | +0.0289 | +0.0168 | +0.0241 |
| 31 | `fa1_buy_ratio_conditioned` | fa1 | +0.0236 | +0.0229 | +0.0247 | +0.0241 |
| 32 | `fa3_ema_mean_depletion_log_hl96` | fa3 | +0.0232 | +0.0106 | +0.0198 | +0.0075 |
| 33 | `fa1_churn_displacement` | fa1 | +0.0232 | +0.0208 | +0.0308 | +0.0308 |
| 34 | `fa2_signed_ret_spread_gate` | fa2 | +0.0232 | +0.0234 | +0.0251 | +0.0253 |
| 35 | `fa1_dimb_delta_fast` | fa1 | +0.0231 | +0.0224 | +0.0222 | +0.0214 |
| 36 | `fa1_stale_asym` | fa1 | +0.0230 | +0.0192 | +0.0358 | +0.0327 |
| 37 | `fa2_big_signed_ema_50` | fa2 | +0.0227 | +0.0208 | -0.0020 | -0.0196 |
| 38 | `fa1_f24_queuefrag_asym_all` | fa1 | +0.0226 | +0.0227 | +0.0225 | +0.0229 |
| 39 | `fa1_neg_imb05_ema100` | fa1 | +0.0222 | +0.0328 | +0.0215 | +0.0327 |
| 40 | `fa3_ema_signed_walk_amount_hl128` | fa3 | -0.0215 | -0.0472 | -0.0204 | -0.0467 |
| 41 | `fa2_big_signed_surprise_50` | fa2 | +0.0211 | +0.0188 | -0.0017 | -0.0194 |
| 42 | `fa2_fast_rev` | fa2 | +0.0210 | +0.0211 | +0.0219 | +0.0216 |
| 43 | `fa2_big_burst_signed` | fa2 | +0.0208 | +0.0221 | -0.0006 | -0.0197 |
| 44 | `fa2_large_trade_flow` | fa2 | -0.0201 | -0.0400 | -0.0095 | -0.0325 |
| 45 | `fa1_cost_curve_asym` | fa1 | -0.0201 | -0.0186 | -0.0216 | -0.0204 |
| 46 | `fa1_cost_asym_4tick` | fa1 | -0.0197 | -0.0169 | -0.0217 | -0.0189 |
| 47 | `fa1_depth_asym20_diff1bar` | fa1 | +0.0190 | +0.0191 | +0.0191 | +0.0194 |
| 48 | `fa1_fair_mid_gap_now_bps` | fa1 | +0.0186 | +0.0188 | +0.0212 | +0.0225 |
| 49 | `fa1_depth_asym20_diff2bar` | fa1 | +0.0186 | +0.0187 | +0.0185 | +0.0188 |
| 50 | `fa1_active_sell_ratio` | fa1 | -0.0182 | -0.0175 | -0.0195 | -0.0183 |
| 51 | `fa3_ema_mean_top5_depletion_log_hl96` | fa3 | +0.0173 | +0.0034 | +0.0137 | -0.0021 |
| 52 | `fa1_imb_gradient` | fa1 | +0.0172 | +0.0190 | +0.0175 | +0.0202 |
| 53 | `fa1_run_den_unsigned` | fa1 | +0.0171 | +0.0078 | +0.0097 | +0.0023 |
| 54 | `fa3_ema_max_walk_bps_hl96` | fa3 | +0.0170 | +0.0118 | +0.0087 | +0.0033 |
| 55 | `fa2_samepx_break_buy` | fa2 | +0.0170 | +0.0156 | -0.0347 | -0.0615 |
| 56 | `fa2_asym_ema50` | fa2 | -0.0166 | -0.0330 | -0.0116 | -0.0319 |
| 57 | `fa3_p2f_dormancy_release_ema50` | fa3 | +0.0165 | +0.0141 | +0.0127 | +0.0089 |
| 58 | `fa1_herf_side_asym` | fa1 | +0.0165 | +0.0172 | +0.0133 | +0.0147 |
| 59 | `fa3_ema_max_depletion_log_hl96` | fa3 | +0.0163 | +0.0130 | +0.0143 | +0.0088 |
| 60 | `fa3_eff_cost_asym_wide_gated_v1` | fa3 | +0.0161 | +0.0138 | +0.0164 | +0.0148 |
| 61 | `fa3_cand_touch_share_imb` | fa3 | +0.0161 | +0.0095 | +0.0194 | +0.0171 |
| 62 | `fa4_s58_core_balance_ema16` | fa4 | -0.0160 | -0.0135 | -0.0193 | -0.0186 |
| 63 | `fa1_imb_l1_x_spread` | fa1 | +0.0159 | +0.0177 | +0.0266 | +0.0268 |
| 64 | `fa2_arrival_logdt_200` | fa2 | -0.0155 | -0.0078 | -0.0114 | -0.0038 |
| 65 | `fa2_ier_ema10` | fa2 | +0.0151 | +0.0084 | +0.0116 | +0.0054 |
| 66 | `fa2_large_absorb_100` | fa2 | +0.0151 | +0.0137 | +0.0185 | +0.0191 |
| 67 | `fa2_hiimpact_ema20` | fa2 | +0.0151 | +0.0114 | -0.0079 | -0.0228 |
| 68 | `fa1_f02_flip_exhaustion` | fa1 | +0.0150 | +0.0159 | +0.0136 | +0.0158 |
| 69 | `fa1_run_int_signed_fast` | fa1 | -0.0149 | -0.0227 | -0.0110 | -0.0138 |
| 70 | `fa1_soft_cond_grad` | fa1 | +0.0147 | +0.0169 | +0.0179 | +0.0193 |
| 71 | `fa3_max_abs_bps_ema5` | fa3 | +0.0146 | +0.0026 | +0.0134 | +0.0030 |
| 72 | `fa1_buy_sell_spread_proxy_ema20` | fa1 | +0.0145 | +0.0131 | +0.0084 | +0.0044 |
| 73 | `fa2_awsi_side_asym` | fa2 | -0.0144 | -0.0356 | -0.0065 | -0.0264 |
| 74 | `fa1_run_purity` | fa1 | -0.0143 | -0.0129 | -0.0098 | -0.0108 |

## Rejected

| signal | set | tr dIC | max \|corr\| | conflicts with |
|---|---|---:|---:|---|
| `fa2_warp_x_imb` | fa2 | +0.0421 | 0.9785 | `fa1_buy_ratio` |
| `fa1_imb_x_herf` | fa1 | +0.0400 | 0.8834 | `fa1_buy_ratio` |
| `fa3_dist_100` | fa3 | -0.0399 | 0.9462 | `fa3_dist_200` |
| `fa1_max_agg_share_signed` | fa1 | +0.0395 | 0.9163 | `fa1_buy_ratio` |
| `fa1_stale_zscore50` | fa1 | +0.0299 | 0.9717 | `fa1_stale_zscore20` |
| `fa3_dist_50` | fa3 | -0.0289 | 0.8863 | `fa3_dist_200` |
| `fa3_imb_l1_rolling_z` | fa3 | +0.0273 | 0.9695 | `fa3_d_imb_ema8` |
| `fa1_depth_imb_1` | fa1 | +0.0268 | 0.8950 | `fa3_d_imb_ema8` |
| `fa1_imb_l1` | fa1 | +0.0268 | 0.8950 | `fa3_d_imb_ema8` |
| `fa3_imb_l1` | fa3 | +0.0268 | 0.8950 | `fa3_d_imb_ema8` |
| `fa1_dimb_l1` | fa1 | +0.0268 | 0.8950 | `fa3_d_imb_ema8` |
| `fa2_ofi_tight_gate40` | fa2 | +0.0268 | 0.9303 | `fa2_ofi_spread_convex` |
| `fa2_ofi_hysteresis` | fa2 | +0.0263 | 0.9164 | `fa2_ofi_spread_convex` |
| `fa1_neg_cost_asym` | fa1 | +0.0248 | 1.0000 | `fa1_depth_cost_asym` |
| `fa1_stale_max_signed` | fa1 | +0.0238 | 0.8993 | `fa2_small_flow_only_h60` |
| `fa1_neg_imb05_ema50` | fa1 | +0.0215 | 0.9808 | `fa1_neg_imb05_ema100` |
| `fa3_dist_25` | fa3 | -0.0213 | 0.8644 | `fa3_dist_200` |
| `fa1_dimb_delta_slow` | fa1 | +0.0210 | 0.9737 | `fa1_dimb_delta_fast` |
| `fa1_stale_active_intensity` | fa1 | +0.0203 | 0.9352 | `fa1_stale_asym` |
| `fa1_neg_imb25_ema50` | fa1 | +0.0190 | 0.8824 | `fa1_neg_imb05_ema100` |
| `fa1_depth_imb_5` | fa1 | +0.0185 | 0.9309 | `fa1_cost_asym_4tick` |
| `fa2_soft_gated_rev` | fa2 | +0.0176 | 0.8688 | `fa2_fast_rev` |
| `fa3_ema_signed_walk_amount_hl64` | fa3 | -0.0162 | 0.9468 | `fa3_ema_signed_walk_amount_hl128` |
| `fa4_s58_pos1_depthimb_ema16` | fa4 | -0.0156 | 0.9696 | `fa4_s58_core_balance_ema16` |
| `fa4_s58_pos25_depthimb_ema16` | fa4 | -0.0152 | 0.9311 | `fa4_s58_core_balance_ema16` |
| `fa2_arrival_logdt_100` | fa2 | -0.0150 | 0.9963 | `fa2_arrival_logdt_200` |
