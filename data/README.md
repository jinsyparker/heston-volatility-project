# Data

The project can fetch fresh option chains with `yfinance`, but reproducible research should keep a saved copy of the cleaned option surface.

Recommended files:

- `data/raw/`: unmodified source pulls, if preserved
- `data/processed/AAPL_surface.csv`: cleaned options table created by notebook 01
- `data/sample/`: frozen canonical snapshot used by the README and run summary

The notebooks are written so the data pull can be rerun, but the main analysis should use a saved CSV once it exists. The current canonical sample was saved from a Yahoo Finance option-chain pull on 2026-10-08 at 21:43 IST.
