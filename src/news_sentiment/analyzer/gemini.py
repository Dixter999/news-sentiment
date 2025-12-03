"""
Sentiment Analyzer using Google Gemini API.

This module provides sentiment analysis for economic events
using Google's Gemini generative AI model.
"""

import io
import json
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

import google.generativeai as genai
import requests
from google.api_core.exceptions import ResourceExhausted
from PIL import Image


class SentimentAnalyzer:
    """Sentiment analyzer using Google Gemini API.

    Analyzes economic events to determine their market sentiment impact
    based on actual vs forecast values and event context.

    Attributes:
        model_name: Name of the Gemini model to use
        api_key: API key for Gemini API
        max_retries: Maximum number of retries for rate-limited requests
    """

    PROMPT_TEMPLATE = """
Analyze the following economic event and provide a sentiment score.

Event: {event_name}
Currency: {currency}
Impact Level: {impact}
Actual: {actual}
Forecast: {forecast}
Previous: {previous}

Score the sentiment impact on {currency} from -1.0 (strongly bearish) to 1.0 (strongly bullish).

Consider:
- Whether actual beat/missed forecast
- The magnitude of the difference
- Historical significance of this indicator
- Market expectations

Respond with JSON only:
{{"score": <float>, "reasoning": "<brief explanation>"}}
"""

    # Image analysis prompt for Reddit posts with charts/screenshots
    IMAGE_PROMPT_TEMPLATE = """
Analyze this trading/financial image along with the post context.

Post Title: {title}
Subreddit: {subreddit}
Post Text: {body}

Analyze the image for:
1. Chart patterns (if it's a chart): trend direction, support/resistance, indicators
2. Trading positions: profit/loss shown, position size, entry/exit points
3. Market sentiment signals: bullish/bearish patterns, volume, momentum
4. Any text/numbers in the image: price targets, percentages, key figures

Based on the image AND text context, provide a sentiment score.

Score from -1.0 (strongly bearish market sentiment) to 1.0 (strongly bullish sentiment).
Consider: Does this suggest markets going up or down? Is the trader winning or losing?
For profit screenshots: winning = bullish sentiment indicator
For chart analysis: uptrend = bullish, downtrend = bearish

Respond with JSON only:
{{"score": <float>, "reasoning": "<brief explanation based on image analysis>"}}
"""

    # Patterns that indicate image URLs
    IMAGE_URL_PATTERNS = [
        r"i\.redd\.it",
        r"i\.imgur\.com",
        r"preview\.redd\.it",
        r"\.jpeg$",
        r"\.jpg$",
        r"\.png$",
        r"\.gif$",
        r"\.webp$",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        max_retries: int = 3,
    ) -> None:
        """Initialize the sentiment analyzer.

        Args:
            api_key: Optional API key. If not provided, uses
                    GEMINI_API_KEY environment variable.
            model_name: Gemini model to use (default: "gemini-2.0-flash")
            max_retries: Maximum retries for rate-limited requests (default: 3)

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Provide api_key parameter "
                "or set GEMINI_API_KEY environment variable."
            )

        self.model_name = model_name
        self.max_retries = max_retries

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def analyze(
        self,
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze sentiment for an economic event.

        Args:
            event: Dictionary containing event data with keys:
                - event_name: Name of the economic event
                - currency: Currency affected
                - impact: Impact level (Low/Medium/High)
                - actual: Actual value (if released)
                - forecast: Forecast value
                - previous: Previous period's value

        Returns:
            Dictionary with:
                - sentiment_score: Float from -1.0 (bearish) to 1.0 (bullish)
                - raw_response: Dict with reasoning and full_response
        """
        try:
            prompt = self._build_prompt(event)

            def generate_content() -> Any:
                return self.model.generate_content(prompt)

            response = self._retry_with_backoff(generate_content)
            return self._parse_response(response.text)

        except Exception as e:
            return {
                "sentiment_score": 0.0,
                "raw_response": {
                    "error": str(e),
                    "full_response": "",
                },
            }

    def batch_analyze(
        self,
        events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple events.

        Args:
            events: List of event dictionaries

        Returns:
            List of analysis result dictionaries
        """
        if not events:
            return []

        results = []
        for event in events:
            result = self.analyze(event)
            results.append(result)

        return results

    def _build_prompt(self, event: Dict[str, Any]) -> str:
        """Build the prompt for Gemini from event data.

        Args:
            event: Dictionary with event data

        Returns:
            Formatted prompt string
        """
        return self.PROMPT_TEMPLATE.format(
            event_name=event.get("event_name", "Unknown"),
            currency=event.get("currency", "Unknown"),
            impact=event.get("impact", "Unknown"),
            actual=event.get("actual") or "Not released",
            forecast=event.get("forecast") or "Not available",
            previous=event.get("previous") or "Not available",
        )

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini response.

        Args:
            response_text: Raw text response from Gemini

        Returns:
            Dictionary with sentiment_score and raw_response
        """
        try:
            # Try to extract JSON from response (handles extra text)
            json_match = re.search(r"\{[^{}]*\}", response_text)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                result = json.loads(response_text)

            # Validate score is numeric
            score_value = result.get("score", 0.0)
            if not isinstance(score_value, (int, float)):
                raise ValueError(f"Score must be numeric, got {type(score_value)}")

            score = self._validate_score(float(score_value))

            return {
                "sentiment_score": score,
                "raw_response": {
                    "reasoning": result.get("reasoning", ""),
                    "full_response": response_text,
                },
            }

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return {
                "sentiment_score": 0.0,
                "raw_response": {
                    "error": str(e),
                    "full_response": response_text,
                },
            }

    def _validate_score(self, score: float) -> float:
        """Ensure score is in [-1.0, 1.0] range.

        Args:
            score: Raw score value

        Returns:
            Score clamped to valid range
        """
        return max(-1.0, min(1.0, score))

    def is_image_url(self, url: Optional[str]) -> bool:
        """Check if URL points to an image.

        Args:
            url: URL to check

        Returns:
            True if URL matches image patterns
        """
        if not url:
            return False
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in self.IMAGE_URL_PATTERNS)

    def _download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """Download image from URL.

        Args:
            url: Image URL
            timeout: Request timeout in seconds

        Returns:
            PIL Image object or None if download fails
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Load image from bytes
            image = Image.open(io.BytesIO(response.content))
            # Convert to RGB if necessary (for RGBA/P mode images)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            return image
        except Exception:
            return None

    def analyze_reddit_post(
        self,
        post: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze sentiment for a Reddit post, with image support.

        If the post URL points to an image, performs multimodal analysis.
        Otherwise falls back to text-only analysis.

        Args:
            post: Dictionary containing post data with keys:
                - title: Post title
                - subreddit: Subreddit name
                - body: Post body text (optional)
                - url: Post URL (may be image)
                - flair: Post flair (optional)

        Returns:
            Dictionary with:
                - sentiment_score: Float from -1.0 to 1.0
                - raw_response: Dict with reasoning and full_response
                - analyzed_image: Boolean indicating if image was analyzed
        """
        url = post.get("url", "")
        analyzed_image = False

        try:
            # Check if post has an image URL
            if self.is_image_url(url):
                image = self._download_image(url)
                if image:
                    # Multimodal analysis with image
                    prompt = self.IMAGE_PROMPT_TEMPLATE.format(
                        title=post.get("title", ""),
                        subreddit=post.get("subreddit", ""),
                        body=post.get("body", "") or "(no text)",
                    )

                    def generate_with_image() -> Any:
                        return self.model.generate_content([prompt, image])

                    response = self._retry_with_backoff(generate_with_image)
                    result = self._parse_response(response.text)
                    result["analyzed_image"] = True
                    return result

            # Fallback to text-only analysis
            prompt = self._build_reddit_prompt(post)

            def generate_content() -> Any:
                return self.model.generate_content(prompt)

            response = self._retry_with_backoff(generate_content)
            result = self._parse_response(response.text)
            result["analyzed_image"] = False
            return result

        except Exception as e:
            return {
                "sentiment_score": 0.0,
                "raw_response": {
                    "error": str(e),
                    "full_response": "",
                },
                "analyzed_image": analyzed_image,
            }

    def _build_reddit_prompt(self, post: Dict[str, Any], image_failed: bool = False) -> str:
        """Build prompt for text-only Reddit post analysis.

        Args:
            post: Dictionary with post data
            image_failed: Whether image download failed for this post

        Returns:
            Formatted prompt string
        """
        # Build the base prompt
        base_prompt = f"""
Analyze this Reddit post for market sentiment.

Title: {post.get("title", "")}
Subreddit: r/{post.get("subreddit", "")}
Flair: {post.get("flair", "None")}"""

        # Add image failure context if applicable
        if image_failed:
            url = post.get("url", "")
            base_prompt += f"""
Image URL (unavailable for analysis): {url}
Note: The image at the URL above could not be downloaded for analysis. 
Please analyze the sentiment based on the title, context, and any available text."""

        # Add the post text
        base_prompt += f"""
Post Text: {post.get("body", "") or "(no text)"}

Score the market sentiment from -1.0 (strongly bearish) to 1.0 (strongly bullish).

Consider:
- Is the post expressing bullish or bearish sentiment?
- What market direction does the discussion suggest?
- Are people optimistic or pessimistic about price movement?"""

        # Add special instruction for image-failed posts
        if image_failed:
            base_prompt += """
- Since the image is unavailable, focus on analyzing sentiment from the title and any textual context"""

        base_prompt += """

Respond with JSON only:
{{"score": <float>, "reasoning": "<brief explanation>"}}
"""
        return base_prompt

    def _retry_with_backoff(
        self,
        func: Callable[[], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with exponential backoff on rate limit.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of successful function call

        Raises:
            Exception: If all retries exhausted or non-rate-limit error
        """
        base_delay = 1.0
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except ResourceExhausted as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = base_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    raise

        raise last_exception  # type: ignore
