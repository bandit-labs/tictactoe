# TicTacToe/api/models.py
from sqlalchemy import Column, String, JSON, DateTime, Integer, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Table for storing the full GameState persistently
class GameStateModel(Base):
    __tablename__ = "game_states"
    game_id = Column(String, primary_key=True)
    state_json = Column(JSON, nullable=False) # Stores the full GameState object
    game_status = Column(String, nullable=False)
    winner = Column(String, nullable=True)
    move_count = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False)

# Table for logging move-specific metrics (sent to platform or kept locally for analysis)
class MoveLogModel(Base):
    __tablename__ = "move_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True) # Unique ID for each log entry
    game_id = Column(String, nullable=False) # Link to the game
    player_id = Column(String, nullable=False) # ID of the player making the move
    move_index = Column(Integer, nullable=False) # The move made (e.g., 0-8 for TicTacToe)
    move_number = Column(Integer, nullable=False) # The sequence number of the move in the game
    previous_state_snapshot = Column(JSON, nullable=True) # Optional: Snapshot of state before move
    next_state_snapshot = Column(JSON, nullable=True)   # Optional: Snapshot of state after move
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow) # When the move was made
    heuristic_value = Column(Float, nullable=True) # Evaluation of the state (placeholder for now)
    # Add other potentially useful metrics here as needed
