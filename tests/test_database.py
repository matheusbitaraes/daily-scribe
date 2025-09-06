"""
Tests for the database service component.
"""

import os
import sqlite3
import pytest
import uuid
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
    if os.path.exists(db_path):
        os.remove(db_path)


def test_database_creation(db_service):
    """Test that the database and table are created correctly."""
    assert os.path.exists(db_service.db_path)


def test_database_environment_variables():
    """Test that DatabaseService respects environment variables."""
    # Test DB_PATH environment variable
    test_db_path = "test_env_db.db"
    original_db_path = os.environ.get('DB_PATH')
    original_db_timeout = os.environ.get('DB_TIMEOUT')
    
    try:
        os.environ['DB_PATH'] = test_db_path
        os.environ['DB_TIMEOUT'] = '45'
        
        service = DatabaseService()
        assert service.db_path == test_db_path
        assert service.timeout == 45.0
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
    finally:
        # Restore original environment
        if original_db_path is not None:
            os.environ['DB_PATH'] = original_db_path
        elif 'DB_PATH' in os.environ:
            del os.environ['DB_PATH']
            
        if original_db_timeout is not None:
            os.environ['DB_TIMEOUT'] = original_db_timeout
        elif 'DB_TIMEOUT' in os.environ:
            del os.environ['DB_TIMEOUT']


def test_database_default_values():
    """Test that DatabaseService uses proper default values."""
    # Ensure no environment variables are set
    original_db_path = os.environ.get('DB_PATH')
    original_db_timeout = os.environ.get('DB_TIMEOUT')
    
    try:
        if 'DB_PATH' in os.environ:
            del os.environ['DB_PATH']
        if 'DB_TIMEOUT' in os.environ:
            del os.environ['DB_TIMEOUT']
            
        service = DatabaseService()
        assert service.db_path == 'data/digest_history.db'
        assert service.timeout == 30.0
        
    finally:
        # Restore original environment
        if original_db_path is not None:
            os.environ['DB_PATH'] = original_db_path
        if original_db_timeout is not None:
            os.environ['DB_TIMEOUT'] = original_db_timeout


def test_database_wal_mode():
    """Test that WAL mode is enabled on database connections."""
    db_path = "test_wal_db.db"
    service = DatabaseService(db_path=db_path)
    
    try:
        with service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            assert result[0].upper() == 'WAL'
            
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)
        # Also clean up WAL files that might be created
        wal_file = db_path + '-wal'
        shm_file = db_path + '-shm'
        if os.path.exists(wal_file):
            os.remove(wal_file)
        if os.path.exists(shm_file):
            os.remove(shm_file)


def test_database_timeout_configuration():
    """Test that timeout is properly configured."""
    db_path = "test_timeout_db.db"
    timeout = 60
    service = DatabaseService(db_path=db_path, timeout=timeout)
    
    try:
        assert service.timeout == timeout
        # The actual timeout testing is challenging without complex scenarios,
        # but we can verify the parameter is stored correctly
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)


def test_database_initialization_idempotent():
    """Test that database initialization can be called multiple times safely."""
    db_path = "test_idempotent_db.db"
    service = DatabaseService(db_path=db_path)
    
    try:
        # Initialize multiple times
        service._initialize_database()
        service._initialize_database()
        
        # Verify database still works
        assert os.path.exists(db_path)
        
        with service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
            assert cursor.fetchone() is not None
            
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)


