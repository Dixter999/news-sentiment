"""
Tests for project structure and imports.

These tests verify that the project structure is correctly set up
and all required modules are importable.

TDD RED PHASE: These tests are written FIRST, before implementation.
"""


class TestPackageStructure:
    """Test that the package structure is correct."""

    def test_news_sentiment_package_exists(self) -> None:
        """The news_sentiment package should be importable."""
        import news_sentiment

        assert news_sentiment is not None

    def test_main_module_exists(self) -> None:
        """The main module should be importable."""
        from news_sentiment import main

        assert main is not None

    def test_scraper_package_exists(self) -> None:
        """The scraper package should be importable."""
        from news_sentiment import scraper

        assert scraper is not None

    def test_analyzer_package_exists(self) -> None:
        """The analyzer package should be importable."""
        from news_sentiment import analyzer

        assert analyzer is not None

    def test_database_package_exists(self) -> None:
        """The database package should be importable."""
        from news_sentiment import database

        assert database is not None


class TestScraperModule:
    """Test the scraper module structure."""

    def test_ff_scraper_module_exists(self) -> None:
        """The ForexFactory scraper module should be importable."""
        from news_sentiment.scraper import ff_scraper

        assert ff_scraper is not None

    def test_forex_factory_scraper_class_exists(self) -> None:
        """The ForexFactoryScraper class should be defined."""
        from news_sentiment.scraper.ff_scraper import ForexFactoryScraper

        assert ForexFactoryScraper is not None

    def test_forex_factory_scraper_has_scrape_week_method(self) -> None:
        """ForexFactoryScraper should have a scrape_week method."""
        from news_sentiment.scraper.ff_scraper import ForexFactoryScraper

        assert hasattr(ForexFactoryScraper, "scrape_week")


class TestAnalyzerModule:
    """Test the analyzer module structure."""

    def test_gemini_module_exists(self) -> None:
        """The Gemini analyzer module should be importable."""
        from news_sentiment.analyzer import gemini

        assert gemini is not None

    def test_sentiment_analyzer_class_exists(self) -> None:
        """The SentimentAnalyzer class should be defined."""
        from news_sentiment.analyzer.gemini import SentimentAnalyzer

        assert SentimentAnalyzer is not None

    def test_sentiment_analyzer_has_analyze_method(self) -> None:
        """SentimentAnalyzer should have an analyze method."""
        from news_sentiment.analyzer.gemini import SentimentAnalyzer

        assert hasattr(SentimentAnalyzer, "analyze")


class TestDatabaseModule:
    """Test the database module structure."""

    def test_models_module_exists(self) -> None:
        """The models module should be importable."""
        from news_sentiment.database import models

        assert models is not None

    def test_economic_event_model_exists(self) -> None:
        """The EconomicEvent model should be defined."""
        from news_sentiment.database.models import EconomicEvent

        assert EconomicEvent is not None

    def test_connection_module_exists(self) -> None:
        """The connection module should be importable."""
        from news_sentiment.database import connection

        assert connection is not None

    def test_get_session_function_exists(self) -> None:
        """The get_session function should be defined."""
        from news_sentiment.database.connection import get_session

        assert get_session is not None

    def test_config_module_exists(self) -> None:
        """The config module should be importable."""
        from news_sentiment.database import config

        assert config is not None


class TestMainModule:
    """Test the main module structure."""

    def test_main_has_run_function(self) -> None:
        """Main module should have a run function."""
        from news_sentiment.main import run

        assert run is not None
        assert callable(run)

    def test_main_has_scrape_events_function(self) -> None:
        """Main module should have a scrape_events function."""
        from news_sentiment.main import scrape_events

        assert scrape_events is not None
        assert callable(scrape_events)

    def test_main_has_store_events_function(self) -> None:
        """Main module should have a store_events function."""
        from news_sentiment.main import store_events

        assert store_events is not None
        assert callable(store_events)

    def test_main_has_analyze_events_function(self) -> None:
        """Main module should have an analyze_events function."""
        from news_sentiment.main import analyze_events

        assert analyze_events is not None
        assert callable(analyze_events)
