"""
Database module for managing PostgreSQL connections and operations.

This module provides:
- Configuration management via Pydantic models
- Custom exception hierarchy for database errors
- Connection pooling and management (DatabaseManager)
- Query execution utilities (coming in future streams)
"""

# Configuration classes
from database.config import DatabaseConfig, AppConfig

# Exception classes
from database.exceptions import (
    DatabaseError,
    DatabaseConnectionError,
    QueryExecutionError,
    DataValidationError,
    PermissionError,
    TimeoutError,
)

# Connection management
from database.connection_manager import DatabaseManager

__all__ = [
    # Configuration
    "DatabaseConfig",
    "AppConfig",
    # Connection Management
    "DatabaseManager",
    # Exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "QueryExecutionError",
    "DataValidationError",
    "PermissionError",
    "TimeoutError",
]
