"""
Tests for the RSS feed processor component.
"""

import json
import tempfile
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.feed_processor import (
    RSSFeedProcessor, 
    Article, 
    FeedResult, 
    process_rss_feeds
)


class TestArticle:
    """Test cases for Article dataclass."""
    
    def test_article_creation(self):
        """Test creating an Article instance."""
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            published_date=datetime(2023, 1, 1, 12, 0),
            feed_source="Test Feed",
            description="Test description",
            author="Test Author",
            content="Full article content",
            summary="Article summary",
            summary_generated=True
        )
        
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.feed_source == "Test Feed"
        assert article.description == "Test description"
        assert article.author == "Test Author"
        assert article.content == "Full article content"
        assert article.summary == "Article summary"
        assert article.summary_generated is True
    
    def test_article_optional_fields(self):
        """Test creating an Article with minimal required fields."""
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            published_date=None,
            feed_source="Test Feed"
        )
        
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.published_date is None
        assert article.description is None
        assert article.author is None
        assert article.content is None
        assert article.summary is None
        assert article.summary_generated is False


class TestFeedResult:
    """Test cases for FeedResult dataclass."""
    
    def test_feed_result_creation(self):
        """Test creating a FeedResult instance."""
        result = FeedResult(
            feed_url="https://example.com/feed",
            success=True,
            articles=[],
            processing_time=1.5
        )
        
        assert result.feed_url == "https://example.com/feed"
        assert result.success is True
        assert result.articles == []
        assert result.processing_time == 1.5
        assert result.error_message is None
    
    def test_feed_result_with_error(self):
        """Test creating a FeedResult with error information."""
        result = FeedResult(
            feed_url="https://example.com/feed",
            success=False,
            articles=[],
            error_message="Connection failed",
            processing_time=0.5
        )
        
        assert result.success is False
        assert result.error_message == "Connection failed"


