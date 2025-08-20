"""
Article Processing Service for Daily Scribe application.

This module combines RSS feed processing, content extraction, and summarization
to create complete article summaries for the daily digest.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any, Tuple
from .feed_processor import RSSFeedProcessor, Article, FeedResult
from .scraper import ArticleScraper, ArticleExtractorError
from .summarizer import ArticleSummarizer, SummarizationResult


class ProcessingStats:
    """Statistics for article processing."""
    
    def __init__(self, total_articles, articles_processed, articles_summarized, 
                 scraping_failures, summarization_failures, processing_time):
        self.total_articles = total_articles
        self.articles_processed = articles_processed
        self.articles_summarized = articles_summarized
        self.scraping_failures = scraping_failures
        self.summarization_failures = summarization_failures
        self.processing_time = processing_time


class ArticleProcessor:
    """Handles end-to-end article processing: RSS -> Content -> Summary."""
    
    def __init__(self, 
                 max_workers: int = 3,
                 max_articles_per_feed: int = 10,
                 scraper_timeout: int = 30,
                 enable_summarization: bool = True):
        """
        Initialize the article processor.
        
        Args:
            max_workers: Maximum number of concurrent article processors
            max_articles_per_feed: Maximum articles to process per feed
            scraper_timeout: Timeout for content scraping
            enable_summarization: Whether to generate summaries
        """
        self.max_workers = max_workers
        self.max_articles_per_feed = max_articles_per_feed
        self.enable_summarization = enable_summarization
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.rss_processor = RSSFeedProcessor(max_workers=max_workers)
        self.scraper = ArticleScraper(timeout=scraper_timeout)
        self.summarizer = ArticleSummarizer()
    
    def process_feeds_with_summaries(self, feed_urls: List[str]) -> Tuple[List[Article], ProcessingStats]:
        """
        Process RSS feeds and generate summaries for articles.
        
        Args:
            feed_urls: List of RSS feed URLs to process
            
        Returns:
            Tuple of (processed_articles, processing_stats)
        """
        start_time = time.time()
        self.logger.info(f"Starting end-to-end processing of {len(feed_urls)} RSS feeds")
        
        # Step 1: Fetch RSS feeds and extract article metadata
        self.logger.info("Step 1: Fetching RSS feeds...")
        feed_results = self.rss_processor.process_feeds(feed_urls)
        
        # Collect all articles from successful feeds
        all_articles = []
        for result in feed_results:
            if result.success:
                # Limit articles per feed to avoid overprocessing
                articles_to_process = result.articles[:self.max_articles_per_feed]
                all_articles.extend(articles_to_process)
                
                if len(result.articles) > self.max_articles_per_feed:
                    self.logger.info(f"Limited {result.feed_url} to {self.max_articles_per_feed} articles "
                                   f"(had {len(result.articles)})")
        
        self.logger.info(f"Found {len(all_articles)} articles across all feeds")
        
        # Step 2: Process articles with content extraction and summarization
        if self.enable_summarization and all_articles:
            self.logger.info("Step 2: Processing articles with content extraction and summarization...")
            processed_articles = self._process_articles_with_content(all_articles)
        else:
            self.logger.info("Summarization disabled, skipping content processing")
            processed_articles = all_articles
        
        # Calculate statistics
        total_time = time.time() - start_time
        stats = self._calculate_stats(all_articles, processed_articles, total_time)
        
        self.logger.info(f"Article processing completed in {total_time:.2f}s")
        self.logger.info(f"Successfully processed {stats.articles_summarized}/{stats.total_articles} articles")
        
        return processed_articles, stats
    
    def _process_articles_with_content(self, articles: List[Article]) -> List[Article]:
        """
        Process articles by extracting content and generating summaries.
        
        Args:
            articles: List of articles to process
            
        Returns:
            List of processed articles with content and summaries
        """
        processed_articles = []
        
        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all article processing tasks
            future_to_article = {
                executor.submit(self._process_single_article, article): article 
                for article in articles
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    processed_article = future.result()
                    processed_articles.append(processed_article)
                    
                    if processed_article.summary_generated:
                        self.logger.debug(f"Successfully processed: {processed_article.title[:50]}...")
                    else:
                        self.logger.warning(f"Failed to process: {processed_article.title[:50]}...")
                        
                except Exception as e:
                    self.logger.error(f"Unexpected error processing article '{article.title[:50]}...': {e}")
                    # Still add the article, but without content/summary
                    processed_articles.append(article)
        
        return processed_articles
    
    def _process_single_article(self, article: Article) -> Article:
        """
        Process a single article: extract content and generate summary.
        
        Args:
            article: Article to process
            
        Returns:
            Processed article with content and summary
        """
        try:
            # Step 1: Extract full content from article URL
            self.logger.debug(f"Extracting content from: {article.url}")
            content, first_paragraph = self.scraper.extract_article_content(article.url)
            
            # Update article with extracted content
            article.content = content
            
            # Step 2: Generate summary
            if content:
                self.logger.debug(f"Generating summary for: {article.title[:50]}...")
                summary_result = self.summarizer.summarize_article(content, first_paragraph)
                
                if summary_result.success:
                    article.summary = summary_result.summary
                    article.summary_generated = True
                    self.logger.debug(f"Summary generated: {len(summary_result.summary)} chars")
                else:
                    self.logger.warning(f"Summarization failed for '{article.title[:50]}...': "
                                      f"{summary_result.error_message}")
                    # Fallback: use description or first paragraph
                    article.summary = article.description or first_paragraph or "No summary available"
                    article.summary_generated = False
            else:
                self.logger.warning(f"No content extracted for '{article.title[:50]}...', using description")
                article.summary = article.description or "No content available"
                article.summary_generated = False
                
        except ArticleExtractorError as e:
            self.logger.warning(f"Content extraction failed for '{article.title[:50]}...': {e}")
            article.summary = article.description or "Content extraction failed"
            article.summary_generated = False
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing '{article.title[:50]}...': {e}")
            article.summary = article.description or "Processing error occurred"
            article.summary_generated = False
        
        return article
    
    def _calculate_stats(self, original_articles: List[Article], 
                        processed_articles: List[Article], 
                        processing_time: float) -> ProcessingStats:
        """
        Calculate processing statistics.
        
        Args:
            original_articles: Original articles from RSS feeds
            processed_articles: Articles after processing
            processing_time: Total processing time
            
        Returns:
            ProcessingStats object
        """
        articles_with_content = sum(1 for a in processed_articles if a.content)
        articles_with_summaries = sum(1 for a in processed_articles if a.summary_generated)
        scraping_failures = len(processed_articles) - articles_with_content
        summarization_failures = articles_with_content - articles_with_summaries
        
        return ProcessingStats(
            total_articles=len(original_articles),
            articles_processed=len(processed_articles),
            articles_summarized=articles_with_summaries,
            scraping_failures=scraping_failures,
            summarization_failures=summarization_failures,
            processing_time=processing_time
        )
    
    def get_processing_info(self) -> Dict[str, Any]:
        """
        Get information about the processing configuration.
        
        Returns:
            Processing configuration dictionary
        """
        return {
            'max_workers': self.max_workers,
            'max_articles_per_feed': self.max_articles_per_feed,
            'enable_summarization': self.enable_summarization,
            'scraper_timeout': self.scraper.timeout,
            'summarizer_config': self.summarizer.get_model_info()
        }
    
    def close(self):
        """Close all resources."""
        if hasattr(self.rss_processor, 'close'):
            self.rss_processor.close()
        if hasattr(self.scraper, 'close'):
            self.scraper.close()


def process_feeds_with_summaries(feed_urls: List[str], 
                                max_workers: int = 3,
                                max_articles_per_feed: int = 10) -> Tuple[List[Article], ProcessingStats]:
    """
    Convenience function to process RSS feeds with summaries.
    
    Args:
        feed_urls: List of RSS feed URLs to process
        max_workers: Maximum number of concurrent workers
        max_articles_per_feed: Maximum articles to process per feed
        
    Returns:
        Tuple of (processed_articles, processing_stats)
    """
    processor = ArticleProcessor(
        max_workers=max_workers,
        max_articles_per_feed=max_articles_per_feed
    )
    try:
        return processor.process_feeds_with_summaries(feed_urls)
    finally:
        processor.close()


if __name__ == "__main__":
    # Test the article processor
    import logging
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test URLs
    test_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml"
    ]
    
    print("Testing Article Processor...")
    articles, stats = process_feeds_with_summaries(test_feeds, max_articles_per_feed=3)
    
    print(f"\nProcessing Results:")
    print(f"Total articles: {stats.total_articles}")
    print(f"Articles summarized: {stats.articles_summarized}")
    print(f"Processing time: {stats.processing_time:.2f}s")
    
    print(f"\nSample articles with summaries:")
    for i, article in enumerate(articles[:2], 1):
        print(f"\n{i}. {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Summary generated: {article.summary_generated}")
        if article.summary:
            print(f"   Summary: {article.summary[:200]}...")
        print()