"""
Database migration utilities for Daily Scribe application.

This module provides database migration functionality to handle 
schema updates and data migrations safely.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


class DatabaseMigrator:
    """Handles database schema migrations."""

    def __init__(self, db_path: str):
        """
        Initialize the database migrator.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_migrations_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection to the SQLite database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_migrations_table(self) -> None:
        """Create the migrations tracking table if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_name TEXT NOT NULL UNIQUE,
                        applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    );
                """)
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating migrations table: {e}")
            raise

    def migration_applied(self, migration_name: str) -> bool:
        """
        Check if a migration has already been applied.
        
        Args:
            migration_name: Name of the migration
            
        Returns:
            True if migration was already applied, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                    (migration_name,)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.error(f"Error checking migration status: {e}")
            return False

    def record_migration(self, migration_name: str, description: str = "") -> None:
        """
        Record that a migration has been applied.
        
        Args:
            migration_name: Name of the migration
            description: Optional description of the migration
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO schema_migrations (migration_name, description)
                    VALUES (?, ?)
                """, (migration_name, description))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error recording migration: {e}")
            raise

    def add_user_tokens_table(self) -> bool:
        """
        Migration to add the user_tokens table for secure preference access.
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "001_add_user_tokens_table"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create user_tokens table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_tokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_id TEXT NOT NULL UNIQUE,
                        token_hash TEXT NOT NULL,
                        user_preferences_id INTEGER NOT NULL,
                        device_fingerprint TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        usage_count INTEGER NOT NULL DEFAULT 0,
                        max_usage INTEGER NOT NULL DEFAULT 10,
                        is_revoked BOOLEAN NOT NULL DEFAULT 0,
                        purpose TEXT NOT NULL DEFAULT 'email_preferences',
                        version INTEGER NOT NULL DEFAULT 1,
                        FOREIGN KEY (user_preferences_id) REFERENCES user_preferences(id) ON DELETE CASCADE
                    );
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_token_id ON user_tokens(token_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_token_hash ON user_tokens(token_hash);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_expires_at ON user_tokens(expires_at);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_user_preferences_id ON user_tokens(user_preferences_id);")
                
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    "Add user_tokens table for secure email preference access"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def add_summary_pt_column(self) -> bool:
        """
        Migration to add the summary_pt column to articles table for Portuguese summaries.
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "002_add_summary_pt_column"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Add summary_pt column to articles table
                cursor.execute("""
                    ALTER TABLE articles ADD COLUMN summary_pt TEXT;
                """)
                
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    "Add summary_pt column to articles table for Portuguese summaries"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def add_title_pt_column(self) -> bool:
        """
        Migration to add the title_pt column to articles table for Portuguese titles.
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "008_add_title_pt_column"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Add title_pt column to articles table
                cursor.execute("""
                    ALTER TABLE articles ADD COLUMN title_pt TEXT;
                """)
                
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    "Add title_pt column to articles table for Portuguese titles"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def add_subscription_tables(self) -> bool:
        """
        Migration to add tables for managing user subscriptions and verification tokens.
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "005_create_subscription_tables"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create pending_subscriptions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pending_subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        verification_token TEXT NOT NULL UNIQUE,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        subscribed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pending_subscriptions_email ON pending_subscriptions(email);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pending_subscriptions_token ON pending_subscriptions(verification_token);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pending_subscriptions_expires_at ON pending_subscriptions(expires_at);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);")
                
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    "Add pending_subscriptions and users tables for subscription management"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def migrate_user_preferences_to_users(self) -> bool:
        """
        Migration to add users from user_preferences table to users table with is_active = 1.
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "006_migrate_user_preferences_to_users"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all unique email addresses from user_preferences that don't exist in users table
                cursor.execute("""
                    INSERT INTO users (email, is_active, subscribed_at, updated_at)
                    SELECT DISTINCT up.email_address, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    FROM user_preferences up
                    LEFT JOIN users u ON up.email_address = u.email
                    WHERE u.email IS NULL AND up.email_address IS NOT NULL AND up.email_address != ''
                """)
                
                migrated_count = cursor.rowcount
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    f"Migrate {migrated_count} users from user_preferences to users table with is_active = 1"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}, migrated {migrated_count} users")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def add_news_scoring_fields(self) -> bool:
        """
        Migration to add urgency_score, impact_score, and subject_pt columns to articles table.
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "007_add_news_scoring_fields"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Add urgency_score column to articles table
                cursor.execute("""
                    ALTER TABLE articles ADD COLUMN urgency_score INTEGER;
                """)
                
                # Add impact_score column to articles table
                cursor.execute("""
                    ALTER TABLE articles ADD COLUMN impact_score INTEGER;
                """)
                
                # Add subject_pt column to articles table
                cursor.execute("""
                    ALTER TABLE articles ADD COLUMN subject_pt TEXT;
                """)
                
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    "Add urgency_score, impact_score, and subject_pt columns to articles table for news scoring"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def convert_scoring_fields_to_100_scale(self) -> bool:
        """
        Migration to convert urgency_score and impact_score from 1-5 scale to 0-100 scale.
        
        Conversion logic:
        - 1 -> 10 (0-20 range, middle value)
        - 2 -> 30 (21-40 range, middle value)
        - 3 -> 50 (41-60 range, middle value)
        - 4 -> 70 (61-80 range, middle value)
        - 5 -> 90 (81-100 range, middle value)
        
        Returns:
            True if successful, False otherwise
        """
        migration_name = "008_convert_scoring_fields_to_100_scale"
        
        if self.migration_applied(migration_name):
            self.logger.info(f"Migration {migration_name} already applied, skipping")
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Update urgency_score: convert 1-5 scale to 0-100 scale
                cursor.execute("""
                    UPDATE articles 
                    SET urgency_score = CASE 
                        WHEN urgency_score = 1 THEN 10
                        WHEN urgency_score = 2 THEN 30
                        WHEN urgency_score = 3 THEN 50
                        WHEN urgency_score = 4 THEN 70
                        WHEN urgency_score = 5 THEN 90
                        ELSE urgency_score
                    END
                    WHERE urgency_score IS NOT NULL AND urgency_score BETWEEN 1 AND 5;
                """)
                
                # Update impact_score: convert 1-5 scale to 0-100 scale
                cursor.execute("""
                    UPDATE articles 
                    SET impact_score = CASE 
                        WHEN impact_score = 1 THEN 10
                        WHEN impact_score = 2 THEN 30
                        WHEN impact_score = 3 THEN 50
                        WHEN impact_score = 4 THEN 70
                        WHEN impact_score = 5 THEN 90
                        ELSE impact_score
                    END
                    WHERE impact_score IS NOT NULL AND impact_score BETWEEN 1 AND 5;
                """)
                
                conn.commit()
                
                # Record the migration
                self.record_migration(
                    migration_name, 
                    "Convert urgency_score and impact_score from 1-5 scale to 0-100 scale"
                )
                
                self.logger.info(f"Successfully applied migration: {migration_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def run_all_migrations(self) -> bool:
        """
        Run all pending migrations.
        
        Returns:
            True if all migrations successful, False otherwise
        """
        try:
            # Add future migrations here
            migrations = [
                self.add_user_tokens_table,
                self.add_summary_pt_column,
                self.add_subscription_tables,
                self.migrate_user_preferences_to_users,
                self.add_news_scoring_fields,
                self.add_title_pt_column,
                self.convert_scoring_fields_to_100_scale,
            ]
            
            for migration in migrations:
                if not migration():
                    return False
            
            self.logger.info("All migrations completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running migrations: {e}")
            return False


def migrate_database(db_path: Optional[str] = None) -> bool:
    """
    Convenience function to run all database migrations.
    
    Args:
        db_path: Path to database file, defaults to environment variable or default path
        
    Returns:
        True if successful, False otherwise
    """
    import os
    
    if db_path is None:
        db_path = os.getenv('DB_PATH', 'data/digest_history.db')
    
    migrator = DatabaseMigrator(db_path)
    return migrator.run_all_migrations()


if __name__ == "__main__":
    # Run migrations when called directly
    logging.basicConfig(level=logging.INFO)
    success = migrate_database()
    if success:
        print("Migrations completed successfully")
    else:
        print("Migration failed")
        exit(1)
