from app.domain.models import GameState, Mark, GameStatus
from app.domain.logic import apply_move, legal_moves


def test_first_move_reduces_legal_moves():
    state = GameState.new()
    assert len(legal_moves(state)) == 9
    state2 = apply_move(state, (0, 0))
    assert len(legal_moves(state2)) == 8


def test_row_win_detection():
    state = GameState.new()
    s1 = apply_move(state, (0, 0))  # X
    s2 = apply_move(s1, (1, 0))     # O
    s3 = apply_move(s2, (0, 1))     # X
    s4 = apply_move(s3, (1, 1))     # O
    s5 = apply_move(s4, (0, 2))     # X wins

    assert s5.status == GameStatus.X_WON
    assert s5.winner == Mark.X
