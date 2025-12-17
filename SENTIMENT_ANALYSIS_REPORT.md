# Sentiment Score Analysis Report

## Executive Summary

This report analyzes null and zero sentiment scores in the news sentiment database. The investigation found that most cases are working as expected, with a few areas needing attention.

**Key Findings:**
- **Null scores (19 economic events)**: Primarily bank holidays and events that were never analyzed
- **Zero scores (183 Reddit posts, 1,568 economic events)**: Mostly legitimate neutral sentiment or insufficient content
- **Critical Issue**: Reddit posts are being analyzed with the wrong prompt template (economic event template)

## Database Statistics

### Overall Distribution
```
Economic Events:
- Total Records: 6,987
- With Sentiment: 6,968 (99.7%)
- Null Sentiment: 19 (0.3%)
- Zero Sentiment: 1,568 (22.4%)

Reddit Posts:
- Total Records: 515
- With Sentiment: 515 (100.0%)
- Null Sentiment: 0 (0.0%)
- Zero Sentiment: 183 (35.5%)
```

## Root Cause Analysis

### 1. NULL Sentiment Scores (Economic Events Only)

#### Pattern 1: Bank Holidays (11 events)
- **Event IDs**: 128-131, 135-136, 154, 158-159
- **Characteristics**: 
  - Event name = "Bank Holiday"
  - Impact = "Holiday"
  - No actual/forecast/previous values
- **Root Cause**: These are market closure notifications, not economic data
- **Recommendation**: **EXCLUDE** - Filter out bank holidays before sentiment analysis

#### Pattern 2: Never Analyzed (8 events)
- **Event IDs**: 126-127, 132-134, 141, 148-149, 155-156
- **Characteristics**:
  - Have valid economic data (actual, forecast, previous)
  - raw_response = None (never sent to Gemini)
  - All created at 2025-12-01 17:47:23
- **Root Cause**: Processing was interrupted after scraping but before analysis
- **Recommendation**: **REPROCESS** - These events should be analyzed

### 2. ZERO Sentiment Scores (Reddit Posts)

#### Pattern 1: Minimal Content (57.4% - 105 posts)
- **Characteristics**:
  - Body text < 50 characters
  - Often just external links with no commentary
  - Title-only posts
- **Example**: "guys i trade mostly liquidity sweeps suggest me some good pairs" (29 chars body)
- **Root Cause**: Insufficient content for sentiment analysis
- **Recommendation**: **WORKING AS INTENDED** - No actionable sentiment

#### Pattern 2: Wrong Prompt Template (36.1% - 66 posts)
- **Critical Finding**: The Gemini model is receiving Reddit posts but analyzing them as if they were economic events
- **Evidence from reasoning**: 
  - "With no information about the event, currency, impact level, actual release, forecast..."
  - "Without any information on the event, currency, impact level, or any data points..."
- **Root Cause**: `analyze_reddit_post()` is using economic event prompt when falling back to text analysis
- **Recommendation**: **FIX ANALYZER** - Use correct Reddit prompt template

#### Pattern 3: Questions/Information Requests (1.6% - 3 posts)
- **Characteristics**: Posts asking for advice or information
- **Example**: "How do you scalp with so high fees?"
- **Root Cause**: No directional market sentiment expressed
- **Recommendation**: **WORKING AS INTENDED** - Neutral is correct

### 3. ZERO Sentiment Scores (Economic Events)

#### Pattern 1: Unreleased Data (Common)
- **Characteristics**: 
  - Actual value is empty/null
  - Event hasn't occurred yet
- **Example**: "Crude Oil Inventories" with no actual value
- **Root Cause**: Analyzing events before data release
- **Recommendation**: **WORKING AS INTENDED** - Zero is appropriate for unreleased data

#### Pattern 2: Mixed Signals
- **Characteristics**: Some indicators positive, others negative
- **Root Cause**: Offsetting impacts result in neutral sentiment
- **Recommendation**: **WORKING AS INTENDED** - Zero accurately reflects neutral impact

## Specific Recommendations

### 1. Immediate Actions

#### Fix Reddit Post Analysis
The most critical issue is that Reddit posts are being analyzed with the wrong prompt template:

**Current Issue in `gemini.py`:**
- When Reddit posts fall back to text-only analysis, they're prompted as economic events
- The model looks for "actual", "forecast", "previous" values that don't exist
- This causes the model to return 0 due to "insufficient information"

**Fix Required:**
- Update `_build_reddit_prompt()` to remove references to economic event fields
- Ensure Reddit posts are always analyzed with Reddit-specific prompts

#### Reprocess Never-Analyzed Events
```sql
-- Find events to reprocess
SELECT id, event_name, currency, actual, forecast, previous
FROM economic_events
WHERE sentiment_score IS NULL 
  AND raw_response IS NULL
  AND event_name != 'Bank Holiday'
  AND (actual IS NOT NULL OR forecast IS NOT NULL);
-- Returns IDs: 127, 132, 133, 134, 141, 148, 149, 155, 156
```

### 2. Data Cleanup

#### Remove Bank Holidays
```sql
-- Option 1: Delete bank holidays
DELETE FROM economic_events 
WHERE event_name = 'Bank Holiday';

-- Option 2: Mark as excluded (add column first)
UPDATE economic_events 
SET excluded_from_analysis = true 
WHERE event_name = 'Bank Holiday';
```

### 3. Process Improvements

#### Pre-filtering Rules
Add filters BEFORE sending to Gemini:
1. Skip bank holidays
2. Skip events with no actual AND no forecast
3. Skip Reddit posts with body < 20 chars AND no meaningful title
4. Skip Reddit "daily discussion" threads

#### Prompt Optimization
1. Create separate, specialized prompts for:
   - Economic events with data
   - Economic events pre-release (forecast only)
   - Reddit text posts
   - Reddit image posts
   - Reddit link posts

#### Monitoring Improvements
1. Track analysis success rate by category
2. Alert on high null/zero sentiment rates
3. Log when prompts fall back to wrong template

## Code Issues Found

### Issue 1: Reddit Prompt Fallback
**File**: `src/news_sentiment/analyzer/gemini.py`
**Problem**: Line 186-202 uses economic event prompt template for Reddit posts
**Impact**: Causes false zero scores for Reddit posts

### Issue 2: No Holiday Filtering
**Problem**: Bank holidays are processed like economic events
**Impact**: Wastes API calls and creates meaningless null scores

### Issue 3: No Content Length Validation
**Problem**: Posts with minimal content are still analyzed
**Impact**: High rate of zero scores that provide no value

## Metrics to Track

After implementing fixes, monitor:
1. **Null sentiment rate**: Should drop to < 0.1% (only true failures)
2. **Zero sentiment rate for Reddit**: Should drop from 35.5% to ~10-15%
3. **Zero sentiment rate for events**: 22.4% is reasonable (many neutral events)
4. **API efficiency**: Reduce wasted calls by 15-20% with pre-filtering

## Conclusion

The analysis reveals that most null and zero sentiment scores are legitimate:
- Null scores are primarily bank holidays (should be excluded)
- Zero scores often reflect genuinely neutral sentiment

However, there is one critical bug causing Reddit posts to be analyzed with the wrong prompt template, resulting in unnecessary zero scores. Fixing this issue and implementing the recommended filters will significantly improve data quality and reduce API waste.

**Priority Actions:**
1. **HIGH**: Fix Reddit post prompt template issue
2. **MEDIUM**: Reprocess 8 never-analyzed economic events
3. **LOW**: Implement pre-filtering rules to skip unsuitable content
4. **LOW**: Clean up bank holiday records