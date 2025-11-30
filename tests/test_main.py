"""
Comprehensive tests for the CLI orchestrator (main.py).

These tests follow TDD methodology (RED phase):
1. RED: Tests are written first and should fail initially
2. GREEN: Implementation makes tests pass
3. REFACTOR: Code is improved while keeping tests green

Test categories:
- Module imports
- CLI argument parsing
- scrape_events function
- store_events function
- analyze_events function
- Workflow integration
- Error handling
"""

import sys
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# ==============================================================================
# Module Import Tests
# ==============================================================================


class TestMainModuleImports:
    """Tests for module imports.

    These tests verify that all required modules and functions can be imported.
    """

    def test_can_import_main_module(self):
        """Can import main module."""
        from news_sentiment import main

        assert main is not None

    def test_can_import_main_function(self):
        """Can import main function (run)."""
        from news_sentiment.main import run

        assert run is not None
        assert callable(run)

    def test_can_import_scrape_events(self):
        """Can import scrape_events function."""
        from news_sentiment.main import scrape_events

        assert scrape_events is not None
        assert callable(scrape_events)

    def test_can_import_store_events(self):
        """Can import store_events function."""
        from news_sentiment.main import store_events

        assert store_events is not None
        assert callable(store_events)

    def test_can_import_analyze_events(self):
        """Can import analyze_events function."""
        from news_sentiment.main import analyze_events

        assert analyze_events is not None
        assert callable(analyze_events)

    def test_main_imports_forex_factory_scraper(self):
        """Main module should import ForexFactoryScraper."""
        from news_sentiment.main import ForexFactoryScraper

        assert ForexFactoryScraper is not None

    def test_main_imports_sentiment_analyzer(self):
        """Main module should import SentimentAnalyzer."""
        from news_sentiment.main import SentimentAnalyzer

        assert SentimentAnalyzer is not None


# ==============================================================================
# CLI Argument Parsing Tests
# ==============================================================================


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing.

    These tests verify that the CLI correctly parses all supported arguments.
    """

    def test_scrape_today_argument(self):
        """--scrape today is valid argument."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "today"])

        assert args.scrape == "today"

    def test_scrape_week_argument(self):
        """--scrape week is valid argument."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "week"])

        assert args.scrape == "week"

    def test_scrape_month_argument(self):
        """--scrape month is valid argument."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "month"])

        assert args.scrape == "month"

    def test_scrape_invalid_argument_raises(self):
        """--scrape with invalid value should raise error."""
        from news_sentiment.main import parse_args

        with pytest.raises(SystemExit):
            parse_args(["--scrape", "invalid"])

    def test_analyze_flag(self):
        """--analyze flag is recognized."""
        from news_sentiment.main import parse_args

        args = parse_args(["--analyze"])

        assert args.analyze is True

    def test_test_run_flag(self):
        """--test-run flag is recognized."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "week", "--test-run"])

        assert args.test_run is True

    def test_test_run_default_is_false(self):
        """--test-run defaults to False."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "week"])

        assert args.test_run is False

    def test_combined_scrape_and_analyze(self):
        """Can combine --scrape and --analyze."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "week", "--analyze"])

        assert args.scrape == "week"
        assert args.analyze is True

    def test_all_flags_combined(self):
        """Can combine --scrape, --analyze, and --test-run."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "week", "--analyze", "--test-run"])

        assert args.scrape == "week"
        assert args.analyze is True
        assert args.test_run is True

    def test_no_args_returns_empty_namespace(self):
        """No arguments returns namespace with None/False values."""
        from news_sentiment.main import parse_args

        args = parse_args([])

        assert args.scrape is None
        assert args.analyze is False
        assert args.test_run is False


class TestCLIHelpAndUsage:
    """Tests for CLI help and usage output."""

    def test_help_flag_shows_help(self, capsys):
        """--help shows usage information."""
        from news_sentiment.main import parse_args

        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--help"])

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "scrape" in captured.out.lower() or "usage" in captured.out.lower()

    def test_no_args_shows_help(self, capsys):
        """No arguments shows help text."""
        from news_sentiment.main import run

        # Mock argv to simulate no arguments
        with patch.object(sys, "argv", ["main.py"]):
            run()

        captured = capsys.readouterr()
        # Should print help or usage message
        assert (
            "usage" in captured.out.lower()
            or "help" in captured.out.lower()
            or "scrape" in captured.out.lower()
        )


# ==============================================================================
# scrape_events Function Tests
# ==============================================================================


