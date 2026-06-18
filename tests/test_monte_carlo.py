import pytest
import numpy as np
from src.analysis.implied_vol import monte_carlo_prob, get_true_prob


def test_monte_carlo_prob_over_high_mean():
    # player averaging 30 points against 15.5 line 
    # over probability should be high
    stat_list = [28, 31, 29, 32, 27, 30, 33, 28, 31, 29]
    prob_over, simulations = monte_carlo_prob(stat_list, K=15.5, stat_category='points')
    assert prob_over > 0.80


def test_monte_carlo_prob_under_low_mean():
    # player averaging 5 points against 15.5 line 
    # over probability should be low
    stat_list = [4, 5, 6, 3, 5, 7, 4, 6, 5, 4]
    prob_over, simulations = monte_carlo_prob(stat_list, K=15.5, stat_category='points')
    assert prob_over < 0.20


def test_monte_carlo_returns_tuple():
    stat_list = [20, 22, 18, 25, 21, 19, 23, 20, 22, 21]
    result = monte_carlo_prob(stat_list, K=20.5, stat_category='points')
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_monte_carlo_prob_between_zero_and_one():
    stat_list = [20, 22, 18, 25, 21, 19, 23, 20, 22, 21]
    prob_over, simulations = monte_carlo_prob(stat_list, K=20.5, stat_category='points')
    assert 0 <= prob_over <= 1


def test_monte_carlo_simulations_length():
    stat_list = [20, 22, 18, 25, 21, 19, 23, 20, 22, 21]
    prob_over, simulations = monte_carlo_prob(stat_list, K=20.5, stat_category='points', n_simulations=10000)
    assert len(simulations) == 10000


def test_monte_carlo_negative_binomial_rebounds():
    # rebounds use negative binomial when variance exceeds mean
    stat_list = [4, 12, 3, 14, 2, 11, 5, 13, 3, 10]
    prob_over, simulations = monte_carlo_prob(stat_list, K=7.5, stat_category='rebounds')
    assert 0 <= prob_over <= 1


def test_monte_carlo_zero_sigma_above_line():
    # all same values above line
    # should return 1.0
    stat_list = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    prob_over, simulations = monte_carlo_prob(stat_list, K=15.5, stat_category='points')
    assert prob_over == 1.0


def test_monte_carlo_zero_sigma_below_line():
    # all same values below line
    # should return 0.0
    stat_list = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
    prob_over, simulations = monte_carlo_prob(stat_list, K=15.5, stat_category='points')
    assert prob_over == 0.0


def test_monte_carlo_pace_factor_increases_prob():
    # higher pace factor increases mu which increases over probability
    stat_list = [20, 22, 18, 25, 21, 19, 23, 20, 22, 21]
    prob_normal, _ = monte_carlo_prob(stat_list, K=20.5, stat_category='points', pace_factor=1.0)
    prob_fast, _ = monte_carlo_prob(stat_list, K=20.5, stat_category='points', pace_factor=1.2)
    assert prob_fast > prob_normal


def test_monte_carlo_def_factor_decreases_prob():
    # lower def factor suppresses mu which decreases over probability
    stat_list = [20, 22, 18, 25, 21, 19, 23, 20, 22, 21]
    prob_normal, _ = monte_carlo_prob(stat_list, K=20.5, stat_category='points', def_factor=1.0)
    prob_elite_defense, _ = monte_carlo_prob(stat_list, K=20.5, stat_category='points', def_factor=0.85)
    assert prob_elite_defense < prob_normal


def test_get_true_prob_all_above():
    # all games above line
    # weighted prob should be 1.0
    stat_list = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    result = get_true_prob(stat_list, K=15.5)
    assert result == 1.0


def test_get_true_prob_all_below():
    # all games below line 
    # weighted prob should be 0.0
    stat_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = get_true_prob(stat_list, K=15.5)
    assert result == 0.0


def test_get_true_prob_empty_list():
    result = get_true_prob([], K=15.5)
    assert result == 0.0


def test_get_true_prob_recent_games_weighted_higher():
    # recent hits weighted more than old hits, same number of hits but different positions
    # recent hit: [20, 5, 5, 5, 5, 5, 5, 5, 5, 5], hit only in most recent game
    # old hit: [5, 5, 5, 5, 5, 5, 5, 5, 5, 20], hit only in oldest game
    recent_hit = get_true_prob([20, 5, 5, 5, 5, 5, 5, 5, 5, 5], K=15.5)
    old_hit = get_true_prob([5, 5, 5, 5, 5, 5, 5, 5, 5, 20], K=15.5)
    assert recent_hit > old_hit


def test_get_true_prob_between_zero_and_one():
    stat_list = [20, 10, 25, 8, 18, 12, 22, 9, 16, 11]
    result = get_true_prob(stat_list, K=15.5)
    assert 0 <= result <= 1
