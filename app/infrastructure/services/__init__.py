"""
External Services Layer
Implementations of domain service interfaces
"""

from .ai_service import HttpAIService
from .platform_service import HttpPlatformService
from .game_state_serializer import GameStateSerializer

__all__ = [
    "HttpAIService",
    "HttpPlatformService",
    "GameStateSerializer",
]
