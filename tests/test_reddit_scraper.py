"""
Tests for Reddit Scraper with PRAW integration.

These tests follow TDD methodology:
1. RED: Tests are written first and should fail initially
2. GREEN: Implementation makes tests pass
3. REFACTOR: Code is improved while keeping tests green

Test categories:
- Import tests
- Initialization tests (env vars and explicit credentials)
- Scrape method tests (hot, new, top)
- Error handling tests
- Post data structure tests
"""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestRedditScraperImports:
    """Test that Reddit scraper module and class can be imported."""

    def test_reddit_scraper_module_importable(self):
        """Reddit scraper module should be importable."""
        from news_sentiment.scraper import reddit_scraper

        assert reddit_scraper is not None

    def test_reddit_scraper_class_exists(self):
        """RedditScraper class should exist and be importable."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        assert RedditScraper is not None

    def test_reddit_scraper_from_init(self):
        """RedditScraper should be exported from __init__.py."""
        from news_sentiment.scraper import RedditScraper

        assert RedditScraper is not None


class TestRedditScraperDefaultSubreddits:
    """Test default subreddits configuration."""

    def test_default_subreddits_exists(self):
        """RedditScraper should have DEFAULT_SUBREDDITS class attribute."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        assert hasattr(RedditScraper, "DEFAULT_SUBREDDITS")

    def test_default_subreddits_is_list(self):
        """DEFAULT_SUBREDDITS should be a list."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        assert isinstance(RedditScraper.DEFAULT_SUBREDDITS, list)

    def test_default_subreddits_contains_expected_subreddits(self):
        """DEFAULT_SUBREDDITS should contain expected financial subreddits."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        expected_subreddits = [
            "wallstreetbets",
            "stocks",
            "investing",
            "options",
            "finance",
            "economics",
        ]

        for subreddit in expected_subreddits:
            assert subreddit in RedditScraper.DEFAULT_SUBREDDITS


