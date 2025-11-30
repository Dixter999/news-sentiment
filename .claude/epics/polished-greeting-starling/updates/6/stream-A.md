---
issue: 6
stream: Project Structure and Configuration
agent: python-backend-engineer
started: 2025-11-30T10:41:05Z
completed: 2025-11-30T11:45:00Z
status: completed
---

# Stream A: Project Structure and Configuration

## Scope
Directory structure, pyproject.toml, environment files

## Files Created/Modified

### Created
- `src/news_sentiment/__init__.py` - Main package with exports
- `src/news_sentiment/main.py` - CLI entry point stub with run, scrape_events, store_events, analyze_events
- `src/news_sentiment/scraper/__init__.py` - Scraper package
- `src/news_sentiment/scraper/ff_scraper.py` - ForexFactoryScraper stub with scrape_week, scrape_day
- `src/news_sentiment/analyzer/__init__.py` - Analyzer package
- `src/news_sentiment/analyzer/gemini.py` - SentimentAnalyzer stub with analyze, batch_analyze
- `src/news_sentiment/database/models.py` - EconomicEvent SQLAlchemy model
- `src/news_sentiment/database/connection.py` - Session management with get_session context manager
- `tests/test_project_structure.py` - Structure validation tests

### Modified
- `pyproject.toml` - Added asyncpg, pydantic, pydantic-settings, pytest-asyncio
- `.env.example` - Added GEMINI_API_KEY, removed hardcoded passwords
- `src/news_sentiment/database/__init__.py` - Fixed to use absolute imports
- `src/news_sentiment/database/connection_manager.py` - Fixed to use absolute imports
- `src/news_sentiment/database/utils.py` - Fixed to use absolute imports
- `tests/test_imports.py` - Removed xfail markers, fixed dependency tests

## Decisions Made

1. **Directory Structure**: Kept existing `src/news_sentiment/` structure rather than PRD's `src/`. This follows PEP 517 package layout and existing code already uses this structure.

2. **Import Paths**: Fixed all database module imports to use absolute paths (`news_sentiment.database.x`) instead of relative paths (`database.x`) for proper package resolution.

3. **Stubs**: All stubs include proper type hints, docstrings, and method signatures matching the PRD requirements. Methods return `pass` but have complete signatures.

4. **EconomicEvent Model**: Created full SQLAlchemy model with all fields from PRD including sentiment_score and raw_response for AI analysis results.

## TDD Cycle

### RED Phase
- Wrote 20 failing tests in `tests/test_project_structure.py`
- Tests verify package imports, class existence, and method signatures

### GREEN Phase
- Created all stub files with proper signatures
- All 20 tests pass

### REFACTOR Phase
- Applied black formatting
- Fixed ruff lint issues (removed unused imports)
- All tests still pass

## Test Results

```
40 passed, 2 skipped in 0.62s
```

- 40 tests passing for package structure, imports, and database module
- 2 tests skipped (playwright and google-generativeai not yet installed - Stream C responsibility)

## Commits

1. `3e3d41a` - Issue #6: Stream A - Project structure and configuration

## Next Steps

Stream C should:
1. Install dependencies with `pip install -e ".[dev]"`
2. Install Playwright browsers with `playwright install chromium`
3. Run validation to confirm all tests pass including dependency tests
