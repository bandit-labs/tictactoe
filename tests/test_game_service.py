# tests/test_game_service.py
import pytest
from unittest.mock import Mock, patch
from app.domain.models import GameState, Mark, GameStatus
from app.infra.orm_models import Game, MoveLog
from app.schemas.game import GameCreate
from app.schemas.move import MoveCreate
from app.services import game_service
from app.services.game_service import AI_PLAYER


# --- Mock Database Session ---
class MockDBSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []
        self._objects = {}

    def get(self, model_class, obj_id):
        return self._objects.get((model_class, obj_id))

    def add(self, obj):
        self.added.append(obj)
        if hasattr(obj, "id"):
            self._objects[(obj.__class__, obj.id)] = obj

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)

    def close(self):
        pass  # Mock close


# --- create_game Tests ---
def test_create_game_pvai():
    """Test creating a PvAI game."""
    db = MockDBSession()
    payload = GameCreate(player_x_id="player123", mode="pvai", ai_difficulty="hard")

    game = game_service.create_game(db, payload)

    assert isinstance(game, Game)
    assert game.mode == "pvai"
    assert game.player_x_id == "player123"
    assert game.player_o_id == "AI"
    assert game.player_o_name == "AI"
    assert game.ai_difficulty == "hard"
    assert game.status == GameStatus.IN_PROGRESS
    assert game.next_player == Mark.X
    assert game.board_state == " " * 9
    assert game in db.added
    assert db.committed


def test_create_game_pvp():
    """Test creating a PvP game."""
    db = MockDBSession()
    payload = GameCreate(
        player_x_id="player123",
        player_o_id="player456",
        mode="pvp",
        player_x_name="Alice",
        player_o_name="Bob",
    )

    game = game_service.create_game(db, payload)

    assert isinstance(game, Game)
    assert game.mode == "pvp"
    assert game.player_x_id == "player123"
    assert game.player_o_id == "player456"
    assert game.player_x_name == "Alice"
    assert game.player_o_name == "Bob"
    assert game.ai_difficulty is None
    assert game.status == GameStatus.IN_PROGRESS
    assert game.next_player == Mark.X
    assert game.board_state == " " * 9
    assert game in db.added
    assert db.committed


def test_create_game_pvp_missing_player_o():
    """Test creating a PvP game without player_o_id raises ValueError."""
    db = MockDBSession()
    payload = GameCreate(
        player_x_id="player123",
        # player_o_id missing
        mode="pvp",
    )

    with pytest.raises(ValueError, match="Player O_id is required for PvP mode"):
        game_service.create_game(db, payload)


def test_add_move_human_pvp():
    """Test adding a human move in a PvP game."""
    db = MockDBSession()
    # Create a game in the mock DB
    game = Game(
        id="test_game_1",
        player_x_id="player123",
        player_o_id="player456",
        mode="pvp",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X,
        move_count=0,
        board_state=" " * 9,
        created_at=None,  # Simplified for test
        finished_at=None,
    )
    db._objects[(Game, game.id)] = game

    payload = MoveCreate(row=0, col=0)

    with patch("app.services.game_service.log_move_to_platform"), patch(
        "app.services.game_service.send_final_result_to_platform"
    ):
        updated_game = game_service.add_move(db, game.id, payload)

    # Check game state updated
    assert updated_game.status == GameStatus.IN_PROGRESS
    assert updated_game.next_player == Mark.O
    assert updated_game.move_count == 1
    assert updated_game.board_state == "X" + " " * 8  # X at position (0,0)

    # Check MoveLog was created and added
    assert len(db.added) == 2  # The updated game object and the new MoveLog
    move_log = next((obj for obj in db.added if isinstance(obj, MoveLog)), None)
    assert move_log is not None
    assert move_log.game_id == game.id
    assert move_log.player_id == "player123"
    assert move_log.mark == Mark.X
    assert move_log.row == 0
    assert move_log.col == 0
    assert move_log.state_before is not None  # Dict populated by build_rich_state
    assert move_log.state_after is not None  # Dict populated by build_rich_state
    assert move_log.heuristic_value == 0.0  # From heuristic_value for in-progress game

    assert db.committed


