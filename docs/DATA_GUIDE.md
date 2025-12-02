# News Sentiment Data Guide

## Overview

This database contains economic calendar events from ForexFactory and Reddit posts, enriched with AI-generated sentiment scores using Google Gemini 2.0 Flash.

## Data Summary

| Metric | Value |
|--------|-------|
| Date Range | Jan 2021 - Dec 2025 |
| Total Economic Events | 6,969 |
| Reddit Posts | 421 |
| Sentiment Coverage | 100% |

### Events by Currency

| Currency | Count | Description |
|----------|-------|-------------|
| USD | 1,762 | US Dollar |
| EUR | 1,418 | Euro |
| GBP | 943 | British Pound |
| JPY | 645 | Japanese Yen |
| AUD | 617 | Australian Dollar |
| CAD | 560 | Canadian Dollar |
| NZD | 392 | New Zealand Dollar |
| CNY | 369 | Chinese Yuan |
| CHF | 254 | Swiss Franc |

### Events by Impact

| Impact | Count | Description |
|--------|-------|-------------|
| High | 1,065 | Major market-moving events (NFP, CPI, rate decisions) |
| Medium | 864 | Moderate impact events |
| Low | 4,797 | Minor economic indicators |
| Holiday | 243 | Bank holidays |

---

## Database Schema

### EconomicEvent Table

```
economic_events
├── id              (int)       Primary key
├── event_name      (str)       Event name (e.g., "Non-Farm Payrolls")
├── currency        (str)       Currency code (USD, EUR, GBP, etc.)
├── timestamp       (datetime)  Event datetime (UTC)
├── impact          (str)       High, Medium, Low, Holiday
├── actual          (str)       Actual value released
├── forecast        (str)       Market forecast
├── previous        (str)       Previous period value
├── sentiment_score (float)     AI sentiment score (-1.0 to +1.0)
├── raw_response    (json)      Full Gemini API response
├── created_at      (datetime)  Record creation time
└── updated_at      (datetime)  Last update time
```

### RedditPost Table

```
reddit_posts
├── id              (int)       Primary key
├── post_id         (str)       Reddit post ID
├── subreddit       (str)       Subreddit name
├── title           (str)       Post title
├── content         (str)       Post body
├── score           (int)       Reddit upvotes
├── num_comments    (int)       Comment count
├── created_utc     (datetime)  Post creation time
├── sentiment_score (float)     AI sentiment score (-1.0 to +1.0)
├── raw_response    (json)      Full Gemini API response
└── created_at      (datetime)  Record creation time
```

---

## Sentiment Score Interpretation

| Score Range | Meaning | Color |
|-------------|---------|-------|
| +0.4 to +1.0 | Bullish for currency | Green |
| +0.1 to +0.3 | Slightly bullish | Light green |
| -0.1 to +0.1 | Neutral | Gray |
| -0.3 to -0.1 | Slightly bearish | Light red |
| -1.0 to -0.4 | Bearish for currency | Red |

**Example**: USD CPI actual > forecast → positive score (+0.6) → bullish USD

---

## Python Usage Examples

### Setup

```python
import sys
sys.path.insert(0, "src")

from news_sentiment.database import EconomicEvent, RedditPost, get_session
from sqlalchemy import func
from datetime import datetime, timedelta
```

### Query All Events for a Currency

```python
with get_session() as session:
    usd_events = session.query(EconomicEvent).filter(
        EconomicEvent.currency == "USD"
    ).order_by(EconomicEvent.timestamp.desc()).all()

    for event in usd_events[:5]:
        print(f"{event.timestamp} | {event.event_name} | {event.sentiment_score:+.2f}")
```

### Get High-Impact Events Only

```python
with get_session() as session:
    high_impact = session.query(EconomicEvent).filter(
        EconomicEvent.impact == "High"
    ).order_by(EconomicEvent.timestamp.desc()).limit(20).all()

    for event in high_impact:
        print(f"{event.currency} | {event.event_name} | {event.sentiment_score:+.2f}")
```

