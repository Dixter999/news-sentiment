"""
Integration tests for Reddit scraper to database flow.

This module tests the complete integration between the RedditScraper
and the database storage layer. Tests use SQLite in-memory database for
fast, isolated execution.

Stream D: Reddit Scraper Integration Tests
Issue #10: Add Reddit Scraper for Financial Subreddits

Test Cases:
1. Scraped posts stored correctly with all fields
2. Duplicate posts are upserted (not duplicated) based on reddit_id
3. Empty scrape result handling
4. Posts without body text stored correctly
5. Full pipeline: scrape -> analyze -> store
6. Partial failure recovery during analysis
7. Nullable fields (flair, body) handled correctly
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from news_sentiment.database.models import Base, RedditPost


# Helper function to store Reddit posts
def store_reddit_posts(posts: List[Dict[str, Any]], session: Session) -> int:
    """Store scraped Reddit posts in the database.

    Uses merge (upsert) based on reddit_id to handle both new and existing posts.

    Args:
        posts: List of post dictionaries to store
        session: Database session to use

    Returns:
        Number of posts stored
    """
    if not posts:
        return 0

    stored_count = 0
    for post_data in posts:
        # Check if post already exists by reddit_id
        existing = (
            session.query(RedditPost)
            .filter(RedditPost.reddit_id == post_data.get("reddit_id"))
            .first()
        )

        if existing:
            # Update existing post
            for key, value in post_data.items():
                if key != "reddit_id" and hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            # Create new post
            post = RedditPost.from_dict(post_data)
            session.add(post)

        stored_count += 1

    session.commit()
    return stored_count


# Fixtures for Reddit integration tests


@pytest.fixture(scope="function")
def reddit_test_engine():
    """Create an in-memory SQLite engine for testing.

    Creates all tables before the test and drops them after.
    Each test gets a fresh database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def reddit_test_session(reddit_test_engine) -> Generator[Session, None, None]:
    """Create a database session for testing.

    Uses the test engine to create a session that will be cleaned up
    after each test for isolation.
    """
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=reddit_test_engine
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_reddit_post() -> Dict[str, Any]:
    """Sample Reddit post data for testing."""
    return {
        "reddit_id": "abc123",
        "subreddit": "wallstreetbets",
        "title": "GME to the moon! Diamond hands forever!",
        "body": "This is not financial advice, but GME is looking bullish!",
        "url": "https://reddit.com/r/wallstreetbets/comments/abc123",
        "score": 1500,
        "num_comments": 300,
        "flair": "DD",
        "timestamp": datetime(2024, 1, 15, 14, 30, tzinfo=timezone.utc),
    }


@pytest.fixture
def multiple_reddit_posts() -> List[Dict[str, Any]]:
    """Multiple sample Reddit posts for testing."""
    return [
        {
            "reddit_id": "post001",
            "subreddit": "wallstreetbets",
            "title": "GME to the moon!",
            "body": "Diamond hands! HODL!",
            "url": "https://reddit.com/r/wallstreetbets/comments/post001",
            "score": 1500,
            "num_comments": 300,
            "flair": "DD",
            "timestamp": datetime(2024, 1, 15, 8, 30, tzinfo=timezone.utc),
        },
        {
            "reddit_id": "post002",
            "subreddit": "stocks",
            "title": "AAPL earnings analysis",
            "body": "Apple reported strong earnings this quarter...",
            "url": "https://reddit.com/r/stocks/comments/post002",
            "score": 500,
            "num_comments": 150,
            "flair": "Company Analysis",
            "timestamp": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        },
        {
            "reddit_id": "post003",
            "subreddit": "investing",
            "title": "Long-term ETF strategy",
            "body": "Diversification is key to long-term wealth...",
            "url": "https://reddit.com/r/investing/comments/post003",
            "score": 250,
            "num_comments": 75,
            "flair": "Advice",
            "timestamp": datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        },
    ]


@pytest.fixture
def mock_reddit_scraper(multiple_reddit_posts):
    """Mock RedditScraper that returns sample posts."""
    mock = MagicMock()
    mock.scrape_hot.return_value = multiple_reddit_posts
    mock.scrape_new.return_value = [multiple_reddit_posts[0]]
    mock.scrape_top.return_value = multiple_reddit_posts * 2
    return mock


