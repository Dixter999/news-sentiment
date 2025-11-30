---
title: News Sentiment Service
status: approved
priority: high
created: 2025-11-30
updated: 2025-11-30
repository: https://github.com/Dixter999/news-sentiment
location: ~/Projects/news-sentiment
related_project: ~/Projects/trading
---

# PRD: News Sentiment Service (Gemini + Playwright)

## Executive Summary

Build a standalone service in the `news-sentiment` repo to ingest Economic Calendar events via a **Playwright scraper**, score them using **Gemini (LLM)**, and store them in the shared AI Model DB. This replaces the previous Selenium/Heuristic approach.

**Goal**: Provide LLM-derived sentiment scores for economic events to improve PPO entry timing.

---

## Problem Statement

The current PPO entry model uses only technical analysis (OHLC + indicators). It has no awareness of scheduled economic events that cause high volatility (NFP, FOMC, CPI). This leads to:
- Entries during high-impact news events with unpredictable outcomes
- Missed opportunities when news aligns with technical signals
- No ability to adjust position sizing based on upcoming volatility

Previous approaches using heuristic rules for sentiment scoring lacked the nuance needed to understand event context and market implications.

---

## Solution Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  news-sentiment repository                       │
│                   ~/Projects/news-sentiment                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Forex Factory Website                                          │
│           ↓ (Playwright scraper)                                 │
│   Economic Event Data (Date, Time, Currency, Impact, etc.)       │
│           ↓ (Gemini LLM Analysis)                                │
│   Sentiment Score (-1.0 to 1.0) + Raw LLM Response               │
│           ↓                                                      │
│   PostgreSQL: economic_events table                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                   Shared PostgreSQL Database
                        (ai_model DB)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    trading repository                            │
│                    ~/Projects/trading                            │
├─────────────────────────────────────────────────────────────────┤
│   entry_env.py queries economic_events table                     │
│   Uses sentiment_score for observation space                     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Separate repo | Yes | News sentiment is a distinct domain, easier to iterate |
| Data source | Forex Factory | Scheduled economic events, predictable, free |
| Scraping method | **Playwright** | More robust than Selenium, better async support, automatic waiting |
| Sentiment analysis | **Gemini LLM** | Semantic understanding of event context and market implications |
| Storage | PostgreSQL | Shared with trading, no new infrastructure |
| Score storage | Same table | `sentiment_score` and `raw_response` in `economic_events` |

---

## Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SCRAPE     │ ──► │   ANALYZE    │ ──► │    STORE     │
│  (Playwright)│     │   (Gemini)   │     │ (PostgreSQL) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  - Navigate FF        - Score event        - Insert/Update
  - Parse table        - sentiment          - economic_events
  - Extract fields     - (-1.0 to 1.0)      - table
```

### Pipeline Steps

1. **Scrape**: Playwright navigates to Forex Factory calendar, extracts event data
2. **Analyze**: For new/unscored events, Gemini generates sentiment score
3. **Store**: Events with scores are stored in `economic_events` table

---

## Database Schema

### Table: economic_events

```sql
CREATE TABLE IF NOT EXISTS economic_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    currency VARCHAR(3),
    event_name VARCHAR(255) NOT NULL,
    impact VARCHAR(20),  -- 'High', 'Medium', 'Low'
    actual VARCHAR(50),
    forecast VARCHAR(50),
    previous VARCHAR(50),
    sentiment_score FLOAT,  -- Gemini score (-1.0 to 1.0)
    raw_response JSONB,     -- Full LLM response for debugging
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timestamp, event_name, currency)
);

CREATE INDEX idx_economic_events_timestamp ON economic_events(timestamp);
CREATE INDEX idx_economic_events_currency ON economic_events(currency);
CREATE INDEX idx_economic_events_impact ON economic_events(impact);
```

### Sentiment Score Interpretation

| Score Range | Interpretation | Example |
|-------------|----------------|---------|
| 0.5 to 1.0 | Strongly Bullish | NFP beats expectations significantly |
| 0.1 to 0.5 | Mildly Bullish | CPI slightly below forecast |
| -0.1 to 0.1 | Neutral | Data meets expectations |
| -0.5 to -0.1 | Mildly Bearish | Unemployment ticks up |
| -1.0 to -0.5 | Strongly Bearish | Major miss on key indicator |

---

## Project Structure

```
~/Projects/news-sentiment/
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI orchestrator
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── ff_scraper.py          # Playwright-based FF scraper
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── gemini.py              # Gemini sentiment analyzer
│   └── database/
│       ├── __init__.py
│       ├── config.py              # DB configuration
│       ├── connection.py          # Connection manager
│       └── models.py              # SQLAlchemy models
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_scraper.py            # Scraper tests
│   ├── test_analyzer.py           # Gemini analyzer tests
│   └── test_integration.py        # End-to-end tests
├── migrations/
│   └── 001_create_events_table.sql
├── .env.example
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

---

## Dependencies

### pyproject.toml

