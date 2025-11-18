from __future__ import annotations
from datetime import datetime
from typing import List

from app.domain.models import GameState, Mark, GameStatus
from app.infra.orm_models import Game, MoveLog


def build_rich_state(
    game: Game,
    state: GameState,
    moves: List[MoveLog],
) -> dict:
    rows = len(state.board)
    cols = len(state.board[0]) if rows else 0

    # legal moves as 0..8 indices
    legal_moves: list[int] = []
    for r in range(rows):
        for c in range(cols):
            if state.board[r][c] == Mark.EMPTY:
                legal_moves.append(r * cols + c)

    # map GameStatus -> ("IN_PROGRESS"|"DRAW"|"WIN", winner)
    if state.status == GameStatus.IN_PROGRESS:
        game_status = "IN_PROGRESS"
        winner = None
    elif state.status == GameStatus.DRAW:
        game_status = "DRAW"
        winner = None
    elif state.status == GameStatus.X_WON:
        game_status = "WIN"
        winner = "X"
    elif state.status == GameStatus.O_WON:
        game_status = "WIN"
        winner = "O"
    else:
        game_status = state.status.value
        winner = None

    # history as [{player: "X"/"O", move: idx}]
    history = [
        {
            "player": log.mark.value,
            "move": log.row * cols + log.col,
        }
        for log in sorted(moves, key=lambda m: m.move_number)
    ]

    # created_at on MoveLog may be None (not flushed yet),
    # and game.created_at can theoretically be None as well.
    timestamps = [m.created_at for m in moves if m.created_at is not None]

    last_ts: datetime | None = None
    if timestamps:
        last_ts = max(timestamps)
    elif getattr(game, "created_at", None) is not None:
        last_ts = game.created_at

    # safety net
    if last_ts is None:
        last_ts = datetime.utcnow()

    # board with "." for empty
    board = [
        [
            "." if cell == Mark.EMPTY else cell.value
            for cell in row
        ]
        for row in state.board
    ]

    return {
        "game_id": game.id,
        "board": board,
        "current_player": state.next_player.value,
        "legal_moves": legal_moves,
        "move_count": state.move_count,
        "game_status": game_status,
        "winner": winner,
        "config": {"rows": rows, "cols": cols},
        "history": history,
        "last_updated": last_ts.isoformat(),
    }
