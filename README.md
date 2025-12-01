# News Sentiment Service

A Python service that aggregates economic calendar events from Forex Factory and Reddit financial communities, then analyzes them using Google Gemini AI to generate sentiment scores for trading decisions.

## Project Overview

This service provides automated collection and sentiment analysis of financial news and social media content. It:

1. **Collects** economic calendar data from [Forex Factory](https://www.forexfactory.com/calendar) using Playwright browser automation
2. **Fetches** Reddit posts from financial subreddits (r/wallstreetbets, r/stocks, r/investing, etc.) via the official Reddit API (PRAW)
3. **Analyzes** content using Google Gemini 2.0 Flash AI to determine market sentiment impact
4. **Stores** results in PostgreSQL for downstream trading applications

## Architecture

```
                              News Sentiment Service
    +---------------------------------------------------------------------+
    |                                                                     |
    |  +------------------+     +------------------+     +---------------+ |
    |  |                  |     |                  |     |               | |
    |  |  Forex Factory   |---->|  Playwright      |---->|   Economic    | |
    |  |  Calendar        |     |  Collector       |     |   Events      | |
    |  |                  |     |                  |     |               | |
    |  +------------------+     +------------------+     +-------+-------+ |
    |                                                            |         |
    |  +------------------+     +------------------+             |         |
    |  |                  |     |                  |             |         |
    |  |  Reddit API      |---->|  PRAW            |---->+-------+-------+ |
    |  |  (OAuth2)        |     |  Client          |     |               | |
    |  |                  |     |                  |     |   Gemini      | |
    |  +------------------+     +------------------+     |   Analyzer    | |
    |                                                    |               | |
    |  +------------------+     +------------------+     +-------+-------+ |
    |  |                  |     |                  |             |         |
    |  |  PostgreSQL      |<----|  Sentiment       |<------------+         |
    |  |  Database        |     |  Scores          |                       |
    |  |                  |     |                  |                       |
    |  +------------------+     +------------------+                       |
    |                                                                     |
    +---------------------------------------------------------------------+
```

**Data Flow:**
1. Playwright navigates to Forex Factory and collects calendar events
2. PRAW connects to Reddit API and fetches posts from financial subreddits
3. Content is parsed and stored in respective database tables
4. Gemini 2.0 Flash analyzes content to generate sentiment scores (-1.0 to +1.0)
5. Scores are stored back to the database for trading strategy consumption

## Features

- **Economic Calendar Aggregation**: Daily, weekly, or monthly event collection from Forex Factory
- **Reddit Integration**: Hot, new, and top posts from multiple financial subreddits via official API
- **AI Sentiment Analysis**: Google Gemini 2.0 Flash for intelligent sentiment scoring
- **Upsert Logic**: Automatic updates for existing records without duplicates
- **Batch Processing**: Efficient bulk analysis with rate limiting
- **CLI Interface**: Full command-line control for all operations

## Quick Start (Docker)

The fastest way to run the service is with Docker:

```bash
# Copy and configure environment variables
cp .env.example .env.docker
# Edit .env.docker with your credentials (no quotes, no 'export')

# Run forex sentiment query
docker compose --profile forex run --rm forex

# Run full data collection pipeline
docker compose --profile scraper run --rm scraper

# Interactive CLI
docker compose run --rm app python -m news_sentiment.main --help
```

## Prerequisites

- **Docker** (recommended) OR Python 3.11+
- PostgreSQL database
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Reddit API credentials ([Create an app here](https://www.reddit.com/prefs/apps))

## Installation

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Dixter999/news-sentiment.git
cd news-sentiment

# Create Docker environment file
cp .env.example .env.docker
# Edit .env.docker - remove 'export' and quotes for Docker compatibility

# Build and run
docker compose build
docker compose --profile forex run --rm forex
```

### Option 2: Local Python

```bash
# Clone the repository
git clone https://github.com/Dixter999/news-sentiment.git
cd news-sentiment

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package with development dependencies
pip install -e ".[dev]"

# Install Playwright browser
playwright install chromium

# Copy environment template and configure
cp .env.example .env
# Edit .env with your credentials (see Configuration section)
```

## Configuration

Edit the `.env` file with your credentials:

```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Reddit API Configuration
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret

# AI Model Database (READ-WRITE) - for storing results
AI_MODEL_DB_HOST=localhost
AI_MODEL_DB_PORT=5432
AI_MODEL_DB_NAME=ai_model
AI_MODEL_DB_USER=ai_model
AI_MODEL_DB_PASSWORD=your-password
```

### Getting Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Fill in name and redirect URI (use `http://localhost:8080`)
5. Copy the client ID (under the app name) and client secret

## CLI Usage

The service is invoked as a Python module:

```bash
# Show help
python -m news_sentiment.main --help

# === Economic Events ===

# Collect events for the current week
python -m news_sentiment.main --scrape week

# Collect events for today only
python -m news_sentiment.main --scrape today

# Collect events for the current month
python -m news_sentiment.main --scrape month

# === Reddit Posts ===

# Fetch hot posts from default subreddits
python -m news_sentiment.main --reddit hot

# Fetch new posts
python -m news_sentiment.main --reddit new

# Fetch top posts
python -m news_sentiment.main --reddit top

# Fetch from specific subreddits with custom limit
python -m news_sentiment.main --reddit hot --subreddits wallstreetbets stocks --reddit-limit 50

# === Sentiment Analysis ===

# Analyze all unscored content (events + posts)
python -m news_sentiment.main --analyze

# === Combined Operations ===

# Full pipeline: collect everything and analyze
python -m news_sentiment.main --scrape week --reddit hot --analyze

# Test run: execute without committing to database
python -m news_sentiment.main --scrape week --reddit hot --analyze --test-run
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `--scrape {today,week,month}` | Collect economic events for the specified period |
| `--reddit {hot,new,top}` | Fetch Reddit posts using the specified sort mode |
| `--reddit-limit N` | Number of posts per subreddit (default: 25) |
| `--subreddits SUB1 SUB2...` | Specific subreddits to fetch from |
| `--analyze` | Analyze unscored content with Gemini sentiment analysis |
| `--forex PAIR` | Query forex pair sentiment (e.g., EURUSD, GBPJPY) |
| `--forex-all` | Show sentiment for all major forex pairs |
| `--test-run` | Test mode - do not commit changes to database |

### Default Subreddits

When `--subreddits` is not specified, posts are fetched from:
- r/wallstreetbets
- r/stocks
- r/investing
- r/options
- r/Economics
- r/finance

### Forex Sentiment Query

Query sentiment for currency pairs based on economic calendar events:

```bash
# Query specific pair
python -m news_sentiment.main --forex EURUSD

# Query all major pairs
python -m news_sentiment.main --forex-all
```

**Example Output:**

```
======================================================================
EUR/USD SENTIMENT
======================================================================
Sentiment:  +0.350 (bullish)
Signal:     Favor EUR strength / USD weakness
Base (EUR):   +0.450 (12 events)
Quote (USD):  -0.200 (7 events)
Period:     Last 168 hours
```

**Supported Pairs:** EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD, EURGBP, EURJPY, GBPJPY

## Docker Usage

### Available Services

| Service | Command | Description |
|---------|---------|-------------|
| `app` | `docker compose run --rm app` | Interactive CLI |
| `scraper` | `docker compose --profile scraper run --rm scraper` | Full pipeline: collect + analyze |
| `forex` | `docker compose --profile forex run --rm forex` | Query EUR/USD sentiment |
| `eurusd-monitor` | `docker compose up -d eurusd-monitor` | Continuous EUR/USD monitoring |
| `postgres` | `docker compose --profile local-db up -d postgres` | Local PostgreSQL |

### EUR/USD Continuous Monitor

Run a background service that continuously monitors and analyzes EUR/USD sentiment:

```bash
# Start the monitor (runs every 30 minutes)
docker compose up -d eurusd-monitor

# View live logs
docker compose logs -f eurusd-monitor

# Stop the monitor
docker compose down eurusd-monitor
```

The monitor:
- Collects Forex Factory economic events for EUR and USD
- Fetches posts from Reddit forex communities (r/Forex, r/forex_trades, r/ForexFactory, r/Economics, r/wallstreetbets)
- Analyzes new content with Gemini AI
- Displays EUR/USD sentiment with trading signal every 30 minutes

### Custom Commands

```bash
# Run any CLI command
docker compose run --rm app python -m news_sentiment.main --scrape today

# Fetch Reddit posts only
docker compose run --rm app python -m news_sentiment.main --reddit hot

# Query specific forex pair
docker compose run --rm app python -m news_sentiment.main --forex GBPJPY
```

### Environment File Format

Docker requires a specific format for `.env.docker` (no quotes, no `export`):

```bash
# .env.docker format
AI_MODEL_DB_HOST=your-db-host
AI_MODEL_DB_PORT=5432
AI_MODEL_DB_NAME=ai_model
AI_MODEL_DB_USER=ai_model
AI_MODEL_DB_PASSWORD=your-password
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
GEMINI_API_KEY=your-gemini-key
```

## Database Schema

This service uses a PostgreSQL database (`ai_model`) for sentiment data storage.

### Tables Overview

| Table | Purpose | Migration |
|-------|---------|-----------|
| `economic_events` | Forex Factory calendar events | 002 |
| `reddit_posts` | Reddit financial posts with sentiment | 003, 004 |

### economic_events

Stores economic calendar events collected from Forex Factory.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NOT NULL | Primary key, auto-increment |
| `timestamp` | TIMESTAMP | NOT NULL | Event date/time |
| `currency` | VARCHAR(10) | NOT NULL | Currency code (USD, EUR, GBP, etc.) |
| `event_name` | VARCHAR(255) | NOT NULL | Economic indicator name |
| `impact` | VARCHAR(20) | NOT NULL | Impact level: Low, Medium, High, Holiday |
| `actual` | VARCHAR(50) | NULL | Actual released value |
| `forecast` | VARCHAR(50) | NULL | Market forecast |
| `previous` | VARCHAR(50) | NULL | Previous period value |
| `sentiment_score` | DOUBLE PRECISION | NULL | AI sentiment score (-1.0 to +1.0) |
| `raw_response` | JSONB | NULL | Full Gemini API response |
| `created_at` | TIMESTAMP | NULL | Record creation time |
| `updated_at` | TIMESTAMP | NULL | Last update time |

**Indexes:**
- `idx_economic_events_timestamp` - Fast time-based queries
- `idx_economic_events_currency` - Filter by currency
- `idx_economic_events_event_name` - Search by event
- `idx_economic_events_impact` - Filter by impact level
- `idx_economic_events_timestamp_currency` - Composite for forex queries
- `uq_economic_events_timestamp_event_currency` - Unique constraint

### reddit_posts

Stores Reddit posts from financial subreddits with AI-analyzed sentiment.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NOT NULL | Primary key, auto-increment |
| `reddit_id` | VARCHAR(20) | NOT NULL | Unique Reddit post ID |
| `subreddit` | VARCHAR(50) | NOT NULL | Subreddit name (wallstreetbets, stocks, etc.) |
| `title` | TEXT | NOT NULL | Post title |
| `body` | TEXT | NULL | Post content/selftext |
| `url` | TEXT | NULL | Linked URL or post URL |
| `score` | INTEGER | NULL | Reddit upvote score |
| `num_comments` | INTEGER | NULL | Number of comments |
| `flair` | VARCHAR(100) | NULL | Post flair/tag |
| `timestamp` | TIMESTAMP | NOT NULL | Post creation time on Reddit |
| `fetched_at` | TIMESTAMP | NULL | When collected by this service |
| `symbols` | TEXT[] | NULL | Extracted ticker symbols (e.g., ['NVDA', 'AAPL']) |
| `symbol_sentiments` | JSONB | NULL | Per-symbol sentiment scores |
| `sentiment_score` | DOUBLE PRECISION | NULL | Overall AI sentiment score (-1.0 to +1.0) |
| `raw_response` | JSONB | NULL | Full Gemini API response |
| `created_at` | TIMESTAMP | NULL | Record creation time |
| `updated_at` | TIMESTAMP | NULL | Last update time |

**Indexes:**
- `idx_reddit_posts_reddit_id` - Fast lookup by Reddit ID
- `idx_reddit_posts_subreddit` - Filter by subreddit
- `idx_reddit_posts_timestamp` - Time-based queries
- `idx_reddit_posts_fetched_at` - Track data freshness
- `idx_reddit_posts_score` - Sort by popularity
- `idx_reddit_posts_symbols` - GIN index for array search
- `idx_reddit_posts_subreddit_timestamp` - Composite for subreddit timelines
- `reddit_posts_reddit_id_key` - Unique constraint

## Sentiment Score Interpretation

The sentiment score ranges from **-1.0 to 1.0**:

| Score Range | Interpretation | Trading Signal |
|-------------|----------------|----------------|
| +0.7 to +1.0 | Strongly Bullish | Strong buy signal |
| +0.3 to +0.7 | Bullish | Moderate buy signal |
| -0.3 to +0.3 | Neutral | No directional bias |
| -0.7 to -0.3 | Bearish | Moderate sell signal |
| -1.0 to -0.7 | Strongly Bearish | Strong sell signal |

### How Scores Are Determined

**For Economic Events:**
- **Actual vs Forecast**: Beat = bullish, miss = bearish
- **Magnitude**: Larger deviations = stronger sentiment
- **Event Impact**: High-impact events weighted more heavily
- **Historical Context**: Gemini considers indicator significance

**For Reddit Posts:**
- **Tone & Language**: Bullish/bearish keywords and sentiment
- **Specific Mentions**: Stocks, sectors, market predictions
- **Flair Context**: Post category (DD, YOLO, Loss, Gain, etc.)
- **Community Engagement**: Upvotes and comments as signals

## Ticker Extraction & Per-Symbol Sentiment

The service automatically extracts ticker symbols from Reddit posts and provides per-symbol sentiment scores.

### Example Output

```
Post: "Just bought $NVDA and $TSLA calls, selling my $AAPL position. BTC looking strong."

Analysis Result:
{
  "sentiment_score": 0.70,           # Overall bullish
  "symbols": ["NVDA", "TSLA", "AAPL", "BTC"],
  "symbol_sentiments": {
    "NVDA": 0.9,    # Very bullish (buying calls, "going to moon")
    "TSLA": 0.8,    # Bullish (buying calls)
    "AAPL": -0.7,   # Bearish (selling position)
    "BTC": 0.3      # Slightly bullish ("looking strong")
  }
}
```

### Supported Symbol Types

| Type | Examples | Detection Method |
|------|----------|------------------|
| **Stocks** | NVDA, AAPL, TSLA, GME | Cashtag ($NVDA) or known tickers |
| **Crypto** | BTC, ETH, SOL, DOGE | Cashtag or crypto symbol list |
| **ETFs** | SPY, QQQ, ARKK, VTI | Cashtag or known ETFs |

### Querying by Symbol

```sql
-- Find all posts mentioning NVDA
SELECT * FROM reddit_posts WHERE 'NVDA' = ANY(symbols);

-- Get average sentiment for NVDA
SELECT AVG((symbol_sentiments->>'NVDA')::float) as avg_sentiment
FROM reddit_posts
WHERE symbol_sentiments ? 'NVDA';

-- Most mentioned symbols
SELECT unnest(symbols) as symbol, COUNT(*) as mentions
FROM reddit_posts
GROUP BY symbol
ORDER BY mentions DESC
LIMIT 10;
```

## Example Output

```
$ python scripts/test_pipeline.py

============================================================
  NEWS SENTIMENT PIPELINE - INTEGRATION TEST
============================================================

✅ Database connection: OK
✅ ForexFactory collector: OK
✅ Reddit client: OK
✅ Reddit storage: OK
✅ Sentiment analyzer: OK
✅ Full pipeline: OK

  Success Rate: 100.0%
```

### Sample Sentiment Analysis

```
REDDIT SENTIMENT DATABASE - COMPLETE ANALYSIS
======================================================================

Total Posts: 212
Average Sentiment: +0.075 (slightly bullish)

Sentiment Distribution:
  🟢 Bullish (> +0.2):   70 (33.0%)
  ⚪ Neutral:            86 (40.6%)
  🔴 Bearish (< -0.2):   56 (26.4%)

By Subreddit:
  🟢 r/wallstreetbets  | 50 posts | avg: +0.18
  🟢 r/stocks          | 50 posts | avg: +0.18
  ⚪ r/investing       | 30 posts | avg: +0.04
  ⚪ r/Economics       | 29 posts | avg: -0.08
```

## Running the Test Suite

```bash
# Run full integration test
python scripts/test_pipeline.py

# Run unit tests
pytest

# Run with coverage
pytest --cov=src/news_sentiment --cov-report=term-missing
```

## Development

### Code Quality

```bash
# Format code with Black
black src tests

# Lint with Ruff
ruff check src tests

# Type checking with mypy
mypy src
```

### Project Structure

```
news-sentiment/
├── src/
│   └── news_sentiment/
│       ├── __init__.py
│       ├── main.py                 # CLI entry point
│       ├── forex_sentiment.py      # Forex pair sentiment calculator
│       ├── analyzer/
│       │   ├── __init__.py
│       │   └── gemini.py           # Gemini 2.0 Flash analyzer
│       ├── database/
│       │   ├── __init__.py
│       │   └── models.py           # SQLAlchemy ORM models
│       └── scraper/
│           ├── __init__.py
│           ├── ff_scraper.py       # Forex Factory data collector
│           └── reddit_scraper.py   # Reddit API client
├── scripts/
│   └── test_pipeline.py            # Integration test suite
├── migrations/
│   ├── 001_create_schema.sql
│   ├── 002_fix_raw_response_type.sql
│   ├── 003_create_reddit_posts_table.sql
│   └── 004_add_ticker_extraction.sql
├── tests/                          # Unit tests
├── Dockerfile                      # Multi-stage Docker build
├── docker-compose.yml              # Service orchestration
├── .dockerignore                   # Docker build exclusions
├── pyproject.toml                  # Project configuration
├── .env.example                    # Environment template (shell)
└── README.md                       # This file
```

## Migrations

Run database migrations in order:

```bash
# Set environment variables
export DB_HOST=your-db-host
export DB_USER=ai_model
export DB_NAME=ai_model
export PGPASSWORD=your-password

# 001: EURUSD rates tables (optional - for markets database)
# psql -h $DB_HOST -U $DB_USER -d markets -f migrations/001_create_eurusd_rates_tables.sql

# 002: Create economic_events table
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/002_create_economic_events_table.sql

# 003: Create reddit_posts table
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/003_create_reddit_posts_table.sql

# 004: Add ticker extraction columns (fetched_at, symbols, symbol_sentiments)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/004_add_ticker_extraction.sql
```

**Migration Files:**

| File | Description |
|------|-------------|
| `001_create_eurusd_rates_tables.sql` | EURUSD OHLC price data (markets database) |
| `002_create_economic_events_table.sql` | Economic calendar events table |
| `003_create_reddit_posts_table.sql` | Reddit posts table |
| `004_add_ticker_extraction.sql` | Add symbols & symbol_sentiments columns |

Or via Python:

```python
from news_sentiment.database import get_session
from sqlalchemy import text

with get_session() as session:
    session.execute(text(open('migrations/003_create_reddit_posts_table.sql').read()))
    session.commit()
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests first (TDD)
4. Implement your changes
5. Ensure all tests pass (`pytest`)
6. Ensure code quality (`black . && ruff check .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request
