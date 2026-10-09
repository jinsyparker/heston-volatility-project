# Heston Volatility Project

I started this project because I wanted to understand implied volatility beyond the constant-volatility Black-Scholes framework. I had worked with option pricing, Greeks, and implied-volatility inversion before, but I wanted to take the next step: use actual option-market data, build a volatility surface, and see how far a stochastic-volatility model could go in reproducing a market smile.

I use AAPL option data for the main example because the option chain is liquid enough to make the cleaning and calibration steps meaningful. As I worked through it, the exercise gradually became a full workflow: collect and clean option quotes, validate the data, construct implied-volatility smiles and surfaces, implement Heston Monte Carlo pricing, and calibrate the model to an observed smile.

The part I found most interesting was moving from "pricing an option" to asking what the shape of the volatility smile is telling me. Heston gives a way to connect that shape to variance dynamics, volatility of volatility, and the relationship between spot moves and variance.

## What I Wanted to Explore

The main question I wanted to answer was:

Can the Heston stochastic-volatility model reproduce the shape of an observed equity-option implied-volatility smile, and what do the calibrated parameters tell me about the underlying volatility dynamics?

To get there, I worked through several smaller pieces:

- collecting and cleaning AAPL option-chain data
- constructing midpoint option prices
- calculating and smoothing implied volatility
- checking quotes with Black-Scholes repricing and put-call parity
- building volatility smiles and a volatility surface
- using Black-Scholes prices and Greeks as a baseline
- implementing Heston Monte Carlo simulation
- validating the Heston engine in the Black-Scholes limiting case
- calibrating Heston parameters to a market implied-volatility smile

## Project Flow

### 1. Market Data and Implied-Volatility Surface

In `notebooks/01_data_and_option_surface.ipynb`, I download the AAPL option chain, construct midpoint prices, filter unusable quotes, and run basic validation checks. I then smooth implied volatility by expiry and combine the fitted smiles into a surface over moneyness and maturity.

The canonical run saved in this repository uses 592 cleaned option observations across 10 expiries, from 2026-10-23 to 2027-04-16.

![Market IV smiles](reports/figures/01_market_iv_smiles.png)

### 2. Black-Scholes, Greeks, and Scenario Analysis

In `notebooks/02_black_scholes_greeks_and_scenarios.ipynb`, I use Black-Scholes as the baseline model. I calculate prices and Greeks, then look at simple spot, volatility, and time scenarios.

I wanted this step in the project because Black-Scholes is still the natural reference point. It gives a clean way to invert option prices into implied volatility, check quotes, and understand how option values respond to basic inputs before moving to stochastic volatility.

### 3. Heston Monte Carlo

In `notebooks/03_heston_monte_carlo.ipynb`, I implement the Heston stochastic-volatility model using Monte Carlo simulation.

```text
dS_t = (r - q) S_t dt + sqrt(v_t) S_t dW_t^S
dv_t = kappa(theta - v_t) dt + sigma sqrt(v_t) dW_t^v
corr(dW_t^S, dW_t^v) = rho
```

The parameters have the following roles:

- `v0`: initial variance
- `kappa`: speed of variance mean reversion
- `theta`: long-run variance
- `sigma`: volatility of variance
- `rho`: correlation between spot and variance shocks

One thing I wanted to check was whether the simulation behaves correctly in a known limiting case. When `sigma = 0` and `v0 = theta`, the Heston model should collapse to Black-Scholes. In the saved validation run, the Heston Monte Carlo ATM call price differs from the analytical Black-Scholes price by 0.2012, or 0.63%.

![Black-Scholes limiting-case validation](reports/figures/03_heston_bs_validation.png)

### 4. Heston Calibration

In `notebooks/04_heston_calibration.ipynb`, I calibrate the five Heston parameters to a selected AAPL implied-volatility smile. I compare the model and market in implied-volatility space, because that makes the calibration error easier to interpret across strikes.

The part I found most interesting here was seeing how the Heston parameters affect the shape of the smile rather than just treating them as numbers inside an SDE. In particular, `rho` affects skew, `sigma` affects curvature through volatility of volatility, and `v0` and `theta` help set the variance level.

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
