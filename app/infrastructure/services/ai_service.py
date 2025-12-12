"""
AI Service Implementation
Concrete implementation of IAIService interface
Communicates with external AI service via HTTP
"""

from typing import Dict, Any
import requests

from app.domain import (
    IAIService,
    Board,
    Mark,
    AIDifficulty,
    Position,
)
from app.core.config import settings


class HttpAIService(IAIService):
    """
    HTTP-based AI service implementation
    Calls external AI service via REST API
    """

    def __init__(self, base_url: str = None):
        """
        Initialize with AI service base URL
        """
        self.base_url = base_url or settings.ai_service_url.rstrip("/")

    def calculate_move(
        self,
        board: Board,
        current_player: Mark,
        difficulty: AIDifficulty,
    ) -> tuple[Position, float, Dict[str, Any]]:
        """
        Calculate the best move for the current player
        Calls external AI service
        """
        # Convert board to AI service format
        board_payload = [
            [None if cell == Mark.EMPTY else cell.value for cell in row]
            for row in board.cells
        ]

        # Get difficulty value (handle both enum and string gracefully)
        difficulty_value = (
            difficulty.value if isinstance(difficulty, AIDifficulty) else difficulty
        )

        # Build request payload
        payload: Dict[str, Any] = {
            "game": "tictactoe",
            "state": {
                "board": board_payload,
                "currentPlayer": current_player.value,
            },
            "difficulty": difficulty_value,
        }

        # Call AI service
        try:
            response = requests.post(
                f"{self.base_url}/api/ai/move",
                json=payload,
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            # Extract move data
            move_data = data["move"]
            row = move_data["row"]
            col = move_data["col"]
            evaluation = data.get("evaluation", 0.5)
            metadata = data.get("metadata", {})

            position = Position(row=row, col=col)

            return position, evaluation, metadata

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get AI move: {str(e)}") from e
