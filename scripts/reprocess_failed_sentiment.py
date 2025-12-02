#!/usr/bin/env python3
"""
Reprocess Failed Sentiment Analysis.

Reprocesses events that have error responses (e.g., from deprecated gemini-pro)
using the current gemini-2.0-flash model.

Usage:
    python scripts/reprocess_failed_sentiment.py [--delay SECONDS]
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


def get_failed_events() -> list[EconomicEvent]:
    """Get events that have error responses."""
    with get_session() as session:
        events = session.query(EconomicEvent).filter(
            EconomicEvent.timestamp >= "2022-01-01",
            EconomicEvent.raw_response.isnot(None)
        ).all()

        failed = []
        for event in events:
            if event.raw_response and isinstance(event.raw_response, dict):
                if 'error' in event.raw_response:
                    session.expunge(event)
                    failed.append(event)

        return failed


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


def reprocess(delay: float = 0.3, model: str = "gemini-2.0-flash") -> None:
    """Reprocess failed events with new model."""
    print("=" * 70)
    print("REPROCESS FAILED SENTIMENT ANALYSIS")
    print("=" * 70)
    print(f"Model: {model}")
    print(f"Delay: {delay}s between requests")
    print("=" * 70)

    # Get failed events
    events = get_failed_events()

    if not events:
        print("\n✅ No failed events to reprocess!")
        return

    print(f"Found {len(events)} events with errors to reprocess\n")

    # Initialize analyzer
    try:
        analyzer = SentimentAnalyzer(model_name=model)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    processed = 0
    errors = 0
    start_time = datetime.now()

    try:
        for i, event in enumerate(events, 1):
            event_desc = f"{event.event_name[:40]}..." if len(event.event_name) > 40 else event.event_name
            print(f"[{i:3}/{len(events)}] ID {event.id:5} | {event.currency:3} | {event_desc}", end=" ")

            try:
                event_data = {
                    "event_name": event.event_name,
                    "currency": event.currency,
                    "impact": event.impact,
                    "actual": event.actual,
                    "forecast": event.forecast,
                    "previous": event.previous,
                }

                result = analyzer.analyze(event_data)
                score = result["sentiment_score"]
                raw_response = result["raw_response"]

                # Check if new result also has error
                if 'error' in raw_response:
                    errors += 1
                    print(f"| ❌ Still failing: {str(raw_response.get('error', ''))[:30]}")
                else:
                    update_event_sentiment(event.id, score, raw_response)
                    processed += 1
                    print(f"| {format_score(score)}")

            except Exception as e:
                errors += 1
                print(f"| ❌ Error: {str(e)[:30]}")

            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")

    finally:
        elapsed = (datetime.now() - start_time).total_seconds()
        print()
        print("=" * 70)
        print("REPROCESSING COMPLETE")
        print("=" * 70)
        print(f"Successfully reprocessed: {processed}")
        print(f"Still failing: {errors}")
        print(f"Time elapsed: {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description="Reprocess failed sentiment analysis with new model"
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
    reprocess(delay=args.delay, model=args.model)


if __name__ == "__main__":
    main()
