"""
Tests for reprocessing script for failed image posts.

This module follows TDD principles - tests are written to define expected
behavior for the reprocessing script that will fix posts with failed image
downloads.
"""

import argparse
import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, call
import pytest
from sqlalchemy.orm import Session

from news_sentiment.database.models import RedditPost


class TestReprocessingScriptDatabaseQuery:
    """Test cases for database querying and filtering."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def sample_failed_posts(self):
        """Create sample posts with failed image analysis."""
        posts = []
        
        # Posts with "no information" patterns
        for i, pattern in enumerate([
            "no information provided",
            "impossible to determine",
            "no information available",
            "completely missing data",
            "post content is inaccessible"
        ]):
            post = Mock(spec=RedditPost)
            post.id = i + 1
            post.reddit_id = f"failed_{i}"
            post.title = f"EUR/USD Chart {i}"
            post.url = f"https://i.redd.it/chart{i}.jpg"
            post.sentiment_score = 0.0
            post.raw_response = {
                "reasoning": f"With {pattern} about the event, it is impossible to determine sentiment",
                "sentiment": 0.0
            }
            posts.append(post)
        
        # Post with 0.0 score but valid reasoning (should be filtered out)
        valid_post = Mock(spec=RedditPost)
        valid_post.id = 100
        valid_post.reddit_id = "valid_neutral"
        valid_post.title = "Neutral news"
        valid_post.sentiment_score = 0.0
        valid_post.raw_response = {
            "reasoning": "The news is neutral with no clear market impact",
            "sentiment": 0.0
        }
        posts.append(valid_post)
        
        return posts

    def test_query_posts_with_zero_sentiment(self, mock_session, sample_failed_posts):
        """Test that script queries all posts with sentiment_score = 0.0."""
        from scripts.reprocess_failed_images import get_failed_posts
        
        mock_session.query.return_value.filter.return_value.all.return_value = sample_failed_posts
        
        posts = get_failed_posts(mock_session)
        
        # Should query for sentiment_score = 0.0
        mock_session.query.assert_called_once_with(RedditPost)
        filter_call = mock_session.query.return_value.filter
        
        # Check that the filter condition checks for 0.0
        # The actual implementation will use: RedditPost.sentiment_score == 0.0
        assert filter_call.called
        
        # Should return all posts with 0.0 score
        assert len(posts) == len(sample_failed_posts)

    def test_filter_posts_with_no_information_patterns(self, sample_failed_posts):
        """Test filtering posts that match 'no information' patterns."""
        from scripts.reprocess_failed_images import filter_no_information_posts
        
        filtered = filter_no_information_posts(sample_failed_posts)
        
        # Should filter out the valid neutral post
        assert len(filtered) == 5  # Only the posts with "no information" patterns
        
        # All filtered posts should have problematic reasoning
        for post in filtered:
            reasoning = post.raw_response.get("reasoning", "").lower()
            assert any(pattern in reasoning for pattern in [
                "no information provided",
                "impossible to determine", 
                "no information available",
                "completely missing data",
                "post content is inaccessible"
            ])

    def test_identify_image_posts(self, sample_failed_posts):
        """Test identifying posts that have image URLs."""
        from scripts.reprocess_failed_images import is_image_post
        
        # Posts with image URLs should be identified
        for post in sample_failed_posts[:5]:
            assert is_image_post(post) is True
        
        # Test non-image URL
        text_post = Mock(spec=RedditPost)
        text_post.url = "https://reddit.com/r/forex/comments/abc123"
        assert is_image_post(text_post) is False
        
        # Test None URL
        no_url_post = Mock(spec=RedditPost)
        no_url_post.url = None
        assert is_image_post(no_url_post) is False


class TestReprocessingLogic:
    """Test cases for the reprocessing logic."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock sentiment analyzer."""
        analyzer = MagicMock()
        return analyzer

    @pytest.fixture
    def failed_post(self):
        """Create a sample failed post."""
        post = Mock(spec=RedditPost)
        post.id = 1
        post.reddit_id = "test123"
        post.title = "EUR/USD Technical Analysis"
        post.subreddit = "Forex"
        post.body = ""
        post.url = "https://i.redd.it/chart.jpg"
        post.sentiment_score = 0.0
        post.raw_response = {
            "reasoning": "With no information provided about the event, it is impossible to determine sentiment",
            "sentiment": 0.0
        }
        # Add to_dict_for_gemini method
        post.to_dict_for_gemini = Mock(return_value={
            "title": post.title,
            "subreddit": post.subreddit,
            "body": post.body,
            "url": post.url,
            "flair": None,
            "score": None,
            "num_comments": None
        })
        return post

    def test_reprocess_single_post_success(self, mock_analyzer, failed_post, mock_session):
        """Test successfully reprocessing a single post."""
        from scripts.reprocess_failed_images import reprocess_post
        
        # Mock successful reanalysis
        mock_analyzer.analyze_reddit_post.return_value = {
            "sentiment_score": 0.65,
            "raw_response": {
                "reasoning": "The chart shows bullish breakout pattern",
                "sentiment": 0.65
            },
            "analyzed_image": True
        }
        
        success = reprocess_post(failed_post, mock_analyzer, mock_session)
        
        # Should call analyzer with post data
        mock_analyzer.analyze_reddit_post.assert_called_once()
        call_args = mock_analyzer.analyze_reddit_post.call_args
        assert call_args[0][0]["title"] == failed_post.title
        assert call_args[0][0]["url"] == failed_post.url
        
        # Should update the post
        assert failed_post.sentiment_score == 0.65
        assert failed_post.raw_response["reasoning"] == "The chart shows bullish breakout pattern"
        
        # Should commit the changes
        mock_session.commit.assert_called_once()
        
        assert success is True

    def test_reprocess_post_still_fails(self, mock_analyzer, failed_post, mock_session):
        """Test when reprocessing still results in failure."""
        from scripts.reprocess_failed_images import reprocess_post
        
        # Mock continued failure
        mock_analyzer.analyze_reddit_post.return_value = {
            "sentiment_score": 0.0,
            "raw_response": {
                "reasoning": "Image download failed again",
                "sentiment": 0.0
            },
            "analyzed_image": False,
            "image_download_failed": True
        }
        
        success = reprocess_post(failed_post, mock_analyzer, mock_session)
        
        # Should not update if still 0.0
        mock_session.commit.assert_not_called()
        
        assert success is False

    def test_reprocess_post_exception_handling(self, mock_analyzer, failed_post, mock_session):
        """Test handling exceptions during reprocessing."""
        from scripts.reprocess_failed_images import reprocess_post
        
        # Mock analyzer throwing exception
        mock_analyzer.analyze_reddit_post.side_effect = Exception("API error")
        
        success = reprocess_post(failed_post, mock_analyzer, mock_session)
        
        # Should handle exception gracefully
        assert success is False
        
        # Should not commit on error
        mock_session.commit.assert_not_called()


