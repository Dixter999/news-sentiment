"""
Tests for image download failure scenarios in Gemini analyzer.

This module follows TDD principles - tests are written to define expected
behavior for image download failure handling, retry logic, and fallback
prompt generation.
"""

import io
import logging
from unittest.mock import MagicMock, Mock, patch, call
import time
import pytest
import requests
from PIL import Image
from requests.exceptions import Timeout, ConnectionError, HTTPError


class TestImageDownloadFailures:
    """Test cases for image download failure scenarios."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            return SentimentAnalyzer(api_key="test-key")

    @pytest.fixture
    def sample_post_with_image(self):
        """Sample Reddit post with image URL."""
        return {
            "title": "EUR/USD surges on ECB rate decision",
            "subreddit": "Forex",
            "body": "",  # Empty body, typical for image posts
            "url": "https://i.redd.it/example.jpg",
            "flair": "News"
        }

    def test_download_image_timeout_handling(self, analyzer):
        """Test that image download handles timeout gracefully with logging."""
        url = "https://example.com/image.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = Timeout("Request timed out")
            
            with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                result = analyzer._download_image(url, timeout=5)
                
                # Should return None on timeout
                assert result is None
                
                # Should log the timeout error with URL
                mock_logger.warning.assert_called_once()
                log_call = mock_logger.warning.call_args[0][0]
                assert "timeout" in log_call.lower()
                assert url in log_call
                assert "5 seconds" in log_call or "5s" in log_call

    def test_download_image_connection_error_handling(self, analyzer):
        """Test that image download handles connection errors with logging."""
        url = "https://unreachable.example.com/image.png"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = ConnectionError("Failed to establish connection")
            
            with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                result = analyzer._download_image(url)
                
                # Should return None on connection error
                assert result is None
                
                # Should log the connection error with URL
                mock_logger.warning.assert_called_once()
                log_call = mock_logger.warning.call_args[0][0]
                assert "connection" in log_call.lower() or "failed" in log_call.lower()
                assert url in log_call

    def test_download_image_http_error_handling(self, analyzer):
        """Test that image download handles HTTP errors (404, 403, etc.) with logging."""
        url = "https://example.com/forbidden.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = HTTPError("403 Forbidden")
            mock_get.return_value = mock_response
            
            with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                result = analyzer._download_image(url)
                
                # Should return None on HTTP error
                assert result is None
                
                # Should log the HTTP error with URL and status code
                mock_logger.warning.assert_called_once()
                log_call = mock_logger.warning.call_args[0][0]
                assert "403" in log_call or "forbidden" in log_call.lower()
                assert url in log_call

    def test_download_image_invalid_content_handling(self, analyzer):
        """Test that image download handles invalid image content with logging."""
        url = "https://example.com/not-an-image.txt"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"This is text, not an image"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                result = analyzer._download_image(url)
                
                # Should return None on invalid image content
                assert result is None
                
                # Should log the invalid content error with URL
                mock_logger.warning.assert_called_once()
                log_call = mock_logger.warning.call_args[0][0]
                assert "invalid" in log_call.lower() or "decode" in log_call.lower()
                assert url in log_call


class TestRetryLogicWithBackoff:
    """Test cases for retry logic with exponential backoff."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance with custom retry settings."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            return SentimentAnalyzer(api_key="test-key", max_retries=3)

    def test_download_image_with_retry_on_timeout(self, analyzer):
        """Test that image download retries on timeout with exponential backoff."""
        url = "https://example.com/image.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # Fail twice, succeed on third attempt
            mock_response = Mock()
            mock_response.content = b"fake image content"
            mock_response.raise_for_status.return_value = None
            
            mock_get.side_effect = [
                Timeout("First timeout"),
                Timeout("Second timeout"),
                mock_response
            ]
            
            with patch("news_sentiment.analyzer.gemini.Image.open") as mock_open:
                mock_image = Mock()
                mock_image.mode = "RGB"
                mock_open.return_value = mock_image
                
                with patch("news_sentiment.analyzer.gemini.time.sleep") as mock_sleep:
                    with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                        result = analyzer._download_image(url)
                        
                        # Should succeed after retries
                        assert result == mock_image
                        
                        # Should have called get 3 times
                        assert mock_get.call_count == 3
                        
                        # Should have exponential backoff delays
                        assert mock_sleep.call_count == 2
                        mock_sleep.assert_has_calls([
                            call(1),  # First retry: 2^0 = 1 second
                            call(2),  # Second retry: 2^1 = 2 seconds
                        ])
                        
                        # Should log retry attempts
                        assert mock_logger.info.call_count >= 2
                        retry_logs = [call[0][0] for call in mock_logger.info.call_args_list]
                        assert any("retry" in log.lower() and "1" in log for log in retry_logs)
                        assert any("retry" in log.lower() and "2" in log for log in retry_logs)

    def test_download_image_max_retries_exceeded(self, analyzer):
        """Test that image download gives up after max retries."""
        url = "https://example.com/image.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # Always fail
            mock_get.side_effect = Timeout("Persistent timeout")
            
            with patch("news_sentiment.analyzer.gemini.time.sleep"):
                with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                    result = analyzer._download_image(url)
                    
                    # Should return None after max retries
                    assert result is None
                    
                    # Should have attempted max_retries + 1 times (initial + retries)
                    assert mock_get.call_count == 4  # 1 initial + 3 retries
                    
                    # Should log final failure
                    mock_logger.error.assert_called_once()
                    error_log = mock_logger.error.call_args[0][0]
                    assert "failed after" in error_log.lower()
                    assert "3 retries" in error_log.lower() or "3 attempts" in error_log.lower()
                    assert url in error_log

    def test_download_image_no_retry_on_permanent_errors(self, analyzer):
        """Test that image download doesn't retry on permanent errors like 404."""
        url = "https://example.com/not-found.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                result = analyzer._download_image(url)
                
                # Should return None without retrying
                assert result is None
                
                # Should only call get once (no retries for 404)
                assert mock_get.call_count == 1
                
                # Should log the permanent error
                mock_logger.warning.assert_called_once()
                log_call = mock_logger.warning.call_args[0][0]
                assert "404" in log_call