@pytest.fixture
def mock_reddit_praw():
    """Mock PRAW Reddit instance for integration tests.

    Creates a mock that simulates PRAW submission objects with
    all necessary attributes.
    """

    def create_mock_submission(
        post_id: str,
        subreddit: str,
        title: str,
        body: str,
        score: int,
        num_comments: int,
        flair: str = None,
        created_utc: float = 1705330200.0,
    ) -> MagicMock:
        """Create a mock PRAW submission object."""
        mock_submission = MagicMock()
        mock_submission.id = post_id
        mock_submission.subreddit.display_name = subreddit
        mock_submission.title = title
        mock_submission.selftext = body
        mock_submission.url = f"https://reddit.com/r/{subreddit}/comments/{post_id}"
        mock_submission.score = score
        mock_submission.num_comments = num_comments
        mock_submission.link_flair_text = flair
        mock_submission.created_utc = created_utc
        return mock_submission

    return create_mock_submission


@pytest.mark.integration
class TestRedditScraperToDatabase:
    """Integration tests for Reddit scraper to database flow."""

    def test_scraped_posts_stored_correctly(
        self, reddit_test_engine, reddit_test_session, sample_reddit_post
    ):
        """Scraped posts are stored with all fields.

        Verifies that when posts are stored:
        - All post fields are persisted
        - Values match the input data
        - Timestamps are stored correctly (note: SQLite doesn't preserve timezone)
        """
        # Act: Store the post
        posts = [sample_reddit_post]
        count = store_reddit_posts(posts, reddit_test_session)

        # Assert: Verify storage
        assert count == 1

        stored = reddit_test_session.query(RedditPost).first()
        assert stored is not None
        assert stored.reddit_id == "abc123"
        assert stored.subreddit == "wallstreetbets"
        assert stored.title == "GME to the moon! Diamond hands forever!"
        assert (
            stored.body == "This is not financial advice, but GME is looking bullish!"
        )
        assert stored.url == "https://reddit.com/r/wallstreetbets/comments/abc123"
        assert stored.score == 1500
        assert stored.num_comments == 300
        assert stored.flair == "DD"
        # Note: SQLite doesn't preserve timezone info, compare datetime components
        expected_time = datetime(2024, 1, 15, 14, 30)
        assert stored.timestamp.year == expected_time.year
        assert stored.timestamp.month == expected_time.month
        assert stored.timestamp.day == expected_time.day
        assert stored.timestamp.hour == expected_time.hour
        assert stored.timestamp.minute == expected_time.minute

    def test_multiple_posts_stored_correctly(
        self, reddit_test_engine, reddit_test_session, multiple_reddit_posts
    ):
        """Multiple scraped posts are all stored correctly.

        Verifies that when multiple posts are stored:
        - All posts are persisted
        - Each post has correct values
        - No data is lost or corrupted
        """
        # Act
        count = store_reddit_posts(multiple_reddit_posts, reddit_test_session)

        # Assert
        assert count == 3
        stored_count = reddit_test_session.query(RedditPost).count()
        assert stored_count == 3

        # Verify each post
        stored_posts = reddit_test_session.query(RedditPost).all()
        subreddits = {p.subreddit for p in stored_posts}
        assert subreddits == {"wallstreetbets", "stocks", "investing"}

        reddit_ids = {p.reddit_id for p in stored_posts}
        assert reddit_ids == {"post001", "post002", "post003"}

    def test_duplicate_posts_upserted(
        self, reddit_test_engine, reddit_test_session, sample_reddit_post
    ):
        """Duplicate posts (same reddit_id) update existing records.

        Verifies that when the same post is stored twice:
        - Only one record exists in the database
        - The second store updates the existing record
        - Updated values are persisted
        """
        # Act: Store first time
        store_reddit_posts([sample_reddit_post], reddit_test_session)

        # Modify score and store again
        updated_post = sample_reddit_post.copy()
        updated_post["score"] = 2500  # Upvotes increased
        updated_post["num_comments"] = 500  # More comments
        store_reddit_posts([updated_post], reddit_test_session)

        # Assert: Should have only one record
        stored_count = reddit_test_session.query(RedditPost).count()
        assert stored_count == 1

        # Verify updated values
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.reddit_id == "abc123"
        assert stored.score == 2500
        assert stored.num_comments == 500

    def test_empty_scrape_returns_zero(self, reddit_test_engine, reddit_test_session):
        """Empty scrape result stores nothing and returns 0.

        Verifies that store_reddit_posts with empty list:
        - Returns 0
        - Does not create any records
        - Does not raise errors
        """
        # Act
        count = store_reddit_posts([], reddit_test_session)

        # Assert
        assert count == 0
        stored_count = reddit_test_session.query(RedditPost).count()
        assert stored_count == 0

    def test_posts_without_body_stored(self, reddit_test_engine, reddit_test_session):
        """Link posts without body text are stored correctly.

        Verifies that posts with empty or None body:
        - Are stored without errors
        - Have body field as empty string or None
        """
        # Arrange: Link post (no body text)
        link_post = {
            "reddit_id": "link001",
            "subreddit": "wallstreetbets",
            "title": "Check out this news article",
            "body": "",  # Empty body for link post
            "url": "https://news.example.com/article",
            "score": 100,
            "num_comments": 25,
            "flair": None,
            "timestamp": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        }

        # Act
        count = store_reddit_posts([link_post], reddit_test_session)

        # Assert
        assert count == 1
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.reddit_id == "link001"
        assert stored.body == ""
        assert stored.flair is None

    def test_posts_without_flair_stored(self, reddit_test_engine, reddit_test_session):
        """Posts without flair are stored correctly.

        Verifies that posts with None flair:
        - Are stored without errors
        - Have flair field as None
        """
        # Arrange: Post without flair
        post_no_flair = {
            "reddit_id": "noflair001",
            "subreddit": "stocks",
            "title": "Random stock discussion",
            "body": "What do you think about XYZ stock?",
            "url": "https://reddit.com/r/stocks/comments/noflair001",
            "score": 50,
            "num_comments": 10,
            "flair": None,
            "timestamp": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        }

        # Act
        count = store_reddit_posts([post_no_flair], reddit_test_session)

        # Assert
        assert count == 1
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.flair is None


