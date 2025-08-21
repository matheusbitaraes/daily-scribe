"""
Database service for Daily Scribe application.

This module handles all interactions with the SQLite database,
including storing and retrieving processed article URLs.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional


class DatabaseService:
    """Handles all interactions with the SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database service.

        Args:
            db_path: Path to the SQLite database file. If None, defaults to 'data/digest_history.db'.
        """
        self.db_path = db_path or "data/digest_history.db"
        self.logger = logging.getLogger(__name__)
        self._create_table_if_not_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.

        Returns:
            A SQLite database connection.
        """
        # Ensure the data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _create_table_if_not_exists(self) -> None:
        """
        Create the 'articles' table if it doesn't already exist.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL UNIQUE,
                        summary TEXT,
                        processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating database table: {e}")
            raise

    def get_processed_urls(self) -> List[str]:
        """
        Get a list of all processed article URLs from the database.

        Returns:
            A list of processed article URLs.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM articles")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting processed URLs from database: {e}")
            return []

    def mark_as_processed(self, url: str, summary: str) -> None:
        """
        Mark an article as processed by storing its URL and summary in the database.

        Args:
            url: The URL of the article to mark as processed.
            summary: The summary of the article.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO articles (url, summary) VALUES (?, ?)", (url, summary))
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Article with URL {url} has already been processed.")
        except sqlite3.Error as e:
            self.logger.error(f"Error marking article as processed in database: {e}")
