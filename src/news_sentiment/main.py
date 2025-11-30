"""
Main entry point for the News Sentiment Service.

This module provides the primary CLI interface and orchestration
functions for the complete pipeline: Scrape -> Analyze -> Store.
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from news_sentiment.analyzer.gemini import SentimentAnalyzer
from news_sentiment.database import EconomicEvent, RedditPost, get_session
from news_sentiment.scraper.ff_scraper import ForexFactoryScraper
from news_sentiment.scraper.reddit_scraper import RedditScraper

# Configure logging
logger = logging.getLogger(__name__)


def scrape_events(
    scraper: ForexFactoryScraper,
    period: str = None,
    mode: str = None,
) -> List[Dict[str, Any]]:
    """Scrape economic calendar events.

    Args:
        scraper: ForexFactoryScraper instance to use for scraping
        period: Scraping period - "today", "week", or "month"
        mode: Alias for period (for backwards compatibility)

    Returns:
        List of event dictionaries containing event data

    Raises:
        ValueError: If an invalid period/mode is specified
    """
    # Support both 'period' and 'mode' parameters
    effective_period = period or mode or "week"
    valid_periods = ["today", "week", "month"]

    if effective_period not in valid_periods:
        raise ValueError(
            f"Invalid period '{effective_period}'. Must be one of: {valid_periods}"
        )

    now = datetime.now()

    if effective_period == "today":
        return scraper.scrape_day(now)
    elif effective_period == "week":
        return scraper.scrape_week(now)
    elif effective_period == "month":
        return scraper.scrape_month(now.year, now.month)

    return []


def store_events(events: List[Dict[str, Any]]) -> int:
    """Store scraped events in the database.

    Uses merge (upsert) to handle both new and existing events.
    Filters out events with null timestamps (e.g., Tentative events).

    Args:
        events: List of event dictionaries to store

    Returns:
        Number of events stored
    """
    if not events:
        return 0

    # Filter out events with null timestamps
    valid_events = [e for e in events if e.get("timestamp") is not None]
    skipped = len(events) - len(valid_events)
    if skipped > 0:
        logger.info(f"Skipped {skipped} events with null timestamps")

    stored_count = 0
    with get_session() as session:
        for event_data in valid_events:
            event = EconomicEvent.from_dict(event_data)
            session.merge(event)
            stored_count += 1

    return stored_count


def analyze_events(
    analyzer: SentimentAnalyzer,
    test_run: bool = False,
) -> int:
    """Analyze events that don't have sentiment scores.

    Queries events that have actual values but no sentiment score,
    analyzes them using Gemini, and stores the results.

    Args:
        analyzer: SentimentAnalyzer instance to use for analysis
        test_run: If True, don't commit changes (rollback instead)

    Returns:
        Number of events successfully analyzed
    """
    analyzed_count = 0

    with get_session() as session:
        # Query events without sentiment score that have actual values
        unscored = (
            session.query(EconomicEvent)
            .filter(
                EconomicEvent.sentiment_score.is_(None),
                EconomicEvent.actual.isnot(None),
            )
            .all()
        )

        for event in unscored:
            try:
                result = analyzer.analyze(event.to_dict_for_gemini())
                event.sentiment_score = result["sentiment_score"]
                event.raw_response = result["raw_response"]
                print(f"  {event.event_name}: {result['sentiment_score']:.2f}")
                analyzed_count += 1
            except Exception as e:
                logger.warning(f"Failed to analyze event {event.event_name}: {e}")
                continue

        if test_run:
            session.rollback()

    return analyzed_count


def scrape_reddit_posts(
    scraper: RedditScraper,
    mode: str = "hot",
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """Scrape Reddit posts from financial subreddits.

    Args:
        scraper: RedditScraper instance to use for scraping
        mode: Scraping mode - "hot", "new", or "top"
        limit: Maximum number of posts per subreddit

    Returns:
        List of post dictionaries containing post data

    Raises:
        ValueError: If an invalid mode is specified
    """
    valid_modes = ["hot", "new", "top"]

    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")

    if mode == "hot":
        return scraper.scrape_hot(limit=limit)
    elif mode == "new":
        return scraper.scrape_new(limit=limit)
    elif mode == "top":
        return scraper.scrape_top(limit=limit)

    return []


def store_reddit_posts(posts: List[Dict[str, Any]]) -> int:
    """Store scraped Reddit posts in the database.

    Uses merge (upsert) to handle both new and existing posts.

    Args:
        posts: List of post dictionaries to store

    Returns:
        Number of posts stored
    """
    if not posts:
        return 0

    stored_count = 0
    with get_session() as session:
        for post_data in posts:
            post = RedditPost.from_dict(post_data)
            session.merge(post)
            stored_count += 1

    return stored_count


def analyze_reddit_posts(
    analyzer: SentimentAnalyzer,
    test_run: bool = False,
) -> int:
    """Analyze Reddit posts that don't have sentiment scores.

    Queries posts that have content but no sentiment score,
    analyzes them using Gemini, and stores the results.

    Args:
        analyzer: SentimentAnalyzer instance to use for analysis
        test_run: If True, don't commit changes (rollback instead)

    Returns:
        Number of posts successfully analyzed
    """
    analyzed_count = 0

    with get_session() as session:
        # Query posts without sentiment score
        unscored = (
            session.query(RedditPost).filter(RedditPost.sentiment_score.is_(None)).all()
        )

        for post in unscored:
            try:
                result = analyzer.analyze(post.to_dict_for_gemini())
                post.sentiment_score = result["sentiment_score"]
                post.raw_response = result["raw_response"]
                print(f"  {post.title[:50]}: {result['sentiment_score']:.2f}")
                analyzed_count += 1
            except Exception as e:
                logger.warning(f"Failed to analyze post {post.title[:30]}: {e}")
                continue

        if test_run:
            session.rollback()

    return analyzed_count


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments.

    This is a convenience function that creates a parser and parses args.

    Args:
        args: List of command line arguments. If None, uses sys.argv.

    Returns:
        Parsed arguments as a Namespace object.
    """
    parser = create_parser()
    return parser.parse_args(args)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance with all supported arguments.
    """
    parser = argparse.ArgumentParser(
        prog="news-sentiment",
        description="News Sentiment Service - Scrape and analyze economic events",
    )

    parser.add_argument(
        "--scrape",
        choices=["today", "week", "month"],
        help="Scrape economic events for the specified period",
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze unscored events with sentiment analysis",
    )

    parser.add_argument(
        "--test-run",
        action="store_true",
        dest="test_run",
        help="Test run mode - do not commit changes to database",
    )

    # Reddit scraping arguments
    parser.add_argument(
        "--reddit",
        choices=["hot", "new", "top"],
        help="Scrape Reddit posts (hot, new, or top)",
    )

    parser.add_argument(
        "--reddit-limit",
        type=int,
        default=25,
        dest="reddit_limit",
        help="Number of posts per subreddit (default: 25)",
    )

    parser.add_argument(
        "--subreddits",
        nargs="+",
        help="Subreddits to scrape (default: financial subreddits)",
    )

    return parser


def main() -> int:
    """Run the main news sentiment pipeline.

    This is the primary entry point for the CLI.
    Orchestrates the complete pipeline: scrape -> store -> analyze.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    args = parser.parse_args()

    # If no action specified, show help and exit
    if not args.scrape and not args.analyze and not args.reddit:
        parser.print_help()
        return 0

    # Handle scraping
    if args.scrape:
        print(f"Scraping events for period: {args.scrape}")
        scraper = ForexFactoryScraper()
        events = scrape_events(scraper, period=args.scrape)
        print(f"Scraped {len(events)} events")

        if not args.test_run and events:
            print("Storing events in database...")
            stored = store_events(events)
            print(f"Stored {stored} events")
        elif args.test_run:
            print("Test run mode - skipping database storage")

    # Handle Reddit scraping
    if args.reddit:
        print(f"Scraping Reddit posts (mode: {args.reddit})")
        reddit_scraper = RedditScraper(subreddits=args.subreddits)
        posts = scrape_reddit_posts(
            reddit_scraper, mode=args.reddit, limit=args.reddit_limit
        )
        print(f"Scraped {len(posts)} posts")

        if not args.test_run and posts:
            print("Storing posts in database...")
            stored = store_reddit_posts(posts)
            print(f"Stored {stored} posts")
        elif args.test_run:
            print("Test run mode - skipping database storage")

    # Handle analysis
    if args.analyze:
        analyzer = SentimentAnalyzer()

        print("Analyzing unscored events...")
        analyzed_events = analyze_events(analyzer, test_run=args.test_run)
        print(f"Analyzed {analyzed_events} events")

        print("Analyzing unscored Reddit posts...")
        analyzed_posts = analyze_reddit_posts(analyzer, test_run=args.test_run)
        print(f"Analyzed {analyzed_posts} posts")

    print("Completed successfully")
    return 0


# Keep run() as alias for backwards compatibility
def run() -> None:
    """Run the main news sentiment pipeline (deprecated, use main()).

    This is kept for backwards compatibility.
    Orchestrates the complete pipeline: scrape -> store -> analyze.
    """
    main()


if __name__ == "__main__":
    sys.exit(main())
