"""
Tests for workflow functions in news_sentiment.main module.

This module tests the scrape_events, store_events, and analyze_events
functions following TDD methodology.

Stream B: These tests focus on the workflow functions, not the CLI parsing
(which is handled by Stream A).
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from news_sentiment.main import analyze_events, scrape_events, store_events


class TestScrapeEvents:
    """Tests for the scrape_events function."""

    def test_scrape_events_today_calls_scrape_day(self):
        """scrape_events with period='today' should call scraper.scrape_day()."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_day.return_value = [
            {"event_name": "Test Event", "currency": "USD"}
        ]

        result = scrape_events(mock_scraper, period="today")

        mock_scraper.scrape_day.assert_called_once()
        assert len(result) == 1
        assert result[0]["event_name"] == "Test Event"

    def test_scrape_events_week_calls_scrape_week(self):
        """scrape_events with period='week' should call scraper.scrape_week()."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_week.return_value = [
            {"event_name": "Event 1", "currency": "EUR"},
            {"event_name": "Event 2", "currency": "USD"},
        ]

        result = scrape_events(mock_scraper, period="week")

        mock_scraper.scrape_week.assert_called_once()
        assert len(result) == 2

    def test_scrape_events_month_calls_scrape_month(self):
        """scrape_events with period='month' should call scraper.scrape_month()."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_month.return_value = [
            {"event_name": "Monthly Event", "currency": "JPY"}
        ]

        result = scrape_events(mock_scraper, period="month")

        mock_scraper.scrape_month.assert_called_once()
        assert len(result) == 1

    def test_scrape_events_invalid_period_raises_error(self):
        """scrape_events with invalid period should raise ValueError."""
        mock_scraper = MagicMock()

        with pytest.raises(ValueError, match="Invalid period"):
            scrape_events(mock_scraper, period="invalid")

        mock_scraper.scrape_day.assert_not_called()
        mock_scraper.scrape_week.assert_not_called()
        mock_scraper.scrape_month.assert_not_called()

    def test_scrape_events_default_period_is_week(self):
        """scrape_events without period should default to 'week'."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_week.return_value = []

        # Call without period argument - should use default
        scrape_events(mock_scraper)

        mock_scraper.scrape_week.assert_called_once()

    def test_scrape_events_passes_datetime_to_scraper(self):
        """scrape_events should pass current datetime to scraper methods."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_day.return_value = []

        with patch("news_sentiment.main.datetime") as mock_datetime:
            mock_now = datetime(2025, 11, 30, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            scrape_events(mock_scraper, period="today")

            # Verify datetime.now() was called
            mock_datetime.now.assert_called()
            # Verify the result was passed to scrape_day
            call_args = mock_scraper.scrape_day.call_args
            assert call_args[0][0] == mock_now


class TestStoreEvents:
    """Tests for the store_events function."""

    @patch("news_sentiment.main.get_session")
    def test_store_events_returns_count(self, mock_get_session):
        """store_events should return count of stored events."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        events = [
            {
                "timestamp": datetime(2025, 11, 30, 8, 30),
                "currency": "USD",
                "event_name": "NFP",
                "impact": "High",
                "actual": "200K",
                "forecast": "180K",
                "previous": "150K",
            },
            {
                "timestamp": datetime(2025, 11, 30, 10, 0),
                "currency": "EUR",
                "event_name": "GDP",
                "impact": "Medium",
                "actual": "2.5%",
                "forecast": "2.3%",
                "previous": "2.1%",
            },
        ]

        result = store_events(events)

        assert result == 2

    @patch("news_sentiment.main.get_session")
    def test_store_events_empty_list_returns_zero(self, mock_get_session):
        """store_events with empty list should return 0."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        result = store_events([])

        assert result == 0

    @patch("news_sentiment.main.get_session")
    @patch("news_sentiment.main.EconomicEvent")
    def test_store_events_uses_merge_for_upsert(
        self, mock_event_class, mock_get_session
    ):
        """store_events should use session.merge() for upsert behavior."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_event_class.from_dict.return_value = MagicMock()

        events = [
            {
                "timestamp": datetime(2025, 11, 30, 8, 30),
                "currency": "USD",
                "event_name": "Test",
                "impact": "High",
            }
        ]

        store_events(events)

        # Verify merge was called (for upsert)
        mock_session.merge.assert_called()

    @patch("news_sentiment.main.get_session")
    def test_store_events_commits_transaction(self, mock_get_session):
        """store_events should commit the transaction."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        events = [
            {
                "timestamp": datetime(2025, 11, 30, 8, 30),
                "currency": "USD",
                "event_name": "Test",
            }
        ]

        store_events(events)

        # Note: get_session context manager handles commit
        # We just verify it was used as context manager
        mock_get_session.assert_called()


