# Mid-Label LGBM Backtest — 3 thresholds × 7 symbols (long-only, taker)

Generated: 2026-04-19

## Setup

- **Model**: `/data/db/crypto/analyzer/fa4/fa4_merged_sota100_midlabel_report/lgbm_model.txt`
  (155 features: `f_ret_1` + 59 fa1 + 41 fa2 + 54 fa4, SOTA FI top-100)
- **Label source**: mid-to-mid `log(mid[t]/mid[t-1])` forward-summed to 100-bar horizon
- **Date range**: 2025-07-01 .. 2026-01-26 (168 train + 42 valid = 210 days)
- **Strategy params** (identical to close SOTA `run_bt_fi_top100_longonly`):
  long-only, taker entry, maker exit (5s replace, 15s market timeout);
  notional 1 000 USDT; latency 50 ms; hysteresis 3.0 bps
- **Thresholds** from mid-train signal quantiles (25.2 M samples):

  | Quantile | OPEN/MARKET bps |
  |---|---:|
  | q99.7 | 6.0899 |
  | q99.9 | 9.2631 |
  | q99.95 | 11.4495 |

## Headline comparison — Valid Net Rate (bps)

| Quantile | close-label SOTA | mid-label | Δ |
|---|---:|---:|---:|
| q99.7 | **−1.64** | **−0.60** | +1.04 |
| q99.9 | **−2.91** | **+0.67** | +3.58 |
| q99.95 | **−2.44** | **+2.50** | +4.94 |

Mid-label flips q99.9 and q99.95 valid from negative to positive.

## Detailed train/valid split

### Mid-label

| Threshold | Set | Net PnL | Gross bps | Fee bps | Net bps | Sharpe | MaxDD | RTs | Win days |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| q99.7 | Train | −2,008 | +0.21 | +0.74 | **−0.52** | −2.51 | −2,102 | 53,472 | 66/168 (39%) |
| q99.7 | Valid | −244 | +0.14 | +0.74 | **−0.60** | −7.30 | −249 | 6,162 | 9/42 (21%) |
| q99.9 | Train | +197 | +0.89 | +0.73 | **+0.16** | 0.62 | −504 | 17,295 | 87/139 (63%) |
| q99.9 | Valid | +64 | +1.41 | +0.73 | **+0.67** | 4.84 | −19 | 1,316 | 19/33 (58%) |
| q99.95 | Train | +409 | +1.34 | +0.73 | **+0.61** | 2.50 | −272 | 9,924 | 61/89 (69%) |
| q99.95 | Valid | +109 | +3.23 | +0.72 | **+2.50** | 7.39 | −19 | 550 | 13/20 (65%) |

### Close-label SOTA (reference)

| Threshold | Set | Net PnL | Net bps | Sharpe | RTs | Win days |
|---|---|---:|---:|---:|---:|---:|
| q99.7 (OPEN=4.89) | Train | +594 | +0.71 | 2.33 | 12,899 | 108/166 (65%) |
| q99.7 | Valid | −211 | **−1.64** | −4.25 | 2,395 | 18/41 (44%) |
| q99.9 | Train | +767 | +2.69 | 4.51 | 4,466 | 97/134 (72%) |
| q99.9 | Valid | −125 | **−2.91** | −3.32 | 790 | 18/34 (53%) |
| q99.95 | Train | +884 | +5.54 | 5.98 | 2,462 | 80/116 (69%) |
| q99.95 | Valid | −59 | **−2.44** | −2.05 | 463 | 20/32 (62%) |

## Output locations

- `/home/cken/crypto_world/zebra/bt_output/fi_top100_midlabel_longonly_taker_q997/`
- `/home/cken/crypto_world/zebra/bt_output/fi_top100_midlabel_longonly_taker_q999/`
- `/home/cken/crypto_world/zebra/bt_output/fi_top100_midlabel_longonly_taker_q9995/`
- Each contains `report.md` + `dashboard.png` + trade/entrust/stats parquets.

## Observations

1. **Mid-label alpha is real at high quantiles.** q99.9 valid +0.67 bps / q99.95 valid +2.50 bps
   flip the sign vs close-label baseline (both negative). Sharpe 4.84 / 7.39 on valid.
2. **Mid-label trades 3–4× more roundtrips** at the same quantile (53k vs 13k at q99.7).
   Its score distribution has a fatter tail than close-label's.
3. **q99.7 still unprofitable** for both, but mid-label is only half as bad on valid
   (−0.60 vs −1.64 bps). Need higher quantile to clear the 0.73 bps taker fee hurdle.
4. **Win-day rate improvement:** mid-label valid win% is 58–65% at q99.9+ vs close 44–62%.