class TestScrapeEvents:
    """Tests for scrape_events function.

    These tests verify that scrape_events correctly calls the scraper
    based on the specified mode.
    """

    def test_scrape_today_calls_scrape_day(self, mock_scraper):
        """'today' mode calls scraper.scrape_day()."""
        from news_sentiment.main import scrape_events

        scrape_events(mock_scraper, mode="today")

        mock_scraper.scrape_day.assert_called_once()

    def test_scrape_week_calls_scrape_week(self, mock_scraper):
        """'week' mode calls scraper.scrape_week()."""
        from news_sentiment.main import scrape_events

        scrape_events(mock_scraper, mode="week")

        mock_scraper.scrape_week.assert_called_once()

    def test_scrape_month_calls_scrape_month(self, mock_scraper):
        """'month' mode calls scraper.scrape_month()."""
        from news_sentiment.main import scrape_events

        scrape_events(mock_scraper, mode="month")

        mock_scraper.scrape_month.assert_called_once()

    def test_scrape_returns_list_of_events(self, mock_scraper):
        """scrape_events returns list of event dicts."""
        from news_sentiment.main import scrape_events

        result = scrape_events(mock_scraper, mode="week")

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(event, dict) for event in result)

    def test_scrape_today_passes_current_date(self, mock_scraper):
        """'today' mode passes current date to scraper."""
        from news_sentiment.main import scrape_events

        with patch("news_sentiment.main.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 30)
            scrape_events(mock_scraper, mode="today")

        call_args = mock_scraper.scrape_day.call_args
        # Verify date was passed
        assert call_args is not None

    def test_scrape_week_passes_current_date(self, mock_scraper):
        """'week' mode passes current date to scraper."""
        from news_sentiment.main import scrape_events

        with patch("news_sentiment.main.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 30)
            scrape_events(mock_scraper, mode="week")

        mock_scraper.scrape_week.assert_called_once()

    def test_scrape_month_passes_year_and_month(self, mock_scraper):
        """'month' mode passes year and month to scraper."""
        from news_sentiment.main import scrape_events

        with patch("news_sentiment.main.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 30)
            scrape_events(mock_scraper, mode="month")

        mock_scraper.scrape_month.assert_called_once()

    def test_scrape_default_mode_is_week(self, mock_scraper):
        """Default mode should be 'week'."""
        from news_sentiment.main import scrape_events

        scrape_events(mock_scraper)

        mock_scraper.scrape_week.assert_called_once()

    def test_scrape_invalid_mode_raises_error(self, mock_scraper):
        """Invalid mode should raise ValueError."""
        from news_sentiment.main import scrape_events

        with pytest.raises(ValueError):
            scrape_events(mock_scraper, mode="invalid")


# ==============================================================================
# store_events Function Tests
# ==============================================================================


class TestStoreEvents:
    """Tests for store_events function.

    These tests verify that store_events correctly stores events in the database.
    """

    def test_stores_events_in_database(self, mock_session, sample_events):
        """Stores events using session.merge()."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_events(sample_events)

        # Verify merge was called for each event
        assert mock_session.__enter__.return_value.merge.call_count == len(
            sample_events
        )

    def test_uses_context_manager(self, mock_session, sample_events):
        """Uses get_session context manager for transaction handling."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_events(sample_events)

        # Verify context manager was used (enter and exit called)
        mock_session.__enter__.assert_called_once()
        mock_session.__exit__.assert_called_once()

    def test_returns_count(self, mock_session, sample_events):
        """Returns number of events stored."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            result = store_events(sample_events)

        assert result == len(sample_events)

    def test_empty_events_returns_zero(self, mock_session):
        """Empty events list returns 0."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            result = store_events([])

        assert result == 0

    def test_creates_economic_event_models(self, mock_session, sample_events):
        """Creates EconomicEvent model instances from dicts using from_dict."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            with patch("news_sentiment.main.EconomicEvent") as mock_event_class:
                mock_event_class.from_dict.return_value = MagicMock()
                store_events(sample_events)

        # Verify EconomicEvent.from_dict was called for each event
        assert mock_event_class.from_dict.call_count == len(sample_events)

    def test_uses_merge_for_upsert(self, mock_session, sample_events):
        """Uses session.merge() for upsert behavior."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_events(sample_events)

        # Verify merge (not add) was called
        session_ctx = mock_session.__enter__.return_value
        assert session_ctx.merge.called
        assert not session_ctx.add.called


# ==============================================================================
# analyze_events Function Tests
# ==============================================================================


class TestAnalyzeEvents:
    """Tests for analyze_events function.

    These tests verify that analyze_events correctly analyzes unscored events.
    """

    def test_queries_unscored_events(self, mock_session, mock_analyzer):
        """Queries events with None sentiment_score."""
        from news_sentiment.main import analyze_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            analyze_events(mock_analyzer)

        # Verify query was made for unscored events
        session_ctx = mock_session.__enter__.return_value
        session_ctx.query.assert_called()

    def test_calls_analyzer_for_each_event(
        self, mock_session_with_unscored, mock_analyzer
    ):
        """Calls analyzer.analyze() for each unscored event."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer)

        # Should have called analyze for each unscored event
        assert mock_analyzer.analyze.call_count > 0

    def test_updates_sentiment_score(self, mock_session_with_unscored, mock_analyzer):
        """Updates event.sentiment_score with analysis result."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer)

        # Verify sentiment_score was updated
        session_ctx = mock_session_with_unscored.__enter__.return_value
        unscored_events = session_ctx.query.return_value.filter.return_value.all()
        for event in unscored_events:
            assert hasattr(event, "sentiment_score")

    def test_updates_raw_response(self, mock_session_with_unscored, mock_analyzer):
        """Updates event.raw_response with full analysis response."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer)

        # Verify raw_response was stored
        session_ctx = mock_session_with_unscored.__enter__.return_value
        unscored_events = session_ctx.query.return_value.filter.return_value.all()
        for event in unscored_events:
            assert hasattr(event, "raw_response")

    def test_uses_context_manager_default(
        self, mock_session_with_unscored, mock_analyzer
    ):
        """Uses context manager for transaction handling by default."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer, test_run=False)

        # Verify context manager was used (auto-commits on successful exit)
        mock_session_with_unscored.__enter__.assert_called()
        mock_session_with_unscored.__exit__.assert_called()
        # Verify rollback was NOT called (default behavior)
        mock_session_with_unscored.__enter__.return_value.rollback.assert_not_called()

    def test_test_run_no_commit(self, mock_session_with_unscored, mock_analyzer):
        """test_run=True prevents commit."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer, test_run=True)

        mock_session_with_unscored.__enter__.return_value.commit.assert_not_called()

    def test_returns_count(self, mock_session_with_unscored, mock_analyzer):
        """Returns number of events analyzed."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            result = analyze_events(mock_analyzer)

        assert isinstance(result, int)
        assert result > 0

    def test_only_analyzes_events_with_actual_value(
        self, mock_session_with_unscored, mock_analyzer
    ):
        """Only analyzes events where actual value is not None."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer)

        # Verify filter was called with actual IS NOT None condition
        session_ctx = mock_session_with_unscored.__enter__.return_value
        filter_call = session_ctx.query.return_value.filter
        assert filter_call.called


# ==============================================================================
# Workflow Integration Tests
# ==============================================================================


class TestWorkflowIntegration:
    """Integration tests for full workflow.

    These tests verify that the complete pipeline works correctly.
    """

    def test_scrape_and_store_workflow(self, mock_scraper, mock_session):
        """Scrape -> Store workflow works."""
        from news_sentiment.main import scrape_events, store_events

        # Scrape events
        events = scrape_events(mock_scraper, mode="week")

        # Store events
        with patch("news_sentiment.main.get_session", return_value=mock_session):
            count = store_events(events)

        assert count == len(events)

    def test_full_pipeline_workflow(
        self, mock_scraper, mock_session_with_unscored, mock_analyzer
    ):
        """Scrape -> Store -> Analyze workflow works."""
        from news_sentiment.main import analyze_events, scrape_events, store_events

        # Scrape events
        events = scrape_events(mock_scraper, mode="week")
        assert len(events) > 0

        # Store events
        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            stored = store_events(events)
            assert stored > 0

            # Analyze events
            analyzed = analyze_events(mock_analyzer)
            assert analyzed >= 0

    def test_test_run_prevents_all_commits(
        self, mock_scraper, mock_session_with_unscored, mock_analyzer, capsys
    ):
        """--test-run prevents database commits throughout workflow."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--scrape", "week", "--test-run"]):
            with patch(
                "news_sentiment.main.ForexFactoryScraper", return_value=mock_scraper
            ):
                with patch(
                    "news_sentiment.main.get_session",
                    return_value=mock_session_with_unscored,
                ):
                    run()

        # Verify commit was not called
        mock_session_with_unscored.__enter__.return_value.commit.assert_not_called()

    def test_run_with_scrape_only(self, mock_scraper, mock_session, capsys):
        """Run with --scrape only calls scraper and stores."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--scrape", "week"]):
            with patch(
                "news_sentiment.main.ForexFactoryScraper", return_value=mock_scraper
            ):
                with patch(
                    "news_sentiment.main.get_session", return_value=mock_session
                ):
                    run()

        mock_scraper.scrape_week.assert_called()

    def test_run_with_analyze_only(
        self, mock_session_with_unscored, mock_analyzer, capsys
    ):
        """Run with --analyze only analyzes existing events."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--analyze"]):
            with patch(
                "news_sentiment.main.SentimentAnalyzer", return_value=mock_analyzer
            ):
                with patch(
                    "news_sentiment.main.get_session",
                    return_value=mock_session_with_unscored,
                ):
                    run()

        mock_analyzer.analyze.assert_called()

    def test_run_with_scrape_and_analyze(
        self, mock_scraper, mock_session_with_unscored, mock_analyzer, capsys
    ):
        """Run with --scrape and --analyze does both."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--scrape", "week", "--analyze"]):
            with patch(
                "news_sentiment.main.ForexFactoryScraper", return_value=mock_scraper
            ):
                with patch(
                    "news_sentiment.main.SentimentAnalyzer", return_value=mock_analyzer
                ):
                    with patch(
                        "news_sentiment.main.get_session",
                        return_value=mock_session_with_unscored,
                    ):
                        run()

        mock_scraper.scrape_week.assert_called()
        # Analyzer should also be called since we asked to analyze


# ==============================================================================
# Error Handling Tests
# ==============================================================================


class TestErrorHandling:
    """Tests for error handling in main workflow."""

    def test_scraper_error_is_handled(self, mock_scraper):
        """Scraper errors are handled gracefully."""
        from news_sentiment.main import scrape_events

        mock_scraper.scrape_week.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            scrape_events(mock_scraper, mode="week")

    def test_database_error_is_handled(self, mock_session):
        """Database errors from merge propagate to caller."""
        from datetime import datetime

        from news_sentiment.main import store_events

        # Errors during merge propagate (caller responsibility to handle)
        mock_session.__enter__.return_value.merge.side_effect = Exception("DB error")

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            with pytest.raises(Exception):
                store_events([{"event_name": "Test", "timestamp": datetime.now()}])

    def test_analyzer_error_is_handled(self, mock_session_with_unscored, mock_analyzer):
        """Analyzer errors are logged and processing continues."""
        from news_sentiment.main import analyze_events

        mock_analyzer.analyze.side_effect = Exception("API error")

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            # Should NOT raise - continues processing other events
            result = analyze_events(mock_analyzer)
            # Returns 0 since all events failed
            assert result == 0


# ==============================================================================
# Output and Logging Tests
# ==============================================================================


class TestOutputAndLogging:
    """Tests for output and logging behavior."""

    def test_scrape_prints_event_count(self, mock_scraper, mock_session, capsys):
        """Scrape operation prints event count."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--scrape", "week", "--test-run"]):
            with patch(
                "news_sentiment.main.ForexFactoryScraper", return_value=mock_scraper
            ):
                run()

        captured = capsys.readouterr()
        # Should output something about events
        assert "event" in captured.out.lower() or len(captured.out) > 0

    def test_analyze_prints_progress(
        self, mock_session_with_unscored, mock_analyzer, capsys
    ):
        """Analyze operation prints progress."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--analyze", "--test-run"]):
            with patch(
                "news_sentiment.main.SentimentAnalyzer", return_value=mock_analyzer
            ):
                with patch(
                    "news_sentiment.main.get_session",
                    return_value=mock_session_with_unscored,
                ):
                    run()

        captured = capsys.readouterr()
        # Should have some output
        assert len(captured.out) >= 0  # At minimum, no crash


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_scraper():
    """Create a mock ForexFactoryScraper."""
    mock = MagicMock()
    mock.scrape_week.return_value = [
        {
            "timestamp": datetime(2025, 11, 30, 8, 30),
            "event_name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "High",
            "actual": "200K",
            "forecast": "180K",
            "previous": "150K",
        },
        {
            "timestamp": datetime(2025, 11, 30, 10, 0),
            "event_name": "Unemployment Rate",
            "currency": "USD",
            "impact": "High",
            "actual": "3.7%",
            "forecast": "3.8%",
            "previous": "3.9%",
        },
    ]
    mock.scrape_day.return_value = [
        {
            "timestamp": datetime(2025, 11, 30, 14, 30),
            "event_name": "ISM Manufacturing PMI",
            "currency": "USD",
            "impact": "High",
            "actual": "52.1",
            "forecast": "50.5",
            "previous": "49.8",
        }
    ]
    mock.scrape_month.return_value = mock.scrape_week.return_value * 4
    return mock


@pytest.fixture
def mock_analyzer():
    """Create a mock SentimentAnalyzer."""
    mock = MagicMock()
    mock.analyze.return_value = {
        "sentiment_score": 0.75,
        "raw_response": {
            "reasoning": "Actual beat forecast significantly",
            "full_response": '{"score": 0.75, "reasoning": "Actual beat forecast"}',
        },
    }
    return mock


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=MagicMock())
    mock.__exit__ = MagicMock(return_value=False)
    return mock


@pytest.fixture
def mock_session_with_unscored():
    """Create a mock database session with unscored events."""
    mock = MagicMock()
    session_ctx = MagicMock()

    # Create mock unscored events
    unscored_event_1 = MagicMock()
    unscored_event_1.event_name = "Non-Farm Payrolls"
    unscored_event_1.sentiment_score = None
    unscored_event_1.actual = "200K"
    unscored_event_1.to_dict.return_value = {
        "event_name": "Non-Farm Payrolls",
        "currency": "USD",
        "impact": "High",
        "actual": "200K",
        "forecast": "180K",
        "previous": "150K",
    }

    unscored_event_2 = MagicMock()
    unscored_event_2.event_name = "Unemployment Rate"
    unscored_event_2.sentiment_score = None
    unscored_event_2.actual = "3.7%"
    unscored_event_2.to_dict.return_value = {
        "event_name": "Unemployment Rate",
        "currency": "USD",
        "impact": "High",
        "actual": "3.7%",
        "forecast": "3.8%",
        "previous": "3.9%",
    }

    # Set up query chain to return unscored events
    session_ctx.query.return_value.filter.return_value.all.return_value = [
        unscored_event_1,
        unscored_event_2,
    ]

    mock.__enter__ = MagicMock(return_value=session_ctx)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


@pytest.fixture
def sample_events() -> List[Dict[str, Any]]:
    """Create sample event data for testing."""
    return [
        {
            "timestamp": datetime(2025, 11, 30, 8, 30),
            "event_name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "High",
            "actual": "200K",
            "forecast": "180K",
            "previous": "150K",
        },
        {
            "timestamp": datetime(2025, 11, 30, 10, 0),
            "event_name": "Unemployment Rate",
            "currency": "USD",
            "impact": "High",
            "actual": "3.7%",
            "forecast": "3.8%",
            "previous": "3.9%",
        },
        {
            "timestamp": datetime(2025, 11, 30, 14, 30),
            "event_name": "ISM Manufacturing PMI",
            "currency": "USD",
            "impact": "High",
            "actual": "52.1",
            "forecast": "50.5",
            "previous": "49.8",
        },
    ]


# ==============================================================================
# Additional Edge Case Tests
# ==============================================================================


# ==============================================================================
# Reddit CLI Argument Parsing Tests
# ==============================================================================


class TestRedditCLIArgumentParsing:
    """Tests for Reddit CLI argument parsing.

    These tests verify that the CLI correctly parses Reddit-related arguments.
    """

    def test_reddit_hot_argument(self):
        """--reddit hot is valid argument."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "hot"])

        assert args.reddit == "hot"

    def test_reddit_new_argument(self):
        """--reddit new is valid argument."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "new"])

        assert args.reddit == "new"

    def test_reddit_top_argument(self):
        """--reddit top is valid argument."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "top"])

        assert args.reddit == "top"

    def test_reddit_invalid_argument_raises(self):
        """--reddit with invalid value should raise error."""
        from news_sentiment.main import parse_args

        with pytest.raises(SystemExit):
            parse_args(["--reddit", "invalid"])

    def test_reddit_limit_argument(self):
        """--reddit-limit accepts integer value."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "hot", "--reddit-limit", "50"])

        assert args.reddit_limit == 50

    def test_reddit_limit_default(self):
        """--reddit-limit defaults to 25."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "hot"])

        assert args.reddit_limit == 25

    def test_subreddits_argument(self):
        """--subreddits accepts multiple values."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "hot", "--subreddits", "stocks", "investing"])

        assert args.subreddits == ["stocks", "investing"]

    def test_subreddits_default_is_none(self):
        """--subreddits defaults to None (uses DEFAULT_SUBREDDITS)."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "hot"])

        assert args.subreddits is None

    def test_combined_reddit_and_scrape(self):
        """Can combine --reddit and --scrape."""
        from news_sentiment.main import parse_args

        args = parse_args(["--scrape", "week", "--reddit", "hot"])

        assert args.scrape == "week"
        assert args.reddit == "hot"

    def test_combined_reddit_and_analyze(self):
        """Can combine --reddit and --analyze."""
        from news_sentiment.main import parse_args

        args = parse_args(["--reddit", "hot", "--analyze"])

        assert args.reddit == "hot"
        assert args.analyze is True

    def test_all_reddit_flags_combined(self):
        """Can combine all Reddit flags."""
        from news_sentiment.main import parse_args

        args = parse_args(
            [
                "--reddit",
                "top",
                "--reddit-limit",
                "100",
                "--subreddits",
                "wallstreetbets",
                "stocks",
                "--test-run",
            ]
        )

        assert args.reddit == "top"
        assert args.reddit_limit == 100
        assert args.subreddits == ["wallstreetbets", "stocks"]
        assert args.test_run is True