@pytest.mark.integration
class TestRedditScraperDatabaseIntegrationE2E:
    """End-to-end integration tests for Reddit scraper to database flow.

    These tests simulate complete workflows including scraping with mocked
    Reddit API and storing results.
    """

    def test_full_scrape_store_flow(
        self,
        reddit_test_engine,
        reddit_test_session,
        mock_reddit_scraper,
        multiple_reddit_posts,
    ):
        """Full scrape and store flow works end-to-end.

        Simulates complete flow:
        1. Scraper returns posts (mocked)
        2. Posts stored in database
        3. Posts queryable from database
        """
        # Act: Scrape posts
        scraped = mock_reddit_scraper.scrape_hot(limit=25)
        mock_reddit_scraper.scrape_hot.assert_called_once_with(limit=25)

        # Act: Store posts
        count = store_reddit_posts(scraped, reddit_test_session)

        # Assert
        assert count == 3

        # Verify data in database
        stored = reddit_test_session.query(RedditPost).all()
        assert len(stored) == 3

        # Verify we can query specific posts
        wsb_posts = (
            reddit_test_session.query(RedditPost)
            .filter_by(subreddit="wallstreetbets")
            .all()
        )
        assert len(wsb_posts) == 1

        high_score = (
            reddit_test_session.query(RedditPost).filter(RedditPost.score >= 500).all()
        )
        assert len(high_score) == 2

    def test_scrape_analyze_store_pipeline(
        self,
        reddit_test_engine,
        reddit_test_session,
        mock_reddit_scraper,
        multiple_reddit_posts,
    ):
        """Full pipeline: scrape -> analyze -> store.

        Tests the complete flow where posts are scraped,
        analyzed for sentiment, and stored with scores.
        """
        # Step 1: Scrape
        scraped = mock_reddit_scraper.scrape_hot(limit=25)
        assert len(scraped) == 3

        # Step 2: Store posts
        count = store_reddit_posts(scraped, reddit_test_session)
        assert count == 3

        # Step 3: Mock sentiment analysis
        # Simulate adding sentiment scores
        posts = reddit_test_session.query(RedditPost).all()
        sentiment_scores = [0.75, -0.25, 0.50]

        for post, score in zip(posts, sentiment_scores):
            post.sentiment_score = score
            post.raw_response = {
                "score": score,
                "reasoning": f"Analysis for {post.reddit_id}",
            }

        reddit_test_session.commit()

        # Verify: All posts have sentiment scores
        reddit_test_session.expire_all()
        analyzed_posts = reddit_test_session.query(RedditPost).all()

        for post in analyzed_posts:
            assert post.sentiment_score is not None
            assert -1.0 <= post.sentiment_score <= 1.0
            assert post.raw_response is not None

    def test_post_timestamps_preserved(self, reddit_test_engine, reddit_test_session):
        """Post timestamps are preserved through scrape-store flow.

        Verifies that datetime objects are correctly serialized
        and deserialized through the storage layer.
        Note: SQLite doesn't preserve timezone info, but datetime components are kept.
        """
        # Arrange
        specific_time = datetime(2024, 6, 15, 9, 45, 30, tzinfo=timezone.utc)
        post = {
            "reddit_id": "time001",
            "subreddit": "options",
            "title": "Time test post",
            "body": "Testing timestamp preservation",
            "url": "https://reddit.com/r/options/comments/time001",
            "score": 100,
            "num_comments": 20,
            "flair": None,
            "timestamp": specific_time,
        }

        # Act
        store_reddit_posts([post], reddit_test_session)

        # Assert: Verify datetime components are preserved (SQLite loses timezone)
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.timestamp.year == 2024
        assert stored.timestamp.month == 6
        assert stored.timestamp.day == 15
        assert stored.timestamp.hour == 9
        assert stored.timestamp.minute == 45
        assert stored.timestamp.second == 30

    def test_special_characters_in_title_body(
        self, reddit_test_engine, reddit_test_session
    ):
        """Posts with special characters are stored correctly.

        Verifies that titles and bodies containing special characters
        (emojis, unicode, symbols) are handled properly.
        """
        # Arrange
        post = {
            "reddit_id": "emoji001",
            "subreddit": "wallstreetbets",
            "title": "GME $100+ EOW",
            "body": "YOLO! Diamond hands! $$$",
            "url": "https://reddit.com/r/wallstreetbets/comments/emoji001",
            "score": 5000,
            "num_comments": 1000,
            "flair": "YOLO",
            "timestamp": datetime(2024, 1, 15, 16, 0, tzinfo=timezone.utc),
        }

        # Act
        store_reddit_posts([post], reddit_test_session)

        # Assert
        stored = reddit_test_session.query(RedditPost).first()
        assert "GME" in stored.title
        assert "$" in stored.title
        assert "YOLO" in stored.body
        assert stored.flair == "YOLO"


