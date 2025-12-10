# tests/test_game_rules.py
from app.domain.services import GameRules
from app.domain.value_objects import Board, Position, Mark, GameStatus


def test_calculate_winner_row():
    board = Board.from_string("XXXOO    ")
    assert GameRules.calculate_winner(board) == Mark.X


def test_calculate_winner_col():
    # Let's use a clear board: X.OXO.X.O
    board = Board.from_string("X OXO X O")  # "X.O/XO./X.O" → X wins col 0
    assert GameRules.calculate_winner(board) == Mark.X


def test_calculate_winner_diagonal():
    board = Board.from_string("X  OX O X")  # X . . / . X . / . . X
    assert GameRules.calculate_winner(board) == Mark.X


def test_calculate_status_draw():
    board = Board.from_string("XOXXXOOXO")
    status = GameRules.calculate_status(board, move_count=9)
    assert status == GameStatus.DRAW


def test_calculate_status_in_progress():
    board = Board.from_string("X        ")
    status = GameRules.calculate_status(board, move_count=1)
    assert status == GameStatus.IN_PROGRESS


def test_is_valid_move():
    board = Board.empty()
    assert GameRules.is_valid_move(board, Position(0, 0))
    board = board.with_mark(Position(0, 0), Mark.X)
    assert not GameRules.is_valid_move(board, Position(0, 0))


def test_get_legal_moves():
    board = Board.from_string("X        ")
    moves = GameRules.get_legal_moves(board)
    assert len(moves) == 8
    assert Position(0, 0) not in moves


def test_calculate_heuristic():
    assert GameRules.calculate_heuristic(GameStatus.X_WON, Mark.X) == 1.0
    assert GameRules.calculate_heuristic(GameStatus.X_WON, Mark.O) == -1.0
    assert GameRules.calculate_heuristic(GameStatus.DRAW, Mark.X) == 0.0
    assert GameRules.calculate_heuristic(GameStatus.IN_PROGRESS, Mark.X) == 0.0
