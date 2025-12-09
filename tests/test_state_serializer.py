# tests/test_state_serializer.py
import pytest
from datetime import datetime
from app.domain.models import GameState, Mark, GameStatus
from app.infra.orm_models import Game, MoveLog
from app.services import state_serializer


def test_build_rich_state_basic():
    """Test building a rich state dictionary for an in-progress game."""
    game = Game(
        id="game_123",
        player_x_id="px",
        player_o_id="po",
        player_x_name="X",
        player_o_name="O",
        mode="pvp",
        board_state="X OOX  OX",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.O,
        move_count=6,
        created_at=datetime(2023, 5, 17, 10, 0, 0),
        finished_at=None,
    )
    state = GameState(
        board=[
            [Mark.X, Mark.EMPTY, Mark.O],
            [Mark.O, Mark.X, Mark.EMPTY],
            [Mark.EMPTY, Mark.O, Mark.X],
        ],
        next_player=Mark.O,
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=6,
    )
    moves = [
        MoveLog(
            id=1,
            game_id="game_123",
            move_number=1,
            player_id="px",
            mark=Mark.X,
            row=0,
            col=0,
            state_before={},
            state_after={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 10, 0, 5),
        ),
        MoveLog(
            id=2,
            game_id="game_123",
            move_number=2,
            player_id="po",
            mark=Mark.O,
            row=0,
            col=1,
            state_after={},
            state_before={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 10, 0, 10),
        ),
        MoveLog(
            id=3,
            game_id="game_123",
            move_number=3,
            player_id="px",
            mark=Mark.X,
            row=1,
            col=1,
            state_after={},
            state_before={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 10, 0, 15),
        ),
        MoveLog(
            id=4,
            game_id="game_123",
            move_number=4,
            player_id="po",
            mark=Mark.O,
            row=1,
            col=0,
            state_after={},
            state_before={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 10, 0, 20),
        ),
        MoveLog(
            id=5,
            game_id="game_123",
            move_number=5,
            player_id="px",
            mark=Mark.X,
            row=2,
            col=2,
            state_after={},
            state_before={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 10, 0, 25),
        ),
        MoveLog(
            id=6,
            game_id="game_123",
            move_number=6,
            player_id="po",
            mark=Mark.O,
            row=2,
            col=1,
            state_after={},
            state_before={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 10, 0, 30),
        ),
    ]

    result = state_serializer.build_rich_state(game, state, moves)

    expected_board = [["X", ".", "O"], ["O", "X", "."], [".", "O", "X"]]
    # Board: X . O (pos 0,1,2)
    #        O X . (pos 3,4,5)
    #        . O X (pos 6,7,8)
    # Empty positions: (0,1), (1,2), (2,0) -> indices 1, 5, 6
    expected_legal_moves = [
        1,
        5,
        6,
    ]  # Positions (0,1), (1,2), (2,0) are empty -> indices 1, 5, 6
    expected_history = [
        {"player": "X", "move": 0},  # (0,0)
        {"player": "O", "move": 1},  # (0,1)
        {"player": "X", "move": 4},  # (1,1)
        {"player": "O", "move": 3},  # (1,0)
        {"player": "X", "move": 8},  # (2,2)
        {"player": "O", "move": 7},  # (2,1)
    ]
    expected_last_updated = datetime(2023, 5, 17, 10, 0, 30).isoformat()

    assert result["game_id"] == "game_123"
    assert result["board"] == expected_board
    assert result["current_player"] == "O"
    assert result["legal_moves"] == expected_legal_moves
    assert result["move_count"] == 6
    assert result["game_status"] == "IN_PROGRESS"
    assert result["winner"] is None
    assert result["config"] == {"rows": 3, "cols": 3}
    assert result["history"] == expected_history
    assert result["last_updated"] == expected_last_updated


