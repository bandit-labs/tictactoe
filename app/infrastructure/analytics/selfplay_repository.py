"""
Self-Play Repository
Writes AI vs AI games ONLY to analytics tables (bypasses operational tables)
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.application.analytics_models import GameAnalytics, MoveAnalytics


class SelfPlayAnalyticsRepository:
    """
    Repository for self-play games that writes ONLY to analytics tables
    Does NOT write to operational Game/MoveLog tables
    """

    def __init__(self, db: Session):
        self.db = db
        self._current_game_id = None
        self._current_game_data = None

    def start_game(
        self,
        game_id: str,
        player_x_id: str,
        player_x_name: str,
        player_o_id: str,
        player_o_name: str,
        mode: str,
        ai_difficulty: str,
        created_at: datetime,
    ) -> None:
        """Initialize game tracking (in-memory, written on first move)"""
        self._current_game_id = game_id
        self._current_game_data = {
            "game_id": game_id,
            "player_x_id": player_x_id,
            "player_o_id": player_o_id,
            "player_x_name": player_x_name,
            "player_o_name": player_o_name,
            "mode": mode,
            "ai_difficulty": ai_difficulty,
            "status": "in_progress",
            "move_count": 0,
            "created_at": created_at,
            "finished_at": None,
        }

    def log_move(
        self,
        game_id: str,
        move_number: int,
        player_id: str,
        mark: str,
        row: int,
        col: int,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        heuristic_value: float,
        ai_metadata: Dict[str, Any],
        created_at: datetime,
    ) -> None:
        """Log move to analytics table"""

        # Ensure game exists in analytics
        game_analytics = (
            self.db.query(GameAnalytics)
            .filter(GameAnalytics.game_id == game_id)
            .first()
        )

        if not game_analytics:
            # First move - create game record
            game_analytics = GameAnalytics(**self._current_game_data)
            self.db.add(game_analytics)
            self.db.flush()

        # Log the move
        move = MoveAnalytics(
            game_id=game_id,
            move_number=move_number,
            player_id=player_id,
            mark=mark,
            row=row,
            col=col,
            state_before=state_before,
            state_after=state_after,
            heuristic_value=heuristic_value,
            ai_metadata=ai_metadata,
            created_at=created_at,
        )
        self.db.add(move)
        self.db.commit()

    def finish_game(
        self, game_id: str, status: str, move_count: int, finished_at: datetime
    ) -> None:
        """Update game with final status"""
        game_analytics = (
            self.db.query(GameAnalytics)
            .filter(GameAnalytics.game_id == game_id)
            .first()
        )

        if game_analytics:
            game_analytics.status = status
            game_analytics.move_count = move_count
            game_analytics.finished_at = finished_at
            self.db.commit()
