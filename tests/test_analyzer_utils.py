"""
Tests for analyzer utility modules: prompts.py and parsers.py.

Following TDD: These tests define the expected behavior of the prompt
building and response parsing utilities. They should FAIL (RED phase)
until the source code is implemented.

Stream B - Issue #4: Implement Gemini Sentiment Analyzer
"""

import pytest


class TestFormatValue:
    """Test the format_value function for prompt formatting."""

    def test_format_value_with_number(self):
        """Numeric values should be formatted as strings."""
        from news_sentiment.analyzer.prompts import format_value

        assert format_value(3.5) == "3.5"
        assert format_value(100) == "100"
        assert format_value(-2.5) == "-2.5"

    def test_format_value_with_string(self):
        """String values should be returned as-is."""
        from news_sentiment.analyzer.prompts import format_value

        assert format_value("2.5%") == "2.5%"
        assert format_value("$150B") == "$150B"

    def test_format_value_with_none(self):
        """None values should return 'N/A'."""
        from news_sentiment.analyzer.prompts import format_value

        assert format_value(None) == "N/A"

    def test_format_value_with_empty_string(self):
        """Empty strings should return 'N/A'."""
        from news_sentiment.analyzer.prompts import format_value

        assert format_value("") == "N/A"
        assert format_value("   ") == "N/A"

    def test_format_value_with_zero(self):
        """Zero should be formatted as '0', not treated as falsy."""
        from news_sentiment.analyzer.prompts import format_value

        assert format_value(0) == "0"
        assert format_value(0.0) == "0.0"


class TestBuildSentimentPrompt:
    """Test the build_sentiment_prompt function."""

    @pytest.fixture
    def sample_event(self):
        """Sample event data for testing."""
        return {
            "event_name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "High",
            "actual": 250,
            "forecast": 200,
            "previous": 180,
        }

    def test_build_prompt_includes_event_name(self, sample_event):
        """Prompt should include the event name."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        prompt = build_sentiment_prompt(sample_event)
        assert "Non-Farm Payrolls" in prompt

    def test_build_prompt_includes_currency(self, sample_event):
        """Prompt should include the currency."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        prompt = build_sentiment_prompt(sample_event)
        assert "USD" in prompt

    def test_build_prompt_includes_impact(self, sample_event):
        """Prompt should include the impact level."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        prompt = build_sentiment_prompt(sample_event)
        assert "High" in prompt

    def test_build_prompt_includes_values(self, sample_event):
        """Prompt should include actual, forecast, and previous values."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        prompt = build_sentiment_prompt(sample_event)
        assert "250" in prompt
        assert "200" in prompt
        assert "180" in prompt

    def test_build_prompt_handles_missing_values(self):
        """Prompt should handle None/missing values gracefully."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        event = {
            "event_name": "CPI",
            "currency": "EUR",
            "impact": "Medium",
            "actual": None,
            "forecast": 2.5,
            "previous": 2.3,
        }
        prompt = build_sentiment_prompt(event)
        assert "N/A" in prompt
        assert "CPI" in prompt
        assert "EUR" in prompt

    def test_build_prompt_requests_json_response(self, sample_event):
        """Prompt should request JSON formatted response."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        prompt = build_sentiment_prompt(sample_event)
        assert "JSON" in prompt or "json" in prompt.lower()
        assert "score" in prompt.lower()
        assert "reasoning" in prompt.lower()

    def test_build_prompt_returns_string(self, sample_event):
        """build_sentiment_prompt should return a string."""
        from news_sentiment.analyzer.prompts import build_sentiment_prompt

        prompt = build_sentiment_prompt(sample_event)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestValidateScore:
    """Test the validate_score function for clamping values."""

    def test_validate_score_within_range(self):
        """Scores within [-1.0, 1.0] should be unchanged."""
        from news_sentiment.analyzer.parsers import validate_score

        assert validate_score(0.5) == 0.5
        assert validate_score(-0.5) == -0.5
        assert validate_score(0.0) == 0.0
        assert validate_score(1.0) == 1.0
        assert validate_score(-1.0) == -1.0

    def test_validate_score_clamps_high(self):
        """Scores above 1.0 should be clamped to 1.0."""
        from news_sentiment.analyzer.parsers import validate_score

        assert validate_score(1.5) == 1.0
        assert validate_score(100.0) == 1.0

    def test_validate_score_clamps_low(self):
        """Scores below -1.0 should be clamped to -1.0."""
        from news_sentiment.analyzer.parsers import validate_score

        assert validate_score(-1.5) == -1.0
        assert validate_score(-100.0) == -1.0

    def test_validate_score_handles_integer(self):
        """Integer scores should be converted to float."""
        from news_sentiment.analyzer.parsers import validate_score

        result = validate_score(1)
        assert result == 1.0
        assert isinstance(result, float)


