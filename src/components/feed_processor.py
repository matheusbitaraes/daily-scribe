"""
RSS Feed Processor for Daily Scribe application.

This module handles fetching content from RSS feeds, parsing XML content,
and extracting individual article information with concurrent processing.
"""

import asyncio
import logging
import time


from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import feedparser
feedparser.PREFERRED_PARSER = "drv_sgmllib"
import requests
from datetime import datetime


class Article:
    """Represents a single article from an RSS feed."""
    
    def __init__(self, title, url, published_date, feed_source, description=None, author=None, 
                 content=None, summary=None, summary_generated=False):
        self.title = title
        self.url = url
        self.published_date = published_date
        self.feed_source = feed_source
        self.description = description
        self.author = author
        self.content = content  # Full article content
        self.summary = summary  # Generated summary
        self.summary_generated = summary_generated  # Whether summary was generated


class FeedResult:
    """Result of processing a single RSS feed."""
    
    def __init__(self, feed_url, success, articles, error_message=None, processing_time=0.0):
        self.feed_url = feed_url
        self.success = success
        self.articles = articles
        self.error_message = error_message
        self.processing_time = processing_time


class RSSFeedProcessor:
    """Handles fetching and parsing RSS feeds with concurrent processing."""
    
    def __init__(self, timeout: int = 15):
        """
        Initialize the RSS feed processor.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Configure requests session with timeout
        self.session = requests.Session()
        self.session.timeout = timeout
    
    def get_all_articles(self, feed_urls: List[str]) -> List[Article]:
        """
        Get all articles from multiple feeds, flattening the results.
        
        Args:
            feed_urls: List of RSS feed URLs to process
            
        Returns:
            List of all Article objects from all feeds
        """
        all_articles = []
        for url in feed_urls:
            result = self._process_single_feed(url)
            if result.success:
                all_articles.extend(result.articles)
            else:
                self.logger.warning(f"Skipping failed feed: {result.feed_url} - Reason: {result.error_message}")
        
        # Sort articles by published date (newest first)
        all_articles.sort(
            key=lambda x: x.published_date or datetime.min,
            reverse=True
        )
        
        self.logger.info(f"Retrieved {len(all_articles)} total articles from {len(feed_urls)} feeds")
        return all_articles

    def _process_single_feed(self, feed_url: str) -> FeedResult:
        """
        Process a single RSS feed.
        
        Args:
            feed_url: URL of the RSS feed to process
            
        Returns:
            FeedResult object with processing results
        """
        start_time = time.time()
        
        try:
            # Validate URL format
            if not self._is_valid_url(feed_url):
                return FeedResult(
                    feed_url=feed_url,
                    success=False,
                    articles=[],
                    error_message="Invalid URL format",
                    processing_time=0.0
                )
            
            # Fetch RSS content
            self.logger.info(f"Fetching RSS feed: {feed_url}")
            response = self.session.get(feed_url, timeout=self.timeout)

            response.raise_for_status()
            
            # Parse RSS content
            feed_data = feedparser.parse(response.content)
            
            # Check if parsing was successful
            if feed_data.bozo:
                return FeedResult(
                    feed_url=feed_url,
                    success=False,
                    articles=[],
                    error_message=f"RSS parsing failed: {feed_data.bozo_exception}",
                    processing_time=time.time() - start_time
                )
            
            # Extract articles
            articles = self._extract_articles(feed_data, feed_url)
            
            processing_time = time.time() - start_time
            
            return FeedResult(
                feed_url=feed_url,
                success=True,
                articles=articles,
                processing_time=processing_time
            )
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout fetching RSS feed {feed_url}: {e}")
            return FeedResult(
                feed_url=feed_url,
                success=False,
                articles=[],
                error_message=f"Timeout fetching feed: {str(e)}",
                processing_time=time.time() - start_time
            )
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request failed for RSS feed {feed_url}: {e}")
            return FeedResult(
                feed_url=feed_url,
                success=False,
                articles=[],
                error_message=f"HTTP request failed: {str(e)}",
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            return FeedResult(
                feed_url=feed_url,
                success=False,
                articles=[],
                error_message=f"Processing error: {str(e)}",
                processing_time=time.time() - start_time
            )

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False
        try:
            result = urlparse(url)
            # Only allow HTTP and HTTPS schemes
            return (result.scheme in ['http', 'https'] and 
                   result.netloc and 
                   '.' in result.netloc)
        except Exception:
            return False

    def _extract_articles(self, feed_data: feedparser.FeedParserDict, feed_url: str) -> List[Article]:
        """
        Extract article information from parsed RSS feed data.
        
        Args:
            feed_data: Parsed RSS feed data from feedparser
            feed_url: Source RSS feed URL
            
        Returns:
            List of Article objects
        """
        articles = []
        feed_source = feed_data.feed.get('title', feed_url)
        
        for entry in feed_data.entries:
            try:
                # Extract basic article information
                title = entry.get('title', 'Untitled')
                url = entry.get('link', '')
                
                # Skip entries without title or URL
                if not title or not url:
                    continue
                
                # Parse published date
                published_date = None
                if 'published_parsed' in entry and entry.published_parsed:
                    try:
                        published_date = datetime(*entry.published_parsed[:6])
                    except (ValueError, TypeError):
                        pass
                
                # Extract description
                description = None
                if 'summary' in entry:
                    description = entry.summary
                elif 'description' in entry:
                    description = entry.description
                
                # Extract author
                author = None
                if 'author' in entry:
                    author = entry.author
                elif 'author_detail' in entry and entry.author_detail.get('name'):
                    author = entry.author_detail.name
                
                article = Article(
                    title=title.strip(),
                    url=url.strip(),
                    published_date=published_date,
                    feed_source=feed_source,
                    description=description.strip() if description else None,
                    author=author.strip() if author else None
                )
                
                articles.append(article)
                
            except Exception as e:
                self.logger.warning(f"Error extracting article from feed {feed_url}: {e}")
                continue
        
        return articles
    
    def close(self):
        """Close the requests session."""
        self.session.close()


def process_rss_feeds(feed_urls: List[str]) -> List[Article]:
    """
    Convenience function to process RSS feeds and return articles.
    
    Args:
        feed_urls: List of RSS feed URLs to process
        
    Returns:
        List of Article objects from all feeds
    """
    processor = RSSFeedProcessor()
    try:
        return processor.get_all_articles(feed_urls)
    finally:
        processor.close()


if __name__ == "__main__":
    # Test the RSS feed processor
    import logging
    
    
    
    # Test URLs
    test_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss"
    ]
    
    print("Testing RSS Feed Processor...")
    articles = process_rss_feeds(test_feeds)
    
    print(f"\nRetrieved {len(articles)} articles:")
    for i, article in enumerate(articles[:5], 1):  # Show first 5 articles
        print(f"{i}. {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Source: {article.feed_source}")
        if article.published_date:
            print(f"   Published: {article.published_date}")
        print() 