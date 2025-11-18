from fastapi import FastAPI
from TicTacToe.api.controller import ai_move

app = FastAPI()

@app.post("/api/ai_move")
def move_endpoint(payload: dict):
    return ai_move(payload["state_json"])
