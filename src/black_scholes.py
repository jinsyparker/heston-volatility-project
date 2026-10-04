"""Black-Scholes pricing, Greeks, and implied-volatility inversion."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, pi, sqrt

import numpy as np


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def norm_pdf(x: float) -> float:
    """Standard normal probability density."""
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)


def price(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    vol: float,
    side: str,
    dividend: float = 0.0,
) -> float:
    """Black-Scholes price for a European call or put."""
    if maturity <= 0 or vol <= 0:
        call_intrinsic = max(0.0, spot * exp(-dividend * maturity) - strike * exp(-rate * maturity))
        put_intrinsic = max(0.0, strike * exp(-rate * maturity) - spot * exp(-dividend * maturity))
        return call_intrinsic if side == "C" else put_intrinsic

    sqrt_t = sqrt(maturity)
    d1 = (log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * maturity) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t

    call = spot * exp(-dividend * maturity) * norm_cdf(d1) - strike * exp(-rate * maturity) * norm_cdf(d2)
    if side == "C":
        return call
    if side == "P":
        return call - spot * exp(-dividend * maturity) + strike * exp(-rate * maturity)
    raise ValueError("side must be 'C' or 'P'")


@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def greeks(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    vol: float,
    side: str,
    dividend: float = 0.0,
) -> Greeks:
    """Return annualized Black-Scholes Greeks."""
    if maturity <= 0 or vol <= 0 or spot <= 0 or strike <= 0:
        if side == "C":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
        return Greeks(delta=delta, gamma=0.0, vega=0.0, theta=0.0, rho=0.0)

    sqrt_t = sqrt(maturity)
    d1 = (log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * maturity) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t
    disc_q = exp(-dividend * maturity)
    disc_r = exp(-rate * maturity)

    gamma = disc_q * norm_pdf(d1) / (spot * vol * sqrt_t)
    vega = spot * disc_q * norm_pdf(d1) * sqrt_t

    if side == "C":
        delta = disc_q * norm_cdf(d1)
        theta = (
            -(spot * disc_q * norm_pdf(d1) * vol) / (2.0 * sqrt_t)
            - rate * strike * disc_r * norm_cdf(d2)
            + dividend * spot * disc_q * norm_cdf(d1)
        )
        rho = strike * maturity * disc_r * norm_cdf(d2)
    elif side == "P":
        delta = disc_q * (norm_cdf(d1) - 1.0)
        theta = (
            -(spot * disc_q * norm_pdf(d1) * vol) / (2.0 * sqrt_t)
            + rate * strike * disc_r * norm_cdf(-d2)
            - dividend * spot * disc_q * norm_cdf(-d1)
        )
        rho = -strike * maturity * disc_r * norm_cdf(-d2)
    else:
        raise ValueError("side must be 'C' or 'P'")

    return Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)


def implied_volatility(
    target_price: float,
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    side: str,
    dividend: float = 0.0,
    lower: float = 1e-6,
    upper: float = 5.0,
    tolerance: float = 1e-7,
    max_iter: int = 100,
) -> float:
    """Invert Black-Scholes price with bisection."""
    if target_price <= 0 or maturity <= 0:
        return np.nan

    intrinsic = price(spot, strike, maturity, rate, lower, side, dividend)
    max_price = spot * exp(-dividend * maturity) if side == "C" else strike * exp(-rate * maturity)
    if target_price < intrinsic - tolerance or target_price > max_price + tolerance:
        return np.nan

    lo, hi = lower, upper
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        model_price = price(spot, strike, maturity, rate, mid, side, dividend)
        error = model_price - target_price
        if abs(error) < tolerance or (hi - lo) < tolerance:
            return mid
        if error > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)

