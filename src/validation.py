"""Market-data validation and no-arbitrage diagnostics."""

from __future__ import annotations

from math import exp, log
from typing import Dict

import numpy as np
import pandas as pd

from .black_scholes import price


def put_call_parity_residual(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    call_price: float,
    put_price: float,
    dividend: float = 0.0,
) -> float:
    """Return C - P - (S exp(-qT) - K exp(-rT))."""
    forward_parity = spot * exp(-dividend * maturity) - strike * exp(-rate * maturity)
    return call_price - put_price - forward_parity


def validate_dataset(
    df: pd.DataFrame,
    spot: float,
    rate: float = 0.0,
    dividend: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Reprice quotes from IV and compute put-call parity diagnostics."""
    checked = df.copy()
    checked["bs_repro"] = [
        price(spot, row.strike, row.T, rate, row.iv_clamped, row.side, dividend)
        for row in checked.itertuples()
    ]
    checked["abs_err_vs_target"] = (checked["bs_repro"] - checked["target_price"]).abs()

    small = checked[["expiry", "T", "strike", "side", "target_price"]].copy()
    pairs = (
        small.pivot_table(
            index=["expiry", "T", "strike"],
            columns="side",
            values="target_price",
            aggfunc="median",
        )
        .dropna(subset=["C", "P"])
        .reset_index()
    )

    pairs["parity_residual"] = [
        put_call_parity_residual(spot, row.strike, row.T, rate, row.C, row.P, dividend)
        for row in pairs.itertuples()
    ]

    summary = {
        "rows": int(len(checked)),
        "mean_abs_err_vs_target": float(checked["abs_err_vs_target"].mean()),
        "median_abs_err_vs_target": float(checked["abs_err_vs_target"].median()),
        "pct_large_err_gt_1": float((checked["abs_err_vs_target"] > 1.0).mean() * 100.0),
        "parity_pairs": int(len(pairs)),
        "parity_residual_mean": float(pairs["parity_residual"].mean()) if len(pairs) else np.nan,
        "parity_residual_median": float(pairs["parity_residual"].median()) if len(pairs) else np.nan,
    }
    return checked, pairs, summary


def infer_rate_dividend_by_expiry(df: pd.DataFrame, spot: float) -> Dict[pd.Timestamp, dict]:
    """Infer discount factor, forward, rate, and dividend yield from put-call parity."""
    out: Dict[pd.Timestamp, dict] = {}
    small = df[["expiry", "T", "strike", "side", "target_price"]].copy()
    pairs = (
        small.pivot_table(
            index=["expiry", "T", "strike"],
            columns="side",
            values="target_price",
            aggfunc="median",
        )
        .dropna(subset=["C", "P"])
        .reset_index()
    )

    for (expiry, maturity), block in pairs.groupby(["expiry", "T"]):
        if maturity <= 0 or len(block) < 5:
            continue
        strikes = block["strike"].to_numpy(dtype=float)
        call_minus_put = (block["C"] - block["P"]).to_numpy(dtype=float)
        design = np.column_stack([np.ones_like(strikes), strikes])
        alpha, beta = np.linalg.lstsq(design, call_minus_put, rcond=None)[0]
        discount_factor = max(1e-8, -beta)
        forward = alpha / discount_factor if discount_factor > 0 else np.nan
        rate = -log(discount_factor) / maturity if discount_factor > 0 else np.nan
        carry = log(forward / spot) / maturity if forward > 0 and spot > 0 else np.nan
        dividend = rate - carry if np.isfinite(carry) else np.nan
        out[pd.to_datetime(expiry)] = {
            "T": float(maturity),
            "DF": float(discount_factor),
            "F": float(forward),
            "r": float(rate),
            "q": float(dividend),
            "n_pairs": int(len(block)),
        }
    return out


def attach_rates_and_recheck(
    df: pd.DataFrame,
    spot: float,
    rate_dividend_map: Dict[pd.Timestamp, dict],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Attach inferred r/q by expiry and recompute diagnostics."""
    checked = df.copy()
    checked["r"] = checked["expiry"].map(
        lambda expiry: rate_dividend_map.get(pd.to_datetime(expiry), {}).get("r", 0.0)
    )
    checked["q"] = checked["expiry"].map(
        lambda expiry: rate_dividend_map.get(pd.to_datetime(expiry), {}).get("q", 0.0)
    )

    checked["bs_repro_rq"] = [
        price(spot, row.strike, row.T, row.r, row.iv_clamped, row.side, row.q)
        for row in checked.itertuples()
    ]
    checked["abs_err_vs_target_rq"] = (checked["bs_repro_rq"] - checked["target_price"]).abs()

    small = checked[["expiry", "T", "strike", "side", "target_price", "r", "q"]].copy()
    pairs = (
        small.pivot_table(
            index=["expiry", "T", "strike", "r", "q"],
            columns="side",
            values="target_price",
            aggfunc="median",
        )
        .dropna(subset=["C", "P"])
        .reset_index()
    )
    pairs["parity_residual_rq"] = [
        put_call_parity_residual(spot, row.strike, row.T, row.r, row.C, row.P, row.q)
        for row in pairs.itertuples()
    ]

    summary = {
        "rows": int(len(checked)),
        "abs_err_vs_target_rq_mean": float(checked["abs_err_vs_target_rq"].mean()),
        "abs_err_vs_target_rq_median": float(checked["abs_err_vs_target_rq"].median()),
        "parity_pairs": int(len(pairs)),
        "parity_residual_rq_mean": float(pairs["parity_residual_rq"].mean()) if len(pairs) else np.nan,
        "parity_residual_rq_median": float(pairs["parity_residual_rq"].median()) if len(pairs) else np.nan,
    }
    return checked, pairs, summary

