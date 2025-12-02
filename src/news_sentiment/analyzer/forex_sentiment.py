"""
Forex Pair Sentiment Calculator.

This module derives forex pair sentiment from economic event analysis.
For example, EUR/USD sentiment is calculated from EUR and USD economic events.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from news_sentiment.database import get_session
from news_sentiment.database.models import EconomicEvent


# Impact weights for sentiment calculation
IMPACT_WEIGHTS = {
    "High": 1.0,
    "Medium": 0.6,
    "Low": 0.3,
    "Holiday": 0.0,
}


def get_currency_sentiment(
    session: Session,
    currency: str,
    hours_back: int = 24,
) -> Dict[str, Any]:
    """Get aggregated sentiment for a single currency.

    Args:
        session: Database session
        currency: Currency code (e.g., "USD", "EUR")
        hours_back: How many hours back to look for events

    Returns:
        Dictionary with:
        - currency: The currency code
        - sentiment: Weighted average sentiment (-1.0 to 1.0)
        - event_count: Number of events analyzed
        - events: List of event summaries
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)

    events = (
        session.query(EconomicEvent)
        .filter(
            EconomicEvent.currency == currency,
            EconomicEvent.timestamp >= cutoff,
            EconomicEvent.sentiment_score.isnot(None),
        )
        .order_by(EconomicEvent.timestamp.desc())
        .all()
    )

    if not events:
        return {
            "currency": currency,
            "sentiment": 0.0,
            "event_count": 0,
            "events": [],
            "message": f"No analyzed events for {currency} in last {hours_back} hours",
        }

    # Calculate weighted sentiment
    total_weight = 0.0
    weighted_sum = 0.0
    event_summaries = []

    for event in events:
        weight = IMPACT_WEIGHTS.get(event.impact, 0.3)
        weighted_sum += event.sentiment_score * weight
        total_weight += weight

        event_summaries.append({
            "name": event.event_name,
            "timestamp": event.timestamp.isoformat(),
            "impact": event.impact,
            "sentiment": event.sentiment_score,
            "actual": event.actual,
            "forecast": event.forecast,
        })

    avg_sentiment = weighted_sum / total_weight if total_weight > 0 else 0.0

    return {
        "currency": currency,
        "sentiment": round(avg_sentiment, 3),
        "event_count": len(events),
        "events": event_summaries,
    }


def get_forex_pair_sentiment(
    pair: str,
    hours_back: int = 24,
) -> Dict[str, Any]:
    """Get sentiment for a forex pair like EUR/USD.

    The sentiment is calculated as: base_sentiment - quote_sentiment
    For EUR/USD: positive = EUR bullish (pair goes up), negative = USD bullish (pair goes down)

    Args:
        pair: Forex pair (e.g., "EURUSD", "EUR/USD", "EUR-USD")
        hours_back: How many hours back to look for events

    Returns:
        Dictionary with:
        - pair: The forex pair
        - sentiment: Combined sentiment (-1.0 to 1.0)
        - direction: "bullish", "bearish", or "neutral"
        - base: Base currency sentiment details
        - quote: Quote currency sentiment details
    """
    # Parse pair
    pair_clean = pair.upper().replace("/", "").replace("-", "").replace("_", "")

    if len(pair_clean) != 6:
        return {"error": f"Invalid pair format: {pair}. Expected format: EURUSD"}

    base_currency = pair_clean[:3]  # EUR
    quote_currency = pair_clean[3:]  # USD

    with get_session() as session:
        base_data = get_currency_sentiment(session, base_currency, hours_back)
        quote_data = get_currency_sentiment(session, quote_currency, hours_back)

    # Calculate pair sentiment
    # Positive base sentiment = base currency strong = pair goes UP
    # Positive quote sentiment = quote currency strong = pair goes DOWN
    pair_sentiment = base_data["sentiment"] - quote_data["sentiment"]
    pair_sentiment = max(-1.0, min(1.0, pair_sentiment))  # Clamp to [-1, 1]

    # Determine direction
    if pair_sentiment > 0.2:
        direction = "bullish"
        signal = f"{base_currency} strength / {quote_currency} weakness"
    elif pair_sentiment < -0.2:
        direction = "bearish"
        signal = f"{quote_currency} strength / {base_currency} weakness"
    else:
        direction = "neutral"
        signal = "No clear directional bias"

    return {
        "pair": f"{base_currency}/{quote_currency}",
        "sentiment": round(pair_sentiment, 3),
        "direction": direction,
        "signal": signal,
        "base": {
            "currency": base_currency,
            "sentiment": base_data["sentiment"],
            "event_count": base_data["event_count"],
        },
        "quote": {
            "currency": quote_currency,
            "sentiment": quote_data["sentiment"],
            "event_count": quote_data["event_count"],
        },
        "hours_analyzed": hours_back,
        "total_events": base_data["event_count"] + quote_data["event_count"],
    }


def get_all_major_pairs_sentiment(hours_back: int = 24) -> List[Dict[str, Any]]:
    """Get sentiment for all major forex pairs.

    Returns:
        List of sentiment data for major pairs
    """
    major_pairs = [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "USDCHF",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
    ]

    results = []
    for pair in major_pairs:
        result = get_forex_pair_sentiment(pair, hours_back)
        results.append(result)

    # Sort by absolute sentiment (most actionable first)
    results.sort(key=lambda x: abs(x.get("sentiment", 0)), reverse=True)

    return results


def search_symbol_sentiment(
    symbol: str,
    hours_back: int = 168,  # 1 week default
) -> Dict[str, Any]:
    """Search for sentiment across both forex events and Reddit posts.

    Args:
        symbol: Symbol to search (e.g., "EURUSD", "NVDA", "BTC")
        hours_back: How many hours back to search

    Returns:
        Combined sentiment data from all sources
    """
    symbol_upper = symbol.upper().replace("/", "").replace("-", "")

    result = {
        "symbol": symbol_upper,
        "forex_sentiment": None,
        "stock_sentiment": None,
        "reddit_mentions": 0,
        "economic_events": 0,
    }

    # Check if it's a forex pair (6 chars)
    if len(symbol_upper) == 6:
        forex_data = get_forex_pair_sentiment(symbol_upper, hours_back)
        if "error" not in forex_data:
            result["forex_sentiment"] = forex_data
            result["economic_events"] = forex_data.get("total_events", 0)

    # Check Reddit posts for symbol mentions
    with get_session() as session:
        # Query Reddit posts with this symbol
        query = text("""
            SELECT
                COUNT(*) as mention_count,
                AVG((symbol_sentiments->>:symbol)::float) as avg_sentiment
            FROM reddit_posts
            WHERE symbols @> ARRAY[:symbol]
            AND timestamp >= NOW() - INTERVAL ':hours hours'
        """)

        # Note: This query might need adjustment based on actual column names
        try:
            reddit_result = session.execute(
                text("""
                    SELECT
                        COUNT(*) as mention_count,
                        AVG((symbol_sentiments->>:symbol)::float) as avg_sentiment
                    FROM reddit_posts
                    WHERE :symbol = ANY(symbols)
                    AND timestamp >= NOW() - INTERVAL '168 hours'
                """),
                {"symbol": symbol_upper},
            ).fetchone()

            if reddit_result and reddit_result.mention_count > 0:
                result["reddit_mentions"] = reddit_result.mention_count
                result["stock_sentiment"] = {
                    "symbol": symbol_upper,
                    "sentiment": round(reddit_result.avg_sentiment or 0, 3),
                    "mention_count": reddit_result.mention_count,
                }
        except Exception:
            # Symbols column might not be populated yet
            pass

    return result