class TestBatchProcessing:
    """Test cases for batch processing functionality."""

    @pytest.fixture
    def batch_of_posts(self):
        """Create a batch of posts for testing."""
        posts = []
        for i in range(25):  # Create 25 posts
            post = Mock(spec=RedditPost)
            post.id = i + 1
            post.reddit_id = f"batch_{i}"
            post.title = f"Post {i}"
            post.url = f"https://i.redd.it/img{i}.jpg"
            post.sentiment_score = 0.0
            post.raw_response = {
                "reasoning": "No information available to determine sentiment",
                "sentiment": 0.0
            }
            posts.append(post)
        return posts

    def test_batch_processing_with_size_limit(self, batch_of_posts):
        """Test processing posts in batches with specified size."""
        from scripts.reprocess_failed_images import process_in_batches
        
        processed = []
        batch_sizes = []
        
        def mock_processor(batch):
            processed.extend(batch)
            batch_sizes.append(len(batch))
            return len(batch)  # Return count of processed
        
        total = process_in_batches(batch_of_posts, mock_processor, batch_size=10)
        
        # Should process in batches of 10
        assert batch_sizes == [10, 10, 5]
        
        # Should process all posts
        assert len(processed) == 25
        assert total == 25

    def test_batch_processing_with_total_limit(self, batch_of_posts):
        """Test limiting total number of posts processed."""
        from scripts.reprocess_failed_images import process_in_batches
        
        processed = []
        
        def mock_processor(batch):
            processed.extend(batch)
            return len(batch)
        
        total = process_in_batches(
            batch_of_posts, 
            mock_processor, 
            batch_size=10,
            limit=15
        )
        
        # Should only process up to limit
        assert len(processed) == 15
        assert total == 15


