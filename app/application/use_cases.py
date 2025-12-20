"""
Use Cases - Application Service Layer
Orchestrates domain objects and coordinates with infrastructure
Each use case represents a single user action/intent
Follows Single Responsibility Principle
"""

import logging
import random
from typing import Optional, Callable, List

from sqlalchemy.orm import Session

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
from app.infrastructure.analytics.selfplay_repository import SelfPlayAnalyticsRepository
from datetime import datetime
import uuid

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


class RunSelfPlayGameUseCase:
    """
    Orchestrates AI vs AI game for dataset generation
    Writes ONLY to analytics tables (not operational tables)
    """

    def __init__(
        self,
        db: Session,  # Change from game_repository to db session
        ai_service: IAIService,
        state_serializer: IGameStateSerializer,
    ):
        self.db = db
        self.ai_service = ai_service
        self.state_serializer = state_serializer

    def execute(
        self,
        difficulty_x: str = "medium",
        difficulty_o: str = "medium",
        add_noise: bool = True,
    ) -> str | None:  # Returns game_id instead of Game entity
        """
        Run one complete AI vs AI game
        Logs ONLY to analytics (not operational tables)
        """

        repo = SelfPlayAnalyticsRepository(self.db)

        # Generate game ID
        game_id = str(uuid.uuid4())

        # Start game tracking
        repo.start_game(
            game_id=game_id,
            player_x_id="ai-selfplay-x",
            player_x_name=f"AI-X-{difficulty_x}",
            player_o_id="ai-selfplay-o",
            player_o_name=f"AI-O-{difficulty_o}",
            mode="pvp",  # AI vs AI
            ai_difficulty=f"{difficulty_x}vs{difficulty_o}",
            created_at=datetime.utcnow(),
        )

        logger.info(
            f"Started self-play game {game_id} (X:{difficulty_x} vs O:{difficulty_o})"
        )

        # Simulate game in-memory (no operational DB writes)
        from app.domain.value_objects import Board, Mark
        from app.domain.services import GameRules

        board = Board.empty()
        current_player = Mark.X
        move_number = 1
        game_over = False

        while not game_over:
            # Determine difficulty
            current_difficulty = (
                difficulty_x if current_player == Mark.X else difficulty_o
            )

            # Add noise
            if add_noise and random.random() < 0.15:
                difficulties = ["easy", "medium", "hard"]
                idx = difficulties.index(current_difficulty)
                if idx > 0:
                    current_difficulty = difficulties[idx - 1]

            # Get AI move
            position, evaluation, metadata = self.ai_service.calculate_move(
                board=board,
                current_player=current_player,
                difficulty=AIDifficulty(current_difficulty),
            )

            # Capture state before
            state_before = {
                "board": board.to_string(),
                "next_player": current_player.value,
            }

            # Apply move
            board = board.with_mark(position, current_player)

            # Capture state after
            state_after = {
                "board": board.to_string(),
                "next_player": current_player.opposite().value,
            }

            # Check if game over
            winner = GameRules.calculate_winner(board)
            is_draw = move_number >= 9 and winner is None
            game_over = (winner is not None) or is_draw

            # Calculate heuristic
            if winner == current_player:
                heuristic = 1.0
            elif winner is not None:
                heuristic = -1.0
            elif is_draw:
                heuristic = 0.0
            else:
                heuristic = evaluation

            # Log move to analytics
            repo.log_move(
                game_id=game_id,
                move_number=move_number,
                player_id=(
                    "ai-selfplay-x" if current_player == Mark.X else "ai-selfplay-o"
                ),
                mark=current_player.value,
                row=position.row,
                col=position.col,
                state_before=state_before,
                state_after=state_after,
                heuristic_value=heuristic,
                ai_metadata=metadata,
                created_at=datetime.utcnow(),
            )

            # Switch player
            current_player = current_player.opposite()
            move_number += 1

        # Finish game
        if winner == Mark.X:
            final_status = "X_win"
        elif winner == Mark.O:
            final_status = "O_win"
        else:
            final_status = "draw"

        repo.finish_game(
            game_id=game_id,
            status=final_status,
            move_count=move_number - 1,
            finished_at=datetime.utcnow(),
        )

        logger.info(
            f"Completed game {game_id}: {final_status} in {move_number - 1} moves"
        )
        return game_id


class RunBatchSelfPlayUseCase:
    """
    Runs multiple self-play games for dataset generation
    """

    def __init__(self, single_game_use_case: RunSelfPlayGameUseCase):
        self.single_game_use_case = single_game_use_case

    def execute(
        self,
        num_games: int,
        difficulty_x: str = "medium",
        difficulty_o: str = "medium",
        add_noise: bool = True,
        alternate_starting_player: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[str]:
        """
        Run multiple self-play games

        Args:
            num_games: Number of games to play
            difficulty_x: Base difficulty for X
            difficulty_o: Base difficulty for O
            add_noise: Add randomness for variety
            alternate_starting_player: Swap X/O difficulties each game
            progress_callback: Optional callback(current, total)

        Returns:
            List of completed game IDs
        """
        game_ids = []

        for i in range(num_games):
            # Alternate who starts with which difficulty
            if alternate_starting_player and i % 2 == 1:
                diff_x, diff_o = difficulty_o, difficulty_x
            else:
                diff_x, diff_o = difficulty_x, difficulty_o

            try:
                game_id = self.single_game_use_case.execute(
                    difficulty_x=diff_x, difficulty_o=diff_o, add_noise=add_noise
                )
                game_ids.append(game_id)

                if progress_callback:
                    progress_callback(i + 1, num_games)

            except Exception as e:
                logger.error(f"Game {i + 1}/{num_games} failed: {e}", exc_info=True)
                continue

        logger.info(
            f"Batch self-play completed: {len(game_ids)}/{num_games} games successful"
        )
        return game_ids
