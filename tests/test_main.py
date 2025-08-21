"""
Tests for the main application entry point.
"""

from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import generate_digest


@patch('main.load_config')
@patch('main.DatabaseService')
@patch('main.RSSFeedProcessor')
@patch('main.ContentExtractor')
def test_generate_digest(
    mock_content_extractor, mock_feed_processor, mock_db_service, mock_load_config
):
    """Test the daily digest generation process."""
    # Mock configuration
    mock_config = Mock()
    mock_config.rss_feeds = ["https://example.com/rss.xml"]
    mock_load_config.return_value = mock_config

    # Mock database
    mock_db_instance = mock_db_service.return_value
    mock_db_instance.get_processed_urls.return_value = []

    # Mock feed processor
    mock_feed_instance = mock_feed_processor.return_value
    mock_feed_instance.get_all_articles.return_value = [
        Mock(title='Article 1', url='https://example.com/article1', description="RSS content for article 1"),
        Mock(title='Article 2', url='https://example.com/article2', description="RSS content for article 2"),
    ]

    # Mock content extractor
    mock_extractor_instance = mock_content_extractor.return_value
    mock_extractor_instance.extract_and_summarize.return_value = "This is a summary."

    # Run the digest generation
    generate_digest()

    # Assert that the correct methods were called
    mock_load_config.assert_called_once()
    mock_db_service.assert_called_once()
    mock_feed_processor.assert_called_once()
    mock_content_extractor.assert_called_once()

    assert mock_feed_instance.get_all_articles.call_count == 1
    assert mock_extractor_instance.extract_and_summarize.call_count == 2
    assert mock_db_instance.mark_as_processed.call_count == 2
