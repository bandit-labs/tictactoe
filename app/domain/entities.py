"""
Domain Entities - Rich domain models with identity and behavior
Following DDD principles for entities
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from .value_objects import (
    Board,
    Position,
    Mark,
    GameStatus,
    GameMode,
    AIDifficulty,
    PlayerId,
)
from .services import GameRules


@dataclass
class Player:
    """
    Represents a player in the game
    """

    id: PlayerId
    name: str
    mark: Mark

    def is_ai(self) -> bool:
        """Check if this player is AI"""
        return self.id.is_ai()


@dataclass
class Move:
    """
    Represents a single move in the game
    Entity with behavior and validation
    """

    position: Position
    mark: Mark
    player_id: PlayerId
    move_number: int
    heuristic_value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_index(self) -> int:
        """Get the linear index of this move"""
        return self.position.to_index()


@dataclass
class Game:
    """
    Rich domain entity representing a Tic-Tac-Toe game
    Contains business logic and enforces invariants
    """

    id: str
    player_x: Player
    player_o: Player
    mode: GameMode
    board: Board
    status: GameStatus
    next_player: Mark
    move_count: int
    moves_history: List[Move]
    ai_difficulty: Optional[AIDifficulty] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    @classmethod
    def create_new(
        cls,
        player_x_id: str,
        player_x_name: str,
        player_o_id: str,
        player_o_name: str,
        mode: GameMode,
        ai_difficulty: Optional[AIDifficulty] = None,
    ) -> Game:
        """
        Factory method to create a new game
        Enforces business rules for game creation
        """
        # Create players
        player_x = Player(id=PlayerId(player_x_id), name=player_x_name, mark=Mark.X)
        player_o = Player(id=PlayerId(player_o_id), name=player_o_name, mark=Mark.O)

        # Validate mode
        if mode == GameMode.PVAI and not player_o.is_ai():
            raise ValueError("In PVAI mode, player O must be AI")

        return cls(
            id=str(uuid4()),
            player_x=player_x,
            player_o=player_o,
            mode=mode,
            board=Board.empty(),
            status=GameStatus.IN_PROGRESS,
            next_player=Mark.X,
            move_count=0,
            moves_history=[],
            ai_difficulty=ai_difficulty,
        )

    def play_move(self, position: Position, player_id: PlayerId) -> Move:
        """
        Play a move on the board
        This is the core business logic method
        Enforces all game rules and invariants
        """
        # Validate game is in progress
        if self.status.is_finished():
            raise ValueError("Game is already finished")

        # Validate it's the correct player's turn
        current_player = self.get_current_player()
        if current_player.id != player_id:
            raise ValueError(
                f"It's {current_player.name}'s turn (expected {current_player.id.value}, got {player_id.value})"
            )

        # Validate move is legal
        if not GameRules.is_valid_move(self.board, position):
            raise ValueError(f"Invalid move at position {position}")

        # Calculate heuristic before making the move
        heuristic = GameRules.calculate_heuristic(self.status, self.next_player)

        # Apply the move (immutable board returns new board)
        self.board = self.board.with_mark(position, self.next_player)
        self.move_count += 1

        # Create move record
        move = Move(
            position=position,
            mark=self.next_player,
            player_id=player_id,
            move_number=self.move_count,
            heuristic_value=heuristic,
        )
        self.moves_history.append(move)

        # Update game status
        self.status = GameRules.calculate_status(self.board, self.move_count)

        # Update next player or finish game
        if self.status == GameStatus.IN_PROGRESS:
            self.next_player = self.next_player.opposite()
        else:
            # Game finished
            self.finished_at = datetime.utcnow()

        return move

    def get_current_player(self) -> Player:
        """Get the player whose turn it is"""
        if self.next_player == Mark.X:
            return self.player_x
        else:
            return self.player_o

    def get_winner(self) -> Optional[Player]:
        """Get the winner of the game if there is one"""
        if self.status == GameStatus.X_WON:
            return self.player_x
        elif self.status == GameStatus.O_WON:
            return self.player_o
        return None

    def is_finished(self) -> bool:
        """Check if game is finished"""
        return self.status.is_finished()

    def is_ai_turn(self) -> bool:
        """Check if it's AI's turn"""
        return self.mode == GameMode.PVAI and self.get_current_player().is_ai()

    def get_legal_moves(self) -> List[Position]:
        """Get all legal moves"""
        if self.is_finished():
            return []
        return GameRules.get_legal_moves(self.board)

    def can_player_move(self, player_id: PlayerId) -> bool:
        """Check if a specific player can make a move"""
        if self.is_finished():
            return False
        return self.get_current_player().id == player_id