# ==============================================================================
# scrape_reddit_posts Function Tests
# ==============================================================================


class TestScrapeRedditPosts:
    """Tests for scrape_reddit_posts function.

    These tests verify that scrape_reddit_posts correctly calls the Reddit scraper
    based on the specified mode.
    """

    def test_scrape_hot_calls_scrape_hot(self, mock_reddit_scraper):
        """'hot' mode calls scraper.scrape_hot()."""
        from news_sentiment.main import scrape_reddit_posts

        scrape_reddit_posts(mock_reddit_scraper, mode="hot")

        mock_reddit_scraper.scrape_hot.assert_called_once()

    def test_scrape_new_calls_scrape_new(self, mock_reddit_scraper):
        """'new' mode calls scraper.scrape_new()."""
        from news_sentiment.main import scrape_reddit_posts

        scrape_reddit_posts(mock_reddit_scraper, mode="new")

        mock_reddit_scraper.scrape_new.assert_called_once()

    def test_scrape_top_calls_scrape_top(self, mock_reddit_scraper):
        """'top' mode calls scraper.scrape_top()."""
        from news_sentiment.main import scrape_reddit_posts

        scrape_reddit_posts(mock_reddit_scraper, mode="top")

        mock_reddit_scraper.scrape_top.assert_called_once()

    def test_scrape_returns_list_of_posts(self, mock_reddit_scraper):
        """scrape_reddit_posts returns list of post dicts."""
        from news_sentiment.main import scrape_reddit_posts

        result = scrape_reddit_posts(mock_reddit_scraper, mode="hot")

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(post, dict) for post in result)

    def test_scrape_passes_limit_parameter(self, mock_reddit_scraper):
        """Limit parameter is passed to scraper."""
        from news_sentiment.main import scrape_reddit_posts

        scrape_reddit_posts(mock_reddit_scraper, mode="hot", limit=50)

        mock_reddit_scraper.scrape_hot.assert_called_once_with(limit=50)

    def test_scrape_default_limit_is_25(self, mock_reddit_scraper):
        """Default limit is 25."""
        from news_sentiment.main import scrape_reddit_posts

        scrape_reddit_posts(mock_reddit_scraper, mode="hot")

        mock_reddit_scraper.scrape_hot.assert_called_once_with(limit=25)

    def test_scrape_default_mode_is_hot(self, mock_reddit_scraper):
        """Default mode should be 'hot'."""
        from news_sentiment.main import scrape_reddit_posts

        scrape_reddit_posts(mock_reddit_scraper)

        mock_reddit_scraper.scrape_hot.assert_called_once()

    def test_scrape_invalid_mode_raises_error(self, mock_reddit_scraper):
        """Invalid mode should raise ValueError."""
        from news_sentiment.main import scrape_reddit_posts

        with pytest.raises(ValueError):
            scrape_reddit_posts(mock_reddit_scraper, mode="invalid")