```toml
[project]
name = "news-sentiment"
version = "0.1.0"
description = "Economic calendar scraping and LLM sentiment analysis for trading"
requires-python = ">=3.11"
dependencies = [
    "playwright>=1.40.0",
    "google-generativeai>=0.3.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.9",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --tb=short"
asyncio_mode = "auto"
```

---

## Environment Variables

### .env.example

```env
# Database Connection (shared with trading)
DB_HOST=10.0.0.4
DB_PORT=5432
DB_NAME=ai_model
DB_USER=ai_model
DB_PASSWORD=your_password_here

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro

# Scraper Settings
SCRAPER_HEADLESS=true
SCRAPER_TIMEOUT=30000
```

---

## Implementation Details

### Scraper (Playwright)

**File**: `src/scraper/ff_scraper.py`

```python
from playwright.sync_api import sync_playwright, Page
from datetime import datetime
from typing import List, Dict

class ForexFactoryScraper:
    """Playwright-based scraper for Forex Factory economic calendar."""

    BASE_URL = "https://www.forexfactory.com/calendar"

    def __init__(self, headless: bool = True):
        self.headless = headless

    def scrape_week(self, date: datetime) -> List[Dict]:
        """Scrape events for a specific week."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            # Navigate to calendar
            url = f"{self.BASE_URL}?week={date.strftime('%b%d.%Y')}"
            page.goto(url)
            page.wait_for_selector(".calendar__row")

            events = self._parse_calendar_table(page)
            browser.close()

        return events

    def _parse_calendar_table(self, page: Page) -> List[Dict]:
        """Parse the calendar table and extract events."""
        events = []
        rows = page.query_selector_all(".calendar__row")

        current_date = None
        for row in rows:
            # Extract date (spans multiple rows)
            date_cell = row.query_selector(".calendar__date")
            if date_cell:
                current_date = self._parse_date(date_cell.inner_text())

            # Extract event data
            time_cell = row.query_selector(".calendar__time")
            currency_cell = row.query_selector(".calendar__currency")
            impact_cell = row.query_selector(".calendar__impact span")
            event_cell = row.query_selector(".calendar__event")
            actual_cell = row.query_selector(".calendar__actual")
            forecast_cell = row.query_selector(".calendar__forecast")
            previous_cell = row.query_selector(".calendar__previous")

            if event_cell:
                events.append({
                    "timestamp": self._combine_datetime(current_date, time_cell),
                    "currency": currency_cell.inner_text() if currency_cell else None,
                    "impact": self._parse_impact(impact_cell),
                    "event_name": event_cell.inner_text().strip(),
                    "actual": actual_cell.inner_text() if actual_cell else None,
                    "forecast": forecast_cell.inner_text() if forecast_cell else None,
                    "previous": previous_cell.inner_text() if previous_cell else None,
                })

        return events
```

### Analyzer (Gemini)

**File**: `src/analyzer/gemini.py`

```python
import google.generativeai as genai
from typing import Dict, Optional
import json
import os

class SentimentAnalyzer:
    """Gemini-based sentiment analyzer for economic events."""

    PROMPT_TEMPLATE = """
    Analyze the following economic event and provide a sentiment score.

    Event: {event_name}
    Currency: {currency}
    Impact Level: {impact}
    Actual: {actual}
    Forecast: {forecast}
    Previous: {previous}

    Score the sentiment impact on {currency} from -1.0 (strongly bearish) to 1.0 (strongly bullish).

    Consider:
    - Whether actual beat/missed forecast
    - The magnitude of the difference
    - Historical significance of this indicator
    - Market expectations

    Respond with JSON only:
    {{"score": <float>, "reasoning": "<brief explanation>"}}
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)

    def analyze(self, event: Dict) -> Dict:
        """Analyze an economic event and return sentiment score."""
        prompt = self.PROMPT_TEMPLATE.format(
            event_name=event.get("event_name", "Unknown"),
            currency=event.get("currency", "Unknown"),
            impact=event.get("impact", "Unknown"),
            actual=event.get("actual", "N/A"),
            forecast=event.get("forecast", "N/A"),
            previous=event.get("previous", "N/A"),
        )

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)

            return {
                "sentiment_score": float(result.get("score", 0.0)),
                "raw_response": {
                    "reasoning": result.get("reasoning", ""),
                    "full_response": response.text,
                },
            }
        except Exception as e:
            return {
                "sentiment_score": 0.0,
                "raw_response": {"error": str(e)},
            }
```

### Orchestrator (Main)

**File**: `src/main.py`

