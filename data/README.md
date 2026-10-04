# Data

The project can fetch fresh option chains with `yfinance`, but reproducible research should keep a saved copy of the cleaned option surface.

Recommended files:

- `data/raw/`: unmodified source pulls, if preserved
- `data/processed/AAPL_surface.csv`: cleaned options table created by notebook 01

The notebooks are written so the data pull can be rerun, but the main analysis should use the saved processed CSV once it exists.

