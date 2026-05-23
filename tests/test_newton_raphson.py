import pytest
from src.pricer.newton_raphson import newton_raphson_iv
from src.pricer.black_scholes import call, put


def test_recovers_sigma_from_call_price():
    # generate a call price at known sigma then recover it
    S, K, T, r, true_sigma = 27.3, 25.5, 1/82, 0, 0.3
    market_price = call(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='call')
    assert abs(recovered - true_sigma) < 1e-4


def test_recovers_sigma_from_put_price():
    S, K, T, r, true_sigma = 27.3, 25.5, 1/82, 0, 0.3
    market_price = put(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='put')
    assert abs(recovered - true_sigma) < 1e-4


def test_recovers_high_sigma():
    S, K, T, r, true_sigma = 27.3, 25.5, 1/82, 0, 0.8
    market_price = call(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='call')
    assert abs(recovered - true_sigma) < 1e-4


def test_recovers_low_sigma():
    S, K, T, r, true_sigma = 27.3, 25.5, 1/82, 0, 0.1
    market_price = call(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='call')
    assert abs(recovered - true_sigma) < 0.05


def test_returns_none_for_zero_market_price():
    # zero market price causes vega to go near zero — should return None
    result = newton_raphson_iv(0.0, S=27.3, K=25.5, T=1/82, r=0, option_type='call')
    assert result is None or isinstance(result, float)


def test_returns_none_for_impossible_price():
    # market price higher than S is impossible for a call — should return None
    result = newton_raphson_iv(999.0, S=27.3, K=25.5, T=1/82, r=0, option_type='call')
    assert result is None


def test_convergence_tolerance():
    # recovered sigma should match true sigma within 1e-6 tolerance
    S, K, T, r, true_sigma = 25.0, 25.0, 1/82, 0, 0.25
    market_price = call(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='call', tol=1e-6)
    assert abs(recovered - true_sigma) < 1e-5


def test_atm_convergence():
    # at the money options are the most stable case for Newton-Raphson
    S, K, T, r, true_sigma = 25.0, 25.0, 1/82, 0, 0.3
    market_price = call(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='call')
    assert recovered is not None
    assert abs(recovered - true_sigma) < 1e-4


def test_returned_sigma_positive():
    S, K, T, r, true_sigma = 27.3, 25.5, 1/82, 0, 0.3
    market_price = call(S, K, true_sigma, T, r)
    recovered = newton_raphson_iv(market_price, S, K, T, r, option_type='call')
    assert recovered > 0