"""
Response parsers for Gemini API sentiment analysis.

This module provides utilities for parsing and extracting sentiment
scores from Gemini API responses. It handles various response formats
including clean JSON, JSON with extra text, and fallback text parsing.

Stream B - Issue #4: Implement Gemini Sentiment Analyzer
"""

import json
import re
from typing import Any, Dict, Optional, Tuple


def validate_score(score: float) -> float:
    """Clamp score to [-1.0, 1.0] range.

    Args:
        score: The sentiment score to validate and clamp.

    Returns:
        Score clamped to the valid range [-1.0, 1.0].

    Examples:
        >>> validate_score(0.5)
        0.5
        >>> validate_score(1.5)
        1.0
        >>> validate_score(-2.0)
        -1.0
    """
    return max(-1.0, min(1.0, float(score)))


def extract_json_from_text(text: str) -> Optional[str]:
    """Extract JSON object from text that may contain extra content.

    LLMs sometimes add explanatory text before/after JSON. This function
    attempts to extract the JSON object from such responses.

    Args:
        text: Raw text that may contain a JSON object.

    Returns:
        Extracted JSON string if found, None otherwise.

    Examples:
        >>> extract_json_from_text('{"score": 0.5}')
        '{"score": 0.5}'
        >>> extract_json_from_text('Here is my analysis:\\n{"score": 0.5}')
        '{"score": 0.5}'
        >>> extract_json_from_text('No JSON here')
        None
    """
    if not text or not text.strip():
        return None

    # Try to find JSON object in the text
    # Pattern matches { ... } including nested braces
    patterns = [
        # Standard JSON object
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
        # JSON in markdown code block
        r"```(?:json)?\s*(\{.*?\})\s*```",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # For code block pattern, use the captured group
            json_str = match.group(1) if match.lastindex else match.group(0)
            # Validate it's actually parseable JSON
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                continue

    return None


def parse_score_from_text(text: str) -> Tuple[float, str]:
    """Fallback parser for when JSON parsing fails.

    Tries to extract a score from natural language response by
    looking for explicit score mentions or sentiment keywords.

    Args:
        text: Natural language text to parse.

    Returns:
        Tuple of (score: float, reasoning: str).
        Score defaults to 0.0 if nothing can be extracted.

    Examples:
        >>> score, reason = parse_score_from_text("score is 0.6")
        >>> score
        0.6
        >>> score, reason = parse_score_from_text("strongly bullish")
        >>> score > 0
        True
    """
    if not text or not text.strip():
        return 0.0, ""

    text_lower = text.lower()
    reasoning = text.strip()

    # Try to find explicit score mention
    score_patterns = [
        r"score[:\s]+is[:\s]+(-?\d+\.?\d*)",
        r"score[:\s]+(-?\d+\.?\d*)",
        r"sentiment[:\s]+score[:\s]+(-?\d+\.?\d*)",
        r"(-?\d+\.?\d*)\s*(?:out of|/)\s*1",
    ]

    for pattern in score_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                score = float(match.group(1))
                return validate_score(score), reasoning
            except ValueError:
                continue

    # Keyword-based sentiment detection
    strong_bullish = ["strongly bullish", "very bullish", "extremely positive"]
    bullish = ["bullish", "positive", "optimistic", "favorable"]
    strong_bearish = ["strongly bearish", "very bearish", "extremely negative"]
    bearish = ["bearish", "negative", "pessimistic", "unfavorable"]
    neutral = ["neutral", "no change", "unchanged", "mixed"]

    for phrase in strong_bullish:
        if phrase in text_lower:
            return 0.8, reasoning

    for phrase in bullish:
        if phrase in text_lower:
            return 0.5, reasoning

    for phrase in strong_bearish:
        if phrase in text_lower:
            return -0.8, reasoning

    for phrase in bearish:
        if phrase in text_lower:
            return -0.5, reasoning

    for phrase in neutral:
        if phrase in text_lower:
            return 0.0, reasoning

    # Default to neutral if no clear sentiment found
    return 0.0, reasoning


def parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parse Gemini response and extract score and reasoning.

    This is the main parsing function that handles various response
    formats from Gemini API. It first tries JSON parsing, then falls
    back to text extraction.

    Args:
        response_text: Raw response text from Gemini API.

    Returns:
        Dictionary with:
            - score: float (sentiment score from -1.0 to 1.0)
            - reasoning: str (explanation of the analysis)
            - error: str (only present if parsing failed)

    Examples:
        >>> result = parse_gemini_response('{"score": 0.75, "reasoning": "Good"}')
        >>> result['score']
        0.75
        >>> result = parse_gemini_response('Invalid response')
        >>> 'error' in result
        True
    """
    if not response_text or not response_text.strip():
        return {
            "score": 0.0,
            "reasoning": "",
            "error": "Empty response from API",
        }

    # Try to extract JSON from the response
    json_str = extract_json_from_text(response_text)

    if json_str:
        try:
            data = json.loads(json_str)

            # Validate that we have a score
            score_value = data.get("score")

            if score_value is None:
                return {
                    "score": 0.0,
                    "reasoning": data.get("reasoning", ""),
                    "error": "Missing 'score' field in response",
                }

            # Try to convert score to float
            try:
                score = float(score_value)
            except (TypeError, ValueError):
                return {
                    "score": 0.0,
                    "reasoning": data.get("reasoning", ""),
                    "error": f"Invalid score value: {score_value}",
                }

            # Clamp score to valid range
            score = validate_score(score)
            reasoning = data.get("reasoning", "")

            return {
                "score": score,
                "reasoning": reasoning if reasoning else "",
            }

        except json.JSONDecodeError:
            # JSON extraction found something but it's not valid
            pass

    # Fallback to text-based parsing
    score, reasoning = parse_score_from_text(response_text)

    return {
        "score": score,
        "reasoning": reasoning,
        "error": "Could not parse JSON from response, used text fallback",
    }
