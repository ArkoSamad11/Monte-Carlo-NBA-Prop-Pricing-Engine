from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import teamgamelogs
import pandas as pd
import time

NBA_API_TIMEOUT = 60
NBA_API_DELAY = 1.0


def get_id(PlayerFullName):
    playerdict = players.find_players_by_full_name(PlayerFullName)
    return playerdict[0]['id']


def get_stats(PlayerFullName, season):
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
            time.sleep(5)


def stat_information(PlayerFullName, season, stat_category):
    stat_category = stat_category.lower().replace(' ', '')
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
    team_name = team_name.lower()
    return df[
    df['TEAM_NAME'].str.lower().str.contains(team_name, na=False)
    ].copy()


def _recent_team_average(df, team_name, n_games=10):
    team_df = _find_team_rows(df, team_name)
    if team_df.empty:
        return None
    team_df = team_df.sort_values('GAME_DATE', ascending=False).head(n_games)
    return {
    'pace': team_df['PACE'].mean(),
    'def_rating': team_df['DEF_RATING'].mean(),
    'games_used': len(team_df)
    }


def get_team_stats(team_name, opponent_team_name, season):
    try:
        regular_df = _fetch_team_logs(season, 'Regular Season')
        playoff_df = _fetch_team_logs(season, 'Playoffs')
        df = pd.concat([regular_df, playoff_df], ignore_index=True)
        if df.empty:
            return 98.5, 98.5, 113.0, 113.0
        df = df.sort_values('GAME_DATE', ascending=False)
        team_l10 = _recent_team_average(df, team_name, n_games=10)
        team_l3 = _recent_team_average(df, team_name, n_games=3)
        opponent_l10 = _recent_team_average(df, opponent_team_name, n_games=10)
        opponent_l3 = _recent_team_average(df, opponent_team_name, n_games=3)
        league_recent = (
            df.sort_values('GAME_DATE', ascending=False)
            .groupby('TEAM_NAME')
            .head(10)
        )
        league_recent_l3 = (
            df.sort_values('GAME_DATE', ascending=False)
            .groupby('TEAM_NAME')
            .head(3)
        )
        league_avg_pace_l10 = league_recent['PACE'].mean()
        league_avg_pace_l3 = league_recent_l3['PACE'].mean()
        league_avg_def_l10 = league_recent['DEF_RATING'].mean()
        league_avg_def_l3 = league_recent_l3['DEF_RATING'].mean()
        league_avg_pace = 0.60 * league_avg_pace_l10 + 0.40 * league_avg_pace_l3
        league_avg_def_rating = 0.60 * league_avg_def_l10 + 0.40 * league_avg_def_l3
        if team_l10 is None:
            team_pace_l10 = league_avg_pace_l10
        else:
            team_pace_l10 = team_l10['pace']
        if team_l3 is None:
            team_pace_l3 = league_avg_pace_l3
        else:
            team_pace_l3 = team_l3['pace']

        if opponent_l10 is None:
            opponent_def_l10 = league_avg_def_l10
        else:
            opponent_def_l10 = opponent_l10['def_rating']
        if opponent_l3 is None:
            opponent_def_l3 = league_avg_def_l3
        else:
            opponent_def_l3 = opponent_l3['def_rating']
        team_pace = 0.60 * team_pace_l10 + 0.40 * team_pace_l3
        opponent_def_rating = 0.60 * opponent_def_l10 + 0.40 * opponent_def_l3
        return team_pace, league_avg_pace, opponent_def_rating, league_avg_def_rating
    except Exception:
        return 98.5, 98.5, 113.0, 113.0


def get_context_factors(team_name, opponent_team_name, season, stat_category):
    team_pace, league_avg_pace, opponent_def_rating, league_avg_def_rating = get_team_stats(
        team_name, opponent_team_name, season
    )
    pace_factor = team_pace / league_avg_pace
    if stat_category in ['points', 'threes', 'assists']:
        def_factor = opponent_def_rating / league_avg_def_rating
    else:
        def_factor = 1.0
    return pace_factor, def_factor