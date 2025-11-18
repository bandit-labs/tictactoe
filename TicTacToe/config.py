# config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This hostname "gamedb" is the Docker service name from docker-compose.yml
DATABASE_URL = "postgresql://game_user:game_password@gamedb:5432/game_db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

db_session = SessionLocal()