class TestFallbackPromptGeneration:
    """Test cases for fallback prompt generation with image context."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = Mock()
            mock_response.text = '{"sentiment": 0.0, "reasoning": "Image unavailable"}'
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            return SentimentAnalyzer(api_key="test-key")

    def test_fallback_prompt_includes_image_context(self, analyzer):
        """Test that fallback prompt includes context about failed image."""
        post = {
            "title": "EUR/USD Technical Analysis Chart",
            "subreddit": "Forex",
            "body": "",  # Empty body
            "url": "https://i.redd.it/chart.jpg",
            "flair": "Technical"
        }
        
        with patch.object(analyzer, "_download_image", return_value=None):
            with patch.object(analyzer, "_build_reddit_prompt") as mock_build:
                mock_build.return_value = "Test prompt"
                
                result = analyzer.analyze_reddit_post(post)
                
                # Should call build_prompt with image failure context
                mock_build.assert_called_once_with(post, include_image_context=True)
                
                # Result should indicate no image was analyzed
                assert result["analyzed_image"] is False
                assert "image_download_failed" in result
                assert result["image_download_failed"] is True
                assert "failed_image_url" in result
                assert result["failed_image_url"] == post["url"]

    def test_fallback_prompt_text_generation(self, analyzer):
        """Test the actual fallback prompt includes image unavailability note."""
        post = {
            "title": "Chart showing EUR/USD breakout",
            "subreddit": "Forex",
            "body": "",
            "url": "https://i.redd.it/breakout.png",
        }
        
        # Test the actual prompt generation
        prompt = analyzer._build_reddit_prompt(post, include_image_context=True)
        
        # Prompt should mention the image URL and that it's unavailable
        assert post["url"] in prompt
        assert "image" in prompt.lower()
        assert any(word in prompt.lower() for word in ["unavailable", "failed", "inaccessible", "could not"])
        
        # Should still include the title and subreddit
        assert post["title"] in prompt
        assert post["subreddit"] in prompt

    def test_fallback_with_body_text_and_failed_image(self, analyzer):
        """Test fallback when post has both text and a failed image."""
        post = {
            "title": "EUR/USD Analysis",
            "subreddit": "Forex",
            "body": "The chart shows a clear breakout pattern. RSI indicates oversold.",
            "url": "https://i.redd.it/analysis.jpg",
        }
        
        with patch.object(analyzer, "_download_image", return_value=None):
            with patch.object(analyzer, "model.generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = '{"sentiment": 0.3, "reasoning": "Bullish based on text"}'
                mock_generate.return_value = mock_response
                
                result = analyzer.analyze_reddit_post(post)
                
                # Should use text content even though image failed
                call_args = mock_generate.call_args[0][0]
                assert post["body"] in call_args
                assert "RSI indicates oversold" in call_args
                
                # Should note that image was unavailable
                assert "image" in call_args.lower()
                assert post["url"] in call_args


class TestMetadataTracking:
    """Test cases for tracking metadata about failed image downloads."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            return SentimentAnalyzer(api_key="test-key")

    def test_metadata_includes_download_failure_reason(self, analyzer):
        """Test that response metadata includes specific failure reason."""
        post = {
            "title": "Technical chart",
            "subreddit": "Forex",
            "body": "",
            "url": "https://i.redd.it/chart.jpg",
        }
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = Timeout("Request timed out after 10 seconds")
            
            with patch.object(analyzer.model, "generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = '{"sentiment": 0.0, "reasoning": "No data"}'
                mock_generate.return_value = mock_response
                
                result = analyzer.analyze_reddit_post(post)
                
                # Metadata should include failure details
                assert "image_download_error" in result
                error_info = result["image_download_error"]
                assert error_info["type"] == "Timeout"
                assert "timed out" in error_info["message"].lower()
                assert error_info["url"] == post["url"]
                assert "timestamp" in error_info

    def test_metadata_tracks_retry_attempts(self, analyzer):
        """Test that metadata tracks number of retry attempts."""
        post = {
            "title": "Chart analysis",
            "subreddit": "Forex",
            "body": "",
            "url": "https://i.redd.it/analysis.png",
        }
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # Fail all attempts
            mock_get.side_effect = Timeout("Persistent timeout")
            
            with patch.object(analyzer.model, "generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = '{"sentiment": 0.0, "reasoning": "No data"}'
                mock_generate.return_value = mock_response
                
                with patch("news_sentiment.analyzer.gemini.time.sleep"):
                    result = analyzer.analyze_reddit_post(post)
                    
                    # Should track retry attempts in metadata
                    assert "image_download_error" in result
                    error_info = result["image_download_error"]
                    assert "retry_count" in error_info
                    assert error_info["retry_count"] == 3  # max_retries

    def test_metadata_differentiates_error_types(self, analyzer):
        """Test that metadata correctly identifies different error types."""
        test_cases = [
            (Timeout("Timeout"), "Timeout"),
            (ConnectionError("Connection failed"), "ConnectionError"),
            (HTTPError("404 Not Found"), "HTTPError"),
            (ValueError("Invalid image"), "ValueError"),
        ]
        
        for error, expected_type in test_cases:
            post = {
                "title": f"Test {expected_type}",
                "subreddit": "Test",
                "body": "",
                "url": f"https://example.com/{expected_type}.jpg",
            }
            
            with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
                if isinstance(error, HTTPError):
                    mock_response = Mock()
                    mock_response.raise_for_status.side_effect = error
                    mock_get.return_value = mock_response
                else:
                    mock_get.side_effect = error
                
                with patch.object(analyzer.model, "generate_content") as mock_generate:
                    mock_response = Mock()
                    mock_response.text = '{"sentiment": 0.0, "reasoning": "No data"}'
                    mock_generate.return_value = mock_response
                    
                    result = analyzer.analyze_reddit_post(post)
                    
                    assert "image_download_error" in result
                    assert result["image_download_error"]["type"] == expected_type


class TestLoggingAndMonitoring:
    """Test cases for logging output verification."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            return SentimentAnalyzer(api_key="test-key")

    def test_structured_logging_for_failures(self, analyzer, caplog):
        """Test that failures produce structured logs for monitoring."""
        url = "https://example.com/image.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = Timeout("Request timeout")
            
            with caplog.at_level(logging.WARNING):
                result = analyzer._download_image(url)
                
                # Verify structured log output
                assert len(caplog.records) > 0
                record = caplog.records[0]
                
                # Log should have proper level
                assert record.levelname == "WARNING"
                
                # Log should have structured fields
                assert hasattr(record, "url") or url in record.getMessage()
                assert hasattr(record, "error_type") or "Timeout" in record.getMessage()
                
                # Log message should be informative
                message = record.getMessage()
                assert url in message
                assert "timeout" in message.lower() or "Timeout" in message

    def test_success_logging_after_retry(self, analyzer, caplog):
        """Test that successful download after retry is logged properly."""
        url = "https://example.com/image.jpg"
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # Fail once, then succeed
            mock_response = Mock()
            mock_response.content = b"fake image"
            mock_response.raise_for_status.return_value = None
            
            mock_get.side_effect = [
                Timeout("First attempt failed"),
                mock_response
            ]
            
            with patch("news_sentiment.analyzer.gemini.Image.open") as mock_open:
                mock_image = Mock()
                mock_image.mode = "RGB"
                mock_open.return_value = mock_image
                
                with patch("news_sentiment.analyzer.gemini.time.sleep"):
                    with caplog.at_level(logging.INFO):
                        result = analyzer._download_image(url)
                        
                        # Should log retry and success
                        log_messages = [r.getMessage() for r in caplog.records]
                        
                        # Should have retry log
                        assert any("retry" in msg.lower() for msg in log_messages)
                        
                        # Should have success log
                        assert any("success" in msg.lower() or "downloaded" in msg.lower() 
                                 for msg in log_messages)
                        
                        # Success log should mention it was after retry
                        success_logs = [msg for msg in log_messages 
                                      if "success" in msg.lower() or "downloaded" in msg.lower()]
                        if success_logs:
                            assert any("retry" in log.lower() or "attempt" in log.lower() 
                                     for log in success_logs)

    def test_aggregate_failure_metrics_logging(self, analyzer, caplog):
        """Test that multiple failures are tracked for metrics."""
        urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg",
        ]
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            mock_get.side_effect = Timeout("All requests timeout")
            
            with caplog.at_level(logging.WARNING):
                for url in urls:
                    analyzer._download_image(url)
                
                # Should have logged each failure
                assert len(caplog.records) >= len(urls)
                
                # Each URL should appear in logs
                log_messages = [r.getMessage() for r in caplog.records]
                for url in urls:
                    assert any(url in msg for msg in log_messages)
                
                # Could aggregate these for metrics/monitoring
                timeout_count = sum(1 for msg in log_messages if "timeout" in msg.lower())
                assert timeout_count == len(urls)


class TestEndToEndFailureScenarios:
    """Integration tests for complete failure scenarios."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        from news_sentiment.analyzer import SentimentAnalyzer

        with patch("news_sentiment.analyzer.gemini.genai") as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            return SentimentAnalyzer(api_key="test-key")

    def test_reddit_image_post_with_network_failure(self, analyzer):
        """Test complete flow when Reddit image post has network failure."""
        post = {
            "title": "EUR/USD Daily Chart - Major Resistance Break",
            "subreddit": "Forex",
            "body": "",  # Empty body typical for image posts
            "url": "https://i.redd.it/eurusd_chart.png",
            "flair": "Technical Analysis"
        }
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # Simulate network failure
            mock_get.side_effect = ConnectionError("Network unreachable")
            
            with patch.object(analyzer.model, "generate_content") as mock_generate:
                # Gemini returns neutral due to lack of data
                mock_response = Mock()
                mock_response.text = '''{
                    "sentiment": 0.0,
                    "reasoning": "Unable to analyze sentiment without the image content. The post appears to be about EUR/USD technical analysis but without seeing the actual chart, no market sentiment can be determined."
                }'''
                mock_generate.return_value = mock_response
                
                with patch("news_sentiment.analyzer.gemini.logger") as mock_logger:
                    result = analyzer.analyze_reddit_post(post)
                    
                    # Should return neutral sentiment
                    assert result["sentiment_score"] == 0.0
                    
                    # Should indicate image analysis failed
                    assert result["analyzed_image"] is False
                    assert "image_download_failed" in result
                    assert result["image_download_failed"] is True
                    
                    # Should include failure metadata
                    assert "image_download_error" in result
                    assert result["image_download_error"]["type"] == "ConnectionError"
                    assert result["image_download_error"]["url"] == post["url"]
                    
                    # Should have logged the failure
                    mock_logger.warning.assert_called()
                    
                    # Reasoning should mention image unavailability
                    assert "image" in result["raw_response"]["reasoning"].lower()
                    assert any(word in result["raw_response"]["reasoning"].lower() 
                             for word in ["unable", "without", "no"])

    def test_bulk_image_failures_tracking(self, analyzer):
        """Test tracking multiple image failures for batch processing."""
        posts = [
            {
                "title": f"Chart {i}",
                "subreddit": "Forex",
                "body": "",
                "url": f"https://i.redd.it/chart{i}.jpg",
            }
            for i in range(5)
        ]
        
        failure_summary = {
            "total": 0,
            "timeout": 0,
            "connection": 0,
            "http_error": 0,
            "other": 0,
        }
        
        with patch("news_sentiment.analyzer.gemini.requests.get") as mock_get:
            # Mix of different failures
            errors = [
                Timeout("Timeout"),
                ConnectionError("Connection failed"),
                HTTPError("404 Not Found"),
                Timeout("Timeout 2"),
                ValueError("Invalid"),
            ]
            
            mock_get.side_effect = errors
            
            with patch.object(analyzer.model, "generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = '{"sentiment": 0.0, "reasoning": "No image"}'
                mock_generate.return_value = mock_response
                
                results = []
                for post in posts:
                    result = analyzer.analyze_reddit_post(post)
                    results.append(result)
                    
                    if "image_download_error" in result:
                        failure_summary["total"] += 1
                        error_type = result["image_download_error"]["type"]
                        
                        if error_type == "Timeout":
                            failure_summary["timeout"] += 1
                        elif error_type == "ConnectionError":
                            failure_summary["connection"] += 1
                        elif error_type == "HTTPError":
                            failure_summary["http_error"] += 1
                        else:
                            failure_summary["other"] += 1
                
                # Verify failure tracking
                assert failure_summary["total"] == 5
                assert failure_summary["timeout"] == 2
                assert failure_summary["connection"] == 1
                assert failure_summary["http_error"] == 1
                assert failure_summary["other"] == 1
                
                # All should have neutral sentiment due to missing images
                assert all(r["sentiment_score"] == 0.0 for r in results)
                assert all(r.get("image_download_failed") is True for r in results)