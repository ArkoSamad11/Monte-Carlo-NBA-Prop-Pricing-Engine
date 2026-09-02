import hmac
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from functools import lru_cache
from src.data.odds_client import get_events_ids, get_odds, parse_props
from src.data.nba_client import stat_information, get_id
from src.analysis.mispricing import find_mispricing
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams
from src.data.db import engine, Session
from src.data.models import Base, MispricingSignal
from src.data.usage import ensure_usage_table, record_event, usage_summary
from datetime import datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Creates the usage_events table on startup if it does not already exist, so a
    deployment provisioned before usage tracking existed picks it up without a
    manual migration. Failure is non-fatal: tracking degrades to a no-op.
    """

    ensure_usage_table()
    yield


app = FastAPI(lifespan=lifespan)


class PropModel(BaseModel):
    player: str
    line: float
    over_odds: int
    under_odds: int


class UsageEventModel(BaseModel):
    session_id: str
    event: str
    player: Optional[str] = None
    stat: Optional[str] = None
    bookmaker: Optional[str] = None


@lru_cache(maxsize=128)
def cached_stat_information(player_name: str, season: str, stat_category: str):
    """
    Caches stat lookups for up to 128 unique player/season/stat combinations.
    
    Args:
        player_name: Name of the player (String).
        season: Name of the season in the format 20XX - YY that is passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop (String).

    Returns: 
            A tuple of up to 10 integers representing the player's most recent qualifying
            game values for the selected stat, ordered most-recent-first. Returned as a
            tuple rather than a list for lru_cache compatibility.
    """
    
    return tuple(stat_information(player_name, season, stat_category))


@lru_cache(maxsize=32)
def cached_roster(home_team: str, away_team: str):
    """
        Caches the combined roster for both teams in the selected game.

    Args:
        home_team: Full or partial name of the home team (String).
        away_team: Full or partial name of the away team (String).

    Returns: 
            A tuple of player name strings representing the combined roster of both teams.
            Returned as a tuple rather than a list for lru_cache compatibility.
    """
    
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
    """
    Returns all available NBA games from the Odds API for game selection in the dashboard.
    Originally used to automatically populate prop lines alongside game selection.

    Returns:
        A list of available NBA game events, each containing the event ID and team
        matchup information used to populate the game selection dropdown in the dashboard.
    """
    
    return get_events_ids()


@app.get('/props')
def props(event_id: str, stat_category: str):
    """
    Returns parsed over/under props for a specific game and stat category from the Odds API.

    Args:
        event_id: Unique identifier for the NBA game returned by the /events endpoint (String).
        stat_category: The selected stat for the player prop (String).
        
    Returns:
        A list of parsed prop objects containing over/under lines and odds for the
        selected game and stat category.
    """
    
    return parse_props(get_odds(event_id, stat_category))


@app.get('/statlist')
def statlist(player_name: str, season: str, stat_category: str):
    """
    Returns the player's last 10 qualifying game values for the selected stat.
    Uses cached_stat_information to avoid redundant NBA Stats API calls.

    Args:
        player_name: Name of the player (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop (String).
    Returns:
        A list of up to 10 integers representing the player's most recent qualifying
        game values for the selected stat, ordered most-recent-first.
    """
    
    return list(cached_stat_information(player_name, season, stat_category))


@app.get('/roster')
def roster(home_team: str, away_team: str):
    """
    Returns the combined roster for both teams in the selected game.
    Uses cached_roster to avoid redundant NBA Stats API calls.

    Args:
        home_team: Full or partial name of the home team (String).
        away_team: Full or partial name of the away team (String).
        
    Returns:
        A list of player name strings representing the combined roster of both teams.
        Used by the dashboard to populate the player selection dropdown.
    """
    
    return list(cached_roster(home_team, away_team))


@app.get('/playerid')
def playerid(player_name: str):
    """
    Returns the NBA Stats API player ID for a given player name.

    Args:
        player_name: Name of the player (String).
        
    Returns:
        A dictionary containing the player's NBA Stats API ID: {'id': int}.
    """
    
    return {'id': get_id(player_name)}


@app.post('/mispricing')
def mispricing(player_name: str, season: str, stat_category: str, prop: PropModel, player_team: str = None, opponent_team: str = None):
    """
    Runs mispricing analysis for a prop without logging it to the database.
    Used by the dashboard to display live probability comparisons and edge detection
    before the user decides whether to log the signal.

    Args:
        player_name: Name of the player (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop (String).
        prop: Pydantic model containing the prop line and market odds (PropModel).
        player_team: Initialized to None. The team that the selected player is on (String).
        opponent_team: Initialized to None. The team the selected player is playing against (String).
    Returns:
        A list containing at most one signal dictionary with probability comparisons,
        edge direction, confidence rating, and simulation data. 
        Empty list if no edge exceeds the threshold.
    """
    
    return find_mispricing(player_name, season, stat_category,prop.model_dump(),player_team=player_team,opponent_team=opponent_team)


@app.post('/log_signal')
def log_signal(player_name: str, season: str, stat_category: str, prop: PropModel, bookmaker: str = 'DraftKings', player_team: str = None, opponent_team: str = None, session_id: str = None):
    """
    Runs mispricing analysis and persists any detected signal to the database.
    Called when the user clicks 'Find Mispricing' in the dashboard after reviewing a prop.
    Only logs a record if the Monte Carlo gap exceeds the threshold.

    Args:
        player_name: Name of the player (String).
        season: Season in the format 20XX-YY passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop (String).
        prop: Pydantic model containing the prop line and market odds (PropModel).
        bookmaker: Initialized to DraftKings. Determines which sportsbook settlement
                   rules are applied during probability computation (String).
        player_team: Initialized to None. The team that the selected player is on (String).
        opponent_team: Initialized to None. The team the selected player is playing against (String).
        session_id: Initialized to None. Anonymous per-browser-session UUID sent by the
                    dashboard for usage tracking. Omitting it skips tracking only, the
                    analysis is unaffected (String).
    Returns:
        A list containing at most one signal dictionary with probability comparisons,
        edge direction, confidence tier, and simulation data. Empty list if no edge
        exceeds the threshold or if an exception occurs during analysis.
    """

    # Recorded before the analysis runs so a request still counts as usage even when
    # the pricing pipeline raises or finds no edge. record_event never raises.
    record_event(session_id, 'price_request', player=player_name, stat=stat_category, bookmaker=bookmaker)

    try:
        results = find_mispricing(player_name, season, stat_category,prop.model_dump(),player_team=player_team,opponent_team=opponent_team,bookmaker=bookmaker)
    # Return empty list on any failure to prevent the dashboard from crashing.    
    except Exception:
        return []
    session = Session()
    for signal in results:
        record = MispricingSignal(player_name=signal['player'],stat_category=stat_category,prop_line=signal['line'],side=signal['side'],implied_vol_over=0.0,
            implied_vol_under=0.0,realized_vol=signal['realized_vol'],gap=signal['mc_gap'],direction=signal['direction'],time_stamp=datetime.now(),
            bookmaker=bookmaker,mc_prob=signal['mc_prob'],empirical_prob=signal['empirical_prob'],confidence=signal['confidence'])
        session.add(record)
    session.commit()
    session.close()
    return results


@app.post('/usage')
def usage(payload: UsageEventModel):
    """
    Records a single anonymous usage event from the dashboard.

    Used for the 'session_start' event fired once per browser session. Pricing
    requests are recorded server side by /log_signal instead, so they cannot be
    missed. Unrecognized event names are ignored rather than stored.

    Args:
        payload: Pydantic model containing the session UUID, event name, and optional
                 player, stat, and bookmaker context (UsageEventModel).

    Returns:
        A dictionary of the form {'recorded': bool}. Returns recorded=False rather
        than raising when the database is unreachable, so a tracking outage never
        surfaces as an error in the dashboard.
    """

    return {'recorded': record_event(payload.session_id, payload.event, player=payload.player, stat=payload.stat, bookmaker=payload.bookmaker)}


@app.get('/usage_stats')
def usage_stats(x_admin_token: str = Header(None)):
    """
    Returns aggregated usage numbers for the developer.

    Protected by the USAGE_ADMIN_TOKEN environment variable and disabled entirely
    when that variable is unset, so usage data is never publicly readable. Pass the
    token in the X-Admin-Token request header.

    Args:
        x_admin_token: Value of the X-Admin-Token request header (String).

    Returns:
        A dictionary containing distinct session and pricing request counts, the date
        range covered, per-day activity, and the most requested players and stats.

    Raises:
        HTTPException: 404 if the endpoint is disabled, 401 if the token is missing
                       or does not match.
    """

    expected = os.getenv('USAGE_ADMIN_TOKEN')
    if not expected:
        raise HTTPException(status_code=404, detail='Usage stats are disabled. Set USAGE_ADMIN_TOKEN to enable this endpoint.')
    # compare_digest avoids leaking the token through response timing.
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail='Invalid or missing X-Admin-Token header.')

    return usage_summary()
