"""
Domain Services - Business logic that doesn't belong to a single entity
Stateless services that operate on domain objects
"""

from __future__ import annotations
from typing import List, Optional

from .value_objects import Board, Position, Mark, GameStatus


class GameRules:
    """
    Domain service for game rules (stateless)
    Encapsulates all game logic: winning conditions, legal moves, etc.
    """

    # All winning lines (rows, columns, diagonals)
    WIN_LINES: List[List[Position]] = [
        # Rows
        [Position(0, 0), Position(0, 1), Position(0, 2)],
        [Position(1, 0), Position(1, 1), Position(1, 2)],
        [Position(2, 0), Position(2, 1), Position(2, 2)],
        # Columns
        [Position(0, 0), Position(1, 0), Position(2, 0)],
        [Position(0, 1), Position(1, 1), Position(2, 1)],
        [Position(0, 2), Position(1, 2), Position(2, 2)],
        # Diagonals
        [Position(0, 0), Position(1, 1), Position(2, 2)],
        [Position(0, 2), Position(1, 1), Position(2, 0)],
    ]

    @staticmethod
    def calculate_winner(board: Board) -> Optional[Mark]:
        """
        Calculate if there's a winner on the board
        Returns the winning mark or None
        """
        for line in GameRules.WIN_LINES:
            marks = {board.get_cell(pos) for pos in line}
            # If all three cells have the same mark and it's not empty
            if len(marks) == 1:
                mark = marks.pop()
                if mark != Mark.EMPTY:
                    return mark
        return None

    @staticmethod
    def calculate_status(board: Board, move_count: int) -> GameStatus:
        """
        Calculate the game status based on the board state
        """
        winner = GameRules.calculate_winner(board)

        if winner == Mark.X:
            return GameStatus.X_WON
        elif winner == Mark.O:
            return GameStatus.O_WON
        elif move_count == 9:  # Board is full
            return GameStatus.DRAW
        else:
            return GameStatus.IN_PROGRESS

    @staticmethod
    def is_valid_move(board: Board, position: Position) -> bool:
        """
        Check if a move is valid
        """
        try:
            return board.is_empty(position)
        except (ValueError, IndexError):
            return False

    @staticmethod
    def get_legal_moves(board: Board) -> List[Position]:
        """
        Get all legal moves for the current board
        """
        return board.get_empty_positions()

    @staticmethod
    def calculate_heuristic(status: GameStatus, for_player: Mark) -> float:
        """
        Calculate heuristic value for a game state
        Returns: 1.0 for win, -1.0 for loss, 0.0 for draw/in-progress
        """
        if status == GameStatus.X_WON:
            return 1.0 if for_player == Mark.X else -1.0
        elif status == GameStatus.O_WON:
            return 1.0 if for_player == Mark.O else -1.0
        else:
            return 0.0


class PlayerFactory:
    """
    Factory for creating player value objects
    Domain service for player-related business logic
    """

    @staticmethod
    def create_ai_player_id() -> str:
        """Create AI player ID"""
        return "AI"

    @staticmethod
    def is_ai_player(player_id: str) -> bool:
        """Check if player is AI"""
        return player_id == "AI"
