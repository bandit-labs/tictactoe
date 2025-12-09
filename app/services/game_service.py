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
from app.services.platform_client import (
    log_move_to_platform,
    send_final_result_to_platform,
)


# For now: AI always plays as O
AI_PLAYER = Mark.O


def create_game(db: Session, payload: GameCreate) -> Game:
    """
    Create a new game based on mode:
    - PvAI: player_o_id = AI & player_o_name = "AI"
    - PvP: both players from payload
    """
    # Determine player O based on mode
    if payload.mode == "pvai":
        player_o_id = "AI"
        player_o_name = "AI"
    elif payload.mode == "pvp":
        if not payload.player_o_id:
            raise ValueError("Player O_id is required for PvP mode")
        player_o_id = payload.player_o_id
        player_o_name = payload.player_o_name or "Player O"
    else:
        raise ValueError(f"Invalid mode: {payload.mode}")

    # Configure player X
    player_x_name = payload.player_x_name or "Player X"

    game = Game(
        player_x_id=payload.player_x_id,
        player_o_id=player_o_id,
        player_x_name=player_x_name,
        player_o_name=player_o_name,
        mode=payload.mode,
        ai_difficulty=payload.ai_difficulty if payload.mode == "pvai" else None,
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X,
        move_count=0,
        board_state=" " * 9,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def add_move(
    db: Session, game_id: str, payload: MoveCreate, is_ai_move: bool = False
) -> Game:
    """
    Apply a move to a game

    For PvAI games:
        - If it's the human player's turn: use row/col from payload
        - If it's AI's turn: call AI service (when called from background task)

      For PvP games:
        - Always use row/col from payload (either player)
    """
    game: Game | None = db.get(Game, game_id)
    if not game:
        raise ValueError("Game not found")

    existing_logs: List[MoveLog] = list(game.moves or [])

    state_before = game_to_state(game)
    if state_before.status != GameStatus.IN_PROGRESS:
        raise ValueError("Game already finished")

    # Determine if this is an AI move
    # Game mode is PvAI AND Current player is AI AND use_ai flag is True
    can_use_ai = game.mode == "pvai" and state_before.next_player == AI_PLAYER
    use_ai_now = can_use_ai and is_ai_move

    if use_ai_now:
        difficulty = game.ai_difficulty or payload.ai_difficulty or "medium"

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
        state_after={},  # filled later
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
