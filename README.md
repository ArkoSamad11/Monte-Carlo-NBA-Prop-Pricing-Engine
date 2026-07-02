# PropVol: Monte Carlo NBA Player Prop Pricing Engine
## Motivation
* Evaluating markets’ prop lines and odds for individual players is difficult without any readily available research. Thus, bettors do not know the player’s recent performance and how it may affect the line or where to place their confidence. PropVol is a platform that aims to bridge the gap between bettors and sportsbooks and prediction markets.
## Modeling Approach
* Initially, this project's foundation was the Black-Scholes model; however, after coding and testing to predict props, the implementation proved impractical. The model assumed all stats were modeled with a log-normal distribution, which was not the case, and this took away from the model's accuracy.
* A common approach to predicting the likelihood of various outcomes is Monte Carlo simulation, a vital part of the platform's engine. The algorithm simulates a specific probability distribution, which depends on the statistic being evaluated.
* For points, the platform applies a Monte Carlo simulation using either a Normal or a Log-Normal distribution. Although points are technically discrete integers, their relatively high volume and wide range of outcomes allow them to be accurately approximated by continuous distributions. A Log-Normal distribution is applied if the player is not consistent (CV > 0.5) relative to their L10 average, indicating high relative variability and a right-skewed scoring distribution. Otherwise, a Normal distribution is used to model scoring outcomes that are more symmetrically distributed around the player's average.
* As for other stats on the platform, including rebounds, assists, steals, blocks, threes, and turnovers, the service applies a Monte Carlo simulation using either a Negative Binomial or a Poisson distribution. These statistics often exhibit count-based distributions, where the probability mass at each individual value is important for prop line evaluation.
* To decide between a Negative Binomial distribution and a Poisson distribution, the algorithm calculates the variance of the player's stat and compares it to the average for that stat over the last 10 games. When the variance exceeds the mean, the data is considered overdispersed, so a Negative Binomial distribution is used instead. Otherwise, the algorithm applies a Poisson distribution.
## Scale
* Since the platform's deployment in late May, 622 player props have been recorded. These player props were split between 317 DraftKings (sportsbook) and 305 Kalshi (prediction market) props. All markets were live during the playoffs: the Western Conference Finals, the Eastern Conference Finals, and the NBA Finals.
<p align="center">
  <img width="350" src="https://github.com/user-attachments/assets/61e53bf4-8cf1-4210-b1bc-49f25c1f98cf" />  <-sample display for a player prop
  <img width="350" src="https://github.com/user-attachments/assets/c1653b5d-a69e-40be-9542-d6f8ce24f1cd" /> * sample monte carlo sim. from test-> 
</p>


## Performance Metrics
* Across the 622 live markets analyzed, the model correctly predicted 55.6% props. Of the 317 DraftKings markets, 55.5% of predictions were correct. Meanwhile, 55.7% of the 305 Kalshi markets were correctly predicted.
* Based on empirical observations and game film, adjustments were made to the model after 221 props. In the WCF, varying game plans for players such as Shai Gilgeous-Alexander and Victor Wembanyama motivated the introduction of a PACE factor, a DRTG factor, and a weighting factor to split impact 60%/40 between the last 10 and last 3 game stats, which affected the mean when performing Monte Carlo simulations.
* Before the weighting adjustment, the model recorded 49.5% accuracy across 95 props (id < 221). The 622 props reported above reflect post-weighting performance only.
* $$SE_{null} = \sqrt{\frac{p_0 \times (1 - p_0)}{n}} = \sqrt{\frac{0.50 \times 0.50}{622}} = \sqrt{\frac{0.25}{622}} \approx 0.02005$$. $$Z = \frac{p - p_0}{SE_{null}} = \frac{0.556 - 0.500}{0.02005} \approx \mathbf{2.79}$$. $p \approx \mathbf{0.0026}$.
* $$SE_{sample} = \sqrt{\frac{p \times (1 - p)}{n}} = \sqrt{\frac{0.556 \times 0.444}{622}} \approx 0.01992$$. $$ME = 1.96 \times SE_{sample} = 1.96 \times 0.01992 \approx \mathbf{0.0390}$$. $$CI = $$[51.7\%, 59.5\%]

**WORK IN PROGRESS!**