class TestExtractJsonFromText:
    """Test the extract_json_from_text function."""

    def test_extract_clean_json(self):
        """Clean JSON should be extracted as-is."""
        from news_sentiment.analyzer.parsers import extract_json_from_text

        text = '{"score": 0.5, "reasoning": "Good data"}'
        result = extract_json_from_text(text)
        assert result == '{"score": 0.5, "reasoning": "Good data"}'

    def test_extract_json_with_prefix_text(self):
        """JSON with leading text should be extracted."""
        from news_sentiment.analyzer.parsers import extract_json_from_text

        text = 'Here is my analysis:\n{"score": 0.5, "reasoning": "Good data"}'
        result = extract_json_from_text(text)
        assert result == '{"score": 0.5, "reasoning": "Good data"}'

    def test_extract_json_with_suffix_text(self):
        """JSON with trailing text should be extracted."""
        from news_sentiment.analyzer.parsers import extract_json_from_text

        text = '{"score": 0.5, "reasoning": "Good data"}\n\nHope this helps!'
        result = extract_json_from_text(text)
        assert result == '{"score": 0.5, "reasoning": "Good data"}'

    def test_extract_json_with_markdown_code_block(self):
        """JSON in markdown code blocks should be extracted."""
        from news_sentiment.analyzer.parsers import extract_json_from_text

        text = '''```json
{"score": 0.5, "reasoning": "Good data"}
```'''
        result = extract_json_from_text(text)
        assert result is not None
        assert '"score": 0.5' in result

    def test_extract_json_returns_none_for_no_json(self):
        """Return None if no valid JSON is found."""
        from news_sentiment.analyzer.parsers import extract_json_from_text

        text = "This is just plain text with no JSON at all."
        result = extract_json_from_text(text)
        assert result is None

    def test_extract_json_empty_string(self):
        """Empty string should return None."""
        from news_sentiment.analyzer.parsers import extract_json_from_text

        result = extract_json_from_text("")
        assert result is None


