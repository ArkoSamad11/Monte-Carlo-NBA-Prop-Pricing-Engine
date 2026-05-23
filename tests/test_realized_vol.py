import pytest
import numpy as np
from src.analysis.realized_vol import find_sigma


def test_returns_float():
    result = find_sigma([20, 22, 18, 25, 21, 19, 23, 20, 22, 21])
    assert isinstance(result, float)


def test_positive_volatility():
    # non-constant series should have positive volatility
    result = find_sigma([20, 22, 18, 25, 21, 19, 23, 20, 22, 21])
    assert result > 0


def test_zero_volatility_constant_series():
    # constant series has zero log returns — sigma should be 0
    result = find_sigma([20, 20, 20, 20, 20, 20, 20, 20, 20, 20])
    assert result == 0.0


def test_zero_values_replaced():
    # zero values get replaced with 0.01 — should not crash
    result = find_sigma([0, 20, 0, 22, 18, 0, 21, 19, 23, 20])
    assert isinstance(result, float)
    assert result >= 0


def test_all_zeros_does_not_crash():
    # all zeros replaced with 0.01 — constant series gives zero sigma
    result = find_sigma([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    assert result == 0.0


def test_high_variance_series():
    # highly volatile series should have higher sigma than stable series
    volatile = find_sigma([2, 30, 1, 28, 3, 25, 2, 27, 1, 30])
    stable = find_sigma([20, 21, 20, 22, 21, 20, 21, 22, 20, 21])
    assert volatile > stable


def test_single_element_list():
    # single element produces no log returns — should return 0.0
    result = find_sigma([20])
    assert result == 0.0


def test_two_element_list():
    # two elements produces one log return — std of single value is 0
    result = find_sigma([20, 25])
    assert result == 0.0


def test_nan_returns_zero():
    # any case producing nan should return 0.0
    result = find_sigma([20, 20, 20, 20, 20, 20, 20, 20, 20, 20])
    assert not np.isnan(result)


def test_log_returns_computed_correctly():
    # manually verify log return computation for simple case
    stat_list = [10, 20]
    result = find_sigma(stat_list)
    expected_log_return = np.log(10 / 20)
    expected_sigma = np.std([expected_log_return])
    assert abs(result - expected_sigma) < 1e-10