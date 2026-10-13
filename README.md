# Heston Stochastic Volatility: Calibration to Equity Option Data

I started this project because I wanted to understand how stochastic-volatility models explain features of option prices that Black-Scholes cannot, especially the implied-volatility smile. I used listed AAPL option data to construct an observed volatility smile and then compared it with a Heston model calibrated using Monte Carlo pricing.

My focus was not only on getting fitted parameters. I also wanted to understand the numerical behavior of the calibration, the residual errors, and which Heston parameters can realistically be identified from one option cross-section.

## Research Question

The main question I wanted to answer was:

Can the Heston stochastic-volatility model reproduce the shape of an observed equity-option implied-volatility smile, and what can the fitted parameters and calibration residuals tell me about the underlying volatility dynamics and the limitations of the model?

To answer that, I needed to move through the full chain from option quotes to model residuals: cleaning market data, converting prices into implied volatilities, using Black-Scholes as a diagnostic benchmark, implementing Heston Monte Carlo pricing, and calibrating the model to a market smile.

## Data

| Item | Value |
| --- | --- |
| Underlying | AAPL |
| Source | Yahoo Finance via `yfinance` |
| Snapshot saved | 2026-10-08 21:43 IST |
| Spot used | 338.72 |
| Clean observations | 592 |
| Expiries retained | 10 |
| Expiry range | 2026-10-23 to 2027-04-16 |
| Calibration expiry | 2027-01-15 |
| Calibration moneyness range | 0.89 to 1.15 |

The option chain needed cleaning before the implied-volatility surface could be analyzed meaningfully. I used midpoint prices, required positive open interest, filtered extreme moneyness, and kept implied volatilities within the range already used by the project.

## Methodology

### 1. Market Data and Implied Volatility

I first cleaned the option chain and converted observed option prices into Black-Scholes implied volatilities. This gives a common scale for comparing options across strikes and makes the volatility smile directly visible.

The cleaned data still reflects real market imperfections: missing or unusable quotes, liquidity differences, and noisy implied-volatility estimates. I smooth the smiles by expiry and combine them into an implied-volatility surface over moneyness and maturity.

![Market IV smiles](reports/figures/01_market_iv_smiles.png)

### 2. Black-Scholes Diagnostics

I use Black-Scholes as the baseline model, not as the final explanation of the smile. It is useful for implied-volatility inversion, quote checks, Greeks, and simple scenario analysis.

The observed strike dependence of implied volatility is exactly why I moved beyond a flat-volatility model. Black-Scholes gives the diagnostic language; Heston is the stochastic-volatility model I then test against the observed smile.

### 3. Heston Monte Carlo

I implemented the Heston stochastic-volatility model using Monte Carlo simulation:

```text
dS_t = (r - q) S_t dt + sqrt(v_t) S_t dW_t^S
dv_t = kappa(theta - v_t) dt + sigma sqrt(v_t) dW_t^v
corr(dW_t^S, dW_t^v) = rho
```

The parameters are:

- `v0`: initial variance
- `theta`: long-run variance
- `kappa`: speed of variance mean reversion
- `sigma`: volatility of variance
- `rho`: correlation between spot and variance shocks

I used Monte Carlo because it makes the stochastic dynamics explicit and gives a direct numerical implementation of the model. It is not the most efficient method for repeated Heston calibration, which is one reason I treat the calibration as an exploratory numerical experiment rather than a production implementation.

One validation step was checking the Black-Scholes limiting case. When `sigma = 0` and `v0 = theta`, the Heston model should collapse to Black-Scholes. In the saved validation run, the Heston Monte Carlo ATM call price differs from the analytical Black-Scholes price by 0.2012, or 0.63%.

![Black-Scholes limiting-case validation](reports/figures/03_heston_bs_validation.png)

### 4. Heston Calibration

I calibrate the five Heston parameters to a selected AAPL implied-volatility smile. The comparison is made in implied-volatility space, and the objective is the mean squared error between model-implied and market-implied volatilities.

The calibration is intentionally limited: it uses one maturity and a moderate Monte Carlo setup. That makes the fitted residuals and weakly identified parameters part of the result rather than something to hide.

## Results

