# TicTacToe/api/db.py
from sqlalchemy import update, delete
from sqlalchemy.exc import SQLAlchemyError
from TicTacToe.api.models import GameStateModel, MoveLogModel
import logging

logger = logging.getLogger(__name__)

def save_or_update_gamestate(game_id: str, state, session):
    """
    Saves or updates the full GameState in the local gamedb.
    Uses an upsert strategy (UPDATE if exists, INSERT if not).
    """
    try:
        stmt = update(GameStateModel).where(
            GameStateModel.game_id == game_id
        ).values(
            state_json=state.to_dict(),
            game_status=state.game_status,
            winner=state.winner,
            move_count=state.move_count,
            updated_at=state.last_updated
        ).execution_options(synchronize_session="fetch") # Handle potential no-rows-updated case

        result = session.execute(stmt)

        # If no rows were updated, it means the game_id didn't exist, so insert it
        if result.rowcount == 0:
            new_entry = GameStateModel(
                game_id=game_id,
                state_json=state.to_dict(),
                game_status=state.game_status,
                winner=state.winner,
                move_count=state.move_count,
                updated_at=state.last_updated
            )
            session.add(new_entry)

        session.commit()
        logger.info(f"GameState for game {game_id} saved/updated successfully.")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error saving GameState for game {game_id}: {e}")
        raise # Re-raise to handle in controller
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error saving GameState for game {game_id}: {e}")
        raise # Re-raise to handle in controller

def log_move_locally(previous_state, new_state, move_idx, player_id, heuristic_value=None, session=None):
    """
    Logs a single move's metrics to the local move_logs table.
    This is an alternative to or in addition to sending to the platform.
    """
    try:
        log_entry = MoveLogModel(
            game_id=new_state.game_id,
            player_id=player_id,
            move_index=move_idx,
            move_number=new_state.move_count, # move_count was incremented in apply_move
            previous_state_snapshot=previous_state.to_dict(), # Optional, depending on analysis needs
            next_state_snapshot=new_state.to_dict(),         # Optional, depending on analysis needs
            timestamp=new_state.last_updated, # Use the timestamp from the state object
            heuristic_value=heuristic_value
        )
        session.add(log_entry)
        session.commit()
        logger.info(f"Move log for game {new_state.game_id}, move {new_state.move_count} saved locally.")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error logging move for game {new_state.game_id}: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error logging move for game {new_state.game_id}: {e}")
        raise
