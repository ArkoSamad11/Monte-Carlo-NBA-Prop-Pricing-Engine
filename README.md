Service Link (NO GAMES AS OF 8/11/26):
https://monte-carlo-nba-prop-pricing-engine-z6w7sprmxzddv45rnzq6y5.streamlit.app/

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
* Observed accuracy: 55.6% (622 markets)
* Calibration Analysis: Model best reflects true probability when the displayed bet probability is in the range 60-65%. The difference between the actual average win rate and predicted average win rate is 0.8%. Percentages below and above this bucket, the model typically is primarily overconfident.

Null hypothesis: p = 0.50

Z-statistic: 2.79

p-value (one-tailed): 0.0026

95% CI: [51.7%, 59.5%]

## System Architecture
```
NBA Stats API
     ↓
     
Data Ingestion (nba_api, scheduled ETL)
     ↓
     
PostgreSQL Warehouse (historical player logs, pace metrics)
     ↓
     
Feature Engineering (pace-adjusted rates, rolling averages, matchup splits)
     ↓
     
Distribution Fitting (Log-Normal: points; Negative Binomial: assists, rebounds)
     ↓
     
Monte Carlo Simulation (10,000 iterations per prop)
     ↓
     
Probability Estimation (P(stat > line) from simulation output)
     ↓
     
Kelly Criterion Sizing (f* = (bp - q) / b on user-inputted odds)
     ↓
     
Streamlit Dashboard (FastAPI backend, real-time output)
```
## Project Structure

```
Monte-Carlo-NBA-Prop-Pricing-Engine/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI endpoints, signal logging, caching
│   ├── analysis/
│   │   ├── implied_vol.py       # Monte Carlo engine, probability estimation
│   │   ├── mispricing.py        # Edge detection, confidence tiering
│   │   └── realized_vol.py      # Log-return volatility calculation
│   ├── data/
│   │   ├── nba_client.py        # NBA Stats API data ingestion
│   │   └── odds_client.py       # Odds API integration
│   ├── pricer/
│   │   ├── black_scholes.py     # Research foundation (not in live pipeline)
│   │   ├── greeks.py            # Research foundation (not in live pipeline)
│   │   └── newton_raphson.py    # Research foundation (not in live pipeline)
│   └── db/
│       └── schema.sql           # PostgreSQL schema
├── tests/
│   ├── test_black_scholes.py
│   ├── test_greeks.py
│   ├── test_newton_raphson.py
│   └── test_realized_vol.py
├── app.py                       # Streamlit dashboard
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── Procfile                     # Railway deployment
└── pytest.ini
```

## Installation

### Prerequisites
- Python 3.11
- PostgreSQL
- Docker (optional)

### Environment Variables
Create a `.env` file in the repo root:

POSTGRES_USER=your_user

POSTGRES_PASSWORD=your_password

ODDS_API_KEY=your_key (Part of original idea, not a part of platform's function)

DATABASE_URL=postgresql://localhost/propvol (optional, defaults to this value)

USAGE_ADMIN_TOKEN=any_long_random_string (optional, enables the /usage_stats endpoint)
### Local Setup
```bash
git clone https://github.com/ArkoSamad11/Monte-Carlo-NBA-Prop-Pricing-Engine.git
cd Monte-Carlo-NBA-Prop-Pricing-Engine
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8001
streamlit run app.py
```

Dashboard available at `http://localhost:8501`.

### Docker
```bash
docker-compose up --build
```

Dashboard available at `http://localhost:8501`.
## Testing

```bash
pytest
```

Coverage report:

```bash
pytest --cov=src/pricer --cov=src/analysis/realized_vol --cov-report=term-missing
```

48 tests across Black-Scholes, Greeks, Newton-Raphson, and realized volatility modules. 96% coverage. CI runs on every push via GitHub Actions.

## Usage

### Local
Start the API first:
```bash
uvicorn src.api.main:app --reload --port 8001
```

Then start the dashboard:
```bash
streamlit run app.py
```

Dashboard: `http://localhost:8501`
API docs: `http://localhost:8001/docs`

### Docker
```bash
docker-compose up --build
```

Dashboard: `http://localhost:8501`

### Using the Dashboard
1. Select a game from the dropdown
2. Select a player
3. Select a stat category
4. Enter the prop line and odds from your sportsbook or prediction market
5. Click **Find Mispricing**
6. Review the Monte Carlo probability, empirical probability, market probability, edge gap, confidence tier, and Kelly Criterion sizing
## Usage Tracking

The dashboard records anonymous usage so adoption can be measured rather than estimated.

**What is collected.** A random UUID is minted once per browser session and sent with each request. Two events are written to the `usage_events` table: `session_start` when a session opens the dashboard, and `price_request` when a prop is submitted for analysis, along with the player, stat, and bookmaker requested. No IP addresses, user agents, or fingerprints are collected or derived.

**What the number means.** This counts **distinct sessions, not distinct people.** Streamlit clears session state when the browser tab closes or when a hosted app sleeps, so one person visiting on five game nights registers as five sessions. The honest way to report it is `N pricing requests across M sessions`. Deriving a headcount from IP or user-agent fingerprints is the alternative and is deliberately not implemented.

Tracking is fail-safe by design: if the database is unreachable the writes are logged and swallowed, so a tracking outage can never break prop analysis.

### Viewing the numbers

The table is created automatically on API startup. For an existing database it can also be created manually:

```bash
psql $DATABASE_URL -f src/db/schema.sql
```

**Option 1, command line.** Reads the database directly, works against local or hosted Postgres:

```bash
python scripts/usage_report.py
```

Against a hosted database, point it at the deployment:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/propvol python scripts/usage_report.py
```

Output includes distinct sessions, sessions that actually priced a prop, total pricing requests, active days, a per-day breakdown, and the most requested players and stats.

**Option 2, API endpoint.** Set `USAGE_ADMIN_TOKEN` in the environment, then:

```bash
curl -H "X-Admin-Token: $USAGE_ADMIN_TOKEN" http://localhost:8001/usage_stats
```

The endpoint returns `404` when `USAGE_ADMIN_TOKEN` is unset and `401` on a bad token, so usage data is never publicly readable.

**Option 3, raw SQL.**

```sql
SELECT COUNT(DISTINCT session_id) AS sessions,
       COUNT(*) FILTER (WHERE event = 'price_request') AS price_requests
FROM usage_events;
```

## Limitations

- Model parameters derived from L10 rolling window only
- No injury, rest, or travel adjustment 
- Calibration analysis in Performance Metrics alludes to reduction in Kelly Sizing in buckets outside of 60-65%
- Playoff-only evaluation sample (Conference Finals and Finals), performance on regular season markets is untested
- Odds API integration removed from live product
- Usage tracking measures distinct browser sessions, not distinct people, and only covers activity after it was instrumented

## License
MIT
