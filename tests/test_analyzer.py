"""
Tests for SentimentAnalyzer using Google Gemini API.

This module follows TDD principles - tests are written first to define
expected behavior before implementation.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


class TestSentimentAnalyzerInit:
    """Test cases for SentimentAnalyzer initialization."""

    def test_init_with_api_key_parameter(self):
        """Analyzer initializes with explicit API key."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            analyzer = SentimentAnalyzer(api_key="test-api-key")

            assert analyzer.api_key == "test-api-key"
            mock_genai.configure.assert_called_once_with(api_key="test-api-key")

    def test_init_with_env_var(self, clean_env):
        """Analyzer uses GEMINI_API_KEY environment variable if not provided."""
        from news_sentiment.analyzer import SentimentAnalyzer

        os.environ["GEMINI_API_KEY"] = "env-api-key"

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            analyzer = SentimentAnalyzer()

            assert analyzer.api_key == "env-api-key"
            mock_genai.configure.assert_called_once_with(api_key="env-api-key")

    def test_init_raises_without_api_key(self, clean_env):
        """Analyzer raises ValueError when no API key available."""
        from news_sentiment.analyzer import SentimentAnalyzer

        # Ensure no API key in environment
        os.environ.pop("GEMINI_API_KEY", None)

        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            SentimentAnalyzer()

    def test_init_with_custom_model(self):
        """Analyzer initializes with custom model name."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            analyzer = SentimentAnalyzer(
                api_key="test-key", model_name="gemini-1.5-pro"
            )

            assert analyzer.model_name == "gemini-1.5-pro"
            mock_genai.GenerativeModel.assert_called_once_with("gemini-1.5-pro")

    def test_init_default_model(self):
        """Analyzer uses gemini-pro as default model."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            analyzer = SentimentAnalyzer(api_key="test-key")

            assert analyzer.model_name == "gemini-pro"
            mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")

    def test_init_with_custom_max_retries(self):
        """Analyzer initializes with custom max_retries."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            analyzer = SentimentAnalyzer(api_key="test-key", max_retries=5)

            assert analyzer.max_retries == 5

    def test_init_default_max_retries(self):
        """Analyzer uses 3 as default max_retries."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            analyzer = SentimentAnalyzer(api_key="test-key")

            assert analyzer.max_retries == 3