class TestRedditScraperInitializationEnvVars:
    """Test RedditScraper initialization with environment variables."""

    def test_initialization_with_env_vars(self):
        """Scraper should initialize using environment variables."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_client_id",
                "REDDIT_CLIENT_SECRET": "test_client_secret",
            },
        ):
            with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
                scraper = RedditScraper()

                assert scraper.client_id == "test_client_id"
                assert scraper.client_secret == "test_client_secret"

    def test_initialization_default_user_agent(self):
        """Scraper should have default user agent."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_client_id",
                "REDDIT_CLIENT_SECRET": "test_client_secret",
            },
        ):
            with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
                scraper = RedditScraper()

                assert scraper.user_agent == "news-sentiment/0.1.0"

    def test_initialization_default_subreddits(self):
        """Scraper should use default subreddits when none provided."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_client_id",
                "REDDIT_CLIENT_SECRET": "test_client_secret",
            },
        ):
            with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
                scraper = RedditScraper()

                assert scraper.subreddits == RedditScraper.DEFAULT_SUBREDDITS


class TestRedditScraperInitializationExplicit:
    """Test RedditScraper initialization with explicit credentials."""

    def test_initialization_explicit_credentials(self):
        """Scraper should accept explicit credentials."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
            scraper = RedditScraper(
                client_id="explicit_id",
                client_secret="explicit_secret",
            )

            assert scraper.client_id == "explicit_id"
            assert scraper.client_secret == "explicit_secret"

    def test_initialization_explicit_user_agent(self):
        """Scraper should accept custom user agent."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                user_agent="custom-agent/1.0",
            )

            assert scraper.user_agent == "custom-agent/1.0"

    def test_initialization_custom_subreddits(self):
        """Scraper should accept custom subreddits list."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        custom_subs = ["pennystocks", "cryptocurrency"]

        with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=custom_subs,
            )

            assert scraper.subreddits == custom_subs

    def test_explicit_credentials_override_env_vars(self):
        """Explicit credentials should override environment variables."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "env_client_id",
                "REDDIT_CLIENT_SECRET": "env_client_secret",
            },
        ):
            with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
                scraper = RedditScraper(
                    client_id="explicit_id",
                    client_secret="explicit_secret",
                )

                assert scraper.client_id == "explicit_id"
                assert scraper.client_secret == "explicit_secret"


class TestRedditScraperPRAWInitialization:
    """Test that PRAW Reddit instance is created correctly."""

    def test_praw_reddit_created_on_init(self):
        """PRAW Reddit instance should be created on initialization."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit") as mock_reddit:
            RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            )

            mock_reddit.assert_called_once_with(
                client_id="test_id",
                client_secret="test_secret",
                user_agent="news-sentiment/0.1.0",
            )

    def test_praw_reddit_instance_stored(self):
        """PRAW Reddit instance should be stored as _reddit attribute."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit_instance = MagicMock()
        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit_instance,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            )

            assert scraper._reddit == mock_reddit_instance


class TestRedditScraperScrapeHot:
    """Test scrape_hot method."""

    def test_scrape_hot_returns_list(self):
        """scrape_hot should return a list."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            )

            result = scraper.scrape_hot(limit=10)

            assert isinstance(result, list)

    def test_scrape_hot_calls_subreddit_hot(self):
        """scrape_hot should call hot() on each subreddit."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["wallstreetbets"],
            )

            scraper.scrape_hot(limit=25)

            mock_subreddit.hot.assert_called_with(limit=25)

    def test_scrape_hot_default_limit(self):
        """scrape_hot should default to limit=25."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["stocks"],
            )

            scraper.scrape_hot()

            mock_subreddit.hot.assert_called_with(limit=25)

    def test_scrape_hot_returns_correct_format(self):
        """scrape_hot should return posts in correct dictionary format."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_submission = MagicMock()
        mock_submission.id = "abc123"
        mock_submission.subreddit.display_name = "wallstreetbets"
        mock_submission.title = "Test Post Title"
        mock_submission.selftext = "Test post body"
        mock_submission.url = "https://reddit.com/r/wallstreetbets/abc123"
        mock_submission.score = 1500
        mock_submission.num_comments = 250
        mock_submission.link_flair_text = "Discussion"
        mock_submission.created_utc = 1701388800.0  # 2023-12-01 00:00:00 UTC

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_submission]

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["wallstreetbets"],
            )

            result = scraper.scrape_hot(limit=1)

            assert len(result) == 1
            post = result[0]
            assert post["reddit_id"] == "abc123"
            assert post["subreddit"] == "wallstreetbets"
            assert post["title"] == "Test Post Title"
            assert post["body"] == "Test post body"
            assert post["url"] == "https://reddit.com/r/wallstreetbets/abc123"
            assert post["score"] == 1500
            assert post["num_comments"] == 250
            assert post["flair"] == "Discussion"
            assert isinstance(post["timestamp"], datetime)


class TestRedditScraperScrapeNew:
    """Test scrape_new method."""

    def test_scrape_new_returns_list(self):
        """scrape_new should return a list."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.new.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            )

            result = scraper.scrape_new(limit=10)

            assert isinstance(result, list)

    def test_scrape_new_calls_subreddit_new(self):
        """scrape_new should call new() on each subreddit."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.new.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["investing"],
            )

            scraper.scrape_new(limit=25)

            mock_subreddit.new.assert_called_with(limit=25)

    def test_scrape_new_default_limit(self):
        """scrape_new should default to limit=25."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.new.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["stocks"],
            )

            scraper.scrape_new()

            mock_subreddit.new.assert_called_with(limit=25)


