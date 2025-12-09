# tests/test_use_cases.py
import pytest
from unittest.mock import Mock
from datetime import datetime
from app.application.use_cases import CreateGameUseCase, PlayMoveUseCase
from app.application.dtos import CreateGameCommand, PlayMoveCommand
from app.domain.entities import Game
from app.domain.value_objects import GameMode, AIDifficulty, Mark, Position, PlayerId
from app.domain.interfaces import (
    IGameRepository,
    IAIService,
    IPlatformService,
    IGameStateSerializer,
)


@pytest.fixture
def mock_repo():
    repo = Mock(spec=IGameRepository)
    repo.save = lambda game: game
    return repo


@pytest.fixture
def mock_ai():
    return Mock(spec=IAIService)


@pytest.fixture
def mock_platform():
    return Mock(spec=IPlatformService)


@pytest.fixture
def mock_serializer():
    mock = Mock(spec=IGameStateSerializer)
    mock.serialize_game_state.return_value = {
        "game_id": "test",
        "board": [[".", ".", "."], [".", ".", "."], [".", ".", "."]],
        "move_count": 0,
        "last_updated": datetime.utcnow().isoformat(),
    }
    return mock


# --- CreateGameUseCase Tests ---
def test_create_game_pvai(mock_repo):
    use_case = CreateGameUseCase(mock_repo)
    cmd = CreateGameCommand(player_x_id="px", mode="pvai", ai_difficulty="hard")

    game = use_case.execute(cmd)

    assert game.player_x.id.value == "px"
    assert game.player_o.id.value == "AI"
    assert game.mode == GameMode.PVAI
    assert game.ai_difficulty == AIDifficulty.HARD
    assert game.status.name == "IN_PROGRESS"
    assert game.next_player == Mark.X
    assert game.board.to_string() == "         "


def test_create_game_pvp(mock_repo):
    use_case = CreateGameUseCase(mock_repo)
    cmd = CreateGameCommand(
        player_x_id="px",
        player_o_id="po",
        player_x_name="Alice",
        player_o_name="Bob",
        mode="pvp",
    )

    game = use_case.execute(cmd)

    assert game.player_x.name == "Alice"
    assert game.player_o.name == "Bob"
    assert game.mode == GameMode.PVP
    assert game.ai_difficulty is None


def test_create_game_pvp_missing_player_o(mock_repo):
    use_case = CreateGameUseCase(mock_repo)
    cmd = CreateGameCommand(player_x_id="px", mode="pvp")
    with pytest.raises(ValueError, match="Player O ID is required for PvP mode"):
        use_case.execute(cmd)


# --- PlayMoveUseCase Tests ---
def test_play_human_move_pvp(mock_repo, mock_ai, mock_platform, mock_serializer):
    # Arrange: fresh game
    existing_game = Game.create_new(
        player_x_id="px",
        player_x_name="X",
        player_o_id="po",
        player_o_name="O",
        mode=GameMode.PVP,
    )
    mock_repo.find_by_id.return_value = existing_game

    use_case = PlayMoveUseCase(mock_repo, mock_ai, mock_platform, mock_serializer)
    cmd = PlayMoveCommand(game_id="g1", player_id="px", row=0, col=0)

    # Act
    result_game = use_case.execute(cmd)

    # Assert
    assert result_game.move_count == 1
    assert result_game.next_player == Mark.O
    assert result_game.board.get_cell(Position(0, 0)) == Mark.X

    mock_platform.log_move.assert_called_once()


def test_play_ai_move_pvai(mock_repo, mock_ai, mock_platform, mock_serializer):
    # Arrange
    game = Game.create_new(
        player_x_id="human",
        player_x_name="Human",
        player_o_id="AI",
        player_o_name="AI",
        mode=GameMode.PVAI,
        ai_difficulty=AIDifficulty.MEDIUM,
    )
    # Human plays first → AI's turn
    game.play_move(Position(0, 0), PlayerId("human"))
    mock_repo.find_by_id.return_value = game

    mock_ai.calculate_move.return_value = (Position(1, 1), 0.8, {})

    use_case = PlayMoveUseCase(mock_repo, mock_ai, mock_platform, mock_serializer)
    cmd = PlayMoveCommand(game_id="g1", player_id="AI", row=None, col=None)

    # Act
    result_game = use_case.execute(cmd)

    # Assert
    assert result_game.move_count == 2
    assert result_game.board.get_cell(Position(1, 1)) == Mark.O
    assert result_game.next_player == Mark.X

    mock_ai.calculate_move.assert_called_once()


def test_play_human_missing_coords(mock_repo, mock_ai, mock_platform, mock_serializer):
    game = Game.create_new("px", "X", "po", "O", GameMode.PVP)
    mock_repo.find_by_id.return_value = game

    use_case = PlayMoveUseCase(mock_repo, mock_ai, mock_platform, mock_serializer)
    cmd = PlayMoveCommand(game_id="g1", player_id="px", row=0, col=None)

    with pytest.raises(ValueError, match="Row and col are required for human moves"):
        use_case.execute(cmd)


def test_play_move_game_not_found(mock_repo, mock_ai, mock_platform, mock_serializer):
    mock_repo.find_by_id.return_value = None
    use_case = PlayMoveUseCase(mock_repo, mock_ai, mock_platform, mock_serializer)
    cmd = PlayMoveCommand(game_id="missing", player_id="px", row=0, col=0)

    with pytest.raises(ValueError, match="Game not found"):
        use_case.execute(cmd)
