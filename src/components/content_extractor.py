"""
Content Extractor for Daily Scribe application.

This module handles extracting content from articles, prioritizing RSS feed data
and falling back to web scraping if necessary.
"""

import logging
from typing import Optional, Tuple
import importlib
import json

from components.feed_processor import Article
from components.scraper import ArticleScraper
from components.database import DatabaseService
from components.feed_parsers.base_parser import BaseParser

class ContentExtractor:
    """Handles extracting and summarizing article content."""

    def __init__(self, scraper: ArticleScraper):
        """
        Initialize the content extractor.

        Args:
            scraper: An instance of ArticleScraper.
        """
        self.logger = logging.getLogger(__name__)
        self.scraper = scraper
        self.db_service = DatabaseService()
        self.parsers = {}

    def _get_parser(self, parser_name: str) -> BaseParser:
        """
        Dynamically load and instantiate a parser.
        """
        if parser_name not in self.parsers:
            try:
                module = importlib.import_module(f"components.feed_parsers.{parser_name.lower()}")
                parser_class = getattr(module, parser_name)
                self.parsers[parser_name] = parser_class()
            except (ImportError, AttributeError) as e:
                self.logger.error(f"Could not load parser {parser_name}: {e}. Using DefaultParser.")
                from components.feed_parsers.default_parser import DefaultParser
                self.parsers[parser_name] = DefaultParser()
        return self.parsers[parser_name]

    def extract_and_save(self, article: Article) -> None:
        """
        Extracts content from an article and saves it to the database.

        Prioritizes content from the RSS feed (description/content fields).
        If not sufficient, falls back to scraping the article URL.

        Args:
            article: The Article object containing title, URL, and potentially description/content.
        """
        content_to_save = None

        feed_details = self.db_service.get_feed_details_by_url(article.feed_source)
        parser_name = feed_details.get('parser', 'DefaultParser') if feed_details else 'DefaultParser'
        parser = self._get_parser(parser_name)
        
        # 1. Try to use content from RSS feed first
        content_parts = parser.parse(article.raw_entry)
        
        # Serialize the list of ContentPart objects to a JSON string
        content_to_save = json.dumps([part.__dict__ for part in content_parts])

        # If RSS content is too short, try scraping
        if not content_parts:
            self.logger.debug(f"RSS content insufficient for {article.title}, attempting to scrape.")
            try:
                scraped_content, _ = self.scraper.extract_article_content(article.url)
                if scraped_content:
                    # For scraped content, we can create a default structure
                    content_to_save = json.dumps([{'text': scraped_content, 'type': 'scraped'}])
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
            self.db_service.add_article_content(db_article['id'], content_to_save)
            self.logger.info(f"Saved content for {article.title}")
        else:
            # This case should ideally not happen if we process articles correctly
            self.logger.warning(f"Could not find article in DB to associate content with: {article.url}")