```python
import argparse
from datetime import datetime, timedelta
from scraper.ff_scraper import ForexFactoryScraper
from analyzer.gemini import SentimentAnalyzer
from database.models import EconomicEvent
from database.connection import get_session

def main():
    parser = argparse.ArgumentParser(description="News Sentiment Service")
    parser.add_argument("--scrape", choices=["today", "week", "month"], help="Scrape period")
    parser.add_argument("--analyze", action="store_true", help="Analyze unscored events")
    parser.add_argument("--test-run", action="store_true", help="Test run (no DB commit)")
    args = parser.parse_args()

    scraper = ForexFactoryScraper()
    analyzer = SentimentAnalyzer()

    if args.scrape:
        # Scrape events
        events = scraper.scrape_week(datetime.now())
        print(f"Scraped {len(events)} events")

        if not args.test_run:
            with get_session() as session:
                for event in events:
                    db_event = EconomicEvent(**event)
                    session.merge(db_event)
                session.commit()

    if args.analyze:
        # Analyze unscored events
        with get_session() as session:
            unscored = session.query(EconomicEvent).filter(
                EconomicEvent.sentiment_score.is_(None)
            ).all()

            for event in unscored:
                result = analyzer.analyze(event.to_dict())
                event.sentiment_score = result["sentiment_score"]
                event.raw_response = result["raw_response"]

            if not args.test_run:
                session.commit()

            print(f"Analyzed {len(unscored)} events")

if __name__ == "__main__":
    main()
```

---

## Implementation Phases

### Phase 1: Project Setup (Day 1)

1. Create project structure
2. Set up `pyproject.toml` with dependencies
3. Create `.env.example`
4. Install Playwright: `playwright install chromium`

### Phase 2: Database Layer (Day 1)

1. Create `migrations/001_create_events_table.sql`
2. Implement SQLAlchemy models in `models.py`
3. Set up connection manager
4. Run migration against ai_model database

### Phase 3: Playwright Scraper (Day 2)

1. Implement `ForexFactoryScraper` class
2. Handle calendar navigation and pagination
3. Parse table rows and extract all fields
4. Handle timezone conversion (ET → UTC)

### Phase 4: Gemini Analyzer (Day 2-3)

1. Implement `SentimentAnalyzer` class
2. Design effective prompt for sentiment scoring
3. Handle rate limits and API errors
4. Parse and validate LLM responses

### Phase 5: Orchestration & Testing (Day 3-4)

1. Implement CLI orchestrator (`main.py`)
2. Write unit tests for scraper
3. Write unit tests for analyzer
4. Write integration tests

---

## Verification Plan

### Automated Tests

**Scraper Test** (`tests/test_scraper.py`):
- Mock Playwright or run headless
- Verify extraction of all data fields from sample HTML
- Test pagination handling
- Test timezone conversion

**Analyzer Test** (`tests/test_analyzer.py`):
- Mock Gemini API responses
- Verify score parsing and validation
- Test error handling for API failures
- Test rate limit handling

**Integration Test** (`tests/test_integration.py`):
- Full pipeline: Scrape → Analyze → Store
- Uses test database or `--test-run` mode

### Manual Verification

1. **Run test scrape**:
   ```bash
   python src/main.py --scrape week --test-run
   ```

2. **Run full pipeline**:
   ```bash
   python src/main.py --scrape week --analyze
   ```

3. **Verify in database**:
   ```sql
   SELECT timestamp, event_name, currency, impact, sentiment_score
   FROM economic_events
   WHERE sentiment_score IS NOT NULL
   ORDER BY timestamp DESC
   LIMIT 10;
   ```

4. **Spot check**: Verify NFP beat = positive score, miss = negative score

---

## Success Metrics

### This Project
- [ ] Scraper extracts all FF calendar fields correctly
- [ ] Gemini generates meaningful sentiment scores (-1.0 to 1.0)
- [ ] All events stored in `economic_events` table
- [ ] `raw_response` captures LLM reasoning for debugging
- [ ] Test coverage > 80%

### Integration Phase (Trading Project)
- [ ] PPO can query sentiment scores by timestamp
- [ ] Observation space includes sentiment feature
- [ ] No regression in model performance

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FF blocks scraping | Medium | High | Rate limiting, headless mode, user agent rotation |
| Gemini rate limits | Medium | Medium | Batch processing, exponential backoff, caching |
| Inconsistent LLM scores | Low | Medium | Prompt engineering, score validation, fallback to 0.0 |
| API key exposure | Low | High | Environment variables, never commit keys |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Project Setup | 0.5 day | Structure, dependencies |
| 2. Database Layer | 0.5 day | Schema, models |
| 3. Playwright Scraper | 1 day | Working scraper |
| 4. Gemini Analyzer | 1.5 days | Sentiment scoring |
| 5. Orchestration & Testing | 1 day | CLI, tests |
| **Total** | **4-5 days** | Complete MVP |

---

## CLI Usage

```bash
# Install
pip install -e ".[dev]"
playwright install chromium

# Scrape this week's events
python src/main.py --scrape week

# Analyze unscored events
python src/main.py --analyze

# Full pipeline
python src/main.py --scrape week --analyze

# Test run (no DB writes)
python src/main.py --scrape week --analyze --test-run
```

---

*Updated 2025-11-30 - Changed from Selenium/Heuristics to Playwright/Gemini architecture*
