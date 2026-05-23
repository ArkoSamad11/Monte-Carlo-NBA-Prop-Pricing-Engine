import pytest
import numpy as np
from src.pricer.black_scholes import d1, d2, call, put, black_scholes


def test_call_positive_itm():
    # in the money call — S above K, should have positive value
    result = call(S=30, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0


def test_put_positive_otm():
    # out of the money put — S above K, put still has value
    result = put(S=30, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0


def test_call_greater_than_put_itm():
    # when S > K call should be worth more than put
    c = call(S=30, K=25, sigma=0.3, T=1/82, r=0)
    p = put(S=30, K=25, sigma=0.3, T=1/82, r=0)
    assert c > p


def test_put_greater_than_call_otm():
    # when S < K put should be worth more than call
    c = call(S=20, K=25, sigma=0.3, T=1/82, r=0)
    p = put(S=20, K=25, sigma=0.3, T=1/82, r=0)
    assert p > c


def test_put_call_parity():
    # put call parity: call - put = S - K * exp(-rT)
    S, K, sigma, T, r = 27.3, 25.5, 0.18, 1/82, 0
    c = call(S, K, sigma, T, r)
    p = put(S, K, sigma, T, r)
    parity = S - K * np.exp(-r * T)
    assert abs((c - p) - parity) < 0.01


def test_atm_call_put_approximately_equal():
    # at the money with r=0 call and put should be approximately equal
    c = call(S=25, K=25, sigma=0.3, T=1/82, r=0)
    p = put(S=25, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(c - p) < 0.1


def test_d1_atm():
    # at the money d1 should be positive when sigma > 0
    result = d1(S=25, K=25, sigma=0.3, T=1/82, r=0)
    assert result > 0


def test_d2_less_than_d1():
    # d2 is always d1 minus sigma*sqrt(T) so d2 < d1
    d1_val = d1(S=27, K=25, sigma=0.3, T=1/82, r=0)
    d2_val = d2(S=27, K=25, sigma=0.3, T=1/82, r=0)
    assert d2_val < d1_val


def test_black_scholes_returns_tuple():
    result = black_scholes(S=27.3, K=25.5, sigma=0.18, T=1/82, r=0)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_higher_volatility_increases_option_value():
    # higher sigma means more uncertainty means higher option value
    c_low = call(S=25, K=25, sigma=0.1, T=1/82, r=0)
    c_high = call(S=25, K=25, sigma=0.5, T=1/82, r=0)
    assert c_high > c_low


def test_zero_volatility_call():
    # zero volatility — call value should be max(S-K, 0)
    c = call(S=30, K=25, sigma=1e-10, T=1/82, r=0)
    assert abs(c - 5.0) < 0.1


def test_zero_volatility_put_otm():
    # zero volatility OTM put — should be worth near zero
    p = put(S=30, K=25, sigma=1e-10, T=1/82, r=0)
    assert p < 0.1


def test_deep_itm_call_approaches_intrinsic():
    # deep in the money call approaches S - K
    c = call(S=50, K=25, sigma=0.3, T=1/82, r=0)
    assert abs(c - 25.0) < 1.0


def test_deep_otm_call_near_zero():
    # deep out of the money call approaches zero
    c = call(S=10, K=50, sigma=0.3, T=1/82, r=0)
    assert c < 0.01


def test_deep_otm_put_near_zero():
    # deep out of the money put approaches zero
    p = put(S=50, K=10, sigma=0.3, T=1/82, r=0)
    assert p < 0.01


def test_call_never_negative():
    # call price can never be negative
    c = call(S=5, K=50, sigma=0.1, T=1/82, r=0)
    assert c >= 0


def test_put_never_negative():
    # put price can never be negative
    p = put(S=50, K=5, sigma=0.1, T=1/82, r=0)
    assert p >= 0


def test_s_equals_zero():
    # if underlying is zero call is worthless
    c = call(S=0.001, K=25, sigma=0.3, T=1/82, r=0)
    assert c < 0.01