For the canonical run, I calibrated the model to the central part of the AAPL smile for the 2027-01-15 expiry. The target uses 15 strikes with moneyness from 0.89 to 1.15.

![Heston calibration fit](reports/figures/04_heston_calibration_fit.png)

| Item | Value |
| --- | ---: |
| Spot used | 338.72 |
| Target expiry | 2027-01-15 |
| Time to maturity | 0.2692 years |
| Number of target strikes | 15 |
| IV RMSE | 0.0157 |
| IV MAE | 0.0134 |
| Max absolute IV residual | 0.0301 |

| Parameter | Fitted value |
| --- | ---: |
| `v0` | 0.0708 |
| `kappa` | 2.0000 |
| `theta` | 0.0423 |
| `sigma` | 0.3000 |
| `rho` | -0.7000 |

I found that the fitted model matches the broad volatility level of the selected smile, but it smooths over a local hump around the lower-middle strikes. The largest residual is near the 321 strike, and the residual pattern is easier to see directly:

![Calibration residuals](reports/figures/05_calibration_residuals.png)

The fitted `v0` is above `theta`, which suggests that the selected smile reflects near-term variance above the model's long-run variance level. The negative `rho` is consistent with the usual equity leverage effect, where downside spot moves are associated with higher variance and a left-skewed smile. Since this is a single-smile calibration, I would not over-interpret every parameter individually, but the fit is useful for understanding how the model responds to the observed smile.

The full run record is saved in `reports/run_summary.md`, and the supporting metrics are saved in `reports/canonical_run_metrics.json`.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── notebooks/
│   ├── 00_original_exploration.ipynb
│   ├── 01_data_and_option_surface.ipynb
│   ├── 02_black_scholes_greeks_and_scenarios.ipynb
│   ├── 03_heston_monte_carlo.ipynb
│   └── 04_heston_calibration.ipynb
├── src/
│   ├── data.py
│   ├── black_scholes.py
│   ├── validation.py
│   ├── heston.py
│   ├── calibration.py
│   └── plotting.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
├── reports/
│   ├── figures/
│   ├── calibration_residuals.csv
│   ├── canonical_run_metrics.json
│   └── run_summary.md
└── tests/
    ├── test_black_scholes.py
    └── test_heston.py
```

`notebooks/00_original_exploration.ipynb` is the earlier exploratory version of the work. The cleaner reviewer path is notebooks `01` through `04`, which separate the workflow into data preparation, Black-Scholes diagnostics, Heston simulation, and calibration.

## Running the Project

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Recommended notebook order:

1. `notebooks/01_data_and_option_surface.ipynb`
2. `notebooks/02_black_scholes_greeks_and_scenarios.ipynb`
3. `notebooks/03_heston_monte_carlo.ipynb`
4. `notebooks/04_heston_calibration.ipynb`

The saved sample data under `data/sample/` lets the later notebooks run without needing to fetch a fresh option chain first. To refresh the market data, rerun notebook `01`.

## What I Learned from the Project

Market data needs more cleaning than the theory usually suggests. Midpoint construction, liquidity filters, parity checks, and noisy quotes all matter before the model calibration step even begins.

The volatility smile makes the limitation of constant-volatility Black-Scholes much more concrete. Black-Scholes is still useful as a baseline and diagnostic tool, but the smile itself is evidence that one volatility input is not enough to describe the market.

Calibration is not just about finding an optimizer minimum. I found that residuals, parameter interpretation, simulation noise, and the selected calibration region all affect how much meaning I should attach to the final parameter values.

## Limitations

- The data comes from `yfinance`, which is useful for this project but not institutional-quality options data.
- The current calibration focuses on a single implied-volatility smile rather than jointly fitting the full surface.
- Monte Carlo calibration introduces simulation noise and is slower than semi-closed-form Heston pricing.

## Possible Extensions

- Calibrate across multiple expiries instead of a single smile.
- Compare the Monte Carlo pricer with the semi-closed-form Heston solution.
- Test parameter stability across different market dates.

## Final Note

This started as a smaller options-pricing exercise and became a deeper project as I got more interested in volatility modelling. My main goal was to understand the full path from market option quotes to implied volatility, stochastic-volatility simulation, and calibration, rather than only using a pre-built pricing library.
