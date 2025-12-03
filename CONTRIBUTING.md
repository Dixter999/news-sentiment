# Contributing to News Sentiment Analysis

Thank you for your interest in contributing to the News Sentiment Analysis project! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- Google Gemini API key
- Reddit API credentials (optional)

### Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/news-sentiment.git
cd news-sentiment
```

2. **Set up development environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Start development database**
```bash
docker compose up -d db
python -m news_sentiment.database.init_db
```

5. **Verify setup**
```bash
# Run tests
python -m pytest

# Start monitor
python -m news_sentiment.eurusd_monitor --test
```

## 🔄 Development Workflow

### Branch Strategy

- **`main`** - Production-ready code
- **`develop`** - Integration branch for features
- **`feature/issue-number-description`** - Feature branches
- **`hotfix/issue-number-description`** - Critical fixes

### Workflow Steps

1. **Create a feature branch**
```bash
git checkout -b feature/123-add-new-sentiment-source
```

2. **Make your changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
```bash
# Run all tests
python -m pytest

# Run linting
black src/ tests/
ruff check src/ tests/

# Test Docker build
docker compose build
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add Twitter sentiment analysis support

- Add TwitterScraper class with rate limiting
- Integrate Twitter data into EUR/USD monitor
- Add tests for tweet sentiment analysis
- Update documentation

Resolves #123"
```

5. **Push and create Pull Request**
```bash
git push origin feature/123-add-new-sentiment-source
# Create PR through GitHub UI
```

## 📝 Coding Standards

### Python Style

We follow **Black** formatting and **PEP 8** standards:

```bash
# Format code
black src/ tests/

# Check style
ruff check src/ tests/

# Type checking (optional but recommended)
mypy src/
```

### Code Quality Guidelines

- **Functions should be single-purpose and well-documented**
- **Use type hints for all function parameters and returns**
- **Keep functions under 50 lines when possible**
- **Use descriptive variable and function names**
- **Add docstrings for all public functions and classes**

#### Example Function
```python
def analyze_sentiment(
    text: str,
    model_name: str = "gemini-2.0-flash",
    timeout: int = 30
) -> Dict[str, float]:
    """Analyze sentiment of given text using AI model.
    
    Args:
        text: Text content to analyze
        model_name: AI model identifier to use
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with sentiment scores and confidence metrics
        
    Raises:
        ValueError: If text is empty or model_name is invalid
        APIError: If sentiment analysis request fails
    """
    if not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Implementation here...
    return {"sentiment": 0.5, "confidence": 0.8}
```

### Database Guidelines

- **Use SQLAlchemy models for all database operations**
- **Add database migrations for schema changes**
- **Include proper indexes for performance**
- **Use transactions for multi-table operations**

### API Integration Guidelines

- **Implement retry logic with exponential backoff**
- **Respect rate limits for external APIs**
- **Log API errors with appropriate detail levels**
- **Handle API failures gracefully**

## 🧪 Testing

### Test Requirements

All contributions must include appropriate tests:

- **Unit tests** for individual functions
- **Integration tests** for API interactions
- **End-to-end tests** for complete workflows
- **Mock external APIs** in tests when possible

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/news_sentiment --cov-report=html

# Run specific test categories
python -m pytest tests/test_analyzer.py
python -m pytest tests/test_scraper.py -v
python -m pytest -k "test_reddit" --tb=short
```

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from news_sentiment.analyzer.gemini import SentimentAnalyzer

class TestSentimentAnalyzer:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.analyzer = SentimentAnalyzer(api_key="test_key")
    
    def test_analyze_positive_sentiment(self):
        """Test sentiment analysis returns positive score for bullish text."""
        # Arrange
        text = "Markets are rallying strongly, great outlook"
        
        # Act
        result = self.analyzer.analyze_text(text)
        
        # Assert
        assert result["sentiment"] > 0.5
        assert "bullish" in result["reasoning"].lower()
    
    @patch('requests.post')
    def test_api_failure_handling(self, mock_post):
        """Test graceful handling of API failures."""
        # Arrange
        mock_post.side_effect = ConnectionError("API unavailable")
        
        # Act & Assert
        with pytest.raises(APIError):
            self.analyzer.analyze_text("test text")
```

## 📤 Submitting Changes

### Pull Request Guidelines

1. **Fill out the PR template completely**
2. **Link related issues with "Closes #123" or "Resolves #123"**
3. **Include screenshots for UI changes**
4. **Add reviewer suggestions**
5. **Ensure CI passes all checks**

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added for new functionality
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Linked to relevant issues

### Commit Message Format

Use conventional commits format:

```
type(scope): brief description

Longer description explaining what changed and why.

- List specific changes
- Include breaking changes
- Reference issues

Closes #123
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Docker version)
- **Error logs** and stack traces
- **Configuration files** (redacted of sensitive data)

Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

### Performance Issues

For performance problems, include:

- **Specific scenarios** where performance degrades
- **Performance metrics** (response times, memory usage)
- **System resources** during the issue
- **Dataset size** being processed

## 💡 Feature Requests

We welcome feature suggestions! Please:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** you're trying to solve
3. **Explain your proposed solution**
4. **Consider alternatives** you've evaluated
5. **Estimate implementation complexity**

Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

## 🏗️ Architecture Guidelines

### Adding New Data Sources

When adding new data sources:

1. **Create scraper class** in `src/news_sentiment/scraper/`
2. **Implement rate limiting** and error handling
3. **Add data validation** and normalization
4. **Create database models** if needed
5. **Add integration tests** with mocked APIs
6. **Update monitor** to include new source

### Extending Sentiment Analysis

For new analysis capabilities:

1. **Extend `SentimentAnalyzer` class**
2. **Add prompt templates** for new content types
3. **Implement result validation**
4. **Add comprehensive testing**
5. **Document API usage** and costs

### Performance Considerations

- **Database queries** - Use proper indexing and query optimization
- **API calls** - Implement caching and rate limiting
- **Memory usage** - Process large datasets in chunks
- **Concurrent operations** - Use async/await patterns where beneficial

## 🔒 Security Considerations

- **Never commit API keys** or secrets
- **Validate all inputs** from external APIs
- **Use environment variables** for configuration
- **Implement proper error handling** that doesn't leak sensitive information
- **Follow security best practices** for database access

## 📚 Documentation

When making changes, update relevant documentation:

- **README.md** - For user-facing changes
- **CHANGELOG.md** - For all notable changes
- **API documentation** - For new endpoints or functions
- **Architecture docs** - For structural changes

## ❓ Getting Help

- **GitHub Discussions** - General questions and community support
- **GitHub Issues** - Bug reports and feature requests
- **Code Review** - Request feedback on your changes

## 🏆 Recognition

Contributors are recognized in our:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub Contributors** page

Thank you for contributing to make financial sentiment analysis more accessible and accurate! 🚀