"""
Database tests for news-sentiment package.

These tests verify:
1. EconomicEvent model has all required fields
2. Model serialization (to_dict) works correctly
3. Model deserialization (from_dict) works correctly
4. Database connection can be established
5. Session management works correctly

Following TDD: These tests define the expected behavior.
They should FAIL (RED phase) until the implementation is complete.
"""

from datetime import datetime, timezone
from typing import Any, Dict


class TestEconomicEventModel:
    """Test EconomicEvent SQLAlchemy model."""

    def test_economic_event_has_all_required_columns(self):
        """EconomicEvent model should have all required columns."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        # Check that all required columns exist
        assert hasattr(EconomicEvent, "id")
        assert hasattr(EconomicEvent, "timestamp")
        assert hasattr(EconomicEvent, "currency")
        assert hasattr(EconomicEvent, "event_name")
        assert hasattr(EconomicEvent, "impact")
        assert hasattr(EconomicEvent, "actual")
        assert hasattr(EconomicEvent, "forecast")
        assert hasattr(EconomicEvent, "previous")
        assert hasattr(EconomicEvent, "sentiment_score")
        assert hasattr(EconomicEvent, "raw_response")
        assert hasattr(EconomicEvent, "created_at")
        assert hasattr(EconomicEvent, "updated_at")

    def test_economic_event_table_name(self):
        """EconomicEvent model should map to 'economic_events' table."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        assert EconomicEvent.__tablename__ == "economic_events"

    def test_to_dict_returns_all_fields(self):
        """to_dict() should return all fields for serialization."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        # Create a test instance
        event = EconomicEvent(
            id=1,
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            currency="USD",
            event_name="Non-Farm Payrolls",
            impact="High",
            actual="250K",
            forecast="200K",
            previous="150K",
            sentiment_score=0.75,
            raw_response='{"analysis": "positive"}',
            created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        )

        result = event.to_dict()

        # Verify all fields are present
        assert "id" in result
        assert "timestamp" in result
        assert "currency" in result
        assert "event_name" in result
        assert "impact" in result
        assert "actual" in result
        assert "forecast" in result
        assert "previous" in result
        assert "sentiment_score" in result
        assert "raw_response" in result
        assert "created_at" in result
        assert "updated_at" in result

        # Verify values
        assert result["id"] == 1
        assert result["currency"] == "USD"
        assert result["event_name"] == "Non-Farm Payrolls"
        assert result["impact"] == "High"
        assert result["actual"] == "250K"
        assert result["forecast"] == "200K"
        assert result["previous"] == "150K"
        assert result["sentiment_score"] == 0.75

    def test_to_dict_for_gemini_returns_analysis_fields(self):
        """to_dict_for_gemini() should return only fields needed for sentiment analysis."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        event = EconomicEvent(
            id=1,
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            currency="USD",
            event_name="Non-Farm Payrolls",
            impact="High",
            actual="250K",
            forecast="200K",
            previous="150K",
            sentiment_score=0.75,
            raw_response='{"analysis": "positive"}',
        )

        result = event.to_dict_for_gemini()

        # Should only include fields needed for Gemini analysis
        assert "event_name" in result
        assert "currency" in result
        assert "impact" in result
        assert "actual" in result
        assert "forecast" in result
        assert "previous" in result

        # Should NOT include internal fields
        assert "id" not in result
        assert "sentiment_score" not in result
        assert "raw_response" not in result
        assert "created_at" not in result
        assert "updated_at" not in result

    def test_from_dict_creates_instance(self):
        """from_dict() class method should create an instance from dictionary."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        data: Dict[str, Any] = {
            "timestamp": datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            "currency": "EUR",
            "event_name": "ECB Interest Rate Decision",
            "impact": "High",
            "actual": "4.50%",
            "forecast": "4.50%",
            "previous": "4.25%",
        }

        event = EconomicEvent.from_dict(data)

        assert isinstance(event, EconomicEvent)
        assert event.timestamp == data["timestamp"]
        assert event.currency == "EUR"
        assert event.event_name == "ECB Interest Rate Decision"
        assert event.impact == "High"
        assert event.actual == "4.50%"
        assert event.forecast == "4.50%"
        assert event.previous == "4.25%"
        # Optional fields should be None
        assert event.sentiment_score is None
        assert event.raw_response is None

    def test_from_dict_handles_optional_fields(self):
        """from_dict() should handle optional fields correctly."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        data: Dict[str, Any] = {
            "timestamp": datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            "currency": "USD",
            "event_name": "Test Event",
            "impact": "Medium",
            "actual": None,  # Optional
            "forecast": "100K",
            "previous": None,  # Optional
            "sentiment_score": 0.5,
            "raw_response": '{"test": true}',
        }

        event = EconomicEvent.from_dict(data)

        assert event.actual is None
        assert event.previous is None
        assert event.sentiment_score == 0.5
        assert event.raw_response == '{"test": true}'

    def test_repr_returns_readable_string(self):
        """__repr__ should return a readable string representation."""
        try:
            from news_sentiment.database.models import EconomicEvent
        except ImportError:
            from src.news_sentiment.database.models import EconomicEvent

        event = EconomicEvent(
            id=1,
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            currency="USD",
            event_name="Non-Farm Payrolls",
        )

        repr_str = repr(event)

        assert "EconomicEvent" in repr_str
        assert "id=1" in repr_str
        assert "USD" in repr_str
        assert "Non-Farm Payrolls" in repr_str


