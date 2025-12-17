# Scraper Code Quality Standards

**Simplified code quality rules for web scraping projects**

## Core Principles for Scrapers

1. **Resilience** - Handle failures gracefully
2. **Efficiency** - Don't waste resources
3. **Maintainability** - Easy to update when sites change
4. **Respectfulness** - Don't abuse target servers

## Code Organization

### File Structure
```
project/
├── scrapers/
│   ├── __init__.py
│   ├── reddit_scraper.py
│   ├── forexfactory_scraper.py
│   └── base_scraper.py      # Common scraper logic
├── parsers/
│   ├── html_parser.py
│   └── json_parser.py
├── storage/
│   ├── database.py
│   └── file_storage.py
├── utils/
│   ├── rate_limiter.py
│   ├── retry.py
│   └── validators.py
└── tests/
    ├── test_scrapers.py
    └── test_parsers.py
```

### Naming Conventions
```python
# Classes: PascalCase
class RedditScraper:
    pass

# Functions/methods: snake_case
def fetch_posts(subreddit, limit=100):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10

# Private methods: _underscore_prefix
def _parse_html(self, html):
    pass
```

## Essential Patterns for Scrapers

### 1. Base Scraper Class (DRY Principle)
```python
from abc import ABC, abstractmethod
import requests
import time

class BaseScraper(ABC):
    """Base class for all scrapers"""

    def __init__(self, rate_limit=2.0, timeout=10):
        self.session = requests.Session()
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0

    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def fetch(self, url):
        """Fetch URL with rate limiting and error handling"""
        self._rate_limit_wait()
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.handle_error(e, url)
            return None

    @abstractmethod
    def parse(self, response):
        """Parse response - must be implemented by subclasses"""
        pass

    def handle_error(self, error, url):
        """Log and handle errors"""
        print(f"Error fetching {url}: {error}")
```

### 2. Error Handling with Retry Logic
```python
from functools import wraps
import time

def retry_on_failure(max_retries=3, backoff_factor=2):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise  # Re-raise on final attempt

                    wait_time = backoff_factor ** attempt
                    print(f"Attempt {attempt + 1} failed: {e}")
                    print(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator

# Usage
@retry_on_failure(max_retries=3)
def fetch_reddit_posts(subreddit):
    # Scraping logic here
    pass
```

### 3. Data Validation
```python
from typing import Dict, List, Optional
from pydantic import BaseModel, validator

class RedditPost(BaseModel):
    """Validated Reddit post model"""
    id: str
    title: str
    author: str
    score: int
    created_utc: float
    url: Optional[str]

    @validator('score')
    def score_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Score cannot be negative')
        return v

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

# Usage
def parse_post(raw_data):
    try:
        return RedditPost(**raw_data)
    except ValueError as e:
        print(f"Invalid post data: {e}")
        return None
```

### 4. Configuration Management
```python
import os
from dataclasses import dataclass

@dataclass
class ScraperConfig:
    """Centralized configuration"""
    reddit_client_id: str = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret: str = os.getenv('REDDIT_CLIENT_SECRET')
    reddit_user_agent: str = os.getenv('REDDIT_USER_AGENT')

    rate_limit_delay: float = 2.0
    max_retries: int = 3
    timeout: int = 10

    def __post_init__(self):
        """Validate required environment variables"""
        if not all([self.reddit_client_id, self.reddit_client_secret]):
            raise ValueError("Missing required environment variables")

# Usage
config = ScraperConfig()
scraper = RedditScraper(config)
```

## Code Quality Checklist

### Before Committing

- [ ] Code follows naming conventions
- [ ] Error handling implemented
- [ ] Rate limiting in place
- [ ] No hardcoded credentials
- [ ] Tests written for core logic
- [ ] No debug print statements
- [ ] Docstrings for public methods
- [ ] Type hints for function signatures

### Functions Should Be

- **Short** - Max 50 lines per function
- **Single Purpose** - One responsibility
- **Well Named** - Describes what it does
- **Testable** - Easy to write unit tests

### Example: Good vs Bad

