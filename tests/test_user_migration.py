"""
Unit tests for the user preferences to users migration.
"""

import tempfile
import sqlite3
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.migrations import DatabaseMigrator


class TestUserPreferencesToUsersMigration:
    """Test cases for the user preferences to users migration."""

    def setup_method(self):
        """Set up test database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create a basic database structure
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create user_preferences table
            cursor.execute("""
                CREATE TABLE user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_address TEXT,
                    enabled_sources TEXT,
                    enabled_categories TEXT,
                    max_news_per_category INTEGER DEFAULT 10,
                    keywords TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create users table
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    subscribed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()

    def teardown_method(self):
        """Clean up test database after each test."""
        Path(self.db_path).unlink(missing_ok=True)

    def test_migration_with_new_users(self):
        """Test migration when user_preferences has users not in users table."""
        # Add test data to user_preferences
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (email_address) VALUES 
                ('user1@example.com'),
                ('user2@example.com'),
                ('user3@example.com')
            """)
            conn.commit()
        
        # Run migration
        migrator = DatabaseMigrator(self.db_path)
        result = migrator.migrate_user_preferences_to_users()
        
        assert result is True
        
        # Check that users were migrated
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE is_active = 1 ORDER BY email")
            users = [row[0] for row in cursor.fetchall()]
            
            expected_users = ['user1@example.com', 'user2@example.com', 'user3@example.com']
            assert users == expected_users

    def test_migration_with_existing_users(self):
        """Test migration when some users already exist in users table."""
        # Add test data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Add to user_preferences
            cursor.execute("""
                INSERT INTO user_preferences (email_address) VALUES 
                ('existing@example.com'),
                ('new@example.com')
            """)
            
            # Add one user to users table already
            cursor.execute("""
                INSERT INTO users (email, is_active) VALUES 
                ('existing@example.com', 1)
            """)
            
            conn.commit()
        
        # Run migration
        migrator = DatabaseMigrator(self.db_path)
        result = migrator.migrate_user_preferences_to_users()
        
        assert result is True
        
        # Check that only new user was added
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE is_active = 1 ORDER BY email")
            users = [row[0] for row in cursor.fetchall()]
            
            expected_users = ['existing@example.com', 'new@example.com']
            assert users == expected_users

    def test_migration_with_empty_emails(self):
        """Test migration handles empty/null email addresses correctly."""
        # Add test data with some empty emails
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (email_address) VALUES 
                ('valid@example.com'),
                (''),
                (NULL)
            """)
            conn.commit()
        
        # Run migration
        migrator = DatabaseMigrator(self.db_path)
        result = migrator.migrate_user_preferences_to_users()
        
        assert result is True
        
        # Check that only valid email was migrated
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE is_active = 1")
            users = [row[0] for row in cursor.fetchall()]
            
            assert users == ['valid@example.com']

    def test_migration_idempotent(self):
        """Test that running migration multiple times doesn't cause issues."""
        # Add test data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (email_address) VALUES 
                ('test@example.com')
            """)
            conn.commit()
        
        # Run migration twice
        migrator = DatabaseMigrator(self.db_path)
        result1 = migrator.migrate_user_preferences_to_users()
        result2 = migrator.migrate_user_preferences_to_users()
        
        assert result1 is True
        assert result2 is True  # Should skip because already applied
        
        # Check that user exists only once
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'test@example.com'")
            count = cursor.fetchone()[0]
            
            assert count == 1

    def test_migration_with_duplicate_emails_in_preferences(self):
        """Test migration handles duplicate emails in user_preferences correctly."""
        # Add test data with duplicates
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (email_address) VALUES 
                ('duplicate@example.com'),
                ('duplicate@example.com'),
                ('unique@example.com')
            """)
            conn.commit()
        
        # Run migration
        migrator = DatabaseMigrator(self.db_path)
        result = migrator.migrate_user_preferences_to_users()
        
        assert result is True
        
        # Check that each email exists only once in users table
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email, COUNT(*) FROM users GROUP BY email")
            users_counts = cursor.fetchall()
            
            # Should have 2 unique users, each with count 1
            assert len(users_counts) == 2
            for email, count in users_counts:
                assert count == 1
                assert email in ['duplicate@example.com', 'unique@example.com']


if __name__ == '__main__':
    pytest.main([__file__])