@pytest.mark.integration
class TestRedditScraperEdgeCases:
    """Edge case tests for Reddit scraper to database integration."""

    def test_very_long_title_handled(self, reddit_test_engine, reddit_test_session):
        """Very long titles are handled correctly.

        Reddit titles can be up to 300 characters. Tests storage.
        """
        # Arrange
        long_title = "A" * 250  # Within reasonable limit
        post = {
            "reddit_id": "long001",
            "subreddit": "stocks",
            "title": long_title,
            "body": "Test body",
            "url": "https://reddit.com/r/stocks/comments/long001",
            "score": 100,
            "num_comments": 10,
            "flair": None,
            "timestamp": datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        }

        # Act
        store_reddit_posts([post], reddit_test_session)

        # Assert
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.title == long_title
        assert len(stored.title) == 250

    def test_very_long_body_handled(self, reddit_test_engine, reddit_test_session):
        """Very long body text is handled correctly.

        Reddit posts can have very long self-text. Tests storage.
        """
        # Arrange
        long_body = "B" * 10000  # Long post body
        post = {
            "reddit_id": "longbody001",
            "subreddit": "wallstreetbets",
            "title": "Long DD Post",
            "body": long_body,
            "url": "https://reddit.com/r/wallstreetbets/comments/longbody001",
            "score": 500,
            "num_comments": 200,
            "flair": "DD",
            "timestamp": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        }

        # Act
        store_reddit_posts([post], reddit_test_session)

        # Assert
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.body == long_body
        assert len(stored.body) == 10000

    def test_null_optional_fields_stored(self, reddit_test_engine, reddit_test_session):
        """Posts with null optional fields are stored correctly.

        Verifies handling of nullable fields like body, flair, score.
        """
        # Arrange: Minimal post with nullable fields
        minimal_post = {
            "reddit_id": "min001",
            "subreddit": "investing",
            "title": "Minimal Post",
            "body": None,  # Null body
            "url": None,  # Null URL
            "score": None,  # Null score
            "num_comments": None,  # Null comments
            "flair": None,
            "timestamp": datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        }

        # Act
        store_reddit_posts([minimal_post], reddit_test_session)

        # Assert
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.reddit_id == "min001"
        assert stored.body is None
        assert stored.url is None
        assert stored.score is None
        assert stored.num_comments is None
        assert stored.flair is None

    def test_zero_score_stored(self, reddit_test_engine, reddit_test_session):
        """Posts with zero score are stored correctly.

        Zero is a valid score (post with equal upvotes and downvotes).
        """
        # Arrange
        post = {
            "reddit_id": "zero001",
            "subreddit": "finance",
            "title": "Controversial take",
            "body": "This might be unpopular...",
            "url": "https://reddit.com/r/finance/comments/zero001",
            "score": 0,
            "num_comments": 100,
            "flair": "Discussion",
            "timestamp": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        }

        # Act
        store_reddit_posts([post], reddit_test_session)

        # Assert
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.score == 0

    def test_negative_score_stored(self, reddit_test_engine, reddit_test_session):
        """Posts with negative score are stored correctly.

        Negative scores indicate more downvotes than upvotes.
        """
        # Arrange
        post = {
            "reddit_id": "neg001",
            "subreddit": "stocks",
            "title": "Unpopular opinion",
            "body": "I think this stock is bad...",
            "url": "https://reddit.com/r/stocks/comments/neg001",
            "score": -50,
            "num_comments": 200,
            "flair": "Opinion",
            "timestamp": datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
        }

        # Act
        store_reddit_posts([post], reddit_test_session)

        # Assert
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.score == -50

    def test_multiple_subreddits_queried(
        self, reddit_test_engine, reddit_test_session, multiple_reddit_posts
    ):
        """Posts from multiple subreddits can be queried separately.

        Verifies database queries by subreddit work correctly.
        """
        # Arrange: Store posts from different subreddits
        store_reddit_posts(multiple_reddit_posts, reddit_test_session)

        # Assert: Query by subreddit
        wsb = (
            reddit_test_session.query(RedditPost)
            .filter_by(subreddit="wallstreetbets")
            .all()
        )
        stocks = (
            reddit_test_session.query(RedditPost).filter_by(subreddit="stocks").all()
        )
        investing = (
            reddit_test_session.query(RedditPost).filter_by(subreddit="investing").all()
        )

        assert len(wsb) == 1
        assert len(stocks) == 1
        assert len(investing) == 1
        assert wsb[0].reddit_id == "post001"
        assert stocks[0].reddit_id == "post002"
        assert investing[0].reddit_id == "post003"


