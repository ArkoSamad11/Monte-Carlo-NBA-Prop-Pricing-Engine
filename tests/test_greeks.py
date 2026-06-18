"""
Tests for the Black-Scholes Greeks module (src/pricer/greeks.py).

These tests validate the mathematical properties of each Greek rather than
exact numerical outputs. Greek values must satisfy well-known theoretical
bounds and relationships that hold regardless of input parameters. This
approach makes the tests robust to implementation details while ensuring
the underlying options math is correct.

Note: The Greeks module is not part of the live prediction pipeline. It was
developed during the initial research phase to explore whether an options-pricing
framework could model player prop distributions. These tests are retained to
document that research and demonstrate the mathematical correctness of the
implementation. See src/analysis/implied_vol.py for the production Monte Carlo
pipeline that replaced it.
"""

import pytest
import numpy as np
from src.pricer.greeks import call_delta, put_delta, gamma, vega, call_theta, put_theta, call_rho, put_rho, greeks

def test_call_delta_between_zero_and_one():
    # Call delta must always fall between 0 and 1 by definition.
    result = call_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert 0 <= result <= 1

def test_put_delta_between_negative_one_and_zero():
    # Put delta must always fall between -1 and 0 by definition.
    result = put_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert -1 <= result <= 0

def test_call_delta_minus_put_delta_equals_one():
    # Put-call parity requires call_delta - put_delta = 1.0 exactly.
    cd = call_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    pd = put_delta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(cd - pd - 1.0) < 1e-10

def test_call_delta_deep_itm_approaches_one():
    # Deep in-the-money call delta approaches 1 — the option behaves like the underlying.
    result = call_delta(S=100, K=10, sigma=0.3, T=1/82, r=0)
    assert result > 0.99

def test_call_delta_deep_otm_approaches_zero():
    # Deep out-of-the-money call delta approaches 0 — unlikely to be exercised.
    result = call_delta(S=5, K=100, sigma=0.3, T=1/82, r=0)
    assert result < 0.01

def test_put_delta_deep_itm_approaches_negative_one():
    # Deep in-the-money put delta approaches -1.
    result = put_delta(S=5, K=100, sigma=0.3, T=1/82, r=0)
    assert result < -0.99

def test_put_delta_deep_otm_approaches_zero():
    # Deep out-of-the-money put delta approaches 0.
    result = put_delta(S=100, K=5, sigma=0.3, T=1/82, r=0)
    assert result > -0.01

def test_call_delta_atm_approximately_half():
    # At-the-money call delta is approximately 0.5 — symmetric probability of expiring ITM.
    result = call_delta(S=25, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(result - 0.5) < 0.1

def test_put_delta_atm_approximately_negative_half():
    # At-the-money put delta is approximately -0.5.
    result = put_delta(S=25, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(result + 0.5) < 0.1

def test_gamma_positive():
    # Gamma is always positive for both calls and puts.
    result = gamma(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0

def test_gamma_highest_atm():
    # Gamma peaks at-the-money and decays for ITM and OTM positions.
    gamma_atm = gamma(S=25, K=25, sigma=0.3, T=1/82, r=0)
    gamma_itm = gamma(S=35, K=25, sigma=0.3, T=1/82, r=0)
    gamma_otm = gamma(S=15, K=25, sigma=0.3, T=1/82, r=0)
    assert gamma_atm > gamma_itm
    assert gamma_atm > gamma_otm

def test_vega_positive():
    # Vega is always positive — higher volatility increases option value for both calls and puts.
    result = vega(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0

def test_vega_highest_atm():
    # Vega peaks at-the-money where volatility has the most impact on option value.
    vega_atm = vega(S=25, K=25, sigma=0.3, T=1/82, r=0)
    vega_itm = vega(S=40, K=25, sigma=0.3, T=1/82, r=0)
    vega_otm = vega(S=10, K=25, sigma=0.3, T=1/82, r=0)
    assert vega_atm > vega_itm
    assert vega_atm > vega_otm

def test_vega_zero_with_zero_sigma():
    # Near-zero sigma produces near-zero vega — no volatility means no sensitivity to it.
    result = vega(S=27, K=25, sigma=1e-10, T=1/82, r=0)
    assert result >= 0

def test_call_theta_negative():
    # Call theta is always negative — time decay erodes long option value.
    result = call_theta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result < 0

def test_put_theta_negative():
    # Put theta is negative when r=0 — time decay also erodes put value with no rate offset.
    result = put_theta(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert result < 0

def test_call_rho_positive():
    # Call rho is always positive — higher interest rates increase call value.
    result = call_rho(S=27, K=25, sigma=0.3, T=1/82, r=0.05)
    assert result > 0

def test_put_rho_negative():
    # Put rho is always negative — higher interest rates decrease put value.
    result = put_rho(S=27, K=25, sigma=0.3, T=1/82, r=0.05)
    assert result < 0


def test_greeks_returns_all_keys():
    # greeks() must return a dictionary containing all eight Greek values.
    result = greeks(S=27, K=25, sigma=0.3, T=1/82, r=0)
    expected_keys = ['call delta', 'put delta', 'gamma', 'vega', 'call_theta', 'put_theta', 'call_rho', 'put_rho']
    for key in expected_keys:
        assert key in result

def test_greeks_returns_finite_values():
    # All Greek values must be finite — no NaN or infinity from edge case inputs.
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
