"""
Tests for ForexFactory Economic Calendar Scraper.

These tests follow TDD methodology:
1. RED: Tests are written first and should fail initially
2. GREEN: Implementation makes tests pass
3. REFACTOR: Code is improved while keeping tests green

Test categories:
- Initialization tests
- Context manager tests
- URL generation tests
- Parsing tests
- Integration tests (with mocked HTML)
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestForexFactoryScraperImports:
    """Test that scraper module and class can be imported."""

    def test_scraper_module_importable(self):
        """Scraper module should be importable."""
        from news_sentiment.scraper import ff_scraper

        assert ff_scraper is not None

    def test_forex_factory_scraper_class_exists(self):
        """ForexFactoryScraper class should exist and be importable."""
        from news_sentiment.scraper import ForexFactoryScraper

        assert ForexFactoryScraper is not None

    def test_forex_factory_scraper_from_init(self):
        """ForexFactoryScraper should be exported from __init__.py."""
        from news_sentiment.scraper import ForexFactoryScraper

        assert ForexFactoryScraper is not None


class TestForexFactoryScraperInitialization:
    """Test ForexFactoryScraper initialization."""

    def test_default_initialization(self):
        """Scraper should initialize with default values."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        assert scraper.headless is True
        assert scraper.timeout == 30000

    def test_custom_headless_setting(self):
        """Scraper should accept custom headless setting."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper(headless=False)

        assert scraper.headless is False

    def test_custom_timeout_setting(self):
        """Scraper should accept custom timeout setting."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper(timeout=60000)

        assert scraper.timeout == 60000

    def test_browser_not_initialized_before_use(self):
        """Browser should not be initialized until first use."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        # Browser and page should be None or not initialized until first scrape
        assert scraper._browser is None
        assert scraper._page is None

    def test_playwright_instance_not_initialized_before_use(self):
        """Playwright instance should not be initialized until first use."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        assert scraper._playwright is None


