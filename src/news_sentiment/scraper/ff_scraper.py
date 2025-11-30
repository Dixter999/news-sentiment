"""
ForexFactory Economic Calendar Scraper.

This module provides functionality to scrape economic calendar events
from ForexFactory.com using Playwright for browser automation.
"""

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from playwright.sync_api import Page, sync_playwright
from playwright_stealth import Stealth


class ForexFactoryScraper:
    """Scraper for ForexFactory economic calendar.

    Uses Playwright for browser automation to scrape economic events
    including event name, time, currency, impact level, and actual/forecast values.

    Attributes:
        headless: Whether to run browser in headless mode
        timeout: Page load timeout in milliseconds
        rate_limit_delay: Delay between requests in seconds
    """

    # Base URL for Forex Factory calendar
    BASE_URL = "https://www.forexfactory.com/calendar"

    # Timezone constants (Forex Factory uses Eastern Time)
    ET_TZ = ZoneInfo("America/New_York")
    UTC_TZ = ZoneInfo("UTC")

    # Impact level mappings from CSS classes to human-readable names
    IMPACT_MAP = {
        "icon--ff-impact-red": "High",
        "icon--ff-impact-ora": "Medium",
        "icon--ff-impact-yel": "Low",
        "icon--ff-impact-gra": "Holiday",
    }

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        rate_limit_delay: float = 1.5,
    ) -> None:
        """Initialize the scraper.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Page load timeout in milliseconds (default: 30000)
            rate_limit_delay: Delay between requests in seconds (default: 1.5)
        """
        self.headless = headless
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay

        # Browser state - initialized lazily on first use
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._page: Optional[Page] = None

        # Track request timing for rate limiting
        self._last_request_time: Optional[float] = None

    def _init_browser(self) -> None:
        """Initialize Playwright browser if not already initialized.

        Creates a Chromium browser instance and a new page with stealth mode
        to bypass Cloudflare and other bot detection.
        """
        if self._browser is not None:
            return

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        # Create context with realistic browser settings
        context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )
        self._page = context.new_page()
        self._page.set_default_timeout(self.timeout)

        # Apply stealth mode to bypass Cloudflare bot detection
        stealth = Stealth()
        stealth.apply_stealth_sync(self._page)

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests.

        Ensures at least rate_limit_delay seconds between page loads.
        """
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)

    def _generate_week_url(self, date: datetime) -> str:
        """Generate the URL for a week's calendar.

        Args:
            date: The start date of the week

        Returns:
            URL string in format: https://www.forexfactory.com/calendar?week=nov24.2025
        """
        month_abbr = date.strftime("%b").lower()
        return f"{self.BASE_URL}?week={month_abbr}{date.day}.{date.year}"

    def _generate_day_url(self, date: datetime) -> str:
        """Generate the URL for a day's calendar.

        Args:
            date: The date to generate URL for

        Returns:
            URL string in format: https://www.forexfactory.com/calendar?day=nov24.2025
        """
        month_abbr = date.strftime("%b").lower()
        return f"{self.BASE_URL}?day={month_abbr}{date.day}.{date.year}"

    def _parse_impact(self, element: Optional[Any]) -> Optional[str]:
        """Parse impact level from an icon element.

        Args:
            element: Playwright element containing the impact icon

        Returns:
            Impact level string ("High", "Medium", "Low", "Holiday") or None
        """
        if element is None:
            return None

        try:
            class_attr = element.get_attribute("class")
            if class_attr is None:
                return None

            for class_name, impact in self.IMPACT_MAP.items():
                if class_name in class_attr:
                    return impact

            return None
        except Exception:
            return None

    def _parse_time(self, time_str: str, base_date: datetime) -> Optional[datetime]:
        """Parse time string and combine with base date.

        Args:
            time_str: Time string like "8:30am", "2:30pm", "All Day", "Tentative"
            base_date: The date to combine with the parsed time

        Returns:
            datetime with the parsed time, or None for special cases
        """
        if not time_str:
            return None

        time_str = time_str.strip()

        # Handle special cases
        if time_str.lower() in ("all day", ""):
            return datetime(base_date.year, base_date.month, base_date.day, 0, 0)

        if time_str.lower() == "tentative":
            return None

        # Parse standard time format: "8:30am" or "2:30pm"
        time_pattern = r"(\d{1,2}):(\d{2})(am|pm)"
        match = re.match(time_pattern, time_str.lower())

        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2))
        meridian = match.group(3)

        # Convert to 24-hour format
        if meridian == "pm" and hour != 12:
            hour += 12
        elif meridian == "am" and hour == 12:
            hour = 0

        return datetime(base_date.year, base_date.month, base_date.day, hour, minute)

    def _parse_calendar_table(
        self, page: Page, base_date: datetime
    ) -> List[Dict[str, Any]]:
        """Parse the calendar table from the current page.

        Args:
            page: Playwright page object
            base_date: Base date for parsing times

        Returns:
            List of event dictionaries
        """
        events: List[Dict[str, Any]] = []

        # Find all calendar rows
        rows = page.query_selector_all(".calendar__row")

        current_date = base_date
        current_time_str = ""

        for row in rows:
            try:
                # Check if this row has event data (skip header/separator rows)
                event_cell = row.query_selector(".calendar__event")
                if event_cell is None:
                    continue

                # Parse date if present (date spans multiple rows)
                date_cell = row.query_selector(".calendar__date")
                if date_cell:
                    date_text = date_cell.inner_text().strip()
                    if date_text:
                        # Parse date like "Mon Nov 24"
                        parsed_date = self._parse_date_cell(date_text, base_date)
                        if parsed_date:
                            current_date = parsed_date

                # Parse time (time spans multiple rows with same value)
                time_cell = row.query_selector(".calendar__time")
                if time_cell:
                    time_text = time_cell.inner_text().strip()
                    if time_text:
                        current_time_str = time_text

                # Parse currency
                currency_cell = row.query_selector(".calendar__currency")
                currency = ""
                if currency_cell:
                    currency = currency_cell.inner_text().strip()

                # Parse impact
                impact_cell = row.query_selector(".calendar__impact span")
                impact = self._parse_impact(impact_cell)

                # Parse event name
                event_name = event_cell.inner_text().strip()

                # Parse actual, forecast, previous values
                actual_cell = row.query_selector(".calendar__actual")
                actual = actual_cell.inner_text().strip() if actual_cell else ""

                forecast_cell = row.query_selector(".calendar__forecast")
                forecast = forecast_cell.inner_text().strip() if forecast_cell else ""

                previous_cell = row.query_selector(".calendar__previous")
                previous = previous_cell.inner_text().strip() if previous_cell else ""

                # Build timestamp
                timestamp = self._parse_time(current_time_str, current_date)

                event = {
                    "timestamp": timestamp,
                    "currency": currency,
                    "event_name": event_name,
                    "impact": impact,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous,
                }

                events.append(event)

            except Exception:
                # Skip rows that can't be parsed
                continue

        return events

    def _parse_date_cell(
        self, date_text: str, base_date: datetime
    ) -> Optional[datetime]:
        """Parse a date cell text like 'Mon Nov 24'.

        Args:
            date_text: Date text from the calendar cell
            base_date: Reference date for year context

        Returns:
            Parsed datetime or None
        """
        # Date format: "Mon Nov 24" or similar
        pattern = r"[A-Za-z]+\s+([A-Za-z]+)\s+(\d+)"
        match = re.match(pattern, date_text)

        if not match:
            return None

        month_str = match.group(1)
        day = int(match.group(2))

        # Map month abbreviation to number
        months = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }

        month = months.get(month_str.lower()[:3])
        if month is None:
            return None

        # Use base_date's year, adjust for year boundary
        year = base_date.year

        return datetime(year, month, day)

    def _parse_date(
        self, date_text: str, year: Optional[int] = None
    ) -> Optional[datetime]:
        """Parse various date formats.

        Supports formats like:
        - "Mon Nov 25" (weekday + month + day)
        - "Nov 25" (month + day)
        - "Nov 25, 2024" (month + day + year)

        Args:
            date_text: Date text to parse
            year: Optional year to use if not in date_text

        Returns:
            Parsed datetime or None
        """
        if not date_text or not date_text.strip():
            return None

        date_text = date_text.strip()

        # Map month abbreviations to numbers
        months = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }

        # Try format: "Mon Nov 25" or "Nov 25"
        pattern_with_weekday = r"(?:[A-Za-z]+\s+)?([A-Za-z]+)\s+(\d+)(?:,?\s*(\d{4}))?"
        match = re.match(pattern_with_weekday, date_text)

        if not match:
            return None

        month_str = match.group(1)
        day = int(match.group(2))
        parsed_year = match.group(3)

        month = months.get(month_str.lower()[:3])
        if month is None:
            return None

        # Determine year
        if parsed_year:
            final_year = int(parsed_year)
        elif year:
            final_year = year
        else:
            final_year = datetime.now().year

        return datetime(final_year, month, day)

    def _parse_value(self, value: Optional[str]) -> Optional[str]:
        """Parse and clean an economic value string.

        Handles empty strings, whitespace, and various value formats.

        Args:
            value: Value string to parse (e.g., "2.5%", "200K", "-0.5%")

        Returns:
            Cleaned value string or None for empty/whitespace values
        """
        if value is None:
            return None

        if not isinstance(value, str):
            return None

        cleaned = value.strip()

        if not cleaned:
            return None

        return cleaned

    def scrape_week(
        self,
        start_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Scrape economic events for a week.

        Args:
            start_date: Optional start date for the week to scrape.
                       If None, scrapes the current week.

        Returns:
            List of event dictionaries with keys:
                - timestamp: datetime of the event
                - currency: Currency affected (e.g., "USD", "EUR")
                - event_name: Name of the economic event
                - impact: Impact level ("Low", "Medium", "High")
                - actual: Actual value (if released)
                - forecast: Forecast value
                - previous: Previous period's value
        """
        self._init_browser()

        if start_date is None:
            start_date = datetime.now()

        url = self._generate_week_url(start_date)

        self._apply_rate_limit()
        self._page.goto(url, wait_until="domcontentloaded")
        self._last_request_time = time.time()

        # Wait for Cloudflare challenge to complete and page to stabilize
        self._page.wait_for_timeout(3000)

        # Wait for calendar rows to be present
        self._page.wait_for_selector(
            ".calendar__row", state="attached", timeout=self.timeout
        )

        return self._parse_calendar_table(self._page, start_date)

    def scrape_day(
        self,
        date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Scrape economic events for a single day.

        Args:
            date: Optional date to scrape. If None, scrapes today.

        Returns:
            List of event dictionaries (same format as scrape_week)
        """
        self._init_browser()

        if date is None:
            date = datetime.now()

        url = self._generate_day_url(date)

        self._apply_rate_limit()
        self._page.goto(url, wait_until="domcontentloaded")
        self._last_request_time = time.time()

        # Wait for Cloudflare challenge to complete and page to stabilize
        self._page.wait_for_timeout(3000)

        # Wait for calendar rows to be present
        self._page.wait_for_selector(
            ".calendar__row", state="attached", timeout=self.timeout
        )

        return self._parse_calendar_table(self._page, date)

    def close(self) -> None:
        """Close the browser and clean up resources."""
        if self._browser is not None:
            self._browser.close()

        if self._playwright is not None:
            self._playwright.stop()

        # Reset state
        self._browser = None
        self._playwright = None
        self._page = None

    def __enter__(self) -> "ForexFactoryScraper":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