class TestBuildPrompt:
    """Test cases for prompt building."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            return SentimentAnalyzer(api_key="test-key")

    @pytest.fixture
    def sample_event(self):
        """Sample economic event for testing."""
        return {
            "event_name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "High",
            "actual": "256K",
            "forecast": "200K",
            "previous": "180K",
        }

    def test_build_prompt_includes_event_name(self, analyzer, sample_event):
        """Prompt includes event name."""
        prompt = analyzer._build_prompt(sample_event)

        assert "Non-Farm Payrolls" in prompt

    def test_build_prompt_includes_currency(self, analyzer, sample_event):
        """Prompt includes currency."""
        prompt = analyzer._build_prompt(sample_event)

        assert "USD" in prompt

    def test_build_prompt_includes_impact(self, analyzer, sample_event):
        """Prompt includes impact level."""
        prompt = analyzer._build_prompt(sample_event)

        assert "High" in prompt

    def test_build_prompt_includes_actual(self, analyzer, sample_event):
        """Prompt includes actual value."""
        prompt = analyzer._build_prompt(sample_event)

        assert "256K" in prompt

    def test_build_prompt_includes_forecast(self, analyzer, sample_event):
        """Prompt includes forecast value."""
        prompt = analyzer._build_prompt(sample_event)

        assert "200K" in prompt

    def test_build_prompt_includes_previous(self, analyzer, sample_event):
        """Prompt includes previous value."""
        prompt = analyzer._build_prompt(sample_event)

        assert "180K" in prompt

    def test_build_prompt_requests_json_response(self, analyzer, sample_event):
        """Prompt requests JSON response format."""
        prompt = analyzer._build_prompt(sample_event)

        assert "JSON" in prompt or "json" in prompt.lower()
        assert "score" in prompt
        assert "reasoning" in prompt

    def test_build_prompt_specifies_score_range(self, analyzer, sample_event):
        """Prompt specifies -1.0 to 1.0 score range."""
        prompt = analyzer._build_prompt(sample_event)

        assert "-1.0" in prompt
        assert "1.0" in prompt

    def test_build_prompt_handles_missing_values(self, analyzer):
        """Prompt handles event with missing values."""
        event = {
            "event_name": "GDP",
            "currency": "EUR",
            "impact": "High",
            "actual": None,
            "forecast": "0.5%",
            "previous": "0.3%",
        }

        prompt = analyzer._build_prompt(event)

        # Should not raise and should include available data
        assert "GDP" in prompt
        assert "EUR" in prompt


class TestParseResponse:
    """Test cases for response parsing."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            return SentimentAnalyzer(api_key="test-key")

    def test_parse_valid_json_response(self, analyzer):
        """Parses valid JSON response correctly."""
        response_text = '{"score": 0.75, "reasoning": "Actual beat forecast"}'

        result = analyzer._parse_response(response_text)

        assert result["sentiment_score"] == 0.75
        assert result["raw_response"]["reasoning"] == "Actual beat forecast"
        assert result["raw_response"]["full_response"] == response_text

    def test_parse_response_with_negative_score(self, analyzer):
        """Parses negative score correctly."""
        response_text = '{"score": -0.5, "reasoning": "Missed forecast"}'

        result = analyzer._parse_response(response_text)

        assert result["sentiment_score"] == -0.5

    def test_parse_invalid_json_returns_zero(self, analyzer):
        """Returns 0.0 score for invalid JSON."""
        response_text = "This is not valid JSON"

        result = analyzer._parse_response(response_text)

        assert result["sentiment_score"] == 0.0
        assert "error" in result["raw_response"]

    def test_parse_response_with_extra_text(self, analyzer):
        """Handles response with extra text around JSON."""
        response_text = 'Here is the analysis:\n{"score": 0.5, "reasoning": "Beat"}\n'

        result = analyzer._parse_response(response_text)

        # Should extract JSON from response
        assert result["sentiment_score"] == 0.5

    def test_parse_response_missing_score_key(self, analyzer):
        """Returns 0.0 when score key is missing."""
        response_text = '{"reasoning": "Analysis without score"}'

        result = analyzer._parse_response(response_text)

        assert result["sentiment_score"] == 0.0

    def test_parse_response_non_numeric_score(self, analyzer):
        """Returns 0.0 when score is not numeric."""
        response_text = '{"score": "high", "reasoning": "Text score"}'

        result = analyzer._parse_response(response_text)

        assert result["sentiment_score"] == 0.0
        assert "error" in result["raw_response"]


