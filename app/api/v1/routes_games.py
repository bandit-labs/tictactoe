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
def create_game_endpoint(payload: GameCreate, db: Session = Depends(get_db)):
    """
    Create a new game session
    Platform call this with player IDs and more
    """
    game = game_service.create_game(db, payload)
    return _to_read(game)


@router.get("/{game_id}", response_model=GameRead)
def get_game(game_id: str, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_read(game)


@router.post("/{game_id}/moves", response_model=GameRead)
def play_move(
    game_id: str,
    payload: MoveCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """
    Apply a move to the game.
      - For PvP: accepts row/col from either player
      - For PvAI: accepts row/col from human, automatically triggers AI move

      The mode is determined from the game in the database, not from the request.
    """
    try:
        # Fetch the game first to check its mode
        game = db.get(Game, game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Determine if AI should play based on game mode
        is_pvai_mode = game.mode == "pvai"

        game = game_service.add_move(db, game_id, payload)

        # If PvAI mode AND game still in progress AND it's AI's turn Schedule AI move in background
        if (
            is_pvai_mode
            and game.status == GameStatus.IN_PROGRESS
            and game.next_player == AI_PLAYER
            and background_tasks is not None
        ):
            ai_difficulty = payload.ai_difficulty or "medium"
            background_tasks.add_task(run_ai_move, game.id, ai_difficulty)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_read(game)


def run_ai_move(game_id: str, ai_difficulty: str | None):
    db = SessionLocal()
    try:
        ai_payload = MoveCreate(
            row=None,
            col=None,
            ai_difficulty=ai_difficulty,
        )
        game_service.add_move(db, game_id, ai_payload, is_ai_move=True)
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
        mode=game.mode,
        ai_difficulty=game.ai_difficulty,
        board=board,
        created_at=game.created_at,
        finished_at=game.finished_at,
    )
