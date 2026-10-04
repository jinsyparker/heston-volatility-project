"""Heston calibration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .black_scholes import implied_volatility
from .heston import HestonParams, price_european_mc_vector, simulate_heston_paths


@dataclass(frozen=True)
class CalibrationResult:
    """Container for Heston calibration output."""

    params: HestonParams
    objective: float
    success: bool
    message: str
    target_expiry: pd.Timestamp
    maturity: float
    strikes: np.ndarray
    target_iv: np.ndarray
    model_iv: np.ndarray


def select_single_expiry_target(
    iv_fit_df: pd.DataFrame,
    spot: float,
    t_min: float = 0.25,
    t_max: float = 0.75,
) -> tuple[pd.Timestamp, float, np.ndarray, np.ndarray]:
    """Select a liquid medium-dated smile for a compact calibration demo."""
    clean = iv_fit_df.dropna(subset=["iv_fit", "T", "moneyness"]).copy()
    if clean.empty:
        raise RuntimeError("No fitted IV data available for calibration.")

    candidates = clean[(clean["T"] >= t_min) & (clean["T"] <= t_max)]
    if candidates.empty:
        target_t = clean["T"].max()
        target_expiry = clean.loc[clean["T"].idxmax(), "expiry"]
    else:
        target_expiry = candidates["expiry"].iloc[0]
        target_t = candidates.loc[candidates["expiry"] == target_expiry, "T"].iloc[0]

    target = clean[clean["expiry"] == target_expiry].sort_values("moneyness")
    strikes = target["moneyness"].to_numpy(dtype=float) * float(spot)
    target_iv = target["iv_fit"].to_numpy(dtype=float)
    return pd.to_datetime(target_expiry), float(target_t), strikes, target_iv


def calibrate_heston_to_smile(
    spot: float,
    rate: float,
    dividend: float,
    maturity: float,
    strikes: np.ndarray,
    target_iv: np.ndarray,
    initial: HestonParams = HestonParams(v0=0.04, kappa=2.0, theta=0.04, sigma=0.3, rho=-0.7),
    bounds: Optional[list[tuple[float, float]]] = None,
    n_steps: int = 100,
    n_paths: int = 30_000,
    maxiter: int = 60,
    seed: int = 42,
    device=None,
):
    """Calibrate Heston parameters by minimizing squared IV errors."""
    from scipy.optimize import minimize

    if bounds is None:
        bounds = [
            (0.1, 10.0),
            (0.005, 1.0),
            (0.01, 2.0),
            (-0.99, -0.01),
            (0.005, 1.0),
        ]

    strikes = np.asarray(strikes, dtype=float)
    target_iv = np.asarray(target_iv, dtype=float)
    x0 = np.array([initial.kappa, initial.theta, initial.sigma, initial.rho, initial.v0], dtype=float)

    def objective(x):
        kappa, theta, sigma, rho, v0 = x
        params = HestonParams(v0=v0, kappa=kappa, theta=theta, sigma=sigma, rho=rho)
        try:
            paths, _ = simulate_heston_paths(
                spot=spot,
                rate=rate,
                dividend=dividend,
                params=params,
                maturity=maturity,
                n_steps=n_steps,
                n_paths=n_paths,
                seed=seed,
                device=device,
            )
            model_prices = price_european_mc_vector(paths, strikes, maturity, rate, side="C")
            model_iv = np.array(
                [
                    implied_volatility(p, spot, k, maturity, rate, "C", dividend)
                    for p, k in zip(model_prices, strikes)
                ]
            )
        except Exception:
            return 1e9

        if np.isnan(model_iv).any():
            return 1e9
        return float(np.mean((model_iv - target_iv) ** 2))

    opt = minimize(
        objective,
        x0,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": maxiter, "ftol": 1e-7},
    )

    kappa, theta, sigma, rho, v0 = opt.x
    params = HestonParams(v0=v0, kappa=kappa, theta=theta, sigma=sigma, rho=rho)
    final_paths, _ = simulate_heston_paths(
        spot=spot,
        rate=rate,
        dividend=dividend,
        params=params,
        maturity=maturity,
        n_steps=max(n_steps, 150),
        n_paths=max(n_paths, 50_000),
        seed=seed,
        device=device,
    )
    final_prices = price_european_mc_vector(final_paths, strikes, maturity, rate, side="C")
    final_iv = np.array(
        [implied_volatility(p, spot, k, maturity, rate, "C", dividend) for p, k in zip(final_prices, strikes)]
    )
    return params, float(opt.fun), bool(opt.success), str(opt.message), final_iv

