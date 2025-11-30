---
issue: 10
title: Add Reddit Scraper for Financial Subreddits
analyzed: 2025-11-30T14:14:08Z
estimated_hours: 12
parallelization_factor: 3.0
---

# Parallel Work Analysis: Issue #10

## Overview
Implement a Reddit scraper to gather financial news and discussions from financial subreddits (r/wallstreetbets, r/stocks, r/investing, etc.) using PRAW with OAuth2 authentication, store posts in database, and integrate with existing Gemini sentiment analyzer.

## Parallel Streams

### Stream A: Database Layer
**Scope**: Create database migration and SQLAlchemy model for reddit_posts table
**Files**:
- `migrations/003_create_reddit_posts_table.sql`
- `src/news_sentiment/database/models.py` (add RedditPost class)
- `src/news_sentiment/database/__init__.py` (export RedditPost)
**Agent Type**: postgresql-expert
**Can Start**: immediately
**Estimated Hours**: 2
**Dependencies**: none

### Stream B: Reddit Scraper Core
**Scope**: Implement PRAW-based Reddit scraper with OAuth2 authentication
**Files**:
- `src/news_sentiment/scraper/reddit_scraper.py`
- `src/news_sentiment/scraper/__init__.py` (export RedditScraper)
- `pyproject.toml` (add praw dependency)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 4
**Dependencies**: none

### Stream C: CLI Integration
**Scope**: Add Reddit scraping commands to main.py CLI
**Files**:
- `src/news_sentiment/main.py` (add --reddit-scrape argument)
**Agent Type**: python-backend-engineer
**Can Start**: after Stream A and Stream B complete
**Estimated Hours**: 2
**Dependencies**: Stream A, Stream B

### Stream D: Test Suite
**Scope**: Unit tests for Reddit scraper with mocked PRAW client
**Files**:
- `tests/test_reddit_scraper.py`
- `tests/test_integration_reddit.py`
- `tests/conftest.py` (add Reddit-related fixtures)
**Agent Type**: python-backend-engineer
**Can Start**: after Stream B completes
**Estimated Hours**: 4
**Dependencies**: Stream B

## Coordination Points

### Shared Files
Files multiple streams need to modify:
- `src/news_sentiment/database/__init__.py` - Stream A (add RedditPost export)
- `src/news_sentiment/scraper/__init__.py` - Stream B (add RedditScraper export)
- `pyproject.toml` - Stream B (add praw dependency)
- `tests/conftest.py` - Stream D (add fixtures)

### Sequential Requirements
1. Database model (Stream A) before CLI integration (Stream C)
2. Reddit scraper (Stream B) before CLI integration (Stream C)
3. Reddit scraper (Stream B) before tests (Stream D)

## Conflict Risk Assessment
- **Low Risk**: Streams A and B work on completely different directories
- **Low Risk**: Stream C and D start after dependencies complete
- **Medium Risk**: `tests/conftest.py` may need coordination with existing fixtures

## Parallelization Strategy

**Recommended Approach**: hybrid

Launch Streams A and B simultaneously (database and scraper are independent).
Start Stream C when both A and B complete.
Start Stream D when Stream B completes.

```
Timeline:
  A (Database):     [=====]
  B (Scraper):      [==========]
  C (CLI):                       [====]
  D (Tests):               [========]
```

## Expected Timeline

With parallel execution:
- Wall time: 6 hours
- Total work: 12 hours
- Efficiency gain: 50%

Without parallel execution:
- Wall time: 12 hours

## Notes
- PRAW simplifies OAuth2 significantly - just needs client_id, client_secret, and user_agent
- Rate limiting is built into PRAW (handles 60 req/min automatically)
- Consider adding a configuration file for subreddit list (future enhancement)
- The 1,000 post ceiling means we should focus on "hot" and "new" posts rather than historical
- Environment variables REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are already documented in .env.example
