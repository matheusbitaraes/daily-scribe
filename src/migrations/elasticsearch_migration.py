"""
Elasticsearch migration service for Daily Scribe application.

This module handles the migration of data from SQLite to Elasticsearch,
including articles, embeddings, and source information.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, scan

from components.database import DatabaseService
from components.elasticsearch_service import ElasticsearchService


class ElasticsearchMigration:
    """Handles migration of data from SQLite to Elasticsearch."""

    def __init__(
        self,
        sqlite_db_path: str = "data/digest_history.db",
        batch_size: int = 100,
        es_service: Optional[ElasticsearchService] = None
    ):
        """
        Initialize the migration service.

        Args:
            sqlite_db_path: Path to the SQLite database file.
            batch_size: Number of documents to process in each batch.
            es_service: Optional ElasticsearchService instance.
        """
        self.logger = logging.getLogger(__name__)
        self.sqlite_db_path = sqlite_db_path
        self.batch_size = batch_size
        
        # Initialize services
        self.db_service = DatabaseService()
        self.es_service = es_service or ElasticsearchService()
        
        # Migration state tracking
        self.state_file = Path("data/migration_state.json")
        self.migration_state = self._load_migration_state()
        
        # Performance metrics
        self.start_time = None
        self.processed_count = 0
        self.error_count = 0

    def _load_migration_state(self) -> Dict[str, Any]:
        """
        Load migration state from file.
        
        Returns:
            Dictionary containing migration state information.
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load migration state: {e}")
        
        return {
            "last_article_id": 0,
            "last_migration_time": None,
            "completed_migrations": [],
            "failed_articles": []
        }

    def _save_migration_state(self) -> None:
        """Save migration state to file."""
        try:
            # Ensure data directory exists
            self.state_file.parent.mkdir(exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                json.dump(self.migration_state, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save migration state: {e}")

    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status and progress.
        
        Returns:
            Dictionary containing migration status information.
        """
        try:
            # Check Elasticsearch health
            es_healthy = self.es_service.is_healthy() if self.es_service.enabled else False
            
            # Get article counts
            sqlite_count = self._get_sqlite_article_count()
            es_count = self._get_elasticsearch_article_count() if es_healthy else 0
            
            # Calculate progress
            progress_percentage = (es_count / sqlite_count * 100) if sqlite_count > 0 else 0
            
            status = {
                "elasticsearch_enabled": self.es_service.enabled,
                "elasticsearch_healthy": es_healthy,
                "sqlite_article_count": sqlite_count,
                "elasticsearch_article_count": es_count,
                "progress_percentage": round(progress_percentage, 2),
                "last_migration_time": self.migration_state.get("last_migration_time"),
                "last_article_id": self.migration_state.get("last_article_id", 0),
                "failed_articles_count": len(self.migration_state.get("failed_articles", [])),
                "batch_size": self.batch_size
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}

    def _get_sqlite_article_count(self) -> int:
        """Get total count of articles in SQLite database."""
        try:
            with self.db_service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM articles")
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Failed to get SQLite article count: {e}")
            return 0

    def _get_elasticsearch_article_count(self) -> int:
        """Get total count of articles in Elasticsearch."""
        try:
            if not self.es_service.enabled or not self.es_service._ensure_connection():
                return 0
                
            count = self.es_service.count_documents('articles')
            return count or 0
        except Exception as e:
            self.logger.error(f"Failed to get Elasticsearch article count: {e}")
            return 0

    def migrate_articles_full(self) -> bool:
        """
        Perform a full migration of all articles from SQLite to Elasticsearch.
        This will reindex everything based on what is in SQLite.
        
        Returns:
            True if migration completed successfully, False otherwise.
        """
        self.logger.info("Starting FULL migration of all articles...")
        self.start_time = time.time()
        self.processed_count = 0
        self.error_count = 0
        
        try:
            # Ensure Elasticsearch is available and index exists
            if not self._prepare_elasticsearch():
                return False
            
            # Clear existing data in Elasticsearch for full migration
            self.logger.info("Clearing existing Elasticsearch data for full migration...")
            if not self._clear_elasticsearch_index():
                self.logger.warning("Failed to clear Elasticsearch index, continuing anyway...")
            
            # Get all articles from SQLite
            articles = self._get_all_articles_from_sqlite()
            if not articles:
                self.logger.warning("No articles found in SQLite database")
                return True
            
            total_articles = len(articles)
            self.logger.info(f"Found {total_articles} articles to migrate")
            
            # Process articles in batches
            for i in range(0, total_articles, self.batch_size):
                batch = articles[i:i + self.batch_size]
                batch_number = (i // self.batch_size) + 1
                
                self.logger.info(f"Processing batch {batch_number}/{(total_articles + self.batch_size - 1) // self.batch_size}")
                
                if not self._process_article_batch(batch):
                    self.logger.error(f"Failed to process batch {batch_number}")
                    self.error_count += len(batch)
                else:
                    self.processed_count += len(batch)
                
                # Update progress
                progress = (i + len(batch)) / total_articles * 100
                self.logger.info(f"Migration progress: {progress:.1f}% ({i + len(batch)}/{total_articles})")
                
                # Save state periodically
                if batch_number % 10 == 0:
                    self._update_migration_state(max(article['id'] for article in batch))
            
            # Final state update
            self._update_migration_state(max(article['id'] for article in articles))
            
            elapsed_time = time.time() - self.start_time
            self.logger.info(f"Full migration completed in {elapsed_time:.2f} seconds")
            self.logger.info(f"Processed: {self.processed_count}, Errors: {self.error_count}")
            
            return self.error_count == 0
            
        except Exception as e:
            self.logger.error(f"Full migration failed: {e}")
            return False

    def migrate_articles_partial(self) -> bool:
        """
        Perform a partial migration, only syncing articles that haven't been synced yet.
        
        Returns:
            True if migration completed successfully, False otherwise.
        """
        self.logger.info("Starting PARTIAL migration of new articles...")
        self.start_time = time.time()
        self.processed_count = 0
        self.error_count = 0
        
        try:
            # Ensure Elasticsearch is available and index exists
            if not self._prepare_elasticsearch():
                return False
            
            # Get articles that need to be synced
            last_article_id = self.migration_state.get("last_article_id", 0)
            articles = self._get_new_articles_from_sqlite(last_article_id)
            
            if not articles:
                self.logger.info("No new articles to migrate")
                return True
            
            total_articles = len(articles)
            self.logger.info(f"Found {total_articles} new articles to migrate (from ID {last_article_id})")
            
            # Process articles in batches
            for i in range(0, total_articles, self.batch_size):
                batch = articles[i:i + self.batch_size]
                batch_number = (i // self.batch_size) + 1
                
                self.logger.info(f"Processing batch {batch_number}/{(total_articles + self.batch_size - 1) // self.batch_size}")
                
                if not self._process_article_batch(batch):
                    self.logger.error(f"Failed to process batch {batch_number}")
                    self.error_count += len(batch)
                else:
                    self.processed_count += len(batch)
                
                # Update progress
                progress = (i + len(batch)) / total_articles * 100
                self.logger.info(f"Migration progress: {progress:.1f}% ({i + len(batch)}/{total_articles})")
                
                # Save state after each batch for partial migration
                self._update_migration_state(max(article['id'] for article in batch))
            
            elapsed_time = time.time() - self.start_time
            self.logger.info(f"Partial migration completed in {elapsed_time:.2f} seconds")
            self.logger.info(f"Processed: {self.processed_count}, Errors: {self.error_count}")
            
            return self.error_count == 0
            
        except Exception as e:
            self.logger.error(f"Partial migration failed: {e}")
            return False

    def _prepare_elasticsearch(self) -> bool:
        """
        Prepare Elasticsearch for migration by ensuring connection and creating index.
        
        Returns:
            True if preparation successful, False otherwise.
        """
        if not self.es_service.enabled:
            self.logger.error("Elasticsearch is not enabled")
            return False
        
        if not self.es_service.is_healthy():
            self.logger.error("Elasticsearch is not healthy")
            return False
        
        # Create the articles index if it doesn't exist
        if not self.es_service.create_daily_scribe_articles_index():
            self.logger.error("Failed to create articles index")
            return False
        
        return True

    def _clear_elasticsearch_index(self) -> bool:
        """
        Clear all documents from the Elasticsearch index.
        
        Returns:
            True if clearing successful, False otherwise.
        """
        try:
            index_name = self.es_service._get_index_name('articles')
            
            # Delete all documents
            delete_query = {"query": {"match_all": {}}}
            result = self.es_service.client.delete_by_query(
                index=index_name,
                body=delete_query,
                wait_for_completion=True,
                refresh=True
            )
            
            deleted = result.get('deleted', 0)
            self.logger.info(f"Cleared {deleted} documents from Elasticsearch index")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear Elasticsearch index: {e}")
            return False

    def _get_all_articles_from_sqlite(self) -> List[Dict[str, Any]]:
        """
        Get all articles from SQLite database with their embeddings and source information.
        
        Returns:
            List of article dictionaries.
        """
        try:
            with self.db_service._get_connection() as conn:
                cursor = conn.cursor()
                
                # Query to get articles with embeddings and source information
                query = """
                SELECT 
                    a.id, a.url, a.title, a.summary, a.summary_pt, a.raw_content,
                    a.sentiment, a.keywords, a.category, a.region,
                    a.published_at, a.processed_at, a.source_id,
                    s.name as source_name,
                    a.urgency_score, a.impact_score,
                    ae.embedding, ae.created_at as embedding_created_at
                FROM articles a
                LEFT JOIN sources s ON a.source_id = s.id
                LEFT JOIN article_embeddings ae ON a.id = ae.article_id
                ORDER BY a.id
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    article = {
                        'id': row[0],
                        'url': row[1],
                        'title': row[2],
                        'summary': row[3],
                        'summary_pt': row[4],
                        'raw_content': row[5],
                        'sentiment': row[6],
                        'keywords': row[7],
                        'category': row[8],
                        'region': row[9],
                        'published_at': row[10],
                        'processed_at': row[11],
                        'source_id': row[12],
                        'source_name': row[13],
                        'urgency_score': row[14],
                        'impact_score': row[15],
                        'embedding': row[16],
                        'embedding_created_at': row[17]
                    }
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            self.logger.error(f"Failed to get articles from SQLite: {e}")
            return []

    def _get_new_articles_from_sqlite(self, last_article_id: int) -> List[Dict[str, Any]]:
        """
        Get new articles from SQLite database that haven't been migrated yet.
        
        Args:
            last_article_id: ID of the last migrated article.
            
        Returns:
            List of new article dictionaries.
        """
        try:
            with self.db_service._get_connection() as conn:
                cursor = conn.cursor()
                
                # Query to get articles with embeddings and source information
                query = """
                SELECT 
                    a.id, a.url, a.title, a.summary, a.summary_pt, a.raw_content,
                    a.sentiment, a.keywords, a.category, a.region,
                    a.published_at, a.processed_at, a.source_id,
                    s.name as source_name,
                    a.urgency_score, a.impact_score,
                    ae.embedding, ae.created_at as embedding_created_at
                FROM articles a
                LEFT JOIN sources s ON a.source_id = s.id
                LEFT JOIN article_embeddings ae ON a.id = ae.article_id
                ORDER BY a.id
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    article = {
                        'id': row[0],
                        'url': row[1],
                        'title': row[2],
                        'summary': row[3],
                        'summary_pt': row[4],
                        'raw_content': row[5],
                        'sentiment': row[6],
                        'keywords': row[7],
                        'category': row[8],
                        'region': row[9],
                        'published_at': row[10],
                        'processed_at': row[11],
                        'source_id': row[12],
                        'source_name': row[13],
                        'urgency_score': row[14],
                        'impact_score': row[15],
                        'embedding': row[16],
                        'embedding_created_at': row[17]
                    }
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            self.logger.error(f"Failed to get new articles from SQLite: {e}")
            return []

    def _process_article_batch(self, articles: List[Dict[str, Any]]) -> bool:
        """
        Process a batch of articles and index them in Elasticsearch.
        
        Args:
            articles: List of article dictionaries to process.
            
        Returns:
            True if batch processing successful, False otherwise.
        """
        try:
            if not articles:
                return True
            
            # Prepare documents for bulk indexing
            documents = []
            for article in articles:
                doc = self._prepare_article_document(article)
                if doc:
                    documents.append(doc)
            
            if not documents:
                self.logger.warning("No valid documents to index in this batch")
                return False
            
            # Perform bulk indexing
            index_name = self.es_service._get_index_name('articles')
            
            success, failed = bulk(
                self.es_service.client,
                documents,
                index=index_name,
                chunk_size=self.batch_size,
                timeout='60s',
                max_retries=3,
                initial_backoff=2,
                max_backoff=600
            )
            
            if failed:
                self.logger.error(f"Failed to index {len(failed)} documents in batch")
                for failure in failed:
                    self.logger.error(f"Failed document: {failure}")
                return False
            
            self.logger.debug(f"Successfully indexed {success} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process article batch: {e}, {e.errors if hasattr(e, 'errors') else 'No additional error info'}")
            return False

    def _prepare_article_document(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prepare an article document for Elasticsearch indexing.
        
        Args:
            article: Article data from SQLite.
            
        Returns:
            Document ready for Elasticsearch indexing or None if preparation failed.
        """
        try:
            # Prepare the base document
            doc = {
                '_id': article['id'],
                'id': article['id'],
                'url': article['url'],
                'title': article['title'] or '',
                'summary': article['summary'] or '',
                'summary_pt': article['summary_pt'] or '',
                'raw_content': article['raw_content'] or '',
                'sentiment': article['sentiment'] or '',
                'keywords': article['keywords'] or '',
                'category': article['category'] or '',
                'region': article['region'] or '',
                'published_at': self._format_date_for_elasticsearch(article['published_at']),
                'processed_at': self._format_date_for_elasticsearch(article['processed_at']),
                'source_id': article['source_id'],
                'source_name': article['source_name'] or '',
                'urgency_score': article['urgency_score'],
                'impact_score': article['impact_score'],
                'has_embedding': bool(article['embedding']),
                'embedding_created_at': self._format_date_for_elasticsearch(article['embedding_created_at'])
            }
            
            # Process embedding if available
            if article['embedding']:
                try:
                    # Convert BLOB to numpy array
                    embedding_blob = article['embedding']
                    embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
                    
                    # Validate embedding dimensions
                    if len(embedding_array) == 1536:
                        doc['embedding'] = embedding_array.tolist()
                    else:
                        self.logger.warning(f"Invalid embedding dimensions for article {article['id']}: {len(embedding_array)}")
                        doc['has_embedding'] = False
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process embedding for article {article['id']}: {e}")
                    doc['has_embedding'] = False
            
            return doc
            
        except Exception as e:
            self.logger.error(f"Failed to prepare document for article {article.get('id', 'unknown')}: {e}")
            return None

    def _format_date_for_elasticsearch(self, date_value: Any) -> Optional[str]:
        """
        Format date value for Elasticsearch indexing.
        
        Args:
            date_value: Date value from SQLite (could be string, None, or datetime).
            
        Returns:
            ISO formatted date string or None if invalid.
        """
        if not date_value:
            return None
            
        try:
            # If it's already a string in SQLite format, parse and convert to ISO
            if isinstance(date_value, str):
                # Handle SQLite datetime format: 'YYYY-MM-DD HH:MM:SS'
                if ' ' in date_value and len(date_value) == 19:
                    dt = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
                    return dt.isoformat() + 'Z'  # Add Z for UTC timezone
                # Handle SQLite date format: 'YYYY-MM-DD'
                elif len(date_value) == 10:
                    dt = datetime.strptime(date_value, '%Y-%m-%d')
                    return dt.isoformat() + 'Z'
                else:
                    # Try to parse other formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S.%f']:
                        try:
                            dt = datetime.strptime(date_value, fmt)
                            return dt.isoformat() + 'Z'
                        except ValueError:
                            continue
                    
            # If it's a datetime object
            elif isinstance(date_value, datetime):
                return date_value.isoformat() + 'Z'
            
            # If none of the above work, return None
            self.logger.warning(f"Could not parse date value: {date_value}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error formatting date {date_value}: {e}")
            return None

    def _update_migration_state(self, last_article_id: int) -> None:
        """
        Update migration state with progress information.
        
        Args:
            last_article_id: ID of the last processed article.
        """
        self.migration_state['last_article_id'] = last_article_id
        self.migration_state['last_migration_time'] = datetime.now().isoformat()
        self._save_migration_state()

    def validate_migration(self) -> Dict[str, Any]:
        """
        Validate the migrated data by comparing SQLite and Elasticsearch counts and sampling data.
        
        Returns:
            Dictionary containing validation results.
        """
        try:
            validation_results = {}
            
            # Get counts
            sqlite_count = self._get_sqlite_article_count()
            es_count = self._get_elasticsearch_article_count()
            
            # Basic count validation
            validation_results['sqlite_count'] = sqlite_count
            validation_results['elasticsearch_count'] = es_count
            validation_results['count_match'] = sqlite_count == es_count
            
            # Sample validation
            if sqlite_count > 0 and es_count > 0:
                sample_valid = self._validate_sample_data()
                validation_results['sample_validation'] = sample_valid
            else:
                validation_results['sample_validation'] = False
            
            # Overall validation status
            validation_results['overall_valid'] = (
                validation_results['count_match'] and 
                validation_results['sample_validation']
            )
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Migration validation failed: {e}")
            return {'error': str(e)}

    def _validate_sample_data(self, sample_size: int = 10) -> bool:
        """
        Validate a sample of migrated data by comparing SQLite and Elasticsearch records.
        
        Args:
            sample_size: Number of records to sample for validation.
            
        Returns:
            True if sample validation passes, False otherwise.
        """
        try:
            # Get sample articles from SQLite
            with self.db_service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, url, title, summary 
                    FROM articles 
                    ORDER BY RANDOM() 
                    LIMIT ?
                """, (sample_size,))
                sample_articles = cursor.fetchall()
            
            if not sample_articles:
                return False
            
            # Check each sample article in Elasticsearch
            for article in sample_articles:
                article_id, url, title, summary = article
                
                # Get document from Elasticsearch
                es_doc = self.es_service.get_document('articles', str(article_id))
                
                if not es_doc:
                    self.logger.warning(f"Article {article_id} not found in Elasticsearch")
                    return False
                
                # Validate key fields
                if (es_doc.get('url') != url or 
                    es_doc.get('title') != (title or '') or 
                    es_doc.get('summary') != (summary or '')):
                    self.logger.warning(f"Data mismatch for article {article_id}")
                    return False
            
            self.logger.info(f"Sample validation passed for {len(sample_articles)} articles")
            return True
            
        except Exception as e:
            self.logger.error(f"Sample validation failed: {e}")
            return False

    def rollback_migration(self) -> bool:
        """
        Rollback migration by clearing all data from Elasticsearch.
        
        Returns:
            True if rollback successful, False otherwise.
        """
        self.logger.info("Starting migration rollback...")
        
        try:
            # Clear the Elasticsearch index
            if not self._clear_elasticsearch_index():
                return False
            
            # Reset migration state
            self.migration_state = {
                "last_article_id": 0,
                "last_migration_time": None,
                "completed_migrations": [],
                "failed_articles": []
            }
            self._save_migration_state()
            
            self.logger.info("Migration rollback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration rollback failed: {e}")
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the last migration operation.
        
        Returns:
            Dictionary containing performance metrics.
        """
        if not self.start_time:
            return {}
        
        elapsed_time = time.time() - self.start_time
        
        metrics = {
            "elapsed_time_seconds": round(elapsed_time, 2),
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "success_rate": round((self.processed_count / (self.processed_count + self.error_count) * 100), 2) if (self.processed_count + self.error_count) > 0 else 0,
            "documents_per_second": round(self.processed_count / elapsed_time, 2) if elapsed_time > 0 else 0,
            "batch_size": self.batch_size
        }
        
        return metrics
