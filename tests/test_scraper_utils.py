"""
Tests for scraper utility functions.

Tests timezone conversions, date/time parsing, and URL building
for Forex Factory scraper.
"""

from datetime import date, datetime, timezone

import pytest

# These imports should fail initially (RED phase)
from news_sentiment.scraper.constants import (
    BASE_URL,
    ET_TIMEZONE,
    SELECTOR_ACTUAL,
    SELECTOR_CURRENCY,
    SELECTOR_DATE,
    SELECTOR_EVENT,
    SELECTOR_FORECAST,
    SELECTOR_IMPACT,
    SELECTOR_PREVIOUS,
    SELECTOR_ROW,
    SELECTOR_TIME,
    UTC_TIMEZONE,
    WEEK_URL_PATTERN,
)
from news_sentiment.scraper.utils import (
    build_month_url,
    build_week_url,
    convert_et_to_utc,
    parse_ff_date,
    parse_ff_time,
)


class TestConstants:
    """Test constants module has expected values."""

    def test_base_url_value(self):
        """BASE_URL should point to Forex Factory calendar."""
        assert BASE_URL == "https://www.forexfactory.com/calendar"

    def test_week_url_pattern_contains_placeholders(self):
        """WEEK_URL_PATTERN should contain format placeholders."""
        assert "{base}" in WEEK_URL_PATTERN
        assert "{month}" in WEEK_URL_PATTERN
        assert "{day}" in WEEK_URL_PATTERN
        assert "{year}" in WEEK_URL_PATTERN

    def test_css_selectors_defined(self):
        """All CSS selectors should be defined."""
        assert SELECTOR_ROW == ".calendar__row"
        assert SELECTOR_DATE == ".calendar__date"
        assert SELECTOR_TIME == ".calendar__time"
        assert SELECTOR_CURRENCY == ".calendar__currency"
        assert SELECTOR_IMPACT == ".calendar__impact span"
        assert SELECTOR_EVENT == ".calendar__event"
        assert SELECTOR_ACTUAL == ".calendar__actual"
        assert SELECTOR_FORECAST == ".calendar__forecast"
        assert SELECTOR_PREVIOUS == ".calendar__previous"

    def test_timezone_constants(self):
        """Timezone constants should be valid timezone strings."""
        assert ET_TIMEZONE == "America/New_York"
        assert UTC_TIMEZONE == "UTC"


class TestParseFfTime:
    """Tests for parse_ff_time function."""

    def test_parse_normal_am_time(self):
        """Parse normal morning time like '8:30am'."""
        normalized, is_special = parse_ff_time("8:30am")
        assert normalized == "08:30"
        assert is_special is False

    def test_parse_normal_pm_time(self):
        """Parse normal afternoon time like '2:00pm'."""
        normalized, is_special = parse_ff_time("2:00pm")
        assert normalized == "14:00"
        assert is_special is False

    def test_parse_noon(self):
        """Parse noon time '12:00pm'."""
        normalized, is_special = parse_ff_time("12:00pm")
        assert normalized == "12:00"
        assert is_special is False

    def test_parse_midnight(self):
        """Parse midnight time '12:00am'."""
        normalized, is_special = parse_ff_time("12:00am")
        assert normalized == "00:00"
        assert is_special is False

    def test_parse_tentative(self):
        """Parse 'Tentative' as special value."""
        normalized, is_special = parse_ff_time("Tentative")
        assert normalized == "tentative"
        assert is_special is True

    def test_parse_all_day(self):
        """Parse 'All Day' as special value."""
        normalized, is_special = parse_ff_time("All Day")
        assert normalized == "all_day"
        assert is_special is True

    def test_parse_empty_string(self):
        """Parse empty string as special value."""
        normalized, is_special = parse_ff_time("")
        assert normalized == "unknown"
        assert is_special is True

    def test_parse_whitespace_handling(self):
        """Handle whitespace in time strings."""
        normalized, is_special = parse_ff_time("  8:30am  ")
        assert normalized == "08:30"
        assert is_special is False

    def test_parse_case_insensitive(self):
        """Handle different case variations."""
        normalized1, _ = parse_ff_time("8:30AM")
        normalized2, _ = parse_ff_time("8:30Am")
        assert normalized1 == "08:30"
        assert normalized2 == "08:30"

    def test_parse_single_digit_hour(self):
        """Parse single digit hour like '3:45pm'."""
        normalized, is_special = parse_ff_time("3:45pm")
        assert normalized == "15:45"
        assert is_special is False


