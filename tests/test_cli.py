"""
Tests for CLI argument parsing and main entry point.

Following TDD: These tests are written FIRST before implementation.
"""

import argparse
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


class TestCLIArgumentParsing:
    """Test cases for CLI argument parsing."""

    def test_parser_creation(self):
        """Test that create_parser returns an ArgumentParser instance."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_description(self):
        """Test that parser has appropriate description."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        assert "News Sentiment" in parser.description
        assert "economic events" in parser.description.lower()

    def test_scrape_argument_choices(self):
        """Test --scrape argument accepts valid choices: today, week, month."""
        from news_sentiment.main import create_parser

        parser = create_parser()

        # Valid choices should work
        for choice in ["today", "week", "month"]:
            args = parser.parse_args(["--scrape", choice])
            assert args.scrape == choice

    def test_scrape_argument_invalid_choice(self):
        """Test --scrape argument rejects invalid choices."""
        from news_sentiment.main import create_parser

        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--scrape", "invalid"])

    def test_analyze_flag(self):
        """Test --analyze is a boolean flag."""
        from news_sentiment.main import create_parser

        parser = create_parser()

        # Without flag
        args = parser.parse_args([])
        assert args.analyze is False

        # With flag
        args = parser.parse_args(["--analyze"])
        assert args.analyze is True

    def test_test_run_flag(self):
        """Test --test-run is a boolean flag."""
        from news_sentiment.main import create_parser

        parser = create_parser()

        # Without flag
        args = parser.parse_args([])
        assert args.test_run is False

        # With flag
        args = parser.parse_args(["--test-run"])
        assert args.test_run is True

    def test_combined_arguments(self):
        """Test combining --scrape and --analyze."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--scrape", "week", "--analyze"])

        assert args.scrape == "week"
        assert args.analyze is True

    def test_all_arguments_combined(self):
        """Test all arguments can be used together."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--scrape", "today", "--analyze", "--test-run"])

        assert args.scrape == "today"
        assert args.analyze is True
        assert args.test_run is True

    def test_scrape_help_text(self):
        """Test --scrape has descriptive help text."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        help_output = StringIO()
        parser.print_help(help_output)
        help_text = help_output.getvalue()

        # Should mention scrape/scraping and period
        assert "--scrape" in help_text
        assert "today" in help_text.lower() or "week" in help_text.lower()

    def test_analyze_help_text(self):
        """Test --analyze has descriptive help text."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        help_output = StringIO()
        parser.print_help(help_output)
        help_text = help_output.getvalue()

        assert "--analyze" in help_text
        # Should mention analyzing/analysis and unscored/sentiment
        assert "analyz" in help_text.lower()

    def test_test_run_help_text(self):
        """Test --test-run has descriptive help text."""
        from news_sentiment.main import create_parser

        parser = create_parser()
        help_output = StringIO()
        parser.print_help(help_output)
        help_text = help_output.getvalue()

        assert "--test-run" in help_text
        # Should mention test/testing and database/commit
        assert "test" in help_text.lower()


