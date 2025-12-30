"""
Data Transfer Objects (DTOs) for Application Layer
Used for input (commands) and output (responses)
Decouples API layer from domain layer
"""

from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


# Commands (Input DTOs)


class CreateGameCommand(BaseModel):
    """
    Command to create a new game
    Represents user intent
    """

    player_x_id: str = Field(..., description="Player X ID")
    player_x_name: Optional[str] = Field(
        None, description="Player X display name")
    player_o_id: Optional[str] = Field(
        None, description="Player O ID (for PvP mode)")
    player_o_name: Optional[str] = Field(
        None, description="Player O display name")
    mode: Literal["pvai", "pvp"] = Field(..., description="Game mode")
    ai_difficulty: Optional[Literal["easy", "medium", "hard", "unbeatable", "ml"]] = (
        Field("medium", description="AI difficulty (only for PvAI mode)")
    )


class PlayMoveCommand(BaseModel):
    """
    Command to play a move
    """

    game_id: str = Field(..., description="Game ID")
    player_id: str = Field(..., description="Player making the move")
    row: Optional[int] = Field(None, description="Row index (0-2)")
    col: Optional[int] = Field(None, description="Column index (0-2)")
    ai_difficulty: Optional[Literal["easy", "medium", "hard", "unbeatable", "ml"]] = (
        Field(None, description="AI difficulty override")
    )


class GetGameQuery(BaseModel):
    """
    Query to get a game by ID
    """

    game_id: str = Field(..., description="Game ID")


# Responses (Output DTOs)


class GameResponse(BaseModel):
    """
    Response containing game state
    Used for API responses
    """

    id: str
    player_x_id: str
    player_x_name: str
    player_o_id: str
    player_o_name: str
    status: str
    next_player: str
    move_count: int
    mode: str
    ai_difficulty: Optional[str]
    board: List[List[str]]
    created_at: datetime
    finished_at: Optional[datetime]
    sessionUrl: str

    class Config:
        from_attributes = True


class MoveResponse(BaseModel):
    """
    Response for a move operation
    Contains updated game state
    """

    game: GameResponse
    move_number: int
    position: dict  # {row: int, col: int}
    mark: str


class ErrorResponse(BaseModel):
    """
    Standard error response
    """

    error: str
    detail: Optional[str] = None
