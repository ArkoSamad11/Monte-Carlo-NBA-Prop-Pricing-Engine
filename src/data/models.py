from sqlalchemy import Column, Integer, String, Float, DateTime
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
