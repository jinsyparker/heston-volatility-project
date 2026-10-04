# Heston Volatility Project

This project builds an end-to-end options analytics workflow around market implied volatility and Heston stochastic-volatility calibration. It started as an exploratory notebook and has been organized into reusable Python modules, explanatory notebooks, tests, and report outputs.

## Project Question

Can a stochastic-volatility model reproduce the shape of an observed equity option implied-volatility smile, and how do the fitted parameters connect to option risk?

The project uses Apple (`AAPL`) options by default, but the data pipeline can be pointed at any ticker supported by `yfinance`.

## What It Covers

- Option-chain collection and cleaning
- Bid/ask midpoint construction and liquidity filtering
- Black-Scholes pricing, Greeks, and implied-volatility inversion
- Put-call parity checks and expiry-level rate/dividend inference
- Implied-volatility smile and surface fitting
- Spot, volatility, and time scenario analysis
- GPU-enabled Heston Monte Carlo simulation
- Monte Carlo validation against the Black-Scholes limit
- Heston calibration to a market implied-volatility smile

## Repository Layout

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
│   └── processed/
├── reports/
│   ├── figures/
│   └── run_summary.md
└── tests/
    ├── test_black_scholes.py
    └── test_heston.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For GPU acceleration, install a PyTorch build compatible with your CUDA version. The notebooks also run on CPU with smaller path counts.

## Recommended Notebook Order

1. `notebooks/01_data_and_option_surface.ipynb`
2. `notebooks/02_black_scholes_greeks_and_scenarios.ipynb`
3. `notebooks/03_heston_monte_carlo.ipynb`
4. `notebooks/04_heston_calibration.ipynb`

The first notebook writes a cleaned options dataset to `data/processed/`. Later notebooks reuse that saved dataset where possible.

## Why This Is Relevant For Financial Engineering

The project demonstrates core topics expected in a financial engineering setting: derivative pricing, volatility surfaces, numerical simulation, model validation, stochastic volatility, calibration, and risk sensitivities. The most academically important part is the path from observed option quotes to a calibrated Heston model; the trade screener and scenario analysis are useful applied extensions.

## Current Limitations

- `yfinance` quotes are convenient but not institutional-quality market data.
- Calibration is set up as a compact single-smile demonstration by default.
- Monte Carlo calibration is noisy and slower than characteristic-function methods.
- Dividend and rate estimates inferred from parity can be noisy when quotes are illiquid.

## Natural Extensions

- Calibrate across multiple expiries with weighted IV error.
- Add confidence intervals for Monte Carlo prices.
- Compare Monte Carlo calibration with a semi-closed-form Heston pricer.
- Use a Treasury curve and dividend assumptions rather than relying only on parity.
- Add out-of-sample checks by fitting one maturity and testing another.