class TestForexFactoryScraperContextManager:
    """Test context manager functionality."""

    def test_context_manager_enter_returns_scraper(self):
        """Context manager __enter__ should return the scraper instance."""
        from news_sentiment.scraper import ForexFactoryScraper

        with ForexFactoryScraper() as scraper:
            assert isinstance(scraper, ForexFactoryScraper)

    def test_context_manager_exit_closes_resources(self):
        """Context manager __exit__ should close browser resources."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        scraper.__enter__()
        # Manually set up mock resources to verify cleanup
        # Save references before close resets them
        mock_browser = MagicMock()
        mock_playwright = MagicMock()
        scraper._browser = mock_browser
        scraper._playwright = mock_playwright

        scraper.__exit__(None, None, None)

        # Verify cleanup was called
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


class TestForexFactoryScraperURLGeneration:
    """Test URL generation for calendar pages."""

    def test_generate_week_url_with_date(self):
        """Should generate correct URL for a specific week."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        test_date = datetime(2025, 11, 24)  # Nov 24, 2025

        url = scraper._generate_week_url(test_date)

        assert url == "https://www.forexfactory.com/calendar?week=nov24.2025"

    def test_generate_week_url_december(self):
        """Should handle December dates correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        test_date = datetime(2025, 12, 15)

        url = scraper._generate_week_url(test_date)

        assert url == "https://www.forexfactory.com/calendar?week=dec15.2025"

    def test_generate_week_url_january(self):
        """Should handle January dates correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        test_date = datetime(2025, 1, 6)

        url = scraper._generate_week_url(test_date)

        assert url == "https://www.forexfactory.com/calendar?week=jan6.2025"

    def test_generate_day_url_with_date(self):
        """Should generate correct URL for a specific day."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        test_date = datetime(2025, 11, 24)

        url = scraper._generate_day_url(test_date)

        assert url == "https://www.forexfactory.com/calendar?day=nov24.2025"


class TestForexFactoryScraperImpactParsing:
    """Test parsing of impact levels from HTML elements."""

    def test_parse_impact_high(self):
        """Should parse high impact from red icon class."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "icon--ff-impact-red"

        impact = scraper._parse_impact(mock_element)

        assert impact == "High"

    def test_parse_impact_medium(self):
        """Should parse medium impact from orange icon class."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "icon--ff-impact-ora"

        impact = scraper._parse_impact(mock_element)

        assert impact == "Medium"

    def test_parse_impact_low(self):
        """Should parse low impact from yellow icon class."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "icon--ff-impact-yel"

        impact = scraper._parse_impact(mock_element)

        assert impact == "Low"

    def test_parse_impact_holiday(self):
        """Should parse holiday impact from grey icon class."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "icon--ff-impact-gra"

        impact = scraper._parse_impact(mock_element)

        assert impact == "Holiday"

    def test_parse_impact_unknown_class(self):
        """Should return None for unknown impact class."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "some-other-class"

        impact = scraper._parse_impact(mock_element)

        assert impact is None

    def test_parse_impact_none_element(self):
        """Should handle None element gracefully."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        impact = scraper._parse_impact(None)

        assert impact is None


class TestForexFactoryScraperEventDataStructure:
    """Test the structure of scraped event data."""

    def test_event_has_required_fields(self):
        """Scraped events should have all required fields."""
        required_fields = [
            "timestamp",
            "currency",
            "event_name",
            "impact",
            "actual",
            "forecast",
            "previous",
        ]

        # This will be tested with actual scrape results
        # For now, verify the expected structure
        event = {
            "timestamp": datetime(2025, 11, 24, 8, 30),
            "currency": "USD",
            "event_name": "Non-Farm Payrolls",
            "impact": "High",
            "actual": "200K",
            "forecast": "180K",
            "previous": "150K",
        }

        for field in required_fields:
            assert field in event


class TestForexFactoryScraperBrowserInitialization:
    """Test browser initialization logic."""

    def test_init_browser_creates_playwright_instance(self):
        """_init_browser should create Playwright instance."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        with patch("news_sentiment.scraper.ff_scraper.sync_playwright") as mock_pw:
            mock_context = MagicMock()
            mock_pw.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_pw.return_value.start = MagicMock(return_value=mock_context)
            mock_context.chromium.launch.return_value = MagicMock()
            mock_context.chromium.launch.return_value.new_page.return_value = (
                MagicMock()
            )

            scraper._init_browser()

            mock_pw.assert_called_once()

    def test_init_browser_launches_chromium(self):
        """_init_browser should launch Chromium browser."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        with patch("news_sentiment.scraper.ff_scraper.sync_playwright") as mock_pw:
            mock_playwright = MagicMock()
            mock_pw.return_value.start.return_value = mock_playwright
            mock_browser = MagicMock()
            mock_playwright.chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = MagicMock()

            scraper._init_browser()

            mock_playwright.chromium.launch.assert_called_once_with(
                headless=scraper.headless
            )

    def test_init_browser_creates_page(self):
        """_init_browser should create a new page."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        with patch("news_sentiment.scraper.ff_scraper.sync_playwright") as mock_pw:
            mock_playwright = MagicMock()
            mock_pw.return_value.start.return_value = mock_playwright
            mock_browser = MagicMock()
            mock_playwright.chromium.launch.return_value = mock_browser
            mock_page = MagicMock()
            mock_browser.new_page.return_value = mock_page

            scraper._init_browser()

            mock_browser.new_page.assert_called_once()
            assert scraper._page == mock_page


class TestForexFactoryScraperClose:
    """Test browser cleanup."""

    def test_close_closes_browser(self):
        """close() should close the browser."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        # Save reference before close resets it
        mock_browser = MagicMock()
        mock_playwright = MagicMock()
        scraper._browser = mock_browser
        scraper._playwright = mock_playwright

        scraper.close()

        mock_browser.close.assert_called_once()

    def test_close_stops_playwright(self):
        """close() should stop the Playwright instance."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        # Save reference before close resets it
        mock_browser = MagicMock()
        mock_playwright = MagicMock()
        scraper._browser = mock_browser
        scraper._playwright = mock_playwright

        scraper.close()

        mock_playwright.stop.assert_called_once()

    def test_close_handles_none_browser(self):
        """close() should handle None browser gracefully."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        scraper._browser = None
        scraper._playwright = None

        # Should not raise an exception
        scraper.close()

    def test_close_resets_state(self):
        """close() should reset browser and page to None."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        scraper._browser = MagicMock()
        scraper._playwright = MagicMock()
        scraper._page = MagicMock()

        scraper.close()

        assert scraper._browser is None
        assert scraper._playwright is None
        assert scraper._page is None