class TestDatabaseConnection:
    """Test database connection module."""

    def test_connection_module_exists(self):
        """connection.py module should be importable."""
        try:
            from news_sentiment.database import connection  # noqa: F401
        except ImportError:
            from src.news_sentiment.database import connection  # noqa: F401

    def test_get_session_function_exists(self):
        """get_session() function should exist in connection module."""
        try:
            from news_sentiment.database.connection import get_session
        except ImportError:
            from src.news_sentiment.database.connection import get_session

        assert callable(get_session)

    def test_get_session_is_context_manager(self):
        """get_session() should be usable as a context manager."""
        try:
            from news_sentiment.database.connection import get_session
        except ImportError:
            from src.news_sentiment.database.connection import get_session

        # Verify it has context manager protocol
        assert hasattr(get_session, "__enter__") or hasattr(
            get_session(), "__enter__"
        ), "get_session must support context manager protocol"

    def test_create_engine_function_exists(self):
        """create_engine() function should exist for custom engine creation."""
        try:
            from news_sentiment.database.connection import create_db_engine
        except ImportError:
            from src.news_sentiment.database.connection import create_db_engine

        assert callable(create_db_engine)

    def test_session_maker_function_exists(self):
        """get_session_maker() should exist for creating session factories."""
        try:
            from news_sentiment.database.connection import get_session_maker
        except ImportError:
            from src.news_sentiment.database.connection import get_session_maker

        assert callable(get_session_maker)


class TestDatabaseConfig:
    """Test database configuration."""

    def test_database_url_construction(self):
        """get_database_url() should construct proper PostgreSQL URL."""
        import os

        # Save original values
        original_host = os.environ.get("AI_MODEL_DB_HOST")
        original_port = os.environ.get("AI_MODEL_DB_PORT")
        original_name = os.environ.get("AI_MODEL_DB_NAME")
        original_user = os.environ.get("AI_MODEL_DB_USER")
        original_password = os.environ.get("AI_MODEL_DB_PASSWORD")

        try:
            # Set up test environment variables (using the actual env var names)
            os.environ["AI_MODEL_DB_HOST"] = "localhost"
            os.environ["AI_MODEL_DB_PORT"] = "5432"
            os.environ["AI_MODEL_DB_NAME"] = "test_db"
            os.environ["AI_MODEL_DB_USER"] = "test_user"
            os.environ["AI_MODEL_DB_PASSWORD"] = "test_pass"

            try:
                from news_sentiment.database.connection import get_database_url
            except ImportError:
                from src.news_sentiment.database.connection import get_database_url

            url = get_database_url()

            assert "postgresql" in url
            assert "localhost" in url
            assert "5432" in url
            assert "test_db" in url
            assert "test_user" in url

        finally:
            # Restore original values
            if original_host is not None:
                os.environ["AI_MODEL_DB_HOST"] = original_host
            elif "AI_MODEL_DB_HOST" in os.environ:
                del os.environ["AI_MODEL_DB_HOST"]

            if original_port is not None:
                os.environ["AI_MODEL_DB_PORT"] = original_port
            elif "AI_MODEL_DB_PORT" in os.environ:
                del os.environ["AI_MODEL_DB_PORT"]

            if original_name is not None:
                os.environ["AI_MODEL_DB_NAME"] = original_name
            elif "AI_MODEL_DB_NAME" in os.environ:
                del os.environ["AI_MODEL_DB_NAME"]

            if original_user is not None:
                os.environ["AI_MODEL_DB_USER"] = original_user
            elif "AI_MODEL_DB_USER" in os.environ:
                del os.environ["AI_MODEL_DB_USER"]

            if original_password is not None:
                os.environ["AI_MODEL_DB_PASSWORD"] = original_password
            elif "AI_MODEL_DB_PASSWORD" in os.environ:
                del os.environ["AI_MODEL_DB_PASSWORD"]

    def test_pool_configuration_defaults(self):
        """Connection pool should have sensible defaults."""
        try:
            from news_sentiment.database.connection import (
                DEFAULT_POOL_SIZE,
                DEFAULT_MAX_OVERFLOW,
            )
        except ImportError:
            from src.news_sentiment.database.connection import (
                DEFAULT_POOL_SIZE,
                DEFAULT_MAX_OVERFLOW,
            )

        assert DEFAULT_POOL_SIZE == 5
        assert DEFAULT_MAX_OVERFLOW == 10