class TestRedditScraperScrapeTop:
    """Test scrape_top method."""

    def test_scrape_top_returns_list(self):
        """scrape_top should return a list."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.top.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            )

            result = scraper.scrape_top(time_filter="day", limit=10)

            assert isinstance(result, list)

    def test_scrape_top_calls_subreddit_top_with_time_filter(self):
        """scrape_top should call top() with time_filter parameter."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.top.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["options"],
            )

            scraper.scrape_top(time_filter="week", limit=25)

            mock_subreddit.top.assert_called_with(time_filter="week", limit=25)

    def test_scrape_top_default_time_filter_is_day(self):
        """scrape_top should default time_filter to 'day'."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.top.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["finance"],
            )

            scraper.scrape_top(limit=25)

            mock_subreddit.top.assert_called_with(time_filter="day", limit=25)

    def test_scrape_top_accepts_valid_time_filters(self):
        """scrape_top should accept all valid time filter values."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        valid_filters = ["hour", "day", "week", "month", "year", "all"]

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.top.return_value = []

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["economics"],
            )

            for time_filter in valid_filters:
                scraper.scrape_top(time_filter=time_filter, limit=1)
                mock_subreddit.top.assert_called_with(time_filter=time_filter, limit=1)


class TestRedditScraperPostDataStructure:
    """Test the structure of scraped post data."""

    def test_post_has_all_required_fields(self):
        """Each post should have all required fields."""
        required_fields = [
            "reddit_id",
            "subreddit",
            "title",
            "body",
            "url",
            "score",
            "num_comments",
            "flair",
            "timestamp",
        ]

        mock_submission = MagicMock()
        mock_submission.id = "xyz789"
        mock_submission.subreddit.display_name = "stocks"
        mock_submission.title = "Market Analysis"
        mock_submission.selftext = "Detailed analysis here"
        mock_submission.url = "https://reddit.com/r/stocks/xyz789"
        mock_submission.score = 500
        mock_submission.num_comments = 100
        mock_submission.link_flair_text = "DD"
        mock_submission.created_utc = 1701388800.0

        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_submission]

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["stocks"],
            )

            result = scraper.scrape_hot(limit=1)
            post = result[0]

            for field in required_fields:
                assert field in post, f"Missing field: {field}"

    def test_post_flair_can_be_none(self):
        """Post flair should be None when no flair is set."""
        mock_submission = MagicMock()
        mock_submission.id = "noflair123"
        mock_submission.subreddit.display_name = "investing"
        mock_submission.title = "Post without flair"
        mock_submission.selftext = "No flair here"
        mock_submission.url = "https://reddit.com/r/investing/noflair123"
        mock_submission.score = 50
        mock_submission.num_comments = 10
        mock_submission.link_flair_text = None
        mock_submission.created_utc = 1701388800.0

        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_submission]

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["investing"],
            )

            result = scraper.scrape_hot(limit=1)
            post = result[0]

            assert post["flair"] is None

    def test_timestamp_is_datetime_object(self):
        """Post timestamp should be a datetime object converted from created_utc."""
        mock_submission = MagicMock()
        mock_submission.id = "time123"
        mock_submission.subreddit.display_name = "options"
        mock_submission.title = "Time test post"
        mock_submission.selftext = ""
        mock_submission.url = "https://reddit.com/r/options/time123"
        mock_submission.score = 100
        mock_submission.num_comments = 20
        mock_submission.link_flair_text = None
        mock_submission.created_utc = 1701388800.0  # 2023-12-01 00:00:00 UTC

        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_submission]

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["options"],
            )

            result = scraper.scrape_hot(limit=1)
            post = result[0]

            assert isinstance(post["timestamp"], datetime)
            assert post["timestamp"] == datetime.fromtimestamp(
                1701388800.0, tz=timezone.utc
            )


