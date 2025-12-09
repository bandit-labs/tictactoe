# tests/test_platform_client.py
import pytest
from unittest.mock import patch, Mock
from app.services import platform_client
import logging

# Capture logs for testing
@pytest.fixture
def caplog(caplog):
    return caplog

def test_log_move_to_platform_success(caplog):
    """Test successful logging of a move to the platform."""
    caplog.set_level(logging.INFO)
    previous_state = {
        "game_id": "game123",
        "board": [[".", ".", "."], [".", "X", "."], [".", ".", "."]],
        "move_count": 1,
        "last_updated": "2023-05-17T10:00:05" # Add required key
    }
    new_state = {
        "game_id": "game123",
        "board": [["O", ".", "."], [".", "X", "."], [".", ".", "."]],
        "move_count": 2,
        "last_updated": "2023-05-17T10:00:10" # Add required key
    }
    move_index = 0
    player_id = "player456"
    heuristic_value = 0.5

    with patch('app.services.platform_client.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        platform_client.log_move_to_platform(previous_state, new_state, move_index, player_id, heuristic_value)

        mock_post.assert_called_once_with(
            f"{platform_client.settings.platform_backend_url}/game-sessions/moves",
            json={
                "game_id": "game123",
                "player_id": "player456",
                "move_index": 0,
                "move_number": 2,
                "previous_state": previous_state,
                "next_state": new_state,
                "timestamp": new_state["last_updated"], # This key now exists
                "heuristic_value": 0.5,
            },
            timeout=5,
        )
        # Check for successful log message
        assert any("Logged move to platform backend" in record.message and "game123" in record.message for record in caplog.records)

def test_log_move_to_platform_failure(caplog):
    """Test logging a move to the platform when the request fails."""
    caplog.set_level(logging.ERROR)
    previous_state = {
        "game_id": "game123",
        "board": [[".", ".", "."], [".", "X", "."], [".", ".", "."]],
        "move_count": 1,
        "last_updated": "2023-05-17T10:00:05" # Add required key
    }
    new_state = {
        "game_id": "game123",
        "board": [["O", ".", "."], [".", "X", "."], [".", ".", "."]],
        "move_count": 2,
        "last_updated": "2023-05-17T10:00:10" # Add required key
    }
    move_index = 0
    player_id = "player456"
    heuristic_value = 0.5

    with patch('app.services.platform_client.requests.post') as mock_post:
        mock_post.side_effect = Exception("Network Error")

        platform_client.log_move_to_platform(previous_state, new_state, move_index, player_id, heuristic_value)

        # Check for error log message
        assert any("Failed to log move to platform" in record.message and "Network Error" in record.message for record in caplog.records)

def test_send_final_result_to_platform_success(caplog):
    """Test successful sending of final result to the platform."""
    caplog.set_level(logging.INFO)
    final_state = {
        "game_id": "game123",
        "winner": "X",
        "move_count": 5,
        "last_updated": "2023-05-17T10:00:15" # Add required key for completeness, though not directly used in payload
    }
    history = [
        {"player": "X", "move": 0, "move_number": 1},
        {"player": "O", "move": 1, "move_number": 2},
        {"player": "X", "move": 2, "move_number": 3},
        {"player": "O", "move": 3, "move_number": 4},
        {"player": "X", "move": 4, "move_number": 5},
    ]

    with patch('app.services.platform_client.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        platform_client.send_final_result_to_platform(final_state, history)

        mock_post.assert_called_once_with(
            f"{platform_client.settings.platform_backend_url}/game-sessions/results",
            json={
                "game_id": "game123",
                "winner": "X",
                "history": history,
                "final_state": final_state,
            },
            timeout=5,
        )
        # Check for successful log message
        assert any("Sent final result to platform backend" in record.message and "game123" in record.message for record in caplog.records)

def test_send_final_result_to_platform_failure(caplog):
    """Test sending final result to the platform when the request fails."""
    caplog.set_level(logging.ERROR)
    final_state = {
        "game_id": "game123",
        "winner": "X",
        "move_count": 5,
        "last_updated": "2023-05-17T10:00:15" # Add required key for completeness, though not directly used in payload
    }
    history = [
        {"player": "X", "move": 0, "move_number": 1},
        {"player": "O", "move": 1, "move_number": 2},
    ]

    with patch('app.services.platform_client.requests.post') as mock_post:
        mock_post.side_effect = Exception("Server Error")

        platform_client.send_final_result_to_platform(final_state, history)

        # Check for error log message
        assert any("Failed to send final result to platform" in record.message and "Server Error" in record.message for record in caplog.records)