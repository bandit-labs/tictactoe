# tests/test_logic.py
import pytest
from app.domain.models import GameState, Mark, GameStatus, Position
from app.domain.logic import (
    legal_moves,
    apply_move,
    _compute_winner,
    board_to_string,
    board_from_string,
    heuristic_value,
)


# --- GameState.new() Test ---
def test_new_game_state():
    """Test creating a new game state."""
    state = GameState.new()
    assert state.board == [
        [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
    ]
    assert state.next_player == Mark.X
    assert state.status == GameStatus.IN_PROGRESS
    assert state.winner is None
    assert state.move_count == 0

    # Test starting player
    state_o = GameState.new(starting_player=Mark.O)
    assert state_o.next_player == Mark.O


# --- legal_moves() Tests ---
def test_legal_moves_initial():
    """Test legal moves for an empty board."""
    initial_state = GameState.new()
    expected_moves = [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ]
    assert set(legal_moves(initial_state)) == set(expected_moves)


def test_legal_moves_some_moves():
    """Test legal moves after a few moves."""
    state = GameState.new()
    # Apply moves X at (0,0), O at (1,1)
    state = apply_move(state, (0, 0))  # X
    state = apply_move(state, (1, 1))  # O
    expected_moves = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    assert set(legal_moves(state)) == set(expected_moves)


def test_legal_moves_game_over():
    """Test legal moves returns empty list when game is over."""
    # Create a winning state for X
    state = GameState(
        board=[
            [Mark.X, Mark.O, Mark.O],
            [Mark.O, Mark.X, Mark.EMPTY],
            [Mark.EMPTY, Mark.EMPTY, Mark.X],
        ],
        next_player=Mark.O,
        status=GameStatus.X_WON,
        winner=Mark.X,
        move_count=5,
    )
    assert legal_moves(state) == []


def test_legal_moves_full_draw():
    """Test legal moves returns empty list on a full draw board."""
    state = GameState(
        board=[
            [Mark.X, Mark.O, Mark.X],
            [Mark.O, Mark.X, Mark.O],
            [Mark.O, Mark.X, Mark.O],
        ],
        next_player=Mark.O,
        status=GameStatus.DRAW,
        winner=None,
        move_count=9,
    )
    assert legal_moves(state) == []


# --- apply_move() Tests ---
def test_apply_move_success():
    """Test applying a valid move."""
    initial_state = GameState.new()
    new_state = apply_move(initial_state, (1, 1))
    expected_board = [
        [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        [Mark.EMPTY, Mark.X, Mark.EMPTY],
        [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
    ]
    assert new_state.board == expected_board
    assert new_state.next_player == Mark.O
    assert new_state.status == GameStatus.IN_PROGRESS
    assert new_state.move_count == 1


def test_apply_move_occupied_cell():
    """Test applying a move to an occupied cell raises ValueError."""
    state = GameState.new()
    state = apply_move(state, (0, 0))  # X plays
    with pytest.raises(ValueError, match="Cell already occupied"):
        apply_move(state, (0, 0))  # X tries to play again


def test_apply_move_out_of_bounds():
    """Test applying a move out of bounds raises ValueError."""
    state = GameState.new()
    with pytest.raises(ValueError, match="Position out of bounds"):
        apply_move(state, (3, 0))
    with pytest.raises(ValueError, match="Position out of bounds"):
        apply_move(state, (0, 3))
    with pytest.raises(ValueError, match="Position out of bounds"):
        apply_move(state, (-1, 0))


def test_apply_move_game_finished():
    """Test applying a move to a finished game raises ValueError."""
    finished_state = GameState(
        board=[
            [Mark.X, Mark.O, Mark.X],
            [Mark.O, Mark.X, Mark.O],
            [Mark.O, Mark.X, Mark.O],
        ],
        next_player=Mark.O,
        status=GameStatus.DRAW,
        winner=None,
        move_count=9,
    )
    with pytest.raises(ValueError, match="Game is already finished"):
        apply_move(finished_state, (0, 0))


def test_apply_move_win_row():
    """Test applying a move that wins the game via a row."""
    state = GameState(
        board=[
            [Mark.X, Mark.X, Mark.EMPTY],
            [Mark.O, Mark.O, Mark.EMPTY],
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        ],
        next_player=Mark.X,
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=4,
    )
    new_state = apply_move(state, (0, 2))
    assert new_state.status == GameStatus.X_WON
    assert new_state.winner == Mark.X
    assert new_state.next_player == Mark.X  # Next player doesn't change after win


def test_apply_move_win_col():
    """Test applying a move that wins the game via a column."""
    # Board setup where O can win column 1 by playing (2,1)
    # X O .
    # O O . <- O plays here to win column 1
    # . . .
    state = GameState(
        board=[
            [Mark.X, Mark.O, Mark.EMPTY],
            [Mark.O, Mark.O, Mark.EMPTY],  # O has (1,1)
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        ],  # O needs (2,1) to win column 1
        next_player=Mark.O,  # O's turn
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=4,
    )
    new_state = apply_move(state, (2, 1))  # O plays (2,1) to win column 1
    assert new_state.status == GameStatus.O_WON
    assert new_state.winner == Mark.O


def test_apply_move_win_diag():
    """Test applying a move that wins the game via the main diagonal."""
    # Board setup where X can win the main diagonal by playing (2,2)
    # X . .
    # . X . <- X needs (2,2) to win (0,0)-(1,1)-(2,2)
    # . . .
    state = GameState(
        board=[
            [Mark.X, Mark.EMPTY, Mark.EMPTY],
            [Mark.EMPTY, Mark.X, Mark.EMPTY],  # X has (1,1)
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        ],  # X needs (2,2) to win main diagonal
        next_player=Mark.X,  # X's turn
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=2,
    )
    new_state = apply_move(state, (2, 2))  # X plays (2,2) to win main diagonal
    assert new_state.status == GameStatus.X_WON
    assert new_state.winner == Mark.X


def test_apply_move_draw():
    """Test applying the final move that results in a draw."""
    state = GameState(
        board=[
            [Mark.X, Mark.O, Mark.X],
            [Mark.O, Mark.X, Mark.O],
            [Mark.O, Mark.X, Mark.EMPTY],
        ],  # 8 moves played
        next_player=Mark.O,
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=8,
    )
    new_state = apply_move(state, (2, 2))
    assert new_state.status == GameStatus.DRAW
    assert new_state.winner is None
    assert new_state.move_count == 9


# --- _compute_winner() Tests ---
def test_compute_winner_no_winner():
    """Test _compute_winner returns None for no winner."""
    board = [
        [Mark.X, Mark.O, Mark.X],
        [Mark.O, Mark.EMPTY, Mark.O],
        [Mark.O, Mark.X, Mark.EMPTY],
    ]
    assert _compute_winner(board) is None


def test_compute_winner_row():
    """Test _compute_winner detects a row win."""
    board_x_win = [
        [Mark.X, Mark.X, Mark.X],
        [Mark.O, Mark.EMPTY, Mark.O],
        [Mark.O, Mark.EMPTY, Mark.EMPTY],
    ]
    assert _compute_winner(board_x_win) == Mark.X

    board_o_win = [
        [Mark.O, Mark.EMPTY, Mark.EMPTY],
        [Mark.X, Mark.X, Mark.EMPTY],
        [Mark.O, Mark.O, Mark.O],
    ]
    assert _compute_winner(board_o_win) == Mark.O


def test_compute_winner_col():
    """Test _compute_winner detects a column win."""
    board_x_win = [
        [Mark.X, Mark.O, Mark.EMPTY],
        [Mark.X, Mark.EMPTY, Mark.O],
        [Mark.X, Mark.EMPTY, Mark.EMPTY],
    ]
    assert _compute_winner(board_x_win) == Mark.X

    board_o_win = [
        [Mark.X, Mark.O, Mark.X],
        [Mark.X, Mark.O, Mark.EMPTY],
        [Mark.EMPTY, Mark.O, Mark.EMPTY],
    ]
    assert _compute_winner(board_o_win) == Mark.O


def test_compute_winner_diag():
    """Test _compute_winner detects a diagonal win."""
    board_x_win = [
        [Mark.X, Mark.O, Mark.EMPTY],
        [Mark.EMPTY, Mark.X, Mark.O],
        [Mark.EMPTY, Mark.EMPTY, Mark.X],
    ]
    assert _compute_winner(board_x_win) == Mark.X

    board_o_win = [
        [Mark.EMPTY, Mark.EMPTY, Mark.O],
        [Mark.EMPTY, Mark.O, Mark.X],
        [Mark.O, Mark.X, Mark.EMPTY],
    ]
    assert _compute_winner(board_o_win) == Mark.O


# --- board_to_string / board_from_string Tests ---
def test_board_to_string():
    """Test converting board to string."""
    board = [
        [Mark.X, Mark.EMPTY, Mark.O],
        [Mark.O, Mark.X, Mark.EMPTY],
        [Mark.EMPTY, Mark.O, Mark.X],
    ]
    expected_str = "X OOX  OX"  # This is 9 characters: X,_,O,O,X,_,_,O,X
    assert board_to_string(board) == expected_str


def test_board_from_string():
    """Test converting string to board."""
    s = "X OOX  OX"  # This is 9 characters
    expected_board = [
        [Mark.X, Mark.EMPTY, Mark.O],
        [Mark.O, Mark.X, Mark.EMPTY],
        [Mark.EMPTY, Mark.O, Mark.X],
    ]
    assert board_from_string(s) == expected_board


def test_board_to_string_from_string_roundtrip():
    """Test converting board to string and back is idempotent."""
    original_board = [
        [Mark.X, Mark.EMPTY, Mark.O],
        [Mark.O, Mark.X, Mark.EMPTY],
        [Mark.EMPTY, Mark.O, Mark.X],
    ]
    string_repr = board_to_string(original_board)
    roundtrip_board = board_from_string(string_repr)
    assert roundtrip_board == original_board


def test_board_from_string_invalid_length():
    """Test board_from_string raises ValueError for incorrect length."""
    with pytest.raises(ValueError, match="Board string must be length 9"):
        board_from_string("short")
    with pytest.raises(ValueError, match="Board string must be length 9"):
        board_from_string("this_string_is_too_long")


# --- heuristic_value() Tests ---
def test_heuristic_value_x_won_for_x():
    """Test heuristic value when X won, evaluated for X."""
    state = GameState(
        board=[
            [Mark.X, Mark.X, Mark.X],
            [Mark.O, Mark.EMPTY, Mark.O],
            [Mark.O, Mark.EMPTY, Mark.EMPTY],
        ],
        next_player=Mark.O,  # Doesn't matter for finished game
        status=GameStatus.X_WON,
        winner=Mark.X,
        move_count=5,
    )
    assert heuristic_value(state, for_player=Mark.X) == 1.0


def test_heuristic_value_x_won_for_o():
    """Test heuristic value when X won, evaluated for O."""
    state = GameState(
        board=[
            [Mark.X, Mark.X, Mark.X],
            [Mark.O, Mark.EMPTY, Mark.O],
            [Mark.O, Mark.EMPTY, Mark.EMPTY],
        ],
        next_player=Mark.O,
        status=GameStatus.X_WON,
        winner=Mark.X,
        move_count=5,
    )
    assert heuristic_value(state, for_player=Mark.O) == -1.0


def test_heuristic_value_o_won_for_o():
    """Test heuristic value when O won, evaluated for O."""
    state = GameState(
        board=[
            [Mark.O, Mark.EMPTY, Mark.EMPTY],
            [Mark.X, Mark.X, Mark.EMPTY],
            [Mark.O, Mark.X, Mark.O],
        ],
        next_player=Mark.X,
        status=GameStatus.O_WON,
        winner=Mark.O,
        move_count=7,
    )
    assert heuristic_value(state, for_player=Mark.O) == 1.0


def test_heuristic_value_o_won_for_x():
    """Test heuristic value when O won, evaluated for X."""
    state = GameState(
        board=[
            [Mark.O, Mark.EMPTY, Mark.EMPTY],
            [Mark.X, Mark.X, Mark.EMPTY],
            [Mark.O, Mark.X, Mark.O],
        ],
        next_player=Mark.X,
        status=GameStatus.O_WON,
        winner=Mark.O,
        move_count=7,
    )
    assert heuristic_value(state, for_player=Mark.X) == -1.0


def test_heuristic_value_draw():
    """Test heuristic value for a draw."""
    state = GameState(
        board=[
            [Mark.X, Mark.O, Mark.X],
            [Mark.O, Mark.X, Mark.O],
            [Mark.O, Mark.X, Mark.O],
        ],
        next_player=Mark.O,
        status=GameStatus.DRAW,
        winner=None,
        move_count=9,
    )
    assert heuristic_value(state, for_player=Mark.X) == 0.0
    assert heuristic_value(state, for_player=Mark.O) == 0.0


def test_heuristic_value_in_progress():
    """Test heuristic value for an in-progress game."""
    state = GameState(
        board=[
            [Mark.X, Mark.EMPTY, Mark.EMPTY],
            [Mark.EMPTY, Mark.O, Mark.EMPTY],
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        ],
        next_player=Mark.X,
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=2,
    )
    # The current implementation returns 0.0 for in-progress games
    assert heuristic_value(state, for_player=Mark.X) == 0.0
    assert heuristic_value(state, for_player=Mark.O) == 0.0
