"""
Dependency Injection Container
Wires together all layers following Dependency Inversion Principle
FastAPI dependencies for clean dependency injection
"""

from functools import lru_cache
from sqlalchemy.orm import Session

from app.core.config import settings

# Domain interfaces
from app.domain import (
    IGameRepository,
    IAIService,
    IPlatformService,
    IGameStateSerializer,
)

# Infrastructure implementations
from app.infrastructure import (
    SQLAlchemyGameRepository,
    HttpAIService,
    HttpPlatformService,
    GameStateSerializer,
)

# Application use cases
from app.application import (
    CreateGameUseCase,
    GetGameUseCase,
    PlayMoveUseCase,
    PlayAIMoveUseCase,
)


# Infrastructure Dependencies


@lru_cache()
def get_ai_service() -> IAIService:
    """
    Get AI service instance (singleton)
    """
    return HttpAIService(base_url=settings.ai_service_url)


@lru_cache()
def get_platform_service() -> IPlatformService:
    """
    Get platform service instance (singleton)
    """
    return HttpPlatformService(base_url=settings.platform_backend_url)


@lru_cache()
def get_game_state_serializer() -> IGameStateSerializer:
    """
    Get game state serializer instance (singleton)
    """
    return GameStateSerializer()


def get_game_repository(db: Session) -> IGameRepository:
    """
    Get game repository instance (scoped to request)
    """
    return SQLAlchemyGameRepository(db_session=db)


# Use Case Dependencies


def get_create_game_use_case(
    repository: IGameRepository,
) -> CreateGameUseCase:
    """
    Get CreateGameUseCase with injected dependencies
    """
    return CreateGameUseCase(game_repository=repository)


def get_get_game_use_case(
    repository: IGameRepository,
) -> GetGameUseCase:
    """
    Get GetGameUseCase with injected dependencies
    """
    return GetGameUseCase(game_repository=repository)


def get_play_move_use_case(
    repository: IGameRepository,
    ai_service: IAIService,
    platform_service: IPlatformService,
    state_serializer: IGameStateSerializer,
) -> PlayMoveUseCase:
    """
    Get PlayMoveUseCase with injected dependencies
    """
    return PlayMoveUseCase(
        game_repository=repository,
        ai_service=ai_service,
        platform_service=platform_service,
        state_serializer=state_serializer,
    )


def get_play_ai_move_use_case(
    repository: IGameRepository,
    ai_service: IAIService,
    platform_service: IPlatformService,
    state_serializer: IGameStateSerializer,
) -> PlayAIMoveUseCase:
    """
    Get PlayAIMoveUseCase with injected dependencies
    """
    return PlayAIMoveUseCase(
        game_repository=repository,
        ai_service=ai_service,
        platform_service=platform_service,
        state_serializer=state_serializer,
    )
