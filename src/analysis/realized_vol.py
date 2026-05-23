import numpy as np

def find_sigma(stat_list):
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