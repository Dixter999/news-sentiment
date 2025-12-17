#!/usr/bin/env python3
"""
Analyze null and zero sentiment scores in the database.
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Database connection
db_host = os.getenv("AI_MODEL_DB_HOST", "localhost")
db_port = os.getenv("AI_MODEL_DB_PORT", "5432")
db_name = os.getenv("AI_MODEL_DB_NAME", "ai_model")
db_user = os.getenv("AI_MODEL_DB_USER", "ai_model")
db_password = os.getenv("AI_MODEL_DB_PASSWORD", "")

# Create database URL
DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def analyze_economic_events():
    """Analyze economic events with null sentiment scores."""
    print("=" * 80)
    print("ANALYZING ECONOMIC EVENTS WITH NULL SENTIMENT SCORES")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Get events with null sentiment scores
        query = text("""
            SELECT id, timestamp, currency, event_name, impact, actual, forecast, previous,
                   sentiment_score, raw_response, created_at
            FROM economic_events
            WHERE sentiment_score IS NULL
               OR id IN (126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 141, 148, 149, 154, 155, 156, 158, 159)
            ORDER BY id
            LIMIT 20
        """)
        
        result = conn.execute(query)
        events = result.fetchall()
        
        print(f"\nFound {len(events)} economic events with null sentiment scores")
        print()
        
        error_patterns = {}
        
        for row in events:
            print(f"ID: {row.id}")
            print(f"  Event: {row.event_name}")
            print(f"  Currency: {row.currency}")
            print(f"  Impact: {row.impact}")
            print(f"  Actual: {row.actual}, Forecast: {row.forecast}, Previous: {row.previous}")
            print(f"  Sentiment Score: {row.sentiment_score}")
            print(f"  Created At: {row.created_at}")
            
            if row.raw_response:
                try:
                    resp = row.raw_response if isinstance(row.raw_response, dict) else json.loads(row.raw_response)
                    
                    if 'error' in resp:
                        error_msg = resp['error']
                        error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
                        error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
                        print(f"  ERROR: {error_msg[:200]}")
                    elif 'sentiment_score' in resp and resp.get('sentiment_score') is None:
                        print(f"  Sentiment was explicitly None in response")
                    else:
                        print(f"  Raw Response Keys: {list(resp.keys())}")
                        if 'sentiment_score' in resp:
                            print(f"    - sentiment_score in response: {resp['sentiment_score']}")
                except Exception as e:
                    print(f"  Error parsing raw_response: {e}")
                    print(f"  Raw Response (first 200 chars): {str(row.raw_response)[:200]}")
            else:
                print(f"  Raw Response: None")
            print()
        
        print("\n" + "=" * 50)
        print("ERROR PATTERN SUMMARY:")
        for error_type, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} occurrences")

def analyze_reddit_posts():
    """Analyze Reddit posts with zero sentiment scores."""
    print("\n" + "=" * 80)
    print("ANALYZING REDDIT POSTS WITH ZERO SENTIMENT SCORES")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Get total count of posts with zero sentiment
        count_query = text("""
            SELECT COUNT(*) as total
            FROM reddit_posts
            WHERE sentiment_score = 0
        """)
        total_count = conn.execute(count_query).fetchone().total
        
        print(f"\nTotal Reddit posts with sentiment_score = 0: {total_count}")
        
        # Get sample of posts with zero sentiment
        query = text("""
            SELECT id, reddit_id, subreddit, title, body, url, 
                   sentiment_score, raw_response, created_at,
                   LENGTH(COALESCE(body, '')) as body_length,
                   LENGTH(title) as title_length
            FROM reddit_posts
            WHERE sentiment_score = 0
            ORDER BY created_at DESC
            LIMIT 15
        """)
        
        result = conn.execute(query)
        posts = result.fetchall()
        
        print(f"\nAnalyzing {len(posts)} sample posts with zero sentiment:")
        print()
        
        patterns = {
            'minimal_content': 0,
            'image_post': 0,
            'error_in_response': 0,
            'explicit_zero': 0,
            'captcha_error': 0,
            'network_error': 0,
            'other': 0
        }
        
        for row in posts[:10]:  # Show first 10 in detail
            print(f"ID: {row.id}, Reddit ID: {row.reddit_id}")
            print(f"  Subreddit: r/{row.subreddit}")
            print(f"  Title: {row.title[:100]}...")
            print(f"  Body Length: {row.body_length} chars")
            print(f"  URL: {row.url[:80] if row.url else 'None'}")
            print(f"  Sentiment Score: {row.sentiment_score}")
            
            # Analyze content
            if row.body_length < 50:
                patterns['minimal_content'] += 1
                print(f"  Pattern: MINIMAL CONTENT (body < 50 chars)")
            
            if row.url and any(ext in str(row.url) for ext in ['.jpg', '.png', '.gif', 'imgur.com', 'i.redd.it']):
                patterns['image_post'] += 1
                print(f"  Pattern: IMAGE POST")
            
            if row.raw_response:
                try:
                    resp = row.raw_response if isinstance(row.raw_response, dict) else json.loads(row.raw_response)
                    
                    if 'error' in resp:
                        error_msg = str(resp['error']).lower()
                        if 'captcha' in error_msg or 'verification' in error_msg:
                            patterns['captcha_error'] += 1
                            print(f"  Pattern: CAPTCHA/VERIFICATION ERROR")
                        elif 'network' in error_msg or 'timeout' in error_msg:
                            patterns['network_error'] += 1
                            print(f"  Pattern: NETWORK ERROR")
                        else:
                            patterns['error_in_response'] += 1
                        print(f"  ERROR: {resp['error'][:200]}")
                    elif 'sentiment_score' in resp and resp.get('sentiment_score') == 0:
                        patterns['explicit_zero'] += 1
                        print(f"  Pattern: EXPLICIT ZERO from model")
                        if 'reasoning' in resp:
                            print(f"  Reasoning: {resp['reasoning'][:200]}")
                    else:
                        patterns['other'] += 1
                except Exception as e:
                    print(f"  Error parsing raw_response: {e}")
            else:
                print(f"  Raw Response: None")
            print()
        
        # Analyze patterns across all zero-sentiment posts
        print("\n" + "=" * 50)
        print("PATTERN ANALYSIS FOR ZERO SENTIMENT POSTS:")
        
        # Query for more detailed pattern analysis
        pattern_query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN LENGTH(COALESCE(body, '')) < 50 THEN 1 END) as minimal_body,
                COUNT(CASE WHEN body IS NULL OR body = '' THEN 1 END) as no_body,
                COUNT(CASE WHEN url LIKE '%imgur.com%' OR url LIKE '%i.redd.it%' 
                           OR url LIKE '%.jpg' OR url LIKE '%.png' OR url LIKE '%.gif' THEN 1 END) as image_posts,
                COUNT(CASE WHEN raw_response::text LIKE '%error%' THEN 1 END) as has_error,
                COUNT(CASE WHEN raw_response::text LIKE '%captcha%' OR raw_response::text LIKE '%verification%' THEN 1 END) as captcha_issues,
                AVG(LENGTH(COALESCE(body, ''))) as avg_body_length,
                MIN(LENGTH(COALESCE(body, ''))) as min_body_length,
                MAX(LENGTH(COALESCE(body, ''))) as max_body_length
            FROM reddit_posts
            WHERE sentiment_score = 0
        """)
        
        stats = conn.execute(pattern_query).fetchone()
        
        print(f"  Total posts with zero sentiment: {stats.total}")
        print(f"  Posts with minimal body (<50 chars): {stats.minimal_body} ({stats.minimal_body/stats.total*100:.1f}%)")
        print(f"  Posts with no body: {stats.no_body} ({stats.no_body/stats.total*100:.1f}%)")
        print(f"  Image/media posts: {stats.image_posts} ({stats.image_posts/stats.total*100:.1f}%)")
        print(f"  Posts with errors in response: {stats.has_error} ({stats.has_error/stats.total*100:.1f}%)")
        print(f"  Posts with captcha/verification issues: {stats.captcha_issues} ({stats.captcha_issues/stats.total*100:.1f}%)")
        print(f"  Average body length: {stats.avg_body_length:.1f} chars")
        print(f"  Body length range: {stats.min_body_length} - {stats.max_body_length} chars")

