---
issue: 4
stream: Prompt Engineering and Response Parsing
agent: python-backend-engineer
started: 2025-11-30T12:02:06Z
completed: 2025-11-30T14:30:00Z
status: completed
---

# Stream B: Prompt Engineering and Response Parsing

## Scope
Prompt templates and response parsing utilities

## Files Created/Modified
- `src/news_sentiment/analyzer/prompts.py` (new file)
- `src/news_sentiment/analyzer/parsers.py` (new file)
- `src/news_sentiment/analyzer/__init__.py` (updated exports)
- `tests/test_analyzer_utils.py` (new test file)

## Tasks Completed
1. Design sentiment analysis prompt template
2. Create prompt builder with field substitution
3. Implement JSON response parser
4. Handle malformed JSON responses
5. Extract score and reasoning from response
6. Add fallback parsing for edge cases

## Implementation Details

### prompts.py
- `SENTIMENT_PROMPT_TEMPLATE`: Multi-line prompt requesting JSON response with score and reasoning
- `format_value(value)`: Formats values for prompt, returns 'N/A' for None/empty
- `build_sentiment_prompt(event)`: Builds prompt from event dictionary

### parsers.py
- `validate_score(score)`: Clamps score to [-1.0, 1.0] range
- `extract_json_from_text(text)`: Extracts JSON from LLM responses (handles extra text, markdown code blocks)
- `parse_score_from_text(text)`: Fallback parser using keyword detection (bullish/bearish/neutral)
- `parse_gemini_response(response_text)`: Main parser combining JSON and text-based extraction

### Edge Cases Handled
- JSON with extra text before/after
- JSON in markdown code blocks
- Missing fields in JSON
- Score outside valid range (clamped)
- Invalid JSON syntax (falls back to text parsing)
- Empty responses
- Non-numeric score values
- Null score values

## Test Coverage
41 tests created covering:
- TestFormatValue (5 tests)
- TestBuildSentimentPrompt (7 tests)
- TestValidateScore (4 tests)
- TestExtractJsonFromText (6 tests)
- TestParseGeminiResponse (8 tests)
- TestParseScoreFromText (6 tests)
- TestPromptTemplateStructure (3 tests)
- TestModuleExports (2 tests)

## Commits
1. `4ccae07` - Issue #4: Add failing tests for prompts.py and parsers.py (RED phase)
2. `fd2470f` - Issue #4: Implement prompts.py and parsers.py (GREEN phase)

## Status: COMPLETED
All 41 tests passing. Code formatted with black and linted with ruff.
