---
issue: 3
title: Database Schema and SQLAlchemy Models
analyzed: 2025-11-30T10:34:55Z
estimated_hours: 3
parallelization_factor: 2.0
---

# Parallel Work Analysis: Issue #3

## Overview
Create the database migration for `economic_events` table with `sentiment_score` and `raw_response` columns, implement SQLAlchemy models, and set up the database connection manager with pooling.

## Parallel Streams

### Stream A: Migration and Schema
**Scope**: SQL migration file and schema definition
**Files**:
- `migrations/001_create_events_table.sql`
**Agent Type**: postgresql-expert
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none

**Tasks**:
1. Create migration file with table definition
2. Add all columns (id, timestamp, currency, event_name, impact, actual, forecast, previous)
3. Add new columns (sentiment_score FLOAT, raw_response JSONB)
4. Create indexes (timestamp, currency, impact)
5. Add UNIQUE constraint (timestamp, event_name, currency)
6. Test migration runs idempotently

### Stream B: SQLAlchemy Models and Connection
**Scope**: Python models and database connection layer
**Files**:
- `src/database/models.py`
- `src/database/connection.py`
- `src/database/config.py`
- `src/database/__init__.py`
- `tests/test_database.py`
**Agent Type**: python-backend-engineer
**Can Start**: immediately (but needs migration to verify)
**Estimated Hours**: 2
**Dependencies**: Stream A (for testing against real schema)

**Tasks**:
1. Write failing tests first (TDD)
2. Implement EconomicEvent model with all columns
3. Add to_dict() method for Gemini analysis
4. Create config.py for database URL construction
5. Implement connection manager with pooling
6. Create get_session() context manager
7. Export models in __init__.py

## Coordination Points

### Shared Files
None - streams work on completely different file types:
- Stream A: SQL only
- Stream B: Python only

### Sequential Requirements
1. Migration should run before model tests (to verify schema)
2. However, model code can be written in parallel
3. Integration testing requires both complete

## Conflict Risk Assessment
- **Low Risk**: Streams work on different file types (SQL vs Python)
- No shared Python files between streams
- Clean separation of concerns

## Parallelization Strategy

**Recommended Approach**: Parallel with coordination

Launch both streams simultaneously:
- Stream A: Write and test migration SQL
- Stream B: Write models and connection code (mock tests initially)

Coordination point:
- After Stream A completes, Stream B runs integration tests against real DB

## Expected Timeline

With parallel execution:
- Wall time: 2 hours (limited by Stream B)
- Total work: 3 hours
- Efficiency gain: 33%

Without parallel execution:
- Wall time: 3 hours

## Notes

- The project already has some database code in `src/news_sentiment/database/` that may need to be refactored
- Migration should be idempotent (CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS)
- Connection pooling is critical for production performance
- Consider adding Alembic for future migrations if needed
- Existing migration file `migrations/001_create_eurusd_rates_tables.sql` may need review

## Pre-existing Code Check

Files that already exist and may need modification:
- `src/news_sentiment/database/__init__.py` - Exists
- `src/news_sentiment/database/config.py` - Exists
- `src/news_sentiment/database/connection_manager.py` - Exists (may need refactoring)
- `src/news_sentiment/database/exceptions.py` - Exists
- `migrations/001_create_eurusd_rates_tables.sql` - Different migration exists

**Action**: Review existing code before creating new files to avoid duplication.
