# Calibration Run — 2026-10-08

This is the fixed run record for the calibration results shown in the README.

## Data

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

The parity adjustment reduces the median residual, but the inferred rates and dividend yields are still noisy. I treat them as a useful diagnostic input rather than a clean market curve.

## Calibration Target

- Expiry: 2027-01-15
- Time to maturity: 0.2692 years
- Number of strikes: 15
- Strike range: 302.18 to 387.90
- Moneyness range: 0.89 to 1.15
- Calibration rate: -0.0094
- Calibration dividend yield: -0.0361

## Numerical Setup

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

## Monte Carlo Validation

- Test: Heston Black-Scholes limiting case with sigma = 0 and v0 = theta
- Strike: ATM, K = 338.72
- Maturity: 1.0 year
- Volatility: 20.00%
- Paths / steps / seed: 20,000 paths, 128 steps, seed 7
- Analytical Black-Scholes price: 31.7100
- Heston Monte Carlo price: 31.5088
- Absolute error: 0.2012
- Relative error: 0.63%

## Observations

The model captures the broad level of the selected smile, but it misses some local curvature around the lower-middle strikes.

Residual errors are structured rather than uniformly distributed across strikes. The largest absolute residual is near the 321 strike.

Several parameters changed little from their starting values. I would not interpret `kappa`, `sigma`, or `rho` strongly from this single-expiry calibration.

The fitted `v0` is above `theta`, which is consistent with the fitted model assigning higher near-term variance than long-run variance. This should be treated cautiously because the calibration target is limited.

## Figures and Supporting Files

- [Market IV smiles](figures/01_market_iv_smiles.png)
- [Smoothed IV surface](figures/02_iv_surface.png)
- [Heston calibration fit](figures/04_heston_calibration_fit.png)
- [Calibration residuals](figures/05_calibration_residuals.png)
- `reports/calibration_residuals.csv`
- `reports/canonical_run_metrics.json`
- `data/sample/AAPL_canonical_surface_checked.csv`
- `data/sample/AAPL_canonical_iv_fit.csv`

## Follow-up Experiment

Natural next experiments:

- Calibrate several maturities jointly instead of fitting one smile.
- Compare the Monte Carlo results with a faster characteristic-function or Fourier-based Heston pricer.
- Repeat the calibration across multiple market dates to check parameter stability.
