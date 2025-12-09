# Tic-Tac-Toe Game Backend

A production-ready FastAPI backend implementing a Tic-Tac-Toe game with AI integration. 

Built following Clean Architecture principles with a rich domain model, three-layer architecture, and SOLID design patterns.

## Architecture Overview

This backend follows Clean Architecture with strict separation of concerns acrossyyy three distinct layers:

**Domain Layer**: Contains pure business logic with no external dependencies. Implements rich domain entities, immutable value objects, and domain services that encapsulate game rules and behavior.

**Application Layer**: Orchestrates use cases and coordinates between domain logic and infrastructure. Manages transactions, handles commands/queries, and transforms data between layers.

**Infrastructure Layer**: Implements interfaces defined by the domain layer. Handles database persistence, external HTTP services, and technical concerns.

## Technology Stack

- **Framework**: FastAPI 0.121.2
- **Database**: PostgreSQL with SQLAlchemy 2.0.44
- **Validation**: Pydantic 2.12.4
- **HTTP Client**: Requests 2.32.5
- **Server**: Uvicorn with standard extras

## Game original Source Code & Prompt Log
- Source code author:
  - **Marc Frances** (marcft)

- Source repository URL:
  - https://github.com/marcft/tic-tac-toe?tab=readme-ov-file

- [Prompt Log](https://docs.google.com/document/d/1cziGDg_u6mhYcuVqztXYtlwn1_R6nuIGRgQhXP1WxRE/edit?usp=sharing)

## Project Structure

```
app/
├── domain/                      # Domain Layer (Core Business Logic)
│   ├── value_objects.py        # Immutable value objects (Mark, Position, Board, etc.)
│   ├── entities.py             # Rich domain entities (Game, Move, Player)
│   ├── services.py             # Domain services (GameRules, PlayerFactory)
│   ├── interfaces.py           # Abstract interfaces (ports)
│   └── __init__.py             # Domain API exports
│
├── application/                 # Application Layer (Use Cases)
│   ├── dtos.py                 # Data Transfer Objects (Commands, Queries, Responses)
│   ├── use_cases.py            # Use case implementations
│   ├── mappers.py              # Domain to DTO conversion
│   └── __init__.py             # Application API exports
│
├── infrastructure/              # Infrastructure Layer (External Dependencies)
│   ├── orm_models.py           # SQLAlchemy ORM definitions
│   ├── persistence/
│   │   ├── repositories.py     # SQLAlchemy repository implementation
│   │   ├── mappers.py          # Domain to ORM conversion
│   │   └── __init__.py
│   └── services/
│       ├── ai_service.py       # HTTP AI service client
│       ├── platform_service.py # Platform integration client
│       ├── game_state_serializer.py
│       └── __init__.py
│
├── api/                         # Presentation Layer
│   └── v1/
│       └── routes_games.py     # FastAPI route handlers
│
├── core/                        # Core Configuration
│   ├── config.py               # Application settings
│   ├── db.py                   # Database configuration
│   └── dependencies.py         # Dependency injection container
│
│
├── schemas/                     # API Schemas
│   ├── game.py                 # Game request/response schemas
│   └── move.py                 # Move request schemas
│
└── main.py                      # Application entry point
```

## Domain Model

### Entities

**Game**: Aggregate root managing the game lifecycle. Enforces business rules for move validation, turn management, and game state transitions. Coordinates Player and Move entities.

**Player**: Represents a game participant with identity (PlayerId), name, and assigned mark (X or O). Includes logic for AI player identification.

**Move**: Represents a single game action with position, player, mark, and associated metadata including heuristic evaluation.

### Value Objects

**Board**: Immutable 3x3 grid representation. Provides operations for cell access, mark placement, and empty position detection. Converts between string and list representations.

**Position**: Immutable row/column coordinate with validation. Supports conversion to/from linear index (0-8).

**Mark**: Enum representing X, O, or EMPTY states. Provides opposite() method for turn alternation.

**PlayerId**: Value object wrapping player identifier with AI detection logic.

**GameStatus**: Enum tracking game state (IN_PROGRESS, X_WON, O_WON, DRAW) with completion checking.

**GameMode**: Enum defining play modes (PVP for player vs player, PVAI for player vs AI).

**AIDifficulty**: Enum for AI strength levels (EASY, MEDIUM, HARD).

### Domain Services

**GameRules**: Stateless service implementing game logic including win detection, move validation, legal move calculation, and heuristic evaluation. Defines all winning line combinations.

**PlayerFactory**: Factory service for player creation and AI player identification.

## Application Layer

### Use Cases

**CreateGameUseCase**: Handles new game creation. Validates player configuration based on game mode, initializes game entity, and persists to repository.

**GetGameUseCase**: Retrieves game by identifier from repository.

**PlayMoveUseCase**: Orchestrates move execution. Coordinates AI move calculation when needed, applies move through domain entity, persists changes, and logs to external platform. Manages both human and AI moves.

**PlayAIMoveUseCase**: Specialized use case for background AI move execution with independent session management.

### Data Transfer Objects

Commands encapsulate user intent with validation. Queries define data retrieval requests. Response DTOs provide API-compatible data structures. All use Pydantic for validation and serialization.

## Infrastructure Layer

### Repository Implementation

**SQLAlchemyGameRepository**: Implements IGameRepository interface. Handles bidirectional conversion between domain entities and ORM models. Manages database transactions and session lifecycle.

### External Services

**HttpAIService**: Implements IAIService interface. Communicates with external AI service via HTTP. Converts board state to AI-compatible format and parses move responses. Includes timeout and error handling.

**HttpPlatformService**: Implements IPlatformService interface. Provides fire-and-forget logging to platform backend. Logs individual moves and final game results without blocking game flow.

**GameStateSerializer**: Implements IGameStateSerializer interface. Converts domain game state to dictionary format for API responses and platform communication.

### ORM Mapping

Mappers handle conversion between rich domain entities and database ORM models. GameORMMapper reconstructs full domain entities from persistence including move history and all value objects.

## Dependency Injection

The application uses FastAPI's dependency injection system with a centralized container in core/dependencies.py.

**Singleton Services**: AI service, platform service, and state serializer are cached singletons shared acrossyyy requests.

**Scoped Dependencies**: Database sessions and repositories are request-scoped, created fresh for each API call.

**Use Case Factories**: Use cases are constructed per-request with all required dependencies injected through constructor parameters.

## API Endpoints

### Create Game
```
POST /games
Body: {
  "player_x_id": "string",
  "player_x_name": "string" (optional),
  "player_o_id": "string" (optional, required for PvP),
  "player_o_name": "string" (optional),
  "mode": "pvai" | "pvp",
  "ai_difficulty": "easy" | "medium" | "hard" (optional, default: medium)
}
Response: GameResponse with complete game state
```

### Get Game
```
GET /games/{game_id}
Response: GameResponse with current game state
```

### Play Move
```
POST /games/{game_id}/moves
Body: {
  "row": 0-2 (optional for AI move),
  "col": 0-2 (optional for AI move),
  "ai_difficulty": "easy" | "medium" | "hard" (optional)
}
Response: GameResponse with updated game state
```

For PvAI games, human moves trigger automatic AI response via background task.

## Game Modes

**Player vs Player (PvP)**: Two human players alternate turns. Both player IDs required at game creation.

**Player vs AI (PvAI)**: Human plays as X, AI plays as O. AI moves are calculated by external service using Monte Carlo Tree Search with configurable difficulty.

### AI Difficulty Levels

**Easy**: 1,000 MCTS iterations, 30% random move probability. Fast response with frequent mistakes.

**Medium**: 5,000 MCTS iterations, 15% random move probability. Balanced performance and difficulty.

**Hard**: 30,000 MCTS iterations, 0% random move probability. Optimal play with slower response time.

## Database Schema

The application uses PostgreSQL with a configurable schema (default: tictactoe).

**games table**: Stores game state including player information, current status, board representation, mode, difficulty, and timestamps.

**moves table**: Records move history with position, player, mark, game state snapshots (before/after), heuristic values, and timestamps. Foreign key to games with cascade delete.

## Configuration

Application settings are managed through environment variables with defaults defined in core/config.py.

**DATABASE_URL**: PostgreSQL connection string (default: postgresql://user:password@localhost:5442/integration)

**DB_SCHEMA**: Database schema name (default: tictactoe)

**AI_SERVICE_URL**: Base URL for external AI service (default: http://localhost:8001)

**PLATFORM_BACKEND_URL**: Base URL for platform backend logging (default: http://localhost:8080/api/v1)

Configuration supports .env file for local development.

## Running the Application

### Prerequisites

- Python 3.12+
- PostgreSQL database running and accessible
- External AI service running (for PvAI mode)
- Platform backend running (optional, for logging)

### Installation

```bash
pip install -r requirements.txt
```

### Database Setup

The application automatically creates the configured schema on startup. Tables are created via SQLAlchemy metadata.

### Starting the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000 with interactive documentation at http://localhost:8000/docs.

## Design Principles

### SOLID Principles

**Single Responsibility**: Each class has one reason to change. Game entity manages game state, repository handles persistence, AI service manages AI communication.

**Open/Closed**: System is extensible without modification. New AI strategies can be added by implementing IAIService. New repositories can be added by implementing IGameRepository.

**Liskov Substitution**: All interface implementations are substitutable. Any IGameRepository implementation can replace SQLAlchemyGameRepository without code changes.

**Interface Segregation**: Interfaces are small and focused. IGameRepository has only three methods: save, find_by_id, delete.

**Dependency Inversion**: High-level modules depend on abstractions. Use cases depend on IGameRepository interface, not concrete SQLAlchemy implementation.

### Domain-Driven Design

The application implements DDD tactical patterns including rich entities with behavior, immutable value objects, domain services for crossyyy-entity logic, and aggregate pattern with Game as root.

### Repository Pattern

Data access is abstracted through repository interfaces. Domain layer defines what operations are needed without knowing how they're implemented. Infrastructure layer provides concrete implementations.

### Use Case Pattern

Each user action is encapsulated in a dedicated use case class. Use cases orchestrate domain objects and coordinate with infrastructure without containing business logic.

## Testing Strategy

### Unit Tests

Domain entities and services can be tested in isolation without any infrastructure dependencies. Use cases can be tested with mocked repositories and services.

### Integration Tests

API endpoints can be tested with FastAPI TestClient using a test database. Full request/response cycle validation including database persistence.

## Error Handling

The application includes comprehensive error handling at each layer.

**Domain Layer**: Raises ValueError for business rule violations (invalid moves, game already finished, wrong player turn).

**Application Layer**: Catches domain exceptions and converts to appropriate HTTP responses.

**Infrastructure Layer**: Handles external service failures gracefully. AI and platform service errors are logged but don't break gameplay. Database errors propagate as 500 responses.

## Logging

The application includes structured logging at key integration points for debugging and monitoring. Use cases log difficulty settings and player actions. Infrastructure services log external API calls with parameters.


## License

This project is part of the Bandit Games project.