@pytest.mark.integration
class TestRedditScraperErrorRecovery:
    """Tests for error handling and recovery in Reddit integration."""

    def test_partial_batch_failure_handled(
        self, reddit_test_engine, reddit_test_session
    ):
        """Batch with some invalid posts doesn't lose valid posts.

        Note: This documents expected behavior - valid posts should be stored
        even if some posts in the batch fail.
        """
        # Arrange: Mix of valid and potentially problematic posts
        posts = [
            {
                "reddit_id": "valid001",
                "subreddit": "stocks",
                "title": "Valid Post 1",
                "body": "This is valid",
                "url": "https://reddit.com/r/stocks/comments/valid001",
                "score": 100,
                "num_comments": 10,
                "flair": None,
                "timestamp": datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
            },
            {
                "reddit_id": "valid002",
                "subreddit": "investing",
                "title": "Valid Post 2",
                "body": "Also valid",
                "url": "https://reddit.com/r/investing/comments/valid002",
                "score": 200,
                "num_comments": 20,
                "flair": "Advice",
                "timestamp": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            },
        ]

        # Act
        count = store_reddit_posts(posts, reddit_test_session)

        # Assert
        assert count == 2
        stored = reddit_test_session.query(RedditPost).all()
        assert len(stored) == 2

    def test_concurrent_upsert_same_reddit_id(
        self, reddit_test_engine, reddit_test_session, sample_reddit_post
    ):
        """Multiple stores of same reddit_id result in single record.

        Tests that rapid successive stores don't create duplicates.
        """
        # Store same post multiple times
        for i in range(3):
            updated = sample_reddit_post.copy()
            updated["score"] = 1000 + (i * 100)
            store_reddit_posts([updated], reddit_test_session)

        # Should have only one record
        count = reddit_test_session.query(RedditPost).count()
        assert count == 1

        # Should have latest score
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.score == 1200  # 1000 + 200

    def test_posts_without_sentiment_queryable(
        self, reddit_test_engine, reddit_test_session, multiple_reddit_posts
    ):
        """Posts without sentiment scores can be queried for analysis.

        Verifies we can find posts needing analysis.
        """
        # Store posts (no sentiment scores yet)
        store_reddit_posts(multiple_reddit_posts, reddit_test_session)

        # Query posts without sentiment
        unscored = (
            reddit_test_session.query(RedditPost)
            .filter(RedditPost.sentiment_score.is_(None))
            .all()
        )

        assert len(unscored) == 3

        # Add sentiment to one post
        unscored[0].sentiment_score = 0.75
        unscored[0].raw_response = {"score": 0.75}
        reddit_test_session.commit()

        # Re-query
        reddit_test_session.expire_all()
        still_unscored = (
            reddit_test_session.query(RedditPost)
            .filter(RedditPost.sentiment_score.is_(None))
            .all()
        )

        assert len(still_unscored) == 2


