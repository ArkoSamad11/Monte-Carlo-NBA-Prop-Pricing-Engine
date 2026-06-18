import numpy as np


def find_sigma(stat_list):
    """
    Finds the log return standard deviation for the selected player and stat L10 qualified games

    Args:
        stat_list: An array of up to 10 integers representing the player's most recent
                   qualifying game values for the selected stat, ordered most-recent-first (List).

    Returns:
            A float representing the log return standard deviation of the player's recent
            qualifying games for the selected stat. Returns 0.0 if the stat list contains
            fewer than 2 values or if the computation produces NaN.
    """
    if len(stat_list) < 2:
        return 0.0
    stat_array = np.array(stat_list, dtype=float)
    for i in range(len(stat_array)):
        if stat_array[i] == 0:
            stat_array[i] = 0.01
    log_returns = np.log(stat_array[:-1] / stat_array[1:])
    sigma = np.std(log_returns)
    if np.isnan(sigma):
        return 0.0
    return float(sigma)
