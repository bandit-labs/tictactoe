"""
Infrastructure Mappers
Converts between domain entities and ORM models
Isolates domain from persistence concerns
"""
from typing import List

from app.domain import (
    Game,
    Player,
    Move,
    PlayerId,
    Mark,
    GameMode,
    AIDifficulty,
    Board,
    Position,
)
from app.infrastructure.orm_models import Game as ORMGame, MoveLog as ORMMoveLog


class GameORMMapper:
    """
    Maps between Game entity and ORM Game model
    Handles bidirectional conversion
    """

    @staticmethod
    def to_orm(game: Game, orm_game: ORMGame = None) -> ORMGame:
        """
        Convert domain Game entity to ORM Game model
        If orm_game is provided, updates it; otherwise creates new
        """
        if orm_game is None:
            orm_game = ORMGame(id=game.id)

        # Map basic attributes
        orm_game.player_x_id = game.player_x.id.value
        orm_game.player_o_id = game.player_o.id.value
        orm_game.player_x_name = game.player_x.name
        orm_game.player_o_name = game.player_o.name
        orm_game.status = game.status
        orm_game.next_player = game.next_player
        orm_game.move_count = game.move_count
        orm_game.mode = game.mode.value
        orm_game.ai_difficulty = game.ai_difficulty.value if game.ai_difficulty else None
        orm_game.board_state = game.board.to_string()
        orm_game.created_at = game.created_at
        orm_game.finished_at = game.finished_at

        return orm_game

    @staticmethod
    def to_domain(orm_game: ORMGame) -> Game:
        """
        Convert ORM Game model to domain Game entity
        Reconstructs the rich domain model from persistence
        """
        # Parse board
        board = Board.from_string(orm_game.board_state)

        # Create players
        player_x = Player(
            id=PlayerId(orm_game.player_x_id),
            name=orm_game.player_x_name,
            mark=Mark.X,
        )
        player_o = Player(
            id=PlayerId(orm_game.player_o_id),
            name=orm_game.player_o_name,
            mark=Mark.O,
        )

        # Parse AI difficulty
        ai_difficulty = None
        if orm_game.ai_difficulty:
            ai_difficulty = AIDifficulty(orm_game.ai_difficulty)

        # Reconstruct moves history
        moves_history: List[Move] = []
        if orm_game.moves:
            for orm_move in sorted(orm_game.moves, key=lambda m: m.move_number):
                move = Move(
                    position=Position(row=orm_move.row, col=orm_move.col),
                    mark=orm_move.mark,
                    player_id=PlayerId(orm_move.player_id),
                    move_number=orm_move.move_number,
                    heuristic_value=orm_move.heuristic_value,
                    timestamp=orm_move.created_at,
                )
                moves_history.append(move)

        # Create domain Game entity
        game = Game(
            id=orm_game.id,
            player_x=player_x,
            player_o=player_o,
            mode=GameMode(orm_game.mode),
            board=board,
            status=orm_game.status,
            next_player=orm_game.next_player,
            move_count=orm_game.move_count,
            moves_history=moves_history,
            ai_difficulty=ai_difficulty,
            created_at=orm_game.created_at,
            finished_at=orm_game.finished_at,
        )

        return game


class MoveORMMapper:
    """
    Maps between Move entity and ORM MoveLog model
    """

    @staticmethod
    def to_orm(
        move: Move,
        game_id: str,
        state_before: dict,
        state_after: dict,
    ) -> ORMMoveLog:
        """
        Convert domain Move entity to ORM MoveLog model
        """
        return ORMMoveLog(
            game_id=game_id,
            move_number=move.move_number,
            player_id=move.player_id.value,
            mark=move.mark,
            row=move.position.row,
            col=move.position.col,
            state_before=state_before,
            state_after=state_after,
            heuristic_value=move.heuristic_value,
            created_at=move.timestamp,
        )
