from sqlalchemy import update, delete
from TicTacToe.api.models import GameStateModel


def save_gamestate(game_id, state, session):
    stmt = update(GameStateModel).where(
        GameStateModel.game_id == game_id
    ).values(
        state_json=state.to_dict(),
        game_status=state.game_status,
        winner=state.winner,
        move_count=state.move_count,
        updated_at=state.last_updated
    )
    session.execute(stmt)
    session.commit()

def delete_game(game_id, session):
    stmt = delete(GameStateModel).where(GameStateModel.game_id == game_id)
    session.execute(stmt)
    session.commit()
