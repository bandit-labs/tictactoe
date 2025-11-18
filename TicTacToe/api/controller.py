import json
from TicTacToe.engine.gamestate import GameState
from TicTacToe.engine.mcts_agent import choose_ai_move
from TicTacToe.api.db import save_gamestate, delete_game
from TicTacToe.api.platform_client import log_move_to_platform, send_final_result_to_platform
from TicTacToe.config import db_session

def ai_move(game_state_json: str):
    state = GameState.from_dict(json.loads(game_state_json))
    previous = state

    move = choose_ai_move(state)
    new_state = state.apply_move(move)

    log_move_to_platform(previous, new_state, move, player_id="AI")
    save_gamestate(new_state.game_id, new_state, db_session)

    if new_state.game_status in ("WIN", "DRAW"):
        send_final_result_to_platform(new_state)
        delete_game(new_state.game_id, db_session)

    return new_state.to_json()
