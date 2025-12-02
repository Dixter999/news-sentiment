#!/usr/bin/env python3
"""
Reprocess Failed Reddit Sentiment Analysis.

Reprocesses Reddit posts that have error responses (e.g., from deprecated gemini-pro)
using the current gemini-2.0-flash model.

Usage:
    python scripts/reprocess_reddit_sentiment.py [--delay SECONDS]
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_sentiment.analyzer import SentimentAnalyzer
from news_sentiment.database import RedditPost, get_session


def get_failed_post_ids() -> list[int]:
    """Get IDs of Reddit posts that have error responses."""
    with get_session() as session:
        posts = session.query(RedditPost).filter(
            RedditPost.raw_response.isnot(None)
        ).all()

        failed_ids = []
        for post in posts:
            if post.raw_response and isinstance(post.raw_response, dict):
                if 'error' in post.raw_response:
                    failed_ids.append(post.id)

        return failed_ids


def get_post_for_analysis(post_id: int) -> dict | None:
    """Get post data for analysis."""
    with get_session() as session:
        post = session.query(RedditPost).filter(RedditPost.id == post_id).first()
        if post:
            return {
                'id': post.id,
                'subreddit': post.subreddit,
                'title': post.title,
                'data': post.to_dict_for_gemini()
            }
        return None


def update_post_sentiment(post_id: int, score: float, raw_response: dict) -> None:
    """Update a Reddit post with its sentiment score."""
    with get_session() as session:
        post = session.query(RedditPost).filter(RedditPost.id == post_id).first()
        if post:
            post.sentiment_score = score
            post.raw_response = raw_response
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
    """Reprocess failed Reddit posts with new model."""
    print("=" * 70)
    print("REPROCESS FAILED REDDIT SENTIMENT")
    print("=" * 70)
    print(f"Model: {model}")
    print(f"Delay: {delay}s between requests")
    print("=" * 70)

    post_ids = get_failed_post_ids()

    if not post_ids:
        print("\n✅ No failed Reddit posts to reprocess!")
        return

    print(f"Found {len(post_ids)} posts with errors to reprocess\n")

    try:
        analyzer = SentimentAnalyzer(model_name=model)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    processed = 0
    errors = 0
    start_time = datetime.now()

    try:
        for i, post_id in enumerate(post_ids, 1):
            post_info = get_post_for_analysis(post_id)
            if not post_info:
                continue

            title = post_info['title'][:50] + "..." if len(post_info['title']) > 50 else post_info['title']
            print(f"[{i:3}/{len(post_ids)}] r/{post_info['subreddit']} | {title}", end=" ")

            try:
                result = analyzer.analyze(post_info['data'])
                score = result["sentiment_score"]
                raw_response = result["raw_response"]

                if 'error' in raw_response:
                    errors += 1
                    print(f"| ❌ Still failing")
                else:
                    update_post_sentiment(post_id, score, raw_response)
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
        description="Reprocess failed Reddit sentiment analysis"
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
