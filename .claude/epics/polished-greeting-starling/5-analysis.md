---
issue: 5
title: Implement Playwright Forex Factory Scraper
analyzed: 2025-11-30T11:41:30Z
estimated_hours: 8
parallelization_factor: 2.5
---

# Parallel Work Analysis: Issue #5

## Overview
Implement the `ForexFactoryScraper` class using Playwright to scrape the Forex Factory economic calendar. Extract all event fields: timestamp, currency, event_name, impact, actual, forecast, previous. Handle pagination and timezone conversion (ET → UTC).

## Parallel Streams

### Stream A: Core Scraper Implementation
**Scope**: Main scraper class with Playwright browser automation
**Files**:
- `src/news_sentiment/scraper/ff_scraper.py` - Main implementation
- `src/news_sentiment/scraper/__init__.py` - Exports
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 4
**Dependencies**: none

**Tasks**:
1. Implement browser initialization with Playwright
2. Implement `scrape_week()` method with URL construction
3. Implement `scrape_day()` method
4. Implement `_parse_calendar_table()` to extract event rows
5. Implement `_parse_impact()` for impact level detection
6. Implement `close()` for cleanup
7. Add rate limiting between page loads
8. Handle headless/headed mode configuration

### Stream B: Timezone and Parsing Utilities
**Scope**: Date/time parsing and timezone conversion
**Files**:
- `src/news_sentiment/scraper/utils.py` (new file)
- `src/news_sentiment/scraper/constants.py` (new file)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 2
**Dependencies**: none

**Tasks**:
1. Implement `convert_et_to_utc()` function
2. Implement `parse_ff_time()` for special values (Tentative, All Day)
3. Implement `parse_ff_date()` for date string parsing
4. Define CSS selectors as constants
5. Define URL patterns as constants
6. Handle DST transitions for ET timezone

### Stream C: Test Suite
**Scope**: Comprehensive test coverage for scraper
**Files**:
- `tests/test_scraper.py`
- `tests/fixtures/` (optional mock HTML fixtures)
**Agent Type**: python-backend-engineer
**Can Start**: immediately (TDD - tests first)
**Estimated Hours**: 2
**Dependencies**: none (tests drive implementation)

**Tasks**:
1. Write failing tests for `scrape_week()`
2. Write failing tests for timezone conversion
3. Write failing tests for impact parsing
4. Write failing tests for special time values
5. Write failing tests for missing values handling
6. Create mock HTML fixtures for offline testing

## Coordination Points

### Shared Files
- `src/news_sentiment/scraper/__init__.py` - Both Stream A and B add exports
  - Coordinate: Stream A exports main class, Stream B exports utilities

### Integration Points
- Stream A imports utilities from Stream B
- Stream C tests both Stream A and Stream B code
- Final integration: Stream A uses Stream B's parsing functions

### Sequential Requirements
1. Stream C (tests) should define expected behavior first (TDD)
2. Stream B (utilities) can be implemented independently
3. Stream A (core) integrates Stream B utilities

## Conflict Risk Assessment
- **Low Risk**: Each stream works on different files
- Stream A: `ff_scraper.py`
- Stream B: `utils.py`, `constants.py` (new files)
- Stream C: `test_scraper.py`
- Only `__init__.py` needs minor coordination (easy merge)

## Parallelization Strategy

**Recommended Approach**: Parallel with TDD coordination

```
Stream C (Tests) ─────────────────────────────┐
                                              ├── Integration
Stream B (Utilities) ─────────────────────────┤
                                              │
Stream A (Core Scraper) ──────────────────────┘
```

1. Launch all three streams simultaneously
2. Stream C writes failing tests first (TDD RED)
3. Stream B implements utilities
4. Stream A implements core scraper using Stream B utilities
5. All tests should pass at completion (GREEN)

## Expected Timeline

With parallel execution:
- Wall time: 4 hours (limited by Stream A)
- Total work: 8 hours
- Efficiency gain: 50%

Without parallel execution:
- Wall time: 8 hours

## Pre-existing Code Status

Files that already exist:
- `src/news_sentiment/scraper/__init__.py` - Has basic exports
- `src/news_sentiment/scraper/ff_scraper.py` - Has class stub with method signatures

**Action**: Build on existing stubs rather than creating new files.

## Notes

- Playwright requires browser binaries (installed in Task 001)
- Forex Factory may have anti-scraping measures - consider rate limiting
- Test fixtures with mock HTML recommended for reliable CI testing
- Timezone handling is critical - ET changes with DST
- Consider using `pytest-playwright` for browser testing
- The scraper should work with the EconomicEvent model from Task 002

## Validation Checklist

After completion, verify:
```bash
# 1. Tests pass
pytest tests/test_scraper.py -v

# 2. Can scrape current week
python -c "from news_sentiment.scraper import ForexFactoryScraper; s = ForexFactoryScraper(); print(s.scrape_week()[:2])"

# 3. Timezone conversion works
python -c "from news_sentiment.scraper.utils import convert_et_to_utc; print(convert_et_to_utc('Nov 25', '8:30am'))"

# 4. Linters pass
black --check src/news_sentiment/scraper/
ruff check src/news_sentiment/scraper/
```
