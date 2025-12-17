#!/usr/bin/env python3
"""Reprocess Reddit posts with images using multimodal analysis.

This script finds Reddit posts that:
1. Have image URLs (i.redd.it, imgur, etc.)
2. Have neutral/zero sentiment scores (likely analyzed without seeing the image)

And reprocesses them using the new multimodal analysis capability.
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_sentiment.analyzer.gemini import SentimentAnalyzer
from news_sentiment.database import get_session
from news_sentiment.database.models import RedditPost


def find_image_posts_to_reprocess(session, limit: int = 50):
    """Find image posts that need reprocessing.

    Finds posts with image URLs that have:
    - sentiment_score = 0.0 (neutral/not analyzed)
    - raw_response containing "no information" or similar
    """
    # Get posts with image URLs
    all_posts = session.query(RedditPost).filter(
        RedditPost.url.isnot(None),
        RedditPost.sentiment_score.isnot(None),
    ).all()

    analyzer = SentimentAnalyzer()

    # Filter to image posts with likely bad analysis
    posts_to_reprocess = []
    for post in all_posts:
        if not analyzer.is_image_url(post.url):
            continue

        # Check if it needs reprocessing
        # Score of 0.0 with generic reasoning usually means image wasn't analyzed
        if post.sentiment_score == 0.0:
            raw = post.raw_response or {}
            reasoning = raw.get("reasoning", "").lower()
            if any(phrase in reasoning for phrase in [
                "no information",
                "without any information",
                "impossible to determine",
                "neutral score is assigned",
            ]):
                posts_to_reprocess.append(post)

        if len(posts_to_reprocess) >= limit:
            break

    return posts_to_reprocess


def reprocess_posts(posts, analyzer: SentimentAnalyzer, dry_run: bool = False):
    """Reprocess posts with multimodal analysis."""
    reprocessed = 0

    for post in posts:
        print(f"\nReprocessing id={post.id}: {post.title[:50]}...")
        print(f"  URL: {post.url}")
        print(f"  Old score: {post.sentiment_score}")

        try:
            result = analyzer.analyze_reddit_post(post.to_dict_for_gemini())

            new_score = result["sentiment_score"]
            analyzed_image = result.get("analyzed_image", False)
            reasoning = result["raw_response"].get("reasoning", "")[:100]

            print(f"  New score: {new_score}")
            print(f"  Analyzed image: {analyzed_image}")
            print(f"  Reasoning: {reasoning}...")

            if not dry_run and not result["raw_response"].get("error"):
                post.sentiment_score = new_score
                post.raw_response = result["raw_response"]
                reprocessed += 1
                print(f"  -> Updated!")
            elif dry_run:
                print(f"  -> Dry run, not saving")
            else:
                print(f"  -> Error, skipping")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  -> Error: {e}")
            continue

    return reprocessed


def main():
    parser = argparse.ArgumentParser(
        description="Reprocess image posts with multimodal analysis"
    )
    parser.add_argument(
        "--limit", type=int, default=50,
        help="Maximum posts to reprocess (default: 50)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Don't save changes, just show what would be done"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("IMAGE POST REPROCESSOR (Multimodal Analysis)")
    print("=" * 60)

    analyzer = SentimentAnalyzer()

    with get_session() as session:
        print(f"\nFinding image posts to reprocess (limit: {args.limit})...")
        posts = find_image_posts_to_reprocess(session, args.limit)

        if not posts:
            print("No image posts found that need reprocessing.")
            return 0

        print(f"Found {len(posts)} posts to reprocess")

        if args.dry_run:
            print("\n[DRY RUN MODE - no changes will be saved]")

        reprocessed = reprocess_posts(posts, analyzer, args.dry_run)

        if not args.dry_run:
            session.commit()

        print(f"\n{'=' * 60}")
        print(f"Reprocessed {reprocessed} posts")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
