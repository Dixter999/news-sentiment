"""
News Sentiment Service.

A service for scraping economic calendar events from ForexFactory
and analyzing their sentiment using Google Gemini API.
"""

from news_sentiment import main
from news_sentiment import scraper
from news_sentiment import analyzer
from news_sentiment import database

__version__ = "0.1.0"

__all__ = [
    "main",
    "scraper",
    "analyzer",
    "database",
    "__version__",
]
