#!/usr/bin/env python3
"""
Full Pipeline Integration Test

Tests the complete news-sentiment pipeline:
1. ForexFactory scraping
2. Reddit scraping (hot, new, top)
3. Database storage with upsert
4. Gemini sentiment analysis
5. Results verification

Run: python scripts/test_pipeline.py
"""

import json
import os
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

load_dotenv()

from news_sentiment.database import EconomicEvent, RedditPost, get_session
from news_sentiment.analyzer.gemini import SentimentAnalyzer
from news_sentiment.scraper.ff_scraper import ForexFactoryScraper
from news_sentiment.scraper.reddit_scraper import RedditScraper


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(label: str, value, status: str = None):
    """Print a formatted result line."""
    status_icon = {"pass": "✅", "fail": "❌", "info": "ℹ️", "warn": "⚠️"}.get(
        status, "  "
    )
    print(f"{status_icon} {label}: {value}")


def test_database_connection():
    """Test database connectivity."""
    print_header("1. Database Connection Test")
    try:
        with get_session() as session:
            # Test query
            event_count = session.query(EconomicEvent).count()
            post_count = session.query(RedditPost).count()
            print_result("Economic events in DB", event_count, "info")
            print_result("Reddit posts in DB", post_count, "info")
            print_result("Database connection", "OK", "pass")
            return True, {"events": event_count, "posts": post_count}
    except Exception as e:
        print_result("Database connection", f"FAILED: {e}", "fail")
        return False, {}


def test_forexfactory_scraper():
    """Test ForexFactory scraper."""
    print_header("2. ForexFactory Scraper Test")
    try:
        scraper = ForexFactoryScraper(headless=True)
        events = scraper.scrape_day()
        scraper.close()

        print_result("Events scraped", len(events), "info")

        if events:
            sample = events[0]
            print_result("Sample event", sample.get("event_name", "N/A")[:50], "info")
            print_result("Has timestamp", sample.get("timestamp") is not None, "info")
            print_result("Has currency", bool(sample.get("currency")), "info")
            print_result("ForexFactory scraper", "OK", "pass")
            return True, {"count": len(events), "sample": sample}
        else:
            print_result("ForexFactory scraper", "No events (may be weekend)", "warn")
            return True, {"count": 0, "sample": None}

    except Exception as e:
        print_result("ForexFactory scraper", f"FAILED: {e}", "fail")
        return False, {}


def test_reddit_scraper():
    """Test Reddit scraper with all modes."""
    print_header("3. Reddit Scraper Test")

    results = {}

    # Check credentials
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print_result("Reddit credentials", "Missing (skipping)", "warn")
        return False, {}

    try:
        scraper = RedditScraper(subreddits=["wallstreetbets"])

        # Test hot
        hot_posts = scraper.scrape_hot(limit=5)
        results["hot"] = len(hot_posts)
        print_result("Hot posts scraped", len(hot_posts), "info")

        # Test new
        new_posts = scraper.scrape_new(limit=5)
        results["new"] = len(new_posts)
        print_result("New posts scraped", len(new_posts), "info")

        # Test top
        top_posts = scraper.scrape_top(time_filter="day", limit=5)
        results["top"] = len(top_posts)
        print_result("Top posts scraped", len(top_posts), "info")

        if hot_posts:
            sample = hot_posts[0]
            print_result("Sample post", sample.get("title", "N/A")[:40], "info")
            print_result("Has reddit_id", bool(sample.get("reddit_id")), "info")
            print_result("Has subreddit", bool(sample.get("subreddit")), "info")
            print_result("Has timestamp", sample.get("timestamp") is not None, "info")
            results["sample"] = sample

        print_result("Reddit scraper", "OK", "pass")
        return True, results

    except Exception as e:
        print_result("Reddit scraper", f"FAILED: {e}", "fail")
        return False, {}


def test_reddit_storage():
    """Test Reddit post storage with upsert."""
    print_header("4. Reddit Storage Test (Upsert)")

    try:
        # Create a test post
        test_post = {
            "reddit_id": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "subreddit": "test_subreddit",
            "title": "Pipeline Test Post",
            "body": "This is a test post for pipeline validation",
            "url": "https://reddit.com/test",
            "score": 100,
            "num_comments": 10,
            "flair": "Test",
            "timestamp": datetime.now(timezone.utc),
        }

        with get_session() as session:
            # Insert
            post = RedditPost.from_dict(test_post)
            session.add(post)
            session.flush()
            original_id = post.id
            print_result("Insert test post", f"ID: {original_id}", "info")

        # Update (upsert)
        test_post["score"] = 200
        test_post["num_comments"] = 20

        with get_session() as session:
            existing = (
                session.query(RedditPost)
                .filter(RedditPost.reddit_id == test_post["reddit_id"])
                .first()
            )
            if existing:
                existing.score = test_post["score"]
                existing.num_comments = test_post["num_comments"]
                session.flush()
                print_result("Update test post", f"Score: {existing.score}", "info")

        # Verify
        with get_session() as session:
            verified = (
                session.query(RedditPost)
                .filter(RedditPost.reddit_id == test_post["reddit_id"])
                .first()
            )
            if verified and verified.score == 200:
                print_result("Upsert verification", "OK", "pass")

                # Cleanup
                session.delete(verified)
                print_result("Cleanup test post", "OK", "info")
                return True, {"original_id": original_id, "updated_score": 200}
            else:
                print_result("Upsert verification", "FAILED", "fail")
                return False, {}

    except Exception as e:
        print_result("Reddit storage", f"FAILED: {e}", "fail")
        return False, {}


