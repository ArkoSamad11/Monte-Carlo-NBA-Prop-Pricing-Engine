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

CREATE TABLE mispricing_signal(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255), 
    stat_category VARCHAR(255),
    prop_line FLOAT,
    side VARCHAR(255),
    implied_vol_over FLOAT,
    implied_vol_under FLOAT,
    realized_vol FLOAT,
    gap FLOAT,
    direction VARCHAR(255),
    time_stamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE game_logs(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255),
    season VARCHAR(255),
    stat_category VARCHAR(255),
    game_date TIMESTAMP, 
    stat_value FLOAT,
    time_stamp TIMESTAMP DEFAULT NOW()
);
=======
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

CREATE TABLE mispricing_signal(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255), 
    stat_category VARCHAR(255),
    prop_line FLOAT,
    side VARCHAR(255),
    implied_vol_over FLOAT,
    implied_vol_under FLOAT,
    realized_vol FLOAT,
    gap FLOAT,
    direction VARCHAR(255),
    time_stamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE game_logs(
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255),
    season VARCHAR(255),
    stat_category VARCHAR(255),
    game_date TIMESTAMP, 
    stat_value FLOAT,
    time_stamp TIMESTAMP DEFAULT NOW()
);
>>>>>>> 4ebe7d745d0e4970ddf29786bc1a0d1bc8d07616
