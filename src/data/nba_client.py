from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import teamgamelogs
import pandas as pd
import time

# Maximum seconds to wait for a response from the NBA Stats API before timing out
NBA_API_TIMEOUT = 60

# Delay in seconds between consecutive NBA Stats API calls to avoid rate limiting.
NBA_API_DELAY = 1.0


def get_id(PlayerFullName):
    """
    Returns the NBA Stats API player ID for a given player's full name.

    Args:
        PlayerFullName: Full name of the player as it appears in the NBA Stats API (String).

    Returns:
        An integer representing the player's unique NBA Stats API ID.
    """
    playerdict = players.find_players_by_full_name(PlayerFullName)
    return playerdict[0]['id']


def get_stats(PlayerFullName, season):
    """
    Fetches the player's most recent qualifying last 10 game logs from the NBA Stats API,
    Games where the player recorded fewer than 20 or more than 48 minutes are excluded.

    Args:
        PlayerFullName: Full name of the player as it appears in the NBA Stats API (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).

    Returns:
        A DataFrame of up to 10 qualifying games containing columns:
        PTS, REB, AST, STL, BLK, FG3M/3PM, TOV. Ordered most-recent-first.
    """
    for attempt in range(3):
        try:
            time.sleep(NBA_API_DELAY)
            reg_gamelog = playergamelog.PlayerGameLog(
                player_id=get_id(PlayerFullName),
                season=season,
                season_type_all_star='Regular Season',
                timeout=NBA_API_TIMEOUT
            )
            time.sleep(NBA_API_DELAY)
            playoff_gamelog = playergamelog.PlayerGameLog(
                player_id=get_id(PlayerFullName),
                season=season,
                season_type_all_star='Playoffs',
                timeout=NBA_API_TIMEOUT
            )
            df_reg = reg_gamelog.get_data_frames()[0]
            df_playoffs = playoff_gamelog.get_data_frames()[0]
            df_combined = pd.concat([df_playoffs, df_reg])
            df_combined['MIN'] = pd.to_numeric(df_combined['MIN'], errors='coerce')
            df_combined = df_combined[(df_combined['MIN'] >= 20) & (df_combined['MIN'] <= 48)]
            df_combined = df_combined.iloc[:10]
            return df_combined[['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TOV']]
        except Exception:
            if attempt == 2:
                raise
            # Wait before retrying to avoid compounding rate limit issues.
            time.sleep(5)


def stat_information(PlayerFullName, season, stat_category):
    """
    Returns the player's last 10 qualifying game values for a specific stat category.
    Wraps get_stats and maps the user-facing stat category string to the corresponding
    NBA Stats API column name.

    Args:
        PlayerFullName: Full name of the player as it appears in the NBA Stats API (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop. Must be one of:
                       'points', 'rebounds', 'assists', 'steals', 'blocks', 'threes', 'turnovers' (String).
    Returns:
        A list of up to 10 floats representing the player's most recent qualifying
        game values for the selected stat, ordered most-recent-first.

    Raises:
        ValueError: If stat_category is not one of the seven supported categories.
    """
    # Normalize input to handle varied casing or spacing from the dashboard.
    stat_category = stat_category.lower().replace(' ', '')
    # Maps user-facing stat category names to NBA Stats API DataFrame column names.
    stat_map = {
        'points': 'PTS',
        'rebounds': 'REB',
        'assists': 'AST',
        'steals': 'STL',
        'blocks': 'BLK',
        'threes': 'FG3M',
        'turnovers': 'TOV'
    }
    if stat_category not in stat_map:
        raise ValueError('Only categories are points, rebounds, assists, steals, blocks, threes, or turnovers.')
    return get_stats(PlayerFullName, season)[stat_map[stat_category]].tolist()


def _fetch_team_logs(season, season_type):
    """
    Fetches advanced team game logs from the NBA Stats API for a given season and season type.

    Args:
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).
        season_type: Either 'Playoffs' or 'Regular Season' (String).
    Returns:
        A DataFrame of advanced team game logs with a SEASON_TYPE column appended
        to identify the source after concatenation. Returns an empty DataFrame if
        the API returns no data for the given season and season type.
    """
    logs = teamgamelogs.TeamGameLogs(
        season_nullable=season,
        season_type_nullable=season_type,
        measure_type_player_game_logs_nullable='Advanced'
    )
    df = logs.get_data_frames()[0]
    if df.empty:
        return df
    df['SEASON_TYPE'] = season_type
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    return df


def _find_team_rows(df, team_name):
    """
    Filters a team game log DataFrame to rows matching the given team name.

    Args:
        df: DataFrame of team game logs returned by _fetch_team_logs (DataFrame).
        team_name: Full or partial team name to filter by (String).
    Returns:
        A copy of the filtered DataFrame containing only rows where TEAM_NAME
        matches the given team name. Returns an empty DataFrame if no match is found.
    """
    # Normalize to lowercase for case-insensitive matching
    team_name = team_name.lower()
    return df[df['TEAM_NAME'].str.lower().str.contains(team_name, na=False)].copy()


def _recent_team_average(df, team_name, n_games=10):
    """
    Computes the average pace and defensive rating for a team over their most recent games.

    Args:
        df: DataFrame of team game logs returned by _fetch_team_logs (DataFrame).
        team_name: Full or partial team name to filter by (String).
        n_games: Number of most recent games to average over. Defaults to 10 (Integer).

    Returns:
        A dictionary containing:
            pace: Average team pace over the n_games window (Float).
            def_rating: Average defensive rating over the n_games window (Float).
            games_used: Actual number of games used in the average, which may be
                        less than n_games if fewer qualifying games are available (Integer).
        Returns None if no matching team rows are found in the DataFrame.
    """
    team_df = _find_team_rows(df, team_name)
    if team_df.empty:
        return None
    # Sort descending by date and take the n most recent games.
    team_df = team_df.sort_values('GAME_DATE', ascending=False).head(n_games)
    return {'pace': team_df['PACE'].mean(), 'def_rating': team_df['DEF_RATING'].mean(), 'games_used': len(team_df)}


