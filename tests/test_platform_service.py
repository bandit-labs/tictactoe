# tests/test_platform_service.py
import pytest
from unittest.mock import patch
from requests import RequestException
from app.infrastructure.services.platform_service import HttpPlatformService
from app.domain.entities import Game, Move
from app.domain.value_objects import Mark, Position, PlayerId, GameMode


@pytest.fixture
def sample_game():
    return Game.create_new("px", "X", "po", "O", GameMode.PVP)


@pytest.fixture
def sample_move():
    return Move(
        position=Position(0, 0),
        mark=Mark.X,
        player_id=PlayerId("px"),
        move_number=1,
        heuristic_value=0.0,
    )


@patch("app.infrastructure.services.platform_service.requests.post")
def test_log_move_success(mock_post, sample_game, sample_move):
    service = HttpPlatformService(base_url="http://platform")
    state = {"game_id": "g1", "last_updated": "2025-01-01T00:00:00"}

    service.log_move(sample_game, sample_move, state, state)

    mock_post.assert_called_once()
    assert "game-sessions/moves" in mock_post.call_args[0][0]


@patch("app.infrastructure.services.platform_service.requests.post")
def test_log_move_failure_logs_error(mock_post, sample_game, sample_move, caplog):
    import logging

    caplog.set_level(logging.ERROR)

    mock_post.side_effect = RequestException("Network down")

    service = HttpPlatformService(base_url="http://platform")
    state = {"game_id": "g1"}

    # This should NOT raise
    service.log_move(sample_game, sample_move, state, state)

    # Now assert error was logged
    assert any(
        "Failed to log move to platform" in record.message
        and "Network down" in record.message
        for record in caplog.records
    )
