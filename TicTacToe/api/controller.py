# TicTacToe/api/controller.py
import json
import logging
from sqlalchemy.orm import Session
from fastapi import Depends
from TicTacToe.engine.gamestate import GameState
from TicTacToe.engine.mcts_agent import choose_ai_move
from TicTacToe.api.db import save_or_update_gamestate, log_move_locally
from TicTacToe.api.platform_client import log_move_to_platform, send_final_result_to_platform
from TicTacToe.config import get_db_session

logger = logging.getLogger(__name__)

def process_ai_move(game_state_json: str, db_session: Session = Depends(get_db_session)):
    """
    Processes an AI move request.
    Handles state loading, AI move selection, state saving, logging, and final result handling.
    """
    try:
        # 1. Deserialize the input state
        state_dict = json.loads(game_state_json)
        state = GameState.from_dict(state_dict)

        # 2. Get previous state (before AI move)
        previous = state

        # 3. Select AI move
        move = choose_ai_move(state)

        # 4. Apply the move to get the new state
        new_state = state.apply_move(move)

        # 5. Save the NEW state permanently to the local gamedb
        save_or_update_gamestate(new_state.game_id, new_state, db_session)

        # 6. Calculate heuristic value (placeholder for now)
        heuristic_value = 0.0 # Replace with actual calculation logic later

        # 7. Log the move metrics (to local DB AND/OR platform DB)
        # Log locally (optional, useful for independent analysis)
        log_move_locally(previous, new_state, move, player_id="AI", heuristic_value=heuristic_value, session=db_session)

        # Log to the main platform backend
        log_move_to_platform(previous, new_state, move, player_id="AI", heuristic_value=heuristic_value)

        # 8. Check if the game is over
        if new_state.game_status in ("WIN", "DRAW"):
            # 8a. Send final result to platform
            send_final_result_to_platform(new_state)

        # 9. Return the new state
        return new_state.to_json()

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received for game state: {e}")
        raise ValueError("Invalid JSON format for game state") # Or return an HTTP error in FastAPI
    except ValueError as e: # Handles errors from GameState.apply_move (e.g., illegal move)
        logger.error(f"Value error during move processing: {e}")
        raise # Re-raise or handle as needed
    except Exception as e: # Catch other unexpected errors
        logger.error(f"Unexpected error processing AI move: {e}")
        raise # Re-raise or handle as needed