class TestParseFfDate:
    """Tests for parse_ff_date function."""

    def test_parse_weekday_month_day_format(self):
        """Parse 'Mon Nov 25' format."""
        result = parse_ff_date("Mon Nov 25", year=2024)
        assert result == date(2024, 11, 25)

    def test_parse_month_day_format(self):
        """Parse 'Nov 25' format without weekday."""
        result = parse_ff_date("Nov 25", year=2024)
        assert result == date(2024, 11, 25)

    def test_parse_full_date_format(self):
        """Parse 'Nov 25, 2025' format with year included."""
        result = parse_ff_date("Nov 25, 2025")
        assert result == date(2025, 11, 25)

    def test_parse_default_year_current(self):
        """When no year provided and not in string, use current year."""
        current_year = datetime.now().year
        result = parse_ff_date("Nov 25")
        assert result.year == current_year
        assert result.month == 11
        assert result.day == 25

    def test_parse_all_months(self):
        """Parse dates from all months correctly."""
        test_cases = [
            ("Jan 15", 1, 15),
            ("Feb 28", 2, 28),
            ("Mar 10", 3, 10),
            ("Apr 1", 4, 1),
            ("May 31", 5, 31),
            ("Jun 15", 6, 15),
            ("Jul 4", 7, 4),
            ("Aug 20", 8, 20),
            ("Sep 5", 9, 5),
            ("Oct 31", 10, 31),
            ("Nov 11", 11, 11),
            ("Dec 25", 12, 25),
        ]
        for date_str, expected_month, expected_day in test_cases:
            result = parse_ff_date(date_str, year=2024)
            assert result.month == expected_month, f"Failed for {date_str}"
            assert result.day == expected_day, f"Failed for {date_str}"

    def test_parse_handles_whitespace(self):
        """Handle extra whitespace in date strings."""
        result = parse_ff_date("  Mon  Nov  25  ", year=2024)
        assert result == date(2024, 11, 25)

    def test_parse_invalid_date_raises_error(self):
        """Invalid date string should raise ValueError."""
        with pytest.raises(ValueError):
            parse_ff_date("Invalid Date", year=2024)


class TestConvertEtToUtc:
    """Tests for convert_et_to_utc function."""

    def test_convert_standard_time_est(self):
        """Convert ET to UTC during EST (winter).

        EST is UTC-5, so 8:30am EST = 13:30 UTC.
        Using January which is definitely EST.
        """
        result = convert_et_to_utc("Mon Jan 15", "8:30am", year=2024)
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 13  # 8:30 + 5 = 13:30
        assert result.minute == 30

    def test_convert_daylight_time_edt(self):
        """Convert ET to UTC during EDT (summer).

        EDT is UTC-4, so 8:30am EDT = 12:30 UTC.
        Using July which is definitely EDT.
        """
        result = convert_et_to_utc("Mon Jul 15", "8:30am", year=2024)
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 12  # 8:30 + 4 = 12:30
        assert result.minute == 30

    def test_convert_pm_time(self):
        """Convert afternoon time properly."""
        result = convert_et_to_utc("Mon Jan 15", "2:00pm", year=2024)
        assert result is not None
        assert result.hour == 19  # 14:00 + 5 = 19:00

    def test_convert_tentative_returns_none(self):
        """Tentative time should return None."""
        result = convert_et_to_utc("Mon Jan 15", "Tentative", year=2024)
        assert result is None

    def test_convert_all_day_returns_none(self):
        """All Day time should return None."""
        result = convert_et_to_utc("Mon Jan 15", "All Day", year=2024)
        assert result is None

    def test_convert_empty_time_returns_none(self):
        """Empty time string should return None."""
        result = convert_et_to_utc("Mon Jan 15", "", year=2024)
        assert result is None

    def test_convert_preserves_date(self):
        """Ensure date is preserved in conversion."""
        result = convert_et_to_utc("Mon Nov 25", "10:00am", year=2024)
        assert result is not None
        assert result.month == 11
        assert result.day == 25
        assert result.year == 2024

    def test_convert_day_rollover(self):
        """Handle day rollover when time pushes to next UTC day.

        11:00pm EST = 04:00 UTC next day.
        """
        result = convert_et_to_utc("Mon Jan 15", "11:00pm", year=2024)
        assert result is not None
        assert result.hour == 4  # 23:00 + 5 = 28:00 = 04:00 next day
        assert result.day == 16  # Next day

    def test_convert_year_rollover(self):
        """Handle year rollover (Dec 31 late night to Jan 1 UTC)."""
        result = convert_et_to_utc("Tue Dec 31", "11:00pm", year=2024)
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 4

    def test_convert_uses_default_year(self):
        """When no year provided, use current year."""
        current_year = datetime.now().year
        result = convert_et_to_utc("Mon Jan 15", "8:30am")
        assert result is not None
        assert result.year == current_year


