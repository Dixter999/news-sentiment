#!/usr/bin/env python3
"""Reprocess Reddit posts that were analyzed with the wrong template.

This script finds Reddit posts that were accidentally analyzed with the 
economic event template instead of the Reddit post template, and reprocesses
them with the correct template.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_sentiment.analyzer.gemini import SentimentAnalyzer
from news_sentiment.database import get_session
from news_sentiment.database.models import RedditPost, EconomicEvent


def find_reddit_posts_with_wrong_template(session, limit=None):
    """Find Reddit posts that were analyzed with the economic event template.
    
    These posts typically have reasoning mentioning economic indicators,
    actual vs forecast, impact levels, etc.
    """
    posts = session.query(RedditPost).filter(
        RedditPost.raw_response.isnot(None)
    ).all()
    
    posts_to_reprocess = []
    
    for post in posts:
        raw = post.raw_response or {}
        reasoning = raw.get('reasoning', '').lower()
        
        # Check for economic event template patterns
        if any(phrase in reasoning for phrase in [
            'no information provided about the event',
            'actual vs forecast',
            'actual value',
            'forecast value',
            'impact level',
            'previous value',
            'economic indicator',
            'economic event',
            'beat forecast',
            'missed forecast',
            'beat expectations',
            'missed expectations',
            'currency pair'
        ]):
            posts_to_reprocess.append(post)
            if limit and len(posts_to_reprocess) >= limit:
                break
    
    return posts_to_reprocess


def find_economic_events_to_reprocess(session):
    """Find economic events with missing sentiment scores.
    
    Returns events with IDs: 127, 132-134, 141, 148-149, 155-156
    """
    target_ids = [127, 132, 133, 134, 141, 148, 149, 155, 156]
    
    events = session.query(EconomicEvent).filter(
        EconomicEvent.id.in_(target_ids)
    ).all()
    
    return events


def reprocess_reddit_posts(posts, analyzer: SentimentAnalyzer, dry_run=False):
    """Reprocess Reddit posts with the correct template."""
    reprocessed = 0
    errors = 0
    
    print(f"\nReprocessing {len(posts)} Reddit posts...")
    
    for i, post in enumerate(posts, 1):
        print(f"\n[{i}/{len(posts)}] Reprocessing post ID {post.id}")
        print(f"  Title: {post.title[:80]}...")
        print(f"  Old score: {post.sentiment_score}")
        
        try:
            # Use the correct Reddit post analysis method
            result = analyzer.analyze_reddit_post(post.to_dict_for_gemini())
            
            new_score = result["sentiment_score"]
            reasoning = result["raw_response"].get("reasoning", "")[:150]
            
            print(f"  New score: {new_score}")
            print(f"  Reasoning: {reasoning}...")
            
            if not dry_run and not result["raw_response"].get("error"):
                post.sentiment_score = new_score
                post.raw_response = result["raw_response"]
                reprocessed += 1
                print("  ✓ Updated successfully")
            elif dry_run:
                print("  [DRY RUN] Would update")
            else:
                print(f"  ✗ Error in analysis: {result['raw_response'].get('error')}")
                errors += 1
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            errors += 1
            continue
    
    return reprocessed, errors


def reprocess_economic_events(events, analyzer: SentimentAnalyzer, dry_run=False):
    """Reprocess economic events."""
    reprocessed = 0
    errors = 0
    
    print(f"\nReprocessing {len(events)} economic events...")
    
    for i, event in enumerate(events, 1):
        print(f"\n[{i}/{len(events)}] Reprocessing event ID {event.id}")
        print(f"  Event: {event.event_name}")
        print(f"  Currency: {event.currency}")
        print(f"  Actual: {event.actual}, Forecast: {event.forecast}, Previous: {event.previous}")
        print(f"  Old score: {event.sentiment_score}")
        
        try:
            # Use the economic event analysis method
            result = analyzer.analyze(event.to_dict_for_gemini())
            
            new_score = result["sentiment_score"]
            reasoning = result["raw_response"].get("reasoning", "")[:150]
            
            print(f"  New score: {new_score}")
            print(f"  Reasoning: {reasoning}...")
            
            if not dry_run and not result["raw_response"].get("error"):
                event.sentiment_score = new_score
                event.raw_response = result["raw_response"]
                reprocessed += 1
                print("  ✓ Updated successfully")
            elif dry_run:
                print("  [DRY RUN] Would update")
            else:
                print(f"  ✗ Error in analysis: {result['raw_response'].get('error')}")
                errors += 1
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            errors += 1
            continue
    
    return reprocessed, errors


def save_checkpoint(checkpoint_file, processed_ids, task_type):
    """Save checkpoint to resume if interrupted."""
    checkpoint = {
        "task_type": task_type,
        "processed_ids": list(processed_ids),
        "timestamp": time.time()
    }
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f)


def load_checkpoint(checkpoint_file):
    """Load checkpoint if exists."""
    if Path(checkpoint_file).exists():
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Reprocess posts/events that were analyzed incorrectly"
    )
    parser.add_argument(
        "--task", 
        choices=["reddit", "events", "both"],
        default="both",
        help="Which task to perform (default: both)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of Reddit posts to reprocess"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save changes, just show what would be done"
    )
    parser.add_argument(
        "--checkpoint",
        default="scripts/.reprocess_checkpoint.json",
        help="Checkpoint file for resuming"
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("REPROCESSING INCORRECTLY ANALYZED POSTS")
    print("=" * 70)
    
    analyzer = SentimentAnalyzer()
    
    with get_session() as session:
        total_reprocessed = 0
        total_errors = 0
        
        # Reprocess Reddit posts
        if args.task in ["reddit", "both"]:
            print("\n" + "=" * 70)
            print("TASK: Reprocess Reddit posts with wrong template")
            print("=" * 70)
            
            posts = find_reddit_posts_with_wrong_template(session, args.limit)
            
            if posts:
                print(f"Found {len(posts)} Reddit posts to reprocess")
                
                if args.dry_run:
                    print("\n[DRY RUN MODE - No changes will be saved]")
                
                reprocessed, errors = reprocess_reddit_posts(posts, analyzer, args.dry_run)
                total_reprocessed += reprocessed
                total_errors += errors
                
                if not args.dry_run:
                    session.commit()
                    print(f"\n✓ Committed {reprocessed} Reddit post updates")
            else:
                print("No Reddit posts found that need reprocessing")
        
        # Reprocess economic events
        if args.task in ["events", "both"]:
            print("\n" + "=" * 70)
            print("TASK: Reprocess economic events with missing sentiment")
            print("=" * 70)
            
            events = find_economic_events_to_reprocess(session)
            
            if events:
                print(f"Found {len(events)} economic events to reprocess")
                
                if args.dry_run:
                    print("\n[DRY RUN MODE - No changes will be saved]")
                
                reprocessed, errors = reprocess_economic_events(events, analyzer, args.dry_run)
                total_reprocessed += reprocessed
                total_errors += errors
                
                if not args.dry_run:
                    session.commit()
                    print(f"\n✓ Committed {reprocessed} economic event updates")
            else:
                print("No economic events found that need reprocessing")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total items reprocessed: {total_reprocessed}")
        print(f"Total errors: {total_errors}")
        
        if args.dry_run:
            print("\n[This was a DRY RUN - no changes were saved]")
    
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())