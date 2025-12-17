---
name: Silent Image Download Failures Cause Mass 0 Sentiment Scores
status: open
priority: high
created: 2025-12-02T22:31:21Z
updated: 2025-12-02T22:31:21Z
github: https://github.com/Dixter999/news-sentiment/issues/12
imported: true
---

# Silent Image Download Failures Cause Mass 0 Sentiment Scores

## Problem

163+ Reddit posts have `sentiment_score = 0` with reasoning like:
- "With no information provided about the event... it is impossible to determine any market sentiment"
- "Without any information about the event... it's impossible to determine the sentiment impact"
- "The post content is inaccessible, so no sentiment can be extracted"

## Root Cause

When image download fails in `gemini.py:_download_image()`, the code:
1. **Silently returns `None`** - no logging, no error tracking
2. **Falls back to text-only analysis** - but Reddit image posts often have empty body text
3. **Sends essentially nothing to Gemini** - just title + `"(no text)"`
4. **Gemini responds with neutral 0.0** - because there's literally nothing to analyze

## Affected Code

### `src/news_sentiment/analyzer/gemini.py`

**Line 290 - Silent failure:**
```python
except Exception:
    return None  # No logging, no error tracking
```

**Lines 321-337 - Silent fallback:**
```python
if self.is_image_url(url):
    image = self._download_image(url)
    if image:  # If None, silently falls through
        # multimodal analysis
        ...
# Falls through to text-only with no indication image failed
```

## Proposed Fixes

1. **Add logging to image download failures**
2. **Track image download failures in response metadata**
3. **Include image URL context in fallback prompt**
4. **Add retry logic for transient failures**
5. **Store failure reason in database `raw_response`**

## Reprocessing Strategy

After fixes are implemented:
1. Query posts where `raw_response` contains "no information" patterns
2. Re-attempt image download with retry logic
3. If still failing, log the specific URL for manual investigation

## Impact

- **163+ posts** currently affected (likely more)
- **Sentiment analysis quality** severely degraded for image-heavy subreddits
- **Silent failures** make debugging impossible

## Priority

**High** - Affects core sentiment analysis accuracy