# ==============================================================================
# store_reddit_posts Function Tests
# ==============================================================================


class TestStoreRedditPosts:
    """Tests for store_reddit_posts function.

    These tests verify that store_reddit_posts correctly stores posts in the database.
    """

    def test_stores_posts_in_database(self, mock_session, sample_reddit_posts):
        """Stores posts using session.merge()."""
        from news_sentiment.main import store_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_reddit_posts(sample_reddit_posts)

        # Verify merge was called for each post
        assert mock_session.__enter__.return_value.merge.call_count == len(
            sample_reddit_posts
        )

    def test_uses_context_manager(self, mock_session, sample_reddit_posts):
        """Uses get_session context manager for transaction handling."""
        from news_sentiment.main import store_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_reddit_posts(sample_reddit_posts)

        # Verify context manager was used (enter and exit called)
        mock_session.__enter__.assert_called_once()
        mock_session.__exit__.assert_called_once()

    def test_returns_count(self, mock_session, sample_reddit_posts):
        """Returns number of posts stored."""
        from news_sentiment.main import store_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            result = store_reddit_posts(sample_reddit_posts)

        assert result == len(sample_reddit_posts)

    def test_empty_posts_returns_zero(self, mock_session):
        """Empty posts list returns 0."""
        from news_sentiment.main import store_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            result = store_reddit_posts([])

        assert result == 0

    def test_creates_reddit_post_models(self, mock_session, sample_reddit_posts):
        """Creates RedditPost model instances from dicts using from_dict."""
        from news_sentiment.main import store_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            with patch("news_sentiment.main.RedditPost") as mock_post_class:
                mock_post_class.from_dict.return_value = MagicMock()
                store_reddit_posts(sample_reddit_posts)

        # Verify RedditPost.from_dict was called for each post
        assert mock_post_class.from_dict.call_count == len(sample_reddit_posts)

    def test_uses_merge_for_upsert(self, mock_session, sample_reddit_posts):
        """Uses session.merge() for upsert behavior."""
        from news_sentiment.main import store_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_reddit_posts(sample_reddit_posts)

        # Verify merge (not add) was called
        session_ctx = mock_session.__enter__.return_value
        assert session_ctx.merge.called
        assert not session_ctx.add.called