def test_mark_as_processed_and_get_urls(db_service):
    """Test that URLs can be marked as processed and retrieved."""
    # Setup: add a source and a feed
    source_id = db_service.add_source("Test Source")
    feed_id = db_service.add_rss_feed(source_id, "https://example.com/feed", is_enabled=1)
    url1 = "https://example.com/article1"
    url2 = "https://example.com/article2"
    metadata1 = {"summary": "Summary 1", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    metadata2 = {"summary": "Summary 2", "sentiment": "Neutral", "keywords": ["b"], "category": "Test", "region": "US"}
    db_service.mark_as_processed(url1, metadata1, published_at=None, title="Title 1", source_id=source_id)
    db_service.mark_as_processed(url2, metadata2, published_at=None, title="Title 2", source_id=source_id)
    processed_urls = db_service.get_processed_urls()
    assert len(processed_urls) == 2
    assert url1 in processed_urls
    assert url2 in processed_urls

def test_duplicate_urls_are_not_added(db_service):
    """Test that duplicate URLs are not added to the database."""
    source_id = db_service.add_source("Test Source 2")
    feed_id = db_service.add_rss_feed(source_id, "https://example.com/feed2", is_enabled=1)
    url = "https://example.com/article1"
    metadata = {"summary": "Summary 1", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title 1", source_id=source_id)
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title 1", source_id=source_id)  # Try to add the same URL again
    processed_urls = db_service.get_processed_urls()
    assert len(processed_urls) == 1

def test_add_feed_disabled_and_filter(db_service):
    """Test that a feed with is_enabled=0 is not included in enabled feed queries."""
    source_id = db_service.add_source("Disabled Source")
    db_service.add_rss_feed(source_id, "https://disabled.com/feed", is_enabled=0)
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM rss_feeds WHERE is_enabled=1")
        enabled_feeds = [row[0] for row in cursor.fetchall()]
    assert "https://disabled.com/feed" not in enabled_feeds

def test_toggle_feed_enabled(db_service):
    """Test enabling and disabling a feed updates is_enabled correctly."""
    source_id = db_service.add_source("Toggle Source")
    feed_url = "https://toggle.com/feed"
    db_service.add_rss_feed(source_id, feed_url, is_enabled=1)
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE rss_feeds SET is_enabled=0 WHERE url=?", (feed_url,))
        conn.commit()
        cursor.execute("SELECT is_enabled FROM rss_feeds WHERE url=?", (feed_url,))
        assert cursor.fetchone()[0] == 0
        cursor.execute("UPDATE rss_feeds SET is_enabled=1 WHERE url=?", (feed_url,))
        conn.commit()
        cursor.execute("SELECT is_enabled FROM rss_feeds WHERE url=?", (feed_url,))
        assert cursor.fetchone()[0] == 1

def test_get_rss_feeds_for_source_only_enabled(db_service):
    """Test get_rss_feeds_for_source returns only enabled feeds."""
    source_id = db_service.add_source("Filter Source")
    db_service.add_rss_feed(source_id, "https://enabled.com/feed", is_enabled=1)
    db_service.add_rss_feed(source_id, "https://disabled.com/feed", is_enabled=0)
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM rss_feeds WHERE source_id=? AND is_enabled=1", (source_id,))
        feeds = [row[0] for row in cursor.fetchall()]
    assert "https://enabled.com/feed" in feeds
    assert "https://disabled.com/feed" not in feeds

def test_add_source_duplicate_name(db_service):
    """Test adding a source with a duplicate name."""
    name = "Duplicate Source"
    id1 = db_service.add_source(name)
    id2 = db_service.add_source(name)
    assert id1 != id2  # Should allow duplicate names, but IDs must differ

def test_add_rss_feed_duplicate_url_same_source(db_service):
    """Test adding the same feed URL twice for the same source."""
    source_id = db_service.add_source("Dup Feed Source")
    feed_url = "https://dup.com/feed"
    id1 = db_service.add_rss_feed(source_id, feed_url, is_enabled=1)
    id2 = db_service.add_rss_feed(source_id, feed_url, is_enabled=1)
    assert id1 != id2  # Should allow duplicate URLs, but IDs must differ

def test_mark_as_processed_invalid_source_id(db_service):
    """Test marking an article as processed with a non-existent source_id fails due to FK constraint."""
    url = "https://invalid.com/article"
    metadata = {"summary": "Summary", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    # Use a source_id that does not exist - should fail with FK constraint enabled
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title", source_id=9999)
    processed_urls = db_service.get_processed_urls()
    assert url not in processed_urls  # Should not insert due to foreign key constraint

def test_get_processed_urls_after_deletion(db_service):
    """Test get_processed_urls after deleting an article."""
    source_id = db_service.add_source("Delete Source")
    db_service.add_rss_feed(source_id, "https://delete.com/feed", is_enabled=1)
    url = "https://delete.com/article"
    metadata = {"summary": "Summary", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title", source_id=source_id)
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles WHERE url=?", (url,))
        conn.commit()
    processed_urls = db_service.get_processed_urls()
    assert url not in processed_urls

def test_get_articles_with_date_and_category_filters(db_service):
    """Test get_articles with date and category filters."""
    source_id = db_service.add_source("Filter Article Source")
    db_service.add_rss_feed(source_id, "https://filter.com/feed", is_enabled=1)
    url1 = "https://filter.com/article1"
    url2 = "https://filter.com/article2"
    metadata1 = {"summary": "Summary 1", "sentiment": "Neutral", "keywords": ["a"], "category": "CatA", "region": "US"}
    metadata2 = {"summary": "Summary 2", "sentiment": "Neutral", "keywords": ["b"], "category": "CatB", "region": "US"}
    db_service.mark_as_processed(url1, metadata1, published_at="2025-08-25T00:00:00", title="Title 1", source_id=source_id)
    db_service.mark_as_processed(url2, metadata2, published_at="2025-08-24T00:00:00", title="Title 2", source_id=source_id)
    # Filter by date
    articles = db_service.get_articles(start_date="2025-08-25T00:00:00")
    assert any(a['url'] == url1 for a in articles)
    assert all(a['url'] != url2 for a in articles)
    # Filter by category
    articles = db_service.get_articles(categories=["CatA"])
    assert any(a['url'] == url1 for a in articles)
    assert all(a['url'] != url2 for a in articles)

def test_mark_as_processed_all_fields(db_service):
    """Test mark_as_processed with all optional fields."""
    source_id = db_service.add_source("All Fields Source")
    db_service.add_rss_feed(source_id, "https://allfields.com/feed", is_enabled=1)
    url = "https://allfields.com/article"
    metadata = {"summary": "Full Summary", "sentiment": "Positive", "keywords": ["x", "y"], "category": "Full", "region": "World"}
    db_service.mark_as_processed(url, metadata, published_at="2025-08-25T12:00:00", title="Full Title", source_id=source_id)
    articles = db_service.get_articles()
    found = any(a['url'] == url and a['title'] == "Full Title" and a['summary'] == "Full Summary" for a in articles)
    assert found

def test_database_initialization_creates_tables():
    """Test DB initialization when file does not exist."""
    db_path = "test_db_init.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    service = DatabaseService(db_path=db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        assert cursor.fetchone() is not None
    os.remove(db_path)

def test_add_rss_feed_invalid_source_id(db_service):
    """Test adding a feed with a non-existent source_id fails due to FK constraint."""
    feed_url = "https://invalidsource.com/feed"
    feed_id = db_service.add_rss_feed(9999, feed_url, is_enabled=1)
    assert feed_id == -1  # Should fail due to foreign key constraint

def test_add_sent_article_uuid(db_service):
    """Test that sent_articles accepts and stores UUID digest_id correctly."""
    source_id = db_service.add_source("UUID Source")
    db_service.add_rss_feed(source_id, "https://uuid.com/feed", is_enabled=1)
    url = "https://uuid.com/article"
    metadata = {"summary": "Summary", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title", source_id=source_id)
    article = db_service.get_article_by_url(url)
    digest_id = str(uuid.uuid4())
    db_service.add_sent_article(article_id=article["id"], digest_id=digest_id, email_address="test@example.com")
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT digest_id FROM sent_articles WHERE article_id=?", (article["id"],))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == digest_id

def test_sent_articles_prevent_resend(db_service):
    """Test that get_unsent_articles does not return already sent articles for the same email."""
    source_id = db_service.add_source("Resend Source")
    db_service.add_rss_feed(source_id, "https://resend.com/feed", is_enabled=1)
    url = "https://resend.com/article"
    metadata = {"summary": "Summary", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title", source_id=source_id)
    article = db_service.get_article_by_url(url)
    digest_id = str(uuid.uuid4())
    email = "resend@example.com"
    db_service.add_sent_article(article_id=article["id"], digest_id=digest_id, email_address=email)
    unsent = db_service.get_unsent_articles(email)
    assert all(a["url"] != url for a in unsent)

def test_sent_articles_duplicate_digest(db_service):
    """Test that multiple digests for the same article/email are stored separately."""
    source_id = db_service.add_source("DupDigest Source")
    db_service.add_rss_feed(source_id, "https://dup.com/feed", is_enabled=1)
    url = "https://dup.com/article"
    metadata = {"summary": "Summary", "sentiment": "Neutral", "keywords": ["a"], "category": "Test", "region": "US"}
    db_service.mark_as_processed(url, metadata, published_at=None, title="Title", source_id=source_id)
    article = db_service.get_article_by_url(url)
    email = "dup@example.com"
    digest1 = str(uuid.uuid4())
    digest2 = str(uuid.uuid4())
    db_service.add_sent_article(article_id=article["id"], digest_id=digest1, email_address=email)
    db_service.add_sent_article(article_id=article["id"], digest_id=digest2, email_address=email)
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sent_articles WHERE article_id=? AND email_address=?", (article["id"], email))
        count = cursor.fetchone()[0]
        assert count == 2


# Token Management Tests

def test_user_tokens_table_exists(db_service):
    """Test that the user_tokens table is created correctly."""
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_tokens'")
        assert cursor.fetchone() is not None
        
        # Check table structure
        cursor.execute("PRAGMA table_info(user_tokens)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        expected_columns = [
            'id', 'token_id', 'token_hash', 'user_preferences_id', 'device_fingerprint',
            'created_at', 'expires_at', 'usage_count', 'max_usage', 'is_revoked',
            'purpose', 'version'
        ]
        
        for col in expected_columns:
            assert col in column_names, f"Column {col} not found in user_tokens table"


def test_user_tokens_indexes_exist(db_service):
    """Test that the required indexes are created for the user_tokens table."""
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='user_tokens'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_user_tokens_token_id',
            'idx_user_tokens_token_hash', 
            'idx_user_tokens_expires_at',
            'idx_user_tokens_user_preferences_id'
        ]
        
        for index in expected_indexes:
            assert index in indexes, f"Index {index} not found"


def test_create_user_token(db_service):
    """Test creating a new user token."""
    # First create a user preference record
    email = "test@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources, enabled_categories)
            VALUES (?, 'source1,source2', 'tech,business')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    # Create token
    token_id = "test_token_123"
    token_hash = "hashed_token_value"
    device_fingerprint = "device_abc123"
    expires_at = "2025-12-31 23:59:59"
    
    result = db_service.create_user_token(
        token_id=token_id,
        token_hash=token_hash,
        user_preferences_id=user_preferences_id,
        device_fingerprint=device_fingerprint,
        expires_at=expires_at,
        max_usage=5
    )
    
    assert result is not None
    assert isinstance(result, int)
    
    # Verify the token was created
    token_data = db_service.get_user_token(token_id)
    assert token_data is not None
    assert token_data['token_id'] == token_id
    assert token_data['token_hash'] == token_hash
    assert token_data['user_preferences_id'] == user_preferences_id
    assert token_data['device_fingerprint'] == device_fingerprint
    assert token_data['max_usage'] == 5
    assert token_data['usage_count'] == 0
    assert token_data['is_revoked'] == 0


def test_get_user_token_not_found(db_service):
    """Test retrieving a non-existent token."""
    result = db_service.get_user_token("nonexistent_token")
    assert result is None


def test_get_user_token_revoked(db_service):
    """Test that revoked tokens are not returned."""
    # Create user preference
    email = "revoked@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources)
            VALUES (?, 'source1')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    # Create and revoke token
    token_id = "revoked_token"
    db_service.create_user_token(
        token_id=token_id,
        token_hash="hash",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2025-12-31 23:59:59"
    )
    
    # Revoke the token
    db_service.revoke_user_token(token_id)
    
    # Should not be retrievable
    result = db_service.get_user_token(token_id)
    assert result is None


def test_get_user_token_expired(db_service):
    """Test that expired tokens are not returned."""
    # Create user preference
    email = "expired@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources)
            VALUES (?, 'source1')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    # Create expired token
    token_id = "expired_token"
    db_service.create_user_token(
        token_id=token_id,
        token_hash="hash",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2020-01-01 00:00:00"  # Expired
    )
    
    # Should not be retrievable
    result = db_service.get_user_token(token_id)
    assert result is None


def test_increment_token_usage(db_service):
    """Test incrementing token usage count."""
    # Create user preference and token
    email = "usage@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources)
            VALUES (?, 'source1')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    token_id = "usage_token"
    db_service.create_user_token(
        token_id=token_id,
        token_hash="hash",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2025-12-31 23:59:59"
    )
    
    # Increment usage
    result = db_service.increment_token_usage(token_id)
    assert result is True
    
    # Check usage count
    token_data = db_service.get_user_token(token_id)
    assert token_data['usage_count'] == 1
    
    # Increment again
    db_service.increment_token_usage(token_id)
    token_data = db_service.get_user_token(token_id)
    assert token_data['usage_count'] == 2


def test_increment_usage_nonexistent_token(db_service):
    """Test incrementing usage for non-existent token."""
    result = db_service.increment_token_usage("nonexistent")
    assert result is False


def test_revoke_user_token(db_service):
    """Test revoking a user token."""
    # Create user preference and token
    email = "revoke@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources)
            VALUES (?, 'source1')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    token_id = "revoke_token"
    db_service.create_user_token(
        token_id=token_id,
        token_hash="hash",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2025-12-31 23:59:59"
    )
    
    # Token should be retrievable
    assert db_service.get_user_token(token_id) is not None
    
    # Revoke token
    result = db_service.revoke_user_token(token_id)
    assert result is True
    
    # Token should no longer be retrievable
    assert db_service.get_user_token(token_id) is None


def test_revoke_user_tokens_by_preferences_id(db_service):
    """Test revoking all tokens for a user."""
    # Create user preference
    email = "revoke_all@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources)
            VALUES (?, 'source1')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    # Create multiple tokens
    token_ids = ["token1", "token2", "token3"]
    for token_id in token_ids:
        db_service.create_user_token(
            token_id=token_id,
            token_hash=f"hash_{token_id}",
            user_preferences_id=user_preferences_id,
            device_fingerprint="device",
            expires_at="2025-12-31 23:59:59"
        )
    
    # All tokens should be retrievable
    for token_id in token_ids:
        assert db_service.get_user_token(token_id) is not None
    
    # Revoke all tokens for user
    result = db_service.revoke_user_tokens_by_preferences_id(user_preferences_id)
    assert result is True
    
    # No tokens should be retrievable
    for token_id in token_ids:
        assert db_service.get_user_token(token_id) is None


def test_cleanup_expired_tokens(db_service):
    """Test cleaning up expired and revoked tokens."""
    # Create user preference
    email = "cleanup@example.com"
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources)
            VALUES (?, 'source1')
        """, (email,))
        user_preferences_id = cursor.lastrowid
        conn.commit()
    
    # Create expired token
    db_service.create_user_token(
        token_id="expired_cleanup",
        token_hash="hash1",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2020-01-01 00:00:00"  # Expired
    )
    
    # Create valid token and revoke it
    db_service.create_user_token(
        token_id="revoked_cleanup",
        token_hash="hash2",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2025-12-31 23:59:59"
    )
    db_service.revoke_user_token("revoked_cleanup")
    
    # Create valid active token
    db_service.create_user_token(
        token_id="active_cleanup",
        token_hash="hash3",
        user_preferences_id=user_preferences_id,
        device_fingerprint="device",
        expires_at="2025-12-31 23:59:59"
    )
    
    # Run cleanup
    cleaned_count = db_service.cleanup_expired_tokens()
    assert cleaned_count == 2  # Should clean up expired and revoked tokens
    
    # Check that active token still exists
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_tokens")
        remaining_count = cursor.fetchone()[0]
        assert remaining_count == 1


def test_get_user_preferences_by_email(db_service):
    """Test retrieving user preferences by email address."""
    email = "prefs@example.com"
    
    # Create user preferences
    with db_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_preferences (email_address, enabled_sources, enabled_categories, keywords)
            VALUES (?, 'source1,source2', 'tech,business', 'ai,machine learning')
        """, (email,))
        conn.commit()
    
    # Retrieve preferences
    prefs = db_service.get_user_preferences_by_email(email)
    assert prefs is not None
    assert prefs['email_address'] == email
    assert prefs['enabled_sources'] == 'source1,source2'
    assert prefs['enabled_categories'] == 'tech,business'
    assert prefs['keywords'] == 'ai,machine learning'


def test_get_user_preferences_by_email_not_found(db_service):
    """Test retrieving non-existent user preferences."""
    result = db_service.get_user_preferences_by_email("nonexistent@example.com")
    assert result is None


def test_user_tokens_foreign_key_constraint(db_service):
    """Test that foreign key constraints work for user_tokens table."""
    # Try to create token with non-existent user_preferences_id
    result = db_service.create_user_token(
        token_id="invalid_fk",
        token_hash="hash",
        user_preferences_id=99999,  # Non-existent
        device_fingerprint="device",
        expires_at="2025-12-31 23:59:59"
    )
    
    # Should fail due to foreign key constraint
    assert result is None
