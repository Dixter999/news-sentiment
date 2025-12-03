"""
Tests for GeminiAnalyzer class focusing on image fallback functionality.

Following TDD principles:
1. RED - Write failing test first
2. GREEN - Write minimal code to pass
3. REFACTOR - Clean up while keeping tests green
"""

import pytest
from unittest.mock import MagicMock, patch
from news_sentiment.analyzer.gemini import SentimentAnalyzer


class TestBuildRedditPrompt:
    """Test cases for _build_reddit_prompt method with image failure handling."""

    def test_build_reddit_prompt_without_image_failed_parameter(self):
        """Test that _build_reddit_prompt works with existing signature (backward compatibility)."""
        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            # Mock the model configuration
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = SentimentAnalyzer(api_key="test-key")
            
            post = {
                "title": "Test post title",
                "subreddit": "wallstreetbets",
                "flair": "Discussion",
                "body": "Test post body"
            }
            
            # This should work with the current implementation
            prompt = analyzer._build_reddit_prompt(post)
            
            assert "Test post title" in prompt
            assert "wallstreetbets" in prompt
            assert "Test post body" in prompt
            # Should not mention anything about image failure
            assert "image" not in prompt.lower() or "fail" not in prompt.lower()

    def test_build_reddit_prompt_with_image_failed_false(self):
        """Test that prompt is unchanged when image_failed=False."""
        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            # Mock the model configuration
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = SentimentAnalyzer(api_key="test-key")
            
            post = {
                "title": "Test post title",
                "subreddit": "wallstreetbets",
                "flair": "Discussion",
                "body": "Test post body",
                "url": "https://example.com/regular-link"
            }
            
            # This will fail initially as the parameter doesn't exist yet
            prompt = analyzer._build_reddit_prompt(post, image_failed=False)
            
            assert "Test post title" in prompt
            assert "wallstreetbets" in prompt
            assert "Test post body" in prompt
            # Should not mention image failure
            assert "image" not in prompt.lower() or "fail" not in prompt.lower()

    def test_build_reddit_prompt_with_image_failed_true_includes_url(self):
        """Test that prompt includes image URL and context when image_failed=True."""
        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            # Mock the model configuration
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = SentimentAnalyzer(api_key="test-key")
            
            post = {
                "title": "Chart showing bullish pattern",
                "subreddit": "wallstreetbets",
                "flair": "Technical Analysis",
                "body": "",  # Empty body, common for image posts
                "url": "https://i.imgur.com/abc123.png"
            }
            
            # This will fail initially as the parameter doesn't exist yet
            prompt = analyzer._build_reddit_prompt(post, image_failed=True)
            
            # Check that basic info is still included
            assert "Chart showing bullish pattern" in prompt
            assert "wallstreetbets" in prompt
            
            # Check that image failure context is added
            assert "https://i.imgur.com/abc123.png" in prompt
            assert "image" in prompt.lower()
            assert any(word in prompt.lower() for word in ["unavailable", "failed", "could not", "unable"])
            
            # Check that it instructs to analyze based on available context
            assert any(phrase in prompt.lower() for phrase in [
                "based on the title",
                "from the title",
                "context available",
                "available information"
            ])

    def test_build_reddit_prompt_with_image_failed_true_no_url(self):
        """Test that prompt handles image_failed=True gracefully when no URL is present."""
        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            # Mock the model configuration
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            analyzer = SentimentAnalyzer(api_key="test-key")
            
            post = {
                "title": "Test post without URL",
                "subreddit": "stocks",
                "flair": "Discussion",
                "body": "Some text content"
            }
            
            # Even with image_failed=True, should handle missing URL gracefully
            prompt = analyzer._build_reddit_prompt(post, image_failed=True)
            
            assert "Test post without URL" in prompt
            assert "stocks" in prompt
            assert "Some text content" in prompt
            # Should still mention image context since image_failed=True
            assert any(word in prompt.lower() for word in ["image", "visual"])