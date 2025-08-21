"""
Tests for the content extractor component.
"""

from unittest.mock import Mock, patch
from pathlib import Path

import pytest

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.content_extractor import ContentExtractor
from components.feed_processor import Article


@pytest.fixture
def mock_scraper():
    return Mock()

@pytest.fixture
def mock_summarizer():
    return Mock()

@pytest.fixture
def content_extractor(mock_scraper, mock_summarizer):
    return ContentExtractor(mock_scraper, mock_summarizer)


def test_extract_and_summarize_from_rss_content(content_extractor, mock_scraper, mock_summarizer):
    """Test extraction and summarization when full content is available in RSS."""
    article = Article(
        title="Test Article",
        url="http://example.com/test",
        published_date=None,
        feed_source="Test Feed",
        content="This is the full content from the RSS feed. It is long enough to be summarized."
    )

    mock_summarizer.summarize.return_value = "RSS content summary."

    summary = content_extractor.extract_and_summarize(article)

    assert summary == "RSS content summary."
    mock_scraper.extract_article_content.assert_not_called()  # Scraper should not be called
    mock_summarizer.summarize.assert_called_once_with(article.content)


def test_extract_and_summarize_from_rss_description(content_extractor, mock_scraper, mock_summarizer):
    """Test extraction and summarization when description is available in RSS."""
    article = Article(
        title="Test Article",
        url="http://example.com/test",
        published_date=None,
        feed_source="Test Feed",
        description="This is the description from the RSS feed. It is long enough to be summarized."
    )

    mock_summarizer.summarize.return_value = "RSS description summary."

    summary = content_extractor.extract_and_summarize(article)

    assert summary == "RSS description summary."
    mock_scraper.extract_article_content.assert_not_called()
    mock_summarizer.summarize.assert_called_once_with(article.description)


def test_extract_and_summarize_fallback_to_scraper(content_extractor, mock_scraper, mock_summarizer):
    """Test fallback to scraper when RSS content is insufficient."""
    article = Article(
        title="Test Article",
        url="http://example.com/test",
        published_date=None,
        feed_source="Test Feed",
        description="Short description."
    )

    mock_scraper.extract_article_content.return_value = ("Scraped full content.", "First paragraph")
    mock_summarizer.summarize.return_value = "Scraped content summary."

    summary = content_extractor.extract_and_summarize(article)

    assert summary == "Scraped content summary."
    mock_scraper.extract_article_content.assert_called_once_with(article.url)
    mock_summarizer.summarize.assert_called_once_with("Scraped full content.")


def test_extract_and_summarize_no_content_available(content_extractor, mock_scraper, mock_summarizer):
    """Test case where no content can be extracted."""
    article = Article(
        title="Test Article",
        url="http://example.com/test",
        published_date=None,
        feed_source="Test Feed",
        description="Short."
    )

    mock_scraper.extract_article_content.return_value = (None, None) # Scraper returns no content

    summary = content_extractor.extract_and_summarize(article)

    assert summary is None
    mock_scraper.extract_article_content.assert_called_once_with(article.url)
    mock_summarizer.summarize.assert_not_called()


def test_extract_and_summarize_scraper_error(content_extractor, mock_scraper, mock_summarizer):
    """Test error handling when scraper fails."""
    article = Article(
        title="Test Article",
        url="http://example.com/test",
        published_date=None,
        feed_source="Test Feed",
        description="Short."
    )

    mock_scraper.extract_article_content.side_effect = Exception("Scraper error")

    summary = content_extractor.extract_and_summarize(article)

    assert summary is None
    mock_scraper.extract_article_content.assert_called_once_with(article.url)
    mock_summarizer.summarize.assert_not_called()


def test_extract_and_summarize_summarizer_error(content_extractor, mock_scraper, mock_summarizer):
    """Test error handling when summarizer fails."""
    article = Article(
        title="Test Article",
        url="http://example.com/test",
        published_date=None,
        feed_source="Test Feed",
        content="Long enough content to summarize."
    )

    mock_summarizer.summarize.return_value = None # Summarizer returns None

    summary = content_extractor.extract_and_summarize(article)

    assert summary is None
    mock_summarizer.summarize.assert_called_once_with(article.content)
