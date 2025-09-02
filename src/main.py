"""
Main entry point for Daily Scribe application.

This module handles the scheduling and execution of the daily digest generation.
"""

import sys
import logging
import time
import uuid
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
from components.digest_builder import DigestBuilder
from components.news_curator import NewsCurator

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


def fetch_news(config_path: Optional[str] = None) -> None:
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


def summarize_articles(config_path: Optional[str] = None) -> None:
    """
    Summarize articles that have been fetched and stored.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting article summarization...")
    try:
        config = load_config(config_path)
        db_service = DatabaseService()
        summarizer = Summarizer(config.gemini)
        
        articles_to_summarize = db_service.get_articles_to_summarize()
        logger.info(f"Found {len(articles_to_summarize)} articles to summarize.")
        
        for article in articles_to_summarize:
            try:
                metadata = summarizer.summarize(article['raw_content'])
                if not metadata or not metadata.get('summary'):
                    logger.warning(f"Could not summarize {article['url']}. Skipping.")
                    continue
                
                db_service.update_article_summary(article['id'], metadata)
                logger.info(f"Summarized and saved: {article['url']}")
            except Exception as e:
                logger.error(f"Failed to summarize article {article['url']}: {e}")
        logger.info("Article summarization complete.")
    except Exception as e:
        logger.error(f"An error occurred during article summarization: {e}")


def send_digest(
    config_path: Optional[str] = None,
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
        config = load_config(config_path)
        db_service = DatabaseService()
        email_address = email_address or config.email.to

        # Safety switch: check if user has received a digest today
        if not force and db_service.has_user_received_digest_today(email_address):
            logger.warning(f"Digest already sent to {email_address} today. Use --force to override.")
            return

        # Update user embedding before curation
        from components.article_clusterer import ArticleClusterer
        clusterer = ArticleClusterer()
        clusterer.update_user_embedding(email_address)

        curator = NewsCurator()
        clustered_curated_articles = curator.curate_and_cluster_for_user(email_address)
        if not clustered_curated_articles:
            logger.info("No curated articles to send after applying curation rules.")
            return

        html_digest = DigestBuilder.build_html_digest(clustered_curated_articles)
        notifier = EmailNotifier(config.email.__dict__)
        subject = f"Your Daily Digest for {time.strftime('%Y-%m-%d')} [BETA]"
        notifier.send_digest(html_digest, email_address, subject)
        # Mark all sent articles in sent_articles table
        digest_id = uuid.uuid4()
        all_sent_articles = [article for cluster in clustered_curated_articles for article in cluster]
        for article in all_sent_articles:
            db_article = db_service.get_article_by_url(article['url'])
            if db_article:
                db_service.add_sent_article(db_article['id'], digest_id=digest_id, email_address=email_address)
        logger.info("Digest generated and sent successfully.")
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
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate the digest but do not send the email"),
    force: bool = typer.Option(False, "--force", help="Force sending the digest even if one has been sent today"),
):
    """
    Generate and send the digest email for articles in a date range and category list.
    """
    setup_logging()

    if dry_run:
        send_digest(config_path, force=force)
    else:
        db_service = DatabaseService()
        email_addresses = db_service.get_all_user_email_addresses()
        if not email_addresses:
            logging.getLogger(__name__).info("No user email addresses found in the database.")
            return
        for email in email_addresses:
            try:
                send_digest(config_path, email_address=email, force=force)
            except Exception as e:
                logging.getLogger(__name__).error(f"Failed to send digest to {email}: {e}")


@app.command(name="run")
def run_digest(config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")):
    """
    Runs the daily digest generation process.
    """
    setup_logging()
    fetch_news(config_path)


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
        schedule.every().day.at(schedule_time).do(fetch_news, config_path=config_path)

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
    config_path: str = typer.Option("config.json", "--config", "-c", help="Path to configuration file"),
    openai_api_key: str = typer.Option(None, "--openai-api-key", envvar="OPENAI_API_KEY", help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """
    Run the full pipeline: fetch articles, generate embeddings, and send the digest.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("[1/3] Fetching articles...")
    fetch_news(config_path)
    logger.info("[2/3] Summarizing articles...")
    summarize_articles(config_path)
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