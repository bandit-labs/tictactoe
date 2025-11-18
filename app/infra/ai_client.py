from __future__ import annotations
from typing import Tuple

from app.domain.models import GameState, Mark
from app.domain.logic import legal_moves
import random


class AILevel(str):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


def choose_ai_move(
    state: GameState, ai_level: str = AILevel.EASY, ai_player: Mark = Mark.O
) -> Tuple[int, int]:
    """
    Placeholder AI.
    Later: call external AI Engine (HTTP or RabbitMQ).
    Now: random legal move so the plumbing is ready.
    """
    moves = legal_moves(state)
    if not moves:
        raise ValueError("No legal moves")

    # later you can vary behavior based on ai_level
    return random.choice(moves)
