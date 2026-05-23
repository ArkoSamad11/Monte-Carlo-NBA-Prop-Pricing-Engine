from src.data.nba_client import stat_information as stat_info, get_context_factors
from src.analysis.realized_vol import find_sigma
from src.data.odds_client import american_to_implied, remove_vigorish
import numpy as np
from scipy.stats import nbinom


def monte_carlo_prob(stat_list, K, stat_category, n_simulations=10000, pace_factor=1.0, def_factor=1.0):
    stat_array = np.array(stat_list, dtype=float)
    mu_raw = np.mean(stat_array)
    sigma = np.std(stat_array)
    mu = mu_raw * pace_factor * def_factor

    if sigma == 0:
        return (1.0 if mu > K else 0.0), np.full(n_simulations, mu).tolist()

    variance = sigma ** 2

    if stat_category in ['rebounds', 'assists', 'steals', 'blocks', 'threes', 'turnovers']:
        if variance > mu:
            r = (mu ** 2) / (variance - mu)
            p = mu / variance
            simulations = nbinom.rvs(r, p, size=n_simulations)
        else:
            simulations = np.random.poisson(mu, size=n_simulations)
    else:
        cv = sigma / mu_raw if mu_raw > 0 else 1.0
        if cv < 0.5:
            simulations = np.random.normal(mu, sigma, n_simulations)
            simulations = np.clip(simulations, 0, None)
        else:
            simulations = np.random.lognormal(
                mean=np.log(mu ** 2 / np.sqrt(variance + mu ** 2)),
                sigma=np.sqrt(np.log(1 + variance / mu ** 2)),
                size=n_simulations
            )

    prob_over = float(np.sum(simulations > K) / n_simulations)
    return prob_over, simulations.tolist()


def get_true_prob(stat_list, K):
    weights = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    weighted_sum = 0
    total_weight = 0
    if len(stat_list) == 0:
        return 0.0
    for i in range(len(stat_list)):
        weight = weights[i]
        if stat_list[i] > K:
            weighted_sum += weight
        total_weight += weight
    return weighted_sum / total_weight


def find_impliedvol(player_name, season, stat_category, prop, player_team=None, opponent_team=None):
    stat_list = stat_info(player_name, season, stat_category)
    realized_vol = find_sigma(stat_list)
    S = sum(stat_list) / len(stat_list)
    K = prop['line']
    over_odds = prop['over_odds']
    under_odds = prop['under_odds']
    implied_over = american_to_implied(over_odds)
    implied_under = american_to_implied(under_odds)
    fair_over, fair_under = remove_vigorish(implied_over, implied_under)

    pace_factor = 1.0
    def_factor = 1.0

    if player_team and opponent_team:
        pace_factor, def_factor = get_context_factors(
            player_team, opponent_team, season, stat_category
        )

    mc_prob_over, simulations = monte_carlo_prob(
        stat_list, K, stat_category,
        pace_factor=pace_factor,
        def_factor=def_factor
    )
    mc_prob_under = 1 - mc_prob_over
    empirical_prob_over = get_true_prob(stat_list, K)
    empirical_prob_under = 1 - empirical_prob_over

    return mc_prob_over, mc_prob_under, empirical_prob_over, empirical_prob_under, fair_over, fair_under, realized_vol, S, K, simulations