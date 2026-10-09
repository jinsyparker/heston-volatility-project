# Canonical Run Summary

## Market Snapshot

- Underlying: AAPL
- Data source: Yahoo Finance via `yfinance`
- Saved-data timestamp: 2026-10-08 21:43 IST
- Spot used: 338.72
- Cleaned observations: 592
- Expiries retained: 10
- Expiry range: 2026-10-23 to 2027-04-16
- Quote filter: positive midpoint, positive open interest, IV between 1% and 250%, moneyness between 0.70 and 1.30

## Quote Validation

- Black-Scholes repricing check, zero-rate baseline:
  - Mean absolute price error: 0.2786
  - Median absolute price error: 0.1053
  - Share with absolute price error above 1.00: 7.26%
- Put-call parity diagnostics:
  - Matched call/put pairs: 256
  - Zero-rate median parity residual: 1.0300
  - Expiry-level inferred-rate median parity residual: 0.0572

The parity-implied rate/dividend inputs reduce the median parity residual, but some inferred rates and dividend yields are noisy. They are suitable for a compact project diagnostic, not for production valuation.

## Heston Calibration

- Target expiry: 2027-01-15
- Time to maturity: 0.2692 years
- Target strikes: 15
- Target moneyness: 0.89 to 1.15
- Calibration rate: -0.0094
- Calibration dividend yield: -0.0361
- Paths / steps / seed: 6,000 paths, 60 steps, seed 42
- Device: CPU
- Optimizer status: converged, `CONVERGENCE: REL_REDUCTION_OF_F_<=_FACTR*EPSMCH`
- Objective: 0.00028786
- IV RMSE: 0.0157
- IV MAE: 0.0134
- Maximum absolute IV residual: 0.0301

## Fitted Parameters

| Parameter | Estimate | Interpretation |
| --- | ---: | --- |
| v0 | 0.0708 | Initial variance level |
| kappa | 2.0000 | Variance mean-reversion speed |
| theta | 0.0423 | Long-run variance |
| sigma | 0.3000 | Volatility of variance |
| rho | -0.7000 | Spot/variance correlation |

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

## Main Finding

The central 2027-01-15 AAPL smile is fit with an IV RMSE of 1.57 volatility points. The fitted v0 is above theta, indicating that the selected smile embeds elevated near-term variance relative to the long-run variance level. The residuals are largest around the 321 strike, and the model smooths over a local hump in the target smile, so the single-expiry calibration should be read as a compact Heston demonstration rather than a fully identified surface model.

## Figures

- [Market IV smiles](figures/01_market_iv_smiles.png)
- [Smoothed IV surface](figures/02_iv_surface.png)
- [Black-Scholes limiting-case validation](figures/03_heston_bs_validation.png)
- [Heston calibration fit](figures/04_heston_calibration_fit.png)
- [Calibration residuals](figures/05_calibration_residuals.png)

## Supporting Files

- `data/sample/AAPL_canonical_surface_checked.csv`
- `data/sample/AAPL_canonical_iv_fit.csv`
- `reports/calibration_residuals.csv`
- `reports/canonical_run_metrics.json`
