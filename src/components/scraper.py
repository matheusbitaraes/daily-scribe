"""
Article Scraper for Daily Scribe application.

This module handles extracting full text content from article URLs
using web scraping techniques with BeautifulSoup.
"""

import logging
import time
from typing import Optional, Tuple
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup, Comment


class ArticleExtractorError(Exception):
    """Custom exception for article extraction errors."""
    pass


class ArticleScraper:
    """Handles extracting full text content from article URLs."""
    
    def __init__(self, timeout: int = 30, max_content_length: int = 50000):
        """
        Initialize the article scraper.
        
        Args:
            timeout: Request timeout in seconds
            max_content_length: Maximum content length to process (characters)
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.logger = logging.getLogger(__name__)
        
        # Configure requests session with timeout and headers
        self.session = requests.Session()
        self.session.timeout = timeout
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_article_content(self, url: str) -> tuple:
        """
        Extract the main content and first paragraph from an article URL.
        
        Args:
            url: The article URL to scrape
            
        Returns:
            Tuple of (full_content, first_paragraph)
            
        Raises:
            ArticleExtractorError: If extraction fails
        """
        self.logger.debug(f"Extracting content from: {url}")
        start_time = time.time()
        
        try:
            # Fetch the HTML content
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content length
            if len(response.content) > self.max_content_length:
                self.logger.warning(f"Content too large ({len(response.content)} chars), truncating")
                content = response.content[:self.max_content_length]
            else:
                content = response.content
            
            # Parse the HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            self._clean_soup(soup)
            
            # Extract the main content
            main_content = self._extract_main_content(soup)
            
            # Extract first paragraph
            first_paragraph = self._extract_first_paragraph(main_content)
            
            processing_time = time.time() - start_time
            self.logger.debug(f"Content extracted in {processing_time:.2f}s: {len(main_content)} chars")
            
            return main_content, first_paragraph
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout fetching article from {url}: {e}")
            raise ArticleExtractorError(f"Timeout fetching URL {url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request failed for article {url}: {e}")
            raise ArticleExtractorError(f"Failed to fetch URL {url}: {str(e)}")
            
        except Exception as e:
            raise ArticleExtractorError(f"Failed to extract content from {url}: {str(e)}")
    
    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """
        Remove unwanted elements from the soup.
        
        Args:
            soup: BeautifulSoup object to clean
        """
        # Remove script and style elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove elements with common ad/navigation classes
        unwanted_classes = [
            'advertisement', 'ads', 'sidebar', 'navigation', 'nav', 
            'footer', 'header', 'menu', 'social', 'share', 'related',
            'comments', 'comment', 'popup', 'modal', 'overlay'
        ]
        
        for class_name in unwanted_classes:
            for element in soup.find_all(class_=lambda x: x and any(cls in class_name for cls in str(x).lower().split())):
                element.decompose()
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main article content from the soup.
        
        Args:
            soup: Cleaned BeautifulSoup object
            
        Returns:
            Main article content as text
        """
        # Try different selectors for main content
        content_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.main-content',
            '#content',
            '#main',
            '.story-body',
            '.article-body'
        ]
        
        main_content = None
        
        # Try each selector until we find substantial content
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Get the largest element (likely the main content)
                largest_element = max(elements, key=lambda x: len(x.get_text()))
                text = largest_element.get_text(separator='\n', strip=True)
                
                # Check if this looks like substantial content (more than 200 chars)
                if len(text) > 200:
                    main_content = text
                    break
        
        # Fallback: extract all paragraph text
        if not main_content:
            paragraphs = soup.find_all('p')
            if paragraphs:
                main_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Final fallback: get all text
        if not main_content:
            main_content = soup.get_text(separator='\n', strip=True)
        
        # Clean up the text
        main_content = self._clean_text(main_content or "")
        
        return main_content
    
    def _extract_first_paragraph(self, content: str) -> str:
        """
        Extract the first substantial paragraph from the content.
        
        Args:
            content: Full article content
            
        Returns:
            First paragraph as text
        """
        if not content:
            return ""
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Find the first substantial paragraph (more than 50 characters)
        for paragraph in paragraphs:
            if len(paragraph) > 50:
                # Limit to reasonable length for a summary
                if len(paragraph) > 500:
                    # Find a good breaking point (sentence end)
                    sentences = paragraph.split('. ')
                    result = sentences[0]
                    for sentence in sentences[1:]:
                        if len(result + '. ' + sentence) <= 500:
                            result += '. ' + sentence
                        else:
                            break
                    return result + ('.' if not result.endswith('.') else '')
                else:
                    return paragraph
        
        # Fallback: return first 300 characters
        if content:
            return content[:300] + ('...' if len(content) > 300 else '')
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and formatting.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Replace multiple whitespace characters with single spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove extra newlines but preserve paragraph breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def close(self):
        """Close the requests session."""
        self.session.close()


def extract_article_content(url: str) -> tuple:
    """
    Convenience function to extract article content.
    
    Args:
        url: Article URL to scrape
        
    Returns:
        Tuple of (full_content, first_paragraph)
    """
    scraper = ArticleScraper()
    try:
        return scraper.extract_article_content(url)
    finally:
        scraper.close()


if __name__ == "__main__":
    # Test the article scraper
    import logging
    
    
    
    # Test URL (you can replace with any article URL)
    test_url = "https://www.bbc.com/news"
    
    print(f"Testing Article Scraper with: {test_url}")
    try:
        content, first_paragraph = extract_article_content(test_url)
        print(f"\nExtracted {len(content)} characters")
        print(f"First paragraph ({len(first_paragraph)} chars):")
        print(f"{first_paragraph}\n")
    except ArticleExtractorError as e:
        print(f"Error: {e}")