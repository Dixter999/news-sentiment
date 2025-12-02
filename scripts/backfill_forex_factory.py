#!/usr/bin/env python3
"""
ForexFactory Historical Data Backfill Script.

Collects 3 years of economic calendar data (Jan 2022 - Dec 2024)
for PPO/SAC trading model training.

Usage:
    python scripts/backfill_forex_factory.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]

Resume from checkpoint:
    python scripts/backfill_forex_factory.py --resume
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_sentiment.scraper import ForexFactoryScraper
from news_sentiment.database import EconomicEvent, get_session


CHECKPOINT_FILE = Path(__file__).parent / ".backfill_checkpoint.json"


def load_checkpoint() -> dict:
    """Load checkpoint from file."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {}


def save_checkpoint(data: dict) -> None:
    """Save checkpoint to file."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_monday_of_week(date: datetime) -> datetime:
    """Get the Monday of the week containing the given date."""
    days_since_monday = date.weekday()
    return date - timedelta(days=days_since_monday)


def generate_weeks(start_date: datetime, end_date: datetime) -> list[datetime]:
    """Generate list of week start dates (Mondays) between start and end."""
    weeks = []
    current = get_monday_of_week(start_date)
    end_monday = get_monday_of_week(end_date)

    while current <= end_monday:
        weeks.append(current)
        current += timedelta(weeks=1)

    return weeks


def week_exists_in_db(week_start: datetime) -> bool:
    """Check if data for a week already exists in database."""
    week_end = week_start + timedelta(days=7)

    with get_session() as session:
        count = session.query(EconomicEvent).filter(
            EconomicEvent.timestamp >= week_start,
            EconomicEvent.timestamp < week_end
        ).count()
        return count > 0


def save_events_to_db(events: list[dict], week_start: datetime) -> int:
    """Save scraped events to database. Returns count of new events."""
    saved = 0

    with get_session() as session:
        for event_data in events:
            # Skip events without timestamp
            if not event_data.get("timestamp"):
                continue

            # Check for duplicate (same timestamp + event_name + currency)
            existing = session.query(EconomicEvent).filter(
                EconomicEvent.timestamp == event_data["timestamp"],
                EconomicEvent.event_name == event_data["event_name"],
                EconomicEvent.currency == event_data.get("currency", "")
            ).first()

            if existing:
                continue

            event = EconomicEvent.from_dict(event_data)
            session.add(event)
            saved += 1

        session.commit()

    return saved


def backfill(
    start_date: datetime,
    end_date: datetime,
    resume: bool = False,
    delay_range: tuple[float, float] = (8.0, 15.0),
) -> None:
    """
    Run the backfill process.

    Args:
        start_date: Start date for backfill
        end_date: End date for backfill
        resume: Whether to resume from checkpoint
        delay_range: Min/max delay between requests (seconds)
    """
    weeks = generate_weeks(start_date, end_date)
    total_weeks = len(weeks)

    print("=" * 70)
    print("FOREXFACTORY HISTORICAL BACKFILL")
    print("=" * 70)
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Total weeks: {total_weeks}")
    print(f"Delay range: {delay_range[0]}-{delay_range[1]}s")
    print("=" * 70)

    # Load checkpoint if resuming
    checkpoint = load_checkpoint() if resume else {}
    completed_weeks = set(checkpoint.get("completed_weeks", []))

    if completed_weeks:
        print(f"Resuming from checkpoint: {len(completed_weeks)} weeks already done")

    # Filter out completed weeks
    pending_weeks = [w for w in weeks if w.isoformat() not in completed_weeks]

    if not pending_weeks:
        print("All weeks already completed!")
        return

    print(f"Weeks to process: {len(pending_weeks)}")
    print()

    total_events = checkpoint.get("total_events", 0)
    errors = 0  # Reset errors on resume
    consecutive_errors = 0

    try:
        for i, week_start in enumerate(pending_weeks, 1):
            week_str = week_start.strftime("%Y-%m-%d")

            # Check if already in DB
            if week_exists_in_db(week_start):
                print(f"[{i:3}/{len(pending_weeks)}] {week_str} - Already in DB, skipping")
                completed_weeks.add(week_start.isoformat())
                continue

            print(f"[{i:3}/{len(pending_weeks)}] {week_str} - Scraping...", end=" ", flush=True)

            # Create fresh scraper for each request to avoid Cloudflare fingerprinting
            scraper = ForexFactoryScraper(
                headless=True,
                timeout=90000,  # 90 second timeout
                rate_limit_delay=delay_range[0],
            )

            try:
                events = scraper.scrape_week(week_start)
                saved = save_events_to_db(events, week_start)
                total_events += saved

                print(f"OK ({saved} events saved, {total_events} total)")

                completed_weeks.add(week_start.isoformat())
                consecutive_errors = 0  # Reset on success

            except Exception as e:
                errors += 1
                consecutive_errors += 1
                print(f"ERROR: {str(e)[:50]}")

                # On error, save checkpoint
                save_checkpoint({
                    "completed_weeks": list(completed_weeks),
                    "total_events": total_events,
                    "errors": errors,
                    "last_error": str(e),
                    "last_error_week": week_str,
                    "updated_at": datetime.now().isoformat(),
                })

                # Exponential backoff based on consecutive errors
                backoff = min(300, 30 * (2 ** min(consecutive_errors - 1, 3)))
                print(f"         Backing off for {backoff}s (consecutive errors: {consecutive_errors})...")
                time.sleep(backoff)

                # If too many consecutive errors, abort
                if consecutive_errors >= 5:
                    print("\n⚠️  Too many consecutive errors. Cloudflare may be blocking.")
                    print("    Try again later or use a VPN/different IP.")
                    break

            finally:
                scraper.close()

            # Save checkpoint every 5 weeks
            if len(completed_weeks) % 5 == 0:
                save_checkpoint({
                    "completed_weeks": list(completed_weeks),
                    "total_events": total_events,
                    "errors": errors,
                    "updated_at": datetime.now().isoformat(),
                })
                print(f"         --- Checkpoint saved ({len(completed_weeks)}/{total_weeks} weeks) ---")

            # Longer random delay to avoid detection
            delay = random.uniform(delay_range[0], delay_range[1])
            print(f"         Waiting {delay:.1f}s before next request...")
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving checkpoint...")

    finally:
        # Final checkpoint save
        save_checkpoint({
            "completed_weeks": list(completed_weeks),
            "total_events": total_events,
            "errors": errors,
            "updated_at": datetime.now().isoformat(),
        })

    print()
    print("=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)
    print(f"Weeks processed: {len(completed_weeks)}/{total_weeks}")
    print(f"Total events saved: {total_events}")
    print(f"Errors encountered: {errors}")
    print(f"Checkpoint: {CHECKPOINT_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill ForexFactory economic calendar data"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2022-01-01",
        help="Start date (YYYY-MM-DD), default: 2022-01-01",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="End date (YYYY-MM-DD), default: 2024-12-31",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=8.0,
        help="Minimum delay between requests (seconds)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=15.0,
        help="Maximum delay between requests (seconds)",
    )

    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    backfill(
        start_date=start_date,
        end_date=end_date,
        resume=args.resume,
        delay_range=(args.min_delay, args.max_delay),
    )


if __name__ == "__main__":
    main()
