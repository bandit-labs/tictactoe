"""
Repository Implementations
Concrete implementations of domain repository interfaces
Handles persistence using SQLAlchemy
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.domain import Game, IGameRepository
from app.infrastructure.orm_models import Game as ORMGame
from .mappers import GameORMMapper


class SQLAlchemyGameRepository(IGameRepository):
    """
    SQLAlchemy implementation of IGameRepository
    Follows Repository pattern to isolate persistence logic
    """

    def __init__(self, db_session: Session):
        """
        Initialize with a database session
        Session management is handled by the caller (application layer or API)
        """
        self.db_session = db_session

    def save(self, game: Game) -> Game:
        """
        Save a game (create or update)
        Handles both new games and updates to existing games
        """
        # Check if game already exists
        orm_game = self.db_session.get(ORMGame, game.id)

        if orm_game:
            # Update existing game
            GameORMMapper.to_orm(game, orm_game)
        else:
            # Create new game
            orm_game = GameORMMapper.to_orm(game)
            self.db_session.add(orm_game)

        # Add new moves (only those not yet persisted)
        persisted_move_numbers = {m.move_number for m in orm_game.moves}

        # Import here to avoid circular dependency
        from .mappers import MoveORMMapper
        from app.infrastructure.services.game_state_serializer import (
            GameStateSerializer,
        )

        serializer = GameStateSerializer()

        for move in game.moves_history:
            if move.move_number not in persisted_move_numbers:
                # Build states for move log
                # This is simplified - in production you'd want proper state tracking
                state_dict = serializer.serialize_game_state(game, include_history=True)

                orm_move = MoveORMMapper.to_orm(
                    move=move,
                    game_id=game.id,
                    state_before=state_dict,  # Simplified
                    state_after=state_dict,  # Simplified
                )
                self.db_session.add(orm_move)

        # Commit and refresh
        self.db_session.commit()
        self.db_session.refresh(orm_game)

        # Convert back to domain entity
        return GameORMMapper.to_domain(orm_game)

    def find_by_id(self, game_id: str) -> Optional[Game]:
        """
        Find game by ID
        Returns None if not found
        """
        orm_game = self.db_session.get(ORMGame, game_id)
        if not orm_game:
            return None

        return GameORMMapper.to_domain(orm_game)

    def delete(self, game_id: str) -> None:
        """
        Delete a game
        """
        orm_game = self.db_session.get(ORMGame, game_id)
        if orm_game:
            self.db_session.delete(orm_game)
            self.db_session.commit()
