# TicTacToe/app.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from TicTacToe.api.controller import process_ai_move, logger  # Renamed function
from TicTacToe.config import get_db_session

app = FastAPI()

@app.post("/api/ai_move")
def move_endpoint(payload: dict, db_session: Session = Depends(get_db_session)):
    try:
        # payload is expected to have a "state_json" key
        state_json_str = payload.get("state_json")
        if not state_json_str:
            raise HTTPException(status_code=400, detail="Missing 'state_json' in request body")

        # Call the controller function, passing the session via dependency injection
        new_state_json = process_ai_move(state_json_str, db_session)
        return new_state_json

    except ValueError as e: # Handle errors from controller
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e: # Handle other unexpected errors
        logger.error(f"Unexpected error in API endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")