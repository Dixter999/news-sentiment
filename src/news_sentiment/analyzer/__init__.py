"""
Analyzer module for sentiment analysis using AI models.

This module provides sentiment analysis functionality using
Google Gemini API to analyze economic events.

Submodules:
    - prompts: Prompt templates and formatting utilities
    - parsers: Response parsing utilities for Gemini API
    - gemini: Main SentimentAnalyzer class
"""

from news_sentiment.analyzer.gemini import SentimentAnalyzer
from news_sentiment.analyzer import parsers, prompts

__all__ = [
    "SentimentAnalyzer",
    "parsers",
    "prompts",
]
