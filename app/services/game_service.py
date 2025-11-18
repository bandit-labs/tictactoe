from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session
from app.domain.logic import (
    board_from_string,
    board_to_string,
    apply_move,
    heuristic_value,
)
from app.domain.models import GameState, Mark, GameStatus
from app.infra.orm_models import Game, MoveLog
from app.infra import ai_client
from app.schemas.game import GameCreate
from app.schemas.move import MoveCreate
from app.core.config import settings

def _to_state(game: Game) -> GameState:
    board = board_from_string(game.board_state)
    winner: Mark | None = None
    if game.status == GameStatus.X_WON:
        winner = Mark.X
    elif game.status == GameStatus.O_WON:
        winner = Mark.O

    return GameState(
        board=board,
        next_player=game.next_player,
        status=game.status,
        winner=winner,
        move_count=game.move_count,
    )


def _serialize_state(state: GameState) -> dict:
    return {
        "board": [[cell.value for cell in row] for row in state.board],
        "next_player": state.next_player.value,
        "status": state.status.value,
        "winner": state.winner.value if state.winner else None,
        "move_count": state.move_count,
    }


def create_game(db: Session, payload: GameCreate) -> Game:
    state = GameState.new()

    game = Game(
        player_x_id=settings.demo_player_x_id,
        player_o_id=settings.demo_player_o_id,
        player_x_name=settings.demo_player_x_name,
        player_o_name=settings.demo_player_o_name,
        status=state.status,
        next_player=state.next_player,
        move_count=state.move_count,
        board_state=board_to_string(state.board),
    )

    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def add_move(db: Session, game_id: str, move_payload: MoveCreate) -> Game:
    game = db.get(Game, game_id)
    if not game:
        raise ValueError("Game not found")

    state_before = _to_state(game)

    if state_before.status != GameStatus.IN_PROGRESS:
        raise ValueError("Game finished")

    if state_before.next_player == Mark.X:
        player_id = game.player_x_id
    else:
        player_id = game.player_o_id

    if move_payload.use_ai:
        row, col = ai_client.choose_ai_move(state_before)
        mark = state_before.next_player
    else:
        row, col = move_payload.row, move_payload.col
        mark = state_before.next_player

    state_after = apply_move(state_before, (row, col))

    game.board_state = board_to_string(state_after.board)
    game.next_player = state_after.next_player
    game.status = state_after.status
    game.move_count = state_after.move_count
    if state_after.status in (GameStatus.X_WON, GameStatus.O_WON, GameStatus.DRAW):
        game.finished_at = datetime.now()

    log = MoveLog(
        game_id=game.id,
        move_number=state_after.move_count,
        player_id=player_id,
        mark=mark,
        row=row,
        col=col,
        state_before=_serialize_state(state_before),
        state_after=_serialize_state(state_after),
        heuristic_value=heuristic_value(state_after),
    )

    db.add(log)
    db.commit()
    db.refresh(game)
    return game
