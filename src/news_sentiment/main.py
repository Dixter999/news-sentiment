"""
Main entry point for the News Sentiment Service.

This module provides the primary CLI interface and orchestration
functions for the complete pipeline: Scrape -> Analyze -> Store.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List

from news_sentiment.analyzer.gemini import SentimentAnalyzer
from news_sentiment.database import EconomicEvent, get_session
from news_sentiment.scraper.ff_scraper import ForexFactoryScraper

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

    Args:
        events: List of event dictionaries to store

    Returns:
        Number of events stored
    """
    if not events:
        return 0

    with get_session() as session:
        for event_data in events:
            event = EconomicEvent.from_dict(event_data)
            session.merge(event)

    return len(events)


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
                event.raw_response = json.dumps(result["raw_response"])
                print(f"  {event.event_name}: {result['sentiment_score']:.2f}")
                analyzed_count += 1
            except Exception as e:
                logger.warning(f"Failed to analyze event {event.event_name}: {e}")
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
    if not args.scrape and not args.analyze:
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

    # Handle analysis
    if args.analyze:
        print("Analyzing unscored events...")
        analyzer = SentimentAnalyzer()
        analyzed = analyze_events(analyzer, test_run=args.test_run)
        print(f"Analyzed {analyzed} events")

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
