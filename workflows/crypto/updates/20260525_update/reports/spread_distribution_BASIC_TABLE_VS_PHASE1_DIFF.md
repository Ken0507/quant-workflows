# basic_table vs phase1 snapshot diff
- Tolerance: |diff| < 1e-09
- spread_raw compared as basic_table[spread_raw] vs 2 * phase1[half_spread_raw]
- spread_bps compared as basic_table[spread_bps] vs 2 * phase1[half_spread_bps]
- basic_table rows with bid1<=0 (OB-not-yet-valid) excluded; phase1 NaN rows excluded
- Primary pass/fail uses CLEAN view: phase1 rows with ask1<=bid1 (stale crossed-book, a known phase1 L2 replay bug) are excluded.
- Strict view = over the full join (including phase1 crossed-book rows); shown below as secondary diagnostic info.

## Row-count bookkeeping

Basis chain: basic_raw -> (drop bid1<=0) -> basic_kept; phase1_raw -> (drop NaN) -> phase1_kept; inner join on bar_id -> joined; drop phase1 crossed-book -> clean (the denominator for diff pass/fail).

| sym | ds | n_basic_raw | n_basic_quote_zero | n_basic_kept | n_phase1_raw | n_phase1_nan_dropped | n_phase1_kept | n_basic_only | n_phase1_only | n_joined | n_phase1_crossed | n_clean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2025-07-15 | 32681 | 0 | 32681 | 32681 | 0 | 32681 | 0 | 0 | 32681 | 594 | 32087 |
| BTCUSDT | 2025-11-15 | 11892 | 0 | 11892 | 11892 | 0 | 11892 | 0 | 0 | 11892 | 0 | 11892 |
| BTCUSDT | 2026-01-15 | 19439 | 0 | 19439 | 19439 | 0 | 19439 | 0 | 0 | 19439 | 10 | 19429 |
| ETHUSDT | 2025-07-15 | 35671 | 0 | 35671 | 35671 | 0 | 35671 | 0 | 0 | 35671 | 0 | 35671 |
| ETHUSDT | 2025-11-15 | 8680 | 0 | 8680 | 8680 | 0 | 8680 | 0 | 0 | 8680 | 1 | 8679 |
| ETHUSDT | 2026-01-15 | 20157 | 0 | 20157 | 20157 | 0 | 20157 | 0 | 0 | 20157 | 0 | 20157 |
| SOLUSDT | 2025-07-15 | 21959 | 0 | 21959 | 21959 | 0 | 21959 | 0 | 0 | 21959 | 0 | 21959 |
| SOLUSDT | 2025-11-15 | 7989 | 0 | 7989 | 7989 | 0 | 7989 | 0 | 0 | 7989 | 1 | 7988 |
| SOLUSDT | 2026-01-15 | 16587 | 0 | 16587 | 16587 | 0 | 16587 | 0 | 0 | 16587 | 54 | 16533 |
| BNBUSDT | 2025-07-15 | 17146 | 0 | 17146 | 17146 | 0 | 17146 | 0 | 0 | 17146 | 0 | 17146 |
| BNBUSDT | 2025-11-15 | 6851 | 0 | 6851 | 6851 | 0 | 6851 | 0 | 0 | 6851 | 458 | 6393 |
| BNBUSDT | 2026-01-15 | 10719 | 0 | 10719 | 10719 | 0 | 10719 | 0 | 0 | 10719 | 0 | 10719 |
| XRPUSDT | 2025-07-15 | 45154 | 0 | 45154 | 45154 | 0 | 45154 | 0 | 0 | 45154 | 0 | 45154 |
| XRPUSDT | 2025-11-15 | 10121 | 0 | 10121 | 10121 | 0 | 10121 | 0 | 0 | 10121 | 1 | 10120 |
| XRPUSDT | 2026-01-15 | 14978 | 0 | 14978 | 14978 | 0 | 14978 | 0 | 0 | 14978 | 25 | 14953 |
| DOGEUSDT | 2025-07-15 | 27370 | 0 | 27370 | 27370 | 0 | 27370 | 0 | 0 | 27370 | 0 | 27370 |
| DOGEUSDT | 2025-11-15 | 6508 | 0 | 6508 | 6508 | 0 | 6508 | 0 | 0 | 6508 | 1 | 6507 |
| DOGEUSDT | 2026-01-15 | 13588 | 0 | 13588 | 13588 | 0 | 13588 | 0 | 0 | 13588 | 0 | 13588 |
| ADAUSDT | 2025-07-15 | 26464 | 0 | 26464 | 26464 | 0 | 26464 | 0 | 0 | 26464 | 35 | 26429 |
| ADAUSDT | 2025-11-15 | 6543 | 1 | 6542 | 6543 | 0 | 6543 | 0 | 1 | 6542 | 0 | 6542 |
| ADAUSDT | 2026-01-15 | 14351 | 0 | 14351 | 14351 | 0 | 14351 | 0 | 0 | 14351 | 0 | 14351 |