def get_team_stats(team_name, opponent_team_name, season):
    """
    Fetches and computes weighted pace and defensive rating for the player's team
    and the opponent team, alongside league averages, used to contextually adjust
    the player's expected stat output in get_context_factors.

    Both team and league averages are computed using a weighted blend of
    the L10 and L3 rolling windows.

    Args:
        team_name: Full or partial name of the player's team (String).
        opponent_team_name: Full or partial name of the opponent team (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).

    Returns:
        A tuple of four floats:
            team_pace: Weighted average pace for the player's team (Float).
            league_avg_pace: Weighted average pace across all teams (Float).
            opponent_def_rating: Weighted average defensive rating for the opponent (Float).
            league_avg_def_rating: Weighted average defensive rating across all teams (Float).
        Returns (98.5, 98.5, 113.0, 113.0) as neutral fallback defaults if the API
        call fails or returns no data — these approximate league averages ensure
        pace_factor and def_factor compute to approximately 1.0, leaving the
        player's expected output unadjusted rather than distorting it with
        erroneous values.
    """
    try:
        regular_df = _fetch_team_logs(season, 'Regular Season')
        playoff_df = _fetch_team_logs(season, 'Playoffs')

        # Combine both season types (if playoffs applicable) into one DataFrame for unified rolling averages.
        df = pd.concat([regular_df, playoff_df], ignore_index=True)

        if df.empty:
            return 98.5, 98.5, 113.0, 113.0

        df = df.sort_values('GAME_DATE', ascending=False)

        # Compute L10 and L3 rolling averages for the player's team.
        team_l10 = _recent_team_average(df, team_name, n_games=10)
        team_l3 = _recent_team_average(df, team_name, n_games=3)

        # Compute L10 and L3 rolling averages for the opponent team.
        opponent_l10 = _recent_team_average(df, opponent_team_name, n_games=10)
        opponent_l3 = _recent_team_average(df, opponent_team_name, n_games=3)

        # Compute league-wide averages by taking the L10 and L3 for every team
        # and averaging across all of them.
        league_recent = (df.sort_values('GAME_DATE', ascending=False).groupby('TEAM_NAME').head(10))
        league_recent_l3 = (df.sort_values('GAME_DATE', ascending=False).groupby('TEAM_NAME').head(3))

        league_avg_pace_l10 = league_recent['PACE'].mean()
        league_avg_pace_l3 = league_recent_l3['PACE'].mean()
        league_avg_def_l10 = league_recent['DEF_RATING'].mean()
        league_avg_def_l3 = league_recent_l3['DEF_RATING'].mean()

        # weighted blend of L10 and L3 for league averages.
        league_avg_pace = 0.60 * league_avg_pace_l10 + 0.40 * league_avg_pace_l3
        league_avg_def_rating = 0.60 * league_avg_def_l10 + 0.40 * league_avg_def_l3

        # Fall back to league average if team-specific data is unavailable.
        team_pace_l10 = team_l10['pace'] if team_l10 is not None else league_avg_pace_l10
        team_pace_l3 = team_l3['pace'] if team_l3 is not None else league_avg_pace_l3
        opponent_def_l10 = opponent_l10['def_rating'] if opponent_l10 is not None else league_avg_def_l10
        opponent_def_l3 = opponent_l3['def_rating'] if opponent_l3 is not None else league_avg_def_l3

        # weighted blend of L10 and L3 for team-specific values.
        team_pace = 0.60 * team_pace_l10 + 0.40 * team_pace_l3
        opponent_def_rating = 0.60 * opponent_def_l10 + 0.40 * opponent_def_l3

        return team_pace, league_avg_pace, opponent_def_rating, league_avg_def_rating

    except Exception:
        # Return neutral fallback defaults on any API failure. Values approximate
        # league averages so pace_factor and def_factor compute to approximately
        # 1.0, leaving the player's expected output unadjusted.
        return 98.5, 98.5, 113.0, 113.0


def get_context_factors(team_name, opponent_team_name, season, stat_category):
    """
    Computes pace and defensive context multipliers used to adjust a player's
    expected stat output for tonight's specific matchup.

    Args:
        team_name: Full or partial name of the player's team (String).
        opponent_team_name: Full or partial name of the opponent team (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop. Determines whether
                       def_factor is applied or defaulted to 1.0 (String).
    Returns:
        A tuple of two floats:
            pace_factor: Ratio of the player's team pace to league average pace.
                         > 1.0 means faster than league average
                         < 1.0 means slower than league average (Float).
            def_factor: Ratio of the opponent's defensive rating to league average
                        defensive rating. > 1.0 means a weaker than average defense
                        (player's expected output scaled up). < 1.0 means a stronger
                        than average defense (player's expected output scaled down).
                        Only applied for points, threes, and assists. Defaults to 1.0
                        for all other stat categories since defensive rating measures
                        points allowed per 100 possessions and does not reliably
                        predict suppression of rebounds, steals, blocks, or turnovers (Float).
    """
    team_pace, league_avg_pace, opponent_def_rating, league_avg_def_rating = get_team_stats(team_name, opponent_team_name, season)
    pace_factor = team_pace / league_avg_pace
    if stat_category in ['points', 'threes', 'assists']:
        def_factor = opponent_def_rating / league_avg_def_rating
    else:
        def_factor = 1.0

    return pace_factor, def_factor
