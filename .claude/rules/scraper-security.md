# Scraper Security Checklist

**Priority:** CRITICAL for web scraping projects

## API Key & Credentials Management

### NEVER
- ❌ Hardcode API keys or credentials in code
- ❌ Commit `.env` files to git
- ❌ Share credentials in logs or error messages
- ❌ Use production credentials in development

### ALWAYS
- ✅ Use environment variables for all credentials
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate API keys regularly (quarterly minimum)
- ✅ Use different credentials for dev/staging/production

### Example
```python
# ❌ WRONG
reddit_client_id = "abc123secret"

# ✅ CORRECT
import os
reddit_client_id = os.environ.get('REDDIT_CLIENT_ID')
if not reddit_client_id:
    raise ValueError("REDDIT_CLIENT_ID not set")
```

## Rate Limiting & Respectful Scraping

### MANDATORY
- ✅ Respect `robots.txt`
- ✅ Implement exponential backoff on errors
- ✅ Add delays between requests (min 1-2 seconds)
- ✅ Use proper User-Agent headers
- ✅ Handle 429 (Too Many Requests) gracefully

### Example
```python
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Respectful retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=2,  # 1s, 2s, 4s delays
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.headers.update({
    'User-Agent': 'NewsSentimentBot/1.0 (contact@example.com)'
})

# Add delay between requests
time.sleep(2)  # 2 second delay
response = session.get(url)
```

## Data Privacy & Compliance

### REQUIRED
- ✅ Anonymize user data before storage
- ✅ Don't scrape or store PII (Personally Identifiable Information)
- ✅ Comply with GDPR if applicable
- ✅ Implement data retention policies

### What NOT to Store
- ❌ Email addresses
- ❌ Phone numbers
- ❌ Real names (unless public figures/authors)
- ❌ IP addresses
- ❌ Physical addresses

### Example
```python
def sanitize_user_data(post):
    """Remove PII before storing scraped data"""
    return {
        'username_hash': hash(post['username']),  # Hash, don't store real username
        'content': post['content'],
        'timestamp': post['timestamp'],
        'subreddit': post['subreddit'],
        # NO email, NO user_id, NO location
    }
```

## Error Handling & Logging

### SECURE LOGGING
```python
import logging

# ❌ WRONG - Logs credentials
logging.info(f"Connecting with API key: {api_key}")

# ✅ CORRECT - Masks sensitive data
logging.info(f"Connecting with API key: {api_key[:4]}***")

# ✅ CORRECT - No credentials in logs
logging.info("Successfully authenticated to Reddit API")
```

### Error Handling
```python
try:
    response = fetch_reddit_posts(subreddit)
except RateLimitError as e:
    # ✅ Log error without exposing credentials
    logging.warning(f"Rate limit hit for subreddit: {subreddit}")
    time.sleep(60)  # Wait 1 minute
    retry()
except Exception as e:
    # ✅ Generic error, no sensitive data
    logging.error(f"Failed to fetch posts: {type(e).__name__}")
    raise
```

## IP Blocking Prevention

### STRATEGIES
- ✅ Use proxy rotation (if permitted)
- ✅ Implement request throttling
- ✅ Respect `Retry-After` headers
- ✅ Use session cookies properly
- ✅ Random delays between requests

### Example
```python
import random
import time

def fetch_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Random delay (1-3 seconds)
            time.sleep(random.uniform(1, 3))

            response = requests.get(url, timeout=10)

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logging.warning(f"Rate limited, waiting {retry_after}s")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff: 2^attempt seconds
            wait_time = 2 ** attempt
            logging.info(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)
```

## Database Security (If Applicable)

### IF STORING SCRAPED DATA
- ✅ Use parameterized queries (prevent SQL injection)
- ✅ Encrypt sensitive data at rest
- ✅ Use connection pooling with timeouts
- ✅ Implement database backups

### Example
```python
# ❌ WRONG - SQL injection risk
cursor.execute(f"INSERT INTO posts VALUES ('{content}')")

# ✅ CORRECT - Parameterized query
cursor.execute("INSERT INTO posts (content) VALUES (?)", (content,))
```

## Legal & Ethical Considerations

### MUST CHECK
- ✅ Review website Terms of Service
- ✅ Check if scraping is explicitly prohibited
- ✅ Don't circumvent technical measures (CAPTCHAs, paywalls)
- ✅ Respect copyright and attribution
- ✅ Don't overload target servers

### RED FLAGS (Don't Proceed)
- ❌ Site explicitly prohibits scraping in ToS
- ❌ Site uses aggressive anti-scraping measures
- ❌ Content behind authentication/paywall
- ❌ Scraping would cause server strain

## Quick Security Checklist

Before deploying your scraper, verify:

- [ ] All API keys in environment variables
- [ ] `.env` in `.gitignore`
- [ ] Rate limiting implemented
- [ ] User-Agent header set
- [ ] Error handling with retries
- [ ] No PII being stored
- [ ] Logs don't contain credentials
- [ ] Compliance with robots.txt
- [ ] Respectful request delays
- [ ] Data retention policy defined

## Emergency Response

If your scraper is blocked or violating ToS:

1. **STOP** the scraper immediately
2. **REVIEW** error logs for ban reason
3. **CHECK** robots.txt and ToS compliance
4. **IMPLEMENT** stricter rate limiting
5. **CONTACT** site admin if appropriate

## References

- [Robots Exclusion Protocol](https://www.robotstxt.org/)
- [GDPR Compliance](https://gdpr.eu/)
- [Reddit API Rules](https://www.reddit.com/wiki/api)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)
