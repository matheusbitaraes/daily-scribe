
"""
Tests for the article scraper component.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.scraper import ArticleScraper, ArticleExtractorError, extract_article_content


class TestArticleScraper:
    """Test cases for ArticleScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = ArticleScraper(timeout=10, max_content_length=1000)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.scraper.close()
    
    def test_scraper_initialization(self):
        """Test ArticleScraper initialization."""
        assert self.scraper.timeout == 10
        assert self.scraper.max_content_length == 1000
        assert self.scraper.session is not None
    
    @patch('components.scraper.requests.Session')
    @patch('components.scraper.BeautifulSoup')
    def test_extract_article_content_success(self, mock_soup_class, mock_session_class):
        """Test successful article content extraction."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = b'<html><body><article><p>First paragraph content.</p><p>Second paragraph.</p></article></body></html>'
        mock_response.raise_for_status.return_value = None
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        self.scraper.session = mock_session
        
        # Mock BeautifulSoup
        mock_soup = Mock()
        mock_soup.find_all.return_value = []
        mock_soup.select.return_value = [Mock()]
        mock_soup.select.return_value[0].get_text.return_value = "First paragraph content.\n\nSecond paragraph."
        mock_soup.get_text.return_value = "First paragraph content.\n\nSecond paragraph."
        mock_soup_class.return_value = mock_soup
        
        content, first_paragraph = self.scraper.extract_article_content("https://example.com/article")
        
        assert content == "First paragraph content. Second paragraph."
        assert len(first_paragraph) > 0
        mock_session.get.assert_called_once_with("https://example.com/article")
    
    def test_extract_article_content_http_error(self):
        """Test handling of HTTP errors."""
        # Mock session to raise an exception
        self.scraper.session = Mock()
        self.scraper.session.get.side_effect = Exception("Connection failed")
        
        with pytest.raises(ArticleExtractorError) as excinfo:
            self.scraper.extract_article_content("https://example.com/article")
        
        assert "Failed" in str(excinfo.value)
    
    @patch('components.scraper.BeautifulSoup')
    def test_extract_content_too_large(self, mock_soup_class):
        """Test handling of content that exceeds max length."""
        # Mock HTTP response with large content
        mock_response = Mock()
        mock_response.content = b'x' * 2000  # Larger than max_content_length of 1000
        mock_response.raise_for_status.return_value = None
        
        self.scraper.session = Mock()
        self.scraper.session.get.return_value = mock_response
        
        # Mock BeautifulSoup
        mock_soup = Mock()
        mock_soup.find_all.return_value = []
        mock_soup.select.return_value = [Mock()]
        mock_soup.select.return_value[0].get_text.return_value = "Extracted content"
        mock_soup.get_text.return_value = "Extracted content"
        mock_soup_class.return_value = mock_soup
        
        # Should not raise an error, but should truncate
        content, first_paragraph = self.scraper.extract_article_content("https://example.com/article")
        
        assert content == "Extracted content"
    
    def test_clean_soup(self):
        """Test soup cleaning functionality."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <head><script>var x = 1;</script></head>
            <body>
                <nav>Navigation</nav>
                <article>Main content</article>
                <footer>Footer content</footer>
                <div class="advertisement">Ad content</div>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        self.scraper._clean_soup(soup)
        
        # Should remove script, nav, footer elements
        assert soup.find('script') is None
        assert soup.find('nav') is None
        assert soup.find('footer') is None
        
        # Main content should remain
        assert soup.find('article') is not None
    
    def test_extract_main_content(self):
        """Test main content extraction."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>First paragraph with substantial content that should be extracted.</p>
                    <p>Second paragraph with more content.</p>
                </article>
                <aside>Sidebar content</aside>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        content = self.scraper._extract_main_content(soup)
        
        assert "First paragraph with substantial content" in content
        assert "Second paragraph with more content" in content
        assert "Sidebar content" not in content
    
    def test_extract_first_paragraph(self):
        """Test first paragraph extraction."""
        content = """
        Short line

        
        This is the first substantial paragraph that contains enough content to be considered
        a proper paragraph for summarization purposes and should be extracted.
        

        This is the second paragraph with additional content.
        """
        
        first_paragraph = self.scraper._extract_first_paragraph(content)
        
        assert "first substantial paragraph" in first_paragraph
        assert "second paragraph" not in first_paragraph
        assert len(first_paragraph) > 50
    
    def test_extract_first_paragraph_long_content(self):
        """Test first paragraph extraction with very long content."""
        # Create a very long paragraph
        long_paragraph = "This is a very long paragraph. " * 50  # Makes it > 500 chars
        content = f"{long_paragraph}\n\nSecond paragraph."
        
        first_paragraph = self.scraper._extract_first_paragraph(content)
        
        # Should be truncated to reasonable length
        assert len(first_paragraph) <= 503  # 500 + some tolerance for sentence completion
        assert first_paragraph.endswith(".")
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = """
        This    has     multiple    spaces
        
        
        
        And multiple newlines
        
        With    more   spaces
        """
        
        clean_text = self.scraper._clean_text(dirty_text)
        
        # Should have single spaces and proper paragraph breaks
        assert "multiple    spaces" not in clean_text
        assert "multiple spaces" in clean_text
        assert "\n\n\n" not in clean_text
        assert clean_text.strip() == clean_text


class TestExtractArticleContentFunction:
    """Test cases for the convenience function."""
    
    @patch('components.scraper.ArticleScraper')
    def test_extract_article_content_function(self, mock_scraper_class):
        """Test the convenience function."""
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        
        mock_scraper.extract_article_content.return_value = ("Test content", "Test paragraph")
        
        content, paragraph = extract_article_content("https://example.com/test")
        
        assert content == "Test content"
        assert paragraph == "Test paragraph"
        
        # Verify scraper was properly closed
        mock_scraper.close.assert_called_once()


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__])
