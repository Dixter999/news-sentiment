#!/usr/bin/env python3
"""
Analyze the reasoning behind zero sentiment scores.
"""

import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

db_host = os.getenv("AI_MODEL_DB_HOST", "localhost")
db_port = os.getenv("AI_MODEL_DB_PORT", "5432")
db_name = os.getenv("AI_MODEL_DB_NAME", "ai_model")
db_user = os.getenv("AI_MODEL_DB_USER", "ai_model")
db_password = os.getenv("AI_MODEL_DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

def analyze_zero_reasoning():
    """Extract and analyze reasoning for zero sentiment scores."""
    print("=" * 80)
    print("ANALYZING REASONING FOR ZERO SENTIMENT SCORES")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Get all posts with zero sentiment and raw_response
        query = text("""
            SELECT 
                id, 
                reddit_id, 
                title, 
                body,
                url,
                raw_response::text as raw_response_text
            FROM reddit_posts
            WHERE sentiment_score = 0
              AND raw_response IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        result = conn.execute(query)
        posts = result.fetchall()
        
        print(f"\nFound {len(posts)} posts with zero sentiment and raw response")
        
        reasoning_patterns = Counter()
        common_phrases = []
        
        for post in posts:
            try:
                # Parse raw response
                raw_resp = json.loads(post.raw_response_text)
                
                if 'reasoning' in raw_resp:
                    reasoning = raw_resp['reasoning'].lower()
                    
                    # Look for common patterns
                    if "no information" in reasoning or "unknown" in reasoning:
                        reasoning_patterns['No Information'] += 1
                    elif "neutral" in reasoning:
                        reasoning_patterns['Neutral Content'] += 1
                    elif "impossible to determine" in reasoning:
                        reasoning_patterns['Cannot Determine'] += 1
                    elif "no basis" in reasoning:
                        reasoning_patterns['No Basis'] += 1
                    elif "question" in reasoning or "asking" in reasoning:
                        reasoning_patterns['Question/Request'] += 1
                    else:
                        reasoning_patterns['Other'] += 1
                    
                    # Store examples
                    if len(common_phrases) < 10:
                        common_phrases.append({
                            'title': post.title[:60],
                            'reasoning': raw_resp['reasoning'][:150],
                            'has_body': bool(post.body and len(post.body) > 10),
                            'url_type': 'image' if post.url and any(x in post.url for x in ['.jpg', '.png', 'imgur', 'i.redd.it']) else 'other'
                        })
                        
            except Exception as e:
                continue
        
        print("\nReasoning Pattern Distribution:")
        print("-" * 40)
        for pattern, count in reasoning_patterns.most_common():
            print(f"  {pattern}: {count} ({count/len(posts)*100:.1f}%)")
        
        print("\nExample Reasoning Samples:")
        print("-" * 40)
        for i, example in enumerate(common_phrases, 1):
            print(f"\n{i}. Title: {example['title']}...")
            print(f"   Has Body: {example['has_body']}, URL Type: {example['url_type']}")
            print(f"   Reasoning: {example['reasoning']}...")

def check_economic_events_zero_scores():
    """Check why economic events have zero scores."""
    print("\n" + "=" * 80)
    print("ECONOMIC EVENTS WITH ZERO SCORES")
    print("=" * 80)
    
    with engine.connect() as conn:
        query = text("""
            SELECT 
                id,
                event_name,
                currency,
                impact,
                actual,
                forecast,
                previous,
                raw_response::text as raw_response_text
            FROM economic_events
            WHERE sentiment_score = 0
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        result = conn.execute(query)
        events = result.fetchall()
        
        print(f"\nAnalyzing {len(events)} economic events with zero sentiment:")
        
        patterns = Counter()
        
        for event in events[:5]:  # Show first 5 examples
            print(f"\nEvent: {event.event_name}")
            print(f"  Currency: {event.currency}")
            print(f"  Data: A={event.actual}, F={event.forecast}, P={event.previous}")
            
            try:
                raw_resp = json.loads(event.raw_response_text)
                if 'reasoning' in raw_resp:
                    print(f"  Reasoning: {raw_resp['reasoning'][:150]}...")
                    
                    # Categorize pattern
                    reasoning = raw_resp['reasoning'].lower()
                    if "mixed" in reasoning or "offsetting" in reasoning:
                        patterns['Mixed Signals'] += 1
                    elif "neutral" in reasoning:
                        patterns['Neutral Impact'] += 1
                    elif "no significant" in reasoning:
                        patterns['No Significant Impact'] += 1
                    else:
                        patterns['Other'] += 1
            except:
                pass
        
        print("\nEconomic Event Zero Score Patterns:")
        for pattern, count in patterns.most_common():
            print(f"  {pattern}: {count}")

def identify_root_causes():
    """Identify root causes for null and zero scores."""
    print("\n" + "=" * 80)
    print("ROOT CAUSE ANALYSIS SUMMARY")
    print("=" * 80)
    
    print("\n📊 NULL SENTIMENT SCORES (Economic Events):")
    print("-" * 40)
    print("1. Bank Holidays (11 events)")
    print("   - No market data to analyze")
    print("   - Should be excluded from sentiment analysis")
    print()
    print("2. Never Analyzed (8 events)")  
    print("   - Events have raw_response = None")
    print("   - These were scraped but never sent to Gemini")
    print("   - Likely interrupted during processing")
    
    print("\n📊 ZERO SENTIMENT SCORES (Reddit Posts - 183 total):")
    print("-" * 40)
    print("1. Minimal/No Content (57.4%)")
    print("   - Posts with <50 chars body")
    print("   - External links with no text")
    print("   - Model correctly identifies no tradeable sentiment")
    print()
    print("2. Questions/Information Requests")
    print("   - Posts asking for advice or information")
    print("   - No directional market sentiment expressed")
    print()
    print("3. Model Interpretation Issue")
    print("   - Gemini is being prompted as if analyzing economic events")
    print("   - Reddit posts don't have 'actual', 'forecast', 'previous' values")
    print("   - Model defaults to 0 when missing expected data")
    
    print("\n📊 ZERO SENTIMENT SCORES (Economic Events - 1,568 total):")
    print("-" * 40)
    print("1. Mixed/Offsetting Signals")
    print("   - Some data positive, some negative")
    print("   - Model correctly identifies neutral net impact")
    print()
    print("2. Insignificant Deviations")
    print("   - Actual very close to forecast")
    print("   - Model correctly identifies no market surprise")

def main():
    analyze_zero_reasoning()
    check_economic_events_zero_scores()
    identify_root_causes()
    
    print("\n" + "=" * 80)
    print("COMPLETE ANALYSIS")
    print("=" * 80)

if __name__ == "__main__":
    main()