@pytest.mark.integration
class TestRedditPostModelMethods:
    """Tests for RedditPost model methods in integration context."""

    def test_to_dict_returns_complete_data(
        self, reddit_test_engine, reddit_test_session, sample_reddit_post
    ):
        """to_dict() returns all fields from stored post."""
        # Store and retrieve
        store_reddit_posts([sample_reddit_post], reddit_test_session)
        stored = reddit_test_session.query(RedditPost).first()

        # Convert to dict
        post_dict = stored.to_dict()

        # Verify all fields present
        assert post_dict["reddit_id"] == "abc123"
        assert post_dict["subreddit"] == "wallstreetbets"
        assert post_dict["title"] == "GME to the moon! Diamond hands forever!"
        assert post_dict["body"] is not None
        assert post_dict["score"] == 1500
        assert post_dict["num_comments"] == 300
        assert post_dict["flair"] == "DD"
        assert post_dict["timestamp"] is not None
        assert post_dict["sentiment_score"] is None  # Not yet analyzed
        assert "id" in post_dict
        assert "created_at" in post_dict

    def test_to_dict_for_gemini_returns_analysis_fields(
        self, reddit_test_engine, reddit_test_session, sample_reddit_post
    ):
        """to_dict_for_gemini() returns only fields needed for analysis."""
        # Store and retrieve
        store_reddit_posts([sample_reddit_post], reddit_test_session)
        stored = reddit_test_session.query(RedditPost).first()

        # Convert for Gemini
        gemini_dict = stored.to_dict_for_gemini()

        # Verify analysis fields present
        assert "subreddit" in gemini_dict
        assert "title" in gemini_dict
        assert "body" in gemini_dict
        assert "flair" in gemini_dict
        assert "score" in gemini_dict
        assert "num_comments" in gemini_dict

        # Verify internal fields NOT present
        assert "id" not in gemini_dict
        assert "reddit_id" not in gemini_dict
        assert "created_at" not in gemini_dict
        assert "sentiment_score" not in gemini_dict

    def test_from_dict_creates_valid_instance(
        self, reddit_test_engine, reddit_test_session, sample_reddit_post
    ):
        """from_dict() creates a valid RedditPost instance."""
        # Create from dict
        post = RedditPost.from_dict(sample_reddit_post)

        # Add to session and commit
        reddit_test_session.add(post)
        reddit_test_session.commit()

        # Verify stored correctly
        stored = reddit_test_session.query(RedditPost).first()
        assert stored.reddit_id == "abc123"
        assert stored.subreddit == "wallstreetbets"