class TestDryRunMode:
    """Test cases for dry-run mode."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def failed_posts(self):
        """Create sample failed posts."""
        posts = []
        for i in range(5):
            post = Mock(spec=RedditPost)
            post.id = i + 1
            post.reddit_id = f"dry_run_{i}"
            post.title = f"Chart {i}"
            post.url = f"https://i.redd.it/chart{i}.jpg"
            post.sentiment_score = 0.0
            post.raw_response = {
                "reasoning": "Post content is inaccessible",
                "sentiment": 0.0
            }
            posts.append(post)
        return posts

    def test_dry_run_does_not_modify_database(self, failed_posts, mock_session):
        """Test that dry-run mode doesn't modify the database."""
        from scripts.reprocess_failed_images import run_reprocessing
        
        with patch("scripts.reprocess_failed_images.get_failed_posts") as mock_get:
            mock_get.return_value = failed_posts
            
            with patch("scripts.reprocess_failed_images.SentimentAnalyzer") as mock_analyzer_class:
                mock_analyzer = MagicMock()
                mock_analyzer_class.return_value = mock_analyzer
                
                stats = run_reprocessing(
                    mock_session,
                    dry_run=True,
                    batch_size=10,
                    limit=None
                )
        
        # Should not call analyzer in dry-run mode
        mock_analyzer.analyze_reddit_post.assert_not_called()
        
        # Should not commit anything
        mock_session.commit.assert_not_called()
        
        # Should return preview statistics
        assert stats["total_found"] == 5
        assert stats["would_process"] == 5
        assert stats["processed"] == 0

    def test_dry_run_output_format(self, failed_posts, capsys):
        """Test that dry-run mode produces informative output."""
        from scripts.reprocess_failed_images import print_dry_run_preview
        
        print_dry_run_preview(failed_posts)
        
        captured = capsys.readouterr()
        
        # Should show preview of what would be processed
        assert "DRY RUN MODE" in captured.out
        assert "Would process 5 posts" in captured.out
        
        # Should list some example posts
        for post in failed_posts[:3]:  # First 3 as examples
            assert post.reddit_id in captured.out
            assert post.title in captured.out


class TestProgressTracking:
    """Test cases for progress tracking and reporting."""

    def test_progress_bar_display(self, capsys):
        """Test that progress bar is displayed during processing."""
        from scripts.reprocess_failed_images import ProgressTracker
        
        tracker = ProgressTracker(total=10)
        
        for i in range(10):
            tracker.update(success=i % 2 == 0)  # Alternate success/failure
        
        tracker.finish()
        
        # Check statistics
        assert tracker.stats["total"] == 10
        assert tracker.stats["successful"] == 5
        assert tracker.stats["failed"] == 5
        assert tracker.stats["success_rate"] == 50.0

    def test_detailed_logging(self, tmp_path):
        """Test detailed logging to file."""
        from scripts.reprocess_failed_images import setup_logging
        
        log_file = tmp_path / "reprocess.log"
        logger = setup_logging(str(log_file))
        
        # Log some test messages
        logger.info("Starting reprocessing")
        logger.error("Failed to process post_123")
        logger.info("Successfully processed post_456")
        
        # Check log file contents
        log_contents = log_file.read_text()
        assert "Starting reprocessing" in log_contents
        assert "Failed to process post_123" in log_contents
        assert "Successfully processed post_456" in log_contents

    def test_final_statistics_report(self, capsys):
        """Test that final statistics are printed."""
        from scripts.reprocess_failed_images import print_statistics
        
        stats = {
            "total_found": 100,
            "filtered": 80,
            "processed": 75,
            "successful": 60,
            "failed": 15,
            "skipped": 5,
            "success_rate": 80.0,
            "duration_seconds": 120.5
        }
        
        print_statistics(stats)
        
        captured = capsys.readouterr()
        
        # Should display all key statistics
        assert "Total posts found: 100" in captured.out
        assert "Posts matching filter: 80" in captured.out
        assert "Posts processed: 75" in captured.out
        assert "Successful: 60" in captured.out
        assert "Failed: 15" in captured.out
        assert "Success rate: 80.0%" in captured.out
        assert "Duration: 2m 0.5s" in captured.out or "Duration: 120.5" in captured.out


