# TicTacToe 

---

## Game Overview
This service implements the backend for a TicTacToe game.
It exposes a small HTTP API over FastAPI, persists game state in PostgreSQL using SQLAlchemy, and integrates with:
- an external AI service (for PvAI games)
- a platform backend for gameplay logging and analytics

#### All core game rules, turn validation and AI orchestration live in this backend.
#### The frontend or platform only sends high level commands like "create game", "play move", "mode = PvP or PvAI".

## Domain Model & Game Rules

**Domain lives in ``app/domain/models.py`` and ``app/domain/logic.py``**

### Key types

- ``Mark``
  - Enum: ``X`` | ``O`` | ``EMPTY``
- ``GameStatus``
  - Enum: ``IN_PROGRESS`` | ``DRAW`` | ``X_WON`` | ``O_WON`` 
- ``GameState``
  - Dataclass with:
    - ``board: List[List[Mark]]``
    - ``next_player: Mark``
    - ``status: GameStatus``
    - ``winner: Optional[Mark]``
    - ``move_count: int``

### Core functions

- ``apply_move(state, position)``
  - Validates that the game is still ``IN_PROGRESS``
  - Validates ``moves``
  - Writes the ``Mark`` on ``board``
  - Sets ``status`` based on winner / full board.
- ``board_to_string``
  -  Convert between ``GameState.board`` and a compact 9 character string stored in the database.
- ``heuristic_value(state, for_player)``
  - 1.0 if for_player has won
  - -1.0 if the opponent has won 
  - 0.0 otherwise

##### The domain knows nothing about HTTP, SQL, JSON or external services.

## Persistence & Database

- ``app/core/config.py``
  - ``database_url`` (PostgreSQL)
  - ``db_schema``
  - AI and platform URLs
- ``app/core/db.py``
  - Ensures the configured schema exists using ``CREATE SCHEMA IF NOT EXISTS``. 
  - Configures ``SessionLocal`` as a scoped session factory. 
  - Exposes ``get_db()`` as a FastAPI dependency that yields a session.
- ``app/infra/orm_models.py``
  - **Game**
    - ``id`` (UUID string primary key)
    - ``player ``ids`` and ``names`` for X and O 
    - ``status``, ``next_player``, ``move_count``
    - ``board_state`` as a 9 character string 
    - ``timestamps`` created_at and finished_at
    - ``moves`` relationship  with **MoveLog**
  - **MoveLog**
    - ``game_id`` (foreign key to games.id)
    - ``move_number``, player_id``, ``mark``, ``row``, ``col``
    - ``state_before`` and ``state_after`` as JSON
    - ``heuristic_value`` for AI and analytics 
    - ``created_at`` timestamp


## API endpoints

##### All endpoints are defined in ``app/api/v1/routes_games.py`` under prefix ``/games``.

### POST ``/games``
- Create a new game
  - Initializes:
    - **Empty Board**
    - ``next_player = X``
    - ``status = IN_PROGRESS``
    - ``move_count = 0``

### GET ``/games/{game_id}``
- Return current **state** of a game
  - Loads ``Game`` from the DB
  - Converts the stored ``board_state`` string back to a 3x3 array.
  - Returns ``GameRead``

### POST ``/games/{game_id}/moves``
- Apply exactly one move to the game and return immediately
- Input: ``MoveCreate``
  - ``row: Optional[int]``
  - ``col: Optional[int]``
  - ``use_ai: bool ``
    - ``False`` for pure **PvP**
    - ``True`` for **PvAI** games
  - ``ai_difficulty: Optional[str]``

### Game Modes

### Player vs Player (PvP)
- Client sends ``use_ai = false`` in ``MoveCreate``
- Every move is a human move
- Backend:
  - Validates the move
  - Applies it using ``apply_move``
  - Persists ``Game`` and ``MoveLog``
  - Returns the updated game
- Flow
  - ``X`` and ``O`` alternate turns.

