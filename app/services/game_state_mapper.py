from app.domain.models import GameState, Mark, GameStatus
from app.domain.logic import board_from_string, board_to_string
from app.infra.orm_models import Game


def game_to_state(game: Game) -> GameState:
    board = board_from_string(game.board_state)
    winner = None
    if game.status == GameStatus.X_WON:
        winner = Mark.X
    elif game.status == GameStatus.O_WON:
        winner = Mark.O

    return GameState(
        board=board,
        next_player=game.next_player,
        status=game.status,
        winner=winner,
        move_count=game.move_count,
    )


def state_to_game(game: Game, state: GameState) -> Game:
    game.board_state = board_to_string(state.board)
    game.status = state.status
    game.next_player = state.next_player
    game.move_count = state.move_count
    # finished_at is set when game is no longer IN_PROGRESS
    if state.status != GameStatus.IN_PROGRESS and game.finished_at is None:
        from datetime import datetime

        game.finished_at = datetime.utcnow()
    return game
