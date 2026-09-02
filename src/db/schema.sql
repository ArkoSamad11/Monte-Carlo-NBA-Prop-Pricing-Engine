-- Stores raw prop lines and market odds fetched from the Odds API.
CREATE TABLE player_props(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255),
    stat_category VARCHAR(255),
    prop_line FLOAT,
    over_odds INT,
    under_odds INT,
    event_id VARCHAR(255),
    time_stamp TIMESTAMP DEFAULT NOW()
);

-- Primary signal store. One record is written per detected mispricing signal
-- when the user clicks 'Find Mispricing' in the dashboard. Used for accuracy
-- tracking, calibration analysis, and model evaluation across live playoff markets.
CREATE TABLE mispricing_signal(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255),
    stat_category VARCHAR(255),
    prop_line FLOAT,
    side VARCHAR(255),               -- 'over' or 'under', the flagged side
    implied_vol_over FLOAT,          
    implied_vol_under FLOAT,         
    realized_vol FLOAT,
    gap FLOAT,                       -- gap betwen monte carlo and market probability
    direction VARCHAR(255),          -- 'underpriced' or 'overpriced'
    time_stamp TIMESTAMP DEFAULT NOW(),
    bookmaker VARCHAR(255),          -- 'DraftKings' or 'Kalshi'
    mc_prob FLOAT,                   -- Monte Carlo probability for the flagged side
    empirical_prob FLOAT,            -- Weighted empirical probability for the flagged side
    confidence VARCHAR(255),         -- 'high' or 'moderate'
    is_primary BOOLEAN,              -- True for the first logged signal per player/stat/bookmaker/date
    outcome VARCHAR(255),            -- 'correct', 'incorrect', or 'invalid' (if player did not meet minutes requirement
    actual_stat FLOAT                -- Actual stat value recorded post-game for outcome evaluation
);

-- Stores individual player game log entries for historical reference.
-- Not actively written to in the current pipeline, the stat data is fetched
-- live from the NBA Stats API on each request via cached_stat_information.
CREATE TABLE game_logs(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255),
    season VARCHAR(255),
    stat_category VARCHAR(255),
    game_date TIMESTAMP,
    stat_value FLOAT,
    time_stamp TIMESTAMP DEFAULT NOW()
);

-- Anonymous usage tracking. One row per tracked dashboard interaction.
-- 'session_id' is a random UUID minted by the Streamlit dashboard once per browser
-- session and sent with each request. It contains no personal information and is
-- never derived from IP address, user agent, or any other fingerprint.
--
-- IMPORTANT: this counts SESSIONS, not people. Streamlit session state resets when
-- the browser tab closes or the app sleeps, so one person across five game nights
-- registers as five sessions. Report the number as distinct sessions.
CREATE TABLE IF NOT EXISTS usage_events(
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    event VARCHAR(64) NOT NULL,      -- 'session_start' or 'price_request'
    player VARCHAR(255),
    stat VARCHAR(255),
    bookmaker VARCHAR(255),
    time_stamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_session ON usage_events (session_id, time_stamp);
CREATE INDEX IF NOT EXISTS idx_usage_event ON usage_events (event, time_stamp);
