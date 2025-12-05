"""
Game State Serializer Implementation
Concrete implementation of IGameStateSerializer interface
Serializes game state to dictionary format for API/platform
"""
from typing import Dict, Any, List

from app.domain import (
    IGameStateSerializer,
    Game,
    Mark,
    GameStatus,
)


class GameStateSerializer(IGameStateSerializer):
    """
    Serializes game state to dictionary format
    Used for API responses and platform communication
    """

    def serialize_game_state(
        self,
        game: Game,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        """
        Serialize game state to dictionary format
        """
        # Convert board (use '.' for empty cells for platform)
        board = [
            [
                "." if cell == Mark.EMPTY else cell.value
                for cell in row
            ]
            for row in game.board.cells
        ]

        # Calculate legal moves as indices
        legal_moves = [pos.to_index() for pos in game.get_legal_moves()]

        # Map game status
        if game.status == GameStatus.IN_PROGRESS:
            game_status = "IN_PROGRESS"
            winner = None
        elif game.status == GameStatus.DRAW:
            game_status = "DRAW"
            winner = None
        elif game.status == GameStatus.X_WON:
            game_status = "WIN"
            winner = "X"
        elif game.status == GameStatus.O_WON:
            game_status = "WIN"
            winner = "O"
        else:
            game_status = game.status.value
            winner = None

        # Build history
        history: List[Dict[str, Any]] = []
        if include_history:
            history = [
                {
                    "player": move.mark.value,
                    "move": move.to_index(),
                }
                for move in game.moves_history
            ]

        # Determine last updated timestamp
        if game.moves_history:
            last_timestamp = game.moves_history[-1].timestamp
        else:
            last_timestamp = game.created_at

        return {
            "game_id": game.id,
            "board": board,
            "current_player": game.next_player.value,
            "legal_moves": legal_moves,
            "move_count": game.move_count,
            "game_status": game_status,
            "winner": winner,
            "config": {"rows": 3, "cols": 3},
            "history": history,
            "last_updated": last_timestamp.isoformat(),
        }
