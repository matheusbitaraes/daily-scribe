"""
Main entry point for Daily Scribe application.

This module demonstrates the configuration loading functionality
and serves as the foundation for the complete application.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from components.config import load_config, AppConfig
from components.feed_processor import process_rss_feeds, Article
from components.article_processor import process_feeds_with_summaries


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('digest.log')
        ]
    )


def main(config_path: Optional[str] = None) -> None:
    """
    Main application entry point.
    
    Args:
        config_path: Optional path to configuration file
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Daily Scribe application...")
        
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config(config_path)
        
        # Display configuration summary
        logger.info("Configuration loaded successfully!")
        logger.info(f"RSS Feeds configured: {len(config.rss_feeds)}")
        logger.info(f"Email destination: {config.email.to}")
        logger.info(f"Daily schedule: {config.schedule.hour:02d}:{config.schedule.minute:02d}")
        
        # Display RSS feeds
        logger.info("Configured RSS feeds:")
        for i, feed_url in enumerate(config.rss_feeds, 1):
            logger.info(f"  {i}. {feed_url}")
        
        # Test RSS feed processing with summarization
        logger.info("Testing RSS feed processing with summarization...")
        try:
            # First test basic RSS processing
            articles = process_rss_feeds(config.rss_feeds)
            logger.info(f"Successfully retrieved {len(articles)} articles from RSS feeds")
            
            # Then test with summarization (limited to 3 articles for demo)
            logger.info("Testing article summarization...")
            summarized_articles, stats = process_feeds_with_summaries(
                config.rss_feeds, 
                max_articles_per_feed=3,
                max_workers=2
            )
            
            logger.info(f"Article processing completed:")
            logger.info(f"  Total articles: {stats.total_articles}")
            logger.info(f"  Articles summarized: {stats.articles_summarized}")
            logger.info(f"  Processing time: {stats.processing_time:.2f}s")
            
            # Display sample articles with summaries
            if summarized_articles:
                logger.info("Sample articles with summaries:")
                for i, article in enumerate(summarized_articles[:2], 1):  # Show first 2 articles
                    logger.info(f"  {i}. {article.title}")
                    logger.info(f"     Source: {article.feed_source}")
                    logger.info(f"     URL: {article.url}")
                    if article.published_date:
                        logger.info(f"     Published: {article.published_date}")
                    logger.info(f"     Summary generated: {article.summary_generated}")
                    if article.summary:
                        # Truncate summary for display
                        summary_preview = article.summary[:150] + "..." if len(article.summary) > 150 else article.summary
                        logger.info(f"     Summary: {summary_preview}")
                    logger.info("")
            
        except Exception as e:
            logger.error(f"Article processing failed: {e}")
            logger.info("Continuing without article processing test...")
        
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error("Please create a config.json file based on config.json.example")
        sys.exit(1)
        
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_logging()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        main(config_path)
    else:
        main() 