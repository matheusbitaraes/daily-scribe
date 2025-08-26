"""
Tests for the main application entry point.
"""

from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import fetch_news, send_digest, fetch_news_command, send_digest_command, run_digest, schedule_digest
import typer
import logging


@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news(
    mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config
):
    """Test the news fetching and processing logic."""
    # Mock configuration
    mock_config = Mock()
    mock_config.gemini = Mock()
    mock_load_config.return_value = mock_config

    # Mock database
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []

    # Mock feed processor
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="RSS content for article 1", feed_source="https://example.com/rss.xml"),
        Mock(title='Article 2', url='https://example.com/article2', description="RSS content for article 2", feed_source="https://example.com/rss.xml"),
    ]

    # Mock content extractor
    mock_extractor_instance = mock_content_extractor.return_value
    mock_extractor_instance.extract_and_summarize.return_value = {"summary": "This is a summary."}

    # Patch the DB connection to return a valid feed_url_to_source_id mapping
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)],  # feeds
        []  # processed_urls
    ]

    # Run the fetch_news process
    fetch_news()

    # Assert that the correct methods were called
    mock_load_config.assert_called_once()
    mock_db_service.assert_called_once()
    mock_feed_processor.assert_called_once()
    mock_content_extractor.assert_called_once()

    assert mock_feed_instance.get_all_articles.call_count == 1
    assert mock_extractor_instance.extract_and_summarize.call_count == 2
    assert mock_db_instance.mark_as_processed.call_count == 2


