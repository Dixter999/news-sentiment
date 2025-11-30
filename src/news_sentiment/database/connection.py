"""
Database connection utilities.

This module provides session management and connection utilities
for the News Sentiment database.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Default connection pool configuration
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10


def get_database_url() -> str:
    """Get database URL from environment variables.

    Uses the AI Model database configuration for sentiment storage.

    Returns:
        PostgreSQL connection URL

    Raises:
        KeyError: If required environment variables are missing
    """
    host = os.environ.get("AI_MODEL_DB_HOST", "localhost")
    port = os.environ.get("AI_MODEL_DB_PORT", "5432")
    database = os.environ.get("AI_MODEL_DB_NAME", "ai_model")
    user = os.environ.get("AI_MODEL_DB_USER", "ai_model")
    password = os.environ.get("AI_MODEL_DB_PASSWORD", "")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def create_db_engine(database_url: str | None = None) -> Engine:
    """Create SQLAlchemy engine.

    Args:
        database_url: Optional database URL. If not provided,
                     constructs from environment variables.

    Returns:
        SQLAlchemy Engine instance
    """
    url = database_url or get_database_url()
    return create_engine(
        url,
        pool_size=DEFAULT_POOL_SIZE,
        max_overflow=DEFAULT_MAX_OVERFLOW,
        pool_pre_ping=True,
    )


# Module-level engine (lazy initialization)
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def _get_engine() -> Engine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_maker() -> sessionmaker:
    """Get or create the session maker.

    Returns:
        SQLAlchemy sessionmaker instance configured for the database

    Note:
        Uses lazy initialization - the session maker is created on first call
        and reused for subsequent calls.
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_get_engine(),
        )
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    Yields:
        SQLAlchemy Session instance

    Example:
        with get_session() as session:
            events = session.query(EconomicEvent).all()
    """
    session_maker = get_session_maker()
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
