"""
Main entry point for Daily Scribe application.

This module handles the scheduling and execution of the daily digest generation.
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional

import schedule
import typer

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from components.database import DatabaseService
from components.feed_processor import RSSFeedProcessor
from components.scraper import ArticleScraper
from components.summarizer import Summarizer
from components.notifier import EmailNotifier
from components.content_extractor import ContentExtractor
from components.digest_builder import DigestBuilder
from components.news_curator import NewsCurator
from components.digest_service import DigestService

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


def fetch_news() -> None:
    """
    Fetch news articles, extract content, and save to DB (no summarization).
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting news fetch and save...")
    try:
        db_service = DatabaseService()
        feed_processor = RSSFeedProcessor()
        scraper = ArticleScraper()
        content_extractor = ContentExtractor(scraper)
        
        # Get all enabled RSS feeds and their source_ids from the database
        feed_url_to_source_id = {}
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT url, source_id FROM rss_feeds WHERE is_enabled is 1;')
            for url, source_id in cursor.fetchall():
                feed_url_to_source_id[url] = source_id
        all_feeds = list(feed_url_to_source_id.keys())
        
        articles = feed_processor.get_all_articles(all_feeds)
        logger.info(f"Retrieved {len(articles)} articles from {len(all_feeds)} feeds.")
        processed_urls = db_service.get_processed_urls()
        new_articles = [article for article in articles if article.url not in processed_urls]
        logger.info(f"Found {len(new_articles)} new articles to process.")
        for article in new_articles:
            try:
                # First, add the article to the articles table to get an ID
                published_at = None
                if hasattr(article, 'published_date') and article.published_date:
                    try:
                        published_at = article.published_date.isoformat()
                    except Exception:
                        published_at = str(article.published_date)
                
                db_service.mark_as_processed(article.url, {}, published_at, title=article.title, source_id=article.source_id)
                
                # Now extract and save the content
                content_extractor.extract_and_save(article)
                
                logger.info(f"Processed and saved content for: {article.title}")
            except Exception as e:
                logger.error(f"Failed to process article {article.url}: {e}")
        logger.info("News fetch and save complete.")
    except Exception as e:
        logger.error(f"An error occurred during news fetch: {e}")


def summarize_articles() -> None:
    """
    Summarize articles that have been fetched and stored.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting article summarization...")
    try:
        db_service = DatabaseService()
        summarizer = Summarizer()
        
        articles_to_summarize = db_service.get_articles_to_summarize()
        logger.info(f"Found {len(articles_to_summarize)} articles to summarize.")
        
        for article in articles_to_summarize:
            try:
                raw_content = article.get('raw_content')

                if not raw_content:
                    logger.warning(f"Article {article['url']} has no raw content, skipping.")
                    continue

                metadata = summarizer.summarize(raw_content)
                if not metadata or not metadata.get('summary'):
                    logger.warning(f"Could not summarize {article['url']}. Skipping.")
                    continue
                
                db_service.update_article_summary(article['id'], metadata)
                logger.info(f"Summarized and saved: id: {article['id']}, title: {article['title']}")
            except Exception as e:
                logger.error(f"Failed to summarize article {article['url']}: {e}")
        logger.info("Article summarization complete.")
    except Exception as e:
        logger.error(f"An error occurred during article summarization: {e}")


def send_digest(
    email_address: Optional[str] = None,
    force: bool = False,
) -> None:
    """
    Generate and send the digest email for articles in a date range and category list.
    Only send articles that have not already been sent to the recipient.
    Includes a safety switch to prevent sending multiple digests per day unless forced.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting digest generation and sending...")
    
    try:
        # Use DigestService to handle digest generation and sending
        digest_service = DigestService()
        result = digest_service.send_digest_to_user(
            email_address=email_address,
            force=force,
            use_alt_method=False
        )
        
        if result["success"]:
            logger.info(f"Digest sent successfully: {result['message']}")
        else:
            if result.get("reason") == "already_sent_today":
                logger.warning(result["message"])
            else:
                logger.error(f"Failed to send digest: {result['message']}")
                
    except Exception as e:
        logger.error(f"An error occurred during digest sending: {e}")


@app.command(name="fetch-news")
def fetch_news_command(config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")):
    """
    Fetch and process news articles, saving them to the database (no email).
    """
    setup_logging()
    fetch_news(config_path)


@app.command(name="summarize-articles")
def summarize_articles_command(config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")):
    """
    Summarize articles that have been fetched and stored.
    """
    setup_logging()
    summarize_articles(config_path)


@app.command(name="send-digest")
def send_digest_command(
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate the digest but do not send the email"),
    force: bool = typer.Option(False, "--force", help="Force sending the digest even if one has been sent today"),
):
    """
    Generate and send the digest email for articles in a date range and category list.
    """
    setup_logging()

    if dry_run:
        email_address = os.getenv("TEST_EMAIL_ADDRESS")
        send_digest(email_address, force=force)
    else:
        db_service = DatabaseService()
        email_addresses = db_service.get_all_user_email_addresses()
        if not email_addresses:
            logging.getLogger(__name__).info("No user email addresses found in the database.")
            return
        for email in email_addresses:
            try:
                send_digest(email_address=email, force=force)
            except Exception as e:
                logging.getLogger(__name__).error(f"Failed to send digest to {email}: {e}")


@app.command(name="run")
def run_digest(config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")):
    """
    Runs the daily digest generation process.
    """
    setup_logging()
    fetch_news(config_path)

@app.command(name="generate-article-embeddings")
def generate_article_embeddings_command(
):
    """
    Generate OpenAI embeddings for all articles in the database that do not have embeddings yet.
    """
    setup_logging()
    from components.article_clusterer import ArticleClusterer
    logger = logging.getLogger(__name__)
    logger.info("Starting article embedding generation process...")
    try:
        clusterer = ArticleClusterer()
        logger.info("Generating embeddings for articles without embeddings...")
        clusterer.generate_embeddings()
        logger.info("Embedding generation complete.")
    except Exception as e:
        logger.error(f"Error during article embedding generation: {e}")


@app.command(name="full-run")
def full_run_command(
    openai_api_key: str = typer.Option(None, "--openai-api-key", envvar="OPENAI_API_KEY", help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """
    Run the full pipeline: fetch articles, generate embeddings, and send the digest.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("[1/3] Fetching articles...")
    fetch_news()
    logger.info("[2/3] Summarizing articles...")
    summarize_articles()
    logger.info("[3/3] Generating embeddings...")
    if not openai_api_key:
        import os
        openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY must be set in environment or passed as argument.")
        raise typer.Exit(1)
    from components.article_clusterer import ArticleClusterer
    clusterer = ArticleClusterer(openai_api_key=openai_api_key)
    clusterer.generate_embeddings()
    logger.info("Full pipeline complete.")


if __name__ == "__main__":
    app()