from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

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

class MispricingSignal(Base):
    __tablename__ = 'mispricing_signal'
    id = Column(Integer, primary_key = True)
    player_name = Column(String)
    stat_category = Column(String)
    prop_line = Column(Float)
    side = Column(String)
    implied_vol_over = Column(Float)
    implied_vol_under = Column(Float)
    realized_vol = Column(Float)
    gap = Column(Float)
    direction = Column(String)
    time_stamp = Column(DateTime, default=datetime.now)
    bookmaker = Column(String)
    mc_prob = Column(Float)
    empirical_prob = Column(Float)
    confidence = Column(String)

class GameLog(Base):
    __tablename__ = 'game_logs'
    id = Column(Integer, primary_key=True)
    player_name = Column(String)
    season = Column(String)
    stat_category = Column(String)
    game_date = Column(DateTime)
    stat_value = Column(Float)
    time_stamp = Column(DateTime, default=datetime.now)
