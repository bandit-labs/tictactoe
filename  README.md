# TicTacToe 

---

## Game Overview
This service implements the backend for a TicTacToe game.
It exposes a small HTTP API over FastAPI, persists game state in PostgreSQL using SQLAlchemy, and integrates with:
- an external AI service (for PvAI games)
- a platform backend for gameplay logging and analytics

#### All core game rules, turn validation and AI orchestration live in this backend.
#### The frontend or platform only sends high level commands like "create game", "play move", "mode = PvP or PvAI".

## Architecture
This structure keeps rules and state transitions in the domain layer,
IO in services, and HTTP handling in the API layer

- ``app/main.py``
    - **FastAPI** application entry point, **CORS** config, router registration, schema creation
- ``app/api/v1/routes_games.py``
    - **HTTP API** for:
      - **Creating games**
      - **Reading games**
      - **Applying moves** 
    - Orchestrates background AI moves.
- ``app/domain/*``
    - Pure domain logic:
      - **Marks**
      - **Game status**
      - **In memory board**
      - **Move application**
- ``app/infra/orm_models.py``
    - SQLAlchemy models Game and MoveLog for persistence and replay.
- ``app/services/*``
    - ``game_service``
      - Applying moves and logging
    - ``ai_client``
      - Calling external AI
    - ``platform_client``
      - Logging to the Platform backend
    - ``state_serializer``
      - Building rich JSON state
    - ``game_state_mapper``
      - Mapping between ORM and Domain models
- ``app/core/*``
      - Settings and Database bootstrapping.

## Domain Model & Game Rules
