#!/usr/bin/env python3
"""
Batch Sentiment Analysis for Historical Economic Events.

Analyzes sentiment for all economic events that don't have a sentiment score.
Uses Gemini 2.0 Flash for fast, cost-effective analysis.

Usage:
    python scripts/analyze_historical_sentiment.py [--batch-size N] [--delay SECONDS]

Resume from where it left off automatically (only analyzes events without scores).
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_sentiment.analyzer import SentimentAnalyzer
from news_sentiment.database import EconomicEvent, get_session


def get_unanalyzed_events(limit: int = 100) -> list[EconomicEvent]:
    """Get events that don't have sentiment scores."""
    with get_session() as session:
        events = session.query(EconomicEvent).filter(
            EconomicEvent.sentiment_score.is_(None),
            EconomicEvent.timestamp >= "2022-01-01"
        ).order_by(EconomicEvent.timestamp).limit(limit).all()

        # Detach from session for use outside
        for event in events:
            session.expunge(event)

        return events


def update_event_sentiment(event_id: int, score: float, raw_response: dict) -> None:
    """Update an event with its sentiment score."""
    with get_session() as session:
        event = session.query(EconomicEvent).filter(EconomicEvent.id == event_id).first()
        if event:
            event.sentiment_score = score
            event.raw_response = raw_response
            session.commit()


def format_score(score: float) -> str:
    """Format score with color indicator."""
    if score > 0.3:
        return f"🟢 +{score:.2f}"
    elif score < -0.3:
        return f"🔴 {score:.2f}"
    else:
        return f"⚪ {score:+.2f}"


def analyze_batch(
    batch_size: int = 50,
    delay: float = 0.5,
    model: str = "gemini-2.0-flash",
) -> None:
    """
    Run batch sentiment analysis.

    Args:
        batch_size: Number of events to process before committing
        delay: Delay between API calls (seconds)
        model: Gemini model to use
    """
    print("=" * 70)
    print("HISTORICAL SENTIMENT ANALYSIS")
    print("=" * 70)
    print(f"Model: {model}")
    print(f"Batch size: {batch_size}")
    print(f"Delay: {delay}s between requests")
    print("=" * 70)

    # Initialize analyzer
    try:
        analyzer = SentimentAnalyzer(model_name=model)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    total_analyzed = 0
    total_errors = 0
    start_time = datetime.now()

    try:
        while True:
            # Get next batch of unanalyzed events
            events = get_unanalyzed_events(limit=batch_size)

            if not events:
                print("\n✅ All events have been analyzed!")
                break

            print(f"\nProcessing batch of {len(events)} events...")

            for i, event in enumerate(events, 1):
                event_desc = f"{event.event_name[:40]}..." if len(event.event_name) > 40 else event.event_name
                print(f"[{total_analyzed + i:5}] {event.currency:3} | {event_desc}", end=" ")

                try:
                    # Prepare event data for analysis
                    event_data = {
                        "event_name": event.event_name,
                        "currency": event.currency,
                        "impact": event.impact,
                        "actual": event.actual,
                        "forecast": event.forecast,
                        "previous": event.previous,
                    }

                    # Analyze
                    result = analyzer.analyze(event_data)
                    score = result["sentiment_score"]
                    raw_response = result["raw_response"]

                    # Update database
                    update_event_sentiment(event.id, score, raw_response)

                    print(f"| {format_score(score)}")

                except Exception as e:
                    total_errors += 1
                    print(f"| ❌ Error: {str(e)[:30]}")

                # Rate limiting
                time.sleep(delay)

            total_analyzed += len(events)

            # Progress update
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = total_analyzed / elapsed if elapsed > 0 else 0
            print(f"\n--- Progress: {total_analyzed} analyzed, {total_errors} errors, {rate:.1f}/sec ---")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")

    finally:
        elapsed = (datetime.now() - start_time).total_seconds()
        print()
        print("=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"Total analyzed: {total_analyzed}")
        print(f"Errors: {total_errors}")
        print(f"Time elapsed: {elapsed:.1f}s")
        if total_analyzed > 0:
            print(f"Average rate: {total_analyzed / elapsed:.2f} events/sec")


def main():
    parser = argparse.ArgumentParser(
        description="Batch sentiment analysis for historical economic events"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of events per batch (default: 50)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Delay between API calls in seconds (default: 0.3)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.0-flash",
        help="Gemini model to use (default: gemini-2.0-flash)",
    )

    args = parser.parse_args()

    analyze_batch(
        batch_size=args.batch_size,
        delay=args.delay,
        model=args.model,
    )


if __name__ == "__main__":
    main()