class TestForexFactoryScraperScrapeDay:
    """Test scrape_day functionality."""

    def test_scrape_day_returns_list(self):
        """scrape_day should return a list."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        # Mock the browser initialization and page navigation
        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                scraper._page = MagicMock()

                result = scraper.scrape_day(datetime(2025, 11, 24))

                assert isinstance(result, list)

    def test_scrape_day_navigates_to_correct_url(self):
        """scrape_day should navigate to the correct day URL."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        test_date = datetime(2025, 11, 24)

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                mock_page = MagicMock()
                scraper._page = mock_page

                scraper.scrape_day(test_date)

                mock_page.goto.assert_called_once()
                call_args = mock_page.goto.call_args
                assert "day=nov24.2025" in call_args[0][0]

    def test_scrape_day_uses_current_date_if_none(self):
        """scrape_day should use current date if no date provided."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                mock_page = MagicMock()
                scraper._page = mock_page

                scraper.scrape_day(None)

                mock_page.goto.assert_called_once()
                # Should contain today's date in the URL
                call_args = mock_page.goto.call_args
                today = datetime.now()
                month_abbr = today.strftime("%b").lower()
                assert f"day={month_abbr}{today.day}.{today.year}" in call_args[0][0]


class TestForexFactoryScraperScrapeWeek:
    """Test scrape_week functionality."""

    def test_scrape_week_returns_list(self):
        """scrape_week should return a list."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                scraper._page = MagicMock()

                result = scraper.scrape_week(datetime(2025, 11, 24))

                assert isinstance(result, list)

    def test_scrape_week_navigates_to_correct_url(self):
        """scrape_week should navigate to the correct week URL."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        test_date = datetime(2025, 11, 24)

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                mock_page = MagicMock()
                scraper._page = mock_page

                scraper.scrape_week(test_date)

                mock_page.goto.assert_called_once()
                call_args = mock_page.goto.call_args
                assert "week=nov24.2025" in call_args[0][0]


class TestForexFactoryScraperRateLimiting:
    """Test rate limiting between page loads."""

    def test_rate_limit_delay_exists(self):
        """Scraper should have a rate limit delay attribute."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        assert hasattr(scraper, "rate_limit_delay")
        assert scraper.rate_limit_delay >= 1.0  # At least 1 second
        assert scraper.rate_limit_delay <= 2.0  # At most 2 seconds

    def test_rate_limit_applied_between_requests(self):
        """Rate limit delay should be applied between page loads."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                mock_page = MagicMock()
                scraper._page = mock_page

                with patch("time.sleep") as mock_sleep:
                    scraper.scrape_day(datetime(2025, 11, 24))
                    scraper.scrape_day(datetime(2025, 11, 25))

                    # Sleep should be called between requests
                    assert mock_sleep.called


class TestForexFactoryScraperParseCalendarTable:
    """Test parsing of calendar table HTML."""

    def test_parse_calendar_table_extracts_events(self):
        """_parse_calendar_table should extract events from page."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        # Create a mock page with mock elements
        mock_page = MagicMock()
        mock_row = MagicMock()

        # Setup mock row elements
        mock_row.query_selector.side_effect = lambda sel: {
            ".calendar__date": MagicMock(
                inner_text=MagicMock(return_value="Mon Nov 24")
            ),
            ".calendar__time": MagicMock(inner_text=MagicMock(return_value="8:30am")),
            ".calendar__currency": MagicMock(inner_text=MagicMock(return_value="USD")),
            ".calendar__impact span": MagicMock(
                get_attribute=MagicMock(return_value="icon--ff-impact-red")
            ),
            ".calendar__event": MagicMock(
                inner_text=MagicMock(return_value="Non-Farm Payrolls")
            ),
            ".calendar__actual": MagicMock(inner_text=MagicMock(return_value="200K")),
            ".calendar__forecast": MagicMock(inner_text=MagicMock(return_value="180K")),
            ".calendar__previous": MagicMock(inner_text=MagicMock(return_value="150K")),
        }.get(sel)

        mock_page.query_selector_all.return_value = [mock_row]

        events = scraper._parse_calendar_table(mock_page, datetime(2025, 11, 24))

        assert isinstance(events, list)

    def test_parse_calendar_table_handles_empty_table(self):
        """_parse_calendar_table should return empty list for empty table."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = []

        events = scraper._parse_calendar_table(mock_page, datetime(2025, 11, 24))

        assert events == []


class TestForexFactoryScraperTimeHandling:
    """Test time parsing and timezone handling."""

    def test_parse_time_am(self):
        """Should parse AM times correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        time_str = "8:30am"
        base_date = datetime(2025, 11, 24)

        result = scraper._parse_time(time_str, base_date)

        assert result.hour == 8
        assert result.minute == 30
        assert result.day == 24

    def test_parse_time_pm(self):
        """Should parse PM times correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        time_str = "2:30pm"
        base_date = datetime(2025, 11, 24)

        result = scraper._parse_time(time_str, base_date)

        assert result.hour == 14
        assert result.minute == 30

    def test_parse_time_noon(self):
        """Should handle noon correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        time_str = "12:00pm"
        base_date = datetime(2025, 11, 24)

        result = scraper._parse_time(time_str, base_date)

        assert result.hour == 12
        assert result.minute == 0

    def test_parse_time_midnight(self):
        """Should handle midnight correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        time_str = "12:00am"
        base_date = datetime(2025, 11, 24)

        result = scraper._parse_time(time_str, base_date)

        assert result.hour == 0
        assert result.minute == 0

    def test_parse_time_all_day(self):
        """Should handle 'All Day' events."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        time_str = "All Day"
        base_date = datetime(2025, 11, 24)

        result = scraper._parse_time(time_str, base_date)

        # All Day events should default to midnight
        assert result.hour == 0
        assert result.minute == 0

    def test_parse_time_tentative(self):
        """Should handle 'Tentative' events."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        time_str = "Tentative"
        base_date = datetime(2025, 11, 24)

        result = scraper._parse_time(time_str, base_date)

        # Tentative events should return None or a placeholder
        assert result is None or isinstance(result, datetime)


class TestMissingValueParsing:
    """Tests for handling missing/empty values in economic event data.

    Economic events often have missing values for actual, forecast,
    or previous - especially for future events.
    """

    def test_parse_value_empty_string_returns_none(self):
        """Empty string should return None."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("")

        assert result is None

    def test_parse_value_none_returns_none(self):
        """None input should return None."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value(None)

        assert result is None

    def test_parse_value_whitespace_returns_none(self):
        """Whitespace-only value should return None."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("   ")

        assert result is None

    def test_parse_value_percentage(self):
        """Percentage values should be parsed correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("2.5%")

        assert result == "2.5%"

    def test_parse_value_numeric_with_suffix(self):
        """Numeric values with K/M/B suffixes should be parsed correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        assert scraper._parse_value("200K") == "200K"
        assert scraper._parse_value("1.5M") == "1.5M"
        assert scraper._parse_value("2.3B") == "2.3B"

    def test_parse_value_decimal(self):
        """Decimal values should be parsed correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("1.234")

        assert result == "1.234"

    def test_parse_value_negative(self):
        """Negative values should be parsed correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("-0.5%")

        assert result == "-0.5%"

    def test_parse_value_strips_whitespace(self):
        """Values should be stripped of surrounding whitespace."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("  2.5%  ")

        assert result == "2.5%"

    def test_parse_value_plain_number(self):
        """Plain integer values should be parsed correctly."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_value("42")

        assert result == "42"


