"""
Utility functions for Forex Factory scraper.

Provides timezone conversion, date/time parsing, and URL building
functionality for scraping economic calendar data.
"""

import re
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from news_sentiment.scraper.constants import (
    BASE_URL,
    ET_TIMEZONE,
    MONTH_ABBREVS,
)


def parse_ff_time(time_str: str) -> tuple[str, bool]:
    """Parse Forex Factory time string, handling special values.

    Args:
        time_str: Time string like "8:30am", "Tentative", "All Day", etc.

    Returns:
        Tuple of (normalized_time, is_special):
        - For normal times: ("08:30", False)
        - For Tentative: ("tentative", True)
        - For All Day: ("all_day", True)
        - For empty/invalid: ("unknown", True)
    """
    time_str = time_str.strip().lower()

    # Handle special values
    if not time_str:
        return ("unknown", True)

    if time_str == "tentative":
        return ("tentative", True)

    if time_str == "all day":
        return ("all_day", True)

    # Parse normal time format: "8:30am" or "12:00pm"
    match = re.match(r"^(\d{1,2}):(\d{2})(am|pm)$", time_str)
    if not match:
        return ("unknown", True)

    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3)

    # Convert to 24-hour format
    if period == "am":
        if hour == 12:
            hour = 0  # 12:00am = 00:00
    else:  # pm
        if hour != 12:
            hour += 12  # 2:00pm = 14:00, but 12:00pm stays 12:00

    return (f"{hour:02d}:{minute:02d}", False)


def parse_ff_date(date_str: str, year: Optional[int] = None) -> date:
    """Parse Forex Factory date string to date object.

    Args:
        date_str: Date string like "Mon Nov 25", "Nov 25", or "Nov 25, 2025"
        year: Year to use if not included in date_str.
              Defaults to current year if None.

    Returns:
        date object

    Raises:
        ValueError: If date string cannot be parsed
    """
    date_str = " ".join(date_str.strip().split())  # Normalize whitespace

    # Try to extract year from date string (format: "Nov 25, 2025")
    year_match = re.search(r",\s*(\d{4})$", date_str)
    if year_match:
        year = int(year_match.group(1))
        date_str = date_str[: year_match.start()].strip()

    # Default to current year if not provided
    if year is None:
        year = datetime.now().year

    # Remove weekday prefix if present ("Mon Nov 25" -> "Nov 25")
    parts = date_str.split()
    if len(parts) == 3:
        # Assume first part is weekday abbreviation
        parts = parts[1:]
    elif len(parts) != 2:
        raise ValueError(f"Cannot parse date string: {date_str}")

    month_str, day_str = parts

    # Parse month abbreviation
    month_str_lower = month_str.lower()[:3]
    try:
        month = MONTH_ABBREVS.index(month_str_lower) + 1
    except ValueError:
        raise ValueError(f"Unknown month abbreviation: {month_str}")

    # Parse day
    try:
        day = int(day_str)
    except ValueError:
        raise ValueError(f"Invalid day value: {day_str}")

    # Create and return date (this will validate the date is valid)
    return date(year, month, day)


def convert_et_to_utc(
    date_str: str, time_str: str, year: Optional[int] = None
) -> Optional[datetime]:
    """Convert Forex Factory datetime (ET) to UTC.

    Forex Factory displays all times in Eastern Time (ET), which
    alternates between EST (UTC-5) and EDT (UTC-4) based on DST.

    Args:
        date_str: Date string like "Mon Nov 25" or "Nov 25"
        time_str: Time string like "8:30am", "Tentative", or "All Day"
        year: Year (defaults to current year)

    Returns:
        datetime in UTC timezone, or None for special time values
        (Tentative, All Day, empty, or invalid time)
    """
    # Parse the time first to check for special values
    normalized_time, is_special = parse_ff_time(time_str)
    if is_special:
        return None

    # Parse the date
    parsed_date = parse_ff_date(date_str, year)

    # Parse time components
    hour, minute = map(int, normalized_time.split(":"))

    # Create datetime in ET timezone
    et_tz = ZoneInfo(ET_TIMEZONE)
    et_datetime = datetime(
        parsed_date.year,
        parsed_date.month,
        parsed_date.day,
        hour,
        minute,
        tzinfo=et_tz,
    )

    # Convert to UTC
    utc_datetime = et_datetime.astimezone(timezone.utc)

    return utc_datetime


def build_week_url(target_date: datetime) -> str:
    """Build Forex Factory week URL for a given date.

    Args:
        target_date: The date within the week to fetch

    Returns:
        URL string like "https://www.forexfactory.com/calendar?week=nov25.2024"
    """
    month_abbrev = MONTH_ABBREVS[target_date.month - 1]
    day = target_date.day
    year = target_date.year

    return f"{BASE_URL}?week={month_abbrev}{day}.{year}"


def build_month_url(year: int, month: int) -> str:
    """Build Forex Factory month URL.

    Args:
        year: The year (e.g., 2024)
        month: The month number (1-12)

    Returns:
        URL string like "https://www.forexfactory.com/calendar?month=nov.2024"
    """
    month_abbrev = MONTH_ABBREVS[month - 1]
    return f"{BASE_URL}?month={month_abbrev}.{year}"
