#!/usr/bin/env python3
"""
EUR/USD Sentiment Monitor - Continuous scraping and sentiment updates.

Runs in a loop:
1. Scrapes Forex Factory economic events for EUR and USD
2. Scrapes Reddit for forex/economics content
3. Analyzes new content with Gemini
4. Displays updated EUR/USD sentiment
5. Waits for configured interval before next cycle
"""

import argparse
import signal
import sys
import time
from datetime import datetime

from news_sentiment.scraper import ForexFactoryScraper, RedditScraper
from news_sentiment.analyzer import SentimentAnalyzer
from news_sentiment.analyzer.forex_sentiment import get_forex_pair_sentiment
from news_sentiment.database import EconomicEvent, RedditPost, get_session


class EURUSDMonitor:
    """Continuous EUR/USD sentiment monitor."""

    # Error patterns that indicate retryable model errors
    MODEL_ERROR_PATTERNS = [
        "is not found for API version",
        "models/gemini-pro",
        "deprecated",
        "404",
    ]

    # Forex-focused subreddits
    FOREX_SUBREDDITS = [
        "Forex",
        "forex_trades",
        "ForexFactory",
        "Economics",
        "wallstreetbets",
    ]

    def __init__(self, interval_minutes: int = 30, reddit_limit: int = 25):
        self.interval_minutes = interval_minutes
        self.reddit_limit = reddit_limit
        self.running = True
        self.cycle_count = 0

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n[{self._timestamp()}] Received shutdown signal, finishing current cycle...")
        self.running = False

    def _timestamp(self) -> str:
        """Get current timestamp string in UTC."""
        from datetime import timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def _print_header(self):
        """Print monitor header."""
        print("=" * 70)
        print("EUR/USD SENTIMENT MONITOR")
        print(f"Interval: {self.interval_minutes} minutes | Reddit limit: {self.reddit_limit}/subreddit")
        print(f"Subreddits: {', '.join(self.FOREX_SUBREDDITS)}")
        print("Auto-reprocess: Enabled (detects and retries model errors)")
        print("=" * 70)
        print(f"[{self._timestamp()}] Monitor started. Press Ctrl+C to stop.\n")

    def _scrape_events(self) -> int:
        """Scrape economic events from Forex Factory."""
        try:
            with ForexFactoryScraper() as scraper:
                events = scraper.scrape_day()

            if not events:
                print(f"[{self._timestamp()}] No new events found")
                return 0

            # Filter for EUR and USD events only
            eur_usd_events = [e for e in events if e.get("currency") in ("EUR", "USD")]

            with get_session() as session:
                stored = 0
                updated = 0
                for event_data in eur_usd_events:
                    timestamp = event_data.get("timestamp")
                    event_name = event_data.get("event_name")
                    currency = event_data.get("currency")

                    if not all([timestamp, event_name, currency]):
                        continue

                    # Check if event already exists (unique constraint: timestamp, event_name, currency)
                    existing = (
                        session.query(EconomicEvent)
                        .filter(
                            EconomicEvent.timestamp == timestamp,
                            EconomicEvent.event_name == event_name,
                            EconomicEvent.currency == currency,
                        )
                        .first()
                    )

                    if existing:
                        # Update existing event with new actual/forecast/previous values
                        existing.actual = event_data.get("actual", existing.actual)
                        existing.forecast = event_data.get("forecast", existing.forecast)
                        existing.previous = event_data.get("previous", existing.previous)
                        existing.impact = event_data.get("impact", existing.impact)
                        updated += 1
                    else:
                        # Insert new event
                        event = EconomicEvent.from_dict(event_data)
                        session.add(event)
                        stored += 1

                session.commit()

            if stored > 0 or updated > 0:
                print(f"[{self._timestamp()}] Events: {stored} new, {updated} updated")
            else:
                print(f"[{self._timestamp()}] No new EUR/USD events")
            return stored

        except Exception as e:
            print(f"[{self._timestamp()}] Event scraping error: {e}")
            return 0

    def _scrape_reddit(self) -> int:
        """Scrape Reddit posts from forex subreddits."""
        try:
            with RedditScraper(subreddits=self.FOREX_SUBREDDITS) as scraper:
                posts = scraper.scrape_hot(limit=self.reddit_limit)

            if not posts:
                print(f"[{self._timestamp()}] No new Reddit posts found")
                return 0

            with get_session() as session:
                stored = 0
                for post_data in posts:
                    reddit_id = post_data.get("reddit_id")
                    if not reddit_id:
                        continue

                    # Check if post already exists
                    existing = (
                        session.query(RedditPost)
                        .filter(RedditPost.reddit_id == reddit_id)
                        .first()
                    )

                    if existing:
                        # Update existing post (keep sentiment_score if analyzed)
                        existing.score = post_data.get("score", existing.score)
                        existing.num_comments = post_data.get("num_comments", existing.num_comments)
                    else:
                        # Insert new post
                        post = RedditPost.from_dict(post_data)
                        session.add(post)
                        stored += 1

                session.commit()

            print(f"[{self._timestamp()}] Scraped {stored} new Reddit posts")
            return stored

        except Exception as e:
            print(f"[{self._timestamp()}] Reddit scraping error: {e}")
            return 0

    def _analyze_pending(self) -> int:
        """Analyze content that hasn't been scored yet."""
        try:
            analyzer = SentimentAnalyzer()
            analyzed = 0

            with get_session() as session:
                # Analyze unscored economic events (EUR/USD only)
                pending_events = session.query(EconomicEvent).filter(
                    EconomicEvent.sentiment_score.is_(None),
                    EconomicEvent.currency.in_(["EUR", "USD"])
                ).limit(20).all()

                for event in pending_events:
                    try:
                        result = analyzer.analyze(event.to_dict_for_gemini())
                        event.sentiment_score = result["sentiment_score"]
                        event.raw_response = result["raw_response"]
                        analyzed += 1
                        time.sleep(0.3)  # Rate limiting
                    except Exception as e:
                        print(f"[{self._timestamp()}] Event analysis error: {e}")

                # Analyze unscored Reddit posts
                pending_posts = session.query(RedditPost).filter(
                    RedditPost.sentiment_score.is_(None)
                ).limit(20).all()

                for post in pending_posts:
                    try:
                        result = analyzer.analyze(post.to_dict_for_gemini())
                        post.sentiment_score = result["sentiment_score"]
                        post.raw_response = result["raw_response"]
                        if "symbols" in result:
                            post.symbols = result["symbols"]
                        if "symbol_sentiments" in result:
                            post.symbol_sentiments = result["symbol_sentiments"]
                        analyzed += 1
                        time.sleep(0.3)  # Rate limiting
                    except Exception as e:
                        print(f"[{self._timestamp()}] Post analysis error: {e}")

                session.commit()

            if analyzed > 0:
                print(f"[{self._timestamp()}] Analyzed {analyzed} items")
            return analyzed

        except Exception as e:
            print(f"[{self._timestamp()}] Analysis error: {e}")
            return 0

    def _display_sentiment(self):
        """Display current EUR/USD sentiment."""
        try:
            result = get_forex_pair_sentiment("EURUSD", hours_back=168)  # 7 days

            if "error" in result:
                print(f"[{self._timestamp()}] Sentiment error: {result['error']}")
                return

            # Determine sentiment emoji and description
            score = result["sentiment"]
            if score > 0.3:
                emoji, desc = "🟢", "BULLISH"
            elif score < -0.3:
                emoji, desc = "🔴", "BEARISH"
            else:
                emoji, desc = "⚪", "NEUTRAL"

            base = result["base"]
            quote = result["quote"]

            print()
            print("-" * 70)
            print(f"{emoji} EUR/USD: {score:+.3f} ({desc})")
            print(f"   EUR: {base['sentiment']:+.3f} ({base['event_count']} events)")
            print(f"   USD: {quote['sentiment']:+.3f} ({quote['event_count']} events)")
            print(f"   Signal: {result['signal']}")
            print("-" * 70)
            print()

        except Exception as e:
            print(f"[{self._timestamp()}] Sentiment display error: {e}")

    def _is_model_error(self, raw_response: dict | None) -> bool:
        """Check if raw_response contains a retryable model error."""
        if not raw_response or not isinstance(raw_response, dict):
            return False

        error_msg = raw_response.get("error", "")
        if not error_msg:
            return False

        error_lower = error_msg.lower()
        return any(pattern.lower() in error_lower for pattern in self.MODEL_ERROR_PATTERNS)

    def _reprocess_failed(self) -> int:
        """Reprocess items that failed due to model errors."""
        try:
            analyzer = SentimentAnalyzer()
            reprocessed = 0

            with get_session() as session:
                # Find Reddit posts with model errors
                failed_posts = session.query(RedditPost).filter(
                    RedditPost.raw_response.isnot(None)
                ).limit(50).all()

                posts_to_retry = [
                    p for p in failed_posts
                    if self._is_model_error(p.raw_response)
                ]

                if posts_to_retry:
                    print(f"[{self._timestamp()}] Found {len(posts_to_retry)} posts with model errors, reprocessing...")

                for post in posts_to_retry:
                    try:
                        result = analyzer.analyze(post.to_dict_for_gemini())

                        # Only update if successful (no error in response)
                        if not result["raw_response"].get("error"):
                            post.sentiment_score = result["sentiment_score"]
                            post.raw_response = result["raw_response"]
                            reprocessed += 1
                            print(f"[{self._timestamp()}] ✓ Reprocessed post id={post.id}")
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"[{self._timestamp()}] Reprocess error (post {post.id}): {e}")

                # Find economic events with model errors
                failed_events = session.query(EconomicEvent).filter(
                    EconomicEvent.raw_response.isnot(None),
                    EconomicEvent.currency.in_(["EUR", "USD"])
                ).limit(50).all()

                events_to_retry = [
                    e for e in failed_events
                    if self._is_model_error(e.raw_response)
                ]

                if events_to_retry:
                    print(f"[{self._timestamp()}] Found {len(events_to_retry)} events with model errors, reprocessing...")

                for event in events_to_retry:
                    try:
                        result = analyzer.analyze(event.to_dict_for_gemini())

                        if not result["raw_response"].get("error"):
                            event.sentiment_score = result["sentiment_score"]
                            event.raw_response = result["raw_response"]
                            reprocessed += 1
                            print(f"[{self._timestamp()}] ✓ Reprocessed event id={event.id}")
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"[{self._timestamp()}] Reprocess error (event {event.id}): {e}")

                session.commit()

            if reprocessed > 0:
                print(f"[{self._timestamp()}] Reprocessed {reprocessed} failed items")
            return reprocessed

        except Exception as e:
            print(f"[{self._timestamp()}] Reprocess error: {e}")
            return 0

    def run_cycle(self):
        """Run a single monitoring cycle."""
        self.cycle_count += 1
        print(f"[{self._timestamp()}] === Cycle {self.cycle_count} ===")

        # Step 1: Scrape economic events
        self._scrape_events()

        # Step 2: Scrape Reddit
        self._scrape_reddit()

        # Step 3: Analyze pending content
        self._analyze_pending()

        # Step 4: Reprocess any failed model errors
        self._reprocess_failed()

        # Step 5: Display current sentiment
        self._display_sentiment()

    def run(self):
        """Run the continuous monitor."""
        self._print_header()

        while self.running:
            self.run_cycle()

            if not self.running:
                break

            # Wait for next cycle
            print(f"[{self._timestamp()}] Next update in {self.interval_minutes} minutes...")

            # Sleep in small increments to allow quick shutdown
            for _ in range(self.interval_minutes * 60):
                if not self.running:
                    break
                time.sleep(1)

        print(f"\n[{self._timestamp()}] Monitor stopped after {self.cycle_count} cycles.")


def main():
    parser = argparse.ArgumentParser(
        description="EUR/USD Sentiment Monitor - Continuous updates"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Update interval in minutes (default: 30)"
    )
    parser.add_argument(
        "--reddit-limit",
        type=int,
        default=25,
        help="Reddit posts per subreddit (default: 25)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't loop)"
    )

    args = parser.parse_args()

    monitor = EURUSDMonitor(
        interval_minutes=args.interval,
        reddit_limit=args.reddit_limit
    )

    if args.once:
        monitor.run_cycle()
    else:
        monitor.run()


if __name__ == "__main__":
    main()
