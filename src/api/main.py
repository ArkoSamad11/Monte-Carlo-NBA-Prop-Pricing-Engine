from fastapi import FastAPI
from pydantic import BaseModel
from functools import lru_cache
from src.data.odds_client import get_events_ids, get_odds, parse_props
from src.data.nba_client import stat_information, get_id
from src.analysis.mispricing import find_mispricing
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models import Base, MispricingSignal
from datetime import datetime

app = FastAPI()

engine = create_engine('postgresql://localhost/propvol')
Session = sessionmaker(bind=engine)


class PropModel(BaseModel):
    player: str
    line: float
    over_odds: int
    under_odds: int


@lru_cache(maxsize=128)
def cached_stat_information(player_name: str, season: str, stat_category: str):
    return tuple(stat_information(player_name, season, stat_category))


@lru_cache(maxsize=32)
def cached_roster(home_team: str, away_team: str):
    all_teams = teams.get_teams()
    player_list = []
    for team_name in [home_team, away_team]:
        for t in all_teams:
            if team_name.lower() in t['full_name'].lower():
                team_roster = commonteamroster.CommonTeamRoster(team_id=t['id'])
                df = team_roster.get_data_frames()[0]
                for player in df['PLAYER'].tolist():
                    player_list.append(player)
    return tuple(player_list)


@app.get('/events')
def events():
    return get_events_ids()


@app.get('/props')
def props(event_id: str, stat_category: str):
    return parse_props(get_odds(event_id, stat_category))


@app.get('/statlist')
def statlist(player_name: str, season: str, stat_category: str):
    return list(cached_stat_information(player_name, season, stat_category))


@app.get('/roster')
def roster(home_team: str, away_team: str):
    return list(cached_roster(home_team, away_team))


@app.get('/playerid')
def playerid(player_name: str):
    return {'id': get_id(player_name)}


@app.post('/mispricing')
def mispricing(player_name: str, season: str, stat_category: str, prop: PropModel, player_team: str = None, opponent_team: str = None):
    return find_mispricing(
        player_name, season, stat_category,
        prop.model_dump(),
        player_team=player_team,
        opponent_team=opponent_team
    )


@app.post('/log_signal')
def log_signal(player_name: str, season: str, stat_category: str, prop: PropModel, bookmaker: str = 'DraftKings', player_team: str = None, opponent_team: str = None):
    try:
        results = find_mispricing(
            player_name, season, stat_category,
            prop.model_dump(),
            player_team=player_team,
            opponent_team=opponent_team,
            bookmaker=bookmaker
        )
    except Exception:
        return []
    session = Session()
    for signal in results:
        record = MispricingSignal(
            player_name=signal['player'],
            stat_category=stat_category,
            prop_line=signal['line'],
            side=signal['side'],
            implied_vol_over=0.0,
            implied_vol_under=0.0,
            realized_vol=signal['realized_vol'],
            gap=signal['mc_gap'],
            direction=signal['direction'],
            time_stamp=datetime.now(),
            bookmaker=bookmaker,
            mc_prob=signal['mc_prob'],
            empirical_prob=signal['empirical_prob'],
            confidence=signal['confidence']
        )
        session.add(record)
    session.commit()
    session.close()
    return results