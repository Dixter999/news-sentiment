---
issue: 7
stream: Workflow Functions
agent: python-backend-engineer
started: 2025-11-30T12:42:25Z
completed: 2025-11-30T13:15:00Z
status: completed
---

# Stream B: Workflow Functions (scrape/store/analyze)

## Scope
Individual workflow functions implementation

## Files Modified
- `src/news_sentiment/main.py` - Workflow functions section
- `tests/test_workflow_functions.py` - New test file with 19 tests

## Tasks Completed

### 1. Implemented `scrape_events()`
- Accepts `scraper` and `period` parameters
- Supports periods: "today", "week", "month"
- Defaults to "week" if no period specified
- Returns empty list for invalid periods
- Passes datetime.now() to scraper methods

### 2. Implemented `store_events()`
- Uses `EconomicEvent.from_dict()` to create model instances
- Uses `session.merge()` for upsert behavior
- Returns count of events stored
- Handles empty list (returns 0)
- Uses context manager from `get_session()`

### 3. Implemented `analyze_events()`
- Queries events with `sentiment_score IS NULL AND actual IS NOT NULL`
- Iterates through unscored events
- Calls `analyzer.analyze()` for each event
- Updates `sentiment_score` and `raw_response` fields
- Converts `raw_response` to JSON string for storage
- Supports `test_run=True` to rollback instead of commit
- Error handling: continues on single event failure
- Returns count of successfully analyzed events
- Logs warnings for failed analyses

### 4. Added Error Handling
- `scrape_events()`: Propagates scraper errors (caller handles)
- `store_events()`: Propagates database errors (caller handles)
- `analyze_events()`: Catches individual event failures, logs warning, continues

## Test Coverage
Created `tests/test_workflow_functions.py` with 19 tests:

### TestScrapeEvents (6 tests)
- test_scrape_events_today_calls_scrape_day
- test_scrape_events_week_calls_scrape_week
- test_scrape_events_month_calls_scrape_month
- test_scrape_events_invalid_period_returns_empty_list
- test_scrape_events_default_period_is_week
- test_scrape_events_passes_datetime_to_scraper

### TestStoreEvents (4 tests)
- test_store_events_returns_count
- test_store_events_empty_list_returns_zero
- test_store_events_uses_merge_for_upsert
- test_store_events_commits_transaction

### TestAnalyzeEvents (6 tests)
- test_analyze_events_returns_count
- test_analyze_events_only_analyzes_unscored_with_actual
- test_analyze_events_updates_sentiment_score
- test_analyze_events_test_run_no_commit
- test_analyze_events_no_events_returns_zero
- test_analyze_events_stores_raw_response

### TestErrorHandling (3 tests)
- test_scrape_events_handles_scraper_error
- test_store_events_handles_database_error
- test_analyze_events_continues_on_single_event_error

## TDD Process Followed
1. Wrote all 19 failing tests first (RED)
2. Implemented functions to make tests pass (GREEN)
3. Refactored for clean code (REFACTOR)
4. All 19 tests pass

## Linting Status
- `black`: Formatted
- `ruff`: Clean (no errors)

## Coordination Notes
- Stream A added `argparse` and `sys` imports for CLI implementation
- These imports are unused by workflow functions but needed by main()
- No merge conflicts expected - functions are independent

## Ready for Integration
Workflow functions are complete and ready to be called by Stream A's main() implementation.

## Coordination Issue Identified

**Parameter naming conflict:**
- Stream B (this work) implemented `scrape_events(scraper, period="week")`
- Stream A used `period` parameter (matching Stream B)
- Stream C tests use `mode` parameter (mismatch)

**Resolution needed:** Stream C's tests in `test_main.py` need to be updated:
1. Change `mode=` to `period=` in all `scrape_events()` calls
2. Add `parse_args` function or update tests to use `create_parser()`

**Files affected:**
- `tests/test_main.py` - Uses `mode` parameter (27 failing tests)
