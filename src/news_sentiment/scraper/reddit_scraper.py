"""
Reddit Scraper for Financial Subreddits.

This module provides functionality to scrape posts from Reddit
using the PRAW (Python Reddit API Wrapper) library for OAuth2 authentication.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import praw


class RedditScraper:
    """Scraper for Reddit financial subreddits.

    Uses PRAW for Reddit API access with OAuth2 authentication.
    Supports scraping hot, new, and top posts from configured subreddits.

    Attributes:
        client_id: Reddit API client ID
        client_secret: Reddit API client secret
        user_agent: User agent string for API requests
        subreddits: List of subreddit names to scrape
    """

    DEFAULT_SUBREDDITS = [
        "wallstreetbets",
        "stocks",
        "investing",
        "options",
        "finance",
        "economics",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "news-sentiment/0.1.0",
        subreddits: Optional[List[str]] = None,
    ) -> None:
        """Initialize the Reddit scraper.

        Args:
            client_id: Reddit API client ID. Falls back to REDDIT_CLIENT_ID env var.
            client_secret: Reddit API client secret. Falls back to REDDIT_CLIENT_SECRET env var.
            user_agent: User agent string for API requests (default: "news-sentiment/0.1.0")
            subreddits: List of subreddits to scrape (default: DEFAULT_SUBREDDITS)

        Raises:
            ValueError: If client_id or client_secret are not provided and not in env vars.
        """
        # Resolve credentials from parameters or environment variables
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent
        self.subreddits = (
            subreddits if subreddits is not None else self.DEFAULT_SUBREDDITS
        )

        # Validate required credentials
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Reddit API credentials required. "
                "Provide client_id and client_secret parameters or set "
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
            )

        # Initialize PRAW Reddit instance
        self._reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )

    def _convert_submission_to_dict(self, submission: Any) -> Dict[str, Any]:
        """Convert a PRAW submission object to a dictionary.

        Args:
            submission: PRAW Submission object

        Returns:
            Dictionary with post data
        """
        return {
            "reddit_id": submission.id,
            "subreddit": submission.subreddit.display_name,
            "title": submission.title,
            "body": submission.selftext,
            "url": submission.url,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "flair": submission.link_flair_text,
            "timestamp": datetime.fromtimestamp(
                submission.created_utc, tz=timezone.utc
            ),
        }

    def scrape_hot(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Scrape hot posts from configured subreddits.

        Args:
            limit: Maximum number of posts to fetch per subreddit (default: 25)

        Returns:
            List of post dictionaries containing:
                - reddit_id: str (submission.id)
                - subreddit: str (submission.subreddit.display_name)
                - title: str
                - body: str (submission.selftext)
                - url: str (submission.url)
                - score: int
                - num_comments: int
                - flair: str or None (submission.link_flair_text)
                - timestamp: datetime (from submission.created_utc)
        """
        posts: List[Dict[str, Any]] = []

        for subreddit_name in self.subreddits:
            try:
                subreddit = self._reddit.subreddit(subreddit_name)
                for submission in subreddit.hot(limit=limit):
                    posts.append(self._convert_submission_to_dict(submission))
            except Exception:
                # Log error but continue with other subreddits
                continue

        return posts

    def scrape_new(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Scrape new posts from configured subreddits.

        Args:
            limit: Maximum number of posts to fetch per subreddit (default: 25)

        Returns:
            List of post dictionaries (same format as scrape_hot)
        """
        posts: List[Dict[str, Any]] = []

        for subreddit_name in self.subreddits:
            try:
                subreddit = self._reddit.subreddit(subreddit_name)
                for submission in subreddit.new(limit=limit):
                    posts.append(self._convert_submission_to_dict(submission))
            except Exception:
                # Log error but continue with other subreddits
                continue

        return posts

    def scrape_top(
        self, time_filter: str = "day", limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Scrape top posts from configured subreddits.

        Args:
            time_filter: Time filter for top posts.
                Valid values: "hour", "day", "week", "month", "year", "all"
                (default: "day")
            limit: Maximum number of posts to fetch per subreddit (default: 25)

        Returns:
            List of post dictionaries (same format as scrape_hot)
        """
        posts: List[Dict[str, Any]] = []

        for subreddit_name in self.subreddits:
            try:
                subreddit = self._reddit.subreddit(subreddit_name)
                for submission in subreddit.top(time_filter=time_filter, limit=limit):
                    posts.append(self._convert_submission_to_dict(submission))
            except Exception:
                # Log error but continue with other subreddits
                continue

        return posts

    def __enter__(self) -> "RedditScraper":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        # PRAW doesn't require explicit cleanup, but we support the protocol
        pass
