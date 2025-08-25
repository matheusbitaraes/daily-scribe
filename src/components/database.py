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
        Create the 'articles', 'sources', and 'rss_feeds' tables if they don't already exist.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Create sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
                    );
                """)
                # Create rss_feeds table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rss_feeds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id INTEGER NOT NULL,
                        url TEXT NOT NULL,
                        is_enabled BOOLEAN NOT NULL DEFAULT 1,
                        FOREIGN KEY (source_id) REFERENCES sources(id)
                    );
                """)
                # Create articles table with source_id foreign key
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL UNIQUE,
                        title TEXT,
                        summary TEXT,
                        sentiment TEXT,
                        keywords TEXT,
                        category TEXT,
                        region TEXT,
                        published_at TIMESTAMP,
                        processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        source_id INTEGER NOT NULL,
                        FOREIGN KEY (source_id) REFERENCES sources(id)
                    );
                """)
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating database tables: {e}")
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

    def mark_as_processed(self, url: str, metadata: dict, published_at: Optional[str] = None, title: Optional[str] = None, source_id: Optional[int] = None) -> None:
        """
        Mark an article as processed by storing its URL, title, NewsMetadata, and source_id in the database.

        Args:
            url: The URL of the article to mark as processed.
            metadata: The NewsMetadata dict (summary, sentiment, keywords, category, region).
            published_at: The published date/time of the article (ISO format string or None).
            title: The title of the article.
            source_id: The id of the source in the sources table.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                keywords_str = ','.join(metadata.get('keywords', [])) if metadata.get('keywords') else None
                cursor.execute(
                    "INSERT INTO articles (url, title, summary, sentiment, keywords, category, region, published_at, source_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        url,
                        title,
                        metadata.get('summary'),
                        metadata.get('sentiment'),
                        keywords_str,
                        metadata.get('category'),
                        metadata.get('region'),
                        published_at,
                        source_id
                    )
                )
                conn.commit()
        except sqlite3.IntegrityError:
            self.logger.warning(f"Article with URL {url} has already been processed.")
        except sqlite3.Error as e:
            self.logger.error(f"Error marking article as processed in database: {e}")

    def add_source(self, name: str) -> int:
        """
        Add a new source to the sources table. Returns the source id.

        Args:
            name: Name of the source (e.g., 'BBC').

        Returns:
            The id of the inserted source.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO sources (name) VALUES (?)",
                    (name,)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Error adding source: {e}")
            return -1

    def add_rss_feed(self, source_id: int, url: str, is_enabled: str = 'true') -> int:
        """
        Add a new RSS feed for a source. Returns the feed id.

        Args:
            source_id: The id of the source.
            url: The RSS feed URL.
            is_enabled: 'true' or 'false' (default 'true').

        Returns:
            The id of the inserted feed.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO rss_feeds (source_id, url, is_enabled) VALUES (?, ?, ?)",
                    (source_id, url, is_enabled)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Error adding RSS feed: {e}")
            return -1

    def get_source_by_name(self, name: str) -> dict:
        """
        Get a source by name.

        Args:
            name: Name of the source.

        Returns:
            Dict with source info or None.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM sources WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    return {'id': row[0], 'name': row[1]}
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting source: {e}")
            return None

    def get_rss_feeds_for_source(self, source_id: int) -> list:
        """
        Get all RSS feed URLs for a given source.

        Args:
            source_id: The id of the source.

        Returns:
            List of feed URLs.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM rss_feeds WHERE source_id = ?", (source_id,))
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting RSS feeds: {e}")
            return []

    def get_articles(self, start_date: Optional[str] = None, end_date: Optional[str] = None, categories: Optional[list] = None) -> list:
        """
        Retrieve articles from the database filtered by date range and categories.

        Args:
            start_date: ISO format string (inclusive), filter articles published after this date.
            end_date: ISO format string (inclusive), filter articles published before this date.
            categories: List of category strings to filter by.

        Returns:
            List of dicts with article data.
        """
        query = "SELECT title, url, summary, sentiment, keywords, category, region, published_at, processed_at FROM articles WHERE 1=1"
        params = []
        if start_date:
            query += " AND published_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND published_at <= ?"
            params.append(end_date)
        if categories:
            query += " AND category IN ({})".format(",".join(["?"] * len(categories)))
            params.extend(categories)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching articles from database: {e}")
            return []
