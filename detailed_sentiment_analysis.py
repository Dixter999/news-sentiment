#!/usr/bin/env python3
"""
Detailed analysis of null and zero sentiment scores with specific examples.
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
db_host = os.getenv("AI_MODEL_DB_HOST", "localhost")
db_port = os.getenv("AI_MODEL_DB_PORT", "5432")
db_name = os.getenv("AI_MODEL_DB_NAME", "ai_model")
db_user = os.getenv("AI_MODEL_DB_USER", "ai_model")
db_password = os.getenv("AI_MODEL_DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

def analyze_null_events_in_detail():
    """Get specific examples of null sentiment score events."""
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS: NULL SENTIMENT ECONOMIC EVENTS")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Check when these events were created vs when sentiment was supposed to be analyzed
        query = text("""
            SELECT 
                id,
                event_name,
                currency,
                impact,
                actual,
                forecast,
                previous,
                sentiment_score,
                raw_response,
                created_at,
                updated_at,
                timestamp as event_timestamp
            FROM economic_events
            WHERE sentiment_score IS NULL
            ORDER BY id
            LIMIT 10
        """)
        
        result = conn.execute(query)
        events = result.fetchall()
        
        print(f"\nAnalyzing {len(events)} events with null sentiment:")
        
        for event in events:
            print(f"\nEvent ID {event.id}:")
            print(f"  Name: {event.event_name}")
            print(f"  Currency: {event.currency}")
            print(f"  Impact: {event.impact}")
            print(f"  Event Time: {event.event_timestamp}")
            print(f"  Created: {event.created_at}")
            print(f"  Updated: {event.updated_at}")
            print(f"  Data: Actual={event.actual}, Forecast={event.forecast}, Previous={event.previous}")
            print(f"  Raw Response: {'None' if event.raw_response is None else 'Has data'}")
            
            # Check if this is a holiday or low-data event
            if "Bank Holiday" in str(event.event_name):
                print("  >> PATTERN: Bank Holiday - typically no market impact to analyze")
            elif not event.actual and not event.forecast:
                print("  >> PATTERN: No actual or forecast data - cannot analyze")
            elif event.raw_response is None:
                print("  >> PATTERN: Never attempted sentiment analysis (raw_response is None)")

def analyze_zero_score_patterns():
    """Analyze patterns in zero sentiment scores."""
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS: ZERO SENTIMENT REDDIT POSTS")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Get examples of each pattern
        patterns = [
            ("Minimal Content Posts", """
                SELECT id, reddit_id, title, body, url, sentiment_score, raw_response
                FROM reddit_posts
                WHERE sentiment_score = 0
                  AND LENGTH(COALESCE(body, '')) < 50
                ORDER BY created_at DESC
                LIMIT 3
            """),
            ("Image/Media Posts", """
                SELECT id, reddit_id, title, body, url, sentiment_score, raw_response
                FROM reddit_posts
                WHERE sentiment_score = 0
                  AND (url LIKE '%imgur.com%' OR url LIKE '%i.redd.it%' 
                       OR url LIKE '%.jpg' OR url LIKE '%.png' OR url LIKE '%.gif')
                ORDER BY created_at DESC
                LIMIT 3
            """),
            ("External Link Posts", """
                SELECT id, reddit_id, title, body, url, sentiment_score, raw_response
                FROM reddit_posts
                WHERE sentiment_score = 0
                  AND url IS NOT NULL
                  AND url NOT LIKE '%reddit.com%'
                  AND (body IS NULL OR body = '')
                ORDER BY created_at DESC
                LIMIT 3
            """),
            ("Normal Content Posts with Zero", """
                SELECT id, reddit_id, title, body, url, sentiment_score, raw_response
                FROM reddit_posts
                WHERE sentiment_score = 0
                  AND LENGTH(COALESCE(body, '')) >= 200
                ORDER BY created_at DESC
                LIMIT 3
            """)
        ]
        
        for pattern_name, query in patterns:
            print(f"\n{pattern_name}:")
            print("-" * 40)
            
            result = conn.execute(text(query))
            posts = result.fetchall()
            
            for post in posts:
                print(f"\nPost ID {post.id} (Reddit: {post.reddit_id}):")
                print(f"  Title: {post.title[:80]}...")
                print(f"  Body Length: {len(post.body) if post.body else 0} chars")
                if post.body and len(post.body) > 0:
                    print(f"  Body Preview: {post.body[:100]}...")
                print(f"  URL Type: {categorize_url(post.url)}")
                
                # Check raw_response for reasoning
                if post.raw_response:
                    try:
                        resp = post.raw_response if isinstance(post.raw_response, dict) else json.loads(post.raw_response)
                        if 'reasoning' in resp:
                            print(f"  Model Reasoning: {resp['reasoning'][:150]}...")
                        if 'error' in resp:
                            print(f"  ERROR: {resp['error'][:100]}...")
                    except:
                        pass

def categorize_url(url):
    """Categorize the type of URL."""
    if not url:
        return "No URL"
    elif "reddit.com" in url:
        return "Reddit post link"
    elif any(x in url for x in ["imgur.com", "i.redd.it", ".jpg", ".png", ".gif"]):
        return "Image/Media"
    elif any(x in url for x in ["reuters.com", "bloomberg.com", "cnbc.com", "foxbusiness.com"]):
        return "News article"
    else:
        return "External link"

def check_sentiment_analysis_timing():
    """Check when sentiment analysis was attempted."""
    print("\n" + "=" * 80)
    print("SENTIMENT ANALYSIS TIMING CHECK")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Check distribution of sentiment scores
        query = text("""
            SELECT 
                'economic_events' as table_name,
                COUNT(*) as total_records,
                COUNT(sentiment_score) as with_sentiment,
                COUNT(*) - COUNT(sentiment_score) as null_sentiment,
                COUNT(CASE WHEN sentiment_score = 0 THEN 1 END) as zero_sentiment,
                COUNT(CASE WHEN raw_response IS NOT NULL THEN 1 END) as has_raw_response
            FROM economic_events
            UNION ALL
            SELECT 
                'reddit_posts' as table_name,
                COUNT(*) as total_records,
                COUNT(sentiment_score) as with_sentiment,
                COUNT(*) - COUNT(sentiment_score) as null_sentiment,
                COUNT(CASE WHEN sentiment_score = 0 THEN 1 END) as zero_sentiment,
                COUNT(CASE WHEN raw_response IS NOT NULL THEN 1 END) as has_raw_response
            FROM reddit_posts
        """)
        
        result = conn.execute(query)
        stats = result.fetchall()
        
        print("\nSentiment Score Distribution:")
        for row in stats:
            print(f"\n{row.table_name}:")
            print(f"  Total Records: {row.total_records}")
            print(f"  With Sentiment: {row.with_sentiment} ({row.with_sentiment/row.total_records*100:.1f}%)")
            print(f"  Null Sentiment: {row.null_sentiment} ({row.null_sentiment/row.total_records*100:.1f}%)")
            print(f"  Zero Sentiment: {row.zero_sentiment} ({row.zero_sentiment/row.total_records*100:.1f}%)")
            print(f"  Has Raw Response: {row.has_raw_response}")
            print(f"  Never Analyzed: {row.total_records - row.has_raw_response}")

def main():
    """Run detailed analysis."""
    try:
        analyze_null_events_in_detail()
        analyze_zero_score_patterns()
        check_sentiment_analysis_timing()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()