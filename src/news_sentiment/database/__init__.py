"""
Database module for managing PostgreSQL connections and operations.

This module provides:
- Configuration management via Pydantic models
- Custom exception hierarchy for database errors
- Connection pooling and management (DatabaseManager)
- SQLAlchemy models (EconomicEvent)
- Session management utilities (get_session)
"""

# Configuration classes
from news_sentiment.database.config import DatabaseConfig, AppConfig

# Exception classes
from news_sentiment.database.exceptions import (
    DatabaseError,
    DatabaseConnectionError,
    QueryExecutionError,
    DataValidationError,
    PermissionError,
    TimeoutError,
)

# Connection management
from news_sentiment.database.connection_manager import DatabaseManager

# Models
from news_sentiment.database.models import Base, EconomicEvent

# Session utilities
from news_sentiment.database.connection import get_session

__all__ = [
    # Configuration
    "DatabaseConfig",
    "AppConfig",
    # Connection Management
    "DatabaseManager",
    # Models
    "Base",
    "EconomicEvent",
    # Session utilities
    "get_session",
    # Exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "QueryExecutionError",
    "DataValidationError",
    "PermissionError",
    "TimeoutError",
]
