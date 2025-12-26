from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

from app.domain import GameStatus, Mark


class GameCreate(BaseModel):
    """
    Request from Platform to create a game.
    - For PvAI only player_x_id is required
    - For PvP both player_x_id and player_o_id are required
    """

    player_x_id: str
    player_o_id: Optional[str] = None
    mode: Literal["pvai", "pvp"]

    player_x_name: Optional[str] = None
    player_o_name: Optional[str] = None
    ai_difficulty: Optional[Literal["easy", "medium", "hard", "unbeatable", "ml"]] = (
        "medium"
    )


class GameRead(BaseModel):
    id: str
    player_x_id: str
    player_o_id: str
    player_x_name: str
    player_o_name: str
    status: GameStatus
    next_player: Mark
    move_count: int
    mode: str
    ai_difficulty: Optional[str]
    board: list[list[str]]
    created_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
