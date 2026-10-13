# Heston Calibration Run

This is the saved run behind the figures and numbers in the README.

## Setup

- Underlying: AAPL
- Source: Yahoo Finance via `yfinance`
- Snapshot saved: 2026-10-08 21:43 IST
- Spot used: 338.72
- Clean observations: 592
- Expiries retained: 10
- Expiry range: 2026-10-23 to 2027-04-16
- Quote filter: positive midpoint, positive open interest, IV between 1% and 250%, moneyness between 0.70 and 1.30

## Quote Checks

- Matched call/put pairs: 256
- Black-Scholes repricing median absolute price error, zero-rate baseline: 0.1053
- Black-Scholes repricing mean absolute price error, zero-rate baseline: 0.2786
- Zero-rate median parity residual: 1.0300
- Expiry-level inferred-rate median parity residual: 0.0572

The parity adjustment reduces the median residual, but the inferred rates and dividend yields are still noisy. I treat them as useful inputs for this experiment, not as a clean market curve.

## Calibration Setup

- Expiry: 2027-01-15
- Time to maturity: 0.2692 years
- Number of strikes: 15
- Strike range: 302.18 to 387.90
- Moneyness range: 0.89 to 1.15
- Calibration rate: -0.0094
- Calibration dividend yield: -0.0361
- Pricing method: Heston Monte Carlo
- Device: CPU
- Calibration paths: 6,000
- Calibration time steps: 60
- Random seed: 42
- Objective: mean squared error in implied-volatility space
- Optimizer status: `CONVERGENCE: REL_REDUCTION_OF_F_<=_FACTR*EPSMCH`

## Results

| Metric | Value |
| --- | ---: |
| Objective | 0.00028786 |
| IV RMSE | 0.0157 |
| IV MAE | 0.0134 |
| Maximum absolute IV residual | 0.0301 |

| Parameter | Value |
| --- | ---: |
| v0 | 0.0708 |
| kappa | 2.0000 |
| theta | 0.0423 |
| sigma | 0.3000 |
| rho | -0.7000 |

## Black-Scholes Limit Check

- Test: Heston Black-Scholes limiting case with sigma = 0 and v0 = theta
- Strike: ATM, K = 338.72
- Maturity: 1.0 year
- Volatility: 20.00%
- Paths / steps / seed: 20,000 paths, 128 steps, seed 7
- Analytical Black-Scholes price: 31.7100
- Heston Monte Carlo price: 31.5088
- Absolute error: 0.2012
- Relative error: 0.63%

## Notes

The fit gets the broad smile level reasonably close, but it misses some local curvature around the lower-middle strikes.

The residual errors are structured across strikes rather than evenly scattered around zero. The largest absolute residual is near the 321 strike.

`kappa`, `sigma`, and `rho` did not move much from their starting values in this run. I would want to use more than one expiry before interpreting those parameters too strongly.

The fitted `v0` is above `theta`, which is consistent with the fitted model assigning higher near-term variance than long-run variance. I would still read this cautiously because the target is one selected expiry.

If I continue this experiment, I would probably fit several expiries together and compare the Monte Carlo prices with the semi-closed-form Heston solution.

## Files

- [Market IV smiles](figures/01_market_iv_smiles.png)
- [Smoothed IV surface](figures/02_iv_surface.png)
- [Heston calibration fit](figures/04_heston_calibration_fit.png)
- [Calibration residuals](figures/05_calibration_residuals.png)
- `reports/calibration_residuals.csv`
- `reports/canonical_run_metrics.json`
- `data/sample/AAPL_canonical_surface_checked.csv`
- `data/sample/AAPL_canonical_iv_fit.csv`
