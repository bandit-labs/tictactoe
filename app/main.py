from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes_games import router as games_router
from app.core.db import Base, engine

# dev-time schema creation; later replace with Alembic migrations
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TicTacToe Backend")

# allow frontend during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://tictactoe-frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router)


# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
