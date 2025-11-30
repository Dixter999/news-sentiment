# News Sentiment Service

A Python service that scrapes economic calendar events from Forex Factory and analyzes them using Google Gemini LLM to generate sentiment scores for trading decisions.

## Project Overview

This service provides automated collection and sentiment analysis of economic news events. It:

1. **Scrapes** economic calendar data from [Forex Factory](https://www.forexfactory.com/calendar) using Playwright browser automation
2. **Analyzes** events using Google Gemini AI to determine market sentiment impact
3. **Stores** results in PostgreSQL for downstream trading applications

## Architecture

```
                              News Sentiment Service
    +-----------------------------------------------------------------+
    |                                                                 |
    |  +-----------------+     +------------------+     +-----------+ |
    |  |                 |     |                  |     |           | |
    |  |  Forex Factory  |---->|  Playwright      |---->|  Economic | |
    |  |  Calendar       |     |  Scraper         |     |  Events   | |
    |  |                 |     |                  |     |           | |
    |  +-----------------+     +------------------+     +-----+-----+ |
    |                                                         |       |
    |                                                         v       |
    |  +-----------------+     +------------------+     +-----------+ |
    |  |                 |     |                  |     |           | |
    |  |  PostgreSQL     |<----|  Sentiment       |<----|  Gemini   | |
    |  |  Database       |     |  Scores          |     |  Analyzer | |
    |  |                 |     |                  |     |           | |
    |  +-----------------+     +------------------+     +-----------+ |
    |                                                                 |
    +-----------------------------------------------------------------+
```

**Data Flow:**
1. Playwright navigates to Forex Factory and scrapes calendar events
2. Events are parsed and stored in the `economic_events` table
3. Gemini analyzes events with actual values to generate sentiment scores
4. Scores are stored back to the database for trading strategy consumption

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Chromium browser (installed via Playwright)

## Installation

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

# Markets Database (READ-ONLY) - for reading market data
MARKETS_DB_HOST=localhost
MARKETS_DB_PORT=5432
MARKETS_DB_NAME=markets
MARKETS_DB_USER=markets
MARKETS_DB_PASSWORD=your-markets-password

# AI Model Database (READ-WRITE) - for storing sentiment results
AI_MODEL_DB_HOST=localhost
AI_MODEL_DB_PORT=5432
AI_MODEL_DB_NAME=ai_model
AI_MODEL_DB_USER=ai_model
AI_MODEL_DB_PASSWORD=your-ai-model-password
```

## CLI Usage

The service is invoked as a Python module:

```bash
# Show help
python -m news_sentiment.main --help

# Scrape events for the current week
python -m news_sentiment.main --scrape week

# Scrape events for today only
python -m news_sentiment.main --scrape today

# Scrape events for the current month
python -m news_sentiment.main --scrape month

# Analyze unscored events (requires GEMINI_API_KEY)
python -m news_sentiment.main --analyze

# Combined: scrape week and analyze
python -m news_sentiment.main --scrape week --analyze

# Test run: execute without committing to database
python -m news_sentiment.main --scrape week --analyze --test-run
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `--scrape {today,week,month}` | Scrape economic events for the specified period |
| `--analyze` | Analyze unscored events with Gemini sentiment analysis |
| `--test-run` | Test mode - do not commit changes to database |

## Database Schema

The service uses the `economic_events` table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `timestamp` | DATETIME | Event date/time (indexed) |
| `currency` | VARCHAR(10) | Currency affected, e.g., "USD", "EUR" (indexed) |
| `event_name` | VARCHAR(255) | Name of the economic event (indexed) |
| `impact` | VARCHAR(20) | Impact level: "Low", "Medium", "High", "Holiday" |
| `actual` | VARCHAR(50) | Actual released value |
| `forecast` | VARCHAR(50) | Market forecast value |
| `previous` | VARCHAR(50) | Previous period's value |
| `sentiment_score` | FLOAT | AI-generated score from -1.0 to 1.0 |
| `raw_response` | TEXT | Raw Gemini API response (JSON) |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

## Sentiment Score Interpretation

The sentiment score ranges from **-1.0 to 1.0**:

| Score Range | Interpretation | Trading Signal |
|-------------|----------------|----------------|
| 0.7 to 1.0 | Strongly Bullish | Strong buy signal for currency |
| 0.3 to 0.7 | Bullish | Moderate buy signal |
| -0.3 to 0.3 | Neutral | No directional bias |
| -0.7 to -0.3 | Bearish | Moderate sell signal |
| -1.0 to -0.7 | Strongly Bearish | Strong sell signal for currency |

**How scores are determined:**
- **Actual vs Forecast**: Beat = bullish, miss = bearish
- **Magnitude**: Larger deviations = stronger sentiment
- **Event Impact**: High-impact events weighted more heavily
- **Historical Context**: Gemini considers indicator significance

## Verification

To verify the service is working correctly:

```bash
# 1. Run the test suite (438 tests)
pytest

# 2. Test scraping (dry run)
python -m news_sentiment.main --scrape today --test-run

# 3. Verify database connection
python -c "from news_sentiment.database import get_session; print('DB OK')"

# 4. Verify Gemini API connection
python -c "from news_sentiment.analyzer.gemini import SentimentAnalyzer; SentimentAnalyzer(); print('API OK')"
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/news_sentiment --cov-report=term-missing

# Run specific test file
pytest tests/test_scraper.py -v
```

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
│       ├── main.py              # CLI entry point
│       ├── analyzer/
│       │   ├── __init__.py
│       │   └── gemini.py        # Gemini sentiment analyzer
│       ├── database/
│       │   ├── __init__.py
│       │   └── models.py        # SQLAlchemy ORM models
│       └── scraper/
│           ├── __init__.py
│           └── ff_scraper.py    # Forex Factory scraper
├── tests/                       # Test suite (438 tests)
├── pyproject.toml              # Project configuration
├── .env.example                # Environment template
└── README.md                   # This file
```

## Quality Metrics

- **Test Coverage**: 438 tests passing
- **Code Style**: Black + Ruff enforced
- **Type Safety**: Full type hints with mypy validation

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
