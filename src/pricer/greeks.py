# imports required for calculations of greeks
from src.pricer.black_scholes import d1, d2
from scipy.stats import norm
import numpy as np

# S represents rolling average for stat
# theoretical change in over bet value when S moves by 1
def call_delta(S, K, sigma, T = 1/365, r = 0):
    return norm.cdf(d1(S, K, sigma, T, r))


# theoretical change in under bet value when S moves by 1
def put_delta(S, K, sigma, T = 1/365, r = 0):
    return norm.cdf(d1(S, K, sigma, T, r)) - 1


# theoretical change in delta when S moves by 1
def gamma(S, K, sigma, T = 1/365, r = 0):
    return (norm.pdf(d1(S, K, sigma, T, r))) / (S * sigma * np.sqrt(T))


# theoretical change in O/U value when volatility changes by .01
def vega(S, K, sigma, T = 1/365, r = 0):
    return (S * np.sqrt(T) * norm.pdf(d1(S, K, sigma, T, r)))


# theoretical price change per day --> slightly irrelevant because T = 1/365 for practically all bets
def call_theta(S, K, sigma, T = 1/365, r = 0):
    return ((-S * norm.pdf(d1(S, K, sigma, T, r)) * sigma) / (2 * np.sqrt(T))) - (r * K * np.exp(-r * T) * norm.cdf(d2(S, K, sigma, T, r)))


def put_theta(S, K, sigma, T = 1/365, r = 0):
    return ((-S * norm.pdf(d1(S, K, sigma, T, r)) * sigma) / (2 * np.sqrt(T))) + (r * K * np.exp(-r * T) * norm.cdf(-(d2(S, K, sigma, T, r))))


# theoretical price change with risk free rate --> time to maturity is negligible, 48 minute games 
def call_rho(S, K, sigma, T = 1/365, r=0):
    return (K * T * np.exp(-r * T) * norm.cdf(d2(S, K, sigma, T, r)))

def put_rho(S, K, sigma, T = 1/365, r=0):
    return (-K * T * np.exp(-r * T) * norm.cdf(-d2(S, K, sigma, T, r)))

# function wrapper
def greeks(S, K, sigma, T = 1/365, r = 0):
        return {'call delta': call_delta(S, K, sigma, T, r), 'put delta': put_delta(S, K, sigma, T, r), 
            'gamma': gamma(S, K, sigma, T, r), 
            'vega': vega(S, K, sigma, T, r), 
            'call_theta': call_theta(S, K, sigma, T, r), 'put_theta': put_theta(S, K, sigma, T,r), 
            'call_rho': call_rho(S, K, sigma, T,r), 'put_rho': put_rho(S, K, sigma, T, r)}
