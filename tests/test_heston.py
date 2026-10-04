import math

import pytest

torch = pytest.importorskip("torch")

from src.black_scholes import price
from src.heston import HestonParams, get_torch_device, price_european_mc, simulate_heston_paths


def test_heston_collapses_to_black_scholes_when_vol_of_vol_is_zero():
    device = get_torch_device(prefer_gpu=False)
    spot = 100.0
    strike = 100.0
    maturity = 1.0
    rate = 0.03
    dividend = 0.0
    vol = 0.2
    params = HestonParams(v0=vol**2, kappa=2.0, theta=vol**2, sigma=0.0, rho=0.0)

    paths, _ = simulate_heston_paths(
        spot=spot,
        rate=rate,
        dividend=dividend,
        params=params,
        maturity=maturity,
        n_steps=64,
        n_paths=20_000,
        seed=7,
        device=device,
    )
    mc_price = price_european_mc(paths, strike=strike, maturity=maturity, rate=rate, side="C").item()
    bs_price = price(spot, strike, maturity, rate, vol, "C", dividend)

    assert math.isclose(mc_price, bs_price, rel_tol=0, abs_tol=0.35)