## Pass/Fail matrix (clean view — PRIMARY)

Denominator = n_clean (joined rows with phase1 crossed-book excluded).
Fail = any row in the clean view with |diff| > tol.

| sym | ds | n_clean | n_crossed | mid | spread_raw | spread_bps | n_fail_clean (mid/sr/sb) | n_fail_strict (mid/sr/sb) | mid_max_clean | sr_max_clean | sb_max_clean | error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2025-07-15 | 32087 | 594 | FAIL | FAIL | FAIL | 3/3/3 | 597/597/597 | 5.000e-02 | 1.000e-01 | 8.573e-03 |  |
| BTCUSDT | 2025-11-15 | 11892 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| BTCUSDT | 2026-01-15 | 19429 | 10 | PASS | PASS | PASS | 0/0/0 | 10/10/10 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| ETHUSDT | 2025-07-15 | 35671 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| ETHUSDT | 2025-11-15 | 8679 | 1 | PASS | PASS | PASS | 0/0/0 | 1/1/1 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| ETHUSDT | 2026-01-15 | 20157 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| SOLUSDT | 2025-07-15 | 21959 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| SOLUSDT | 2025-11-15 | 7988 | 1 | PASS | PASS | PASS | 0/0/0 | 1/1/1 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| SOLUSDT | 2026-01-15 | 16533 | 54 | PASS | PASS | PASS | 0/0/0 | 54/54/54 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| BNBUSDT | 2025-07-15 | 17146 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| BNBUSDT | 2025-11-15 | 6393 | 458 | PASS | PASS | PASS | 0/0/0 | 458/458/458 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| BNBUSDT | 2026-01-15 | 10719 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| XRPUSDT | 2025-07-15 | 45154 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| XRPUSDT | 2025-11-15 | 10120 | 1 | PASS | PASS | PASS | 0/0/0 | 1/1/1 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| XRPUSDT | 2026-01-15 | 14953 | 25 | PASS | PASS | PASS | 0/0/0 | 25/25/25 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| DOGEUSDT | 2025-07-15 | 27370 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| DOGEUSDT | 2025-11-15 | 6507 | 1 | PASS | PASS | PASS | 0/0/0 | 1/1/1 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| DOGEUSDT | 2026-01-15 | 13588 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| ADAUSDT | 2025-07-15 | 26429 | 35 | PASS | PASS | PASS | 0/0/0 | 35/35/35 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| ADAUSDT | 2025-11-15 | 6542 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |
| ADAUSDT | 2026-01-15 | 14351 | 0 | PASS | PASS | PASS | 0/0/0 | 0/0/0 | 0.000e+00 | 0.000e+00 | 0.000e+00 |  |

## Pass/Fail matrix (strict view — secondary, includes phase1 crossed-book)

