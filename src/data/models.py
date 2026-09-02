from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Stores raw prop lines and market odds fetched from the Odds API.
class PlayerProp(Base):
    __tablename__ = 'player_props'
    id = Column(Integer, primary_key = True)
    player_name = Column(String)
    stat_category = Column(String)
    prop_line = Column(Float)
    over_odds = Column(Integer)
    under_odds = Column(Integer)
    event_id = Column(String)
    time_stamp = Column(DateTime, default=datetime.now)

# Primary signal store. One record is written per detected mispricing signal
# when the user clicks 'Find Mispricing' in the dashboard. Used for accuracy
# tracking, calibration analysis, and model evaluation across live playoff markets.
class MispricingSignal(Base):
    __tablename__ = 'mispricing_signal'
    id = Column(Integer, primary_key = True)
    player_name = Column(String)
    stat_category = Column(String)
    prop_line = Column(Float)
    side = Column(String) # 'over' or 'under', the flagged side
    implied_vol_over = Column(Float) # not relevant to final product, was apart of original idea
    implied_vol_under = Column(Float) # not relevant to final product, was apart of original idea
    realized_vol = Column(Float)
    gap = Column(Float) # gap between monte carlo probability and market probability 
    direction = Column(String) # 'underpriced' or 'overpriced'
    time_stamp = Column(DateTime, default=datetime.now)
    bookmaker = Column(String)
    mc_prob = Column(Float) # Monte Carlo probability for the flagged side 
    empirical_prob = Column(Float) # Weighted empirical probability for the flagged side 
    confidence = Column(String) # 'high' or 'moderate' 
    
# Stores individual player game log entries for historical reference.
class GameLog(Base):
    __tablename__ = 'game_logs'
    id = Column(Integer, primary_key=True)
    player_name = Column(String)
    season = Column(String)
    stat_category = Column(String)
    game_date = Column(DateTime)
    stat_value = Column(Float)
    time_stamp = Column(DateTime, default=datetime.now)


# Anonymous usage tracking. One row per tracked dashboard interaction.
# session_id is a random UUID minted by the Streamlit dashboard once per browser
# session. It holds no personal information and is not derived from IP address,
# user agent, or any other fingerprint.
#
# This counts sessions, not people: Streamlit session state resets when the tab
# closes or the app sleeps, so one person across five game nights registers as
# five sessions. Report the metric as distinct sessions.
class UsageEvent(Base):
    __tablename__ = 'usage_events'
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    event = Column(String(64), nullable=False) # 'session_start' or 'price_request'
    player = Column(String)
    stat = Column(String)
    bookmaker = Column(String)
    time_stamp = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_usage_session', 'session_id', 'time_stamp'),
        Index('idx_usage_event', 'event', 'time_stamp'),
    )
