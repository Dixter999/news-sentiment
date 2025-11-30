-- Migration 003: Create reddit_posts table
-- Created: 2025-11-30
-- Purpose: Store scraped Reddit posts from financial subreddits with AI sentiment analysis
--
-- Architecture:
-- - reddit_posts: Stores posts from subreddits like wallstreetbets, stocks, investing
-- - Designed for efficient querying by subreddit, timestamp, and reddit_id
-- - Supports storing full AI response in JSONB for future analysis
--
-- Related: See SQLAlchemy model in src/news_sentiment/database/models.py

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Create the reddit_posts table
CREATE TABLE IF NOT EXISTS reddit_posts (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Core post data (from Reddit API/scraping)
    reddit_id VARCHAR(20) UNIQUE NOT NULL,
    subreddit VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    url TEXT,
    score INTEGER,
    num_comments INTEGER,
    flair VARCHAR(100),
    timestamp TIMESTAMPTZ NOT NULL,

    -- AI Analysis fields
    sentiment_score FLOAT,
    raw_response JSONB,

    -- Audit timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on reddit_id for uniqueness lookups (already created by UNIQUE constraint)
-- This is created implicitly but we document it here for clarity
CREATE INDEX IF NOT EXISTS idx_reddit_posts_reddit_id
    ON reddit_posts(reddit_id);

-- Index on subreddit for filtering by subreddit
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit
    ON reddit_posts(subreddit);

-- Index on timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_reddit_posts_timestamp
    ON reddit_posts(timestamp DESC);

-- Composite index for common query pattern: posts by subreddit and time
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit_timestamp
    ON reddit_posts(subreddit, timestamp DESC);

-- Index on score for filtering popular posts
CREATE INDEX IF NOT EXISTS idx_reddit_posts_score
    ON reddit_posts(score DESC);

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE reddit_posts IS 'Reddit posts scraped from financial subreddits with AI sentiment analysis from Gemini';
COMMENT ON COLUMN reddit_posts.id IS 'Auto-incrementing primary key';
COMMENT ON COLUMN reddit_posts.reddit_id IS 'Reddit unique post ID (e.g., abc123xyz)';
COMMENT ON COLUMN reddit_posts.subreddit IS 'Subreddit name without r/ prefix (e.g., wallstreetbets)';
COMMENT ON COLUMN reddit_posts.title IS 'Post title';
COMMENT ON COLUMN reddit_posts.body IS 'Post body/selftext (nullable for link posts)';
COMMENT ON COLUMN reddit_posts.url IS 'Full URL to the post';
COMMENT ON COLUMN reddit_posts.score IS 'Net upvotes (upvotes - downvotes)';
COMMENT ON COLUMN reddit_posts.num_comments IS 'Number of comments on the post';
COMMENT ON COLUMN reddit_posts.flair IS 'Post flair/category if present';
COMMENT ON COLUMN reddit_posts.timestamp IS 'When the post was created on Reddit (UTC)';
COMMENT ON COLUMN reddit_posts.sentiment_score IS 'AI-generated sentiment score (-1.0 bearish to 1.0 bullish)';
COMMENT ON COLUMN reddit_posts.raw_response IS 'Full AI model response in JSONB format for detailed analysis';
COMMENT ON COLUMN reddit_posts.created_at IS 'Timestamp when the record was created';
COMMENT ON COLUMN reddit_posts.updated_at IS 'Timestamp when the record was last updated';

-- ============================================================================
-- DOWN MIGRATION (Rollback)
-- ============================================================================
-- To rollback this migration, run the following:
--
-- DROP INDEX IF EXISTS idx_reddit_posts_score;
-- DROP INDEX IF EXISTS idx_reddit_posts_subreddit_timestamp;
-- DROP INDEX IF EXISTS idx_reddit_posts_timestamp;
-- DROP INDEX IF EXISTS idx_reddit_posts_subreddit;
-- DROP INDEX IF EXISTS idx_reddit_posts_reddit_id;
-- DROP TABLE IF EXISTS reddit_posts;
--
-- ============================================================================

-- Commented out DROP statements for rollback (uncomment to reverse migration)
-- DROP TABLE IF EXISTS reddit_posts CASCADE;