class TestMainFunction:
    """Test cases for the main() function orchestration."""

    def test_main_no_arguments_shows_help(self, capsys):
        """Test that main() with no arguments shows help text."""
        from news_sentiment.main import main

        # Simulate no arguments
        with patch("sys.argv", ["news-sentiment"]):
            result = main()

        captured = capsys.readouterr()
        # Should print help when no action specified
        assert "--scrape" in captured.out or result == 0

    def test_main_returns_zero_on_success(self):
        """Test that main() returns 0 on successful execution."""
        from news_sentiment.main import main

        with patch("sys.argv", ["news-sentiment", "--scrape", "today", "--test-run"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.scrape_events", return_value=[]):
                    result = main()

        assert result == 0

    def test_main_scrape_calls_scrape_events(self):
        """Test that --scrape triggers scrape_events()."""
        from news_sentiment.main import main

        mock_scrape = MagicMock(return_value=[])

        with patch("sys.argv", ["news-sentiment", "--scrape", "week", "--test-run"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.scrape_events", mock_scrape):
                    main()

        mock_scrape.assert_called_once()
        # Verify period argument is passed
        call_args = mock_scrape.call_args
        assert call_args is not None

    def test_main_scrape_today_passes_correct_period(self):
        """Test that --scrape today passes period='today' to scrape_events."""
        from news_sentiment.main import main

        mock_scrape = MagicMock(return_value=[])

        with patch("sys.argv", ["news-sentiment", "--scrape", "today", "--test-run"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.scrape_events", mock_scrape):
                    main()

        # Check that period='today' was passed
        call_kwargs = mock_scrape.call_args
        # Either positional or keyword argument
        assert "today" in str(call_kwargs)

    def test_main_scrape_without_test_run_calls_store_events(self):
        """Test that --scrape without --test-run calls store_events()."""
        from news_sentiment.main import main

        mock_scrape = MagicMock(return_value=[{"event": "test"}])
        mock_store = MagicMock(return_value=1)

        with patch("sys.argv", ["news-sentiment", "--scrape", "week"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.scrape_events", mock_scrape):
                    with patch("news_sentiment.main.store_events", mock_store):
                        main()

        mock_store.assert_called_once()

    def test_main_scrape_with_test_run_skips_store_events(self):
        """Test that --scrape --test-run does NOT call store_events()."""
        from news_sentiment.main import main

        mock_scrape = MagicMock(return_value=[{"event": "test"}])
        mock_store = MagicMock(return_value=1)

        with patch("sys.argv", ["news-sentiment", "--scrape", "week", "--test-run"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.scrape_events", mock_scrape):
                    with patch("news_sentiment.main.store_events", mock_store):
                        main()

        mock_store.assert_not_called()

    def test_main_analyze_calls_analyze_events(self):
        """Test that --analyze triggers analyze_events()."""
        from news_sentiment.main import main

        mock_analyze = MagicMock(return_value=0)

        with patch("sys.argv", ["news-sentiment", "--analyze"]):
            with patch("news_sentiment.main.SentimentAnalyzer"):
                with patch("news_sentiment.main.analyze_events", mock_analyze):
                    main()

        mock_analyze.assert_called_once()

    def test_main_analyze_with_test_run_passes_flag(self):
        """Test that --analyze --test-run passes test_run=True."""
        from news_sentiment.main import main

        mock_analyze = MagicMock(return_value=0)

        with patch("sys.argv", ["news-sentiment", "--analyze", "--test-run"]):
            with patch("news_sentiment.main.SentimentAnalyzer"):
                with patch("news_sentiment.main.analyze_events", mock_analyze):
                    main()

        # Verify test_run=True was passed
        call_kwargs = mock_analyze.call_args
        assert call_kwargs is not None
        # Check for test_run=True in call
        assert call_kwargs.kwargs.get("test_run") is True

    def test_main_combined_scrape_and_analyze(self):
        """Test that --scrape and --analyze both execute."""
        from news_sentiment.main import main

        mock_scrape = MagicMock(return_value=[{"event": "test"}])
        mock_store = MagicMock(return_value=1)
        mock_analyze = MagicMock(return_value=1)

        with patch("sys.argv", ["news-sentiment", "--scrape", "today", "--analyze"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.SentimentAnalyzer"):
                    with patch("news_sentiment.main.scrape_events", mock_scrape):
                        with patch("news_sentiment.main.store_events", mock_store):
                            with patch(
                                "news_sentiment.main.analyze_events", mock_analyze
                            ):
                                main()

        mock_scrape.assert_called_once()
        mock_store.assert_called_once()
        mock_analyze.assert_called_once()

    def test_main_prints_progress_messages(self, capsys):
        """Test that main() prints progress messages during execution."""
        from news_sentiment.main import main

        mock_scrape = MagicMock(return_value=[{"event": "test"}])
        mock_store = MagicMock(return_value=1)

        with patch("sys.argv", ["news-sentiment", "--scrape", "week"]):
            with patch("news_sentiment.main.ForexFactoryScraper"):
                with patch("news_sentiment.main.scrape_events", mock_scrape):
                    with patch("news_sentiment.main.store_events", mock_store):
                        main()

        captured = capsys.readouterr()
        # Should print some progress indication
        output = captured.out.lower()
        assert "scrap" in output or "event" in output or "complet" in output


class TestEntryPoint:
    """Test cases for the module entry point."""

    def test_module_has_main_function(self):
        """Test that main() function is importable."""
        from news_sentiment.main import main

        assert callable(main)

    def test_module_can_be_run_as_script(self):
        """Test that the module can be executed as a script."""
        # This tests the if __name__ == "__main__" block
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "news_sentiment.main", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/dixter/Projects/news-sentiment/src",
        )
        # --help should exit with code 0
        assert result.returncode == 0
        assert "--scrape" in result.stdout
