"""
Prompt templates and utilities for Gemini sentiment analysis.

This module provides the prompt template and helper functions for
building prompts to send to Google Gemini for economic event
sentiment analysis.

Stream B - Issue #4: Implement Gemini Sentiment Analyzer
"""

from typing import Any


SENTIMENT_PROMPT_TEMPLATE = """
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


def format_value(value: Any) -> str:
    """Format a value for the prompt, handling None/empty values.

    Args:
        value: The value to format. Can be any type including None,
               numbers, strings, etc.

    Returns:
        String representation of the value, or 'N/A' for None/empty.

    Examples:
        >>> format_value(3.5)
        '3.5'
        >>> format_value(None)
        'N/A'
        >>> format_value("")
        'N/A'
        >>> format_value(0)
        '0'
    """
    # Handle None explicitly
    if value is None:
        return "N/A"

    # Handle strings - check for empty or whitespace-only
    if isinstance(value, str):
        if not value.strip():
            return "N/A"
        return value

    # Handle numeric types (int, float)
    # Note: 0 and 0.0 are valid values, not falsy for our purposes
    return str(value)


def build_sentiment_prompt(event: dict) -> str:
    """Build a sentiment analysis prompt from an event dictionary.

    Args:
        event: Dictionary with event data containing:
            - event_name: Name of the economic event
            - currency: Currency affected by the event
            - impact: Impact level (Low/Medium/High)
            - actual: Actual released value (may be None)
            - forecast: Forecasted value
            - previous: Previous period's value

    Returns:
        Formatted prompt string ready to send to Gemini API.

    Examples:
        >>> event = {
        ...     "event_name": "Non-Farm Payrolls",
        ...     "currency": "USD",
        ...     "impact": "High",
        ...     "actual": 250,
        ...     "forecast": 200,
        ...     "previous": 180
        ... }
        >>> prompt = build_sentiment_prompt(event)
        >>> "Non-Farm Payrolls" in prompt
        True
    """
    return SENTIMENT_PROMPT_TEMPLATE.format(
        event_name=format_value(event.get("event_name")),
        currency=format_value(event.get("currency")),
        impact=format_value(event.get("impact")),
        actual=format_value(event.get("actual")),
        forecast=format_value(event.get("forecast")),
        previous=format_value(event.get("previous")),
    )
