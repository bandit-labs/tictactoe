from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.infra.orm_models import Game
from app.schemas.game import GameCreate, GameRead
from app.schemas.move import MoveCreate
from app.services import game_service
from app.domain.logic import board_from_string

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=GameRead)
def create_game_endpoint(db: Session = Depends(get_db)):
    game = game_service.create_game(db, GameCreate())
    return _to_read(game)


@router.get("/{game_id}", response_model=GameRead)
def get_game(game_id: str, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_read(game)


@router.post("/{game_id}/moves", response_model=GameRead)
def play_move(game_id: str, payload: MoveCreate, db: Session = Depends(get_db)):
    try:
        game = game_service.add_move(db, game_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_read(game)


def _to_read(game: Game) -> GameRead:
    board = [[c for c in row] for row in board_from_string(game.board_state)]
    return GameRead(
        id=game.id,
        player_x_id=game.player_x_id,
        player_o_id=game.player_o_id,
        player_x_name=game.player_x_name,
        player_o_name=game.player_o_name,
        status=game.status,
        next_player=game.next_player,
        move_count=game.move_count,
        board=board,
        created_at=game.created_at,
        finished_at=game.finished_at,
    )
