# TicTacToe/api/platform_client.py
import requests
import logging

PLATFORM_BACKEND_URL = "http://platform-backend:8080"
logger = logging.getLogger(__name__)

def log_move_to_platform(previous_state, new_state, move_idx, player_id, heuristic_value=0.0):
    """
    Sends move metrics to the main platform backend.
    """
    entry = {
        "game_id": new_state.game_id,
        "player_id": player_id,
        "move_index": move_idx,
        "move_number": new_state.move_count, # Use the count AFTER the move was applied
        "previous_state": previous_state.to_dict(),
        "next_state": new_state.to_dict(),
        "timestamp": new_state.last_updated,
        "heuristic_value": heuristic_value # Pass the calculated value
    }

    try:
        response = requests.post(f"{PLATFORM_BACKEND_URL}/api/log_move", json=entry, timeout=10) # Add timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        logger.info(f"Move log for game {new_state.game_id} sent to platform successfully.")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to platform backend at {PLATFORM_BACKEND_URL} for logging: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout sending move log to platform backend: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from platform backend when logging move: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e: # Catch other requests errors
        logger.error(f"Request error sending move log to platform: {e}")
    except Exception as e: # Catch unexpected errors during request
        logger.error(f"Unexpected error during platform logging request: {e}")

def send_final_result_to_platform(final_state):
    """
    Sends final game result to the main platform backend.
    """
    result = {
        "game_id": final_state.game_id,
        "winner": final_state.winner,
        "history": final_state.history,
        "final_state": final_state.to_dict()
    }

    try:
        response = requests.post(f"{PLATFORM_BACKEND_URL}/api/game_result", json=result, timeout=10)
        response.raise_for_status()
        logger.info(f"Final result for game {final_state.game_id} sent to platform successfully.")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to platform backend for final result: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout sending final result to platform: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from platform backend for final result: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending final result to platform: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during final result request: {e}")