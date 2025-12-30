from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://user:password@localhost:5442/integration",
        description="SQLAlchemy database URL",
    )

    db_schema: str = "tictactoe"

    demo_player_x_id: str = "demo-x"
    demo_player_o_id: str = "demo-o"
    demo_player_x_name: str = "Player X"
    demo_player_o_name: str = "Player O"

    ai_service_url: str = Field(
        default="http://localhost:8002",
        description="Base URL of the external AI service (MCTS/Minimax)",
    )
    ml_service_url: str = Field(
        default="http://localhost:8001",
        description="Base URL of the ML prediction service",
    )
    ai_difficulty_default: str = Field(
        default="medium",
        description="Default AI difficulty (easy|medium|hard)",
    )
    platform_backend_url: str = Field(
        default="http://localhost:8080/api/v1",
        description="Base URL of the main Platform backend for logging",
    )

    # RabbitMQ
    rabbitmq_user: str = 'user'
    rabbitmq_password: str = "password"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    class Config:
        env_file = ".env"


settings = Settings()