@patch('main.load_config', side_effect=Exception("Config error"))
def test_fetch_news_config_error(mock_load_config):
    """Test fetch_news handles config loading exception."""
    fetch_news()
    mock_load_config.assert_called_once()

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_no_new_articles(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config):
    """Test fetch_news when all articles are already processed."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = ["https://example.com/article1", "https://example.com/article2"]
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="desc", feed_source="https://example.com/rss.xml"),
        Mock(title='Article 2', url='https://example.com/article2', description="desc", feed_source="https://example.com/rss.xml"),
    ]
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    fetch_news()
    assert mock_db_instance.mark_as_processed.call_count == 0

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_no_enabled_feeds(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config):
    """Test fetch_news when there are no enabled feeds."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [[], []]
    fetch_news()
    # get_all_articles is called with an empty list, so call_count is 1
    assert mock_feed_processor.return_value.get_all_articles.call_count == 1

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_article_missing_feed_source(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config):
    """Test fetch_news with article missing feed_source."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="desc", feed_source=None),
    ]
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    fetch_news()
    assert mock_db_instance.mark_as_processed.call_count == 1

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_no_summary(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config):
    """Test fetch_news skips article if no summary is returned."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="desc", feed_source="https://example.com/rss.xml"),
    ]
    mock_content_extractor.return_value.extract_and_summarize.return_value = {}
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    fetch_news()
    assert mock_db_instance.mark_as_processed.call_count == 0

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_missing_published_date(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config):
    """Test fetch_news with article missing published_date."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []
    article = Mock(title='Article 1', url='https://example.com/article1', description="desc", feed_source="https://example.com/rss.xml")
    delattr(article, 'published_date')
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [article]
    mock_content_extractor.return_value.extract_and_summarize.return_value = {"summary": "ok"}
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    fetch_news()
    assert mock_db_instance.mark_as_processed.call_count == 1

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_db_error_on_mark(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config, caplog):
    """Test fetch_news logs error if mark_as_processed raises DB error."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="desc", feed_source="https://example.com/rss.xml"),
    ]
    mock_content_extractor.return_value.extract_and_summarize.return_value = {"summary": "ok"}
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    mock_db_instance.mark_as_processed.side_effect = Exception("DB error")
    with caplog.at_level(logging.ERROR):
        fetch_news()
    assert any("Failed to process article" in r for r in caplog.text.splitlines())

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_fetch_news_content_extractor_exception(mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config, caplog):
    """Test fetch_news logs error if extract_and_summarize raises exception."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="desc", feed_source="https://example.com/rss.xml"),
    ]
    mock_content_extractor.return_value.extract_and_summarize.side_effect = Exception("Extractor error")
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    with caplog.at_level(logging.ERROR):
        fetch_news()
    assert any("Failed to process article" in r for r in caplog.text.splitlines())

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
def test_fetch_news_feed_fetch_exception(mock_feed_processor, mock_db_service, mock_load_config, caplog):
    """Test fetch_news logs error if get_all_articles raises exception."""
    mock_config = Mock(); mock_config.gemini = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance._get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.side_effect = [
        [("https://example.com/rss.xml", 1)], []
    ]
    mock_feed_processor.return_value.get_all_articles.side_effect = Exception("Feed error")
    with caplog.at_level(logging.ERROR):
        fetch_news()
    assert any("An error occurred during news fetch" in r for r in caplog.text.splitlines())

@patch('main.load_config')
@patch('main.DatabaseService')
def test_send_digest_no_articles(mock_db_service, mock_load_config, caplog):
    """Test send_digest logs info if no articles found for filters."""
    mock_config = Mock(); mock_config.email = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_articles.return_value = []
    with caplog.at_level(logging.INFO):
        send_digest()
    assert any("No articles found for the given filters" in r for r in caplog.text.splitlines())

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.DigestBuilder')
@patch('main.EmailNotifier')
def test_send_digest_happy_path(mock_email_notifier, mock_digest_builder, mock_db_service, mock_load_config):
    """Test send_digest happy path sends email."""
    mock_config = Mock(); mock_config.email = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_articles.return_value = [{"url": "u", "link": "u"}]
    mock_digest_builder.build_html_digest.return_value = "html"
    mock_email_notifier.return_value.send_digest.return_value = None
    send_digest()
    assert mock_email_notifier.return_value.send_digest.called

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.DigestBuilder')
@patch('main.EmailNotifier')
def test_send_digest_email_exception(mock_email_notifier, mock_digest_builder, mock_db_service, mock_load_config, caplog):
    """Test send_digest logs error if email sending fails."""
    mock_config = Mock(); mock_config.email = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_articles.return_value = [{"url": "u", "link": "u"}]
    mock_digest_builder.build_html_digest.return_value = "html"
    mock_email_notifier.return_value.send_digest.side_effect = Exception("Email error")
    with caplog.at_level(logging.ERROR):
        send_digest()
    assert any("An error occurred during digest sending" in r for r in caplog.text.splitlines())

@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.DigestBuilder')
def test_send_digest_digest_builder_exception(mock_digest_builder, mock_db_service, mock_load_config, caplog):
    """Test send_digest logs error if digest builder fails."""
    mock_config = Mock(); mock_config.email = Mock(); mock_load_config.return_value = mock_config
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_articles.return_value = [{"url": "u", "link": "u"}]
    mock_digest_builder.build_html_digest.side_effect = Exception("Digest error")
    with caplog.at_level(logging.ERROR):
        send_digest()
    assert any("An error occurred during digest sending" in r for r in caplog.text.splitlines())

@patch('main.load_config', side_effect=Exception("Config error"))
def test_send_digest_config_error(mock_load_config, caplog):
    """Test send_digest logs error if config loading fails."""
    with caplog.at_level(logging.ERROR):
        send_digest()
    assert any("An error occurred during digest sending" in r for r in caplog.text.splitlines())

# CLI command tests (smoke)
def test_fetch_news_command(monkeypatch):
    called = {}
    def fake_fetch_news(config_path=None):
        called['fetch'] = config_path
    monkeypatch.setattr('main.fetch_news', fake_fetch_news)
    fetch_news_command(config_path='foo.json')
    assert called['fetch'] == 'foo.json'

def test_send_digest_command(monkeypatch):
    called = {}
    def fake_send_digest(config_path=None, start_date=None, end_date=None, categories=None):
        called['args'] = (config_path, start_date, end_date, categories)
    monkeypatch.setattr('main.send_digest', fake_send_digest)
    send_digest_command(config_path='foo.json', start_date='2025-08-25', end_date='2025-08-26', categories='A,B')
    assert called['args'] == ('foo.json', '2025-08-25', '2025-08-26', 'A,B')

# The run_digest and schedule_digest commands are wrappers; test they call fetch_news
@patch('main.fetch_news')
def test_run_digest_command(mock_fetch_news):
    run_digest(config_path='foo.json')
    mock_fetch_news.assert_called_once_with('foo.json')
