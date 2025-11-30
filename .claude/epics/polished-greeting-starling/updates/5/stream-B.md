---
issue: 5
stream: Timezone and Parsing Utilities
agent: python-backend-engineer
started: 2025-11-30T11:43:49Z
completed: 2025-11-30T12:15:00Z
status: completed
---

# Stream B: Timezone and Parsing Utilities

## Status: COMPLETED

## Summary

Implemented timezone conversion utilities and date/time parsing for the Forex Factory scraper following TDD methodology.

## Files Created

### Source Files

1. **`src/news_sentiment/scraper/constants.py`**
   - URL patterns: `BASE_URL`, `WEEK_URL_PATTERN`, `MONTH_URL_PATTERN`
   - CSS Selectors: `SELECTOR_ROW`, `SELECTOR_DATE`, `SELECTOR_TIME`, `SELECTOR_CURRENCY`, `SELECTOR_IMPACT`, `SELECTOR_EVENT`, `SELECTOR_ACTUAL`, `SELECTOR_FORECAST`, `SELECTOR_PREVIOUS`
   - Timezone constants: `ET_TIMEZONE`, `UTC_TIMEZONE`
   - Helper constants: `MONTH_ABBREVS`, `SPECIAL_TIME_VALUES`

2. **`src/news_sentiment/scraper/utils.py`**
   - `parse_ff_time(time_str)` - Parse FF time strings with special value handling
   - `parse_ff_date(date_str, year)` - Parse FF date strings to date objects
   - `convert_et_to_utc(date_str, time_str, year)` - Convert ET to UTC timezone
   - `build_week_url(target_date)` - Build week calendar URL
   - `build_month_url(year, month)` - Build month calendar URL

### Test Files

3. **`tests/test_scraper_utils.py`**
   - 45 tests total, all passing
   - Tests organized in classes:
     - `TestConstants` (4 tests)
     - `TestParseFfTime` (10 tests)
     - `TestParseFfDate` (7 tests)
     - `TestConvertEtToUtc` (10 tests)
     - `TestBuildWeekUrl` (5 tests)
     - `TestBuildMonthUrl` (3 tests)
     - `TestEdgeCases` (6 tests)

### Modified Files

4. **`src/news_sentiment/scraper/__init__.py`**
   - Added exports for all new constants and utility functions

## Tasks Completed

1. [x] Implement `convert_et_to_utc()` function
2. [x] Implement `parse_ff_time()` for special values (Tentative, All Day)
3. [x] Implement `parse_ff_date()` for date string parsing
4. [x] Define CSS selectors as constants
5. [x] Define URL patterns as constants
6. [x] Handle DST transitions for ET timezone

## Edge Cases Handled

1. **DST Transitions**
   - Spring forward (March): Correctly handles EST to EDT transition
   - Fall back (November): Uses first occurrence (EDT) for ambiguous times

2. **Date/Time Parsing**
   - Multiple date formats: "Mon Nov 25", "Nov 25", "Nov 25, 2025"
   - 12-hour time format with am/pm conversion
   - Special values: "Tentative", "All Day", empty strings

3. **Year Handling**
   - Year rollover (Dec 31 to Jan 1)
   - Day rollover when UTC pushes to next day
   - Default to current year when not specified
   - Leap year validation (Feb 29)

4. **Invalid Input Handling**
   - Invalid date strings raise `ValueError`
   - Invalid time formats return `("unknown", True)`

## TDD Commits

1. `Issue #5: test: add failing tests for scraper utilities (TDD RED)`
2. `Issue #5: feat: implement scraper constants and utilities (TDD GREEN)`
3. `Issue #5: refactor: apply black formatting (TDD REFACTOR)`

## Test Coverage

All functions have 100% test coverage with meaningful tests covering:
- Normal operation paths
- Edge cases (DST, year boundaries)
- Error conditions
- Input validation

## Dependencies

- Uses `zoneinfo` (stdlib) for timezone handling - no external pytz dependency
- All tests pass with Python 3.12
