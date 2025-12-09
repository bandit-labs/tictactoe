"""
Domain Layer - Core business logic
This is the heart of the application with no external dependencies
"""

# Value Objects
from .value_objects import (
    Mark,
    GameStatus,
    GameMode,
    AIDifficulty,
    Position,
    PlayerId,
    Board,
)

# Entities
from .entities import (
    Player,
    Move,
    Game,
)

# Domain Services
from .services import (
    GameRules,
    PlayerFactory,
)

# Interfaces (Ports)
from .interfaces import (
    IGameRepository,
    IAIService,
    IPlatformService,
    IGameStateSerializer,
)

__all__ = [
    # Value Objects
    "Mark",
    "GameStatus",
    "GameMode",
    "AIDifficulty",
    "Position",
    "PlayerId",
    "Board",
    # Entities
    "Player",
    "Move",
    "Game",
    # Domain Services
    "GameRules",
    "PlayerFactory",
    # Interfaces
    "IGameRepository",
    "IAIService",
    "IPlatformService",
    "IGameStateSerializer",
]
