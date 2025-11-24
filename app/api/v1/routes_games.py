from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.db import get_db, SessionLocal
from app.domain.models import GameStatus
from app.infra.orm_models import Game
from app.schemas.game import GameCreate, GameRead
from app.schemas.move import MoveCreate
from app.services import game_service
from app.domain.logic import board_from_string
from app.services.game_service import AI_PLAYER

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
def play_move(game_id: str,
              payload: MoveCreate,
              db: Session = Depends(get_db),
              background_tasks: BackgroundTasks = None,):
    """
    Apply exactly ONE move (human or AI) and return immediately.
    If this is a PvAI game (payload.use_ai) and after the human move
    it's AI's turn, schedule the AI move in a background task.
    """
    try:
        # First move
        game = game_service.add_move(db, game_id, payload)

        # if mode is PvAI, and it is AI turn, schedule AI move async
        if (payload.use_ai
            and game.status == GameStatus.IN_PROGRESS
            and game.next_player == AI_PLAYER
            and background_tasks is not None):
            background_tasks.add_task(run_ai_move, game.id, payload.ai_difficulty)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_read(game)

def run_ai_move(game_id:str, ai_difficulty:str | None):
    db = SessionLocal()
    try:
        ai_payload = MoveCreate(
            row=None,
            col=None,
            use_ai=True,
            ai_difficulty=ai_difficulty,
        )
        game_service.add_move(db, game_id, ai_payload)
    finally:
        db.close()

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
