"""
Tests for Gemini analyzer image download functionality.

Following TDD principles:
1. RED: Write failing tests first
2. GREEN: Implement minimum code to pass
3. REFACTOR: Clean up while keeping tests green
"""

import logging
from unittest.mock import MagicMock, patch, call
import requests
from PIL import Image
import io
import pytest

from news_sentiment.analyzer.gemini import SentimentAnalyzer


class TestImageDownloadWithLogging:
    """Test cases for _download_image with proper logging and retry."""

    def test_download_image_logs_connection_error(self, caplog):
        """Should log connection errors when image download fails."""
        with patch("news_sentiment.analyzer.gemini.genai"):
            analyzer = SentimentAnalyzer(api_key="test-key")
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Failed to connect")
            
            with caplog.at_level(logging.ERROR):
                result = analyzer._download_image("http://example.com/image.jpg")
            
            # Should return structured failure info (not just None)
            assert result is not None
            assert result.get("error") is True
            assert "ConnectionError" in result.get("error_type", "")
            assert "Failed to connect" in result.get("error_message", "")
            
            # Should log the error
            assert len(caplog.records) > 0
            assert "Failed to download image" in caplog.text
            assert "http://example.com/image.jpg" in caplog.text
            assert "ConnectionError" in caplog.text

    def test_download_image_logs_timeout_error(self, caplog):
        """Should log timeout errors when image download times out."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")
            
            with caplog.at_level(logging.ERROR):
                result = analyzer._download_image("http://example.com/image.jpg")
            
            assert result is not None
            assert result.get("error") is True
            assert "Timeout" in result.get("error_type", "")
            
            assert "Failed to download image" in caplog.text
            assert "Timeout" in caplog.text

    def test_download_image_logs_http_error(self, caplog):
        """Should log HTTP errors (404, 500, etc.)."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with caplog.at_level(logging.ERROR):
                result = analyzer._download_image("http://example.com/image.jpg")
            
            assert result is not None
            assert result.get("error") is True
            assert "HTTPError" in result.get("error_type", "")
            assert "404 Not Found" in result.get("error_message", "")


class TestImageDownloadRetryLogic:
    """Test cases for retry logic on transient failures."""

    def test_download_image_retries_on_connection_error(self):
        """Should retry on connection errors."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        # Create valid image bytes
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # First attempt fails, second succeeds
            mock_response = MagicMock()
            mock_response.content = img_bytes.getvalue()
            mock_response.raise_for_status = MagicMock()
            
            mock_get.side_effect = [
                requests.ConnectionError("Connection failed"),
                mock_response
            ]
            
            result = analyzer._download_image("http://example.com/image.jpg")
            
            # Should succeed after retry
            assert result is not None
            assert result.get("error") is not True
            assert result.get("image") is not None
            assert isinstance(result.get("image"), Image.Image)
            assert result.get("retry_count", 0) == 1
            
            # Should have called get twice
            assert mock_get.call_count == 2

    def test_download_image_retries_on_timeout(self):
        """Should retry on timeout errors."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        # Create valid image bytes
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = img_bytes.getvalue()
            mock_response.raise_for_status = MagicMock()
            
            # First two attempts timeout, third succeeds
            mock_get.side_effect = [
                requests.Timeout("Timeout 1"),
                requests.Timeout("Timeout 2"),
                mock_response
            ]
            
            result = analyzer._download_image("http://example.com/image.jpg", max_retries=3)
            
            assert result is not None
            assert result.get("error") is not True
            assert result.get("image") is not None
            assert result.get("retry_count", 0) == 2
            assert mock_get.call_count == 3

    def test_download_image_stops_after_max_retries(self, caplog):
        """Should stop retrying after max_retries attempts."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Always timeout")
            
            with caplog.at_level(logging.ERROR):
                result = analyzer._download_image(
                    "http://example.com/image.jpg", 
                    max_retries=3
                )
            
            # Should fail after max retries
            assert result is not None
            assert result.get("error") is True
            assert result.get("retry_count", 0) == 3
            
            # Should have tried max_retries times
            assert mock_get.call_count == 3
            
            # Should log the final failure
            assert "after 3 retries" in caplog.text

    def test_download_image_no_retry_on_non_transient_errors(self):
        """Should NOT retry on non-transient errors like 404."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            result = analyzer._download_image("http://example.com/image.jpg", max_retries=3)
            
            # Should fail immediately without retries
            assert result is not None
            assert result.get("error") is True
            assert result.get("retry_count", 0) == 0
            
            # Should only call once (no retries for 404)
            assert mock_get.call_count == 1


class TestAnalyzeRedditPostWithImageFailure:
    """Test cases for analyze_reddit_post handling image failures."""

    def test_analyze_reddit_post_tracks_image_download_failure(self):
        """Should track image_download_failed in metadata."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        post = {
            "title": "Test Post",
            "subreddit": "test",
            "body": "",
            "url": "http://example.com/image.jpg"
        }
        
        with patch.object(analyzer, "is_image_url", return_value=True):
            with patch.object(analyzer, "_download_image") as mock_download:
                # Return failure info
                mock_download.return_value = {
                    "error": True,
                    "error_type": "ConnectionError",
                    "error_message": "Failed to connect"
                }
                
                with patch.object(analyzer, "model") as mock_model:
                    mock_response = MagicMock()
                    mock_response.text = '{"sentiment_score": 0.0, "reasoning": "No image available"}'
                    mock_model.generate_content.return_value = mock_response
                    
                    result = analyzer.analyze_reddit_post(post)
                    
                    # Should track failure in metadata
                    assert result.get("image_download_failed") is True
                    assert result.get("failure_reason") == "ConnectionError: Failed to connect"
                    assert result.get("analyzed_image") is False

    def test_analyze_reddit_post_includes_image_url_in_fallback(self):
        """Should include image URL context in fallback prompt when download fails."""
        analyzer = SentimentAnalyzer(api_key="test-key")
        
        post = {
            "title": "Market crash image",
            "subreddit": "wallstreetbets",
            "body": "",
            "url": "http://example.com/chart.jpg"
        }
        
        with patch.object(analyzer, "is_image_url", return_value=True):
            with patch.object(analyzer, "_download_image") as mock_download:
                mock_download.return_value = {
                    "error": True,
                    "error_type": "Timeout",
                    "error_message": "Request timed out"
                }
                
                with patch.object(analyzer, "model") as mock_model:
                    mock_response = MagicMock()
                    mock_response.text = '{"sentiment_score": 0.0, "reasoning": "Image unavailable"}'
                    mock_model.generate_content.return_value = mock_response
                    
                    result = analyzer.analyze_reddit_post(post)
                    
                    # Should have called generate_content with image URL context
                    call_args = mock_model.generate_content.call_args
                    prompt = call_args[0][0] if call_args else ""
                    
                    # Prompt should mention the failed image URL
                    assert "http://example.com/chart.jpg" in prompt or "image" in prompt.lower()