class TestBuildWeekUrl:
    """Tests for build_week_url function."""

    def test_build_url_for_specific_date(self):
        """Build URL for a specific date."""
        test_date = datetime(2024, 11, 25)
        url = build_week_url(test_date)
        assert url == "https://www.forexfactory.com/calendar?week=nov25.2024"

    def test_build_url_lowercase_month(self):
        """Month abbreviation should be lowercase."""
        test_date = datetime(2024, 1, 15)
        url = build_week_url(test_date)
        assert "jan" in url.lower()
        assert "JAN" not in url

    def test_build_url_single_digit_day(self):
        """Handle single digit day properly."""
        test_date = datetime(2024, 3, 5)
        url = build_week_url(test_date)
        assert "mar5.2024" in url

    def test_build_url_double_digit_day(self):
        """Handle double digit day properly."""
        test_date = datetime(2024, 12, 25)
        url = build_week_url(test_date)
        assert "dec25.2024" in url

    def test_build_url_all_months(self):
        """Test URL generation for all months."""
        expected_months = [
            "jan", "feb", "mar", "apr", "may", "jun",
            "jul", "aug", "sep", "oct", "nov", "dec"
        ]
        for month_num, expected_abbrev in enumerate(expected_months, 1):
            test_date = datetime(2024, month_num, 15)
            url = build_week_url(test_date)
            assert expected_abbrev in url.lower(), f"Failed for month {month_num}"


class TestBuildMonthUrl:
    """Tests for build_month_url function."""

    def test_build_month_url_specific_month(self):
        """Build URL for a specific month."""
        url = build_month_url(2024, 11)
        assert url == "https://www.forexfactory.com/calendar?month=nov.2024"

    def test_build_month_url_all_months(self):
        """Test URL generation for all months."""
        expected = [
            (1, "jan"), (2, "feb"), (3, "mar"), (4, "apr"),
            (5, "may"), (6, "jun"), (7, "jul"), (8, "aug"),
            (9, "sep"), (10, "oct"), (11, "nov"), (12, "dec"),
        ]
        for month_num, abbrev in expected:
            url = build_month_url(2024, month_num)
            assert f"?month={abbrev}.2024" in url

    def test_build_month_url_lowercase(self):
        """Month abbreviation should be lowercase."""
        url = build_month_url(2024, 1)
        assert "jan" in url
        assert "Jan" not in url
        assert "JAN" not in url


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_dst_transition_spring_forward(self):
        """Handle DST transition in spring.

        On March 10, 2024, clocks spring forward at 2am.
        2:30am doesn't exist - it jumps from 1:59am to 3:00am.
        """
        # Before DST (1:30am EST = 6:30am UTC)
        result = convert_et_to_utc("Sun Mar 10", "1:30am", year=2024)
        assert result is not None
        assert result.hour == 6
        assert result.minute == 30

    def test_dst_transition_fall_back(self):
        """Handle DST transition in fall.

        On November 3, 2024, clocks fall back at 2am.
        1:30am occurs twice. Python's zoneinfo defaults to fold=0
        (the first occurrence, which is still DST/EDT).

        1:30am EDT = 5:30am UTC
        """
        result = convert_et_to_utc("Sun Nov 3", "1:30am", year=2024)
        assert result is not None
        # Default to first occurrence (EDT = UTC-4)
        assert result.hour == 5
        assert result.minute == 30

    def test_leap_year_february_29(self):
        """Handle February 29 in leap year."""
        result = parse_ff_date("Feb 29", year=2024)
        assert result == date(2024, 2, 29)

    def test_non_leap_year_february_29_raises(self):
        """February 29 in non-leap year should raise error."""
        with pytest.raises(ValueError):
            parse_ff_date("Feb 29", year=2023)

    def test_parse_time_invalid_format(self):
        """Invalid time format should return unknown."""
        normalized, is_special = parse_ff_time("invalid")
        assert normalized == "unknown"
        assert is_special is True

    def test_parse_time_numeric_only(self):
        """Numeric-only time without am/pm should return unknown."""
        normalized, is_special = parse_ff_time("830")
        assert normalized == "unknown"
        assert is_special is True