### Calculate EUR/USD Sentiment

```python
with get_session() as session:
    # Get recent EUR and USD events (last 24 hours)
    since = datetime.utcnow() - timedelta(hours=24)

    eur_events = session.query(EconomicEvent).filter(
        EconomicEvent.currency == "EUR",
        EconomicEvent.timestamp >= since,
        EconomicEvent.sentiment_score.isnot(None)
    ).all()

    usd_events = session.query(EconomicEvent).filter(
        EconomicEvent.currency == "USD",
        EconomicEvent.timestamp >= since,
        EconomicEvent.sentiment_score.isnot(None)
    ).all()

    eur_sentiment = sum(e.sentiment_score for e in eur_events) / len(eur_events) if eur_events else 0
    usd_sentiment = sum(e.sentiment_score for e in usd_events) / len(usd_events) if usd_events else 0

    # EUR/USD sentiment = EUR strength - USD strength
    eurusd_sentiment = eur_sentiment - usd_sentiment
    print(f"EUR/USD Sentiment: {eurusd_sentiment:+.3f}")
```

### Get Events by Date Range

```python
with get_session() as session:
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)

    events_2024 = session.query(EconomicEvent).filter(
        EconomicEvent.timestamp >= start,
        EconomicEvent.timestamp <= end
    ).all()

    print(f"Events in 2024: {len(events_2024)}")
```

### Aggregate Sentiment by Day

```python
with get_session() as session:
    from sqlalchemy import cast, Date

    daily_sentiment = session.query(
        cast(EconomicEvent.timestamp, Date).label('date'),
        EconomicEvent.currency,
        func.avg(EconomicEvent.sentiment_score).label('avg_sentiment'),
        func.count(EconomicEvent.id).label('event_count')
    ).filter(
        EconomicEvent.currency == "USD"
    ).group_by(
        cast(EconomicEvent.timestamp, Date),
        EconomicEvent.currency
    ).order_by('date').all()

    for row in daily_sentiment[-10:]:
        print(f"{row.date} | {row.currency} | {row.avg_sentiment:+.3f} | {row.event_count} events")
```

---

## Export for ML Models (PPO/SAC)

### Export to CSV

```python
import pandas as pd
from news_sentiment.database import EconomicEvent, get_session

with get_session() as session:
    events = session.query(EconomicEvent).filter(
        EconomicEvent.timestamp >= "2022-01-01"
    ).all()

    data = [{
        'timestamp': e.timestamp,
        'currency': e.currency,
        'event_name': e.event_name,
        'impact': e.impact,
        'actual': e.actual,
        'forecast': e.forecast,
        'previous': e.previous,
        'sentiment_score': e.sentiment_score
    } for e in events]

    df = pd.DataFrame(data)
    df.to_csv('sentiment_data.csv', index=False)
    print(f"Exported {len(df)} events to sentiment_data.csv")
```

### Export to Parquet (Recommended for ML)

```python
import pandas as pd
from news_sentiment.database import EconomicEvent, get_session

with get_session() as session:
    events = session.query(EconomicEvent).filter(
        EconomicEvent.timestamp >= "2022-01-01"
    ).all()

    data = [{
        'timestamp': e.timestamp,
        'currency': e.currency,
        'event_name': e.event_name,
        'impact': e.impact,
        'sentiment_score': e.sentiment_score
    } for e in events]

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp')
    df.to_parquet('sentiment_data.parquet', index=False)
```

### Create Feature Matrix for Trading

