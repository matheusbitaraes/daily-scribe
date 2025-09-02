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
from components.database import DatabaseService


class ContentExtractor:
    """Handles extracting and summarizing article content."""

    def __init__(self, scraper: ArticleScraper):
        """
        Initialize the content extractor.

        Args:
            scraper: An instance of ArticleScraper.
            db_service: An instance of DatabaseService.
        """
        self.logger = logging.getLogger(__name__)
        self.scraper = scraper
        self.db_service = DatabaseService()

    def extract_and_save(self, article: Article) -> None:
        """
        Extracts content from an article and saves it to the database.

        Prioritizes content from the RSS feed (description/content fields).
        If not sufficient, falls back to scraping the article URL.

        Args:
            article: The Article object containing title, URL, and potentially description/content.
        """
        content_to_save = None

        # 1. Try to use content from RSS feed first
        if article.content:
            content_to_save = article.content
            self.logger.debug(f"Using full content from RSS for {article.title}")
        elif article.description:
            content_to_save = article.description
            self.logger.debug(f"Using description from RSS for {article.title}")

        # If RSS content is too short, try scraping
        if not content_to_save or len(content_to_save) < 30:
            self.logger.debug(f"RSS content insufficient for {article.title}, attempting to scrape.")
            try:
                scraped_content, _ = self.scraper.extract_article_content(article.url)
                if scraped_content:
                    content_to_save = scraped_content
                    self.logger.debug(f"Successfully scraped content for {article.title}")
                else:
                    self.logger.warning(f"Scraping failed for {article.url}. No content to save.")
                    return
            except Exception as e:
                self.logger.error(f"Error scraping {article.url}: {e}")
                return

        if not content_to_save:
            self.logger.warning(f"No content available to save for {article.title}")
            return
        
        db_article = self.db_service.get_article_by_url(article.url)
        if db_article:
            self.db_service.add_article_content(db_article['id'], article.url, content_to_save)
            self.logger.info(f"Saved content for {article.title}")
        else:
            # This case should ideally not happen if we process articles correctly
            self.logger.warning(f"Could not find article in DB to associate content with: {article.url}")
