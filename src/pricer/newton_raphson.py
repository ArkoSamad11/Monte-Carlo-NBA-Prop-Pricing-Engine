import numpy as np
from src.pricer.black_scholes import call, put
from src.pricer.greeks import vega


def newton_raphson_iv(market_price, S, K, T=1/82, r=0, option_type='call', tol=1e-6, max_iter=1000):
    sigma = 0.5
    i = 0

    while i < max_iter:
        if option_type == 'call':
            price = call(S, K, sigma, T, r)
        else:
            price = put(S, K, sigma, T, r)

        v = vega(S, K, sigma, T, r)

        if v < 1e-10:
            return None

        diff = price - market_price

        if abs(diff) < tol:
            return sigma

        sigma = sigma - diff / v

        if sigma <= 0:
            sigma = 1e-4

        i += 1

    return None
