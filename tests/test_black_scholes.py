import math

from src.black_scholes import greeks, implied_volatility, price
from src.validation import put_call_parity_residual


def test_put_call_parity_residual_is_small():
    spot = 100.0
    strike = 105.0
    maturity = 0.75
    rate = 0.04
    dividend = 0.01
    vol = 0.22

    call = price(spot, strike, maturity, rate, vol, "C", dividend)
    put = price(spot, strike, maturity, rate, vol, "P", dividend)

    residual = put_call_parity_residual(spot, strike, maturity, rate, call, put, dividend)
    assert abs(residual) < 1e-10


def test_implied_volatility_recovers_input_vol():
    spot = 100.0
    strike = 95.0
    maturity = 0.5
    rate = 0.03
    dividend = 0.0
    vol = 0.27

    option_price = price(spot, strike, maturity, rate, vol, "C", dividend)
    recovered = implied_volatility(option_price, spot, strike, maturity, rate, "C", dividend)

    assert math.isclose(recovered, vol, rel_tol=0, abs_tol=1e-5)


def test_call_delta_between_zero_and_one():
    g = greeks(spot=100.0, strike=100.0, maturity=1.0, rate=0.05, vol=0.2, side="C")
    assert 0.0 < g.delta < 1.0
    assert g.gamma > 0.0
    assert g.vega > 0.0

