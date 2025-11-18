from __future__ import annotations
from typing import List

from .models import GameState, Mark, GameStatus, Position


WIN_LINES: List[List[Position]] = [
    # rows
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # cols
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # diagonals
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


def legal_moves(state: GameState) -> List[Position]:
    if state.status != GameStatus.IN_PROGRESS:
        return []
    moves: List[Position] = []
    for r in range(3):
        for c in range(3):
            if state.board[r][c] == Mark.EMPTY:
                moves.append((r, c))
    return moves


def apply_move(state: GameState, pos: Position) -> GameState:
    r, c = pos
    if state.status != GameStatus.IN_PROGRESS:
        raise ValueError("Game is already finished")
    if not (0 <= r < 3 and 0 <= c < 3):
        raise ValueError("Position out of bounds")
    if state.board[r][c] != Mark.EMPTY:
        raise ValueError("Cell already occupied")

    # copy board
    new_board = [row[:] for row in state.board]
    new_board[r][c] = state.next_player

    winner = _compute_winner(new_board)
    move_count = state.move_count + 1

    if winner == Mark.X:
        status = GameStatus.X_WON
    elif winner == Mark.O:
        status = GameStatus.O_WON
    elif move_count == 9:
        status = GameStatus.DRAW
    else:
        status = GameStatus.IN_PROGRESS

    next_player = (
        Mark.O if state.next_player == Mark.X else Mark.X
    ) if status == GameStatus.IN_PROGRESS else state.next_player

    return GameState(
        board=new_board,
        next_player=next_player,
        status=status,
        winner=winner,
        move_count=move_count,
    )


def _compute_winner(board) -> Mark | None:
    for line in WIN_LINES:
        marks = {board[r][c] for r, c in line}
        if len(marks) == 1:
            mark = marks.pop()
            if mark != Mark.EMPTY:
                return mark
    return None


def board_to_string(board) -> str:
    # 9 characters, row-major
    return "".join(board[r][c].value for r in range(3) for c in range(3))


def board_from_string(s: str):
    if len(s) != 9:
        raise ValueError("Board string must be length 9")
    return [[Mark(s[r * 3 + c]) for c in range(3)] for r in range(3)]


def heuristic_value(state: GameState, for_player: Mark = Mark.X) -> float:
    if state.status == GameStatus.X_WON:
        return 1.0 if for_player == Mark.X else -1.0
    if state.status == GameStatus.O_WON:
        return 1.0 if for_player == Mark.O else -1.0
    return 0.0
