"""
Platform Service Implementation
Concrete implementation of IPlatformService interface
Communicates with platform backend via HTTP
"""

import logging
from typing import List, Dict, Any
import requests

from app.domain import (
    IPlatformService,
    Game,
    Move,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class HttpPlatformService(IPlatformService):
    """
    HTTP-based platform service implementation
    Logs game events to platform backend via REST API
    """

    def __init__(self, base_url: str = None):
        """
        Initialize with platform backend base URL
        """
        self.base_url = base_url or settings.platform_backend_url.rstrip("/")

    def log_move(
        self,
        game: Game,
        move: Move,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
    ) -> None:
        """
        Log a move to the platform
        Fire-and-forget: logs errors but doesn't raise exceptions
        """
        entry = {
            "game_id": game.id,
            "player_id": move.player_id.value,
            "move_index": move.to_index(),
            "move_number": move.move_number,
            "previous_state": state_before,
            "next_state": state_after,
            "timestamp": state_after.get("last_updated"),
            "heuristic_value": move.heuristic_value,
        }

        try:
            response = requests.post(
                f"{self.base_url}/game-sessions/moves",
                json=entry,
                timeout=5,
            )
            response.raise_for_status()
            logger.info("Logged move to platform backend for game %s", game.id)
        except requests.RequestException as e:
            logger.error("Failed to log move to platform: %s", e)

    def send_final_result(
        self,
        game: Game,
        final_state: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> None:
        """
        Send final game result to platform
        Fire-and-forget: logs errors but doesn't raise exceptions
        """
        result = {
            "game_id": game.id,
            "winner": final_state.get("winner"),
            "history": history,
            "final_state": final_state,
        }

        try:
            response = requests.post(
                f"{self.base_url}/game-sessions/results",
                json=result,
                timeout=5,
            )
            response.raise_for_status()
            logger.info("Sent final result to platform backend for game %s", game.id)
        except requests.RequestException as e:
            logger.error("Failed to send final result to platform: %s", e)