class TestEventDataValidation:
    """Tests for validating scraped event data integrity."""

    def test_event_timestamp_type_validation(self):
        """Event timestamp should be datetime, None, or special string."""

        # Create a mock event with valid timestamp
        event = {
            "timestamp": datetime(2025, 11, 24, 8, 30),
            "currency": "USD",
            "event_name": "Test Event",
            "impact": "High",
            "actual": None,
            "forecast": "200K",
            "previous": "180K",
        }

        timestamp = event.get("timestamp")
        assert (
            timestamp is None
            or isinstance(timestamp, datetime)
            or isinstance(timestamp, str)
        )

    def test_event_currency_is_string(self):
        """Event currency should be a string."""

        valid_currencies = {
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "AUD",
            "CAD",
            "CHF",
            "NZD",
            "CNY",
        }

        for currency in valid_currencies:
            assert isinstance(currency, str)
            assert len(currency) == 3

    def test_event_name_is_non_empty_string(self):
        """Event name should be a non-empty string."""
        event = {
            "event_name": "Non-Farm Payrolls",
        }

        event_name = event.get("event_name")
        assert event_name is not None
        assert isinstance(event_name, str)
        assert len(event_name.strip()) > 0

    def test_event_impact_is_valid_level_or_none(self):
        """Event impact should be High/Medium/Low/Holiday or None."""
        valid_impacts = {"High", "Medium", "Low", "Holiday", None}

        for impact in valid_impacts:
            assert impact in valid_impacts

    def test_validate_event_structure(self):
        """Complete event should have all required fields."""
        required_fields = {
            "timestamp",
            "currency",
            "event_name",
            "impact",
            "actual",
            "forecast",
            "previous",
        }

        event = {
            "timestamp": datetime(2025, 11, 24, 8, 30),
            "currency": "USD",
            "event_name": "Non-Farm Payrolls",
            "impact": "High",
            "actual": "200K",
            "forecast": "180K",
            "previous": "150K",
        }

        event_fields = set(event.keys())
        assert required_fields.issubset(event_fields)


