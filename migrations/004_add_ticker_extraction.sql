-- Migration 004: Add ticker extraction and fetched_at tracking
-- Run: psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/004_add_ticker_extraction.sql

-- Add fetched_at column to track when the post was scraped
ALTER TABLE reddit_posts
ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add symbols array to store extracted tickers (e.g., ['NVDA', 'AAPL', 'BTC'])
ALTER TABLE reddit_posts
ADD COLUMN IF NOT EXISTS symbols TEXT[];

-- Add symbol_sentiments JSONB to store per-symbol sentiment
-- Example: {"NVDA": 0.8, "AAPL": 0.5, "TSLA": -0.3}
ALTER TABLE reddit_posts
ADD COLUMN IF NOT EXISTS symbol_sentiments JSONB;

-- Create index on symbols for efficient queries
CREATE INDEX IF NOT EXISTS idx_reddit_posts_symbols
ON reddit_posts USING GIN (symbols);

-- Create index on fetched_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_reddit_posts_fetched_at
ON reddit_posts (fetched_at);

-- Update existing records to set fetched_at to created_at
UPDATE reddit_posts
SET fetched_at = created_at
WHERE fetched_at IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN reddit_posts.fetched_at IS 'Timestamp when the post was scraped from Reddit';
COMMENT ON COLUMN reddit_posts.symbols IS 'Array of ticker symbols mentioned in the post (e.g., NVDA, AAPL, BTC)';
COMMENT ON COLUMN reddit_posts.symbol_sentiments IS 'Per-symbol sentiment scores as JSON (e.g., {"NVDA": 0.8, "AAPL": -0.3})';
