#!/usr/bin/env python3
"""
Reprocess Reddit posts with failed image downloads.

This script identifies posts with sentiment_score = 0.0 that have
"no information" patterns in their reasoning, indicating failed image
downloads, and re-attempts analysis with the updated image download logic.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from sqlalchemy import and_
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from news_sentiment.analyzer import SentimentAnalyzer
from news_sentiment.database import get_session
from news_sentiment.database.models import RedditPost


# Patterns that indicate failed image analysis
NO_INFORMATION_PATTERNS = [
    "no information provided",
    "impossible to determine",
    "no information available", 
    "completely missing data",
    "post content is inaccessible",
    "without any information",
    "unable to analyze",
    "without the image content",
    "without seeing the actual",
    "image download failed",
    "failed to download",
    "could not load",
    "image unavailable"
]


def setup_logging(log_file: str) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_file: Path to log file
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger("reprocess_failed_images")
    logger.setLevel(logging.INFO)
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler for progress
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_failed_posts(session: Session) -> List[RedditPost]:
    """Query database for posts with sentiment_score = 0.0.
    
    Args:
        session: Database session
        
    Returns:
        List of RedditPost objects with 0.0 sentiment
    """
    return session.query(RedditPost).filter(
        RedditPost.sentiment_score == 0.0
    ).all()


def filter_no_information_posts(posts: List[RedditPost]) -> List[RedditPost]:
    """Filter posts that have 'no information' patterns in reasoning.
    
    Args:
        posts: List of RedditPost objects
        
    Returns:
        Filtered list containing only posts with problematic reasoning
    """
    filtered = []
    
    for post in posts:
        if not post.raw_response:
            continue
            
        reasoning = post.raw_response.get("reasoning", "").lower()
        
        # Check if any pattern matches
        if any(pattern in reasoning for pattern in NO_INFORMATION_PATTERNS):
            filtered.append(post)
    
    return filtered


def is_image_post(post: RedditPost) -> bool:
    """Check if a post has an image URL.
    
    Args:
        post: RedditPost object
        
    Returns:
        True if post URL is an image
    """
    if not post.url:
        return False
        
    # Common image extensions and domains
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
    image_domains = ('i.redd.it', 'i.imgur.com', 'imgur.com', 'preview.redd.it')
    
    url_lower = post.url.lower()
    
    # Check extensions
    if any(url_lower.endswith(ext) for ext in image_extensions):
        return True
    
    # Check domains
    if any(domain in url_lower for domain in image_domains):
        return True
    
    return False


def reprocess_post(
    post: RedditPost,
    analyzer: SentimentAnalyzer,
    session: Session
) -> bool:
    """Reprocess a single post with the updated analyzer.
    
    Args:
        post: RedditPost to reprocess
        analyzer: SentimentAnalyzer instance
        session: Database session
        
    Returns:
        True if reprocessing was successful, False otherwise
    """
    try:
        # Convert post to dict format expected by analyzer
        post_data = post.to_dict_for_gemini()
        
        # Re-analyze with updated logic
        result = analyzer.analyze_reddit_post(post_data)
        
        # Check if we got a better result
        new_score = result.get("sentiment_score", 0.0)
        new_reasoning = result.get("raw_response", {}).get("reasoning", "").lower()
        
        # Only update if we got a non-zero score OR if zero but with valid reasoning
        if new_score != 0.0 or (
            new_score == 0.0 and 
            new_reasoning and
            not any(pattern in new_reasoning for pattern in NO_INFORMATION_PATTERNS)
        ):
            # Update the post with new results
            post.sentiment_score = new_score
            post.raw_response = result.get("raw_response", {})
            post.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            return True
        else:
            # Still failing
            return False
            
    except Exception as e:
        logging.error(f"Error reprocessing post {post.reddit_id}: {e}")
        session.rollback()
        return False


def process_in_batches(
    posts: List[RedditPost],
    processor: Callable[[List[RedditPost]], int],
    batch_size: int = 10,
    limit: Optional[int] = None
) -> int:
    """Process posts in batches.
    
    Args:
        posts: List of posts to process
        processor: Function to process a batch
        batch_size: Size of each batch
        limit: Maximum total posts to process
        
    Returns:
        Total number of posts processed
    """
    total_processed = 0
    
    for i in range(0, len(posts), batch_size):
        if limit and total_processed >= limit:
            break
            
        batch_end = min(i + batch_size, len(posts))
        if limit:
            batch_end = min(batch_end, i + (limit - total_processed))
            
        batch = posts[i:batch_end]
        processed = processor(batch)
        total_processed += processed
        
    return total_processed


def print_dry_run_preview(posts: List[RedditPost]) -> None:
    """Print preview of what would be processed in dry-run mode.
    
    Args:
        posts: List of posts that would be processed
    """
    print("\n" + "="*60)
    print("DRY RUN MODE - No changes will be made")
    print("="*60)
    print(f"\nWould process {len(posts)} posts\n")
    
    # Show first few examples
    print("Example posts to be reprocessed:")
    print("-" * 40)
    
    for post in posts[:3]:
        print(f"ID: {post.reddit_id}")
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        if post.raw_response:
            reasoning = post.raw_response.get("reasoning", "")[:100]
            print(f"Current reasoning: {reasoning}...")
        print("-" * 40)
    
    if len(posts) > 3:
        print(f"... and {len(posts) - 3} more posts")


class ProgressTracker:
    """Track and display progress during reprocessing."""
    
    def __init__(self, total: int):
        """Initialize tracker.
        
        Args:
            total: Total number of items to process
        """
        self.total = total
        self.current = 0
        self.stats = {
            "total": total,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0
        }
        self.start_time = time.time()
    
    def update(self, success: bool) -> None:
        """Update progress.
        
        Args:
            success: Whether the current item was successful
        """
        self.current += 1
        
        if success:
            self.stats["successful"] += 1
        else:
            self.stats["failed"] += 1
        
        # Calculate success rate
        if self.current > 0:
            self.stats["success_rate"] = (
                self.stats["successful"] / self.current * 100
            )
        
        # Print progress
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        
        print(
            f"\rProgress: {self.current}/{self.total} "
            f"({self.stats['success_rate']:.1f}% success, "
            f"{rate:.1f} posts/sec)",
            end=""
        )
    
    def finish(self) -> None:
        """Finish tracking and print final line."""
        print()  # New line after progress


def print_statistics(stats: Dict[str, Any]) -> None:
    """Print final statistics.
    
    Args:
        stats: Dictionary of statistics
    """
    print("\n" + "="*60)
    print("REPROCESSING COMPLETE")
    print("="*60)
    
    print(f"\nTotal posts found: {stats.get('total_found', 0)}")
    print(f"Posts matching filter: {stats.get('filtered', 0)}")
    print(f"Posts processed: {stats.get('processed', 0)}")
    print(f"Successful: {stats.get('successful', 0)}")
    print(f"Failed: {stats.get('failed', 0)}")
    
    if stats.get('processed', 0) > 0:
        success_rate = stats.get('success_rate', 0.0)
        print(f"Success rate: {success_rate:.1f}%")
    
    if 'duration_seconds' in stats:
        duration = stats['duration_seconds']
        minutes = int(duration // 60)
        seconds = duration % 60
        print(f"Duration: {minutes}m {seconds:.1f}s")
    
    if stats.get('skipped', 0) > 0:
        print(f"Skipped (not image posts): {stats['skipped']}")


def run_reprocessing(
    session: Session,
    dry_run: bool = False,
    batch_size: int = 10,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Run the reprocessing workflow.
    
    Args:
        session: Database session
        dry_run: If True, preview only without making changes
        batch_size: Number of posts to process at once
        limit: Maximum number of posts to process
        
    Returns:
        Statistics dictionary
    """
    start_time = time.time()
    logger = logging.getLogger("reprocess_failed_images")
    
    # Query failed posts
    logger.info("Querying for posts with sentiment_score = 0.0...")
    all_failed_posts = get_failed_posts(session)
    logger.info(f"Found {len(all_failed_posts)} posts with 0.0 sentiment")
    
    # Filter for "no information" patterns
    logger.info("Filtering for 'no information' patterns...")
    filtered_posts = filter_no_information_posts(all_failed_posts)
    logger.info(f"Found {len(filtered_posts)} posts matching patterns")
    
    # Further filter for image posts
    image_posts = [p for p in filtered_posts if is_image_post(p)]
    logger.info(f"Found {len(image_posts)} image posts to reprocess")
    
    stats = {
        "total_found": len(all_failed_posts),
        "filtered": len(filtered_posts),
        "image_posts": len(image_posts),
        "would_process": len(image_posts),
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "skipped": len(filtered_posts) - len(image_posts)
    }
    
    if dry_run:
        print_dry_run_preview(image_posts)
        return stats
    
    # Initialize analyzer
    logger.info("Initializing sentiment analyzer...")
    try:
        analyzer = SentimentAnalyzer()
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        stats["error"] = str(e)
        return stats
    
    # Process posts
    if not image_posts:
        logger.info("No posts to reprocess")
        return stats
    
    logger.info(f"Starting reprocessing of {len(image_posts)} posts...")
    tracker = ProgressTracker(min(len(image_posts), limit or len(image_posts)))
    
    def process_batch(batch: List[RedditPost]) -> int:
        """Process a batch of posts."""
        processed = 0
        for post in batch:
            success = reprocess_post(post, analyzer, session)
            tracker.update(success)
            
            if success:
                stats["successful"] += 1
                logger.info(f"Successfully reprocessed {post.reddit_id}")
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to reprocess {post.reddit_id}")
            
            processed += 1
        
        return processed
    
    stats["processed"] = process_in_batches(
        image_posts, 
        process_batch, 
        batch_size, 
        limit
    )
    
    tracker.finish()
    
    # Calculate final statistics
    if stats["processed"] > 0:
        stats["success_rate"] = (
            stats["successful"] / stats["processed"] * 100
        )
    else:
        stats["success_rate"] = 0.0
    
    stats["duration_seconds"] = time.time() - start_time
    
    return stats


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: List of arguments (for testing)
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Reprocess Reddit posts with failed image downloads"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without making changes"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of posts to process in each batch (default: 10)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of posts to process (default: no limit)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default=f"reprocess_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        help="Path to log file (default: reprocess_TIMESTAMP.log)"
    )
    
    return parser.parse_args(args)


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(args.log_file)
    logger.info("Starting failed image reprocessing script")
    logger.info(f"Arguments: dry_run={args.dry_run}, batch_size={args.batch_size}, "
                f"limit={args.limit}, log_file={args.log_file}")
    
    # Run reprocessing
    try:
        with get_session() as session:
            stats = run_reprocessing(
                session,
                dry_run=args.dry_run,
                batch_size=args.batch_size,
                limit=args.limit
            )
            
            # Print statistics
            print_statistics(stats)
            
            # Log final statistics
            logger.info(f"Final statistics: {json.dumps(stats, indent=2)}")
            
            # Return success if we processed something
            if stats.get("error"):
                return 1
            return 0
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())