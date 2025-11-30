"""
Test fixtures for news-sentiment scraper tests.

This module provides sample HTML and data fixtures for offline testing
of the ForexFactory scraper without network dependencies.
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent

# Path to sample calendar HTML
CALENDAR_SAMPLE_PATH = FIXTURES_DIR / "calendar_sample.html"


def load_calendar_sample() -> str:
    """Load the sample calendar HTML fixture.

    Returns:
        str: The HTML content of the sample calendar.
    """
    return CALENDAR_SAMPLE_PATH.read_text()


# Expected data from the sample HTML fixture
EXPECTED_EVENTS_COUNT = 13  # Total events in the sample

EXPECTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "NZD", "CNY"}

EXPECTED_IMPACTS = {"High", "Medium", "Low", "Holiday"}

# Sample event for validation
SAMPLE_NFP_EVENT = {
    "currency": "USD",
    "event_name": "Non-Farm Payrolls",
    "impact": "High",
    "actual": "200K",
    "forecast": "180K",
    "previous": "150K",
}