```python
# ❌ BAD - Too long, multiple responsibilities
def scrape_and_store(subreddit, db_connection):
    # 100 lines of mixed scraping, parsing, validation, and storage
    pass

# ✅ GOOD - Separated concerns
def scrape_posts(subreddit) -> List[Dict]:
    """Scrape posts from subreddit"""
    pass

def validate_posts(posts: List[Dict]) -> List[RedditPost]:
    """Validate and transform posts"""
    pass

def store_posts(posts: List[RedditPost], db_connection):
    """Store validated posts in database"""
    pass
```

## Performance for Scrapers

### DO
- ✅ Use connection pooling
- ✅ Batch database writes
- ✅ Cache parsed results
- ✅ Use async for I/O-bound operations (if needed)

### DON'T
- ❌ Make sequential requests when parallel is possible
- ❌ Parse the same HTML multiple times
- ❌ Store duplicate data
- ❌ Load entire datasets into memory

### Example: Efficient Scraping
```python
import asyncio
import aiohttp

async def fetch_multiple_pages(urls):
    """Fetch multiple URLs concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()
```

## Testing Requirements

### Unit Tests (MANDATORY)
```python
import pytest
from scrapers.reddit_scraper import RedditScraper

def test_rate_limiting():
    """Verify rate limiting enforces delays"""
    scraper = RedditScraper(rate_limit=1.0)

    start = time.time()
    scraper.fetch("https://example.com")
    scraper.fetch("https://example.com")
    elapsed = time.time() - start

    assert elapsed >= 1.0, "Rate limiting not enforced"

def test_retry_on_failure(mocker):
    """Verify retry logic works"""
    mock_get = mocker.patch('requests.Session.get')
    mock_get.side_effect = [
        requests.RequestException("Timeout"),
        requests.RequestException("Timeout"),
        mocker.Mock(status_code=200, text="Success")
    ]

    result = fetch_with_retry("https://example.com", max_retries=3)
    assert result.text == "Success"
    assert mock_get.call_count == 3
```

### Integration Tests
```python
@pytest.mark.integration
def test_full_scraping_workflow():
    """Test end-to-end scraping workflow"""
    scraper = RedditScraper(config)

    # Scrape real data (use test subreddit)
    posts = scraper.scrape_posts('test', limit=5)

    assert len(posts) > 0
    assert all(isinstance(p, RedditPost) for p in posts)
```

## Documentation Requirements

### Docstrings (REQUIRED for Public Methods)
```python
def scrape_posts(subreddit: str, limit: int = 100) -> List[RedditPost]:
    """
    Scrape posts from a subreddit.

    Args:
        subreddit: Name of the subreddit (e.g., 'python')
        limit: Maximum number of posts to scrape (default: 100)

    Returns:
        List of validated RedditPost objects

    Raises:
        ValueError: If subreddit is invalid
        RateLimitError: If Reddit API rate limit is exceeded

    Example:
        >>> scraper = RedditScraper()
        >>> posts = scraper.scrape_posts('python', limit=10)
        >>> len(posts)
        10
    """
    pass
```

## Anti-Patterns for Scrapers

### NEVER DO
- ❌ Scrape without rate limiting
- ❌ Ignore error responses
- ❌ Store raw HTML (parse and extract data)
- ❌ Use regex for complex HTML parsing (use BeautifulSoup/lxml)
- ❌ Hardcode URLs or selectors
- ❌ Run scrapers as long-running processes without monitoring

## Monitoring & Logging

### Simple Logging Setup
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.info(f"Starting scrape for subreddit: {subreddit}")
logger.warning(f"Rate limit hit, waiting 60s")
logger.error(f"Failed to parse post ID: {post_id}")
```

### Metrics to Track
- Number of posts scraped
- Success/failure rate
- Average response time
- Rate limit hits
- Errors by type

## Summary

**For scraper projects, prioritize:**

1. **Resilience** - Handle network failures, rate limits, and parsing errors
2. **Efficiency** - Batch operations, cache results, respect rate limits
3. **Maintainability** - Modular code, clear separation of concerns
4. **Compliance** - Respect ToS, robots.txt, and rate limits

**Simple is better than complex for scrapers. Focus on:**
- Clear error handling
- Proper rate limiting
- Validated data structures
- Testable components
