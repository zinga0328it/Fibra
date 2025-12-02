"""
Test fixtures for Gestionale Fibra.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.config import Settings


@pytest.fixture
def settings():
    """Provide test settings."""
    return Settings(
        app_name="Gestionale Fibra Test",
        app_env="test",
        debug=True,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
    )


@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session
