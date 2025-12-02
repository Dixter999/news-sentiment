"""
Sentiment Analyzer using Google Gemini API.

This module provides sentiment analysis for economic events
using Google's Gemini generative AI model.
"""

import json
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted


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
