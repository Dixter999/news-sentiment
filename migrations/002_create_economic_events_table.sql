-- Migration 002: Create economic_events table
-- Created: 2025-11-30
-- Purpose: Store scraped economic calendar events and their AI sentiment analysis
--
-- Architecture:
-- - economic_events: Stores events from ForexFactory calendar with Gemini sentiment analysis
-- - Designed for efficient querying by timestamp, currency, and impact level
-- - Supports storing full AI response in JSONB for future analysis
--
-- Related: See SQLAlchemy model in src/news_sentiment/database/models.py

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Create the economic_events table
CREATE TABLE IF NOT EXISTS economic_events (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Core event data (from ForexFactory calendar)
    timestamp TIMESTAMPTZ NOT NULL,
    currency VARCHAR(10) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    impact VARCHAR(20) NOT NULL,
    actual VARCHAR(50),
    forecast VARCHAR(50),
    previous VARCHAR(50),

    -- AI Analysis fields
    sentiment_score FLOAT,
    raw_response JSONB,

    -- Audit timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_impact_values CHECK (impact IN ('high', 'medium', 'low')),
    CONSTRAINT uq_economic_events_timestamp_event_currency UNIQUE (timestamp, event_name, currency)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_economic_events_timestamp
    ON economic_events(timestamp DESC);

-- Index on currency for filtering by currency
CREATE INDEX IF NOT EXISTS idx_economic_events_currency
    ON economic_events(currency);

-- Index on impact for filtering by impact level
CREATE INDEX IF NOT EXISTS idx_economic_events_impact
    ON economic_events(impact);

-- Composite index for common query pattern: events by time and currency
CREATE INDEX IF NOT EXISTS idx_economic_events_timestamp_currency
    ON economic_events(timestamp, currency);

-- Index on event_name for searching specific events
CREATE INDEX IF NOT EXISTS idx_economic_events_event_name
    ON economic_events(event_name);

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE economic_events IS 'Economic calendar events scraped from ForexFactory with AI sentiment analysis from Gemini';
COMMENT ON COLUMN economic_events.id IS 'Auto-incrementing primary key';
COMMENT ON COLUMN economic_events.timestamp IS 'Event date/time in UTC with timezone';
COMMENT ON COLUMN economic_events.currency IS 'Currency code affected by the event (e.g., USD, EUR)';
COMMENT ON COLUMN economic_events.event_name IS 'Name of the economic event (e.g., Non-Farm Payrolls)';
COMMENT ON COLUMN economic_events.impact IS 'Impact level: high, medium, or low';
COMMENT ON COLUMN economic_events.actual IS 'Actual released value (may include units like %, K, M)';
COMMENT ON COLUMN economic_events.forecast IS 'Market consensus forecast value';
COMMENT ON COLUMN economic_events.previous IS 'Previous period value';
COMMENT ON COLUMN economic_events.sentiment_score IS 'AI-generated sentiment score (-1.0 bearish to 1.0 bullish)';
COMMENT ON COLUMN economic_events.raw_response IS 'Full AI model response in JSONB format for detailed analysis';
COMMENT ON COLUMN economic_events.created_at IS 'Timestamp when the record was created';
COMMENT ON COLUMN economic_events.updated_at IS 'Timestamp when the record was last updated';

-- ============================================================================
-- DOWN MIGRATION (Rollback)
-- ============================================================================
-- To rollback this migration, run the following:
--
-- DROP INDEX IF EXISTS idx_economic_events_event_name;
-- DROP INDEX IF EXISTS idx_economic_events_timestamp_currency;
-- DROP INDEX IF EXISTS idx_economic_events_impact;
-- DROP INDEX IF EXISTS idx_economic_events_currency;
-- DROP INDEX IF EXISTS idx_economic_events_timestamp;
-- DROP TABLE IF EXISTS economic_events;
--
-- ============================================================================

-- Commented out DROP statements for rollback (uncomment to reverse migration)
-- DROP TABLE IF EXISTS economic_events CASCADE;
