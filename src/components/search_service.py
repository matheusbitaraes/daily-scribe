"""
Search service for Daily Scribe application.

This module provides advanced search capabilities including full-text search,
boolean queries, filtering, aggregations, and sorting using Elasticsearch.
"""
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date

from components.elasticsearch_service import ElasticsearchService


class SearchService:
    """
    Provides advanced search capabilities for Daily Scribe articles.
    
    This service builds on top of ElasticsearchService to provide:
    - Full-text search across article fields
    - Boolean query support (AND, OR, NOT)
    - Multi-field search with field boosting
    - Advanced filtering (date ranges, categories, sources)
    - Aggregations for faceted search results
    - Sorting by relevance, date, and other fields
    """

    def __init__(self, elasticsearch_service: Optional[ElasticsearchService] = None):
        """
        Initialize the search service.

        Args:
            elasticsearch_service: ElasticsearchService instance. If None, creates a new one.
        """
        self.logger = logging.getLogger(__name__)
        self.es_service = elasticsearch_service or ElasticsearchService()
        
        # Default field boosting for multi-field search
        self.default_field_boosts = {
            "title": 3.0,
            "keywords": 2.5,
            "summary": 2.0,
            "summary_pt": 2.0,
            "raw_content": 1.0
        }
        
        # Default index type for articles
        self.articles_index = "articles"

    def is_available(self) -> bool:
        """
        Check if search service is available.
        
        Returns:
            True if Elasticsearch is healthy and service is ready, False otherwise.
        """
        if not self.es_service.enabled:
            return False
        return self.es_service.is_healthy()

    def _build_match_query(self, query_text: str, fields: Optional[List[str]] = None, 
                          field_boosts: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Build a multi-match query with field boosting.
        
        Args:
            query_text: The text to search for.
            fields: List of fields to search in. If None, uses default fields.
            field_boosts: Field boosting configuration. If None, uses defaults.
            
        Returns:
            Elasticsearch multi_match query dictionary.
        """
        if fields is None:
            fields = list(self.default_field_boosts.keys())
            
        if field_boosts is None:
            field_boosts = self.default_field_boosts
            
        # Build fields with boost values
        boosted_fields = []
        for field in fields:
            boost = field_boosts.get(field, 1.0)
            if boost != 1.0:
                boosted_fields.append(f"{field}^{boost}")
            else:
                boosted_fields.append(field)
        
        return {
            "multi_match": {
                "query": query_text,
                "fields": boosted_fields,
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "and"
            }
        }

    def _build_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build filter clauses from filter dictionary.
        
        Args:
            filters: Dictionary of filter criteria.
            
        Returns:
            List of Elasticsearch filter clauses.
        """
        filter_clauses = []
        
        # Date range filters
        if "date_from" in filters or "date_to" in filters:
            date_range = {}
            if "date_from" in filters:
                date_range["gte"] = filters["date_from"]
            if "date_to" in filters:
                date_range["lte"] = filters["date_to"]
            
            filter_clauses.append({
                "range": {
                    "published_at": date_range
                }
            })
        
        # Category filter
        if "categories" in filters and filters["categories"]:
            if isinstance(filters["categories"], list):
                # Normalize categories to lowercase for case-insensitive matching
                normalized_categories = [cat.lower() for cat in filters["categories"]]
                filter_clauses.append({
                    "terms": {
                        "category": normalized_categories
                    }
                })
            else:
                # Normalize single category to lowercase
                filter_clauses.append({
                    "term": {
                        "category": filters["categories"].lower()
                    }
                })
        
        # Source filter
        if "sources" in filters and filters["sources"]:
            if isinstance(filters["sources"], list):
                filter_clauses.append({
                    "terms": {
                        "source_name": filters["sources"]
                    }
                })
            else:
                filter_clauses.append({
                    "term": {
                        "source_name": filters["sources"]
                    }
                })
        
        # Source ID filter
        if "source_ids" in filters and filters["source_ids"]:
            if isinstance(filters["source_ids"], list):
                filter_clauses.append({
                    "terms": {
                        "source_id": filters["source_ids"]
                    }
                })
            else:
                filter_clauses.append({
                    "term": {
                        "source_id": filters["source_ids"]
                    }
                })
        
        # Sentiment filter
        if "sentiments" in filters and filters["sentiments"]:
            if isinstance(filters["sentiments"], list):
                filter_clauses.append({
                    "terms": {
                        "sentiment": filters["sentiments"]
                    }
                })
            else:
                filter_clauses.append({
                    "term": {
                        "sentiment": filters["sentiments"]
                    }
                })
        
        # Region filter
        if "regions" in filters and filters["regions"]:
            if isinstance(filters["regions"], list):
                filter_clauses.append({
                    "terms": {
                        "region": filters["regions"]
                    }
                })
            else:
                filter_clauses.append({
                    "term": {
                        "region": filters["regions"]
                    }
                })
        
        # Urgency score range
        if "urgency_min" in filters or "urgency_max" in filters:
            urgency_range = {}
            if "urgency_min" in filters:
                urgency_range["gte"] = filters["urgency_min"]
            if "urgency_max" in filters:
                urgency_range["lte"] = filters["urgency_max"]
            
            filter_clauses.append({
                "range": {
                    "urgency_score": urgency_range
                }
            })
        
        # Impact score range
        if "impact_min" in filters or "impact_max" in filters:
            impact_range = {}
            if "impact_min" in filters:
                impact_range["gte"] = filters["impact_min"]
            if "impact_max" in filters:
                impact_range["lte"] = filters["impact_max"]
            
            filter_clauses.append({
                "range": {
                    "impact_score": impact_range
                }
            })
        
        # Has embedding filter
        if "has_embedding" in filters:
            filter_clauses.append({
                "term": {
                    "has_embedding": filters["has_embedding"]
                }
            })
        
        return filter_clauses

    def _build_sort_criteria(self, sort_by: str = "relevance", sort_order: str = "desc") -> List[Dict[str, Any]]:
        """
        Build sort criteria for search results.
        
        Args:
            sort_by: Field to sort by ('relevance', 'date', 'urgency', 'impact').
            sort_order: Sort order ('asc' or 'desc').
            
        Returns:
            List of Elasticsearch sort criteria.
        """
        if sort_by == "relevance":
            # For relevance, we don't add explicit sort - ES uses _score by default
            return []
        
        sort_field_mapping = {
            "date": "published_at",
            "published_date": "published_at",
            "processed_date": "processed_at",
            "urgency": "urgency_score",
            "impact": "impact_score"
        }
        
        field = sort_field_mapping.get(sort_by, sort_by)
        
        return [
            {field: {"order": sort_order}},
            {"_score": {"order": "desc"}}  # Secondary sort by relevance
        ]

    def search_articles(self, 
                       query_text: Optional[str] = None,
                       filters: Optional[Dict[str, Any]] = None,
                       sort_by: str = "relevance",
                       sort_order: str = "desc",
                       page: int = 1,
                       page_size: int = 10,
                       include_aggregations: bool = False) -> Dict[str, Any]:
        """
        Perform a comprehensive search for articles.
        
        Args:
            query_text: Text to search for. If None, returns all articles matching filters.
            filters: Dictionary of filter criteria.
            sort_by: Field to sort by ('relevance', 'date', 'urgency', 'impact').
            sort_order: Sort order ('asc' or 'desc').
            page: Page number (1-based).
            page_size: Number of results per page.
            include_aggregations: Whether to include aggregation data.
            
        Returns:
            Dictionary containing search results, pagination info, and aggregations.
        """
        if not self.is_available():
            self.logger.warning("Search service not available")
            return {
                "hits": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "aggregations": {}
            }
        
        # Calculate pagination
        from_offset = (page - 1) * page_size
        
        # Build the query
        query = {"query": {"bool": {}}}
        
        # Add text search if provided
        if query_text and query_text.strip():
            query["query"]["bool"]["must"] = [
                self._build_match_query(query_text.strip())
            ]
        else:
            query["query"]["bool"]["must"] = [{"match_all": {}}]
        
        # Add filters if provided
        if filters:
            filter_clauses = self._build_filters(filters)
            if filter_clauses:
                query["query"]["bool"]["filter"] = filter_clauses
        
        # Add sorting
        sort_criteria = self._build_sort_criteria(sort_by, sort_order)
        if sort_criteria:
            query["sort"] = sort_criteria
        
        # Add aggregations if requested
        if include_aggregations:
            query["aggs"] = self._build_aggregations()
        
        # Execute search
        try:
            result = self.es_service.search(
                index_type=self.articles_index,
                query=query,
                size=page_size,
                from_=from_offset
            )
            
            if not result:
                return {
                    "hits": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "aggregations": {}
                }
            
            # Extract results
            hits = []
            for hit in result.get("hits", {}).get("hits", []):
                article = hit["_source"]
                article["_score"] = hit.get("_score")
                hits.append(article)
            
            # Calculate pagination info
            total_hits = result.get("hits", {}).get("total", {})
            if isinstance(total_hits, dict):
                total = total_hits.get("value", 0)
            else:
                total = total_hits
            
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
            
            return {
                "hits": hits,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "aggregations": result.get("aggregations", {})
            }
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {
                "hits": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "aggregations": {}
            }

    def simple_search(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a simple text search with minimal configuration.
        
        Args:
            query_text: Text to search for.
            limit: Maximum number of results to return.
            
        Returns:
            List of article dictionaries.
        """
        result = self.search_articles(
            query_text=query_text,
            page_size=limit,
            page=1
        )
        
        return result.get("hits", [])

    def search_by_keywords(self, keywords: List[str], operator: str = "OR") -> List[Dict[str, Any]]:
        """
        Search articles by specific keywords.
        
        Args:
            keywords: List of keywords to search for.
            operator: Boolean operator ('AND' or 'OR').
            
        Returns:
            List of matching articles.
        """
        if not keywords:
            return []
        
        # Join keywords with the specified operator
        if operator.upper() == "AND":
            query_text = " AND ".join(keywords)
        else:
            query_text = " OR ".join(keywords)
        
        return self.simple_search(query_text)

    def boolean_search(self, 
                      must_queries: Optional[List[str]] = None,
                      should_queries: Optional[List[str]] = None,
                      must_not_queries: Optional[List[str]] = None,
                      filters: Optional[Dict[str, Any]] = None,
                      minimum_should_match: int = 1) -> List[Dict[str, Any]]:
        """
        Perform a boolean search with explicit AND, OR, NOT logic.
        
        Args:
            must_queries: Queries that MUST match (AND logic).
            should_queries: Queries that SHOULD match (OR logic).
            must_not_queries: Queries that MUST NOT match (NOT logic).
            filters: Additional filters to apply.
            minimum_should_match: Minimum number of should queries that must match.
            
        Returns:
            List of matching articles.
        """
        if not self.is_available():
            return []
        
        # Build the boolean query
        bool_query = {"bool": {}}
        
        # Add must clauses (AND)
        if must_queries:
            bool_query["bool"]["must"] = [
                self._build_match_query(query) for query in must_queries
            ]
        
        # Add should clauses (OR)
        if should_queries:
            bool_query["bool"]["should"] = [
                self._build_match_query(query) for query in should_queries
            ]
            bool_query["bool"]["minimum_should_match"] = minimum_should_match
        
        # Add must_not clauses (NOT)
        if must_not_queries:
            bool_query["bool"]["must_not"] = [
                self._build_match_query(query) for query in must_not_queries
            ]
        
        # Add filters
        if filters:
            filter_clauses = self._build_filters(filters)
            if filter_clauses:
                bool_query["bool"]["filter"] = filter_clauses
        
        # If no queries provided, match all
        if not any([must_queries, should_queries, must_not_queries]):
            bool_query = {"match_all": {}}
        
        query = {"query": bool_query}
        
        try:
            result = self.es_service.search(
                index_type=self.articles_index,
                query=query,
                size=100  # Default limit for boolean search
            )
            
            if not result:
                return []
            
            hits = []
            for hit in result.get("hits", {}).get("hits", []):
                article = hit["_source"]
                article["_score"] = hit.get("_score")
                hits.append(article)
            
            return hits
            
        except Exception as e:
            self.logger.error(f"Boolean search failed: {e}")
            return []

    def advanced_search(self, 
                       query_text: Optional[str] = None,
                       title_query: Optional[str] = None,
                       content_query: Optional[str] = None,
                       keyword_query: Optional[str] = None,
                       exact_phrase: Optional[str] = None,
                       exclude_terms: Optional[List[str]] = None,
                       **kwargs) -> List[Dict[str, Any]]:
        """
        Perform an advanced search with field-specific queries.
        
        Args:
            query_text: General text query across all fields.
            title_query: Query specifically for article titles.
            content_query: Query specifically for article content.
            keyword_query: Query specifically for keywords.
            exact_phrase: Exact phrase to match.
            exclude_terms: Terms to exclude from results.
            **kwargs: Additional arguments passed to search_articles.
            
        Returns:
            List of matching articles.
        """
        if not self.is_available():
            return []
        
        # Build complex boolean query
        must_queries = []
        must_not_queries = []
        
        # Add general text query
        if query_text:
            must_queries.append(query_text)
        
        # Add field-specific queries
        if title_query or content_query or keyword_query:
            field_queries = []
            
            if title_query:
                field_queries.append(f"title:({title_query})")
            
            if content_query:
                field_queries.append(f"raw_content:({content_query}) OR summary:({content_query})")
            
            if keyword_query:
                field_queries.append(f"keywords:({keyword_query})")
            
            if field_queries:
                must_queries.append(" OR ".join(field_queries))
        
        # Add exact phrase matching
        if exact_phrase:
            must_queries.append(f'"{exact_phrase}"')
        
        # Add exclusions
        if exclude_terms:
            must_not_queries.extend(exclude_terms)
        
        # Use boolean search if we have complex queries
        if len(must_queries) > 1 or must_not_queries:
            return self.boolean_search(
                must_queries=must_queries if len(must_queries) > 1 else None,
                should_queries=[must_queries[0]] if len(must_queries) == 1 else None,
                must_not_queries=must_not_queries if must_not_queries else None,
                filters=kwargs.get("filters")
            )
        
        # Otherwise use simple search
        if must_queries:
            result = self.search_articles(query_text=must_queries[0], **kwargs)
            return result.get("hits", [])
        
        return []

    def multi_field_search(self, 
                          query_text: str,
                          fields: Optional[List[str]] = None,
                          field_boosts: Optional[Dict[str, float]] = None,
                          match_type: str = "best_fields",
                          fuzziness: str = "AUTO",
                          operator: str = "and") -> List[Dict[str, Any]]:
        """
        Perform a multi-field search with customizable field boosting.
        
        Args:
            query_text: Text to search for.
            fields: List of fields to search in. If None, uses all searchable fields.
            field_boosts: Field boosting configuration. If None, uses defaults.
            match_type: Type of multi-match query ('best_fields', 'most_fields', 'cross_fields').
            fuzziness: Fuzziness level for fuzzy matching ('0', '1', '2', 'AUTO').
            operator: Boolean operator for terms ('and', 'or').
            
        Returns:
            List of matching articles.
        """
        if not self.is_available() or not query_text.strip():
            return []
        
        # Use provided fields or defaults
        search_fields = fields or list(self.default_field_boosts.keys())
        boosts = field_boosts or self.default_field_boosts
        
        # Build the multi-match query with custom parameters
        query = {
            "query": {
                "multi_match": {
                    "query": query_text.strip(),
                    "fields": [
                        f"{field}^{boosts.get(field, 1.0)}" if boosts.get(field, 1.0) != 1.0 else field
                        for field in search_fields
                    ],
                    "type": match_type,
                    "fuzziness": fuzziness,
                    "operator": operator
                }
            }
        }
        
        try:
            result = self.es_service.search(
                index_type=self.articles_index,
                query=query,
                size=50
            )
            
            if not result:
                return []
            
            hits = []
            for hit in result.get("hits", {}).get("hits", []):
                article = hit["_source"]
                article["_score"] = hit.get("_score")
                hits.append(article)
            
            return hits
            
        except Exception as e:
            self.logger.error(f"Multi-field search failed: {e}")
            return []

    def search_with_custom_boosting(self, 
                                   query_text: str,
                                   title_boost: float = 3.0,
                                   keywords_boost: float = 2.5,
                                   summary_boost: float = 2.0,
                                   content_boost: float = 1.0) -> List[Dict[str, Any]]:
        """
        Search with custom field boosting values.
        
        Args:
            query_text: Text to search for.
            title_boost: Boost value for title field.
            keywords_boost: Boost value for keywords field.
            summary_boost: Boost value for summary fields.
            content_boost: Boost value for content field.
            
        Returns:
            List of matching articles.
        """
        custom_boosts = {
            "title": title_boost,
            "keywords": keywords_boost,
            "summary": summary_boost,
            "summary_pt": summary_boost,
            "raw_content": content_boost
        }
        
        return self.multi_field_search(
            query_text=query_text,
            field_boosts=custom_boosts
        )

    def search_by_date_range(self, 
                           date_from: Optional[Union[str, datetime, date]] = None,
                           date_to: Optional[Union[str, datetime, date]] = None,
                           query_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search articles within a specific date range.
        
        Args:
            date_from: Start date (inclusive).
            date_to: End date (inclusive).
            query_text: Optional text query.
            
        Returns:
            List of matching articles.
        """
        filters = {}
        
        if date_from:
            if isinstance(date_from, (datetime, date)):
                date_from = date_from.isoformat()
            filters["date_from"] = date_from
            
        if date_to:
            if isinstance(date_to, (datetime, date)):
                date_to = date_to.isoformat()
            filters["date_to"] = date_to
        
        result = self.search_articles(
            query_text=query_text,
            filters=filters,
            page_size=100
        )
        
        return result.get("hits", [])

    def search_by_category(self, 
                          categories: Union[str, List[str]], 
                          query_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search articles by category.
        
        Args:
            categories: Category name or list of category names.
            query_text: Optional text query.
            
        Returns:
            List of matching articles.
        """
        filters = {"categories": categories}
        
        result = self.search_articles(
            query_text=query_text,
            filters=filters,
            page_size=100
        )
        
        return result.get("hits", [])

    def search_by_source(self, 
                        sources: Union[str, List[str]], 
                        query_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search articles by source.
        
        Args:
            sources: Source name or list of source names.
            query_text: Optional text query.
            
        Returns:
            List of matching articles.
        """
        filters = {"sources": sources}
        
        result = self.search_articles(
            query_text=query_text,
            filters=filters,
            page_size=100
        )
        
        return result.get("hits", [])

    def search_by_sentiment(self, 
                           sentiments: Union[str, List[str]], 
                           query_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search articles by sentiment.
        
        Args:
            sentiments: Sentiment value or list of sentiment values.
            query_text: Optional text query.
            
        Returns:
            List of matching articles.
        """
        filters = {"sentiments": sentiments}
        
        result = self.search_articles(
            query_text=query_text,
            filters=filters,
            page_size=100
        )
        
        return result.get("hits", [])

    def search_by_urgency_range(self, 
                               min_urgency: Optional[float] = None,
                               max_urgency: Optional[float] = None,
                               query_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search articles by urgency score range.
        
        Args:
            min_urgency: Minimum urgency score.
            max_urgency: Maximum urgency score.
            query_text: Optional text query.
            
        Returns:
            List of matching articles.
        """
        filters = {}
        
        if min_urgency is not None:
            filters["urgency_min"] = min_urgency
            
        if max_urgency is not None:
            filters["urgency_max"] = max_urgency
        
        result = self.search_articles(
            query_text=query_text,
            filters=filters,
            page_size=100
        )
        
        return result.get("hits", [])

    def _build_aggregations(self) -> Dict[str, Any]:
        """
        Build aggregation queries for faceted search results.
        
        Returns:
            Dictionary of aggregation configurations.
        """
        return {
            "categories": {
                "terms": {
                    "field": "category",
                    "size": 20,
                    "missing": "unknown"
                }
            },
            "sources": {
                "terms": {
                    "field": "source_name",
                    "size": 50,
                    "missing": "unknown"
                }
            },
            "sentiments": {
                "terms": {
                    "field": "sentiment",
                    "size": 10,
                    "missing": "unknown"
                }
            },
            "regions": {
                "terms": {
                    "field": "region",
                    "size": 30,
                    "missing": "unknown"
                }
            },
            "date_histogram": {
                "date_histogram": {
                    "field": "published_at",
                    "calendar_interval": "day",
                    "min_doc_count": 1,
                    "format": "yyyy-MM-dd"
                }
            },
            "urgency_ranges": {
                "range": {
                    "field": "urgency_score",
                    "ranges": [
                        {"key": "low", "to": 0.3},
                        {"key": "medium", "from": 0.3, "to": 0.7},
                        {"key": "high", "from": 0.7}
                    ]
                }
            },
            "impact_ranges": {
                "range": {
                    "field": "impact_score",
                    "ranges": [
                        {"key": "low", "to": 0.3},
                        {"key": "medium", "from": 0.3, "to": 0.7},
                        {"key": "high", "from": 0.7}
                    ]
                }
            },
            "has_embedding": {
                "terms": {
                    "field": "has_embedding",
                    "size": 2
                }
            }
        }

    def get_search_facets(self, 
                         query_text: Optional[str] = None,
                         filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get faceted search results showing available filter options.
        
        Args:
            query_text: Optional text query to scope the facets.
            filters: Optional filters to apply before generating facets.
            
        Returns:
            Dictionary containing facet counts for each category.
        """
        result = self.search_articles(
            query_text=query_text,
            filters=filters,
            page_size=0,  # We only want aggregations, not results
            include_aggregations=True
        )
        
        return result.get("aggregations", {})

    def get_category_statistics(self) -> Dict[str, int]:
        """
        Get article count statistics by category.
        
        Returns:
            Dictionary mapping category names to article counts.
        """
        if not self.is_available():
            return {}
        
        query = {
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "category",
                        "size": 100
                    }
                }
            }
        }
        
        try:
            result = self.es_service.search(
                index_type=self.articles_index,
                query=query,
                size=0
            )
            
            if not result or "aggregations" not in result:
                return {}
            
            categories = {}
            for bucket in result["aggregations"]["categories"]["buckets"]:
                categories[bucket["key"]] = bucket["doc_count"]
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to get category statistics: {e}")
            return {}

    def get_source_statistics(self) -> Dict[str, int]:
        """
        Get article count statistics by source.
        
        Returns:
            Dictionary mapping source names to article counts.
        """
        if not self.is_available():
            return {}
        
        query = {
            "aggs": {
                "sources": {
                    "terms": {
                        "field": "source_name",
                        "size": 100
                    }
                }
            }
        }
        
        try:
            result = self.es_service.search(
                index_type=self.articles_index,
                query=query,
                size=0
            )
            
            if not result or "aggregations" not in result:
                return {}
            
            sources = {}
            for bucket in result["aggregations"]["sources"]["buckets"]:
                sources[bucket["key"]] = bucket["doc_count"]
            
            return sources
            
        except Exception as e:
            self.logger.error(f"Failed to get source statistics: {e}")
            return {}