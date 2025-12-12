"""
Domain Value Objects - Immutable objects defined by their attributes
Following DDD principles for value objects
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List


class Mark(str, Enum):
    """Represents a mark on the board"""

    X = "X"
    O = "O"  # noqa: E741
    EMPTY = " "

    def opposite(self) -> Mark:
        """Get the opposite mark"""
        if self == Mark.X:
            return Mark.O
        elif self == Mark.O:
            return Mark.X
        return Mark.EMPTY


class GameStatus(str, Enum):
    """Represents the current status of a game"""

    IN_PROGRESS = "IN_PROGRESS"
    DRAW = "DRAW"
    X_WON = "X_WON"
    O_WON = "O_WON"

    def is_finished(self) -> bool:
        """Check if the game is finished"""
        return self != GameStatus.IN_PROGRESS


class GameMode(str, Enum):
    """Represents the game mode"""

    PVP = "pvp"
    PVAI = "pvai"


class AIDifficulty(str, Enum):
    """AI difficulty levels"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class Position:
    """Represents a position on the board (immutable)"""

    row: int
    col: int

    def __post_init__(self):
        if not (0 <= self.row < 3 and 0 <= self.col < 3):
            raise ValueError(f"Position out of bounds: ({self.row}, {self.col})")

    def to_index(self) -> int:
        """Convert to linear index (0-8)"""
        return self.row * 3 + self.col

    @classmethod
    def from_index(cls, index: int) -> Position:
        """Create position from linear index"""
        if not (0 <= index < 9):
            raise ValueError(f"Index out of bounds: {index}")
        return cls(row=index // 3, col=index % 3)


@dataclass(frozen=True)
class PlayerId:
    """Represents a player identifier (value object)"""

    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Player ID cannot be empty")

    def is_ai(self) -> bool:
        """Check if this is an AI player"""
        return self.value == "AI"


@dataclass(frozen=True)
class Board:
    """
    Represents the game board (immutable)
    Encapsulates board logic and provides rich behavior
    """

    cells: tuple[
        tuple[Mark, Mark, Mark], tuple[Mark, Mark, Mark], tuple[Mark, Mark, Mark]
    ]

    @classmethod
    def empty(cls) -> Board:
        """Create an empty board"""
        empty_row = (Mark.EMPTY, Mark.EMPTY, Mark.EMPTY)
        return cls(cells=(empty_row, empty_row, empty_row))

    @classmethod
    def from_list(cls, board: List[List[Mark]]) -> Board:
        """Create board from 2D list"""
        if len(board) != 3 or any(len(row) != 3 for row in board):
            raise ValueError("Board must be 3x3")
        return cls(cells=(tuple(board[0]), tuple(board[1]), tuple(board[2])))

    @classmethod
    def from_string(cls, s: str) -> Board:
        """Create board from 9-character string"""
        if len(s) != 9:
            raise ValueError("Board string must be length 9")
        cells = [[Mark(s[r * 3 + c]) for c in range(3)] for r in range(3)]
        return cls.from_list(cells)

    def to_string(self) -> str:
        """Convert board to string representation"""
        return "".join(cell.value for row in self.cells for cell in row)

    def to_list(self) -> List[List[Mark]]:
        """Convert to 2D list"""
        return [list(row) for row in self.cells]

    def get_cell(self, position: Position) -> Mark:
        """Get mark at position"""
        return self.cells[position.row][position.col]

    def is_empty(self, position: Position) -> bool:
        """Check if position is empty"""
        return self.get_cell(position) == Mark.EMPTY

    def with_mark(self, position: Position, mark: Mark) -> Board:
        """Return new board with mark placed at position (immutable)"""
        if not self.is_empty(position):
            raise ValueError(f"Cell at {position} is already occupied")

        new_cells = [list(row) for row in self.cells]
        new_cells[position.row][position.col] = mark
        return Board.from_list(new_cells)

    def get_empty_positions(self) -> List[Position]:
        """Get all empty positions on the board"""
        positions = []
        for row in range(3):
            for col in range(3):
                pos = Position(row, col)
                if self.is_empty(pos):
                    positions.append(pos)
        return positions

    def is_full(self) -> bool:
        """Check if board is full"""
        return len(self.get_empty_positions()) == 0
