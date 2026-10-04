"""Option-chain data loading and cleaning utilities."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd


def time_to_maturity_years(
    expiry: Union[str, pd.Timestamp],
    as_of: Optional[Union[str, pd.Timestamp]] = None,
) -> float:
    """Return ACT/365.25 time to maturity in years."""
    now = pd.Timestamp.utcnow() if as_of is None else pd.to_datetime(as_of)
    exp_ts = pd.to_datetime(expiry)

    now_naive = now.tz_convert(None) if now.tzinfo is not None else now.tz_localize(None)
    exp_naive = exp_ts.tz_convert(None) if exp_ts.tzinfo is not None else exp_ts.tz_localize(None)
    seconds = (exp_naive - now_naive).total_seconds()
    return max(seconds / (365.25 * 24 * 3600), 0.0)


def add_side_and_mid(df: pd.DataFrame, side: str) -> pd.DataFrame:
    """Attach option side and a robust mid quote."""
    out = df.copy()
    out["side"] = side
    has_bid_ask = out[["bid", "ask"]].notna().all(axis=1) & (out["ask"] > 0)
    out["mid"] = np.where(has_bid_ask, (out["bid"] + out["ask"]) / 2.0, out["lastPrice"])
    return out


def robust_target_price(row: pd.Series) -> float:
    """Prefer mid clipped to bid/ask; otherwise use last price."""
    bid, ask, mid, last = row.get("bid"), row.get("ask"), row.get("mid"), row.get("lastPrice")
    if pd.notna(bid) and pd.notna(ask) and ask > 0 and pd.notna(mid):
        return float(min(max(mid, bid), ask))
    if pd.notna(mid):
        return float(mid)
    return float(last)


def build_option_dataset(
    ticker: str,
    expiries: Union[str, List[str], None] = "auto",
    tmin: float = 0.02,
    tmax: float = 0.75,
    moneyness_bounds: Tuple[float, float] = (0.6, 1.4),
    iv_bounds: Tuple[float, float] = (0.01, 3.0),
    require_open_interest: bool = True,
    save_csv: Optional[Union[str, Path]] = None,
    as_of: Optional[Union[str, pd.Timestamp]] = None,
) -> Tuple[pd.DataFrame, float]:
    """Fetch and clean option chains into a calibration-ready table."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install yfinance or load a saved CSV from data/processed.") from exc

    opt = yf.Ticker(ticker)
    all_expiries = list(opt.options or [])

    if isinstance(expiries, list):
        chosen_expiries = [e for e in expiries if e in all_expiries]
    elif expiries == "auto" or expiries is None:
        chosen_expiries = [
            e for e in all_expiries if tmin <= time_to_maturity_years(e, as_of=as_of) <= tmax
        ]
    else:
        chosen_expiries = [expiries] if expiries in all_expiries else []

    if not chosen_expiries:
        raise ValueError(f"No expiries selected for {ticker}. Available sample: {all_expiries[:5]}")

    hist = opt.history(period="5d", interval="1d")
    if hist.empty:
        raise RuntimeError(f"No price history returned for {ticker}.")
    spot = float(hist["Close"].iloc[-1])

    tables = []
    for expiry in chosen_expiries:
        chain = opt.option_chain(expiry)
        calls = add_side_and_mid(chain.calls, "C")
        puts = add_side_and_mid(chain.puts, "P")
        table = pd.concat([calls, puts], ignore_index=True).rename(
            columns={"impliedVolatility": "iv"}
        )
        table["iv"] = pd.to_numeric(table["iv"], errors="coerce")
        table["expiry"] = pd.to_datetime(expiry)
        table["T"] = time_to_maturity_years(expiry, as_of=as_of)
        table["underlying"] = ticker
        tables.append(table)

    df = pd.concat(tables, ignore_index=True)
    df["moneyness"] = df["strike"] / spot
    df["type"] = np.where(df["side"] == "C", 1, -1)
    df["iv_clamped"] = df["iv"].clip(lower=iv_bounds[0], upper=iv_bounds[1])

    liquid = df["mid"].notna() & (df["mid"] > 0)
    if require_open_interest:
        liquid &= df["openInterest"].fillna(0) > 0

    df = df[liquid & df["moneyness"].between(*moneyness_bounds)].copy()
    df["target_price"] = df.apply(robust_target_price, axis=1)

    columns = [
        "underlying",
        "expiry",
        "T",
        "side",
        "type",
        "strike",
        "moneyness",
        "bid",
        "ask",
        "mid",
        "lastPrice",
        "target_price",
        "openInterest",
        "volume",
        "iv",
        "iv_clamped",
        "inTheMoney",
        "currency",
    ]
    df = df[columns].sort_values(["expiry", "side", "strike"]).reset_index(drop=True)

    if save_csv:
        path = Path(save_csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)

    return df, spot


def load_option_dataset(path: Union[str, Path]) -> pd.DataFrame:
    """Load a saved option dataset and restore date columns."""
    df = pd.read_csv(path)
    if "expiry" in df.columns:
        df["expiry"] = pd.to_datetime(df["expiry"])
    return df