class TestCommandLineInterface:
    """Test cases for CLI argument parsing."""

    def test_cli_argument_parsing(self):
        """Test parsing command-line arguments."""
        from scripts.reprocess_failed_images import parse_arguments
        
        # Test with all arguments
        args = parse_arguments([
            "--dry-run",
            "--batch-size", "20",
            "--limit", "100",
            "--log-file", "/tmp/test.log"
        ])
        
        assert args.dry_run is True
        assert args.batch_size == 20
        assert args.limit == 100
        assert args.log_file == "/tmp/test.log"
        
        # Test defaults
        args = parse_arguments([])
        assert args.dry_run is False
        assert args.batch_size == 10
        assert args.limit is None
        assert args.log_file is not None  # Should have default

    def test_cli_help_text(self, capsys):
        """Test that help text is informative."""
        from scripts.reprocess_failed_images import parse_arguments
        
        with pytest.raises(SystemExit):
            parse_arguments(["--help"])
        
        captured = capsys.readouterr()
        
        # Should explain what the script does
        assert "Reprocess Reddit posts" in captured.out or "reprocess" in captured.out.lower()
        assert "failed image" in captured.out.lower()
        
        # Should document all options
        assert "--dry-run" in captured.out
        assert "--batch-size" in captured.out
        assert "--limit" in captured.out
        assert "--log-file" in captured.out


class TestIntegrationScenarios:
    """Integration tests for complete reprocessing scenarios."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    def test_full_reprocessing_workflow(self, mock_session):
        """Test the complete reprocessing workflow."""
        from scripts.reprocess_failed_images import main
        
        # Create test posts
        failed_posts = []
        for i in range(3):
            post = Mock(spec=RedditPost)
            post.id = i + 1
            post.reddit_id = f"full_test_{i}"
            post.title = f"Test {i}"
            post.url = f"https://i.redd.it/test{i}.jpg"
            post.sentiment_score = 0.0
            post.raw_response = {
                "reasoning": "No information provided",
                "sentiment": 0.0
            }
            # Add to_dict method for compatibility
            post.to_dict_for_gemini = Mock(return_value={
                "title": post.title,
                "url": post.url,
                "subreddit": "test",
                "body": ""
            })
            failed_posts.append(post)
        
        mock_session.query.return_value.filter.return_value.all.return_value = failed_posts
        
        with patch("scripts.reprocess_failed_images.SentimentAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            # Mock successful reanalysis for 2 posts, failure for 1
            mock_analyzer.analyze_reddit_post.side_effect = [
                {
                    "sentiment_score": 0.5,
                    "raw_response": {"reasoning": "Bullish", "sentiment": 0.5},
                    "analyzed_image": True
                },
                {
                    "sentiment_score": 0.0,
                    "raw_response": {"reasoning": "Still failed", "sentiment": 0.0},
                    "analyzed_image": False
                },
                {
                    "sentiment_score": -0.3,
                    "raw_response": {"reasoning": "Bearish", "sentiment": -0.3},
                    "analyzed_image": True
                }
            ]
            
            # Run with test arguments
            with patch("sys.argv", ["reprocess_failed_images.py", "--limit", "3"]):
                with patch("scripts.reprocess_failed_images.get_session") as mock_get_session:
                    mock_get_session.return_value.__enter__.return_value = mock_session
                    
                    result = main()
        
        # Should process all 3 posts
        assert mock_analyzer.analyze_reddit_post.call_count == 3
        
        # Should commit successful updates
        assert mock_session.commit.call_count >= 2  # 2 successful reprocesses
        
        # Should return success
        assert result == 0

    def test_reprocessing_with_api_failures(self, mock_session):
        """Test handling API failures during reprocessing."""
        from scripts.reprocess_failed_images import run_reprocessing
        
        failed_post = Mock(spec=RedditPost)
        failed_post.id = 1
        failed_post.reddit_id = "api_fail"
        failed_post.title = "Test"
        failed_post.url = "https://i.redd.it/test.jpg"
        failed_post.sentiment_score = 0.0
        failed_post.raw_response = {"reasoning": "No information provided to analyze", "sentiment": 0.0}
        failed_post.to_dict_for_gemini = Mock(return_value={"title": "Test", "url": failed_post.url})
        
        with patch("scripts.reprocess_failed_images.get_failed_posts") as mock_get:
            mock_get.return_value = [failed_post]
            
            with patch("scripts.reprocess_failed_images.SentimentAnalyzer") as mock_analyzer_class:
                mock_analyzer = MagicMock()
                mock_analyzer_class.return_value = mock_analyzer
                
                # Mock API failure
                mock_analyzer.analyze_reddit_post.side_effect = Exception("API quota exceeded")
                
                stats = run_reprocessing(mock_session)
        
        # Should handle the error gracefully
        assert stats["processed"] == 1
        assert stats["failed"] == 1
        assert stats["successful"] == 0
        
        # Should not crash
        assert "error" not in stats or stats.get("error") is None