class TestValidateScore:
    """Test cases for score validation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            return SentimentAnalyzer(api_key="test-key")

    def test_validate_score_in_range(self, analyzer):
        """Score in valid range passes through unchanged."""
        assert analyzer._validate_score(0.5) == 0.5
        assert analyzer._validate_score(-0.5) == -0.5
        assert analyzer._validate_score(0.0) == 0.0

    def test_validate_score_clamps_high(self, analyzer):
        """Score above 1.0 is clamped to 1.0."""
        assert analyzer._validate_score(1.5) == 1.0
        assert analyzer._validate_score(100.0) == 1.0

    def test_validate_score_clamps_low(self, analyzer):
        """Score below -1.0 is clamped to -1.0."""
        assert analyzer._validate_score(-1.5) == -1.0
        assert analyzer._validate_score(-100.0) == -1.0

    def test_validate_score_boundary_values(self, analyzer):
        """Boundary values are handled correctly."""
        assert analyzer._validate_score(1.0) == 1.0
        assert analyzer._validate_score(-1.0) == -1.0


class TestAnalyze:
    """Test cases for the main analyze method."""

    @pytest.fixture
    def sample_event(self):
        """Sample economic event for testing."""
        return {
            "event_name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "High",
            "actual": "256K",
            "forecast": "200K",
            "previous": "180K",
        }

    @pytest.fixture
    def mock_response(self):
        """Create mock Gemini response."""
        mock = MagicMock()
        mock.text = '{"score": 0.7, "reasoning": "Strong jobs data"}'
        return mock

    def test_analyze_returns_valid_score(self, sample_event, mock_response):
        """Analyzer returns score in [-1.0, 1.0] range."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(sample_event)

            assert "sentiment_score" in result
            assert -1.0 <= result["sentiment_score"] <= 1.0

    def test_analyze_returns_raw_response(self, sample_event, mock_response):
        """Analyzer returns raw_response with reasoning."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(sample_event)

            assert "raw_response" in result
            assert "reasoning" in result["raw_response"]

    def test_analyze_calls_gemini_api(self, sample_event, mock_response):
        """Analyzer calls Gemini API with prompt."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            analyzer.analyze(sample_event)

            mock_model.generate_content.assert_called_once()

    def test_positive_beat_returns_positive_score(self, mock_response):
        """When actual beats forecast, score is positive."""
        from news_sentiment.analyzer import SentimentAnalyzer

        event = {
            "event_name": "NFP",
            "currency": "USD",
            "impact": "High",
            "actual": "300K",
            "forecast": "200K",
            "previous": "180K",
        }
        mock_response.text = '{"score": 0.8, "reasoning": "Strong beat"}'

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(event)

            assert result["sentiment_score"] > 0

    def test_negative_miss_returns_negative_score(self, mock_response):
        """When actual misses forecast, score is negative."""
        from news_sentiment.analyzer import SentimentAnalyzer

        event = {
            "event_name": "NFP",
            "currency": "USD",
            "impact": "High",
            "actual": "100K",
            "forecast": "200K",
            "previous": "180K",
        }
        mock_response.text = '{"score": -0.6, "reasoning": "Weak jobs data"}'

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(event)

            assert result["sentiment_score"] < 0