### Player vs AI (PvAI)
- Client sends ``use_ai = true`` in ``MoveCreate``
- AI is playing as ``O``
- Flow
  - Human clicks cell and sends a ``MoveCreate`` with coordinates and ``use_ai = true``
  - ``game_service.add_move``:
    - Applies the human move as usual. 
    - Logs it in ``MoveLog``.
  - ``play_move`` endpoint:
    - Checks if game is still ``IN_PROGRESS`` and it is now AI turn. 
    - If yes, schedules a background task via ``BackgroundTasks.add_task(run_ai_move, ...)``.
  - ``run_ai_move``:
    - Opens a new DB session.
    - Creates a ``MoveCreate`` payload with ``use_ai = true`` and no coordinates.
    - Calls ``game_service.add_move``.
    - ``add_move`` detects that it is AI turn then calls ``request_ai_move``.
  - ``request_ai_move``:
    - Calls the external AI HTTP service with the current board and difficulty.
    - Receives the row and column for the AI move plus an evaluation score.
  - AI move is applied, logged and persisted like a normal move.

## AI Integration

##### AI integration is encapsulated in ``app/services/ai_client.py``.
- Builds a minimal payload that represents the current board and the current player for the external AI:
  - ``board``: 3x3 matrix with ``None`` for empty cells and ``"X"`` or ``"O"`` for marks.
  - ``currentPlayer``: ``"X"`` or ``"O"``.
- Sends a POST request to:
  - ``{AI_BASE_URL}/api/ai/move`` where ``AI_BASE_URL`` comes from settings.
- Expects JSON response with:
  - ``move`` object containing ``row`` and ``col``.
  - Optional ``evaluation`` and ``metadata``.
- game_service.add_move uses the evaluation value when logging the move which can later be used for analytics or training.

## Project structure
```
├── app/
│   ├── main.py                      # FastAPI entry point, CORS config, router registration, schema creation
│   │
│   ├── core/
│   │   ├── config.py                # Settings (DB URL, schema, AI URL, platform URL)
│   │   └── db.py                    # SQLAlchemy engine, schema bootstrap and SessionLocal factory
│   │
│   ├── domain/
│   │   ├── models.py                # Pure domain model: Mark, GameStatus, GameState
│   │   └── logic.py                 # Game rules: apply_move, win detection, board serialization, heuristics
│   │
│   ├── infra/
│   │   └── orm_models.py            # SQLAlchemy ORM models: Game and MoveLog
│   │
│   ├── api/
│   │   └── v1/
│   │       └── routes_games.py      # HTTP routes for /games: create, read, play move, schedules background AI task
│   │
│   ├── schemas/
│   │   ├── game.py                  # Pydantic DTOs: GameCreate, GameRead
│   │   └── move.py                  # Pydantic DTO: MoveCreate (row, col, use_ai, ai_difficulty)
│   │
│   └── services/
│       ├── ai_client.py             # HTTP client for external AI service, converts GameState to AI payload
│       ├── game_service.py          # Application service that applies moves, calls AI, builds MoveLog
│       ├── game_state_mapper.py     # Mapping between ORM Game and domain GameState
│       ├── platform_client.py       # HTTP client to platform backend for move and result logging
│       └── state_serializer.py      # Builds rich JSON view of game state for logging and analytics
│
└── (other files like requirements.txt, .env, ...)
```

## Unified file/directory structure for Containerization to work
## Project structure
```
YOUR FOLDER ROOT (Bandit Games, bandit, choose yourself, etc...)
├── ai-modules/                 # clone from git
│     └ ...
│
├── Game/                       # name however you like
│     ├── back/                 # name however you like
│     │    └── TicTacToe/       # clone from git (Game Backend code)
│     │         └ ...
│     └── front/                # name however you like
│          └── TicTacToe/       # clone from git (Game Frontend code)
│               └ ...
│
└── (In the future unified Platform code)

```

## Game original Source Code & Prompt Log
- Source code author:
  - **Marc Frances** (marcft)

- Source repository URL:
  - https://github.com/marcft/tic-tac-toe?tab=readme-ov-file

- [Prompt Log](https://docs.google.com/document/d/1cziGDg_u6mhYcuVqztXYtlwn1_R6nuIGRgQhXP1WxRE/edit?usp=sharing)