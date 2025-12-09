from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class Mark(str, Enum):
    X = "X"
    O = "O"  # noqa: E741
    EMPTY = " "


class GameStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    DRAW = "DRAW"
    X_WON = "X_WON"
    O_WON = "O_WON"


Board = List[List[Mark]]
Position = Tuple[int, int]


@dataclass
class GameState:
    board: Board
    next_player: Mark
    status: GameStatus
    winner: Optional[Mark]
    move_count: int = 0

    @staticmethod
    def new(starting_player: Mark = Mark.X) -> "GameState":
        empty_board: Board = [[Mark.EMPTY for _ in range(3)] for _ in range(3)]
        return GameState(
            board=empty_board,
            next_player=starting_player,
            status=GameStatus.IN_PROGRESS,
            winner=None,
            move_count=0,
        )
