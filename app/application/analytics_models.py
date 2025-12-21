from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base
from app.core.config import settings

SCHEMA = settings.db_schema

"""
Analytics ORM Models (Analytical Database / Data Warehouse)

These models represent historical game data for ML and reporting:
- GameAnalytics: Completed game metadata (players, outcome, duration)
- MoveAnalytics: Move-by-move analysis with MCTS stats and state transitions

Purpose: ML training, dataset export, performance analysis, reporting
Data Lifecycle: Populated after each move via platform_service.log_move()
Schema: No schema prefix (default schema)

Data Flow:
1. Game played through domain/entities.py
2. Moves logged via PlayMoveUseCase -> platform_service.log_move()
3. Data written to GameAnalytics/MoveAnalytics
4. Exported to Parquet via MLDatasetExportService

See also: app/infrastructure/orm_models.py for operational/transactional models
"""


class GameAnalytics(Base):
    __tablename__ = "game_analytics"
    __table_args__ = {"schema": SCHEMA}

    game_id: Mapped[str] = mapped_column(String, primary_key=True)
    player_x_id: Mapped[str] = mapped_column(String, nullable=False)
    player_o_id: Mapped[str] = mapped_column(String, nullable=False)
    player_x_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    player_o_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)  # "pvp" | "pvai"
    ai_difficulty: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # "easy" | "medium" | "hard"
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "in_progress" | "win" | "draw" etc.
    move_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    moves: Mapped[list["MoveAnalytics"]] = relationship(
        "MoveAnalytics",
        back_populates="game",
        cascade="all, delete-orphan",
        primaryjoin="GameAnalytics.game_id==MoveAnalytics.game_id",
    )


class MoveAnalytics(Base):
    __tablename__ = "move_analytics"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.game_analytics.game_id"), nullable=False
    )

    move_number: Mapped[int] = mapped_column(Integer, nullable=False)
    player_id: Mapped[str] = mapped_column(String, nullable=False)
    mark: Mapped[str] = mapped_column(String, nullable=False)  # "X" | "O"
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    col: Mapped[int] = mapped_column(Integer, nullable=False)

    state_before: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    state_after: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    heuristic_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    ai_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    game: Mapped[GameAnalytics] = relationship("GameAnalytics", back_populates="moves")
