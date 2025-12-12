from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes_games import router as games_router
from app.core.db import Base, engine
from app.core.db import ensure_schema_exists

# dev-time schema creation; later replace with Alembic migrations
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TicTacToe Backend")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@app.on_event("startup")
def startup_event():
    ensure_schema_exists()


# allow frontend during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router)


# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