```python
import pandas as pd
import numpy as np
from news_sentiment.database import EconomicEvent, get_session

def create_sentiment_features(currency_pair: str = "EURUSD", lookback_hours: int = 24):
    """Create feature matrix for a currency pair."""
    base = currency_pair[:3]  # EUR
    quote = currency_pair[3:]  # USD

    with get_session() as session:
        events = session.query(EconomicEvent).filter(
            EconomicEvent.currency.in_([base, quote]),
            EconomicEvent.timestamp >= "2022-01-01"
        ).order_by(EconomicEvent.timestamp).all()

        data = [{
            'timestamp': e.timestamp,
            'currency': e.currency,
            'impact': e.impact,
            'sentiment': e.sentiment_score
        } for e in events]

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Pivot by currency
    base_df = df[df['currency'] == base].copy()
    quote_df = df[df['currency'] == quote].copy()

    # Resample to hourly and forward-fill
    base_hourly = base_df.set_index('timestamp')['sentiment'].resample('1H').mean().ffill()
    quote_hourly = quote_df.set_index('timestamp')['sentiment'].resample('1H').mean().ffill()

    # Combine
    features = pd.DataFrame({
        f'{base}_sentiment': base_hourly,
        f'{quote}_sentiment': quote_hourly,
    }).dropna()

    # Calculate pair sentiment (base - quote)
    features[f'{currency_pair}_sentiment'] = features[f'{base}_sentiment'] - features[f'{quote}_sentiment']

    # Add rolling features
    features[f'{currency_pair}_sentiment_ma4'] = features[f'{currency_pair}_sentiment'].rolling(4).mean()
    features[f'{currency_pair}_sentiment_ma24'] = features[f'{currency_pair}_sentiment'].rolling(24).mean()

    return features.dropna()

# Usage
features = create_sentiment_features("EURUSD")
features.to_parquet('eurusd_features.parquet')
print(features.tail())
```

---

## SQL Direct Queries

Connect to PostgreSQL:
```bash
psql -h <host> -U ai_model -d ai_model
```

### Recent High-Impact Events
```sql
SELECT timestamp, currency, event_name, sentiment_score
FROM economic_events
WHERE impact = 'High'
ORDER BY timestamp DESC
LIMIT 20;
```

### Daily Sentiment Averages
```sql
SELECT
    DATE(timestamp) as date,
    currency,
    AVG(sentiment_score) as avg_sentiment,
    COUNT(*) as event_count
FROM economic_events
WHERE currency IN ('EUR', 'USD')
GROUP BY DATE(timestamp), currency
ORDER BY date DESC;
```

### EUR/USD Sentiment Calculation
```sql
WITH eur AS (
    SELECT AVG(sentiment_score) as sentiment
    FROM economic_events
    WHERE currency = 'EUR'
    AND timestamp >= NOW() - INTERVAL '24 hours'
),
usd AS (
    SELECT AVG(sentiment_score) as sentiment
    FROM economic_events
    WHERE currency = 'USD'
    AND timestamp >= NOW() - INTERVAL '24 hours'
)
SELECT
    eur.sentiment as eur_sentiment,
    usd.sentiment as usd_sentiment,
    eur.sentiment - usd.sentiment as eurusd_signal
FROM eur, usd;
```

---

## Docker Commands

```bash
# Start continuous monitor
docker-compose up -d eurusd-monitor

# View logs
docker-compose logs -f eurusd-monitor

# Run one-time scrape (all currencies)
docker-compose --profile scraper run --rm scraper

# Stop all
docker-compose down
```

---

## File Locations

```
news-sentiment/
├── src/news_sentiment/
│   ├── database/          # Database models and connection
│   ├── scraper/           # ForexFactory & Reddit scrapers
│   ├── analyzer/          # Gemini sentiment analyzer
│   └── eurusd_monitor.py  # Continuous monitoring service
├── scripts/
│   ├── backfill_forex_factory.py      # Historical data collection
│   ├── analyze_historical_sentiment.py # Batch sentiment analysis
│   └── reprocess_failed_sentiment.py   # Fix failed analyses
└── docs/
    └── DATA_GUIDE.md      # This file
```