Fail = any row in the full join (n_joined) with |diff| > tol, including phase1 crossed-book rows.
These failures are expected whenever n_phase1_crossed > 0 — phase1's crossed-book rows carry bogus prices and are not bugs on the basic_table side.

| sym | ds | n_joined | mid | spread_raw | spread_bps | mid_max_strict | sr_max_strict | sb_max_strict |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2025-07-15 | 32681 | FAIL | FAIL | FAIL | 2.216e+02 | 4.432e+02 | 3.788e+01 |
| BTCUSDT | 2025-11-15 | 11892 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| BTCUSDT | 2026-01-15 | 19439 | FAIL | FAIL | FAIL | 1.300e+01 | 2.600e+01 | 2.693e+00 |
| ETHUSDT | 2025-07-15 | 35671 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ETHUSDT | 2025-11-15 | 8680 | FAIL | FAIL | FAIL | 2.250e-01 | 4.500e-01 | 1.418e+00 |
| ETHUSDT | 2026-01-15 | 20157 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| SOLUSDT | 2025-07-15 | 21959 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| SOLUSDT | 2025-11-15 | 7989 | FAIL | FAIL | FAIL | 1.500e-02 | 3.000e-02 | 2.108e+00 |
| SOLUSDT | 2026-01-15 | 16587 | FAIL | FAIL | FAIL | 7.000e-02 | 1.400e-01 | 9.661e+00 |
| BNBUSDT | 2025-07-15 | 17146 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| BNBUSDT | 2025-11-15 | 6851 | FAIL | FAIL | FAIL | 2.900e+00 | 5.800e+00 | 6.212e+01 |
| BNBUSDT | 2026-01-15 | 10719 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| XRPUSDT | 2025-07-15 | 45154 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| XRPUSDT | 2025-11-15 | 10121 | FAIL | FAIL | FAIL | 5.000e-05 | 1.000e-04 | 4.378e-01 |
| XRPUSDT | 2026-01-15 | 14978 | FAIL | FAIL | FAIL | 1.100e-03 | 2.200e-03 | 1.041e+01 |
| DOGEUSDT | 2025-07-15 | 27370 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| DOGEUSDT | 2025-11-15 | 6508 | FAIL | FAIL | FAIL | 2.000e-05 | 4.000e-05 | 2.475e+00 |
| DOGEUSDT | 2026-01-15 | 13588 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ADAUSDT | 2025-07-15 | 26464 | FAIL | FAIL | FAIL | 7.000e-04 | 1.400e-03 | 1.907e+01 |
| ADAUSDT | 2025-11-15 | 6542 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ADAUSDT | 2026-01-15 | 14351 | PASS | PASS | PASS | 0.000e+00 | 0.000e+00 | 0.000e+00 |

## Failing-row examples (clean view, first 10 per combo)

### BTCUSDT 2025-07-15

| bar_id | mid (bt) | mid (ph) | mid_diff | spread_raw (bt) | 2*hsr (ph) | sr_diff | spread_bps (bt) | 2*hsb (ph) | sb_diff |
|---|---|---|---|---|---|---|---|---|---|
| 21330 | 116639 | 116639.05 | 5.000e-02 | 0.2 | 0.1 | 1.000e-01 | 0.01714692341 | 0.008573458032 | 8.573e-03 |
| 21331 | 116639 | 116639.05 | 5.000e-02 | 0.2 | 0.1 | 1.000e-01 | 0.01714692341 | 0.008573458032 | 8.573e-03 |
| 21332 | 116639 | 116639.05 | 5.000e-02 | 0.2 | 0.1 | 1.000e-01 | 0.01714692341 | 0.008573458032 | 8.573e-03 |

## Summary

- Combos: 21
- Clean all-three-pass (PRIMARY): 20 / 21
- Strict all-three-pass (secondary, incl phase1 crossed-book): 11 / 21
- Clean overall: HAS FAILURES
- Strict overall: HAS FAILURES
