# tests/test_ai_service.py
from unittest.mock import patch, Mock
from app.infrastructure.services.ai_service import HttpAIService
from app.domain.value_objects import Board, Mark, AIDifficulty, Position


@patch("app.infrastructure.services.ai_service.requests.post")
def test_calculate_move(mock_post):
    mock_post.return_value = Mock(
        json=lambda: {"move": {"row": 1, "col": 1}, "evaluation": 0.75, "metadata": {}}
    )
    ai = HttpAIService(base_url="http://mocked-ai")
    board = Board.empty()
    pos, eval, meta = ai.calculate_move(board, Mark.O, AIDifficulty.MEDIUM)

    assert pos == Position(1, 1)
    assert eval == 0.75
    mock_post.assert_called_once()
