from sqlalchemy import Column, Integer, create_engine, Text, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Referee(Base):
    __tablename__ = 'referees'
    id = Column(Integer, primary_key=True)
    f_name = Column(String(50), nullable=False)
    l_name = Column(String(50), nullable=False)
    number = Column(Integer, nullable=False)
    years_active = Column(Integer, nullable=False)
    games_reffed = Column(Integer, nullable=False, default=0)


class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)


class StatLine(Base):
    __tablename__ = "statlines"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    active_ref_id = Column(Integer, ForeignKey("referees.id"), nullable=False)
    total_penalties = Column(Integer, nullable=False)

engine = create_engine('sqlite:///flaskapp.db')


Base.metadata.create_all(engine)
