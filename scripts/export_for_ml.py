#!/usr/bin/env python3
"""
Export sentiment data for ML models (PPO/SAC).

Usage:
    python scripts/export_for_ml.py [--pair EURUSD] [--format csv|parquet] [--output FILE]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_sentiment.database import EconomicEvent, get_session


def export_raw_events(output_path: str, format: str = "parquet") -> None:
    """Export all events as raw data."""
    with get_session() as session:
        events = session.query(EconomicEvent).filter(
            EconomicEvent.timestamp >= "2022-01-01"
        ).order_by(EconomicEvent.timestamp).all()

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
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    if format == "csv":
        df.to_csv(output_path, index=False)
    else:
        df.to_parquet(output_path, index=False)

    print(f"Exported {len(df)} events to {output_path}")


def export_pair_features(pair: str, output_path: str, format: str = "parquet") -> None:
    """Export features for a specific currency pair."""
    base = pair[:3].upper()
    quote = pair[3:].upper()

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

    # Separate by currency
    base_df = df[df['currency'] == base].set_index('timestamp')['sentiment']
    quote_df = df[df['currency'] == quote].set_index('timestamp')['sentiment']

    # Resample to hourly, forward-fill gaps
    base_hourly = base_df.resample('1H').mean().ffill()
    quote_hourly = quote_df.resample('1H').mean().ffill()

    # Build feature dataframe
    features = pd.DataFrame({
        f'{base}_sentiment': base_hourly,
        f'{quote}_sentiment': quote_hourly,
    }).dropna()

    # Pair sentiment (positive = bullish base, bearish quote)
    features[f'{pair}_sentiment'] = features[f'{base}_sentiment'] - features[f'{quote}_sentiment']

    # Rolling features
    features[f'{pair}_ma4h'] = features[f'{pair}_sentiment'].rolling(4).mean()
    features[f'{pair}_ma24h'] = features[f'{pair}_sentiment'].rolling(24).mean()
    features[f'{pair}_ma7d'] = features[f'{pair}_sentiment'].rolling(24 * 7).mean()

    # Momentum (change from N periods ago)
    features[f'{pair}_momentum_4h'] = features[f'{pair}_sentiment'] - features[f'{pair}_sentiment'].shift(4)
    features[f'{pair}_momentum_24h'] = features[f'{pair}_sentiment'] - features[f'{pair}_sentiment'].shift(24)

    # Volatility (rolling std)
    features[f'{pair}_volatility_24h'] = features[f'{pair}_sentiment'].rolling(24).std()

    features = features.dropna()

    if format == "csv":
        features.to_csv(output_path)
    else:
        features.to_parquet(output_path)

    print(f"Exported {len(features)} hourly rows for {pair} to {output_path}")
    print(f"\nFeatures:")
    for col in features.columns:
        print(f"  - {col}")
    print(f"\nDate range: {features.index.min()} to {features.index.max()}")


def main():
    parser = argparse.ArgumentParser(description="Export sentiment data for ML")
    parser.add_argument(
        "--pair",
        type=str,
        default=None,
        help="Currency pair (e.g., EURUSD). If not specified, exports all raw events."
    )
    parser.add_argument(
        "--format",
        choices=["csv", "parquet"],
        default="parquet",
        help="Output format (default: parquet)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path"
    )

    args = parser.parse_args()

    if args.pair:
        output = args.output or f"{args.pair.lower()}_features.{args.format}"
        export_pair_features(args.pair, output, args.format)
    else:
        output = args.output or f"sentiment_data.{args.format}"
        export_raw_events(output, args.format)


if __name__ == "__main__":
    main()
