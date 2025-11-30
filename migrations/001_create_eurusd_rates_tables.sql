-- Migration 001: Create eurusd_*_rates tables in markets database
-- Created: 2025-11-22
-- Purpose: Store raw OHLC data for EURUSD symbol in markets database
--
-- Architecture:
-- - markets.eurusd_*_rates: Raw OHLC price data (THIS FILE)
-- - ai_model.technical_indicators: Calculated indicators (separate)

-- ============================================================================
-- M1 (1-minute) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_m1_rates (
    rate_time BIGINT PRIMARY KEY,  -- Unix timestamp in seconds
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_m1_time ON eurusd_m1_rates(rate_time DESC);

-- ============================================================================
-- M5 (5-minute) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_m5_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_m5_time ON eurusd_m5_rates(rate_time DESC);

-- ============================================================================
-- M10 (10-minute) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_m10_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_m10_time ON eurusd_m10_rates(rate_time DESC);

-- ============================================================================
-- M15 (15-minute) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_m15_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_m15_time ON eurusd_m15_rates(rate_time DESC);

-- ============================================================================
-- M20 (20-minute) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_m20_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_m20_time ON eurusd_m20_rates(rate_time DESC);

-- ============================================================================
-- M30 (30-minute) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_m30_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_m30_time ON eurusd_m30_rates(rate_time DESC);

-- ============================================================================
-- H1 (1-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h1_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h1_time ON eurusd_h1_rates(rate_time DESC);

-- ============================================================================
-- H2 (2-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h2_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h2_time ON eurusd_h2_rates(rate_time DESC);

-- ============================================================================
-- H3 (3-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h3_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h3_time ON eurusd_h3_rates(rate_time DESC);

-- ============================================================================
-- H4 (4-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h4_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h4_time ON eurusd_h4_rates(rate_time DESC);

-- ============================================================================
-- H6 (6-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h6_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h6_time ON eurusd_h6_rates(rate_time DESC);

-- ============================================================================
-- H8 (8-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h8_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h8_time ON eurusd_h8_rates(rate_time DESC);

-- ============================================================================
-- H12 (12-hour) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_h12_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_h12_time ON eurusd_h12_rates(rate_time DESC);

-- ============================================================================
-- D1 (1-day) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_d1_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_d1_time ON eurusd_d1_rates(rate_time DESC);

-- ============================================================================
-- W1 (1-week) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_w1_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_w1_time ON eurusd_w1_rates(rate_time DESC);

-- ============================================================================
-- MN1 (1-month) EURUSD Rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS eurusd_mn1_rates (
    rate_time BIGINT PRIMARY KEY,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    readable_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_eurusd_mn1_time ON eurusd_mn1_rates(rate_time DESC);

-- ============================================================================
-- Table Comments
-- ============================================================================
COMMENT ON TABLE eurusd_m1_rates IS 'Raw OHLC EURUSD price data - 1 minute timeframe';
COMMENT ON TABLE eurusd_m5_rates IS 'Raw OHLC EURUSD price data - 5 minute timeframe';
COMMENT ON TABLE eurusd_m10_rates IS 'Raw OHLC EURUSD price data - 10 minute timeframe';
COMMENT ON TABLE eurusd_m15_rates IS 'Raw OHLC EURUSD price data - 15 minute timeframe';
COMMENT ON TABLE eurusd_m20_rates IS 'Raw OHLC EURUSD price data - 20 minute timeframe';
COMMENT ON TABLE eurusd_m30_rates IS 'Raw OHLC EURUSD price data - 30 minute timeframe';
COMMENT ON TABLE eurusd_h1_rates IS 'Raw OHLC EURUSD price data - 1 hour timeframe';
COMMENT ON TABLE eurusd_h2_rates IS 'Raw OHLC EURUSD price data - 2 hour timeframe';
COMMENT ON TABLE eurusd_h3_rates IS 'Raw OHLC EURUSD price data - 3 hour timeframe';
COMMENT ON TABLE eurusd_h4_rates IS 'Raw OHLC EURUSD price data - 4 hour timeframe';
COMMENT ON TABLE eurusd_h6_rates IS 'Raw OHLC EURUSD price data - 6 hour timeframe';
COMMENT ON TABLE eurusd_h8_rates IS 'Raw OHLC EURUSD price data - 8 hour timeframe';
COMMENT ON TABLE eurusd_h12_rates IS 'Raw OHLC EURUSD price data - 12 hour timeframe';
COMMENT ON TABLE eurusd_d1_rates IS 'Raw OHLC EURUSD price data - 1 day timeframe';
COMMENT ON TABLE eurusd_w1_rates IS 'Raw OHLC EURUSD price data - 1 week timeframe';
COMMENT ON TABLE eurusd_mn1_rates IS 'Raw OHLC EURUSD price data - 1 month timeframe';
