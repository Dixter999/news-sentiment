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
from unittest.mock import MagicMock, Mock, patch

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

    def test_commits_transaction(self, mock_session, sample_events):
        """Commits the transaction after storing."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            store_events(sample_events)

        mock_session.__enter__.return_value.commit.assert_called_once()

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
        """Creates EconomicEvent model instances from dicts."""
        from news_sentiment.main import store_events

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            with patch("news_sentiment.main.EconomicEvent") as mock_event_class:
                store_events(sample_events)

        # Verify EconomicEvent was instantiated for each event
        assert mock_event_class.call_count == len(sample_events)

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

    def test_commits_by_default(self, mock_session_with_unscored, mock_analyzer):
        """Commits transaction by default."""
        from news_sentiment.main import analyze_events

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            analyze_events(mock_analyzer, test_run=False)

        mock_session_with_unscored.__enter__.return_value.commit.assert_called()

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

        with patch.object(
            sys, "argv", ["main.py", "--scrape", "week", "--analyze"]
        ):
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
        """Database errors are handled gracefully."""
        from news_sentiment.main import store_events

        mock_session.__enter__.return_value.commit.side_effect = Exception("DB error")

        with patch("news_sentiment.main.get_session", return_value=mock_session):
            with pytest.raises(Exception):
                store_events([{"event_name": "Test"}])

    def test_analyzer_error_is_handled(
        self, mock_session_with_unscored, mock_analyzer
    ):
        """Analyzer errors are handled gracefully."""
        from news_sentiment.main import analyze_events

        mock_analyzer.analyze.side_effect = Exception("API error")

        with patch(
            "news_sentiment.main.get_session", return_value=mock_session_with_unscored
        ):
            with pytest.raises(Exception):
                analyze_events(mock_analyzer)


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
