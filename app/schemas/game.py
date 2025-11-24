from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.domain.models import GameStatus, Mark


class GameCreate(BaseModel):
    """
    Placeholder for future data from Platform.
    For now, it is empty: backend fills players from Settings.
    """
    pass


class GameRead(BaseModel):
    id: str
    player_x_id: str
    player_o_id: str
    player_x_name: str
    player_o_name: str
    status: GameStatus
    next_player: Mark
    move_count: int
    board: list[list[str]]
    created_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
