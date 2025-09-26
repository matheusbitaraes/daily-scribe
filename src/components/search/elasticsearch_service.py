"""
Elasticsearch service for Daily Scribe application.

This module handles all interactions with Elasticsearch,
including connection management, index operations, and document CRUD operations.
"""
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

from components.env_loader import get_env_var


class ElasticsearchService:
    """Handles all interactions with Elasticsearch cluster."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        enabled: Optional[bool] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_on_timeout: Optional[bool] = None,
        index_prefix: Optional[str] = None
    ):
        """
        Initialize the Elasticsearch service.

        Args:
            host: Elasticsearch host. If None, uses ELASTICSEARCH_HOST environment variable.
            port: Elasticsearch port. If None, uses ELASTICSEARCH_PORT environment variable.
            enabled: Whether Elasticsearch is enabled. If None, uses ELASTICSEARCH_ENABLED.
            timeout: Connection timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_on_timeout: Whether to retry on timeout.
            index_prefix: Prefix for all index names.
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration from environment variables
        self.enabled = enabled if enabled is not None else get_env_var('ELASTICSEARCH_ENABLED', 'false').lower() == 'true'
        self.host = host or get_env_var('ELASTICSEARCH_HOST', 'localhost')
        self.port = port or int(get_env_var('ELASTICSEARCH_PORT', '9200'))
        self.timeout = timeout or int(get_env_var('ELASTICSEARCH_TIMEOUT', '30'))
        self.max_retries = max_retries or int(get_env_var('ELASTICSEARCH_MAX_RETRIES', '3'))
        self.retry_on_timeout = retry_on_timeout if retry_on_timeout is not None else get_env_var('ELASTICSEARCH_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
        self.index_prefix = index_prefix or get_env_var('ELASTICSEARCH_INDEX_PREFIX', 'daily_scribe')
        
        # Initialize client
        self.client: Optional[Elasticsearch] = None
        self._connection_healthy = False
        
        if self.enabled:
            self._initialize_client()
        else:
            self.logger.info("Elasticsearch is disabled in configuration")

    def _initialize_client(self) -> None:
        """Initialize the Elasticsearch client with retry logic."""
        try:
            # Configure client
            client_config = {
                'hosts': [{'host': self.host, 'port': self.port, 'scheme': 'http'}],
                'timeout': self.timeout,
                'max_retries': self.max_retries,
                'retry_on_timeout': self.retry_on_timeout,
                'verify_certs': False,  # For development with self-signed certificates
                'ssl_show_warn': False
            }
            
            self.client = Elasticsearch(**client_config)
            
            # Test connection
            if self._test_connection():
                self.logger.info(f"Successfully connected to Elasticsearch at {self.host}:{self.port}")
                self._connection_healthy = True
            else:
                self.logger.warning("Failed to establish connection to Elasticsearch")
                self._connection_healthy = False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Elasticsearch client: {e}")
            self.client = None
            self._connection_healthy = False

    def _test_connection(self) -> bool:
        """
        Test the connection to Elasticsearch.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        if not self.client:
            return False
            
        try:
            info = self.client.info()
            self.logger.debug(f"Elasticsearch cluster info: {info.get('cluster_name', 'unknown')}")
            return True
        except Exception as e:
            self.logger.warning(f"Elasticsearch connection test failed: {e}")
            return False

    def is_healthy(self) -> bool:
        """
        Check if Elasticsearch connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise.
        """
        if not self.enabled or not self.client:
            return False
            
        try:
            health = self.client.cluster.health()
            return health.get('status') in ['yellow', 'green']
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            self._connection_healthy = False
            return False

    def reconnect(self) -> bool:
        """
        Attempt to reconnect to Elasticsearch.
        
        Returns:
            True if reconnection successful, False otherwise.
        """
        if not self.enabled:
            return False
            
        self.logger.info("Attempting to reconnect to Elasticsearch...")
        self._initialize_client()
        return self._connection_healthy

    def get_cluster_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cluster information.
        
        Returns:
            Cluster information dictionary or None if connection failed.
        """
        if not self._ensure_connection():
            return None
            
        try:
            return self.client.info()
        except Exception as e:
            self.logger.error(f"Failed to get cluster info: {e}")
            return None

    def get_cluster_health(self) -> Optional[Dict[str, Any]]:
        """
        Get cluster health information.
        
        Returns:
            Cluster health dictionary or None if connection failed.
        """
        if not self._ensure_connection():
            return None
            
        try:
            return self.client.cluster.health()
        except Exception as e:
            self.logger.error(f"Failed to get cluster health: {e}")
            return None

    def _ensure_connection(self) -> bool:
        """
        Ensure we have a healthy connection to Elasticsearch.
        
        Returns:
            True if connection is available, False otherwise.
        """
        if not self.enabled:
            self.logger.debug("Elasticsearch is disabled")
            return False
            
        if not self.client or not self._connection_healthy:
            self.logger.info("Elasticsearch connection not healthy, attempting to reconnect...")
            return self.reconnect()
            
        return True

    def _get_index_name(self, index_type: str) -> str:
        """
        Get the full index name with prefix.
        
        Args:
            index_type: Type of index (articles, user_preferences, etc.)
            
        Returns:
            Full index name with prefix.
        """
        return f"{self.index_prefix}_{index_type}"

    # Index Management Methods

    def create_index(self, index_type: str, mapping: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create an index with the given mapping and settings.
        
        Args:
            index_type: Type of index to create.
            mapping: Index mapping configuration.
            settings: Optional index settings.
            
        Returns:
            True if index created successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            # Check if index already exists
            if self.client.indices.exists(index=index_name):
                self.logger.info(f"Index {index_name} already exists")
                return True
                
            # Create index body
            index_body = {"mappings": mapping}
            if settings:
                index_body["settings"] = settings
                
            # Create the index
            result = self.client.indices.create(index=index_name, body=index_body)
            self.logger.info(f"Successfully created index {index_name}")
            return result.get('acknowledged', False)
            
        except Exception as e:
            self.logger.error(f"Failed to create index {index_name}: {e}")
            return False

    def delete_index(self, index_type: str) -> bool:
        """
        Delete an index.
        
        Args:
            index_type: Type of index to delete.
            
        Returns:
            True if index deleted successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            if not self.client.indices.exists(index=index_name):
                self.logger.info(f"Index {index_name} does not exist")
                return True
                
            result = self.client.indices.delete(index=index_name)
            self.logger.info(f"Successfully deleted index {index_name}")
            return result.get('acknowledged', False)
            
        except Exception as e:
            self.logger.error(f"Failed to delete index {index_name}: {e}")
            return False

    def index_exists(self, index_type: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_type: Type of index to check.
            
        Returns:
            True if index exists, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            return self.client.indices.exists(index=index_name)
        except Exception as e:
            self.logger.error(f"Failed to check if index {index_name} exists: {e}")
            return False

    def refresh_index(self, index_type: str) -> bool:
        """
        Refresh an index to make recent changes searchable.
        
        Args:
            index_type: Type of index to refresh.
            
        Returns:
            True if refresh successful, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            self.client.indices.refresh(index=index_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to refresh index {index_name}: {e}")
            return False

    # Document Operations

    def index_document(self, index_type: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Index a single document.
        
        Args:
            index_type: Type of index to index into.
            doc_id: Document ID.
            document: Document to index.
            
        Returns:
            True if document indexed successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            result = self.client.index(
                index=index_name,
                id=doc_id,
                body=document
            )
            self.logger.debug(f"Indexed document {doc_id} in {index_name}")
            return result.get('result') in ['created', 'updated']
            
        except Exception as e:
            self.logger.error(f"Failed to index document {doc_id} in {index_name}: {e}")
            return False

    def get_document(self, index_type: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            index_type: Type of index to search in.
            doc_id: Document ID.
            
        Returns:
            Document dictionary or None if not found.
        """
        if not self._ensure_connection():
            return None
            
        index_name = self._get_index_name(index_type)
        
        try:
            result = self.client.get(index=index_name, id=doc_id)
            return result.get('_source')
        except NotFoundError:
            self.logger.debug(f"Document {doc_id} not found in {index_name}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get document {doc_id} from {index_name}: {e}")
            return None

    def update_document(self, index_type: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a document.
        
        Args:
            index_type: Type of index to update in.
            doc_id: Document ID.
            updates: Fields to update.
            
        Returns:
            True if document updated successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            result = self.client.update(
                index=index_name,
                id=doc_id,
                body={"doc": updates}
            )
            self.logger.debug(f"Updated document {doc_id} in {index_name}")
            return result.get('result') == 'updated'
            
        except Exception as e:
            self.logger.error(f"Failed to update document {doc_id} in {index_name}: {e}")
            return False

    def delete_document(self, index_type: str, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            index_type: Type of index to delete from.
            doc_id: Document ID.
            
        Returns:
            True if document deleted successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            result = self.client.delete(index=index_name, id=doc_id)
            self.logger.debug(f"Deleted document {doc_id} from {index_name}")
            return result.get('result') == 'deleted'
            
        except NotFoundError:
            self.logger.debug(f"Document {doc_id} not found for deletion in {index_name}")
            return True  # Consider deletion successful if document doesn't exist
        except Exception as e:
            self.logger.error(f"Failed to delete document {doc_id} from {index_name}: {e}")
            return False

    def bulk_index_documents(self, index_type: str, documents: List[Dict[str, Any]], id_field: str = 'id') -> bool:
        """
        Bulk index multiple documents.
        
        Args:
            index_type: Type of index to index into.
            documents: List of documents to index.
            id_field: Field name to use as document ID.
            
        Returns:
            True if all documents indexed successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        if not documents:
            return True
            
        index_name = self._get_index_name(index_type)
        
        try:
            # Prepare bulk actions
            actions = []
            for doc in documents:
                if id_field not in doc:
                    self.logger.warning(f"Document missing {id_field} field, skipping: {doc}")
                    continue
                    
                action = {
                    '_index': index_name,
                    '_id': doc[id_field],
                    '_source': doc
                }
                actions.append(action)
            
            if not actions:
                self.logger.warning("No valid documents to index")
                return True
                
            # Execute bulk operation
            success_count, errors = bulk(self.client, actions)
            
            if errors:
                self.logger.error(f"Bulk indexing had errors: {errors}")
                return False
                
            self.logger.info(f"Successfully bulk indexed {success_count} documents to {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to bulk index documents to {index_name}: {e}")
            return False

    def search(self, index_type: str, query: Dict[str, Any], size: int = 10, from_: int = 0) -> Optional[Dict[str, Any]]:
        """
        Perform a search query.
        
        Args:
            index_type: Type of index to search in.
            query: Elasticsearch query DSL.
            size: Number of results to return.
            from_: Starting offset for pagination.
            
        Returns:
            Search results dictionary or None if search failed.
        """
        if not self._ensure_connection():
            return None
            
        index_name = self._get_index_name(index_type)
        
        try:
            # Prepare search parameters
            search_params = {
                "index": index_name,
                "size": size,
                "from": from_
            }
            
            # Add query parameters
            search_params.update(query)
            
            result = self.client.search(**search_params)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to search in {index_name}: {e}")
            return None

    def count_documents(self, index_type: str) -> Optional[int]:
        """
        Get the count of documents in an index.
        
        Args:
            index_type: Type of index to count documents in.
            
        Returns:
            Number of documents in the index or None if count failed.
        """
        if not self._ensure_connection():
            return None
            
        index_name = self._get_index_name(index_type)
        
        try:
            result = self.client.count(index=index_name)
            return result.get("count", 0)
            
        except Exception as e:
            self.logger.error(f"Failed to count documents in {index_name}: {e}")
            return None

    def load_mapping_config(self) -> Optional[Dict[str, Any]]:
        """
        Load mapping configuration from the mappings file.
        
        Returns:
            Dictionary containing all index mappings or None if loading failed.
        """
        
        try:
            # Get the mappings file path relative to this file
            current_dir = Path(__file__).parent.parent
            config_path = current_dir.parent / "config" / "elasticsearch_mappings.json"
            
            if not config_path.exists():
                self.logger.error(f"Mapping configuration file not found: {config_path}")
                return None
                
            with open(config_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                
            self.logger.info(f"Successfully loaded mapping configuration from {config_path}")
            return mappings
            
        except Exception as e:
            self.logger.error(f"Failed to load mapping configuration: {e}")
            return None

    def create_daily_scribe_articles_index(self) -> bool:
        """
        Create the daily_scribe_articles index with proper mapping and settings.
        
        Returns:
            True if index created successfully, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        try:
            # Load the mapping configuration
            mappings_config = self.load_mapping_config()
            if not mappings_config:
                self.logger.error("Could not load mapping configuration")
                return False
                
            # Get the daily_scribe_articles configuration
            articles_config = mappings_config.get('daily_scribe_articles')
            if not articles_config:
                self.logger.error("daily_scribe_articles configuration not found in mappings")
                return False
                
            # Extract mappings and settings
            mappings = articles_config.get('mappings', {})
            settings = articles_config.get('settings', {})
            
            # Create the index
            success = self.create_index('articles', mappings, settings)
            
            if success:
                self.logger.info("Successfully created daily_scribe_articles index")
            else:
                self.logger.error("Failed to create daily_scribe_articles index")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating daily_scribe_articles index: {e}")
            return False

    def validate_mapping(self, index_type: str) -> bool:
        """
        Validate that an index exists and has the expected mapping structure.
        
        Args:
            index_type: Type of index to validate.
            
        Returns:
            True if mapping is valid, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            # Check if index exists
            if not self.client.indices.exists(index=index_name):
                self.logger.warning(f"Index {index_name} does not exist")
                return False
                
            # Get current mapping
            mapping_response = self.client.indices.get_mapping(index=index_name)
            current_mapping = mapping_response.get(index_name, {}).get('mappings', {})
            
            # Load expected mapping from configuration
            mappings_config = self.load_mapping_config()
            if not mappings_config:
                self.logger.error("Could not load mapping configuration for validation")
                return False
                
            # Get expected mapping for this index type
            expected_config = mappings_config.get(index_type)
            if not expected_config:
                self.logger.error(f"No expected mapping found for index type: {index_type}")
                return False
                
            expected_mapping = expected_config.get('mappings', {})
            
            # Compare key fields (this is a basic validation)
            expected_properties = expected_mapping.get('properties', {})
            current_properties = current_mapping.get('properties', {})
            
            # Check if all expected properties exist
            for field_name, field_config in expected_properties.items():
                if field_name not in current_properties:
                    self.logger.warning(f"Missing field in mapping: {field_name}")
                    return False
                    
                # Check field type
                expected_type = field_config.get('type')
                current_type = current_properties[field_name].get('type')
                
                if expected_type != current_type:
                    self.logger.warning(f"Field type mismatch for {field_name}: expected {expected_type}, got {current_type}")
                    return False
            
            self.logger.info(f"Mapping validation passed for index {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate mapping for {index_name}: {e}")
            return False

    def setup_all_indices(self) -> Dict[str, bool]:
        """
        Set up all indices defined in the mapping configuration.
        
        Returns:
            Dictionary mapping index types to creation success status.
        """
        if not self._ensure_connection():
            return {}
            
        try:
            # Load mapping configuration
            mappings_config = self.load_mapping_config()
            if not mappings_config:
                self.logger.error("Could not load mapping configuration")
                return {}
                
            results = {}
            
            # Create each index defined in the configuration
            for index_type, config in mappings_config.items():
                try:
                    mappings = config.get('mappings', {})
                    settings = config.get('settings', {})
                    
                    success = self.create_index(index_type, mappings, settings)
                    results[index_type] = success
                    
                    if success:
                        self.logger.info(f"Successfully set up index: {index_type}")
                    else:
                        self.logger.error(f"Failed to set up index: {index_type}")
                        
                except Exception as e:
                    self.logger.error(f"Error setting up index {index_type}: {e}")
                    results[index_type] = False
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error in setup_all_indices: {e}")
            return {}

    # Migration and Bulk Operations

    def clear_index(self, index_type: str) -> bool:
        """
        Clear all documents from an Elasticsearch index.
        
        Args:
            index_type: Type of index to clear.
            
        Returns:
            True if clearing successful, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        index_name = self._get_index_name(index_type)
        
        try:
            # Delete all documents
            delete_query = {"query": {"match_all": {}}}
            result = self.client.delete_by_query(
                index=index_name,
                body=delete_query,
                wait_for_completion=True,
                refresh=True
            )
            
            deleted = result.get('deleted', 0)
            self.logger.info(f"Cleared {deleted} documents from index {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear index {index_name}: {e}")
            return False

    def bulk_index_articles(self, articles: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """
        Process a batch of articles and index them in Elasticsearch.
        
        Args:
            articles: List of article dictionaries to process.
            batch_size: Size of batches for bulk operations.
            
        Returns:
            True if batch processing successful, False otherwise.
        """
        if not self._ensure_connection():
            return False
            
        try:
            if not articles:
                return True
            
            # Prepare documents for bulk indexing
            documents = []
            for article in articles:
                doc = self.prepare_article_document(article)
                if doc:
                    documents.append(doc)
            
            if not documents:
                self.logger.warning("No valid documents to index in this batch")
                return False
            
            # Perform bulk indexing
            index_name = self._get_index_name('articles')
            
            success, failed = bulk(
                self.client,
                documents,
                index=index_name,
                chunk_size=batch_size,
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

    def prepare_article_document(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                'title_pt': article['title_pt'] or '',
                'summary': article['summary'] or '',
                'summary_pt': article['summary_pt'] or '',
                'raw_content': article['raw_content'] or '',
                'sentiment': article['sentiment'] or '',
                'keywords': article['keywords'] or '',
                'category': article['category'] or '',
                'region': article['region'] or '',
                'published_at': self.format_date_for_elasticsearch(article['published_at']),
                'processed_at': self.format_date_for_elasticsearch(article['processed_at']),
                'source_id': article['source_id'],
                'source_name': article['source_name'] or '',
                'urgency_score': article['urgency_score'],
                'impact_score': article['impact_score'],
                'has_embedding': bool(article['embedding']),
                'embedding_created_at': self.format_date_for_elasticsearch(article['embedding_created_at'])
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

    def format_date_for_elasticsearch(self, date_value: Any) -> Optional[str]:
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

    def index_article(self, article: int) -> bool:
        """
        Index a single article to Elasticsearch by its ID.
        
        Args:
            article_id: The ID of the article to index.
            
        Returns:
            True if article indexed successfully, False otherwise.
        """
        if not self._ensure_connection():
            self.logger.error("No Elasticsearch connection available")
            return False
            
        try:    
            # Prepare document for Elasticsearch
            document = self.prepare_article_document(article)
            if not document:
                self.logger.error(f"Failed to prepare document for article {article.id}")
                return False
                
            # Index the document
            success = self.index_document('articles', str(article.id), document)
            
            if success:
                self.logger.info(f"Successfully indexed article {article.id} to Elasticsearch")
            else:
                self.logger.error(f"Failed to index article {article.id} to Elasticsearch")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error indexing article {article.id}: {e}")
            return False

    def get_similar_articles(self, article: Dict[str, Any], top_k: int = 20, similarity_threshold: float = 0.75, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """
        Find similar articles using Elasticsearch vector similarity search.
        
        Args:
            article: The article to find similar articles for
            top_k: Maximum number of similar articles to return
            similarity_threshold: Minimum similarity score threshold
            start_date: Optional start date filter for similar articles
            end_date: Optional end date filter for similar articles
            
        Returns:
            List of similar articles
        """
        if not self._ensure_connection():
            return []
            
        # Check if the article has an embedding
        if not article.get('has_embedding') or not article.get('embedding'):
            self.logger.debug(f"Article {article.get('id', 'unknown')} has no embedding available")
            return []
        
        try:
            # Build k-NN query for vector similarity search
            knn_query = {
                "knn": {
                    "field": "embedding",
                    "query_vector": article['embedding'],
                    "k": top_k,
                    "num_candidates": top_k * 2,  # Search more candidates for better results
                    "filter": {
                        "bool": {
                            "must_not": [
                                {"term": {"id": article['id']}}  # Exclude the source article itself
                            ],
                            "filter": []
                        }
                    }
                }
            }
            
            # Add date range filter if specified
            if start_date and end_date:
                # Extend date range for clustering to allow finding older similar articles
                extended_start = start_date - timedelta(days=0) # for now, no extension
                knn_query["knn"]["filter"]["bool"]["filter"].append({
                    "range": {
                        "published_at": {
                            "gte": extended_start.isoformat(),
                            "lte": end_date.isoformat()
                        }
                    }
                })
            
            # Ensure articles have embeddings
            knn_query["knn"]["filter"]["bool"]["filter"].append({
                "term": {"has_embedding": True}
            })
            
            # Execute k-NN search
            response = self.search(
                index_type="articles",
                query=knn_query,
                size=top_k,
                from_=0
            )
            
            if not response or 'hits' not in response:
                self.logger.debug(f"No k-NN search results for article {article['id']}")
                return []
            
            similar_articles = []
            for hit in response["hits"]["hits"]:
                # Check similarity threshold (Elasticsearch returns similarity scores)
                if hit.get("_score", 0) >= similarity_threshold:
                    similar_article = hit["_source"]
                    similar_articles.append(similar_article)
            
            self.logger.debug(f"Found {len(similar_articles)} similar articles for article {article['id']} (threshold: {similarity_threshold})")
            return similar_articles
            
        except Exception as e:
            self.logger.error(f"Elasticsearch k-NN search failed for article {article['id']}: {e}")
            return []
