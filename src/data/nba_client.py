from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import leaguedashteamstats
import pandas as pd


def get_id(PlayerFullName):
    playerdict = players.find_players_by_full_name(PlayerFullName)
    return playerdict[0]['id']


def get_stats(PlayerFullName, season):
    reg_gamelog = playergamelog.PlayerGameLog(
        player_id=get_id(PlayerFullName),
        season=season,
        season_type_all_star='Regular Season'
    )
    playoff_gamelog = playergamelog.PlayerGameLog(
        player_id=get_id(PlayerFullName),
        season=season,
        season_type_all_star='Playoffs'
    )
    df_reg = reg_gamelog.get_data_frames()[0]
    df_playoffs = playoff_gamelog.get_data_frames()[0]
    df_combined = pd.concat([df_playoffs, df_reg])
    df_combined['MIN'] = pd.to_numeric(df_combined['MIN'], errors='coerce')
    df_combined = df_combined[(df_combined['MIN'] >= 20) & (df_combined['MIN'] <= 48)]
    df_combined = df_combined.iloc[:10]
    return df_combined[['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TOV']]


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

def get_team_stats(team_name, opponent_team_name, season):
    try:
        stats = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Advanced'
        )
        df = stats.get_data_frames()[0]
        league_avg_pace = df['PACE'].mean()
        league_avg_def_rating = df['DEF_RATING'].mean()
        team_pace = league_avg_pace
        opponent_def_rating = league_avg_def_rating
        for _, row in df.iterrows():
            if team_name.lower() in row['TEAM_NAME'].lower():
                team_pace = row['PACE']
            if opponent_team_name.lower() in row['TEAM_NAME'].lower():
                opponent_def_rating = row['DEF_RATING']
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