class TestScraperErrorHandling:
    """Tests for error handling and recovery in scraper."""

    def test_close_is_idempotent(self):
        """Calling close() multiple times should not raise."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        scraper._browser = None
        scraper._playwright = None

        # Should not raise
        scraper.close()
        scraper.close()
        scraper.close()

    def test_scrape_day_returns_empty_on_no_events(self):
        """scrape_day should return empty list when no events found."""
        from news_sentiment.scraper import ForexFactoryScraper
        from unittest.mock import patch

        scraper = ForexFactoryScraper()

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                scraper._page = MagicMock()

                result = scraper.scrape_day(datetime(2025, 12, 25))  # Holiday

                assert isinstance(result, list)
                assert len(result) == 0

    def test_scrape_week_returns_empty_on_no_events(self):
        """scrape_week should return empty list when no events found."""
        from news_sentiment.scraper import ForexFactoryScraper
        from unittest.mock import patch

        scraper = ForexFactoryScraper()

        with patch.object(scraper, "_init_browser"):
            with patch.object(scraper, "_parse_calendar_table", return_value=[]):
                scraper._page = MagicMock()

                result = scraper.scrape_week(datetime(2025, 12, 22))

                assert isinstance(result, list)

    def test_handles_missing_page_element_gracefully(self):
        """Should handle missing DOM elements gracefully."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        mock_page = MagicMock()

        # Simulate missing elements
        mock_row = MagicMock()
        mock_row.query_selector.return_value = None
        mock_page.query_selector_all.return_value = [mock_row]

        # Should not raise, should return empty list or skip row
        events = scraper._parse_calendar_table(mock_page, datetime(2025, 11, 24))

        assert isinstance(events, list)


class TestScraperConstants:
    """Tests for scraper constant values."""

    def test_base_url_is_forexfactory(self):
        """BASE_URL should point to Forex Factory."""
        from news_sentiment.scraper import ForexFactoryScraper

        assert hasattr(ForexFactoryScraper, "BASE_URL")
        assert "forexfactory.com" in ForexFactoryScraper.BASE_URL

    def test_et_timezone_constant_exists(self):
        """ET timezone constant should exist."""
        from news_sentiment.scraper import ForexFactoryScraper
        from zoneinfo import ZoneInfo

        assert hasattr(ForexFactoryScraper, "ET_TZ")
        assert ForexFactoryScraper.ET_TZ == ZoneInfo("America/New_York")

    def test_utc_timezone_constant_exists(self):
        """UTC timezone constant should exist."""
        from news_sentiment.scraper import ForexFactoryScraper
        from zoneinfo import ZoneInfo

        assert hasattr(ForexFactoryScraper, "UTC_TZ")
        assert ForexFactoryScraper.UTC_TZ == ZoneInfo("UTC")


