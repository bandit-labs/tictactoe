from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LOCAL DEV DEFAULT:
    # Docker postgres is mapped host->container: 5443:5432
    database_url: str = Field(
        default="postgresql://user:password@localhost:5443/postgres",
        description="SQLAlchemy database URL",
    )

    db_schema: str = "tictactoe"

    demo_player_x_id: str = "demo-x"
    demo_player_o_id: str = "demo-o"
    demo_player_x_name: str = "Player X"
    demo_player_o_name: str = "Player O"

    class Config:
        env_file = ".env"


settings = Settings()