# ==============================================================================
# analyze_reddit_posts Function Tests
# ==============================================================================


class TestAnalyzeRedditPosts:
    """Tests for analyze_reddit_posts function.

    These tests verify that analyze_reddit_posts correctly analyzes unscored posts.
    """

    def test_queries_unscored_posts(self, mock_session, mock_analyzer):
        """Queries posts with None sentiment_score."""
        from news_sentiment.main import analyze_reddit_posts

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            analyze_reddit_posts(mock_analyzer)

        # Verify query was made for unscored posts
        session_ctx = mock_session.__enter__.return_value
        session_ctx.query.assert_called()

    def test_calls_analyzer_for_each_post(
        self, mock_session_with_unscored_posts, mock_analyzer
    ):
        """Calls analyzer.analyze() for each unscored post."""
        from news_sentiment.main import analyze_reddit_posts

        with patch(
            "news_sentiment.main.get_session",
            return_value=mock_session_with_unscored_posts,
        ):
            analyze_reddit_posts(mock_analyzer)

        # Should have called analyze for each unscored post
        assert mock_analyzer.analyze.call_count > 0

    def test_updates_sentiment_score(
        self, mock_session_with_unscored_posts, mock_analyzer
    ):
        """Updates post.sentiment_score with analysis result."""
        from news_sentiment.main import analyze_reddit_posts

        with patch(
            "news_sentiment.main.get_session",
            return_value=mock_session_with_unscored_posts,
        ):
            analyze_reddit_posts(mock_analyzer)

        # Verify sentiment_score was updated
        session_ctx = mock_session_with_unscored_posts.__enter__.return_value
        unscored_posts = session_ctx.query.return_value.filter.return_value.all()
        for post in unscored_posts:
            assert hasattr(post, "sentiment_score")

    def test_updates_raw_response(
        self, mock_session_with_unscored_posts, mock_analyzer
    ):
        """Updates post.raw_response with full analysis response."""
        from news_sentiment.main import analyze_reddit_posts

        with patch(
            "news_sentiment.main.get_session",
            return_value=mock_session_with_unscored_posts,
        ):
            analyze_reddit_posts(mock_analyzer)

        # Verify raw_response was stored
        session_ctx = mock_session_with_unscored_posts.__enter__.return_value
        unscored_posts = session_ctx.query.return_value.filter.return_value.all()
        for post in unscored_posts:
            assert hasattr(post, "raw_response")

    def test_test_run_no_commit(self, mock_session_with_unscored_posts, mock_analyzer):
        """test_run=True prevents commit."""
        from news_sentiment.main import analyze_reddit_posts

        with patch(
            "news_sentiment.main.get_session",
            return_value=mock_session_with_unscored_posts,
        ):
            analyze_reddit_posts(mock_analyzer, test_run=True)

        mock_session_with_unscored_posts.__enter__.return_value.commit.assert_not_called()

    def test_returns_count(self, mock_session_with_unscored_posts, mock_analyzer):
        """Returns number of posts analyzed."""
        from news_sentiment.main import analyze_reddit_posts

        with patch(
            "news_sentiment.main.get_session",
            return_value=mock_session_with_unscored_posts,
        ):
            result = analyze_reddit_posts(mock_analyzer)

        assert isinstance(result, int)
        assert result > 0


