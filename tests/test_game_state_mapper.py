# tests/test_game_state_mapper.py
import pytest
from app.domain.models import GameState, Mark, GameStatus
from app.infra.orm_models import Game
from app.services import game_state_mapper

def test_game_to_state():
    """Test mapping ORM Game object to domain GameState."""
    # The board_state string uses ' ' for empty, not '.'
    # String: "XXOOO XOX"
    # Board:
    # X X O (row 0: pos 0,1,2)
    # O O _ (row 1: pos 3,4,5) -> _ is space ' '
    # X O X (row 2: pos 6,7,8)
    orm_game = Game(
        id="test_game_123",
        player_x_id="player1",
        player_o_id="player2",
        player_x_name="Alice",
        player_o_name="Bob",
        status=GameStatus.X_WON, # Status indicates X won (e.g., row 0)
        next_player=Mark.O, # Doesn't matter for finished game, but let's set it
        move_count=5,
        mode="pvp",
        board_state="XXOOO XOX", # Corrected string
        created_at=None,
        finished_at=None,
        moves=[] # Simplified for this test
    )

    domain_state = game_state_mapper.game_to_state(orm_game)

    expected_board = [
        [Mark.X, Mark.X, Mark.O], # Row 0
        [Mark.O, Mark.O, Mark.EMPTY], # Row 1
        [Mark.X, Mark.O, Mark.X]  # Row 2
    ]
    assert domain_state.board == expected_board
    assert domain_state.next_player == Mark.O
    assert domain_state.status == GameStatus.X_WON
    assert domain_state.winner == Mark.X # Should be derived from status
    assert domain_state.move_count == 5

def test_state_to_game():
    """Test mapping domain GameState to ORM Game object."""
    domain_state = GameState(
        board=[[Mark.X, Mark.EMPTY, Mark.O],
               [Mark.O, Mark.X, Mark.EMPTY],
               [Mark.EMPTY, Mark.O, Mark.X]],
        next_player=Mark.O,
        status=GameStatus.IN_PROGRESS,
        winner=None,
        move_count=4
    )
    # Start with an existing ORM game object
    orm_game = Game(
        id="test_game_456",
        player_x_id="player3",
        player_o_id="player4",
        player_x_name="Charlie",
        player_o_name="Dave",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X, # Will be updated
        move_count=3,       # Will be updated
        mode="pvp",
        board_state="X OOX  O", # Will be updated
        created_at=None,
        finished_at=None,
        moves=[]
    )

    updated_orm_game = game_state_mapper.state_to_game(orm_game, domain_state)

    expected_board_str = "X OOX  OX" # From the board state
    assert updated_orm_game.board_state == expected_board_str
    assert updated_orm_game.status == GameStatus.IN_PROGRESS
    assert updated_orm_game.next_player == Mark.O
    assert updated_orm_game.move_count == 4
    # finished_at should remain None as game is in progress
    assert updated_orm_game.finished_at is None

def test_state_to_game_finished_sets_finished_at():
    """Test that state_to_game sets finished_at when game status changes to finished."""
    from datetime import datetime
    # Initial state is in progress
    domain_state = GameState(
        board=[[Mark.X, Mark.O, Mark.X],
               [Mark.O, Mark.X, Mark.O],
               [Mark.O, Mark.X, Mark.O]],
        next_player=Mark.O, # Doesn't matter now
        status=GameStatus.DRAW, # Status changes to finished
        winner=None,
        move_count=9
    )
    orm_game = Game(
        id="test_game_789",
        player_x_id="player5",
        player_o_id="player6",
        player_x_name="Eve",
        player_o_name="Frank",
        status=GameStatus.IN_PROGRESS, # Was in progress
        next_player=Mark.O,
        move_count=8,
        mode="pvp",
        board_state="XOXOXO.OX", # Before final move
        created_at=datetime(2023, 1, 1), # Fixed created_at
        finished_at=None, # Was None
        moves=[]
    )

    updated_orm_game = game_state_mapper.state_to_game(orm_game, domain_state)

    assert updated_orm_game.status == GameStatus.DRAW
    assert updated_orm_game.finished_at is not None # Should be set by the mapper
    assert updated_orm_game.finished_at >= datetime(2023, 1, 1) # Should be now or later than created_at
    # Check that it was only set if it was previously None
    initial_finished_at = datetime(2024, 1, 1)
    orm_game_with_finished_at = Game(
        id="test_game_abc",
        player_x_id="player7",
        player_o_id="player8",
        player_x_name="Grace",
        player_o_name="Henry",
        status=GameStatus.IN_PROGRESS,
        next_player=Mark.X,
        move_count=0,
        mode="pvp",
        board_state="         ",
        created_at=datetime(2023, 1, 1),
        finished_at=initial_finished_at, # Already set
        moves=[]
    )
    domain_state_won = GameState(
        board=[[Mark.X, Mark.X, Mark.X],
               [Mark.O, Mark.EMPTY, Mark.O],
               [Mark.O, Mark.EMPTY, Mark.EMPTY]],
        next_player=Mark.O,
        status=GameStatus.X_WON,
        winner=Mark.X,
        move_count=5
    )
    updated_orm_game_with_finished_at = game_state_mapper.state_to_game(orm_game_with_finished_at, domain_state_won)
    # finished_at should remain unchanged if it was already set
    assert updated_orm_game_with_finished_at.finished_at == initial_finished_at