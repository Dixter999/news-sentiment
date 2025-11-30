"""
SQLAlchemy ORM models for the News Sentiment database.

This module defines the database schema for storing economic events
and their sentiment analysis results.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EconomicEvent(Base):
    """Model representing an economic calendar event.

    Stores scraped event data from ForexFactory along with
    sentiment analysis results from Gemini.

    Attributes:
        id: Primary key
        timestamp: Event date/time
        currency: Currency affected (e.g., "USD", "EUR")
        event_name: Name of the economic event
        impact: Impact level ("Low", "Medium", "High")
        actual: Actual value when released
        forecast: Market forecast value
        previous: Previous period's value
        sentiment_score: AI-generated sentiment score (-1.0 to 1.0)
        raw_response: Raw AI model response
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    __tablename__ = "economic_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    currency = Column(String(10), nullable=False, index=True)
    event_name = Column(String(255), nullable=False, index=True)
    impact = Column(String(20), nullable=True)
    actual = Column(String(50), nullable=True)
    forecast = Column(String(50), nullable=True)
    previous = Column(String(50), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        Returns:
            Dictionary representation of the event with all fields
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "currency": self.currency,
            "event_name": self.event_name,
            "impact": self.impact,
            "actual": self.actual,
            "forecast": self.forecast,
            "previous": self.previous,
            "sentiment_score": self.sentiment_score,
            "raw_response": self.raw_response,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict_for_gemini(self) -> Dict[str, Any]:
        """Convert model to dictionary for Gemini sentiment analysis.

        Returns only the fields needed for sentiment analysis,
        excluding internal fields like id, timestamps, and existing scores.

        Returns:
            Dictionary with event data for Gemini analysis
        """
        return {
            "event_name": self.event_name,
            "currency": self.currency,
            "impact": self.impact,
            "actual": self.actual,
            "forecast": self.forecast,
            "previous": self.previous,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EconomicEvent":
        """Create an EconomicEvent instance from a dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            EconomicEvent instance

        Example:
            >>> data = {
            ...     "timestamp": datetime.now(),
            ...     "currency": "USD",
            ...     "event_name": "Non-Farm Payrolls",
            ...     "impact": "High",
            ... }
            >>> event = EconomicEvent.from_dict(data)
        """
        return cls(
            timestamp=data.get("timestamp"),
            currency=data.get("currency"),
            event_name=data.get("event_name"),
            impact=data.get("impact"),
            actual=data.get("actual"),
            forecast=data.get("forecast"),
            previous=data.get("previous"),
            sentiment_score=data.get("sentiment_score"),
            raw_response=data.get("raw_response"),
        )

    def __repr__(self) -> str:
        """String representation of the event."""
        return (
            f"<EconomicEvent("
            f"id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"currency={self.currency}, "
            f"event_name={self.event_name!r}"
            f")>"
        )
