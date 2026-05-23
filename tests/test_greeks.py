import pytest
import numpy as np
from src.pricer.greeks import call_delta, put_delta, gamma, vega, call_theta, put_theta, call_rho, put_rho, greeks


def test_call_delta_between_zero_and_one():
    result = call_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert 0 <= result <= 1


def test_put_delta_between_negative_one_and_zero():
    result = put_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert -1 <= result <= 0


def test_call_delta_minus_put_delta_equals_one():
    cd = call_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    pd = put_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(cd - pd - 1.0) < 1e-10


def test_call_delta_deep_itm_approaches_one():
    # deep in the money call delta approaches 1
    result = call_delta(S=100, K=10, sigma=0.3, T=1/82, r=0)
    assert result > 0.99


def test_call_delta_deep_otm_approaches_zero():
    # deep out of the money call delta approaches 0
    result = call_delta(S=5, K=100, sigma=0.3, T=1/82, r=0)
    assert result < 0.01


def test_put_delta_deep_itm_approaches_negative_one():
    # deep in the money put delta approaches -1
    result = put_delta(S=5, K=100, sigma=0.3, T=1/82, r=0)
    assert result < -0.99


def test_put_delta_deep_otm_approaches_zero():
    # deep out of the money put delta approaches 0
    result = put_delta(S=100, K=5, sigma=0.3, T=1/82, r=0)
    assert result > -0.01


def test_gamma_positive():
    # gamma is always positive
    result = gamma(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0


def test_gamma_highest_atm():
    # gamma is highest at the money
    gamma_atm = gamma(S=25, K=25, sigma=0.3, T=1/82, r=0)
    gamma_itm = gamma(S=35, K=25, sigma=0.3, T=1/82, r=0)
    gamma_otm = gamma(S=15, K=25, sigma=0.3, T=1/82, r=0)
    assert gamma_atm > gamma_itm
    assert gamma_atm > gamma_otm


def test_vega_positive():
    # vega is always positive
    result = vega(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0


def test_vega_highest_atm():
    # vega is highest at the money
    vega_atm = vega(S=25, K=25, sigma=0.3, T=1/82, r=0)
    vega_itm = vega(S=40, K=25, sigma=0.3, T=1/82, r=0)
    vega_otm = vega(S=10, K=25, sigma=0.3, T=1/82, r=0)
    assert vega_atm > vega_itm
    assert vega_atm > vega_otm


def test_call_theta_negative():
    # call theta is always negative — time decay hurts long positions
    result = call_theta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result < 0


def test_put_theta_negative():
    # put theta is negative with r=0
    result = put_theta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result < 0


def test_call_rho_positive():
    # call rho is always positive — calls benefit from higher rates
    result = call_rho(S=27, K=25, sigma=0.3, T=1/82, r=0.05)
    assert result > 0


def test_put_rho_negative():
    # put rho is always negative — puts hurt from higher rates
    result = put_rho(S=27, K=25, sigma=0.3, T=1/82, r=0.05)
    assert result < 0


def test_greeks_returns_all_keys():
    result = greeks(S=27, K=25, sigma=0.3, T=1/82, r=0)
    expected_keys = ['call delta', 'put delta', 'gamma', 'vega', 'call_theta', 'put_theta', 'call_rho', 'put_rho']
    for key in expected_keys:
        assert key in result


def test_greeks_returns_finite_values():
    result = greeks(S=27, K=25, sigma=0.3, T=1/82, r=0)
    for key, value in result.items():
        assert np.isfinite(value)


def test_vega_zero_with_zero_sigma():
    # near zero sigma vega approaches zero
    result = vega(S=27, K=25, sigma=1e-10, T=1/82, r=0)
    assert result >= 0


def test_call_delta_atm_approximately_half():
    # at the money call delta is approximately 0.5
    result = call_delta(S=25, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(result - 0.5) < 0.1


def test_put_delta_atm_approximately_negative_half():
    # at the money put delta is approximately -0.5
    result = put_delta(S=25, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(result + 0.5) < 0.1