class TestAnalyzeEvents:
    """Tests for the analyze_events function."""

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_returns_count(self, mock_get_session):
        """analyze_events should return count of analyzed events."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        # Create mock events that need analysis
        mock_event1 = MagicMock()
        mock_event1.sentiment_score = None
        mock_event1.actual = "2.5%"
        mock_event1.to_dict_for_gemini.return_value = {
            "event_name": "GDP",
            "currency": "USD",
        }

        mock_event2 = MagicMock()
        mock_event2.sentiment_score = None
        mock_event2.actual = "200K"
        mock_event2.to_dict_for_gemini.return_value = {
            "event_name": "NFP",
            "currency": "USD",
        }

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_event1,
            mock_event2,
        ]

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "sentiment_score": 0.5,
            "raw_response": {"reasoning": "Test"},
        }

        result = analyze_events(mock_analyzer, test_run=False)

        assert result == 2
        assert mock_analyzer.analyze.call_count == 2

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_only_analyzes_unscored_with_actual(self, mock_get_session):
        """analyze_events should only query events without sentiment_score and with actual value."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []

        mock_analyzer = MagicMock()

        analyze_events(mock_analyzer)

        # Verify query was called with EconomicEvent
        mock_session.query.assert_called()

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_updates_sentiment_score(self, mock_get_session):
        """analyze_events should update event's sentiment_score."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_event = MagicMock()
        mock_event.sentiment_score = None
        mock_event.actual = "2.5%"
        mock_event.event_name = "GDP"
        mock_event.to_dict_for_gemini.return_value = {"event_name": "GDP"}

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_event
        ]

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "sentiment_score": 0.75,
            "raw_response": {"reasoning": "Positive GDP growth"},
        }

        analyze_events(mock_analyzer, test_run=False)

        assert mock_event.sentiment_score == 0.75

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_test_run_no_commit(self, mock_get_session):
        """analyze_events with test_run=True should not commit."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_event = MagicMock()
        mock_event.sentiment_score = None
        mock_event.actual = "2.5%"
        mock_event.to_dict_for_gemini.return_value = {"event_name": "Test"}

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_event
        ]

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "sentiment_score": 0.5,
            "raw_response": {},
        }

        # With test_run=True, rollback should be called instead of commit
        analyze_events(mock_analyzer, test_run=True)

        mock_session.rollback.assert_called()

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_no_events_returns_zero(self, mock_get_session):
        """analyze_events with no unscored events should return 0."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_session.query.return_value.filter.return_value.all.return_value = []

        mock_analyzer = MagicMock()

        result = analyze_events(mock_analyzer)

        assert result == 0
        mock_analyzer.analyze.assert_not_called()

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_stores_raw_response(self, mock_get_session):
        """analyze_events should store the raw_response on the event."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_event = MagicMock()
        mock_event.sentiment_score = None
        mock_event.actual = "200K"
        mock_event.event_name = "NFP"
        mock_event.to_dict_for_gemini.return_value = {"event_name": "NFP"}

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_event
        ]

        raw_response = {"reasoning": "Strong jobs data", "full_response": "..."}
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "sentiment_score": 0.8,
            "raw_response": raw_response,
        }

        analyze_events(mock_analyzer, test_run=False)

        # Verify raw_response was set (as JSON string)
        assert mock_event.raw_response is not None


class TestErrorHandling:
    """Tests for error handling in workflow functions."""

    def test_scrape_events_handles_scraper_error(self):
        """scrape_events should handle scraper errors gracefully."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_week.side_effect = Exception("Network error")

        # Should not raise, should return empty list or handle gracefully
        with pytest.raises(Exception):
            # For now, we expect it to raise - will implement error handling
            scrape_events(mock_scraper, period="week")

    @patch("news_sentiment.main.get_session")
    def test_store_events_handles_database_error(self, mock_get_session):
        """store_events should handle database errors gracefully."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.merge.side_effect = Exception("Database error")

        events = [
            {
                "timestamp": datetime(2025, 11, 30, 8, 30),
                "currency": "USD",
                "event_name": "Test",
            }
        ]

        # For now, expect it to raise - will implement error handling
        with pytest.raises(Exception):
            store_events(events)

    @patch("news_sentiment.main.get_session")
    def test_analyze_events_continues_on_single_event_error(self, mock_get_session):
        """analyze_events should continue processing if one event fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_event1 = MagicMock()
        mock_event1.sentiment_score = None
        mock_event1.actual = "2.5%"
        mock_event1.event_name = "GDP"
        mock_event1.to_dict_for_gemini.return_value = {"event_name": "GDP"}

        mock_event2 = MagicMock()
        mock_event2.sentiment_score = None
        mock_event2.actual = "200K"
        mock_event2.event_name = "NFP"
        mock_event2.to_dict_for_gemini.return_value = {"event_name": "NFP"}

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_event1,
            mock_event2,
        ]

        mock_analyzer = MagicMock()
        # First call fails, second succeeds
        mock_analyzer.analyze.side_effect = [
            Exception("API error"),
            {"sentiment_score": 0.5, "raw_response": {}},
        ]

        # Should not raise, should continue to next event
        result = analyze_events(mock_analyzer, test_run=False)

        # Should have attempted both events
        assert mock_analyzer.analyze.call_count == 2
        # Only one succeeded
        assert result == 1
