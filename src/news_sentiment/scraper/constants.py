"""
Constants for Forex Factory scraper.

Contains URL patterns, CSS selectors, and timezone definitions
used throughout the scraper module.
"""

# Base URL for Forex Factory calendar
BASE_URL = "https://www.forexfactory.com/calendar"

# URL pattern for fetching a specific week
# Format: ?week=nov25.2024 for week starting November 25, 2024
WEEK_URL_PATTERN = "{base}?week={month}{day}.{year}"

# URL pattern for fetching a specific month
# Format: ?month=nov.2024 for November 2024
MONTH_URL_PATTERN = "{base}?month={month}.{year}"

# CSS Selectors for parsing calendar table
SELECTOR_ROW = ".calendar__row"
SELECTOR_DATE = ".calendar__date"
SELECTOR_TIME = ".calendar__time"
SELECTOR_CURRENCY = ".calendar__currency"
SELECTOR_IMPACT = ".calendar__impact span"
SELECTOR_EVENT = ".calendar__event"
SELECTOR_ACTUAL = ".calendar__actual"
SELECTOR_FORECAST = ".calendar__forecast"
SELECTOR_PREVIOUS = ".calendar__previous"

# Timezone constants
# Forex Factory displays times in Eastern Time (ET)
# ET alternates between EST (UTC-5) and EDT (UTC-4)
ET_TIMEZONE = "America/New_York"
UTC_TIMEZONE = "UTC"

# Month abbreviations (lowercase) for URL construction
MONTH_ABBREVS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]

# Special time values that cannot be converted to actual times
SPECIAL_TIME_VALUES = frozenset({"tentative", "all day", ""})
