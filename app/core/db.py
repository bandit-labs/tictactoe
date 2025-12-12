# app/core/db.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session
from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Create engine, but DO NOT connect immediately
engine = create_engine(settings.database_url, future=True)

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)


def ensure_schema_exists():
    """
    Call this during application startup (e.g., in main.py or a lifespan event).
    Do NOT call it at module level.
    """
    with engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.db_schema}"'))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
