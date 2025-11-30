---
issue: 7
title: Implement CLI Orchestrator
analyzed: 2025-11-30T12:40:54Z
estimated_hours: 4
parallelization_factor: 2.0
---

# Parallel Work Analysis: Issue #7

## Overview
Implement the main CLI entry point (`main.py`) that orchestrates the scrape → analyze → store workflow. Support command-line arguments for scraping period, analysis, and test-run mode.

## Parallel Streams

### Stream A: CLI Argument Parsing and Main Entry Point
**Scope**: argparse setup, main() function, and CLI interface
**Files**:
- `src/news_sentiment/main.py` - Main CLI implementation
- `src/news_sentiment/__init__.py` - Update exports if needed
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 2
**Dependencies**: none

**Tasks**:
1. Implement argparse with --scrape, --analyze, --test-run
2. Implement main() function with workflow orchestration
3. Add help text and usage examples
4. Handle no-arguments case (show help)
5. Support combining --scrape and --analyze
6. Add progress output with event counts

### Stream B: Workflow Functions (scrape/store/analyze)
**Scope**: Individual workflow functions implementation
**Files**:
- `src/news_sentiment/main.py` - Workflow functions (separate section)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 1.5
**Dependencies**: none (works on different functions in same file)

**Tasks**:
1. Implement `scrape_events()` - calls scraper based on period
2. Implement `store_events()` - stores events in database with upsert
3. Implement `analyze_events()` - analyzes unscored events with Gemini
4. Add error handling for API/DB failures
5. Support test-run mode (no commits)

### Stream C: Test Suite
**Scope**: Comprehensive tests for CLI and workflow
**Files**:
- `tests/test_main.py`
**Agent Type**: python-backend-engineer
**Can Start**: immediately (TDD - tests first)
**Estimated Hours**: 1.5
**Dependencies**: none

**Tasks**:
1. Write tests for argument parsing
2. Write tests for scrape workflow
3. Write tests for store workflow
4. Write tests for analyze workflow
5. Write tests for test-run mode
6. Write tests for combined operations
7. Mock scraper, analyzer, and database

## Coordination Points

### Shared Files
- `src/news_sentiment/main.py` - Both Stream A and B modify this file
  - **Coordination**: Stream A handles main() and argparse, Stream B handles workflow functions
  - Low conflict risk since functions are independent

### Integration Points
- All streams integrate through main.py
- Stream C tests both Stream A and B code
- Uses ForexFactoryScraper from completed Task 003
- Uses SentimentAnalyzer from completed Task 004
- Uses EconomicEvent model from completed Task 002

### Sequential Requirements
1. Stream C (tests) should define expected behavior first (TDD)
2. Streams A and B can work in parallel on different sections
3. Final integration when all complete

## Conflict Risk Assessment
- **Low Risk**: Streams work on different functions within main.py
- Stream A: main(), argparse setup
- Stream B: scrape_events(), store_events(), analyze_events()
- Stream C: tests in separate file
- Clean separation by function, easy to merge

## Parallelization Strategy

**Recommended Approach**: Parallel with function-level separation

```
Stream C (Tests) ─────────────────────────────┐
                                              ├── Integration
Stream A (CLI/main) ──────────────────────────┤
                                              │
Stream B (Workflow functions) ────────────────┘
```

1. Launch all three streams simultaneously
2. Stream C writes failing tests first (TDD RED)
3. Stream A implements CLI parsing and main()
4. Stream B implements workflow functions
5. All streams work on independent sections
6. Merge when complete

## Expected Timeline

With parallel execution:
- Wall time: 2 hours (limited by Stream A)
- Total work: 5 hours
- Efficiency gain: 60%

Without parallel execution:
- Wall time: 5 hours

## Pre-existing Code Status

Files that already exist:
- `src/news_sentiment/main.py` - Has stub with function signatures
- Imports for ForexFactoryScraper, SentimentAnalyzer already present

**Action**: Build on existing stubs, implement the `pass` methods.

## Dependencies (All Complete)

- ✅ Task 002 (Issue #3): Database models - COMPLETE
- ✅ Task 003 (Issue #5): Scraper - COMPLETE
- ✅ Task 004 (Issue #4): Analyzer - COMPLETE

## Notes

- This is the final orchestration task before integration tests
- Uses all previously implemented components
- CLI should be user-friendly with good help text
- Test-run mode is critical for development/testing
- Error handling should be graceful (log and continue where possible)
- Consider adding --verbose flag for detailed output

## Validation Checklist

After completion, verify:
```bash
# 1. Tests pass
pytest tests/test_main.py -v

# 2. CLI help works
python -m news_sentiment.main --help

# 3. Scrape test-run works
python -m news_sentiment.main --scrape week --test-run

# 4. Combined workflow test-run works
python -m news_sentiment.main --scrape week --analyze --test-run

# 5. Linters pass
black --check src/news_sentiment/main.py
ruff check src/news_sentiment/main.py
```