class TestRSSFeedProcessor:
    """Test cases for RSSFeedProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = RSSFeedProcessor(max_workers=2, timeout=10)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.processor.close()
    
    def test_processor_initialization(self):
        """Test RSSFeedProcessor initialization."""
        assert self.processor.max_workers == 2
        assert self.processor.timeout == 10
        assert self.processor.session is not None
    
    def test_valid_url_validation(self):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "https://example.com/feed",
            "http://example.com/feed",
            "https://feeds.bbci.co.uk/news/rss.xml"
        ]
        
        for url in valid_urls:
            assert self.processor._is_valid_url(url) is True
    
    def test_invalid_url_validation(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com/feed",
            "example.com/feed",
            "",
            None
        ]
        
        for url in invalid_urls:
            assert self.processor._is_valid_url(url) is False
    
    def test_process_single_feed_success(self):
        """Test successful processing of a single RSS feed."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.content = b'<rss><channel><title>Test Feed</title><item><title>Test Article</title><link>https://example.com/article</link></item></channel></rss>'
        mock_response.raise_for_status.return_value = None
        
        # Mock the session to return our mock response
        self.processor.session = Mock()
        self.processor.session.get.return_value = mock_response
        
        # Mock feedparser to return valid data
        with patch('components.feed_processor.feedparser.parse') as mock_parse:
            mock_feed_data = Mock()
            mock_feed_data.bozo = False
            mock_feed_data.feed = {'title': 'Test Feed'}
            
            # Create a proper mock entry that handles both .get() and 'in' operations
            mock_entry = Mock()
            entry_data = {
                'title': 'Test Article',
                'link': 'https://example.com/article',
                'published_parsed': None,
                'summary': 'Test description'
            }
            
            # Mock the .get() method
            mock_entry.get.side_effect = lambda key, default=None: entry_data.get(key, default)
            
            # Mock the 'in' operator by implementing __contains__
            mock_entry.__contains__ = lambda self, key: key in entry_data
            
            # Mock attribute access for direct properties
            mock_entry.title = 'Test Article'
            mock_entry.link = 'https://example.com/article'
            mock_entry.published_parsed = None
            mock_entry.summary = 'Test description'
            
            mock_feed_data.entries = [mock_entry]
            mock_parse.return_value = mock_feed_data
            
            result = self.processor._process_single_feed("https://example.com/feed")
            
            assert result.success is True
            assert len(result.articles) == 1
            assert result.articles[0].title == "Test Article"
            assert result.articles[0].url == "https://example.com/article"
            assert result.articles[0].feed_source == "Test Feed"
    
    def test_process_single_feed_http_error(self):
        """Test handling of HTTP errors when processing a feed."""
        # Mock the session to return our mock response
        self.processor.session = Mock()
        self.processor.session.get.side_effect = Exception("Connection failed")
        
        result = self.processor._process_single_feed("https://example.com/feed")
        
        assert result.success is False
        assert "Connection failed" in result.error_message
    
    def test_process_single_feed_invalid_url(self):
        """Test processing a feed with invalid URL."""
        result = self.processor._process_single_feed("not-a-valid-url")
        
        assert result.success is False
        assert result.error_message == "Invalid URL format"
    
    def test_process_single_feed_parsing_error(self):
        """Test handling of RSS parsing errors."""
        mock_response = Mock()
        mock_response.content = b'invalid xml content'
        mock_response.raise_for_status.return_value = None
        
        # Mock the session to return our mock response
        self.processor.session = Mock()
        self.processor.session.get.return_value = mock_response
        
        with patch('components.feed_processor.feedparser.parse') as mock_parse:
            mock_feed_data = Mock()
            mock_feed_data.bozo = True
            mock_feed_data.bozo_exception = "XML parsing error"
            mock_parse.return_value = mock_feed_data
            
            result = self.processor._process_single_feed("https://example.com/feed")
            
            assert result.success is False
            assert "RSS parsing failed" in result.error_message
    
    def test_extract_articles(self):
        """Test article extraction from parsed RSS data."""
        # Create a simple test that doesn't require complex mocking
        # We'll test the core logic with a simplified approach
        
        # Create a simple mock feed data
        mock_feed_data = Mock()
        mock_feed_data.feed = {'title': 'Test Feed'}
        
        # Create a simple mock entry that works
        mock_entry1 = Mock()
        mock_entry1.get.side_effect = lambda key, default=None: {
            'title': 'Article 1',
            'link': 'https://example.com/article1',
            'summary': 'Description 1',
            'author': 'Author 1'
        }.get(key, default)
        mock_entry1.__contains__ = lambda self, key: key in ['title', 'link', 'summary', 'author', 'published_parsed']
        mock_entry1.title = 'Article 1'
        mock_entry1.link = 'https://example.com/article1'
        mock_entry1.summary = 'Description 1'
        mock_entry1.author = 'Author 1'
        mock_entry1.published_parsed = (2023, 1, 1, 12, 0, 0, 0, 0, 0)
        
        mock_entry2 = Mock()
        mock_entry2.get.side_effect = lambda key, default=None: {
            'title': 'Article 2',
            'link': 'https://example.com/article2',
            'description': 'Description 2'
        }.get(key, default)
        mock_entry2.__contains__ = lambda self, key: key in ['title', 'link', 'description']
        mock_entry2.title = 'Article 2'
        mock_entry2.link = 'https://example.com/article2'
        mock_entry2.description = 'Description 2'
        mock_entry2.published_parsed = None
        
        mock_feed_data.entries = [mock_entry1, mock_entry2]
        
        articles = self.processor._extract_articles(mock_feed_data, "https://example.com/feed")
        
        assert len(articles) == 2
        
        # Check first article
        assert articles[0].title == "Article 1"
        assert articles[0].url == "https://example.com/article1"
        assert articles[0].feed_source == "Test Feed"
        assert articles[0].description == "Description 1"
        assert articles[0].author == "Author 1"
        assert articles[0].published_date == datetime(2023, 1, 1, 12, 0)
        
        # Check second article
        assert articles[1].title == "Article 2"
        assert articles[1].url == "https://example.com/article2"
        assert articles[1].published_date is None
        assert articles[1].description == "Description 2"
    
    @patch('components.feed_processor.ThreadPoolExecutor')
    @patch('components.feed_processor.as_completed')
    def test_process_feeds_concurrent(self, mock_as_completed, mock_executor_class):
        """Test concurrent processing of multiple feeds."""
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock successful feed processing
        mock_future1 = Mock()
        mock_future1.result.return_value = FeedResult(
            feed_url="https://feed1.com",
            success=True,
            articles=[Article("Article 1", "https://example.com/1", None, "Feed 1")],
            processing_time=1.0
        )
        
        mock_future2 = Mock()
        mock_future2.result.return_value = FeedResult(
            feed_url="https://feed2.com",
            success=False,
            articles=[],
            error_message="Connection failed",
            processing_time=0.5
        )
        
        mock_executor.submit.side_effect = [mock_future1, mock_future2]
        
        # Mock as_completed to return our futures in sequence
        mock_as_completed.return_value = [mock_future1, mock_future2]
        
        feed_urls = ["https://feed1.com", "https://feed2.com"]
        results = self.processor.process_feeds(feed_urls)
        
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert len(results[0].articles) == 1
        assert len(results[1].articles) == 0
    
    def test_get_all_articles(self):
        """Test getting all articles from multiple feeds."""
        # Mock feed results
        mock_results = [
            FeedResult(
                feed_url="https://feed1.com",
                success=True,
                articles=[
                    Article("Article 1", "https://example.com/1", datetime(2023, 1, 2), "Feed 1"),
                    Article("Article 2", "https://example.com/2", datetime(2023, 1, 1), "Feed 1")
                ],
                processing_time=1.0
            ),
            FeedResult(
                feed_url="https://feed2.com",
                success=False,
                articles=[],
                error_message="Connection failed",
                processing_time=0.5
            ),
            FeedResult(
                feed_url="https://feed3.com",
                success=True,
                articles=[
                    Article("Article 3", "https://example.com/3", datetime(2023, 1, 3), "Feed 3")
                ],
                processing_time=0.8
            )
        ]
        
        with patch.object(self.processor, 'process_feeds', return_value=mock_results):
            articles = self.processor.get_all_articles(["https://feed1.com", "https://feed2.com", "https://feed3.com"])
            
            # Should get articles from successful feeds only
            assert len(articles) == 3
            
            # Articles should be sorted by published date (newest first)
            assert articles[0].title == "Article 3"  # Latest date
            assert articles[1].title == "Article 1"
            assert articles[2].title == "Article 2"  # Earliest date


class TestProcessRSSFeedsFunction:
    """Test cases for the convenience function."""
    
    def test_process_rss_feeds_function(self):
        """Test the convenience function for processing RSS feeds."""
        feed_urls = ["https://feed1.com", "https://feed2.com"]
        
        with patch('components.feed_processor.RSSFeedProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            mock_processor.get_all_articles.return_value = [
                Article("Test Article", "https://example.com/test", None, "Test Feed")
            ]
            
            articles = process_rss_feeds(feed_urls)
            
            assert len(articles) == 1
            assert articles[0].title == "Test Article"
            
            # Verify processor was properly closed
            mock_processor.close.assert_called_once()


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__]) 