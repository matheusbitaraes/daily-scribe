"""
Tests for the database service component.
"""

import os
import sqlite3
import pytest
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.database import DatabaseService


@pytest.fixture
def db_service():
    """Create a database service with a temporary database for testing."""
    db_path = "test_digest_history.db"
    service = DatabaseService(db_path=db_path)
    yield service
    # Clean up the temporary database file
    os.remove(db_path)


def test_database_creation(db_service):
    """Test that the database and table are created correctly."""
    assert os.path.exists(db_service.db_path)
    
    with sqlite3.connect(db_service.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        assert cursor.fetchone() is not None

def test_mark_as_processed_and_get_urls(db_service):
    """Test that URLs can be marked as processed and retrieved."""
    url1 = "https://example.com/article1"
    url2 = "https://example.com/article2"
    summary1 = "Summary 1"
    summary2 = "Summary 2"
    
    db_service.mark_as_processed(url1, summary1)
    db_service.mark_as_processed(url2, summary2)
    
    processed_urls = db_service.get_processed_urls()
    
    assert len(processed_urls) == 2
    assert url1 in processed_urls
    assert url2 in processed_urls

def test_duplicate_urls_are_not_added(db_service):
    """Test that duplicate URLs are not added to the database."""
    url = "https://example.com/article1"
    summary = "Summary 1"
    
    db_service.mark_as_processed(url, summary)
    db_service.mark_as_processed(url, summary)  # Try to add the same URL again
    
    processed_urls = db_service.get_processed_urls()
    
    assert len(processed_urls) == 1
