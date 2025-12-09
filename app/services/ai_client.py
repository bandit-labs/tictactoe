from __future__ import annotations
from typing import Any, Dict
import requests
from app.core.config import settings
from app.domain.models import GameState, Mark

AI_BASE_URL = settings.ai_service_url.rstrip("/")


def _state_to_ai_model_payload(state: GameState) -> dict:
    """
    Convert our domain GameState into the AiMoveRequest.state format:
    {
      "board": [[None | "X" | "O"]],
      "currentPlayer": "X" | "O"
    }
    """
    board_payload: list[list[str | None]] = []
    for row in state.board:
        row_payload: list[str | None] = []
        for cell in row:
            if cell == Mark.EMPTY:
                row_payload.append(None)
            else:
                row_payload.append(cell.value)
        board_payload.append(row_payload)

    return {
        "board": board_payload,
        "currentPlayer": state.next_player.value,
    }


def request_ai_move(
    state: GameState,
    difficulty: str = "medium",
) -> tuple[tuple[int, int], float, dict]:
    """
    Call external AI service and return (row, col), evaluation, metadata.
    """
    board_for_ai = [
        [None if cell == Mark.EMPTY else cell.value for cell in row]
        for row in state.board
    ]

    payload: Dict[str, Any] = {
        "game": "tictactoe",
        "state": {
            "board": board_for_ai,
            "currentPlayer": state.next_player.value,
        },
        "difficulty": difficulty,
    }

    resp = requests.post(f"{AI_BASE_URL}/api/ai/move", json=payload, timeout=5)
    resp.raise_for_status()
    data = resp.json()

    move = data["move"]
    row = move["row"]
    col = move["col"]
    evaluation = data.get("evaluation", 0.5)
    metadata = data.get("metadata", {})

    return (row, col), evaluation, metadata
