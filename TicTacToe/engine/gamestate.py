import copy
import json
from datetime import datetime

class GameState:
    EMPTY = "."

    def __init__(
        self,
        game_id=None,
        board=None,
        current_player="X",
        move_count=0,
        history=None,
        config=None,
        game_status="IN_PROGRESS",
        winner=None,
        last_updated=None
    ):
        self.game_id = game_id
        self.config = config or {"rows": 3, "cols": 3}
        self.board = board or [
            [self.EMPTY for _ in range(self.config["cols"])]
            for _ in range(self.config["rows"])
        ]
        self.current_player = current_player
        self.move_count = move_count
        self.history = history or []
        self.game_status = game_status
        self.winner = winner
        self.last_updated = last_updated or datetime.utcnow().isoformat()

    def get_legal_moves(self):
        moves = []
        for r in range(self.config["rows"]):
            for c in range(self.config["cols"]):
                if self.board[r][c] == self.EMPTY:
                    moves.append(r * self.config["cols"] + c)
        return moves

    def check_winner(self):
        b = self.board
        n = self.config["rows"]

        # Rows
        for r in range(n):
            if b[r][0] != self.EMPTY and len(set(b[r])) == 1:
                return b[r][0]

        # Columns
        for c in range(n):
            col = [b[r][c] for r in range(n)]
            if col[0] != self.EMPTY and len(set(col)) == 1:
                return col[0]

        # Diagonals
        diag1 = [b[i][i] for i in range(n)]
        diag2 = [b[i][n - i - 1] for i in range(n)]
        if diag1[0] != self.EMPTY and len(set(diag1)) == 1:
            return diag1[0]
        if diag2[0] != self.EMPTY and len(set(diag2)) == 1:
            return diag2[0]

        return None

    def apply_move(self, move_idx: int):
        new_state = copy.deepcopy(self)
        r = move_idx // self.config["cols"]
        c = move_idx % self.config["cols"]

        if new_state.board[r][c] != self.EMPTY:
            raise ValueError("Illegal move")

        new_state.board[r][c] = self.current_player
        new_state.history.append({"player": self.current_player, "move": move_idx})

        new_state.move_count += 1
        new_state.last_updated = datetime.utcnow().isoformat()

        winner = new_state.check_winner()
        if winner:
            new_state.game_status = "WIN"
            new_state.winner = winner
        elif new_state.move_count == self.config["rows"] * self.config["cols"]:
            new_state.game_status = "DRAW"
        else:
            new_state.current_player = "O" if self.current_player == "X" else "X"

        return new_state

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "board": self.board,
            "current_player": self.current_player,
            "legal_moves": self.get_legal_moves(),
            "move_count": self.move_count,
            "game_status": self.game_status,
            "winner": self.winner,
            "config": self.config,
            "history": self.history,
            "last_updated": self.last_updated
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data):
        return GameState(
            game_id=data["game_id"],
            board=data["board"],
            current_player=data["current_player"],
            move_count=data["move_count"],
            game_status=data["game_status"],
            winner=data["winner"],
            config=data["config"],
            history=data["history"],
            last_updated=data.get("last_updated")
        )
