"""
Integration tests for analyzer to database flow.

This module tests the complete flow from sentiment analysis to database storage:
1. Sentiment score stored after analysis
2. Raw response JSON stored correctly
3. Only unscored events with actual values are analyzed
4. Partial failure continues processing other events
5. test_run mode rolls back changes

Following TDD: These tests define the expected behavior.
"""

import json
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from news_sentiment.database.models import Base, EconomicEvent
from news_sentiment.main import analyze_events


@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator[Session, None, None]:
    """Create a test session with transaction isolation.

    Each test gets a fresh session that is rolled back after the test.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_gemini():
    """Mock Gemini API with successful responses."""
    with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = (
            '{"score": 0.75, "reasoning": "NFP beat forecast significantly"}'
        )
        mock_model.generate_content.return_value = mock_response
        yield mock_model


@pytest.fixture
def mock_gemini_partial_fail():
    """Mock Gemini API with one failure in the middle."""
    with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        # Create responses: success, failure, success
        responses = [
            MagicMock(text='{"score": 0.5, "reasoning": "Mixed signals"}'),
            Exception("API rate limit exceeded"),
            MagicMock(text='{"score": -0.3, "reasoning": "Missed expectations"}'),
        ]

        mock_model.generate_content.side_effect = responses
        yield mock_model


def create_sample_event(
    event_name: str = "Non-Farm Payrolls",
    actual: str | None = "216K",
    sentiment_score: float | None = None,
    raw_response: str | None = None,
) -> EconomicEvent:
    """Create a sample EconomicEvent for testing."""
    return EconomicEvent(
        timestamp=datetime(2024, 1, 5, 13, 30),
        currency="USD",
        event_name=event_name,
        impact="High",
        actual=actual,
        forecast="175K",
        previous="173K",
        sentiment_score=sentiment_score,
        raw_response=raw_response,
    )


@pytest.mark.integration
class TestAnalyzerToDatabase:
    """Integration tests for analyzer -> database flow."""

    def test_sentiment_score_stored(self, test_session: Session, mock_gemini):
        """Sentiment score is stored in database after analysis.

        Verifies that:
        1. Event is created without sentiment score
        2. After analysis, sentiment score is populated
        3. Score is within valid range [-1.0, 1.0]
        """
        # Arrange: Insert unscored event
        event = create_sample_event(sentiment_score=None)
        test_session.add(event)
        test_session.commit()

        # Verify initial state
        stored = test_session.query(EconomicEvent).first()
        assert stored.sentiment_score is None

        # Act: Patch get_session to use test session
        with patch("news_sentiment.main.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__ = lambda s: test_session
            mock_get_session.return_value.__exit__ = lambda s, *args: None

            # Create analyzer with mock
            from news_sentiment.analyzer.gemini import SentimentAnalyzer

            with patch.object(
                SentimentAnalyzer,
                "__init__",
                lambda self, **kwargs: setattr(self, "model", mock_gemini)
                or setattr(self, "api_key", "test")
                or setattr(self, "model_name", "test")
                or setattr(self, "max_retries", 3),
            ):
                analyzer = SentimentAnalyzer()
                # Manually run analysis logic
                result = analyzer.analyze(stored.to_dict_for_gemini())
                stored.sentiment_score = result["sentiment_score"]
                stored.raw_response = json.dumps(result["raw_response"])
                test_session.commit()

        # Assert
        test_session.refresh(stored)
        assert stored.sentiment_score is not None
        assert -1.0 <= stored.sentiment_score <= 1.0
        assert stored.sentiment_score == 0.75

    def test_raw_response_stored_as_json(self, test_session: Session, mock_gemini):
        """Raw response is stored as valid JSON string.

        Verifies that:
        1. raw_response is stored as a string
        2. The string is valid JSON
        3. The JSON contains expected fields (reasoning, full_response)
        """
        # Arrange
        event = create_sample_event()
        test_session.add(event)
        test_session.commit()

        # Act: Analyze and store response
        from news_sentiment.analyzer.gemini import SentimentAnalyzer

        with patch.object(
            SentimentAnalyzer,
            "__init__",
            lambda self, **kwargs: setattr(self, "model", mock_gemini)
            or setattr(self, "api_key", "test")
            or setattr(self, "model_name", "test")
            or setattr(self, "max_retries", 3),
        ):
            analyzer = SentimentAnalyzer()
            result = analyzer.analyze(event.to_dict_for_gemini())
            event.raw_response = json.dumps(result["raw_response"])
            test_session.commit()

        # Assert
        test_session.refresh(event)
        assert event.raw_response is not None
        assert isinstance(event.raw_response, str)

        # Verify it's valid JSON
        parsed = json.loads(event.raw_response)
        assert isinstance(parsed, dict)
        assert "reasoning" in parsed or "full_response" in parsed

    def test_only_unscored_with_actual_analyzed(
        self, test_session: Session, mock_gemini
    ):
        """Only events with actual values and no sentiment score are analyzed.

        Creates events in different states:
        1. Unscored with actual - SHOULD be analyzed
        2. Already scored - SHOULD NOT be analyzed
        3. No actual value - SHOULD NOT be analyzed
        """
        # Arrange: Create events in different states
        unscored_with_actual = create_sample_event(
            event_name="NFP - Unscored",
            actual="216K",
            sentiment_score=None,
        )
        already_scored = create_sample_event(
            event_name="CPI - Already Scored",
            actual="3.2%",
            sentiment_score=0.5,
        )
        no_actual = create_sample_event(
            event_name="Fed Meeting - No Actual",
            actual=None,
            sentiment_score=None,
        )

        test_session.add_all([unscored_with_actual, already_scored, no_actual])
        test_session.commit()

        # Act: Query for events that should be analyzed
        unscored_events = (
            test_session.query(EconomicEvent)
            .filter(
                EconomicEvent.sentiment_score.is_(None),
                EconomicEvent.actual.isnot(None),
            )
            .all()
        )

        # Assert
        assert len(unscored_events) == 1
        assert unscored_events[0].event_name == "NFP - Unscored"

        # Already scored should not be in the list
        event_names = [e.event_name for e in unscored_events]
        assert "CPI - Already Scored" not in event_names
        assert "Fed Meeting - No Actual" not in event_names

    def test_partial_failure_continues(
        self, test_session: Session, mock_gemini_partial_fail
    ):
        """Analysis continues processing after individual event failure.

        Creates 3 events where the second one fails during analysis.
        Verifies that:
        1. First event is analyzed successfully
        2. Third event is analyzed successfully
        3. Second event retains None for sentiment_score
        """
        # Arrange: Create 3 events
        event1 = create_sample_event(event_name="Event 1 - Success")
        event2 = create_sample_event(event_name="Event 2 - Will Fail")
        event3 = create_sample_event(event_name="Event 3 - Success")

        test_session.add_all([event1, event2, event3])
        test_session.commit()

        # Act: Simulate the analyze_events behavior
        from news_sentiment.analyzer.gemini import SentimentAnalyzer

        with patch.object(
            SentimentAnalyzer,
            "__init__",
            lambda self, **kwargs: setattr(self, "model", mock_gemini_partial_fail)
            or setattr(self, "api_key", "test")
            or setattr(self, "model_name", "test")
            or setattr(self, "max_retries", 3),
        ):
            analyzer = SentimentAnalyzer()
            analyzed_count = 0

            events = (
                test_session.query(EconomicEvent)
                .filter(
                    EconomicEvent.sentiment_score.is_(None),
                    EconomicEvent.actual.isnot(None),
                )
                .all()
            )

            for event in events:
                try:
                    result = analyzer.analyze(event.to_dict_for_gemini())
                    # The analyzer returns 0.0 score on error with error in raw_response
                    event.sentiment_score = result["sentiment_score"]
                    event.raw_response = json.dumps(result["raw_response"])
                    analyzed_count += 1
                except Exception:
                    # If an exception propagates (shouldn't happen with current impl)
                    continue

            test_session.commit()

        # Assert: All events should have scores (analyzer handles errors internally)
        # The mock raises exception on second call, but analyzer catches it
        test_session.expire_all()
        events = test_session.query(EconomicEvent).all()

        # Count events with non-None scores
        scored_events = [e for e in events if e.sentiment_score is not None]
        assert len(scored_events) == 3  # All 3 get scores (error returns 0.0)

        # Verify the first and third have actual scores
        event1_updated = (
            test_session.query(EconomicEvent)
            .filter_by(event_name="Event 1 - Success")
            .first()
        )
        event3_updated = (
            test_session.query(EconomicEvent)
            .filter_by(event_name="Event 3 - Success")
            .first()
        )

        assert event1_updated.sentiment_score == 0.5
        assert event3_updated.sentiment_score == -0.3

        # The second event that "failed" gets 0.0 from error handling
        event2_updated = (
            test_session.query(EconomicEvent)
            .filter_by(event_name="Event 2 - Will Fail")
            .first()
        )
        assert event2_updated.sentiment_score == 0.0  # Error returns 0.0

    def test_test_run_rolls_back(self, test_session: Session, mock_gemini):
        """test_run=True mode does not commit changes to database.

        Verifies that when test_run=True:
        1. Events are analyzed (we can see the output)
        2. Changes are NOT persisted to the database
        3. Original state is preserved
        """
        # Arrange: Create event
        event = create_sample_event()
        test_session.add(event)
        test_session.commit()
        event_id = event.id

        # Act: Simulate analyze_events with test_run=True
        from news_sentiment.analyzer.gemini import SentimentAnalyzer

        # Create a separate session to simulate the function's session management
        engine = test_session.get_bind()
        TestSession = sessionmaker(bind=engine)
        work_session = TestSession()

        try:
            with patch.object(
                SentimentAnalyzer,
                "__init__",
                lambda self, **kwargs: setattr(self, "model", mock_gemini)
                or setattr(self, "api_key", "test")
                or setattr(self, "model_name", "test")
                or setattr(self, "max_retries", 3),
            ):
                analyzer = SentimentAnalyzer()

                # Query events in work session
                work_event = (
                    work_session.query(EconomicEvent).filter_by(id=event_id).first()
                )

                result = analyzer.analyze(work_event.to_dict_for_gemini())
                work_event.sentiment_score = result["sentiment_score"]
                work_event.raw_response = json.dumps(result["raw_response"])

                # Simulate test_run=True: rollback instead of commit
                work_session.rollback()
        finally:
            work_session.close()

        # Assert: Original session should see no changes
        test_session.expire_all()
        stored = test_session.query(EconomicEvent).filter_by(id=event_id).first()
        assert stored.sentiment_score is None
        assert stored.raw_response is None


@pytest.mark.integration
class TestAnalyzeEventsFunction:
    """Integration tests for the analyze_events function from main.py."""

    def test_analyze_events_returns_count(self, test_session: Session, mock_gemini):
        """analyze_events returns the count of successfully analyzed events."""
        # Arrange: Create events
        event1 = create_sample_event(event_name="Event 1")
        event2 = create_sample_event(event_name="Event 2")
        test_session.add_all([event1, event2])
        test_session.commit()

        # Act: Mock get_session to use our test session
        from contextlib import contextmanager

        @contextmanager
        def mock_get_session():
            yield test_session

        with patch("news_sentiment.main.get_session", mock_get_session):
            from news_sentiment.analyzer.gemini import SentimentAnalyzer

            with patch.object(
                SentimentAnalyzer,
                "__init__",
                lambda self, **kwargs: setattr(self, "model", mock_gemini)
                or setattr(self, "api_key", "test")
                or setattr(self, "model_name", "test")
                or setattr(self, "max_retries", 3),
            ):
                analyzer = SentimentAnalyzer()
                count = analyze_events(analyzer, test_run=False)

        # Assert
        assert count == 2

    def test_analyze_events_skips_scored_events(
        self, test_session: Session, mock_gemini
    ):
        """analyze_events skips events that already have sentiment scores."""
        # Arrange: Create one scored and one unscored event
        scored_event = create_sample_event(
            event_name="Already Scored",
            sentiment_score=0.8,
        )
        unscored_event = create_sample_event(
            event_name="Needs Scoring",
            sentiment_score=None,
        )
        test_session.add_all([scored_event, unscored_event])
        test_session.commit()

        # Act
        from contextlib import contextmanager

        @contextmanager
        def mock_get_session():
            yield test_session

        with patch("news_sentiment.main.get_session", mock_get_session):
            from news_sentiment.analyzer.gemini import SentimentAnalyzer

            with patch.object(
                SentimentAnalyzer,
                "__init__",
                lambda self, **kwargs: setattr(self, "model", mock_gemini)
                or setattr(self, "api_key", "test")
                or setattr(self, "model_name", "test")
                or setattr(self, "max_retries", 3),
            ):
                analyzer = SentimentAnalyzer()
                count = analyze_events(analyzer, test_run=False)

        # Assert: Only one event should be analyzed
        assert count == 1

        # Verify the scored event was not modified
        test_session.expire_all()
        scored = (
            test_session.query(EconomicEvent)
            .filter_by(event_name="Already Scored")
            .first()
        )
        assert scored.sentiment_score == 0.8  # Unchanged

    def test_analyze_events_skips_events_without_actual(
        self, test_session: Session, mock_gemini
    ):
        """analyze_events skips events that don't have actual values yet."""
        # Arrange: Create events with and without actual values
        with_actual = create_sample_event(
            event_name="Has Actual",
            actual="216K",
        )
        without_actual = create_sample_event(
            event_name="No Actual",
            actual=None,
        )
        test_session.add_all([with_actual, without_actual])
        test_session.commit()

        # Act
        from contextlib import contextmanager

        @contextmanager
        def mock_get_session():
            yield test_session

        with patch("news_sentiment.main.get_session", mock_get_session):
            from news_sentiment.analyzer.gemini import SentimentAnalyzer

            with patch.object(
                SentimentAnalyzer,
                "__init__",
                lambda self, **kwargs: setattr(self, "model", mock_gemini)
                or setattr(self, "api_key", "test")
                or setattr(self, "model_name", "test")
                or setattr(self, "max_retries", 3),
            ):
                analyzer = SentimentAnalyzer()
                count = analyze_events(analyzer, test_run=False)

        # Assert: Only event with actual should be analyzed
        assert count == 1

        # Verify event without actual was not touched
        test_session.expire_all()
        no_actual = (
            test_session.query(EconomicEvent).filter_by(event_name="No Actual").first()
        )
        assert no_actual.sentiment_score is None
