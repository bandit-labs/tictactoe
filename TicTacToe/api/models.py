from sqlalchemy import Column, String, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GameStateModel(Base):
    __tablename__ = "game_states"

    game_id = Column(String, primary_key=True)
    state_json = Column(JSON, nullable=False)
    game_status = Column(String, nullable=False)
    winner = Column(String, nullable=True)
    move_count = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False)