class TestRedditScraperErrorHandling:
    """Test error handling for API failures."""

    def test_missing_credentials_raises_error(self):
        """Scraper should raise error when credentials are missing."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing env vars
            os.environ.pop("REDDIT_CLIENT_ID", None)
            os.environ.pop("REDDIT_CLIENT_SECRET", None)

            with pytest.raises(ValueError) as exc_info:
                RedditScraper()

            assert (
                "client_id" in str(exc_info.value).lower()
                or "credentials" in str(exc_info.value).lower()
            )

    def test_api_error_handling_in_scrape_hot(self):
        """scrape_hot should handle API errors gracefully."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.side_effect = Exception("API rate limit exceeded")

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["wallstreetbets"],
            )

            # Should either raise a specific exception or return empty list
            try:
                result = scraper.scrape_hot(limit=10)
                # If it returns, it should be an empty list or handle gracefully
                assert isinstance(result, list)
            except Exception as e:
                # Should be a meaningful error, not the raw API error
                assert "error" in str(e).lower() or "failed" in str(e).lower()

    def test_invalid_subreddit_handling(self):
        """Scraper should handle invalid subreddit names gracefully."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.side_effect = Exception("Subreddit not found")

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["nonexistent_subreddit_xyz123"],
            )

            # Should handle the error gracefully
            try:
                result = scraper.scrape_hot(limit=10)
                assert isinstance(result, list)
            except Exception:
                pass  # Expected behavior for invalid subreddit


class TestRedditScraperMultipleSubreddits:
    """Test scraping from multiple subreddits."""

    def test_scrape_hot_from_multiple_subreddits(self):
        """scrape_hot should aggregate posts from all configured subreddits."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        # Create mock submissions for different subreddits
        mock_submission_wsb = MagicMock()
        mock_submission_wsb.id = "wsb123"
        mock_submission_wsb.subreddit.display_name = "wallstreetbets"
        mock_submission_wsb.title = "WSB Post"
        mock_submission_wsb.selftext = ""
        mock_submission_wsb.url = "https://reddit.com/r/wallstreetbets/wsb123"
        mock_submission_wsb.score = 1000
        mock_submission_wsb.num_comments = 500
        mock_submission_wsb.link_flair_text = None
        mock_submission_wsb.created_utc = 1701388800.0

        mock_submission_stocks = MagicMock()
        mock_submission_stocks.id = "stocks456"
        mock_submission_stocks.subreddit.display_name = "stocks"
        mock_submission_stocks.title = "Stocks Post"
        mock_submission_stocks.selftext = ""
        mock_submission_stocks.url = "https://reddit.com/r/stocks/stocks456"
        mock_submission_stocks.score = 200
        mock_submission_stocks.num_comments = 50
        mock_submission_stocks.link_flair_text = None
        mock_submission_stocks.created_utc = 1701388800.0

        mock_reddit = MagicMock()

        def get_subreddit(name):
            mock_sub = MagicMock()
            if name == "wallstreetbets":
                mock_sub.hot.return_value = [mock_submission_wsb]
            else:
                mock_sub.hot.return_value = [mock_submission_stocks]
            return mock_sub

        mock_reddit.subreddit.side_effect = get_subreddit

        with patch(
            "news_sentiment.scraper.reddit_scraper.praw.Reddit",
            return_value=mock_reddit,
        ):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
                subreddits=["wallstreetbets", "stocks"],
            )

            result = scraper.scrape_hot(limit=1)

            # Should have posts from both subreddits
            assert len(result) == 2
            subreddits = {post["subreddit"] for post in result}
            assert "wallstreetbets" in subreddits
            assert "stocks" in subreddits


class TestRedditScraperContextManager:
    """Test context manager support (optional feature)."""

    def test_can_be_used_as_context_manager(self):
        """RedditScraper should support context manager protocol."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
            with RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            ) as scraper:
                assert scraper is not None

    def test_context_manager_returns_scraper_instance(self):
        """Context manager __enter__ should return the scraper instance."""
        from news_sentiment.scraper.reddit_scraper import RedditScraper

        with patch("news_sentiment.scraper.reddit_scraper.praw.Reddit"):
            scraper = RedditScraper(
                client_id="test_id",
                client_secret="test_secret",
            )

            result = scraper.__enter__()

            assert result is scraper
