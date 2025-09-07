"""
Database service for Daily Scribe application.

This module handles all interactions with the SQLite database,
including storing and retrieving processed article URLs.
"""

import logging
import os
import sqlite3
import uuid
from pathlib import Path
from typing import List, Optional
from utils.migrations import migrate_database


class DatabaseService:
    """Handles all interactions with the SQLite database."""

    def __init__(self, db_path: Optional[str] = None, timeout: Optional[float] = None):
        """
        Initialize the database service.

        Args:
            db_path: Path to the SQLite database file. If None, uses DB_PATH environment 
                    variable or defaults to 'data/digest_history.db'.
            timeout: Connection timeout in seconds. If None, uses DB_TIMEOUT environment
                    variable or defaults to 30 seconds.
        """
        self.db_path = db_path or os.getenv('DB_PATH', 'data/digest_history.db')
        self.timeout = timeout if timeout is not None else float(os.getenv('DB_TIMEOUT', '30'))
        self.logger = logging.getLogger(__name__)
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database with proper timeout and thread safety.

        Returns:
            A SQLite database connection with WAL mode enabled.
        """
        # Ensure the data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection with timeout
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        
        # Enable WAL mode for better concurrency (only needs to be set once, but it's idempotent)
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Additional pragmas for better performance and reliability
        conn.execute("PRAGMA synchronous=NORMAL")  # Good balance of safety and performance
        conn.execute("PRAGMA cache_size=1000")     # Reasonable cache size
        conn.execute("PRAGMA temp_store=MEMORY")   # Store temp tables in memory
        
        return conn

    def _initialize_database(self) -> None:
        """
        Initialize the database with proper configuration and create tables if needed.
        This method is idempotent and can be called multiple times safely.
        """
        try:
            self.logger.info(f"Initializing database at {self.db_path}")
            self._create_table_if_not_exists()
            
            # Run migrations after initial table creation
            migrate_database(self.db_path)
            
            self.logger.info("Database initialization completed successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

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
                        parser TEXT NOT NULL DEFAULT 'DefaultParser',
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
                        summary_pt TEXT,
                        sentiment TEXT,
                        keywords TEXT,
                        category TEXT,
                        region TEXT,
                        published_at TIMESTAMP,
                        processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        source_id INTEGER NOT NULL,
                        raw_content TEXT,
                        FOREIGN KEY (source_id) REFERENCES sources(id)
                    );
                """)
                # Create sent_articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sent_articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER NOT NULL,
                        digest_id UUID NOT NULL,
                        email_address TEXT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    );
                """)
                # Create user_preferences table with keywords column
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_address TEXT NOT NULL,
                        enabled_sources TEXT, -- comma-separated source names or ids
                        enabled_categories TEXT, -- comma-separated category names
                        max_news_per_category INTEGER DEFAULT 10,
                        keywords TEXT, -- comma-separated keywords representing user interests
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create user_tokens table for secure preference access
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
                
                # Create indexes for user_tokens table for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_token_id ON user_tokens(token_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_token_hash ON user_tokens(token_hash);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_expires_at ON user_tokens(expires_at);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_user_preferences_id ON user_tokens(user_preferences_id);")

            # Create embeddings and clusters tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL UNIQUE,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    cluster_id INTEGER NOT NULL,
                    similarity_score REAL,
                    clustering_run_id TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
            ''')
            
                # Create user_preferences_embeddings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_preferences_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_preferences_id) REFERENCES user_preferences(id)
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise

    def add_article_content(self, article_id: int, raw_content: str) -> None:
        """
        Store the raw content of an article.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE articles SET raw_content = ? WHERE id = ?",
                    (raw_content, article_id)
                )
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error adding article content to database: {e}")

    def get_article_by_url(self, url: str) -> Optional[dict]:
        """
        Get an article by its URL.

        Args:
            url: The URL of the article.

        Returns:
            A dict with article data or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, url, title, summary, summary_pt, sentiment, keywords, category, region, published_at, processed_at, source_id, raw_content FROM articles WHERE url = ?", (url,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting article by URL from database: {e}")
            return None

    def add_sent_article(self, article_id: int, digest_id: uuid.UUID, email_address: str) -> None:
        """
        Record that an article has been sent in an email.

        Args:
            article_id: The ID of the article.
            digest_id: The ID of the digest.
            email_address: The email address the article was sent to.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO sent_articles (article_id, digest_id, email_address) VALUES (?, ?, ?)",
                    (article_id, str(digest_id), email_address)
                )
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error adding sent article to database: {e}")

    def check_if_article_sent(self, article_id: int, email_address: str) -> bool:
        """
        Check if an article has already been sent to a specific email address.

        Args:
            article_id: The ID of the article.
            email_address: The email address to check.

        Returns:
            True if the article has been sent, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM sent_articles WHERE article_id = ? AND email_address = ?",
                    (article_id, email_address)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.error(f"Error checking if article was sent: {e}")
            return False

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

    def get_all_sources(self) -> List[dict]:
        """
        Get all sources from the database.

        Returns:
            List of dicts with source info (id, name).
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM sources ORDER BY name")
                rows = cursor.fetchall()
                return [{'id': row[0], 'name': row[1]} for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting all sources: {e}")
            return []

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

    def get_articles(self, start_date: Optional[str] = None, end_date: Optional[str] = None, categories: Optional[list] = None, source_ids: Optional[list] = None, limit: int = 100, offset: int = 0) -> list:
        """
        Retrieve articles from the database filtered by date range, categories, and source_id.

        Args:
            start_date: ISO format string (inclusive), filter articles published after this date.
            end_date: ISO format string (inclusive), filter articles published before this date.
            categories: List of category strings to filter by.
            source_id: The id of the source to filter by.
            limit: The maximum number of articles to return.
            offset: The number of articles to skip.

        Returns:
            List of dicts with article data including source_name.
        """
        query = """
            SELECT a.id, a.title, a.url, a.summary, a.summary_pt, a.sentiment, a.keywords, a.category, a.region, 
                   a.published_at, a.processed_at, a.source_id, s.name as source_name
            FROM articles a
            LEFT JOIN sources s ON a.source_id = s.id
            WHERE (a.summary is not null OR a.summary_pt is not null)
        """
        params = []
        if start_date:
            query += " AND a.published_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND a.published_at <= ?"
            params.append(end_date)
        if categories:
            query += " AND a.category IN ({})".format(",".join(["?"] * len(categories)))
            params.extend(categories)
        if source_ids is not None:
            query += " AND a.source_id IN ({})".format(",".join(["?"] * len(source_ids)))
            params.extend(source_ids)

        query += " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching articles from database: {e}")
            return []

    def get_sent_article_ids_for_email(self, email_address: str) -> set:
        """
        Get a set of article IDs that have already been sent to the given email address.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT article_id FROM sent_articles WHERE email_address = ?", (email_address,))
                return set(row[0] for row in cursor.fetchall())
        except sqlite3.Error as e:
            self.logger.error(f"Error getting sent article IDs: {e}")
            return set()

    def get_unsent_articles(self, email_address: str, start_date: Optional[str] = None, end_date: Optional[str] = None, categories: Optional[list] = None, source_ids: Optional[list] = None) -> list:
        """
        Retrieve articles that have NOT been sent to the given email address, filtered by date, category, and user preferences.
        """
        sent_ids = self.get_sent_article_ids_for_email(email_address)
        all_articles = self.get_articles(start_date, end_date, categories, source_ids)
        if not sent_ids:
            filtered = all_articles
        else:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    url_to_id = {}
                    for article in all_articles:
                        cursor.execute("SELECT id FROM articles WHERE url = ?", (article['url'],))
                        row = cursor.fetchone()
                        if row:
                            url_to_id[article['url']] = row[0]
                    filtered = [a for a in all_articles if url_to_id.get(a['url']) not in sent_ids]
            except sqlite3.Error as e:
                self.logger.error(f"Error filtering unsent articles: {e}")
                filtered = all_articles
        return filtered

    def get_user_preferences(self, email_address: str) -> Optional[dict]:
        """
        Retrieve user preferences for a given email address.
        Returns a dict with enabled_sources, enabled_categories, max_news_per_category, or None if not set.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT enabled_sources, enabled_categories, max_news_per_category, keywords FROM user_preferences WHERE email_address = ? ORDER BY updated_at DESC LIMIT 1",
                    (email_address,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'enabled_sources': row[0].split(',') if row[0] else [],
                        'enabled_categories': row[1].split(',') if row[1] else [],
                        'max_news_per_category': row[2] if row[2] is not None else 10,
                        'keywords': row[3].split(',') if row[3] else []
                    }
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting user preferences: {e}")
            return None

    def set_user_preferences(self, email_address: str, enabled_sources: Optional[list] = None, enabled_categories: Optional[list] = None, max_news_per_category: Optional[int] = 10) -> None:
        """
        Set or update user preferences for a given email address.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_preferences (email_address, enabled_sources, enabled_categories, max_news_per_category, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    (
                        email_address,
                        ','.join(enabled_sources) if enabled_sources else None,
                        ','.join(enabled_categories) if enabled_categories else None,
                        max_news_per_category
                    )
                )
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error setting user preferences: {e}")
            return

    def get_articles_without_embeddings(self) -> list:
        """
        Return articles (id, title, summary, summary_pt, keywords, category) that do not have embeddings yet.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.id, a.title, a.summary, a.summary_pt, a.keywords, a.category
                    FROM articles a
                    LEFT JOIN article_embeddings ae ON a.id = ae.article_id
                    WHERE ae.article_id IS NULL
                    AND a.title IS NOT NULL
                    AND (a.summary IS NOT NULL OR a.summary_pt IS NOT NULL)
                    ORDER BY a.id
                ''')
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching articles without embeddings: {e}")
            return []

    def store_article_embedding(self, article_id: int, embedding_bytes: bytes):
        """
        Store embedding bytes for an article.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO article_embeddings (article_id, embedding)
                    VALUES (?, ?)
                ''', (article_id, embedding_bytes))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing article embedding: {e}")

    def get_all_article_embeddings(self, article_ids: Optional[List[int]] = None):
        """
        Return (embeddings_matrix, article_ids) for all articles with embeddings.
        Can be filtered by a list of article_ids.
        """
        import numpy as np
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT ae.article_id, ae.embedding
                    FROM article_embeddings ae
                    INNER JOIN articles a ON ae.article_id = a.id
                '''
                params = []
                if article_ids:
                    query += " WHERE ae.article_id IN ({})".format(",".join(["?"] * len(article_ids)))
                    params.extend(article_ids)
                
                query += ' ORDER BY ae.article_id'
                
                cursor.execute(query, params)
                
                embeddings = []
                returned_article_ids = []
                for article_id, embedding_bytes in cursor.fetchall():
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    embeddings.append(embedding)
                    returned_article_ids.append(article_id)
                return (np.array(embeddings), returned_article_ids)
        except Exception as e:
            self.logger.error(f"Error fetching all article embeddings: {e}")
            return (np.array([]), [])

    def store_article_clusters(self, article_ids, cluster_labels, similarity_scores, run_id):
        """
        Store clustering results for articles.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM article_clusters WHERE clustering_run_id = ?', (run_id,))
                for article_id, cluster_id, similarity_score in zip(article_ids, cluster_labels, similarity_scores):
                    cursor.execute('''
                        INSERT INTO article_clusters 
                        (article_id, cluster_id, similarity_score, clustering_run_id)
                        VALUES (?, ?, ?, ?)
                    ''', (article_id, cluster_id, similarity_score, run_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing article clusters: {e}")

    def get_article_by_id(self, article_id: int):
        """
        Return article dict by id, including source_name.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT a.*, s.name as source_name, s.id as source_id
                    FROM articles a
                    LEFT JOIN sources s ON a.source_id = s.id
                    WHERE a.id = ?
                """
                cursor.execute(query, (article_id,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            self.logger.error(f"Error getting article by id: {e}")
            return None

    def analyze_clusters(self, run_id: str):
        """
        Return cluster analysis for a given run_id.
        """
        import pandas as pd
        try:
            with self._get_connection() as conn:
                query = '''
                    SELECT 
                        ac.cluster_id,
                        COUNT(*) as article_count,
                        AVG(ac.similarity_score) as avg_similarity,
                        GROUP_CONCAT(DISTINCT a.category) as categories,
                        GROUP_CONCAT(a.title, ' | ') as sample_titles
                    FROM article_clusters ac
                    JOIN articles a ON ac.article_id = a.id
                    WHERE ac.clustering_run_id = ?
                    GROUP BY ac.cluster_id
                    ORDER BY article_count DESC
                '''
                df = pd.read_sql_query(query, conn, params=(run_id,))
                df['sample_titles'] = df['sample_titles'].apply(
                    lambda x: (x[:200] + '...') if len(str(x)) > 200 else x
                )
                return {
                    'total_clusters': len(df),
                    'total_articles': df['article_count'].sum(),
                    'avg_cluster_size': df['article_count'].mean(),
                    'cluster_details': df.to_dict('records')
                }
        except Exception as e:
            self.logger.error(f"Error analyzing clusters: {e}")
            return {}

    def store_user_embedding(self, email_address: str, embedding: list):
        """
        Store or update the embedding for a user's preferences.
        Args:
            email_address: The user's email address.
            embedding: The embedding vector as a list of floats or bytes.
        """
        import numpy as np
        embedding_bytes = (
            embedding if isinstance(embedding, (bytes, bytearray))
            else np.array(embedding, dtype=np.float32).tobytes()
        )
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Get the latest user_preferences id for this user
                cursor.execute(
                    "SELECT id FROM user_preferences WHERE email_address = ? ORDER BY updated_at DESC LIMIT 1",
                    (email_address,)
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"No user_preferences found for {email_address}")
                user_preferences_id = row[0]
                # Insert or replace embedding for this user_preferences_id
                cursor.execute(
                    '''INSERT OR REPLACE INTO user_preferences_embeddings (user_preferences_id, embedding) VALUES (?, ?)''',
                    (user_preferences_id, embedding_bytes)
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing user embedding: {e}")

    def get_user_embedding(self, email_address: str):
        """
        Retrieve the latest embedding for a user's preferences.
        Args:
            email_address: The user's email address.
        Returns:
            The embedding as a numpy array, or None if not found.
        """
        import numpy as np
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Get the latest user_preferences id for this user
                cursor.execute(
                    "SELECT id FROM user_preferences WHERE email_address = ? ORDER BY updated_at DESC LIMIT 1",
                    (email_address,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                user_preferences_id = row[0]
                # Get the latest embedding for this user_preferences_id
                cursor.execute(
                    '''SELECT embedding FROM user_preferences_embeddings WHERE user_preferences_id = ? ORDER BY created_at DESC LIMIT 1''',
                    (user_preferences_id,)
                )
                emb_row = cursor.fetchone()
                if not emb_row:
                    return None
                embedding_bytes = emb_row[0]
                return np.frombuffer(embedding_bytes, dtype=np.float32)
        except Exception as e:
            self.logger.error(f"Error retrieving user embedding: {e}")
            return None

    def get_articles_to_summarize(self) -> list:
        """
        Return articles that have raw content but have not been summarized yet.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.id, a.url, a.title, a.raw_content
                    FROM articles a
                    WHERE (a.summary IS NULL AND a.summary_pt IS NULL) AND a.raw_content IS NOT NULL
                ''')
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching articles to summarize: {e}")
            return []

    def update_article_summary(self, article_id: int, metadata: dict) -> None:
        """
        Update an article with its summary and other metadata.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                keywords_str = ','.join(metadata.get('keywords', [])) if metadata.get('keywords') else None
                
                # Check if we're updating with Portuguese summary
                if 'summary_pt' in metadata:
                    cursor.execute(
                        """
                        UPDATE articles
                        SET summary_pt = ?, sentiment = ?, keywords = ?, category = ?, region = ?
                        WHERE id = ?
                        """,
                        (
                            metadata.get('summary_pt'),
                            metadata.get('sentiment'),
                            keywords_str,
                            metadata.get('category'),
                            metadata.get('region'),
                            article_id
                        )
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE articles
                        SET summary = ?, sentiment = ?, keywords = ?, category = ?, region = ?
                        WHERE id = ?
                        """,
                        (
                            metadata.get('summary'),
                            metadata.get('sentiment'),
                            keywords_str,
                            metadata.get('category'),
                            metadata.get('region'),
                            article_id
                        )
                    )
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error updating article summary in database: {e}")

    def get_preferred_summary(self, article: dict) -> str:
        """
        Get the preferred summary for an article (Portuguese if available, otherwise English).
        
        Args:
            article: Article dict containing summary and summary_pt fields
            
        Returns:
            The preferred summary text
        """
        return article.get('summary_pt') or article.get('summary', '')

    def get_preferred_summary_field_name(self, article: dict) -> str:
        """
        Get the name of the field containing the preferred summary.
        
        Args:
            article: Article dict containing summary and summary_pt fields
            
        Returns:
            'summary_pt' if Portuguese summary exists, otherwise 'summary'
        """
        return 'summary_pt' if article.get('summary_pt') else 'summary'

    def update_article_summary_pt(self, article_id: int, summary_pt: str) -> None:
        """
        Update an article with its Portuguese summary.
        
        Args:
            article_id: The ID of the article to update
            summary_pt: The Portuguese summary text
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE articles SET summary_pt = ? WHERE id = ?",
                    (summary_pt, article_id)
                )
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error updating article Portuguese summary in database: {e}")

    def get_all_user_email_addresses(self) -> list:
        """
        Return a list of all unique user email addresses from the user_preferences table.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT email_address FROM user_preferences")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching user email addresses: {e}")
            return []

    def get_source_id_by_feed_url(self, feed_url: str) -> Optional[int]:
        """
        Get the source_id for a given feed_url from the rss_feeds table.
        Args:
            feed_url: The RSS feed URL.
        Returns:
            The source_id if found, else None.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_id FROM rss_feeds WHERE url = ?", (feed_url,))
                row = cursor.fetchone()
                if row:
                    return row[0]
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting source_id by feed_url: {e}")
            return None

    def get_feed_details_by_url(self, feed_url: str) -> Optional[dict]:
        """
        Get details for a given feed_url from the rss_feeds table.
        Args:
            feed_url: The RSS feed URL.
        Returns:
            A dict with feed details or None if not found.
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT source_id, parser FROM rss_feeds WHERE url = ?", (feed_url,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting feed details by url: {e}")
            return None

    def has_user_received_digest_today(self, email_address: str) -> bool:
        """
        Check if a user has received a digest today.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Check for entries for the user from today in local time
                cursor.execute(
                    "SELECT 1 FROM sent_articles WHERE email_address = ? AND DATE(sent_at, 'localtime') = DATE('now', 'localtime')",
                    (email_address,)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.error(f"Error checking if user received digest today: {e}")
            # Fail safe: if check fails, better to not send than to send multiple times.
            return True

    # Token Management Methods

    def create_user_token(self, token_id: str, token_hash: str, user_preferences_id: int, 
                         device_fingerprint: str, expires_at: str, max_usage: int = 10) -> Optional[int]:
        """
        Create a new user token for secure preference access.
        
        Args:
            token_id: Unique token identifier
            token_hash: Hashed version of the token for security
            user_preferences_id: Foreign key to user_preferences table
            device_fingerprint: Device fingerprint for additional security
            expires_at: Token expiration timestamp
            max_usage: Maximum number of times token can be used
            
        Returns:
            The token record ID if successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_tokens (
                        token_id, token_hash, user_preferences_id, device_fingerprint,
                        expires_at, max_usage, purpose, version
                    ) VALUES (?, ?, ?, ?, ?, ?, 'email_preferences', 1)
                """, (token_id, token_hash, user_preferences_id, device_fingerprint, expires_at, max_usage))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Error creating user token: {e}")
            return None

    def get_user_token(self, token_id: str) -> Optional[dict]:
        """
        Retrieve a user token by token_id.
        
        Args:
            token_id: The token identifier
            
        Returns:
            Dict with token data or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_tokens 
                    WHERE token_id = ? AND is_revoked = 0 AND expires_at > CURRENT_TIMESTAMP
                """, (token_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving user token: {e}")
            return None

    def increment_token_usage(self, token_id: str) -> bool:
        """
        Increment the usage count for a token.
        
        Args:
            token_id: The token identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_tokens 
                    SET usage_count = usage_count + 1
                    WHERE token_id = ? AND is_revoked = 0 AND expires_at > CURRENT_TIMESTAMP
                """, (token_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            self.logger.error(f"Error incrementing token usage: {e}")
            return False

    def revoke_user_token(self, token_id: str) -> bool:
        """
        Revoke a specific user token.
        
        Args:
            token_id: The token identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_tokens 
                    SET is_revoked = 1
                    WHERE token_id = ?
                """, (token_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            self.logger.error(f"Error revoking user token: {e}")
            return False

    def revoke_user_tokens_by_preferences_id(self, user_preferences_id: int) -> bool:
        """
        Revoke all tokens for a specific user (by user_preferences_id).
        
        Args:
            user_preferences_id: The user preferences ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_tokens 
                    SET is_revoked = 1
                    WHERE user_preferences_id = ?
                """, (user_preferences_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error revoking user tokens: {e}")
            return False

    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from the database.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_tokens 
                    WHERE expires_at <= CURRENT_TIMESTAMP OR is_revoked = 1
                """)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up expired tokens: {e}")
            return 0

    def get_user_preferences_by_email(self, email_address: str) -> Optional[dict]:
        """
        Get user preferences by email address.
        
        Args:
            email_address: User's email address
            
        Returns:
            Dict with user preferences or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_preferences 
                    WHERE email_address = ?
                """, (email_address,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving user preferences by email: {e}")
            return None

    def update_user_preferences(
        self, 
        preferences_id: int, 
        enabled_sources: Optional[str] = None,
        enabled_categories: Optional[str] = None,
        keywords: Optional[str] = None,
        max_news_per_category: Optional[int] = None
    ) -> bool:
        """
        Update user preferences by ID.
        
        Args:
            preferences_id: User preferences ID
            enabled_sources: Comma-separated enabled sources
            enabled_categories: Comma-separated enabled categories
            keywords: Comma-separated keywords
            max_news_per_category: Maximum news articles per category
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Build dynamic update query based on provided parameters
            update_fields = []
            params = []
            
            if enabled_sources is not None:
                update_fields.append("enabled_sources = ?")
                params.append(enabled_sources)
            
            if enabled_categories is not None:
                update_fields.append("enabled_categories = ?")
                params.append(enabled_categories)
            
            if keywords is not None:
                update_fields.append("keywords = ?")
                params.append(keywords)
            
            if max_news_per_category is not None:
                update_fields.append("max_news_per_category = ?")
                params.append(max_news_per_category)
            
            if not update_fields:
                self.logger.warning("No fields provided for user preferences update")
                return False
            
            # Add updated timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(preferences_id)
            
            query = f"""
                UPDATE user_preferences 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if cursor.rowcount == 0:
                    self.logger.warning(f"No user preferences found with ID: {preferences_id}")
                    return False
                
                conn.commit()
                self.logger.info(f"Updated user preferences for ID: {preferences_id}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error updating user preferences: {e}")
            return False

    def add_user_preferences(
        self,
        email_address: str,
        enabled_sources: Optional[List[str]] = None,
        enabled_categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        max_news_per_category: int = 10
    ) -> Optional[int]:
        """
        Add new user preferences.
        
        Args:
            email_address: User's email address
            enabled_sources: List of enabled sources
            enabled_categories: List of enabled categories
            keywords: List of keywords
            max_news_per_category: Maximum news per category
            
        Returns:
            User preferences ID if successful, None otherwise
        """
        try:
            # Convert lists to comma-separated strings
            sources_str = ','.join(enabled_sources) if enabled_sources else ''
            categories_str = ','.join(enabled_categories) if enabled_categories else ''
            keywords_str = ','.join(keywords) if keywords else ''
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_preferences 
                    (email_address, enabled_sources, enabled_categories, keywords, max_news_per_category)
                    VALUES (?, ?, ?, ?, ?)
                """, (email_address, sources_str, categories_str, keywords_str, max_news_per_category))
                
                preferences_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Added user preferences for {email_address} with ID: {preferences_id}")
                return preferences_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Error adding user preferences: {e}")
            return None