def analyze_gemini_code():
    """Analyze the Gemini analyzer code to understand scoring logic."""
    print("\n" + "=" * 80)
    print("ANALYZING GEMINI ANALYZER CODE")
    print("=" * 80)
    
    # Read the Gemini analyzer code
    gemini_path = "/home/dixter/Projects/news-sentiment/src/news_sentiment/analyzer/gemini.py"
    if os.path.exists(gemini_path):
        with open(gemini_path, 'r') as f:
            content = f.read()
            
        # Look for key patterns
        print("\nKey findings from Gemini analyzer code:")
        
        if "return None" in content or "sentiment_score = None" in content:
            print("  ✓ Code can return None sentiment scores")
        
        if "sentiment_score = 0" in content or "return 0" in content:
            print("  ✓ Code can return 0 sentiment scores")
            
        if "captcha" in content.lower() or "verification" in content.lower():
            print("  ✓ Code handles captcha/verification cases")
            
        if "error" in content.lower() and "except" in content:
            print("  ✓ Code has error handling")
            
        # Check for minimal content handling
        if "len(" in content or "length" in content.lower():
            print("  ✓ Code checks content length")
            
        print("\n  Note: Full code review needed for complete understanding")
    else:
        print(f"  Gemini analyzer file not found at: {gemini_path}")

def main():
    """Run all analyses."""
    try:
        analyze_economic_events()
        analyze_reddit_posts()
        analyze_gemini_code()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()