class TestParseGeminiResponse:
    """Test the main parse_gemini_response function."""

    def test_parse_valid_json_response(self):
        """Valid JSON response should be parsed correctly."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = '{"score": 0.75, "reasoning": "Strong employment data"}'
        result = parse_gemini_response(response)

        assert result["score"] == 0.75
        assert result["reasoning"] == "Strong employment data"
        assert "error" not in result

    def test_parse_json_with_extra_text(self):
        """JSON with extra text should still be parsed."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = '''Based on my analysis:
{"score": 0.5, "reasoning": "Mixed signals"}
This is my assessment.'''
        result = parse_gemini_response(response)

        assert result["score"] == 0.5
        assert result["reasoning"] == "Mixed signals"

    def test_parse_response_clamps_invalid_score(self):
        """Score outside valid range should be clamped."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = '{"score": 2.5, "reasoning": "Very bullish"}'
        result = parse_gemini_response(response)

        assert result["score"] == 1.0  # Clamped

    def test_parse_response_handles_missing_reasoning(self):
        """Missing reasoning should use empty string."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = '{"score": 0.3}'
        result = parse_gemini_response(response)

        assert result["score"] == 0.3
        assert result["reasoning"] == ""

    def test_parse_response_handles_missing_score(self):
        """Missing score should return error with default values."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = '{"reasoning": "No score provided"}'
        result = parse_gemini_response(response)

        assert result["score"] == 0.0
        assert "error" in result

    def test_parse_response_handles_invalid_json(self):
        """Invalid JSON should return error with default values."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = "This is not valid JSON at all"
        result = parse_gemini_response(response)

        assert result["score"] == 0.0
        assert result["reasoning"] == ""
        assert "error" in result

    def test_parse_response_handles_empty_string(self):
        """Empty response should return error."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        result = parse_gemini_response("")

        assert result["score"] == 0.0
        assert "error" in result

    def test_parse_response_handles_null_score(self):
        """Null score in JSON should be handled."""
        from news_sentiment.analyzer.parsers import parse_gemini_response

        response = '{"score": null, "reasoning": "Unable to determine"}'
        result = parse_gemini_response(response)

        assert result["score"] == 0.0
        assert "error" in result


class TestParseScoreFromText:
    """Test the fallback parse_score_from_text function."""

    def test_parse_score_from_explicit_statement(self):
        """Extract score from 'score is X' type statements."""
        from news_sentiment.analyzer.parsers import parse_score_from_text

        score, reasoning = parse_score_from_text(
            "The sentiment score is 0.6 because of strong data."
        )
        assert score == 0.6
        assert len(reasoning) > 0

    def test_parse_score_from_bullish_language(self):
        """Bullish language should extract positive score."""
        from news_sentiment.analyzer.parsers import parse_score_from_text

        score, reasoning = parse_score_from_text(
            "This is strongly bullish for the currency."
        )
        assert score > 0

    def test_parse_score_from_bearish_language(self):
        """Bearish language should extract negative score."""
        from news_sentiment.analyzer.parsers import parse_score_from_text

        score, reasoning = parse_score_from_text(
            "This is strongly bearish for the currency."
        )
        assert score < 0

    def test_parse_score_from_neutral_language(self):
        """Neutral language should extract score near zero."""
        from news_sentiment.analyzer.parsers import parse_score_from_text

        score, reasoning = parse_score_from_text("The impact is neutral, no change.")
        assert -0.3 <= score <= 0.3

    def test_parse_score_from_empty_text(self):
        """Empty text should return 0.0."""
        from news_sentiment.analyzer.parsers import parse_score_from_text

        score, reasoning = parse_score_from_text("")
        assert score == 0.0

    def test_parse_score_returns_tuple(self):
        """Function should return tuple of (score, reasoning)."""
        from news_sentiment.analyzer.parsers import parse_score_from_text

        result = parse_score_from_text("Some text")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], str)


class TestPromptTemplateStructure:
    """Test that the SENTIMENT_PROMPT_TEMPLATE is properly defined."""

    def test_template_exists(self):
        """SENTIMENT_PROMPT_TEMPLATE should be defined."""
        from news_sentiment.analyzer.prompts import SENTIMENT_PROMPT_TEMPLATE

        assert SENTIMENT_PROMPT_TEMPLATE is not None
        assert isinstance(SENTIMENT_PROMPT_TEMPLATE, str)

    def test_template_has_placeholders(self):
        """Template should have expected placeholders."""
        from news_sentiment.analyzer.prompts import SENTIMENT_PROMPT_TEMPLATE

        assert "{event_name}" in SENTIMENT_PROMPT_TEMPLATE
        assert "{currency}" in SENTIMENT_PROMPT_TEMPLATE
        assert "{impact}" in SENTIMENT_PROMPT_TEMPLATE
        assert "{actual}" in SENTIMENT_PROMPT_TEMPLATE
        assert "{forecast}" in SENTIMENT_PROMPT_TEMPLATE
        assert "{previous}" in SENTIMENT_PROMPT_TEMPLATE

    def test_template_requests_json_format(self):
        """Template should request JSON formatted response."""
        from news_sentiment.analyzer.prompts import SENTIMENT_PROMPT_TEMPLATE

        # Check for JSON format request
        template_lower = SENTIMENT_PROMPT_TEMPLATE.lower()
        assert "json" in template_lower
        assert "score" in template_lower
        assert "reasoning" in template_lower


class TestModuleExports:
    """Test that analyzer module exports the utility functions."""

    def test_prompts_importable_from_analyzer(self):
        """prompts module should be importable from analyzer."""
        from news_sentiment.analyzer import prompts

        assert hasattr(prompts, "SENTIMENT_PROMPT_TEMPLATE")
        assert hasattr(prompts, "build_sentiment_prompt")
        assert hasattr(prompts, "format_value")

    def test_parsers_importable_from_analyzer(self):
        """parsers module should be importable from analyzer."""
        from news_sentiment.analyzer import parsers

        assert hasattr(parsers, "parse_gemini_response")
        assert hasattr(parsers, "extract_json_from_text")
        assert hasattr(parsers, "validate_score")
        assert hasattr(parsers, "parse_score_from_text")
