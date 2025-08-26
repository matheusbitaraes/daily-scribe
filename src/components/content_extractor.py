"""
Content Extractor for Daily Scribe application.

This module handles extracting content from articles, prioritizing RSS feed data
and falling back to web scraping if necessary.
"""

import logging
from typing import Optional, Tuple

from components.feed_processor import Article
from components.scraper import ArticleScraper
from components.summarizer import Summarizer


class ContentExtractor:
    """Handles extracting and summarizing article content."""

    def __init__(self, scraper: ArticleScraper, summarizer: Summarizer):
        """
        Initialize the content extractor.

        Args:
            scraper: An instance of ArticleScraper.
            summarizer: An instance of Summarizer.
        """
        self.logger = logging.getLogger(__name__)
        self.scraper = scraper
        self.summarizer = summarizer

    def extract_and_summarize(self, article: Article) -> Optional[dict]:
        """
        Extracts content from an article and summarizes it, returning metadata dict.

        Prioritizes content from the RSS feed (description/content fields).
        If not sufficient, falls back to scraping the article URL.

        Args:
            article: The Article object containing title, URL, and potentially description/content.

        Returns:
            A dict with summary, sentiment, keywords, category, region, or None if summarization fails.
        """
        content_to_summarize = None

        # 1. Try to use content from RSS feed first
        if article.content:
            content_to_summarize = article.content
            self.logger.debug(f"Using full content from RSS for {article.title}")
        elif article.description:
            content_to_summarize = article.description
            self.logger.debug(f"Using description from RSS for {article.title}")

        # If RSS content is too short, try scraping
        if not content_to_summarize or len(content_to_summarize) < 30:
            self.logger.debug(f"RSS content insufficient for {article.title}, attempting to scrape.")
            try:
                scraped_content, _ = self.scraper.extract_article_content(article.url)
                if scraped_content:
                    content_to_summarize = scraped_content
                    self.logger.debug(f"Successfully scraped content for {article.title}")
                else:
                    self.logger.warning(f"Scraping failed for {article.url}. No content to summarize.")
                    return None
            except Exception as e:
                self.logger.error(f"Error scraping {article.url}: {e}")
                return None

        if not content_to_summarize:
            self.logger.warning(f"No content available to summarize for {article.title}")
            return None

        # Summarize the chosen content and extract metadata
        try:
            metadata = self.summarizer.summarize(content_to_summarize)
            if metadata and metadata.get('summary'):
                self.logger.debug(f"Successfully summarized {article.title}")
                # log metadata for debugging
                # self.logger.info(f"Metadata: {metadata}")
                return metadata
            else:
                self.logger.warning(f"Summarization returned empty for {article.title}")
                return None
        except Exception as e:
            self.logger.error(f"Error summarizing {article.title}: {e}")
            return None
