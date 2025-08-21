"""
Main entry point for Daily Scribe application.

This module handles the scheduling and execution of the daily digest generation.
"""

import sys
import logging
import time
from pathlib import Path
from typing import Optional

import schedule
import typer

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from components.config import load_config
from components.database import DatabaseService
from components.feed_processor import RSSFeedProcessor
from components.scraper import ArticleScraper
from components.summarizer import Summarizer
from components.notifier import EmailNotifier
from components.content_extractor import ContentExtractor

app = typer.Typer()

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


def generate_digest(config_path: Optional[str] = None) -> None:
    """
    Generate the daily digest.

    Args:
        config_path: Optional path to the configuration file.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting daily digest generation...")

    try:
        # Load configuration
        config = load_config(config_path)

        # Initialize components
        db_service = DatabaseService()
        feed_processor = RSSFeedProcessor()
        scraper = ArticleScraper()
        summarizer = Summarizer()
        content_extractor = ContentExtractor(scraper, summarizer)

        # Fetch articles
        articles = feed_processor.get_all_articles(config.rss_feeds)
        logger.info(f"Retrieved {len(articles)} articles from {len(config.rss_feeds)} feeds.")

        # Filter out processed articles
        processed_urls = db_service.get_processed_urls()
        new_articles = [article for article in articles if article.url not in processed_urls]
        logger.info(f"Found {len(new_articles)} new articles to process.")

        # Process new articles
        summaries = []
        for article in new_articles:
            try:
                # Extract and summarize content
                summary = content_extractor.extract_and_summarize(article)
                if not summary:
                    logger.warning(f"Could not summarize {article.url}. Skipping.")
                    continue

                # Store article and summary
                db_service.mark_as_processed(article.url, summary)
                summaries.append({
                    'title': article.title,
                    'link': article.url,
                    'summary': summary
                })
                logger.info(f"Processed and summarized: {article.title}")

            except Exception as e:
                logger.error(f"Failed to process article {article.url}: {e}")

        # Compile digest
        if summaries:
            digest = """
            Here is your daily digest:
            """
            for summary in summaries:
                digest += f"\n## {summary['title']}\n"
                digest += f"**Link:** {summary['link']}\n\n"
                digest += f"{summary['summary']}\n\n"

            # Send email with the digest
            notifier = EmailNotifier(config.email.__dict__)
            subject = f"Your Daily Digest for {time.strftime('%Y-%m-%d')}"
            notifier.send_digest(digest, config.email.to, subject)

            logger.info("Daily digest generated and sent successfully.")
        else:
            logger.info("No new articles to generate a digest.")

    except Exception as e:
        logger.error(f"An error occurred during digest generation: {e}")


@app.command(name="run")
def run_digest(config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")):
    """
    Runs the daily digest generation process.
    """
    setup_logging()
    generate_digest(config_path)


@app.command(name="schedule")
def schedule_digest(config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")):
    """
    Schedules the daily digest generation process.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Load configuration to get schedule details
        config = load_config(config_path)
        schedule_time = f"{config.schedule.hour:02d}:{config.schedule.minute:02d}"
        logger.info(f"Scheduling daily digest for {schedule_time}.")

        # Schedule the job
        schedule.every().day.at(schedule_time).do(generate_digest, config_path=config_path)

        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()