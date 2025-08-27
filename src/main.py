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
    Fetch news articles, summarize, and save to DB (no email sending).
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting news fetch and save...")
    try:
        config = load_config(config_path)
        db_service = DatabaseService()
        feed_processor = RSSFeedProcessor()
        scraper = ArticleScraper()
        summarizer = Summarizer(config.gemini)
        content_extractor = ContentExtractor(scraper, summarizer)
        
        # Get all enabled RSS feeds and their source_ids from the database
        feed_url_to_source_id = {}
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT url, source_id FROM rss_feeds WHERE is_enabled is true;')
            for url, source_id in cursor.fetchall():
                feed_url_to_source_id[url] = source_id
        all_feeds = list(feed_url_to_source_id.keys())
        
        articles = feed_processor.get_all_articles(all_feeds)
        # Assign source_id to each article based on its feed_source (which is the feed URL)
        for article in articles:
            article.source_id = feed_url_to_source_id.get(article.feed_source)
        logger.info(f"Retrieved {len(articles)} articles from {len(all_feeds)} feeds.")
        processed_urls = db_service.get_processed_urls()
        new_articles = [article for article in articles if article.url not in processed_urls]
        logger.info(f"Found {len(new_articles)} new articles to process.")
        for article in new_articles:
            try:
                metadata = content_extractor.extract_and_summarize(article)
                if not metadata or not metadata.get('summary'):
                    logger.warning(f"Could not summarize {article.url}. Skipping.")
                    continue
                published_at = None
                if hasattr(article, 'published_date') and article.published_date:
                    try:
                        published_at = article.published_date.isoformat()
                    except Exception:
                        published_at = str(article.published_date)

                db_service.mark_as_processed(article.url, metadata, published_at, title=article.title, source_id=article.source_id)
                logger.info(f"Processed and saved: {article.title}")
            except Exception as e:
                logger.error(f"Failed to process article {article.url}: {e}")
        logger.info("News fetch and save complete.")
    except Exception as e:
        logger.error(f"An error occurred during news fetch: {e}")


def send_digest(
    config_path: Optional[str] = None,
) -> None:
    """
    Generate and send the digest email for articles in a date range and category list.
    Only send articles that have not already been sent to the recipient.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting digest generation and sending...")
    try:
        config = load_config(config_path)
        db_service = DatabaseService()
        email_address = config.email.to

        curator = NewsCurator()
        curated_articles = curator.curate_for_user(email_address)
        if not curated_articles:
            logger.info("No curated articles to send after applying curation rules.")
            return

        # Cluster similar articles
        from components.article_clusterer import ArticleClusterer
        clusterer = ArticleClusterer()
        clustered_curated_articles = []
        used_article_ids = set()
        for article in curated_articles:
            if article['id'] in used_article_ids:
                continue
            cluster = [article]
            used_article_ids.add(article['id'])
            try:
                similar = clusterer.get_similar_articles(article['id'], top_k=5, similarity_threshold=0.55)
                for sim_article in similar:
                    if sim_article['id'] not in used_article_ids:
                        cluster.append(sim_article)
                        used_article_ids.add(sim_article['id'])
            except Exception as e:
                logger.warning(f"Could not get similar articles for {article['id']}: {e}")
            clustered_curated_articles.append(cluster)

        html_digest = DigestBuilder.build_html_digest(clustered_curated_articles)
        notifier = EmailNotifier(config.email.__dict__)
        subject = f"Your Daily Digest for {time.strftime('%Y-%m-%d')}"
        notifier.send_digest(html_digest, email_address, subject)
        # Mark all sent articles in sent_articles table
        digest_id = uuid.uuid4()
        for article in curated_articles:
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


@app.command(name="send-digest")
def send_digest_command(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
):
    """
    Generate and send the digest email for articles in a date range and category list.
    """
    setup_logging()
    send_digest(config_path)


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
    db_path: str = typer.Option("data/digest_history.db", "--db-path", help="Path to the SQLite database file"),
    openai_api_key: str = typer.Option(..., "--openai-api-key", envvar="OPENAI_API_KEY", help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """
    Generate OpenAI embeddings for all articles in the database that do not have embeddings yet.
    """
    setup_logging()
    from components.article_clusterer import ArticleClusterer
    logger = logging.getLogger(__name__)
    logger.info("Starting article embedding generation process...")
    try:
        clusterer = ArticleClusterer(db_path, openai_api_key)
        logger.info("Generating embeddings for articles without embeddings...")
        clusterer.generate_embeddings()
        logger.info("Embedding generation complete.")
    except Exception as e:
        logger.error(f"Error during article embedding generation: {e}")

if __name__ == "__main__":
    app()