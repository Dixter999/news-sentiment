---
issue: 4
title: Implement Gemini Sentiment Analyzer
analyzed: 2025-11-30T12:00:43Z
estimated_hours: 8
parallelization_factor: 2.0
---

# Parallel Work Analysis: Issue #4

## Overview
Implement the `SentimentAnalyzer` class using Google's Gemini API to score economic events. Design an effective prompt for sentiment scoring (-1.0 to 1.0). Handle rate limits, API errors, and parse/validate LLM responses.

## Parallel Streams

### Stream A: Core Analyzer Implementation
**Scope**: Main analyzer class with Gemini API integration
**Files**:
- `src/news_sentiment/analyzer/gemini.py` - Main implementation
- `src/news_sentiment/analyzer/__init__.py` - Exports
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 4
**Dependencies**: none

**Tasks**:
1. Configure Gemini API with google-generativeai
2. Implement `analyze()` method for single event analysis
3. Implement `batch_analyze()` for multiple events
4. Implement `_build_prompt()` for prompt construction
5. Implement `_parse_response()` for JSON parsing
6. Implement `_validate_score()` for score clamping
7. Add exponential backoff for rate limits
8. Handle API errors gracefully

### Stream B: Prompt Engineering and Response Parsing
**Scope**: Prompt templates and response parsing utilities
**Files**:
- `src/news_sentiment/analyzer/prompts.py` (new file)
- `src/news_sentiment/analyzer/parsers.py` (new file)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 2
**Dependencies**: none

**Tasks**:
1. Design sentiment analysis prompt template
2. Create prompt builder with field substitution
3. Implement JSON response parser
4. Handle malformed JSON responses
5. Extract score and reasoning from response
6. Add fallback parsing for edge cases

### Stream C: Test Suite
**Scope**: Comprehensive test coverage with mocked Gemini API
**Files**:
- `tests/test_analyzer.py`
- `tests/mocks/gemini_mock.py` (optional)
**Agent Type**: python-backend-engineer
**Can Start**: immediately (TDD - tests first)
**Estimated Hours**: 2
**Dependencies**: none (tests drive implementation)

**Tasks**:
1. Write failing tests for `analyze()`
2. Write failing tests for score validation
3. Write failing tests for API error handling
4. Write failing tests for rate limit retry
5. Write failing tests for JSON parsing
6. Create mock fixtures for Gemini responses

## Coordination Points

### Shared Files
- `src/news_sentiment/analyzer/__init__.py` - Both Stream A and B add exports
  - Coordinate: Stream A exports main class, Stream B exports utilities

### Integration Points
- Stream A imports prompts from Stream B
- Stream C tests both Stream A and Stream B code
- All streams work with `EconomicEvent.to_dict_for_gemini()` format

### Sequential Requirements
1. Stream C (tests) defines expected behavior first (TDD)
2. Stream B (prompts/parsers) can be implemented independently
3. Stream A (core) integrates Stream B utilities

## Conflict Risk Assessment
- **Low Risk**: Each stream works on different files
- Stream A: `gemini.py`
- Stream B: `prompts.py`, `parsers.py` (new files)
- Stream C: `test_analyzer.py`
- Only `__init__.py` needs minor coordination (easy merge)

## Parallelization Strategy

**Recommended Approach**: Parallel with TDD coordination

```
Stream C (Tests) ─────────────────────────────┐
                                              ├── Integration
Stream B (Prompts/Parsers) ───────────────────┤
                                              │
Stream A (Core Analyzer) ─────────────────────┘
```

1. Launch all three streams simultaneously
2. Stream C writes failing tests first (TDD RED)
3. Stream B implements prompt templates and parsers
4. Stream A implements core analyzer using Stream B utilities
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
- `src/news_sentiment/analyzer/__init__.py` - Has basic exports
- `src/news_sentiment/analyzer/gemini.py` - Has class stub with method signatures

**Action**: Build on existing stubs rather than creating new files.

## Notes

- Gemini API requires `GEMINI_API_KEY` environment variable
- Use `google-generativeai` package (already in pyproject.toml)
- Mock API calls in tests to avoid hitting real API
- Consider using `pytest-mock` or `unittest.mock`
- Prompt engineering is critical for quality scores
- JSON parsing should be robust (LLMs sometimes add extra text)
- Rate limit handling with exponential backoff is essential

## Validation Checklist

After completion, verify:
```bash
# 1. Tests pass (with mocked API)
pytest tests/test_analyzer.py -v

# 2. Analyzer initializes (needs API key)
python -c "import os; os.environ['GEMINI_API_KEY']='test'; from news_sentiment.analyzer import SentimentAnalyzer; print(SentimentAnalyzer())"

# 3. Score validation works
python -c "from news_sentiment.analyzer.gemini import SentimentAnalyzer; a = SentimentAnalyzer.__new__(SentimentAnalyzer); print(a._validate_score(1.5))"

# 4. Linters pass
black --check src/news_sentiment/analyzer/
ruff check src/news_sentiment/analyzer/
```
