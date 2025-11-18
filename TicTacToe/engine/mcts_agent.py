from TicTacToe.engine.gamestate import GameState

def choose_ai_move(state: GameState):
    # Later replaced with real MCTS
    legal = state.get_legal_moves()
    return legal[0]  # pick first legal move
