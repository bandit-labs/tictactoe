import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    DateTime,
    Enum,
    Integer,
    ForeignKey,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum as PyEnum
from app.core.db import Base
from app.core.config import settings
from app.domain import GameStatus, Mark

SCHEMA = settings.db_schema


class GameMode(str, PyEnum):
    PVAI = "pvai"
    PVP = "pvp"


class Game(Base):
    __tablename__ = "games"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    player_x_id: Mapped[str] = mapped_column(String, nullable=False)
    player_o_id: Mapped[str] = mapped_column(String, nullable=False)

    # optional names (for now we just store what you pass; later the platform can resolve)
    player_x_name: Mapped[str] = mapped_column(String, nullable=False)
    player_o_name: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[GameStatus] = mapped_column(Enum(GameStatus), nullable=False)
    next_player: Mapped[Mark] = mapped_column(Enum(Mark), nullable=False)
    move_count: Mapped[int] = mapped_column(Integer, default=0)
    mode: Mapped[str] = mapped_column(String, nullable=False, default="pvai")
    ai_difficulty: Mapped[str | None] = mapped_column(
        String, nullable=True, default="medium"
    )

    # serialized 3x3 board as 9-char string
    board_state: Mapped[str] = mapped_column(String(9), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    moves: Mapped[list["MoveLog"]] = relationship(
        "MoveLog", back_populates="game", cascade="all, delete-orphan"
    )


class MoveLog(Base):
    __tablename__ = "moves"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(f"{SCHEMA}.games.id", ondelete="CASCADE"),
        nullable=False,
    )

    move_number: Mapped[int] = mapped_column(Integer, nullable=False)
    player_id: Mapped[str] = mapped_column(String, nullable=False)
    mark: Mapped[Mark] = mapped_column(Enum(Mark), nullable=False)
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    col: Mapped[int] = mapped_column(Integer, nullable=False)

    # For ML / replay later
    state_before: Mapped[dict] = mapped_column(JSON, nullable=False)
    state_after: Mapped[dict] = mapped_column(JSON, nullable=False)
    heuristic_value: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    game: Mapped[Game] = relationship("Game", back_populates="moves")