class TestAnalyzeErrorHandling:
    """Test cases for error handling in analyze method."""

    @pytest.fixture
    def sample_event(self):
        """Sample economic event for testing."""
        return {
            "event_name": "GDP",
            "currency": "EUR",
            "impact": "High",
            "actual": "0.5%",
            "forecast": "0.3%",
            "previous": "0.2%",
        }

    def test_handles_api_error(self, sample_event):
        """API errors return 0.0 with error in raw_response."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API Error")
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(sample_event)

            assert result["sentiment_score"] == 0.0
            assert "error" in result["raw_response"]

    def test_handles_invalid_json_response(self, sample_event):
        """Invalid JSON response handled gracefully."""
        from news_sentiment.analyzer import SentimentAnalyzer

        mock_response = MagicMock()
        mock_response.text = "This is not JSON"

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(sample_event)

            assert result["sentiment_score"] == 0.0
            assert "error" in result["raw_response"]

    def test_handles_empty_response(self, sample_event):
        """Empty response handled gracefully."""
        from news_sentiment.analyzer import SentimentAnalyzer

        mock_response = MagicMock()
        mock_response.text = ""

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            result = analyzer.analyze(sample_event)

            assert result["sentiment_score"] == 0.0


class TestRetryWithBackoff:
    """Test cases for retry with exponential backoff."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            return SentimentAnalyzer(api_key="test-key", max_retries=3)

    def test_retry_on_rate_limit_error(self, analyzer):
        """Retries with backoff on rate limit error."""
        from google.api_core.exceptions import ResourceExhausted

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ResourceExhausted("Rate limit exceeded")
            return "Success"

        with patch("time.sleep"):  # Speed up test
            result = analyzer._retry_with_backoff(side_effect)

        assert result == "Success"
        assert call_count == 3

    def test_retry_respects_max_retries(self, analyzer):
        """Stops retrying after max_retries."""
        from google.api_core.exceptions import ResourceExhausted

        call_count = 0

        def always_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ResourceExhausted("Rate limit exceeded")

        with patch("time.sleep"):  # Speed up test
            with pytest.raises(ResourceExhausted):
                analyzer._retry_with_backoff(always_fail)

        assert call_count == 3  # max_retries

    def test_retry_uses_exponential_backoff(self, analyzer):
        """Backoff time increases exponentially."""
        from google.api_core.exceptions import ResourceExhausted

        sleep_times = []

        def track_sleep(seconds):
            sleep_times.append(seconds)

        call_count = 0

        def fail_twice(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ResourceExhausted("Rate limit")
            return "Success"

        with patch("time.sleep", side_effect=track_sleep):
            analyzer._retry_with_backoff(fail_twice)

        # Verify exponential backoff pattern
        assert len(sleep_times) == 2
        assert sleep_times[1] > sleep_times[0]

    def test_no_retry_on_non_rate_limit_error(self, analyzer):
        """Does not retry on non-rate-limit errors."""
        call_count = 0

        def fail_with_other_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ValueError("Some other error")

        with pytest.raises(ValueError):
            analyzer._retry_with_backoff(fail_with_other_error)

        assert call_count == 1  # No retries


class TestBatchAnalyze:
    """Test cases for batch analysis."""

    @pytest.fixture
    def sample_events(self):
        """Sample list of economic events."""
        return [
            {
                "event_name": "NFP",
                "currency": "USD",
                "impact": "High",
                "actual": "256K",
                "forecast": "200K",
                "previous": "180K",
            },
            {
                "event_name": "GDP",
                "currency": "EUR",
                "impact": "Medium",
                "actual": "0.5%",
                "forecast": "0.3%",
                "previous": "0.2%",
            },
        ]

    def test_batch_analyze_returns_list(self, sample_events):
        """batch_analyze returns list of results."""
        from news_sentiment.analyzer import SentimentAnalyzer

        mock_response = MagicMock()
        mock_response.text = '{"score": 0.5, "reasoning": "Test"}'

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            results = analyzer.batch_analyze(sample_events)

            assert isinstance(results, list)
            assert len(results) == 2

    def test_batch_analyze_each_result_has_score(self, sample_events):
        """Each result in batch has sentiment_score."""
        from news_sentiment.analyzer import SentimentAnalyzer

        mock_response = MagicMock()
        mock_response.text = '{"score": 0.5, "reasoning": "Test"}'

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            results = analyzer.batch_analyze(sample_events)

            for result in results:
                assert "sentiment_score" in result
                assert "raw_response" in result

    def test_batch_analyze_empty_list(self):
        """batch_analyze handles empty list."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai"):
            analyzer = SentimentAnalyzer(api_key="test-key")
            results = analyzer.batch_analyze([])

            assert results == []

    def test_batch_analyze_continues_on_single_failure(self, sample_events):
        """batch_analyze continues processing if one event fails."""
        from news_sentiment.analyzer import SentimentAnalyzer

        call_count = 0

        def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = MagicMock()
            if call_count == 1:
                raise Exception("API Error")
            mock_response.text = '{"score": 0.5, "reasoning": "Success"}'
            return mock_response

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = mock_generate
            mock_genai.GenerativeModel.return_value = mock_model

            analyzer = SentimentAnalyzer(api_key="test-key")
            results = analyzer.batch_analyze(sample_events)

            # First result should be error, second should succeed
            assert len(results) == 2
            assert results[0]["sentiment_score"] == 0.0  # Error case
            assert results[1]["sentiment_score"] == 0.5  # Success case
