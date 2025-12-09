from __future__ import annotations
import logging
from typing import List, Dict, Any
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


def log_move_to_platform(
    previous_state: Dict[str, Any],
    new_state: Dict[str, Any],
    move_index: int,
    player_id: str,
    heuristic_value: float = 0.0,
) -> None:
    entry = {
        "game_id": new_state["game_id"],
        "player_id": player_id,
        "move_index": move_index,
        "move_number": new_state["move_count"],
        "previous_state": previous_state,
        "next_state": new_state,
        "timestamp": new_state["last_updated"],
        "heuristic_value": heuristic_value,
    }

    try:
        r = requests.post(
            f"{settings.platform_backend_url}/game-sessions/moves",
            json=entry,
            timeout=5,
        )
        r.raise_for_status()
        logger.info("Logged move to platform backend for game %s", new_state["game_id"])
    except Exception as e:
        logger.error("Failed to log move to platform: %s", e)


def send_final_result_to_platform(
    final_state: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> None:
    result = {
        "game_id": final_state["game_id"],
        "winner": final_state["winner"],
        "history": history,
        "final_state": final_state,
    }

    try:
        r = requests.post(
            f"{settings.platform_backend_url}/game-sessions/results",
            json=result,
            timeout=5,
        )
        r.raise_for_status()
        logger.info(
            "Sent final result to platform backend for game %s", final_state["game_id"]
        )
    except Exception as e:
        logger.error("Failed to send final result to platform: %s", e)
