"""
Pytest configuration and fixtures for news-sentiment tests.

This module provides:
- Environment setup (loads .env.test if exists)
- Common fixtures for testing
- Database fixtures for integration tests
"""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from dotenv import load_dotenv


# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest before running tests.

    Loads environment variables from .env.test if it exists,
    otherwise falls back to .env.
    """
    env_test = PROJECT_ROOT / ".env.test"
    env_default = PROJECT_ROOT / ".env"

    if env_test.exists():
        load_dotenv(env_test)
    elif env_default.exists():
        load_dotenv(env_default)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_path() -> Path:
    """Return the src directory path."""
    return SRC_PATH


@pytest.fixture
def clean_env() -> Generator[dict, None, None]:
    """Provide a clean environment for tests that modify env vars.

    Saves current environment, yields it, then restores it after test.
    """
    original_env = os.environ.copy()
    yield original_env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_env_vars(clean_env: dict) -> Generator[dict, None, None]:
    """Provide mock environment variables for database config tests.

    Sets up minimal valid configuration for testing without real credentials.
    """
    test_vars = {
        "MARKETS_DB_HOST": "localhost",
        "MARKETS_DB_PORT": "5432",
        "MARKETS_DB_NAME": "test_markets",
        "MARKETS_DB_USER": "test_user",
        "MARKETS_DB_PASSWORD": "test_password",
        "AI_MODEL_DB_HOST": "localhost",
        "AI_MODEL_DB_PORT": "5432",
        "AI_MODEL_DB_NAME": "test_ai_model",
        "AI_MODEL_DB_USER": "test_user",
        "AI_MODEL_DB_PASSWORD": "test_password",
        "GEMINI_API_KEY": "test_api_key",
        "GEMINI_MODEL": "gemini-pro",
    }
    os.environ.update(test_vars)
    yield test_vars


# Database fixtures will be added when database module is ready
# These are placeholders for integration tests

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine.

    Uses SQLite in-memory database for fast, isolated tests.
    Will be implemented when SQLAlchemy models are available.
    """
    # TODO: Implement when Stream A completes database models
    # from sqlalchemy import create_engine
    # from src.database.models import Base
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine)
    # yield engine
    # Base.metadata.drop_all(engine)
    pytest.skip("Database models not yet implemented")


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session.

    Provides a transactional session that rolls back after each test.
    """
    # TODO: Implement when database module is ready
    pytest.skip("Database session not yet implemented")
