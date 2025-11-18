import requests

PLATFORM_BACKEND_URL = "http://platform-backend:8080"

def log_move_to_platform(previous_state, new_state, move_idx, player_id):
    entry = {
        "game_id": new_state.game_id,
        "player_id": player_id,
        "move_index": move_idx,
        "move_number": new_state.move_count,
        "previous_state": previous_state.to_dict(),
        "next_state": new_state.to_dict(),
        "timestamp": new_state.last_updated,
        "heuristic_value": 0.0  # placeholder
    }
    requests.post(f"{PLATFORM_BACKEND_URL}/api/log_move", json=entry)

def send_final_result_to_platform(final_state):
    result = {
        "game_id": final_state.game_id,
        "winner": final_state.winner,
        "history": final_state.history,
        "final_state": final_state.to_dict()
    }
    requests.post(f"{PLATFORM_BACKEND_URL}/api/game_result", json=result)