class TestDatabaseExports:
    """Test that database module exports all necessary components."""

    def test_base_exported(self):
        """Base declarative class should be exported from database module."""
        try:
            from news_sentiment.database.models import Base
        except ImportError:
            from src.news_sentiment.database.models import Base

        assert Base is not None

    def test_economic_event_exported_from_database(self):
        """EconomicEvent should be exported from database module."""
        try:
            from news_sentiment.database import EconomicEvent
        except ImportError:
            from src.news_sentiment.database import EconomicEvent

        assert EconomicEvent is not None

    def test_get_session_exported_from_database(self):
        """get_session should be exported from database module."""
        try:
            from news_sentiment.database import get_session
        except ImportError:
            from src.news_sentiment.database import get_session

        assert callable(get_session)


class TestRedditPostModel:
    """Test RedditPost SQLAlchemy model for storing Reddit post data."""

    def test_reddit_post_has_all_required_columns(self):
        """RedditPost model should have all required columns."""
        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        # Check that all required columns exist
        assert hasattr(RedditPost, "id")
        assert hasattr(RedditPost, "reddit_id")
        assert hasattr(RedditPost, "subreddit")
        assert hasattr(RedditPost, "title")
        assert hasattr(RedditPost, "body")
        assert hasattr(RedditPost, "url")
        assert hasattr(RedditPost, "score")
        assert hasattr(RedditPost, "num_comments")
        assert hasattr(RedditPost, "flair")
        assert hasattr(RedditPost, "timestamp")
        assert hasattr(RedditPost, "sentiment_score")
        assert hasattr(RedditPost, "raw_response")
        assert hasattr(RedditPost, "created_at")
        assert hasattr(RedditPost, "updated_at")

    def test_reddit_post_table_name(self):
        """RedditPost model should map to 'reddit_posts' table."""
        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        assert RedditPost.__tablename__ == "reddit_posts"

    def test_to_dict_returns_all_fields(self):
        """to_dict() should return all fields for serialization."""
        from datetime import datetime, timezone

        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        # Create a test instance
        post = RedditPost(
            id=1,
            reddit_id="abc123xyz",
            subreddit="wallstreetbets",
            title="GME to the moon!",
            body="Diamond hands forever",
            url="https://reddit.com/r/wallstreetbets/comments/abc123xyz",
            score=1500,
            num_comments=342,
            flair="YOLO",
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            sentiment_score=0.85,
            raw_response={"analysis": "bullish", "confidence": 0.9},
            created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        )

        result = post.to_dict()

        # Verify all fields are present
        assert "id" in result
        assert "reddit_id" in result
        assert "subreddit" in result
        assert "title" in result
        assert "body" in result
        assert "url" in result
        assert "score" in result
        assert "num_comments" in result
        assert "flair" in result
        assert "timestamp" in result
        assert "sentiment_score" in result
        assert "raw_response" in result
        assert "created_at" in result
        assert "updated_at" in result

        # Verify values
        assert result["id"] == 1
        assert result["reddit_id"] == "abc123xyz"
        assert result["subreddit"] == "wallstreetbets"
        assert result["title"] == "GME to the moon!"
        assert result["body"] == "Diamond hands forever"
        assert result["score"] == 1500
        assert result["num_comments"] == 342
        assert result["flair"] == "YOLO"
        assert result["sentiment_score"] == 0.85

    def test_to_dict_for_gemini_returns_analysis_fields(self):
        """to_dict_for_gemini() should return only fields needed for sentiment analysis."""
        from datetime import datetime, timezone

        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        post = RedditPost(
            id=1,
            reddit_id="abc123xyz",
            subreddit="wallstreetbets",
            title="GME to the moon!",
            body="Diamond hands forever",
            url="https://reddit.com/r/wallstreetbets/comments/abc123xyz",
            score=1500,
            num_comments=342,
            flair="YOLO",
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            sentiment_score=0.85,
            raw_response={"analysis": "bullish"},
        )

        result = post.to_dict_for_gemini()

        # Should only include fields needed for Gemini analysis
        assert "subreddit" in result
        assert "title" in result
        assert "body" in result
        assert "flair" in result
        assert "score" in result
        assert "num_comments" in result

        # Should NOT include internal fields
        assert "id" not in result
        assert "reddit_id" not in result
        assert "url" not in result
        assert "sentiment_score" not in result
        assert "raw_response" not in result
        assert "created_at" not in result
        assert "updated_at" not in result
        assert "timestamp" not in result

    def test_from_dict_creates_instance(self):
        """from_dict() class method should create an instance from dictionary."""
        from datetime import datetime, timezone
        from typing import Any, Dict

        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        data: Dict[str, Any] = {
            "reddit_id": "xyz789abc",
            "subreddit": "stocks",
            "title": "AAPL earnings beat expectations",
            "body": "Apple reported Q4 earnings above consensus...",
            "url": "https://reddit.com/r/stocks/comments/xyz789abc",
            "score": 2500,
            "num_comments": 450,
            "flair": "Earnings",
            "timestamp": datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
        }

        post = RedditPost.from_dict(data)

        assert isinstance(post, RedditPost)
        assert post.reddit_id == "xyz789abc"
        assert post.subreddit == "stocks"
        assert post.title == "AAPL earnings beat expectations"
        assert post.body == "Apple reported Q4 earnings above consensus..."
        assert post.url == "https://reddit.com/r/stocks/comments/xyz789abc"
        assert post.score == 2500
        assert post.num_comments == 450
        assert post.flair == "Earnings"
        assert post.timestamp == data["timestamp"]
        # Optional fields should be None
        assert post.sentiment_score is None
        assert post.raw_response is None

    def test_from_dict_handles_optional_fields(self):
        """from_dict() should handle optional fields correctly."""
        from datetime import datetime, timezone
        from typing import Any, Dict

        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        # Minimal data with optional fields
        data: Dict[str, Any] = {
            "reddit_id": "min123",
            "subreddit": "investing",
            "title": "Link post with no body",
            "body": None,  # Link posts have no body
            "url": "https://reddit.com/r/investing/comments/min123",
            "score": 100,
            "num_comments": 25,
            "flair": None,  # No flair
            "timestamp": datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
            "sentiment_score": -0.3,
            "raw_response": {"sentiment": "bearish"},
        }

        post = RedditPost.from_dict(data)

        assert post.body is None
        assert post.flair is None
        assert post.sentiment_score == -0.3
        assert post.raw_response == {"sentiment": "bearish"}

    def test_repr_returns_readable_string(self):
        """__repr__ should return a readable string representation."""
        from datetime import datetime, timezone

        try:
            from news_sentiment.database.models import RedditPost
        except ImportError:
            from src.news_sentiment.database.models import RedditPost

        post = RedditPost(
            id=1,
            reddit_id="abc123",
            subreddit="wallstreetbets",
            title="GME to the moon!",
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
        )

        repr_str = repr(post)

        assert "RedditPost" in repr_str
        assert "id=1" in repr_str
        assert "abc123" in repr_str
        assert "wallstreetbets" in repr_str


class TestRedditPostExport:
    """Test that RedditPost is exported from database module."""

    def test_reddit_post_exported_from_database(self):
        """RedditPost should be exported from database module."""
        try:
            from news_sentiment.database import RedditPost
        except ImportError:
            from src.news_sentiment.database import RedditPost

        assert RedditPost is not None