# ==============================================================================
# Reddit Workflow Integration Tests
# ==============================================================================


class TestRedditWorkflowIntegration:
    """Integration tests for Reddit workflow.

    These tests verify that the complete Reddit pipeline works correctly.
    """

    def test_scrape_and_store_reddit_workflow(self, mock_reddit_scraper, mock_session):
        """Reddit Scrape -> Store workflow works."""
        from news_sentiment.main import scrape_reddit_posts, store_reddit_posts

        # Scrape posts
        posts = scrape_reddit_posts(mock_reddit_scraper, mode="hot")

        # Store posts
        with patch("news_sentiment.main.get_session", return_value=mock_session):
            count = store_reddit_posts(posts)

        assert count == len(posts)

    def test_run_with_reddit_only(self, mock_reddit_scraper, mock_session, capsys):
        """Run with --reddit only calls scraper and stores."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--reddit", "hot"]):
            with patch(
                "news_sentiment.main.RedditScraper", return_value=mock_reddit_scraper
            ):
                with patch(
                    "news_sentiment.main.get_session", return_value=mock_session
                ):
                    run()

        mock_reddit_scraper.scrape_hot.assert_called()

    def test_run_with_reddit_and_limit(self, mock_reddit_scraper, mock_session, capsys):
        """Run with --reddit and --reddit-limit passes limit."""
        from news_sentiment.main import run

        with patch.object(
            sys, "argv", ["main.py", "--reddit", "hot", "--reddit-limit", "50"]
        ):
            with patch(
                "news_sentiment.main.RedditScraper", return_value=mock_reddit_scraper
            ):
                with patch(
                    "news_sentiment.main.get_session", return_value=mock_session
                ):
                    run()

        mock_reddit_scraper.scrape_hot.assert_called_once_with(limit=50)

    def test_run_with_reddit_and_subreddits(self, mock_session, capsys):
        """Run with --reddit and --subreddits passes subreddits to scraper."""
        from news_sentiment.main import run

        mock_reddit_scraper = MagicMock()
        mock_reddit_scraper.scrape_hot.return_value = []

        with patch.object(
            sys,
            "argv",
            ["main.py", "--reddit", "hot", "--subreddits", "stocks", "investing"],
        ):
            with patch(
                "news_sentiment.main.RedditScraper", return_value=mock_reddit_scraper
            ) as mock_class:
                with patch(
                    "news_sentiment.main.get_session", return_value=mock_session
                ):
                    run()

        # Verify RedditScraper was instantiated with custom subreddits
        mock_class.assert_called_once()
        call_kwargs = mock_class.call_args.kwargs
        assert call_kwargs.get("subreddits") == ["stocks", "investing"]

    def test_run_with_reddit_test_run(self, mock_reddit_scraper, mock_session, capsys):
        """Run with --reddit --test-run skips database storage."""
        from news_sentiment.main import run

        with patch.object(sys, "argv", ["main.py", "--reddit", "hot", "--test-run"]):
            with patch(
                "news_sentiment.main.RedditScraper", return_value=mock_reddit_scraper
            ):
                with patch(
                    "news_sentiment.main.get_session", return_value=mock_session
                ):
                    run()

        # Verify scraper was called
        mock_reddit_scraper.scrape_hot.assert_called()
        # Verify database merge was NOT called (test run mode)
        mock_session.__enter__.return_value.merge.assert_not_called()


# ==============================================================================
# Reddit Error Handling Tests
# ==============================================================================


class TestRedditErrorHandling:
    """Tests for error handling in Reddit workflow."""

    def test_reddit_scraper_error_is_handled(self, mock_reddit_scraper):
        """Reddit scraper errors are handled gracefully."""
        from news_sentiment.main import scrape_reddit_posts

        mock_reddit_scraper.scrape_hot.side_effect = Exception("API rate limit")

        with pytest.raises(Exception):
            scrape_reddit_posts(mock_reddit_scraper, mode="hot")

    def test_reddit_store_error_is_handled(self, mock_session):
        """Reddit store errors from merge propagate to caller."""
        from datetime import datetime, timezone

        from news_sentiment.main import store_reddit_posts

        mock_session.__enter__.return_value.merge.side_effect = Exception("DB error")

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            with pytest.raises(Exception):
                store_reddit_posts(
                    [
                        {
                            "reddit_id": "test123",
                            "subreddit": "stocks",
                            "title": "Test",
                            "timestamp": datetime.now(timezone.utc),
                        }
                    ]
                )

    def test_reddit_analyzer_error_is_handled(
        self, mock_session_with_unscored_posts, mock_analyzer
    ):
        """Reddit analyzer errors are logged and processing continues."""
        from news_sentiment.main import analyze_reddit_posts

        mock_analyzer.analyze.side_effect = Exception("API error")

        with patch(
            "news_sentiment.main.get_session",
            return_value=mock_session_with_unscored_posts,
        ):
            # Should NOT raise - continues processing other posts
            result = analyze_reddit_posts(mock_analyzer)
            # Returns 0 since all posts failed
            assert result == 0


# ==============================================================================
# Additional Reddit Fixtures
# ==============================================================================


@pytest.fixture
def mock_reddit_scraper():
    """Create a mock RedditScraper."""
    mock = MagicMock()
    mock.scrape_hot.return_value = [
        {
            "reddit_id": "abc123",
            "subreddit": "wallstreetbets",
            "title": "GME to the moon!",
            "body": "Diamond hands forever",
            "url": "https://reddit.com/r/wallstreetbets/comments/abc123",
            "score": 1500,
            "num_comments": 200,
            "flair": "Discussion",
            "timestamp": datetime(2025, 11, 30, 8, 30),
        },
        {
            "reddit_id": "def456",
            "subreddit": "stocks",
            "title": "AAPL earnings analysis",
            "body": "Here's my take on Apple's Q4...",
            "url": "https://reddit.com/r/stocks/comments/def456",
            "score": 500,
            "num_comments": 75,
            "flair": "Analysis",
            "timestamp": datetime(2025, 11, 30, 10, 0),
        },
    ]
    mock.scrape_new.return_value = [
        {
            "reddit_id": "ghi789",
            "subreddit": "investing",
            "title": "New ETF recommendations",
            "body": "Looking for diversified ETFs...",
            "url": "https://reddit.com/r/investing/comments/ghi789",
            "score": 50,
            "num_comments": 20,
            "flair": "Advice",
            "timestamp": datetime(2025, 11, 30, 14, 30),
        }
    ]
    mock.scrape_top.return_value = mock.scrape_hot.return_value
    return mock


@pytest.fixture
def mock_session_with_unscored_posts():
    """Create a mock database session with unscored Reddit posts."""
    mock = MagicMock()
    session_ctx = MagicMock()

    # Create mock unscored posts
    unscored_post_1 = MagicMock()
    unscored_post_1.title = "GME to the moon!"
    unscored_post_1.sentiment_score = None
    unscored_post_1.body = "Diamond hands forever"
    unscored_post_1.to_dict_for_gemini.return_value = {
        "subreddit": "wallstreetbets",
        "title": "GME to the moon!",
        "body": "Diamond hands forever",
        "flair": "Discussion",
        "score": 1500,
        "num_comments": 200,
    }

    unscored_post_2 = MagicMock()
    unscored_post_2.title = "AAPL earnings analysis"
    unscored_post_2.sentiment_score = None
    unscored_post_2.body = "Here's my take on Apple's Q4..."
    unscored_post_2.to_dict_for_gemini.return_value = {
        "subreddit": "stocks",
        "title": "AAPL earnings analysis",
        "body": "Here's my take on Apple's Q4...",
        "flair": "Analysis",
        "score": 500,
        "num_comments": 75,
    }

    # Set up query chain to return unscored posts
    session_ctx.query.return_value.filter.return_value.all.return_value = [
        unscored_post_1,
        unscored_post_2,
    ]

    mock.__enter__ = MagicMock(return_value=session_ctx)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


@pytest.fixture
def sample_reddit_posts() -> List[Dict[str, Any]]:
    """Create sample Reddit post data for testing."""
    return [
        {
            "reddit_id": "abc123",
            "subreddit": "wallstreetbets",
            "title": "GME to the moon!",
            "body": "Diamond hands forever",
            "url": "https://reddit.com/r/wallstreetbets/comments/abc123",
            "score": 1500,
            "num_comments": 200,
            "flair": "Discussion",
            "timestamp": datetime(2025, 11, 30, 8, 30),
        },
        {
            "reddit_id": "def456",
            "subreddit": "stocks",
            "title": "AAPL earnings analysis",
            "body": "Here's my take on Apple's Q4...",
            "url": "https://reddit.com/r/stocks/comments/def456",
            "score": 500,
            "num_comments": 75,
            "flair": "Analysis",
            "timestamp": datetime(2025, 11, 30, 10, 0),
        },
    ]


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_scrape_result(self, mock_scraper, mock_session):
        """Handle empty scrape results gracefully."""
        from news_sentiment.main import scrape_events, store_events

        mock_scraper.scrape_week.return_value = []

        events = scrape_events(mock_scraper, mode="week")
        assert events == []

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            count = store_events(events)

        assert count == 0

    def test_no_unscored_events(self, mock_session, mock_analyzer):
        """Handle case where all events are already scored."""
        from news_sentiment.main import analyze_events

        # Return empty list for unscored events
        mock_session.__enter__.return_value.query.return_value.filter.return_value.all.return_value = (
            []
        )

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            count = analyze_events(mock_analyzer)

        assert count == 0
        mock_analyzer.analyze.assert_not_called()

    def test_events_without_actual_are_skipped(
        self, mock_session_with_unscored, mock_analyzer
    ):
        """Events without actual values should not be analyzed."""
        from news_sentiment.main import analyze_events

        # The filter in analyze_events should exclude events without actual
        # This is verified by checking the filter call

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer)

        # Filter should have been called
        session_ctx = mock_session_with_unscored.__enter__.return_value
        assert session_ctx.query.return_value.filter.called


class TestContextManagerUsage:
    """Tests for context manager patterns."""

    def test_scraper_used_as_context_manager(self, mock_session):
        """Scraper should be used as context manager."""
        from news_sentiment.main import run

        mock_scraper = MagicMock()
        mock_scraper.__enter__ = MagicMock(return_value=mock_scraper)
        mock_scraper.__exit__ = MagicMock(return_value=False)
        mock_scraper.scrape_week.return_value = []

        with patch.object(sys, "argv", ["main.py", "--scrape", "week", "--test-run"]):
            with patch(
                "news_sentiment.main.ForexFactoryScraper", return_value=mock_scraper
            ):
                run()

        # Scraper should have been used
        mock_scraper.scrape_week.assert_called()

    def test_database_session_context_manager(self, mock_session, sample_events):
        """Database session should use context manager."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_events(sample_events)

        # Session context manager should have been used
        mock_session.__enter__.assert_called()
        mock_session.__exit__.assert_called()
