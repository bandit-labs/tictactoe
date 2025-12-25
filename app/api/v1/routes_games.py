"""
Game API Routes (Refactored)
Presentation layer using clean architecture with dependency injection
Thin controllers that delegate to use cases
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import (
    get_game_repository,
    get_create_game_use_case,
    get_get_game_use_case,
    get_play_move_use_case,
    get_ai_service,
    get_ml_service,
    get_platform_service,
    get_game_state_serializer,
)

from app.domain import (
    IAIService,
    IPlatformService,
    IGameStateSerializer,
    GameStatus,
    PlayerFactory,
    Mark,
    Position,
)

from app.application import (
    CreateGameCommand,
    PlayMoveCommand,
    GetGameQuery,
    GameResponse,
    CreateGameUseCase,
    GetGameUseCase,
    PlayMoveUseCase,
    GameMapper,
)

from app.schemas.game import GameCreate
from app.schemas.move import MoveCreate

router = APIRouter(prefix="/games", tags=["games"])


# Dependency Injection Helpers


def inject_create_game_use_case(
    db: Session = Depends(get_db),
) -> CreateGameUseCase:
    """Inject CreateGameUseCase with all dependencies"""
    repository = get_game_repository(db)
    return get_create_game_use_case(repository)


def inject_get_game_use_case(
    db: Session = Depends(get_db),
) -> GetGameUseCase:
    """Inject GetGameUseCase with all dependencies"""
    repository = get_game_repository(db)
    return get_get_game_use_case(repository)


def inject_play_move_use_case(
    db: Session = Depends(get_db),
    ai_service: IAIService = Depends(get_ai_service),
    platform_service: IPlatformService = Depends(get_platform_service),
    state_serializer: IGameStateSerializer = Depends(get_game_state_serializer),
) -> PlayMoveUseCase:
    """Inject PlayMoveUseCase with all dependencies"""
    repository = get_game_repository(db)
    return get_play_move_use_case(
        repository,
        ai_service,
        platform_service,
        state_serializer,
    )


# API Endpoints


@router.post("", response_model=GameResponse)
def create_game_endpoint(
    payload: GameCreate,
    use_case: CreateGameUseCase = Depends(inject_create_game_use_case),
):
    """
    Create a new game session
    Delegates to CreateGameUseCase
    """
    try:
        # Convert schema to command
        command = CreateGameCommand(
            player_x_id=payload.player_x_id,
            player_x_name=payload.player_x_name,
            player_o_id=payload.player_o_id,
            player_o_name=payload.player_o_name,
            mode=payload.mode,
            ai_difficulty=payload.ai_difficulty,
        )
        game = use_case.execute(command)
        return GameMapper.to_response(game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{game_id}", response_model=GameResponse)
def get_game_endpoint(
    game_id: str,
    use_case: GetGameUseCase = Depends(inject_get_game_use_case),
):
    """
    Get a game by ID
    Delegates to GetGameUseCase
    """
    query = GetGameQuery(game_id=game_id)
    game = use_case.execute(query)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameMapper.to_response(game)


@router.get("/{game_id}/hint")
def get_hint_endpoint(
    game_id: str,
    use_case: GetGameUseCase = Depends(inject_get_game_use_case),
    ml_service = Depends(get_ml_service),
):
    """
    Get a hint for the next move
    Calls ML service to suggest the best move using ML models
    """
    query = GetGameQuery(game_id=game_id)
    game = use_case.execute(query)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Game is already finished")

    try:
        # Convert game board to ML service format
        board_2d = []
        for row_idx in range(3):
            row = []
            for col_idx in range(3):
                pos = Position(row=row_idx, col=col_idx)
                cell = game.board.get_cell(pos)
                if cell == Mark.X:
                    row.append("X")
                elif cell == Mark.O:
                    row.append("O")
                else:
                    row.append(None)
            board_2d.append(row)

        current_player_str = "X" if game.next_player == Mark.X else "O"

        # Call ML service hint endpoint
        hint_result = ml_service.get_hint(board_2d, current_player_str)

        return hint_result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hint: {str(e)}")


@router.post("/{game_id}/moves", response_model=GameResponse)
def play_move_endpoint(
    game_id: str,
    payload: MoveCreate,
    background_tasks: BackgroundTasks,
    use_case: PlayMoveUseCase = Depends(inject_play_move_use_case),
    get_game_use_case: GetGameUseCase = Depends(inject_get_game_use_case),
):
    """
    Play a move in the game
    Delegates to PlayMoveUseCase
    Handles AI moves in background
    """
    try:
        # First, get the game to determine whose turn it is
        query = GetGameQuery(game_id=game_id)
        game = get_game_use_case.execute(query)

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Determine player ID based on whose turn it is
        player_id = game.get_current_player().id.value

        # Build command from request
        command = PlayMoveCommand(
            game_id=game_id,
            player_id=player_id,
            row=payload.row,
            col=payload.col,
            ai_difficulty=payload.ai_difficulty,
        )

        # Execute the move
        game = use_case.execute(command)

        # If it's AI's turn and game still in progress, schedule AI move
        if game.is_ai_turn() and game.status == GameStatus.IN_PROGRESS:
            ai_difficulty = payload.ai_difficulty or (
                game.ai_difficulty.value if game.ai_difficulty else "medium"
            )
            background_tasks.add_task(
                run_ai_move_background,
                game_id=game.id,
                ai_difficulty=ai_difficulty,
            )

        return GameMapper.to_response(game)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Background Tasks


def run_ai_move_background(
    game_id: str,
    ai_difficulty: str,
):
    """
    Run AI move in background
    Creates a new database session to avoid session conflicts
    """
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        # Create fresh dependencies with new session
        repository = get_game_repository(db)
        ai_service = get_ai_service()
        platform_service = get_platform_service()
        state_serializer = get_game_state_serializer()

        command = PlayMoveCommand(
            game_id=game_id,
            player_id=PlayerFactory.create_ai_player_id(),
            row=None,
            col=None,
            ai_difficulty=ai_difficulty,
        )

        use_case = PlayMoveUseCase(
            game_repository=repository,
            ai_service=ai_service,
            platform_service=platform_service,
            state_serializer=state_serializer,
        )

        use_case.execute(command)
    except Exception as e:
        # Log error but don't raise (background task)
        import logging

        logging.error(f"AI move failed: {e}")
    finally:
        db.close()
