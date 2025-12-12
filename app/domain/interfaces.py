"""
Domain Interfaces (Ports) - Abstractions for external dependencies
Following Hexagonal Architecture / Ports & Adapters pattern
Domain depends on these abstractions, not on concrete implementations
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from .entities import Game, Move
from .value_objects import Position, AIDifficulty, Board, Mark


class IGameRepository(ABC):
    """
    Repository interface for Game aggregate
    Abstraction for persistence operations
    """

    @abstractmethod
    def save(self, game: Game) -> Game:
        """Save a game (create or update)"""
        pass

    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]:
        """Find game by ID"""
        pass

    @abstractmethod
    def delete(self, game_id: str) -> None:
        """Delete a game"""
        pass


class IAIService(ABC):
    """
    Service interface for AI move calculation
    Abstraction for external AI service
    """

    @abstractmethod
    def calculate_move(
        self,
        board: Board,
        current_player: Mark,
        difficulty: AIDifficulty,
    ) -> tuple[Position, float, Dict[str, Any]]:
        """
        Calculate the best move for the current player
        Returns: (position, evaluation, metadata)
        """
        pass


class IPlatformService(ABC):
    """
    Service interface for platform integration
    Abstraction for external platform API calls
    """

    @abstractmethod
    def log_move(
        self,
        game: Game,
        move: Move,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
    ) -> None:
        """Log a move to the platform"""
        pass

    @abstractmethod
    def send_final_result(
        self,
        game: Game,
        final_state: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> None:
        """Send final game result to platform"""
        pass


class IGameStateSerializer(ABC):
    """
    Service interface for serializing game state
    Used for platform communication and logging
    """

    @abstractmethod
    def serialize_game_state(
        self,
        game: Game,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        """
        Serialize game state to dictionary format
        Used for API responses and platform communication
        """
        pass
