"""
Use Cases - Application Service Layer
Orchestrates domain objects and coordinates with infrastructure
Each use case represents a single user action/intent
Follows Single Responsibility Principle
"""

import logging
from typing import Optional

from app.domain import (
    Game,
    GameMode,
    AIDifficulty,
    Position,
    PlayerId,
    IGameRepository,
    IAIService,
    IPlatformService,
    IGameStateSerializer,
    PlayerFactory,
)
from .dtos import (
    CreateGameCommand,
    PlayMoveCommand,
    GetGameQuery,
)

logger = logging.getLogger(__name__)


class CreateGameUseCase:
    """
    Use case for creating a new game
    Responsibility: Orchestrate game creation with proper validation
    """

    def __init__(self, game_repository: IGameRepository):
        self.game_repository = game_repository

    def execute(self, command: CreateGameCommand) -> Game:
        """
        Execute the create game use case
        """
        # Determine player O based on mode
        if command.mode == "pvai":
            player_o_id = PlayerFactory.create_ai_player_id()
            player_o_name = "AI"
        elif command.mode == "pvp":
            if not command.player_o_id:
                raise ValueError("Player O ID is required for PvP mode")
            player_o_id = command.player_o_id
            player_o_name = command.player_o_name or "Player O"
        else:
            raise ValueError(f"Invalid game mode: {command.mode}")

        # Set player X name
        player_x_name = command.player_x_name or "Player X"

        # Parse AI difficulty
        ai_difficulty = None
        if command.mode == "pvai" and command.ai_difficulty:
            ai_difficulty = AIDifficulty(command.ai_difficulty)

        # Create game entity (rich domain model)
        game = Game.create_new(
            player_x_id=command.player_x_id,
            player_x_name=player_x_name,
            player_o_id=player_o_id,
            player_o_name=player_o_name,
            mode=GameMode(command.mode),
            ai_difficulty=ai_difficulty,
        )

        # Persist the game
        game = self.game_repository.save(game)

        return game


class GetGameUseCase:
    """
    Use case for retrieving a game
    Responsibility: Fetch game by ID
    """

    def __init__(self, game_repository: IGameRepository):
        self.game_repository = game_repository

    def execute(self, query: GetGameQuery) -> Optional[Game]:
        """
        Execute the get game use case
        """
        return self.game_repository.find_by_id(query.game_id)


class PlayMoveUseCase:
    """
    Use case for playing a move
    Responsibility: Orchestrate move playing, AI moves, and platform logging
    """

    def __init__(
        self,
        game_repository: IGameRepository,
        ai_service: IAIService,
        platform_service: IPlatformService,
        state_serializer: IGameStateSerializer,
    ):
        self.game_repository = game_repository
        self.ai_service = ai_service
        self.platform_service = platform_service
        self.state_serializer = state_serializer

    def execute(self, command: PlayMoveCommand) -> Game:
        """
        Execute the play move use case
        Handles both human and AI moves
        """
        # Fetch the game
        game = self.game_repository.find_by_id(command.game_id)
        if not game:
            raise ValueError("Game not found")

        # Determine if this is an AI move
        is_ai_move = game.is_ai_turn() and (command.row is None or command.col is None)

        # Calculate position
        if is_ai_move:
            # AI move - call AI service
            # Convert string difficulty to enum if needed
            if command.ai_difficulty:
                difficulty = AIDifficulty(command.ai_difficulty)
            elif game.ai_difficulty:
                difficulty = game.ai_difficulty
            else:
                difficulty = AIDifficulty.MEDIUM

            position, evaluation, _metadata = self.ai_service.calculate_move(
                board=game.board,
                current_player=game.next_player,
                difficulty=difficulty,
            )
        else:
            # Human move - use provided coordinates
            if command.row is None or command.col is None:
                raise ValueError("Row and col are required for human moves")
            position = Position(row=command.row, col=command.col)

        # Capture state before move for logging
        state_before = self.state_serializer.serialize_game_state(game)

        # Play the move (domain logic)
        player_id = (
            PlayerId(command.player_id)
            if not is_ai_move
            else PlayerId(PlayerFactory.create_ai_player_id())
        )
        move = game.play_move(position, player_id)

        # Persist the updated game
        game = self.game_repository.save(game)

        # Capture state after move
        state_after = self.state_serializer.serialize_game_state(game)

        # Log to platform (fire and forget - don't break on failure)
        try:
            self.platform_service.log_move(
                game=game,
                move=move,
                state_before=state_before,
                state_after=state_after,
            )

            # If game finished, send final result
            if game.is_finished():
                history = [
                    {
                        "player": m.mark.value,
                        "move": m.to_index(),
                        "move_number": m.move_number,
                    }
                    for m in game.moves_history
                ]
                self.platform_service.send_final_result(
                    game=game,
                    final_state=state_after,
                    history=history,
                )
        except Exception as e:
            # Log the error message and traceback
            logger.error(
                "Platform logging failed (gameplay unaffected): %s", e, exc_info=True
            )

            # Don't break gameplay if platform logging fails
            pass

        return game


class PlayAIMoveUseCase:
    """
    Use case specifically for AI moves (triggered in background)
    Responsibility: Orchestrate AI move independently
    """

    def __init__(
        self,
        game_repository: IGameRepository,
        ai_service: IAIService,
        platform_service: IPlatformService,
        state_serializer: IGameStateSerializer,
    ):
        self.game_repository = game_repository
        self.ai_service = ai_service
        self.platform_service = platform_service
        self.state_serializer = state_serializer

    def execute(self, game_id: str, ai_difficulty: Optional[str] = None) -> Game:
        """
        Execute AI move
        Used for background task execution
        """
        command = PlayMoveCommand(
            game_id=game_id,
            player_id=PlayerFactory.create_ai_player_id(),
            row=None,
            col=None,
            ai_difficulty=ai_difficulty,
        )

        play_move_use_case = PlayMoveUseCase(
            game_repository=self.game_repository,
            ai_service=self.ai_service,
            platform_service=self.platform_service,
            state_serializer=self.state_serializer,
        )

        return play_move_use_case.execute(command)