def test_build_rich_state_finished_win():
    """Test building a rich state dictionary for a finished game (X won).
    Legal moves are calculated based on empty board cells, regardless of status."""
    game = Game(
        id="game_456",
        player_x_id="px",
        player_o_id="po",
        player_x_name="X",
        player_o_name="O",
        mode="pvp",
        board_state="XXXOO O O",
        status=GameStatus.X_WON,
        next_player=Mark.X,
        move_count=5,
        created_at=datetime(2023, 5, 17, 11, 0, 0),
        finished_at=datetime(2023, 5, 17, 11, 0, 35),
    )
    # The domain state object reflects the board state after the winning move,
    # even though the game status is finished.
    # Board: X X X (win)
    #        O _ O -> (1,1) is empty -> index 4
    #        _ O _ -> (2,0), (2,2) are empty -> indices 6, 8
    state = GameState(
        board=[
            [Mark.X, Mark.X, Mark.X],
            [Mark.O, Mark.EMPTY, Mark.O],
            [Mark.EMPTY, Mark.O, Mark.EMPTY],
        ],
        next_player=Mark.X,
        status=GameStatus.X_WON,
        winner=Mark.X,
        move_count=5,
    )
    moves = [
        MoveLog(
            id=1,
            game_id="game_456",
            move_number=1,
            player_id="px",
            mark=Mark.X,
            row=0,
            col=0,
            state_before={},
            state_after={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 11, 0, 5),
        ),
        MoveLog(
            id=2,
            game_id="game_456",
            move_number=2,
            player_id="po",
            mark=Mark.O,
            row=1,
            col=0,
            state_before={},
            state_after={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 11, 0, 10),
        ),
        MoveLog(
            id=3,
            game_id="game_456",
            move_number=3,
            player_id="px",
            mark=Mark.X,
            row=0,
            col=1,
            state_before={},
            state_after={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 11, 0, 15),
        ),
        MoveLog(
            id=4,
            game_id="game_456",
            move_number=4,
            player_id="po",
            mark=Mark.O,
            row=2,
            col=0,
            state_before={},
            state_after={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 11, 0, 20),
        ),
        MoveLog(
            id=5,
            game_id="game_456",
            move_number=5,
            player_id="px",
            mark=Mark.X,
            row=0,
            col=2,
            state_before={},
            state_after={},
            heuristic_value=1.0,
            created_at=datetime(2023, 5, 17, 11, 0, 25),
        ),  # Winning move
    ]

    result = state_serializer.build_rich_state(game, state, moves)

    assert result["game_status"] == "WIN"
    assert result["winner"] == "X"
    # Legal moves are calculated based on the board state, not the game status.
    # Empty positions: (1,1), (2,0), (2,2) -> indices 4, 6, 8
    assert result["legal_moves"] == [4, 6, 8]
    # last_updated should come from the latest move log
    expected_last_updated = datetime(2023, 5, 17, 11, 0, 25).isoformat()
    assert result["last_updated"] == expected_last_updated


def test_build_rich_state_finished_draw():
    """Test building a rich state dictionary for a finished game (draw).
    Legal moves are calculated based on empty board cells, regardless of status."""
    game = Game(
        id="game_789",
        player_x_id="px",
        player_o_id="po",
        player_x_name="X",
        player_o_name="O",
        mode="pvp",
        board_state="XOXOXO.OX",
        status=GameStatus.DRAW,
        next_player=Mark.O,
        move_count=9,
        created_at=datetime(2023, 5, 17, 12, 0, 0),
        finished_at=datetime(2023, 5, 17, 12, 0, 40),
    )
    # The domain state object reflects the final board state after the draw move,
    # even though the game status is finished.
    # Let's use the board string "XOXOXOXOX" for a full draw in the ORM object.
    # Board: X O X
    #        O X O
    #        X O X (All cells filled)
    full_draw_board = [
        [Mark.X, Mark.O, Mark.X],
        [Mark.O, Mark.X, Mark.O],
        [Mark.X, Mark.O, Mark.X],
    ]
    state = GameState(
        board=full_draw_board,
        next_player=Mark.O,
        status=GameStatus.DRAW,
        winner=None,
        move_count=9,
    )
    game_corrected = Game(
        id="game_789",
        player_x_id="px",
        player_o_id="po",
        player_x_name="X",
        player_o_name="O",
        mode="pvp",
        board_state="XOXOXOXOX",
        status=GameStatus.DRAW,
        next_player=Mark.O,
        move_count=9,
        created_at=datetime(2023, 5, 17, 12, 0, 0),
        finished_at=datetime(2023, 5, 17, 12, 0, 40),
    )
    moves = [
        # ... (Assume 9 moves leading to the full board represented in state)
        MoveLog(
            id=9,
            game_id="game_789",
            move_number=9,
            player_id="po",
            mark=Mark.O,
            row=2,
            col=0,
            state_before={},
            state_after={},
            heuristic_value=0.0,
            created_at=datetime(2023, 5, 17, 12, 0, 35),
        ),
    ]

    result = state_serializer.build_rich_state(game_corrected, state, moves)

    assert result["game_status"] == "DRAW"
    assert result["winner"] is None
    # Legal moves are calculated based on the board state, not the game status.
    # In this full board draw state, there are no empty cells.
    assert result["legal_moves"] == []  # Board is full
    # last_updated should come from the latest move log
    expected_last_updated = datetime(2023, 5, 17, 12, 0, 35).isoformat()
    assert result["last_updated"] == expected_last_updated


def test_build_rich_state_no_moves_timestamp():
    """Test building state when no moves exist, uses game's created_at."""
    game = Game(
        id="game_abc",
        player_x_id="px",
        player_o_id="po",
        player_x_name="X",
        player_o_name="O",
        mode="pvp",
        board_state="         ",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X,
        move_count=0,
        created_at=datetime(2023, 5, 17, 13, 0, 0),
        finished_at=None,
    )
    state = GameState(
        board=[
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
            [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
        ],
        next_player=Mark.X,
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=0,
    )
    moves = []

    result = state_serializer.build_rich_state(game, state, moves)

    # last_updated should come from game's created_at since no moves exist
    expected_last_updated = datetime(2023, 5, 17, 13, 0, 0).isoformat()
    assert result["last_updated"] == expected_last_updated
