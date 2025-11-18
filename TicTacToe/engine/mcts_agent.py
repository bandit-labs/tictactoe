# TicTacToe/engine/mcts_agent.py
from TicTacToe.engine.gamestate import GameState

def choose_ai_move(state: GameState):
    # Later replaced with real MCTS
    legal = state.get_legal_moves()
    if not legal:
        raise ValueError("No legal moves available, game should be over.")
    return legal[0]  # pick first legal move - TO BE REPLACED WITH MCTS