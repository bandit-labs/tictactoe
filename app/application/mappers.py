"""
Application Layer Mappers
Converts between domain entities and DTOs
Keeps domain layer isolated from presentation concerns
"""
from typing import List

from app.domain import Game
from .dtos import GameResponse


class GameMapper:
    """
    Maps Game entity to GameResponse DTO
    """

    @staticmethod
    def to_response(game: Game) -> GameResponse:
        """
        Convert Game entity to GameResponse DTO
        """
        board_list: List[List[str]] = [
            [cell.value for cell in row]
            for row in game.board.cells
        ]

        return GameResponse(
            id=game.id,
            player_x_id=game.player_x.id.value,
            player_x_name=game.player_x.name,
            player_o_id=game.player_o.id.value,
            player_o_name=game.player_o.name,
            status=game.status.value,
            next_player=game.next_player.value,
            move_count=game.move_count,
            mode=game.mode.value,
            ai_difficulty=game.ai_difficulty.value if game.ai_difficulty else None,
            board=board_list,
            created_at=game.created_at,
            finished_at=game.finished_at,
        )