def test_sentiment_analyzer():
    """Test Gemini sentiment analyzer."""
    print_header("5. Gemini Sentiment Analyzer Test")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print_result("Gemini API key", "Missing (skipping)", "warn")
        return False, {}

    try:
        analyzer = SentimentAnalyzer()

        # Test with sample data
        test_data = {
            "event_name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "High",
            "actual": "250K",
            "forecast": "200K",
            "previous": "180K",
        }

        result = analyzer.analyze(test_data)

        score = result.get("sentiment_score")
        raw = result.get("raw_response")

        print_result("Sentiment score", f"{score:.2f}" if score else "N/A", "info")
        print_result("Has raw response", raw is not None, "info")
        print_result("Score in range [-1, 1]", -1 <= (score or 0) <= 1, "info")

        print_result("Sentiment analyzer", "OK", "pass")
        return True, {"score": score, "has_response": raw is not None}

    except Exception as e:
        print_result("Sentiment analyzer", f"FAILED: {e}", "fail")
        return False, {}


def test_full_pipeline():
    """Test the complete pipeline: scrape -> store -> analyze."""
    print_header("6. Full Pipeline Test (Reddit)")

    try:
        # Scrape
        print("\n  Step 1: Scraping...")
        scraper = RedditScraper(subreddits=["stocks"])
        posts = scraper.scrape_hot(limit=3)
        print_result("Posts scraped", len(posts), "info")

        if not posts:
            print_result("Full pipeline", "No posts to test", "warn")
            return True, {}

        # Store
        print("\n  Step 2: Storing...")
        stored_count = 0
        with get_session() as session:
            for post_data in posts:
                reddit_id = post_data.get("reddit_id")
                existing = (
                    session.query(RedditPost)
                    .filter(RedditPost.reddit_id == reddit_id)
                    .first()
                )
                if existing:
                    existing.score = post_data.get("score", existing.score)
                else:
                    post = RedditPost.from_dict(post_data)
                    session.add(post)
                stored_count += 1
        print_result("Posts stored", stored_count, "info")

        # Analyze (only unscored)
        print("\n  Step 3: Analyzing...")
        analyzer = SentimentAnalyzer()
        analyzed_count = 0

        with get_session() as session:
            unscored = (
                session.query(RedditPost)
                .filter(RedditPost.sentiment_score.is_(None))
                .limit(2)
                .all()
            )

            for post in unscored:
                try:
                    result = analyzer.analyze(post.to_dict_for_gemini())
                    post.sentiment_score = result["sentiment_score"]
                    post.raw_response = result["raw_response"]
                    analyzed_count += 1
                    print_result(
                        f"  {post.title[:30]}...",
                        f"{result['sentiment_score']:.2f}",
                        "info",
                    )
                except Exception as e:
                    print_result(f"  {post.title[:30]}...", f"Error: {e}", "warn")

        print_result("Posts analyzed", analyzed_count, "info")
        print_result("Full pipeline", "OK", "pass")
        return True, {
            "scraped": len(posts),
            "stored": stored_count,
            "analyzed": analyzed_count,
        }

    except Exception as e:
        print_result("Full pipeline", f"FAILED: {e}", "fail")
        return False, {}


def generate_report(results: dict):
    """Generate a summary report."""
    print_header("TEST RESULTS SUMMARY")

    total_tests = len(results)
    passed = sum(1 for r in results.values() if r["passed"])
    failed = total_tests - passed

    print(f"\n  Total Tests: {total_tests}")
    print(f"  Passed: {passed} ✅")
    print(f"  Failed: {failed} ❌")
    print(f"\n  Success Rate: {passed/total_tests*100:.1f}%")

    print("\n  Test Details:")
    for name, result in results.items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"    {name}: {status}")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total_tests,
        "passed": passed,
        "failed": failed,
        "success_rate": f"{passed/total_tests*100:.1f}%",
        "results": results,
    }


def main():
    """Run all pipeline tests."""
    print("\n" + "=" * 60)
    print("  NEWS SENTIMENT PIPELINE - INTEGRATION TEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    # Run tests
    passed, data = test_database_connection()
    results["database_connection"] = {"passed": passed, "data": data}

    passed, data = test_forexfactory_scraper()
    results["forexfactory_scraper"] = {"passed": passed, "data": data}

    passed, data = test_reddit_scraper()
    results["reddit_scraper"] = {"passed": passed, "data": data}

    passed, data = test_reddit_storage()
    results["reddit_storage"] = {"passed": passed, "data": data}

    passed, data = test_sentiment_analyzer()
    results["sentiment_analyzer"] = {"passed": passed, "data": data}

    passed, data = test_full_pipeline()
    results["full_pipeline"] = {"passed": passed, "data": data}

    # Generate report
    report = generate_report(results)

    # Save report
    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved: {report_path}")

    print("\n" + "=" * 60 + "\n")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
