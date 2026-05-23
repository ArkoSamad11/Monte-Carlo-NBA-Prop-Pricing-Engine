# imports
import numpy as np
from scipy.stats import norm

def d1(S, K, sigma, T=1/82, r=0):
    if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
        raise ValueError("S, K, sigma, and T must be positive")
    return (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))

def d2(S, K, sigma, T=1/82, r=0):
    return d1(S, K, sigma, T, r) - sigma * np.sqrt(T)

def call(S, K, sigma, T=1/82, r=0):
    return float(S * norm.cdf(d1(S, K, sigma, T, r)) - K * np.exp(-r*T) * norm.cdf(d2(S, K, sigma, T, r)))

def put(S, K, sigma, T=1/82, r=0):
    return float(K * np.exp(-r*T) * norm.cdf(-d2(S, K, sigma, T, r)) - S * norm.cdf(-d1(S, K, sigma, T, r)))

def black_scholes(S, K, sigma, T=1/82, r=0):
<<<<<<< HEAD
    return call(S, K, sigma, T, r), put(S, K, sigma, T, r)
=======
    return call(S, K, sigma, T, r), put(S, K, sigma, T, r)
>>>>>>> 4ebe7d745d0e4970ddf29786bc1a0d1bc8d07616
