from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.domain.models import Mark, GameStatus
from app.domain.logic import apply_move, heuristic_value
from app.infra.orm_models import Game, MoveLog
from app.services.game_state_mapper import game_to_state, state_to_game
from app.schemas.game import GameCreate
from app.schemas.move import MoveCreate
from app.services.state_serializer import build_rich_state
from app.services.ai_client import request_ai_move
from app.services.platform_client import log_move_to_platform, send_final_result_to_platform


# For now: AI always plays as O
AI_PLAYER = Mark.O


def create_game(db: Session, payload: GameCreate) -> Game:
    game = Game(
        player_x_id=settings.demo_player_x_id,
        player_o_id=settings.demo_player_o_id,
        player_x_name=settings.demo_player_x_name,
        player_o_name=settings.demo_player_o_name,
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X,
        move_count=0,
        board_state=" " * 9,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def add_move(db: Session, game_id: str, payload: MoveCreate) -> Game:
    """
    Apply a move to a game:
      - if it's AI's turn *and* payload.use_ai is True -> let AI choose move (PvAI)
      - otherwise -> use row/col from payload (human move)
    """
    game: Game | None = db.get(Game, game_id)
    if not game:
        raise ValueError("Game not found")

    existing_logs: List[MoveLog] = list(game.moves or [])

    state_before = game_to_state(game)
    if state_before.status != GameStatus.IN_PROGRESS:
        raise ValueError("Game already finished")

    # Is it AI's turn right now?
    is_ai_turn = state_before.next_player == AI_PLAYER
    use_ai_now = bool(payload.use_ai and is_ai_turn)

    if use_ai_now:
        # --- AI MOVE (AI plays as O) ---
        difficulty = payload.ai_difficulty or "medium"

        (row, col), evaluation, _meta = request_ai_move(
            state=state_before,
            difficulty=difficulty,
        )

        player_id = "AI"
        mark = state_before.next_player
        heuristic_val = evaluation
    else:
        if payload.row is None or payload.col is None:
            # If UI accidentally sends use_ai=False but no coordinates
            raise ValueError("row and col are required for human moves")

        row = payload.row
        col = payload.col
        mark = state_before.next_player
        player_id = game.player_x_id if mark == Mark.X else game.player_o_id
        heuristic_val = heuristic_value(state_before, for_player=mark)

    # Build rich state BEFORE move
    state_before_dict = build_rich_state(game, state_before, existing_logs)

    # Apply move with domain rules
    new_state = apply_move(state_before, (row, col))

    # Update Game entity from new_state
    state_to_game(game, new_state)

    # Prepare a MoveLog object
    move_log = MoveLog(
        game_id=game.id,
        move_number=new_state.move_count,
        player_id=player_id,
        mark=mark,
        row=row,
        col=col,
        state_before={},  # filled later
        state_after={},   # filled later
        heuristic_value=heuristic_val,
    )

    # History AFTER = existing logs + this new one
    history_after_logs = existing_logs + [move_log]

    state_after_dict = build_rich_state(game, new_state, history_after_logs)

    move_log.state_before = state_before_dict
    move_log.state_after = state_after_dict

    db.add(game)
    db.add(move_log)
    db.commit()
    db.refresh(game)

    # Fire-and-forget logging to Platform
    try:
        move_index = row * 3 + col
        log_move_to_platform(
            previous_state=state_before_dict,
            new_state=state_after_dict,
            move_index=move_index,
            player_id=player_id,
            heuristic_value=heuristic_val,
        )

        if new_state.status in (GameStatus.X_WON, GameStatus.O_WON, GameStatus.DRAW):
            history_payload = [
                {
                    "player": log.mark.value,
                    "move": log.row * 3 + log.col,
                    "move_number": log.move_number,
                }
                for log in history_after_logs
            ]
            send_final_result_to_platform(
                final_state=state_after_dict,
                history=history_payload,
            )
    except Exception:
        # Don't break gameplay if platform logging fails
        pass

    return game
