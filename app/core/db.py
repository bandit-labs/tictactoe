from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session

from app.core.config import settings

class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, future=True)

# ensure schema exists
with engine.connect() as conn:
    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.db_schema}"'))
    conn.commit()

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
