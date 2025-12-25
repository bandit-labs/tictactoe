"""
ML Service Client
Communicates with external ML prediction service via HTTP
"""

from typing import Dict, Any, List, Optional
import requests

from app.core.config import settings


class HttpMLService:
    """
    HTTP-based ML service client
    Calls external ML service for predictions (hints, win probability, etc.)
    """

    def __init__(self, base_url: str = None):
        """
        Initialize with ML service base URL
        """
        self.base_url = base_url or settings.ml_service_url.rstrip("/")

    def get_hint(
        self,
        board: List[List[Optional[str]]],
        current_player: str,
    ) -> Dict[str, Any]:
        """
        Get a hint for the next move from ML service

        Args:
            board: 3x3 board state (None for empty, "X" or "O" for occupied)
            current_player: Current player ("X" or "O")

        Returns:
            Dictionary containing:
            - suggested_move: {"row": int, "col": int}
            - win_probability: float
            - confidence: float
            - metadata: dict
        """
        # Build request payload
        payload: Dict[str, Any] = {
            "game": "tictactoe",
            "state": {
                "board": board,
                "currentPlayer": current_player,
            },
        }

        # Call ML service hint endpoint
        try:
            response = requests.post(
                f"{self.base_url}/api/ml/hint",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get hint from ML service: {str(e)}") from e

    def predict_win_probability(
        self,
        board: List[List[Optional[str]]],
        current_player: str,
        move_number: Optional[int] = None,
    ) -> float:
        """
        Predict win probability for current game state

        Args:
            board: 3x3 board state
            current_player: Current player ("X" or "O")
            move_number: Optional move number

        Returns:
            Win probability (0.0 to 1.0)
        """
        payload: Dict[str, Any] = {
            "board": board,
            "current_player": current_player,
        }

        if move_number is not None:
            payload["move_number"] = move_number

        try:
            response = requests.post(
                f"{self.base_url}/api/ml/win-probability/predict",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["win_probability"]

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to predict win probability: {str(e)}") from e

    def predict_policy(
        self,
        board: List[List[Optional[str]]],
        current_player: str,
    ) -> Dict[str, Any]:
        """
        Predict best move using policy imitation model

        Args:
            board: 3x3 board state
            current_player: Current player ("X" or "O")

        Returns:
            Dictionary containing:
            - move: {"row": int, "col": int}
            - probabilities: list of floats
            - metadata: dict
        """
        payload: Dict[str, Any] = {
            "board": board,
            "current_player": current_player,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/ml/policy/predict",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to predict policy: {str(e)}") from e
