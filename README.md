# Heston Volatility Project

I started this project because I wanted to understand implied volatility beyond the constant-volatility Black-Scholes model. I had worked with option pricing and Greeks before, but I wanted to use actual option-market data and see what the volatility smile looked like in practice.

That led me to the Heston model. I used listed AAPL option data, built an implied-volatility surface, implemented Heston Monte Carlo pricing, and then tried to calibrate the model to one observed market smile. The point was not just to get a set of parameters, but to understand what the fit and the residuals say about the model.

## What I Wanted to Explore

The main question I had was:

Can the Heston stochastic-volatility model reproduce the shape of an observed equity-option implied-volatility smile, and what do the fitted parameters and residuals tell me about the model?

To get there, I worked through the full path from market option quotes to implied volatility, simulation, and calibration:

- collect and clean AAPL option-chain data;
- construct midpoint option prices;
- calculate and smooth implied volatility;
- check quotes with Black-Scholes repricing and put-call parity;
- build volatility smiles across maturities;
- use Black-Scholes prices and Greeks as a baseline;
- implement Heston Monte Carlo simulation;
- calibrate Heston parameters to a selected market smile.

## Project Flow

### 1. Market Data and Implied-Volatility Surface

I first cleaned the AAPL option chain and converted observed option prices into Black-Scholes implied volatilities. This made the strike dependence of volatility visible and gave me a common scale for comparing options across strikes and expiries.

The saved run uses 592 cleaned option observations across 10 expiries, with the AAPL spot price at 338.72. I used midpoint prices, required positive open interest, filtered extreme moneyness, and kept implied volatilities within the range used by the project.

### 2. Black-Scholes, Greeks, and Scenario Analysis

I used Black-Scholes as the baseline model. It is useful for implied-volatility inversion, quote checks, Greeks, and simple scenarios, even though a flat volatility input cannot explain the observed smile.

This step helped me separate two ideas: Black-Scholes is still a very useful diagnostic tool, but the smile itself is the reason to move to a stochastic-volatility model.

### 3. Heston Monte Carlo

I implemented the Heston model with Monte Carlo simulation:

```text
dS_t = (r - q) S_t dt + sqrt(v_t) S_t dW_t^S
dv_t = kappa(theta - v_t) dt + sigma sqrt(v_t) dW_t^v
corr(dW_t^S, dW_t^v) = rho
```

The parameters are:

- `v0`: initial variance;
- `theta`: long-run variance;
- `kappa`: speed of variance mean reversion;
- `sigma`: volatility of variance;
- `rho`: correlation between spot and variance shocks.

One check I wanted to include was the Black-Scholes limiting case. When `sigma = 0` and `v0 = theta`, the Heston simulation should collapse to Black-Scholes. In the saved validation run, the Heston Monte Carlo ATM call price differs from the analytical Black-Scholes price by 0.2012, or 0.63%.

### 4. Heston Calibration

I calibrated the five Heston parameters to a selected AAPL implied-volatility smile. The comparison is done in implied-volatility space, which makes the errors easier to read across strikes.

The part I found most interesting was seeing how the parameters affect the shape of the smile rather than just treating them as inputs to an SDE. `rho` affects skew, `sigma` affects curvature through volatility of volatility, and `v0` and `theta` help set the variance level.

## Results

The cleaned option data shows clear strike dependence in implied volatility.

![Market IV smiles](reports/figures/01_market_iv_smiles.png)

For the calibration shown here, I used the central part of the AAPL smile for the 2027-01-15 expiry. The target uses 15 strikes with moneyness from 0.89 to 1.15.

![Heston calibration fit](reports/figures/04_heston_calibration_fit.png)

The fit gets the broad volatility level reasonably close, but it smooths over the hump around the lower-middle strikes.

| Metric | Value |
| --- | ---: |
| IV RMSE | 0.0157 |
| IV MAE | 0.0134 |
| Max absolute IV residual | 0.0301 |

| Parameter | Interpretation | Calibrated value |
| --- | --- | ---: |
| `v0` | Initial variance | 0.0708 |
| `kappa` | Mean-reversion speed | 2.0000 |
| `theta` | Long-run variance | 0.0423 |
| `sigma` | Volatility of variance | 0.3000 |
| `rho` | Spot/variance correlation | -0.7000 |

What stood out to me more than the headline error number was the pattern in the residuals. They are not just random noise around zero; the model under-fits part of the lower-middle region and over-fits much of the right side.

![Calibration residuals](reports/figures/05_calibration_residuals.png)

The full run details are in `reports/run_summary.md`, with supporting metrics in `reports/canonical_run_metrics.json`.

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

I initially worked through most of the project in `00_original_exploration.ipynb`. As the analysis grew, I split the main pieces into separate notebooks for the option surface, Black-Scholes diagnostics, Heston simulation, and calibration. The later notebooks mostly follow that progression.

## Running the Project

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The main notebooks are:

1. `notebooks/01_data_and_option_surface.ipynb`
2. `notebooks/02_black_scholes_greeks_and_scenarios.ipynb`
3. `notebooks/03_heston_monte_carlo.ipynb`
4. `notebooks/04_heston_calibration.ipynb`

The saved sample data under `data/sample/` lets the later notebooks run without needing to fetch a fresh option chain first. To refresh the market data, rerun notebook `01`.

## What I Learned from the Project

The market-data part ended up being more important than I initially expected. Midpoint construction, liquidity filters, parity checks, and noisy quotes all affect the volatility surface before the Heston model even enters the picture.

The volatility smile also made the limits of constant-volatility Black-Scholes much more concrete. I still found Black-Scholes useful as a baseline and for implied-volatility inversion, but the observed smile is exactly the feature that motivated moving to a stochastic-volatility model.

The calibration step made me more cautious about interpreting fitted parameters. A low objective value on its own does not mean every parameter is well identified, especially when the calibration uses one expiry and Monte Carlo prices.

This started as a smaller options-pricing exercise and gradually became more about understanding the link between market option quotes, implied volatility, and stochastic-volatility models.

## A Few Things I Would Keep in Mind

The option data here comes from `yfinance`, which is useful for experimentation but can contain noisy or illiquid quotes.

I also only calibrate to one selected expiry here. That is enough to study how Heston changes the shape of a smile, but I would not treat all five fitted parameters as strongly identified from this run.

Monte Carlo adds simulation noise and makes the calibration relatively slow. If I continue the project, I would probably try fitting several expiries together and compare the Monte Carlo prices with the semi-closed-form Heston solution.
