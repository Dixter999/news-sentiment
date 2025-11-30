"""
Scraper module for fetching economic calendar data.

This module provides web scraping functionality for extracting
economic events from financial news websites.
"""

from news_sentiment.scraper.constants import (
    BASE_URL,
    ET_TIMEZONE,
    MONTH_ABBREVS,
    MONTH_URL_PATTERN,
    SELECTOR_ACTUAL,
    SELECTOR_CURRENCY,
    SELECTOR_DATE,
    SELECTOR_EVENT,
    SELECTOR_FORECAST,
    SELECTOR_IMPACT,
    SELECTOR_PREVIOUS,
    SELECTOR_ROW,
    SELECTOR_TIME,
    SPECIAL_TIME_VALUES,
    UTC_TIMEZONE,
    WEEK_URL_PATTERN,
)
from news_sentiment.scraper.ff_scraper import ForexFactoryScraper
from news_sentiment.scraper.utils import (
    build_month_url,
    build_week_url,
    convert_et_to_utc,
    parse_ff_date,
    parse_ff_time,
)

__all__ = [
    # Main scraper class
    "ForexFactoryScraper",
    # Utility functions
    "build_month_url",
    "build_week_url",
    "convert_et_to_utc",
    "parse_ff_date",
    "parse_ff_time",
    # Constants
    "BASE_URL",
    "ET_TIMEZONE",
    "MONTH_ABBREVS",
    "MONTH_URL_PATTERN",
    "SELECTOR_ACTUAL",
    "SELECTOR_CURRENCY",
    "SELECTOR_DATE",
    "SELECTOR_EVENT",
    "SELECTOR_FORECAST",
    "SELECTOR_IMPACT",
    "SELECTOR_PREVIOUS",
    "SELECTOR_ROW",
    "SELECTOR_TIME",
    "SPECIAL_TIME_VALUES",
    "UTC_TIMEZONE",
    "WEEK_URL_PATTERN",
]