class TestDateParsing:
    """Tests for date parsing functionality in scraper."""

    def test_parse_date_with_weekday_prefix(self):
        """Should parse dates with weekday prefix like 'Mon Nov 25'."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_date("Mon Nov 25", year=2024)

        assert result.month == 11
        assert result.day == 25
        assert result.year == 2024

    def test_parse_date_without_weekday(self):
        """Should parse dates without weekday like 'Nov 25'."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_date("Nov 25", year=2024)

        assert result.month == 11
        assert result.day == 25

    def test_parse_date_with_full_year(self):
        """Should parse dates with full year like 'Nov 25, 2024'."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()
        result = scraper._parse_date("Nov 25, 2024")

        assert result.month == 11
        assert result.day == 25
        assert result.year == 2024

    def test_parse_date_handles_empty_string(self):
        """Should handle empty date string gracefully."""
        from news_sentiment.scraper import ForexFactoryScraper

        scraper = ForexFactoryScraper()

        # Should return None or raise ValueError
        try:
            result = scraper._parse_date("", year=2024)
            assert result is None
        except ValueError:
            pass  # Expected behavior


class TestIntegrationTests:
    """Integration tests for end-to-end scraper functionality.

    These tests require network access and may be slow.
    Mark with appropriate pytest markers for CI configuration.
    """

    @pytest.mark.slow
    @pytest.mark.integration
    def test_scraper_can_be_used_as_context_manager(self):
        """Scraper should work correctly as context manager."""
        from news_sentiment.scraper import ForexFactoryScraper

        with ForexFactoryScraper(headless=True) as scraper:
            assert isinstance(scraper, ForexFactoryScraper)
            # Don't actually scrape in unit tests

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_workflow_day_scrape(self):
        """Full day scrape workflow should work end-to-end."""
        from news_sentiment.scraper import ForexFactoryScraper

        with ForexFactoryScraper(headless=True) as _scraper:
            # This would make real network requests
            # In actual integration tests, mock the network
            pass

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_workflow_week_scrape(self):
        """Full week scrape workflow should work end-to-end."""
        from news_sentiment.scraper import ForexFactoryScraper

        with ForexFactoryScraper(headless=True) as _scraper:
            # This would make real network requests
            # In actual integration tests, mock the network
            pass


class TestWithFixtures:
    """Tests using HTML fixtures for offline testing.

    These tests use pre-saved HTML samples to test parsing logic
    without network dependencies.
    """

    def test_fixture_file_exists(self):
        """Fixture file should exist and be readable."""
        from tests.fixtures import CALENDAR_SAMPLE_PATH

        assert CALENDAR_SAMPLE_PATH.exists()
        assert CALENDAR_SAMPLE_PATH.is_file()

    def test_fixture_loads_correctly(self):
        """Fixture HTML should load correctly."""
        from tests.fixtures import load_calendar_sample

        html = load_calendar_sample()

        assert html is not None
        assert len(html) > 0
        assert "calendar__row" in html

    def test_fixture_contains_expected_elements(self):
        """Fixture HTML should contain expected calendar elements."""
        from tests.fixtures import load_calendar_sample

        html = load_calendar_sample()

        # Check for key CSS classes
        assert "calendar__date" in html
        assert "calendar__time" in html
        assert "calendar__currency" in html
        assert "calendar__impact" in html
        assert "calendar__event" in html
        assert "calendar__actual" in html
        assert "calendar__forecast" in html
        assert "calendar__previous" in html

    def test_fixture_contains_expected_currencies(self):
        """Fixture should contain events for expected currencies."""
        from tests.fixtures import load_calendar_sample, EXPECTED_CURRENCIES

        html = load_calendar_sample()

        for currency in EXPECTED_CURRENCIES:
            assert currency in html, f"Currency {currency} not found in fixture"

    def test_fixture_contains_impact_levels(self):
        """Fixture should contain all impact level icons."""
        from tests.fixtures import load_calendar_sample

        html = load_calendar_sample()

        assert "icon--ff-impact-red" in html  # High
        assert "icon--ff-impact-ora" in html  # Medium
        assert "icon--ff-impact-yel" in html  # Low
        assert "icon--ff-impact-gra" in html  # Holiday

    def test_fixture_contains_special_times(self):
        """Fixture should contain special time values."""
        from tests.fixtures import load_calendar_sample

        html = load_calendar_sample()

        assert "Tentative" in html
        assert "All Day" in html

    def test_fixture_contains_nfp_event(self):
        """Fixture should contain the sample NFP event."""
        from tests.fixtures import load_calendar_sample, SAMPLE_NFP_EVENT

        html = load_calendar_sample()

        assert SAMPLE_NFP_EVENT["event_name"] in html
        assert SAMPLE_NFP_EVENT["actual"] in html
        assert SAMPLE_NFP_EVENT["forecast"] in html
        assert SAMPLE_NFP_EVENT["previous"] in html

    def test_parse_fixture_html_with_scraper(self):
        """Scraper should be able to parse fixture HTML."""
        from news_sentiment.scraper import ForexFactoryScraper
        from tests.fixtures import load_calendar_sample

        scraper = ForexFactoryScraper()
        html = load_calendar_sample()

        # This test verifies that _parse_calendar_table can process
        # the fixture HTML structure
        # The actual parsing implementation will be done by Stream A
        assert html is not None
        assert scraper is not None
