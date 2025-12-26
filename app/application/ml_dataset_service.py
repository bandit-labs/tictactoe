"""
ML Dataset Export Service
Exports analytics data in format ready for ML training
"""

import os
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.application.analytics_models import GameAnalytics, MoveAnalytics


def _extract_board_string(state_json: Dict) -> str:
    """
    Extract 9-character board string from state JSON
    Format: "XXO......" where . = empty
    """
    if "board" in state_json:
        board = state_json["board"]
        if isinstance(board, str) and len(board) == 9:
            return board
        elif isinstance(board, list):
            # Convert 2D list to string
            flat = []
            for row in board:
                for cell in row:
                    if cell is None or cell == "EMPTY":
                        flat.append(".")
                    else:
                        flat.append(cell)
            return "".join(flat)
    return "." * 9  # Empty board fallback


def _calculate_legal_moves(board_str: str) -> str:
    """
    Calculate legal moves mask from board string
    Returns: 9-char binary string, e.g., "101010101"
    """
    # Empty positions can be either '.' or ' ' (space)
    return "".join("1" if c not in ("X", "O") else "0" for c in board_str)


def _map_outcome(status: str) -> str:
    """Map GameAnalytics status to standard outcome"""
    status_lower = status.lower()
    if "x" in status_lower and "win" in status_lower:
        return "X_win"
    elif "o" in status_lower and "win" in status_lower:
        return "O_win"
    else:
        return "draw"


def _outcome_from_perspective(outcome: str, player_mark: str) -> int:
    """
    Get outcome value from player's perspective
    1 = win, 0 = draw, -1 = loss
    """
    if outcome == "draw":
        return 0
    elif (outcome == "X_win" and player_mark == "X") or (
        outcome == "O_win" and player_mark == "O"
    ):
        return 1
    else:
        return -1


class MLDatasetExportService:
    """
    Service for exporting ML-ready datasets from analytics

    Dataset Schema for Part 2b:
    - Policy Imitation Model: needs (state, best_move) pairs
    - Win Probability Model: needs (state, outcome) pairs
    """

    def __init__(self, db: Session):
        self.db = db

    def export_to_dataframe(
        self,
        min_games: Optional[int] = None,
        max_games: Optional[int] = None,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        mode_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Export analytics to pandas DataFrame with ML-ready schema

        Returns DataFrame with columns:
        - game_id: str
        - move_number: int
        - player_mark: str ('X' or 'O')
        - position_row: int (0-2)
        - position_col: int (0-2)
        - position_index: int (0-8) - for classification
        - board_before: str (9-char string like "XXO......")
        - board_after: str
        - legal_moves_mask: str (9-char binary like "001101010")
        - ai_difficulty: str
        - heuristic_value: float
        - game_outcome: str ('X_win', 'O_win', 'draw')
        - outcome_from_perspective: int (1=win, 0=draw, -1=loss)
        - moves_to_end: int
        - ai_metadata: dict (MCTS stats if available)
        """

        # Build query
        query = (
            self.db.query(
                GameAnalytics.game_id,
                GameAnalytics.mode,
                GameAnalytics.ai_difficulty,
                GameAnalytics.status,
                GameAnalytics.move_count,
                GameAnalytics.created_at,
                MoveAnalytics.move_number,
                MoveAnalytics.player_id,
                MoveAnalytics.mark,
                MoveAnalytics.row,
                MoveAnalytics.col,
                MoveAnalytics.state_before,
                MoveAnalytics.state_after,
                MoveAnalytics.heuristic_value,
                MoveAnalytics.ai_metadata,
            )
            .join(MoveAnalytics, GameAnalytics.game_id == MoveAnalytics.game_id)
            .filter(
                GameAnalytics.status.in_(
                    ["X_win", "O_win", "draw"]
                )  # Only completed games
            )
        )

        # Apply filters
        if mode_filter:
            query = query.filter(GameAnalytics.mode == mode_filter)
        if min_date:
            query = query.filter(GameAnalytics.created_at >= min_date)
        if max_date:
            query = query.filter(GameAnalytics.created_at <= max_date)

        query = query.order_by(GameAnalytics.created_at, MoveAnalytics.move_number)

        # Limit games if specified
        if max_games:
            # Get game IDs first, then filter
            game_ids_query = (
                self.db.query(GameAnalytics.game_id)
                .filter(GameAnalytics.status.in_(["X_win", "O_win", "draw"]))
                .order_by(GameAnalytics.created_at)
                .limit(max_games)
            )
            game_ids = [row[0] for row in game_ids_query]
            query = query.filter(GameAnalytics.game_id.in_(game_ids))

        # Execute query
        results = query.all()

        # Transform to records
        records = []
        for row in results:
            # Extract board state from JSON
            board_before = _extract_board_string(row.state_before)
            board_after = _extract_board_string(row.state_after)

            # Calculate legal moves mask
            legal_moves = _calculate_legal_moves(board_before)

            # Map outcome
            outcome = _map_outcome(row.status)

            # Outcome from current player's perspective
            outcome_value = _outcome_from_perspective(outcome, row.mark)

            # Moves to end
            moves_to_end = row.move_count - row.move_number

            record = {
                "game_id": row.game_id,
                "move_number": row.move_number,
                "player_mark": row.mark,
                "position_row": row.row,
                "position_col": row.col,
                "position_index": row.row * 3 + row.col,
                "board_before": board_before,
                "board_after": board_after,
                "legal_moves_mask": legal_moves,
                "ai_difficulty": row.ai_difficulty or "unknown",
                "heuristic_value": row.heuristic_value,
                "game_outcome": outcome,
                "outcome_from_perspective": outcome_value,
                "moves_to_end": moves_to_end,
                "ai_metadata": row.ai_metadata or {},
            }
            records.append(record)

        df = pd.DataFrame(records)
        return df

    def export_to_parquet(self, output_path: str, **kwargs) -> Dict[str, Any]:
        """
        Export to Parquet file

        Returns:
            Statistics about the export
        """
        df = self.export_to_dataframe(**kwargs)

        # Export to Parquet
        df.to_parquet(output_path, index=False, engine="pyarrow")

        # Calculate statistics
        stats = {
            "total_moves": len(df),
            "total_games": df["game_id"].nunique(),
            "outcomes": df.groupby("game_outcome").size().to_dict(),
            "avg_moves_per_game": df.groupby("game_id")["move_number"].max().mean(),
            "difficulties": df["ai_difficulty"].value_counts().to_dict(),
            "file_size_mb": os.path.getsize(output_path) / (1024 * 1024),
        }

        return stats
