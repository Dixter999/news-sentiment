"""
Tests for conftest.py fixtures.

TDD Phase: RED - These tests define expected fixture behavior.
They will FAIL until the fixtures are properly implemented.

Tests verify:
1. test_db fixture creates SQLite in-memory database with correct schema
2. test_session fixture provides session with auto-rollback
3. mock_gemini fixture provides mocked Gemini API
4. mock_gemini_partial_fail fixture handles mixed success/failure
5. mock_scraper fixture provides mocked ForexFactory scraper
6. integration marker is registered
"""

from datetime import datetime, timezone

import pytest


class TestDatabaseFixtures:
    """Test database-related fixtures."""

    @pytest.mark.integration
    def test_test_db_creates_in_memory_database(self, test_db):
        """test_db fixture should create SQLite in-memory engine."""
        # Verify it's an engine
        assert test_db is not None
        assert hasattr(test_db, "connect")
        # Verify it's SQLite
        assert "sqlite" in str(test_db.url)

    @pytest.mark.integration
    def test_test_db_creates_all_tables(self, test_db):
        """test_db fixture should create all tables from models."""
        from sqlalchemy import inspect

        inspector = inspect(test_db)
        tables = inspector.get_table_names()

        # EconomicEvent table should exist
        assert "economic_events" in tables

    @pytest.mark.integration
    def test_test_session_provides_session(self, test_session):
        """test_session fixture should provide a database session."""
        from sqlalchemy.orm import Session

        assert isinstance(test_session, Session)

    @pytest.mark.integration
    def test_test_session_allows_crud_operations(self, test_session):
        """test_session should allow CRUD operations."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        # Create
        event = EconomicEvent(
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            currency="USD",
            event_name="Test Event",
            impact="High",
        )
        test_session.add(event)
        test_session.flush()

        # Read
        result = test_session.query(EconomicEvent).filter_by(currency="USD").first()
        assert result is not None
        assert result.event_name == "Test Event"

    @pytest.mark.integration
    def test_test_session_is_isolated(self, test_session):
        """Each test should get a fresh, isolated session."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        # Previous test's data should not exist
        count = test_session.query(EconomicEvent).count()
        assert count == 0, "Session should be empty (isolated from other tests)"


class TestMockFixtures:
    """Test mock fixtures for external dependencies."""

    def test_mock_gemini_returns_mock(self, mock_gemini):
        """mock_gemini fixture should return a configured mock."""
        assert mock_gemini is not None
        # Should have a generate_content method
        assert hasattr(mock_gemini, "generate_content")

    def test_mock_gemini_has_successful_response(self, mock_gemini):
        """mock_gemini should return successful response by default."""
        response = mock_gemini.generate_content("test prompt")
        # Response should have text attribute
        assert hasattr(response, "text")
        # Text should contain sentiment-like JSON
        assert (
            "sentiment_score" in response.text or "sentiment" in response.text.lower()
        )

    def test_mock_gemini_partial_fail_exists(self, mock_gemini_partial_fail):
        """mock_gemini_partial_fail fixture should exist."""
        assert mock_gemini_partial_fail is not None

    def test_mock_gemini_partial_fail_returns_mixed_responses(
        self, mock_gemini_partial_fail
    ):
        """mock_gemini_partial_fail should return mix of success/failure."""
        # First call succeeds
        response1 = mock_gemini_partial_fail.generate_content("test 1")
        assert response1 is not None

        # At least one call should fail or return error
        has_failure = False
        for i in range(5):
            try:
                response = mock_gemini_partial_fail.generate_content(f"test {i}")
                if "error" in str(response.text).lower():
                    has_failure = True
                    break
            except Exception:
                has_failure = True
                break

        assert has_failure, "mock_gemini_partial_fail should simulate some failures"

    def test_mock_scraper_exists(self, mock_scraper):
        """mock_scraper fixture should provide a mock scraper."""
        assert mock_scraper is not None

    def test_mock_scraper_has_scrape_method(self, mock_scraper):
        """mock_scraper should have scrape method."""
        assert hasattr(mock_scraper, "scrape_calendar")
        # Should return list of events
        events = mock_scraper.scrape_calendar()
        assert isinstance(events, list)


class TestPytestMarkers:
    """Test that custom pytest markers are registered."""

    def test_integration_marker_is_registered(self, request):
        """integration marker should be registered in pytest_configure."""
        markers = list(request.config.getini("markers"))
        marker_names = [m.split(":")[0] for m in markers]
        assert "integration" in marker_names
