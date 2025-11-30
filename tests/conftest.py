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
    otherwise falls back to .env. Also registers custom markers.
    """
    env_test = PROJECT_ROOT / ".env.test"
    env_default = PROJECT_ROOT / ".env"

    if env_test.exists():
        load_dotenv(env_test)
    elif env_default.exists():
        load_dotenv(env_default)

    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests requiring external resources",
    )


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


# Database fixtures for integration tests
# These use SQLite in-memory database for fast, isolated tests


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine.

    Uses SQLite in-memory database for fast, isolated tests.
    Creates all tables before the test and drops them after.
    Each test gets a fresh database.
    """
    from sqlalchemy import create_engine

    from news_sentiment.database.models import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator:
    """Create a test database session.

    Uses the test engine to create a session that will be cleaned up
    after each test for isolation.
    """
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db() -> Generator:
    """Create SQLite in-memory database for integration tests.

    Creates a fresh in-memory database with all tables for each test.
    Tables are dropped after the test completes.

    Yields:
        SQLAlchemy Engine connected to in-memory SQLite database
    """
    from sqlalchemy import create_engine

    from news_sentiment.database.models import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_db) -> Generator:
    """Provide a database session with automatic rollback.

    Each test gets an isolated session. Any changes made during the test
    are automatically rolled back after the test completes.

    Args:
        test_db: The test database engine fixture

    Yields:
        SQLAlchemy Session for database operations
    """
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_gemini():
    """Mock Gemini API with successful response.

    Provides a mock that simulates successful Gemini API calls
    returning valid sentiment analysis responses.

    Returns:
        MagicMock configured to return successful sentiment responses
    """
    from unittest.mock import MagicMock

    mock = MagicMock()

    # Create a mock response with sentiment data
    mock_response = MagicMock()
    mock_response.text = '{"sentiment_score": 0.75, "confidence": 0.9, "reasoning": "Positive economic data"}'

    mock.generate_content.return_value = mock_response

    return mock


@pytest.fixture
def mock_gemini_partial_fail():
    """Mock Gemini API with mixed success/failure responses.

    Simulates a scenario where some API calls succeed and others fail,
    useful for testing error handling and retry logic.

    Returns:
        MagicMock that alternates between success and failure
    """
    from unittest.mock import MagicMock

    mock = MagicMock()

    # Track call count to alternate responses
    call_count = [0]  # Use list to allow mutation in nested function

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] % 3 == 0:  # Every 3rd call fails
            raise Exception("API rate limit exceeded")
        elif call_count[0] % 2 == 0:  # Every 2nd call returns error in response
            response = MagicMock()
            response.text = (
                '{"error": "Unable to process request", "sentiment_score": null}'
            )
            return response
        else:  # Other calls succeed
            response = MagicMock()
            response.text = '{"sentiment_score": 0.5, "confidence": 0.8, "reasoning": "Neutral outlook"}'
            return response

    mock.generate_content.side_effect = side_effect

    return mock


@pytest.fixture
def mock_scraper():
    """Mock ForexFactoryScraper for isolation in integration tests.

    Provides a mock scraper that returns predefined event data,
    allowing tests to run without actual web scraping.

    Returns:
        MagicMock configured with sample calendar events
    """
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    mock = MagicMock()

    # Sample events that would be scraped from ForexFactory
    sample_events = [
        {
            "timestamp": datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            "currency": "USD",
            "event_name": "Non-Farm Payrolls",
            "impact": "High",
            "actual": "200K",
            "forecast": "180K",
            "previous": "150K",
        },
        {
            "timestamp": datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "currency": "EUR",
            "event_name": "ECB Interest Rate Decision",
            "impact": "High",
            "actual": "4.50%",
            "forecast": "4.50%",
            "previous": "4.25%",
        },
        {
            "timestamp": datetime(2025, 1, 15, 8, 30, 0, tzinfo=timezone.utc),
            "currency": "GBP",
            "event_name": "GDP Growth Rate",
            "impact": "Medium",
            "actual": "0.2%",
            "forecast": "0.3%",
            "previous": "0.1%",
        },
    ]

    mock.scrape_calendar.return_value = sample_events

    return mock
