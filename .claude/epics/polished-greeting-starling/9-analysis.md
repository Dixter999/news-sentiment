---
issue: 9
title: Write Integration Tests
analyzed: 2025-11-30T12:58:24Z
estimated_hours: 6
parallelization_factor: 2.0
---

# Parallel Work Analysis: Issue #9

## Overview
Write comprehensive integration tests for the full pipeline: Scrape → Analyze → Store. Tests should cover database operations, error recovery, and end-to-end workflow validation. Currently, the project has 380 unit tests but lacks integration tests.

## Parallel Streams

### Stream A: Database Fixtures and Conftest Updates
**Scope**: Update conftest.py with working database fixtures for integration tests
**Files**:
- `tests/conftest.py` - Add test_db, test_session, mock_gemini fixtures
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 1.5
**Dependencies**: none

**Tasks**:
1. Implement `test_db` fixture with SQLite in-memory database
2. Implement `test_session` fixture with transaction rollback
3. Add `mock_gemini` fixture for API mocking
4. Add `mock_gemini_partial_fail` fixture for error testing
5. Add `mock_scraper` fixture for scraper integration tests
6. Register `@pytest.mark.integration` marker

### Stream B: Scraper-to-Database Integration Tests
**Scope**: Tests for scraper → database storage flow
**Files**:
- `tests/test_integration_scraper.py` - New file
**Agent Type**: python-backend-engineer
**Can Start**: immediately (fixtures can be mocked initially)
**Estimated Hours**: 2
**Dependencies**: none (coordinates with Stream A for fixtures)

**Tasks**:
1. Test scraped events stored correctly
2. Test duplicate events upserted (not duplicated)
3. Test empty scrape result handling
4. Test scraper error propagation
5. Test database transaction rollback on error

### Stream C: Analyzer-to-Database Integration Tests
**Scope**: Tests for analyzer → database update flow
**Files**:
- `tests/test_integration_analyzer.py` - New file
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 2
**Dependencies**: none (coordinates with Stream A for fixtures)

**Tasks**:
1. Test sentiment score stored after analysis
2. Test raw_response JSON stored correctly
3. Test only unscored events with actual values analyzed
4. Test partial failure continues processing
5. Test test_run mode rollback behavior

### Stream D: End-to-End Pipeline Tests
**Scope**: Full pipeline integration tests
**Files**:
- `tests/test_integration_e2e.py` - New file
**Agent Type**: python-backend-engineer
**Can Start**: after Streams B and C complete (uses similar patterns)
**Estimated Hours**: 1.5
**Dependencies**: Streams B, C (for fixture validation)

**Tasks**:
1. Test full pipeline: scrape → store → analyze
2. Test CLI orchestration with --test-run
3. Test multiple invocations don't duplicate data
4. Test recovery from partial failures
5. Test combined --scrape --analyze workflow

## Coordination Points

### Shared Files
- `tests/conftest.py` - Stream A owns this file
  - Streams B, C, D consume fixtures from it
  - Stream A should commit first so others can import
- No other shared files (each stream creates independent test files)

### Fixture Dependencies
All integration tests depend on fixtures from Stream A:
- `test_db` - SQLite in-memory database
- `test_session` - Database session with rollback
- `mock_gemini` - Mocked Gemini API responses
- `mock_scraper` - Mocked scraper for isolation

### Sequential Requirements
1. Stream A completes conftest.py fixtures first
2. Streams B and C can run in parallel after Stream A
3. Stream D runs after B and C to validate patterns

## Conflict Risk Assessment
- **Low Risk**: Each stream creates its own test file
- Stream A is the only one modifying conftest.py
- Clean separation by integration test category

## Parallelization Strategy

**Recommended Approach**: Hybrid

```
Stream A (Fixtures) ──────────────────┐
                                      ├── Stream D (E2E)
Stream B (Scraper Integration) ───────┤
                                      │
Stream C (Analyzer Integration) ──────┘
```

1. Launch Stream A first to establish fixtures
2. Once fixtures committed, launch Streams B & C in parallel
3. Stream D starts after B & C validate the fixture patterns
4. Alternatively: All streams can start together with temporary local fixtures, then refactor to use shared conftest.py

## Expected Timeline

With parallel execution:
- Wall time: 3.5 hours (A: 1.5h, then B+C parallel: 2h)
- Total work: 7 hours
- Efficiency gain: 50%

Without parallel execution:
- Wall time: 7 hours

## Pre-existing Code Status

Files that already exist:
- `tests/conftest.py` - Has placeholder fixtures (TODO comments)
- All other test files are unit tests, not integration

**Action**: Stream A updates conftest.py, other streams create new files.

## Notes

- Integration tests should be marked with `@pytest.mark.integration`
- Use SQLite in-memory for speed, not real PostgreSQL
- Mock external APIs (Gemini, Playwright web requests)
- The task specification mentions `test_db` fixture - implementation exists as placeholder
- Coverage requirement: >80% after integration tests added
- Consider running integration tests separately: `pytest -m integration`
