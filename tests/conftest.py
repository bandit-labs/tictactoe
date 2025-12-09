# tests/conftest.py
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import sessionmaker


@pytest.fixture(autouse=True)
def mock_db_engine():
    """
    Automatically mock the database engine for all tests.
    This prevents any test from trying to connect to a real database.
    """
    # Create a mock engine and session factory
    mock_engine = MagicMock()
    mock_session_factory = MagicMock(spec=sessionmaker)

    # Patch the engine and session factory in the core module
    with patch("app.core.db.engine", mock_engine), \
         patch("app.core.db.SessionLocal", mock_session_factory):
        yield  # Run the test