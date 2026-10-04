"""Heston Monte Carlo simulation and pricing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class HestonParams:
    """Heston stochastic volatility parameters."""

    v0: float
    kappa: float
    theta: float
    sigma: float
    rho: float


def get_torch_device(prefer_gpu: bool = True):
    """Return a torch device, using CUDA when requested and available."""
    import torch

    if prefer_gpu and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def simulate_heston_paths(
    spot: float,
    rate: float,
    dividend: float,
    params: HestonParams,
    maturity: float,
    n_steps: int,
    n_paths: int,
    use_antithetic: bool = True,
    seed: Optional[int] = 42,
    device=None,
):
    """Simulate spot and variance paths with log-Euler and full truncation."""
    import torch

    if device is None:
        device = get_torch_device()
    if seed is not None:
        torch.manual_seed(seed)
        if device.type == "cuda":
            torch.cuda.manual_seed_all(seed)

    if use_antithetic and n_paths % 2 != 0:
        n_paths += 1
    n_gen = n_paths // 2 if use_antithetic else n_paths

    spot_t = torch.tensor(float(spot), device=device)
    rate_t = torch.tensor(float(rate), device=device)
    dividend_t = torch.tensor(float(dividend), device=device)
    v0_t = torch.tensor(float(params.v0), device=device)
    kappa_t = torch.tensor(float(params.kappa), device=device)
    theta_t = torch.tensor(float(params.theta), device=device)
    sigma_t = torch.tensor(float(params.sigma), device=device)
    rho_t = torch.tensor(float(params.rho), device=device)

    dt = float(maturity) / int(n_steps)
    sqrt_dt = torch.tensor(dt, device=device).sqrt()
    sqrt_one_minus_rho_sq = (1.0 - rho_t**2).sqrt()

    z_v = torch.randn(n_gen, n_steps, device=device)
    z_s = torch.randn(n_gen, n_steps, device=device)
    if use_antithetic:
        z_v = torch.cat([z_v, -z_v], dim=0)
        z_s = torch.cat([z_s, -z_s], dim=0)

    dw_v = sqrt_dt * z_v
    dw_s = sqrt_dt * (rho_t * z_v + sqrt_one_minus_rho_sq * z_s)

    log_spot_paths = torch.zeros(n_paths, n_steps + 1, device=device)
    variance_paths = torch.zeros(n_paths, n_steps + 1, device=device)
    log_spot_paths[:, 0] = spot_t.log()
    variance_paths[:, 0] = v0_t

    eps = torch.tensor(1e-10, device=device)
    for step in range(n_steps):
        v_t = torch.maximum(variance_paths[:, step], eps)
        sqrt_v_t = v_t.sqrt()
        v_next = variance_paths[:, step] + kappa_t * (theta_t - v_t) * dt + sigma_t * sqrt_v_t * dw_v[:, step]
        variance_paths[:, step + 1] = torch.maximum(v_next, eps)
        log_spot_paths[:, step + 1] = (
            log_spot_paths[:, step]
            + (rate_t - dividend_t - 0.5 * v_t) * dt
            + sqrt_v_t * dw_s[:, step]
        )

    return torch.exp(log_spot_paths), variance_paths


def price_european_mc(spot_paths, strike: float, maturity: float, rate: float, side: str = "C"):
    """Price one European option from simulated terminal spots."""
    import torch

    device = spot_paths.device
    strike_t = torch.tensor(float(strike), device=device)
    rate_t = torch.tensor(float(rate), device=device)
    maturity_t = torch.tensor(float(maturity), device=device)
    terminal = spot_paths[:, -1]

    if side == "C":
        payoffs = torch.maximum(terminal - strike_t, torch.tensor(0.0, device=device))
    elif side == "P":
        payoffs = torch.maximum(strike_t - terminal, torch.tensor(0.0, device=device))
    else:
        raise ValueError("side must be 'C' or 'P'")

    return torch.mean(payoffs) * torch.exp(-rate_t * maturity_t)


def price_european_mc_vector(spot_paths, strikes, maturity: float, rate: float, side: str = "C") -> np.ndarray:
    """Price several strikes from the same simulated terminal spots."""
    import torch

    device = spot_paths.device
    strike_t = torch.tensor(np.asarray(strikes, dtype=float), device=device).unsqueeze(0)
    terminal = spot_paths[:, -1].unsqueeze(1)

    if side == "C":
        payoffs = torch.maximum(terminal - strike_t, torch.tensor(0.0, device=device))
    elif side == "P":
        payoffs = torch.maximum(strike_t - terminal, torch.tensor(0.0, device=device))
    else:
        raise ValueError("side must be 'C' or 'P'")

    prices = torch.mean(payoffs, dim=0) * torch.exp(torch.tensor(-rate * maturity, device=device))
    return prices.detach().cpu().numpy()


def pathwise_delta(spot_paths, spot: float, strike: float, maturity: float, rate: float, side: str = "C"):
    """Pathwise delta estimator for European calls and puts."""
    import torch

    device = spot_paths.device
    terminal = spot_paths[:, -1]
    strike_t = torch.tensor(float(strike), device=device)
    spot_t = torch.tensor(float(spot), device=device)
    rate_t = torch.tensor(float(rate), device=device)
    maturity_t = torch.tensor(float(maturity), device=device)

    if side == "C":
        payoff_derivative = (terminal > strike_t).float()
    elif side == "P":
        payoff_derivative = -(terminal < strike_t).float()
    else:
        raise ValueError("side must be 'C' or 'P'")

    return torch.mean(payoff_derivative * terminal / spot_t) * torch.exp(-rate_t * maturity_t)


def finite_difference_v0_vega(
    base_price: float,
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    dividend: float,
    params: HestonParams,
    n_steps: int,
    n_paths: int,
    side: str = "C",
    v0_bump: float = 0.001,
    seed: int = 42,
    device=None,
):
    """Estimate sensitivity to initial volatility via a v0 finite difference."""
    import torch

    if device is None:
        device = get_torch_device()
    bumped = HestonParams(
        v0=params.v0 + v0_bump,
        kappa=params.kappa,
        theta=params.theta,
        sigma=params.sigma,
        rho=params.rho,
    )
    bumped_paths, _ = simulate_heston_paths(
        spot=spot,
        rate=rate,
        dividend=dividend,
        params=bumped,
        maturity=maturity,
        n_steps=n_steps,
        n_paths=n_paths,
        seed=seed,
        device=device,
    )
    bumped_price = price_european_mc(bumped_paths, strike, maturity, rate, side=side)
    if device.type == "cuda":
        torch.cuda.empty_cache()
    sensitivity_to_v0 = (bumped_price.item() - float(base_price)) / v0_bump
    return sensitivity_to_v0 * (2.0 * np.sqrt(params.v0))