def test_add_move_human_pvp_not_next_player():
    """Test adding a human move when it's not their turn."""
    db = MockDBSession()
    game = Game(
        id="test_game_2",
        player_x_id="player123",
        player_o_id="player456",
        mode="pvp",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.O,  # O's turn
        move_count=1,
        board_state="X" + " " * 8,  # X played at (0,0)
        created_at=None,
        finished_at=None,
    )
    db._objects[(Game, game.id)] = game

    payload = MoveCreate(
        row=0, col=1
    )  # X tries to play again, but service applies O's move
    # The service will apply the move for the *actual* next player (Mark.O) at the requested position (0,1)

    with patch("app.services.game_service.log_move_to_platform"), patch(
        "app.services.game_service.send_final_result_to_platform"
    ):
        updated_game = game_service.add_move(db, game.id, payload)

    # Check game state updated for O's move at (0,1)
    assert updated_game.next_player == Mark.X  # Next player is X after O played
    assert updated_game.move_count == 2
    # Board should be X at (0,0), O at (0,1) -> "XO       "
    assert updated_game.board_state == "XO" + " " * 7
    # The service correctly applies the move for the player whose turn it is (O), not necessarily
    # the player indicated by the coordinates in the payload if it's the wrong turn.


def test_add_move_ai_pvai():
    """Test adding an AI move in a PvAI game."""
    db = MockDBSession()
    game = Game(
        id="test_game_3",
        player_x_id="player123",
        player_o_id="AI",
        mode="pvai",
        ai_difficulty="medium",
        status=GameStatus.IN_PROGRESS,
        next_player=AI_PLAYER,  # O's turn (AI)
        move_count=1,
        board_state="X" + " " * 8,  # X played at (0,0)
        created_at=None,
        finished_at=None,
    )
    db._objects[(Game, game.id)] = game

    # Mock the AI client to return a specific move and evaluation
    ai_row, ai_col = 1, 1
    ai_eval = 0.75
    mock_request_ai_move = Mock(return_value=((ai_row, ai_col), ai_eval, {}))

    with patch(
        "app.services.game_service.request_ai_move", mock_request_ai_move
    ), patch("app.services.game_service.log_move_to_platform"), patch(
        "app.services.game_service.send_final_result_to_platform"
    ):
        updated_game = game_service.add_move(db, game.id, MoveCreate(), is_ai_move=True)

    # Verify AI client was called
    mock_request_ai_move.assert_called_once_with(
        state=GameState(
            board=[
                [Mark.X, Mark.EMPTY, Mark.EMPTY],
                [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
                [Mark.EMPTY, Mark.EMPTY, Mark.EMPTY],
            ],
            next_player=AI_PLAYER,
            status=GameStatus.IN_PROGRESS,
            winner=None,
            move_count=1,
        ),
        difficulty="medium",
    )

    # Check game state updated for AI's move at (1,1)
    # Board: X at (0,0), O at (1,1) -> "X  O     " (4 spaces between X and O, then 4 spaces)
    expected_board_str = list(" " * 9)
    expected_board_str[0] = "X"  # Index 0*3 + 0 = 0
    expected_board_str[4] = "O"  # Index 1*3 + 1 = 4
    expected_board_str = "".join(expected_board_str)
    assert updated_game.board_state == expected_board_str
    assert updated_game.next_player == Mark.X
    assert updated_game.move_count == 2

    # Check MoveLog was created for AI
    move_log = next((obj for obj in db.added if isinstance(obj, MoveLog)), None)
    assert move_log is not None
    assert move_log.player_id == "AI"
    assert move_log.mark == AI_PLAYER
    assert move_log.row == ai_row
    assert move_log.col == ai_col
    assert move_log.heuristic_value == ai_eval  # Uses AI's evaluation


def test_add_move_game_not_found():
    """Test adding a move to a non-existent game raises ValueError."""
    db = MockDBSession()
    payload = MoveCreate(row=0, col=0)

    with pytest.raises(ValueError, match="Game not found"):
        game_service.add_move(db, "non_existent_id", payload)


def test_add_move_game_finished():
    """Test adding a move to a finished game raises ValueError."""
    db = MockDBSession()
    game = Game(
        id="finished_game",
        player_x_id="player123",
        player_o_id="player456",
        mode="pvp",
        status=GameStatus.X_WON,  # Game is finished
        next_player=Mark.X,
        move_count=5,
        board_state="XXXOO O O",
        created_at=None,
        finished_at=None,
    )
    db._objects[(Game, game.id)] = game

    payload = MoveCreate(row=0, col=0)

    with pytest.raises(ValueError, match="Game already finished"):
        game_service.add_move(db, game.id, payload)


def test_add_move_missing_coords_for_human():
    """Test adding a move without row/col for a human player raises ValueError."""
    db = MockDBSession()
    game = Game(
        id="test_game_4",
        player_x_id="player123",
        player_o_id="player456",
        mode="pvp",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X,
        move_count=0,
        board_state=" " * 9,
        created_at=None,
        finished_at=None,
    )
    db._objects[(Game, game.id)] = game

    payload = MoveCreate()  # No row/col provided

    with pytest.raises(ValueError, match="row and col are required for human moves"):
        game_service.add_move(db, game.id, payload)
