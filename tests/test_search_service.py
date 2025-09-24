"""
Unit tests for SearchService.

This module contains comprehensive tests for the SearchService class,
covering all search functionality, filtering, aggregations, and error handling.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.search_service import SearchService
from components.search.elasticsearch_service import ElasticsearchService


class TestSearchService(unittest.TestCase):
    """Test cases for SearchService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_es_service = Mock(spec=ElasticsearchService)
        self.mock_es_service.enabled = True
        self.search_service = SearchService(elasticsearch_service=self.mock_es_service)

    def test_initialization_with_provided_service(self):
        """Test SearchService initialization with provided ElasticsearchService."""
        service = SearchService(self.mock_es_service)
        self.assertEqual(service.es_service, self.mock_es_service)
        self.assertEqual(service.articles_index, "articles")

    def test_initialization_without_service(self):
        """Test SearchService initialization without provided service."""
        with patch('components.search_service.ElasticsearchService') as mock_es:
            service = SearchService()
            mock_es.assert_called_once()

    def test_is_available_when_enabled_and_healthy(self):
        """Test is_available returns True when ES is enabled and healthy."""
        self.mock_es_service.enabled = True
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.is_available()
        
        self.assertTrue(result)
        self.mock_es_service.is_healthy.assert_called_once()

    def test_is_available_when_disabled(self):
        """Test is_available returns False when ES is disabled."""
        self.mock_es_service.enabled = False
        
        result = self.search_service.is_available()
        
        self.assertFalse(result)
        self.mock_es_service.is_healthy.assert_not_called()

    def test_is_available_when_unhealthy(self):
        """Test is_available returns False when ES is unhealthy."""
        self.mock_es_service.enabled = True
        self.mock_es_service.is_healthy.return_value = False
        
        result = self.search_service.is_available()
        
        self.assertFalse(result)

    def test_build_match_query_with_defaults(self):
        """Test _build_match_query with default parameters."""
        query_text = "test query"
        
        result = self.search_service._build_match_query(query_text)
        
        expected = {
            "multi_match": {
                "query": query_text,
                "fields": ["title^3.0", "keywords^2.5", "summary^2.0", "summary_pt^2.0", "raw_content"],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "and"
            }
        }
        self.assertEqual(result, expected)

    def test_build_match_query_with_custom_fields_and_boosts(self):
        """Test _build_match_query with custom fields and boosts."""
        query_text = "test query"
        fields = ["title", "summary"]
        boosts = {"title": 2.0, "summary": 1.0}
        
        result = self.search_service._build_match_query(query_text, fields, boosts)
        
        expected = {
            "multi_match": {
                "query": query_text,
                "fields": ["title^2.0", "summary"],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "and"
            }
        }
        self.assertEqual(result, expected)

    def test_build_filters_date_range(self):
        """Test _build_filters with date range filters."""
        filters = {
            "date_from": "2023-01-01",
            "date_to": "2023-12-31"
        }
        
        result = self.search_service._build_filters(filters)
        
        expected = [{
            "range": {
                "published_at": {
                    "gte": "2023-01-01",
                    "lte": "2023-12-31"
                }
            }
        }]
        self.assertEqual(result, expected)

    def test_build_filters_categories(self):
        """Test _build_filters with category filters."""
        # Test single category
        filters = {"categories": "technology"}
        result = self.search_service._build_filters(filters)
        expected = [{"term": {"category": "technology"}}]
        self.assertEqual(result, expected)
        
        # Test multiple categories
        filters = {"categories": ["technology", "science"]}
        result = self.search_service._build_filters(filters)
        expected = [{"terms": {"category": ["technology", "science"]}}]
        self.assertEqual(result, expected)

    def test_build_filters_sources(self):
        """Test _build_filters with source filters."""
        filters = {"sources": ["BBC", "CNN"]}
        result = self.search_service._build_filters(filters)
        expected = [{"terms": {"source_name": ["BBC", "CNN"]}}]
        self.assertEqual(result, expected)

    def test_build_filters_urgency_range(self):
        """Test _build_filters with urgency score range."""
        filters = {
            "urgency_min": 0.5,
            "urgency_max": 0.9
        }
        
        result = self.search_service._build_filters(filters)
        
        expected = [{
            "range": {
                "urgency_score": {
                    "gte": 0.5,
                    "lte": 0.9
                }
            }
        }]
        self.assertEqual(result, expected)

    def test_build_sort_criteria_relevance(self):
        """Test _build_sort_criteria for relevance sorting."""
        result = self.search_service._build_sort_criteria("relevance")
        self.assertEqual(result, [])

    def test_build_sort_criteria_date(self):
        """Test _build_sort_criteria for date sorting."""
        result = self.search_service._build_sort_criteria("date", "desc")
        expected = [
            {"published_at": {"order": "desc"}},
            {"_score": {"order": "desc"}}
        ]
        self.assertEqual(result, expected)

    def test_search_articles_success(self):
        """Test search_articles with successful response."""
        # Mock successful ES response
        mock_response = {
            "hits": {
                "total": {"value": 5},
                "hits": [
                    {
                        "_source": {"id": 1, "title": "Test Article 1"},
                        "_score": 2.5
                    },
                    {
                        "_source": {"id": 2, "title": "Test Article 2"},
                        "_score": 2.1
                    }
                ]
            },
            "aggregations": {"categories": {"buckets": []}}
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.search_articles(
            query_text="test",
            page=1,
            page_size=10,
            include_aggregations=True
        )
        
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["hits"]), 2)
        self.assertEqual(result["hits"][0]["id"], 1)
        self.assertEqual(result["hits"][0]["_score"], 2.5)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 10)
        self.assertEqual(result["total_pages"], 1)

    def test_search_articles_service_unavailable(self):
        """Test search_articles when service is unavailable."""
        self.mock_es_service.enabled = False
        
        result = self.search_service.search_articles(query_text="test")
        
        expected = {
            "hits": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "total_pages": 0,
            "aggregations": {}
        }
        self.assertEqual(result, expected)

    def test_search_articles_with_filters(self):
        """Test search_articles with filters applied."""
        filters = {
            "categories": ["technology"],
            "date_from": "2023-01-01"
        }
        
        mock_response = {
            "hits": {
                "total": {"value": 1},
                "hits": []
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.search_articles(
            query_text="test",
            filters=filters
        )
        
        # Verify ES search was called with correct query structure
        self.mock_es_service.search.assert_called_once()
        call_args = self.mock_es_service.search.call_args[1]
        query = call_args["query"]
        
        # Should have both must and filter clauses
        self.assertIn("query", query)
        self.assertIn("bool", query["query"])
        self.assertIn("must", query["query"]["bool"])
        self.assertIn("filter", query["query"]["bool"])

    def test_simple_search_success(self):
        """Test simple_search method."""
        mock_response = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {"_source": {"id": 1, "title": "Article 1"}, "_score": 2.0}
                ]
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.simple_search("test query", limit=5)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_search_by_keywords_or(self):
        """Test search_by_keywords with OR operator."""
        with patch.object(self.search_service, 'simple_search') as mock_simple:
            mock_simple.return_value = [{"id": 1}]
            
            result = self.search_service.search_by_keywords(
                ["python", "programming"], 
                operator="OR"
            )
            
            mock_simple.assert_called_once_with("python OR programming")
            self.assertEqual(result, [{"id": 1}])

    def test_search_by_keywords_and(self):
        """Test search_by_keywords with AND operator."""
        with patch.object(self.search_service, 'simple_search') as mock_simple:
            mock_simple.return_value = [{"id": 1}]
            
            result = self.search_service.search_by_keywords(
                ["python", "programming"], 
                operator="AND"
            )
            
            mock_simple.assert_called_once_with("python AND programming")

    def test_boolean_search_success(self):
        """Test boolean_search with must, should, and must_not queries."""
        mock_response = {
            "hits": {
                "hits": [
                    {"_source": {"id": 1, "title": "Article 1"}, "_score": 2.0}
                ]
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.boolean_search(
            must_queries=["python"],
            should_queries=["programming", "coding"],
            must_not_queries=["javascript"]
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_multi_field_search_success(self):
        """Test multi_field_search with custom parameters."""
        mock_response = {
            "hits": {
                "hits": [
                    {"_source": {"id": 1, "title": "Test Article"}, "_score": 2.0}
                ]
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.multi_field_search(
            query_text="python programming",
            fields=["title", "summary"],
            field_boosts={"title": 2.0, "summary": 1.0},
            match_type="most_fields",
            fuzziness="1",
            operator="or"
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_search_by_date_range_with_datetime_objects(self):
        """Test search_by_date_range with datetime objects."""
        date_from = datetime(2023, 1, 1)
        date_to = date(2023, 12, 31)
        
        with patch.object(self.search_service, 'search_articles') as mock_search:
            mock_search.return_value = {"hits": []}
            
            self.search_service.search_by_date_range(
                date_from=date_from,
                date_to=date_to,
                query_text="test"
            )
            
            call_args = mock_search.call_args[1]
            filters = call_args["filters"]
            
            self.assertEqual(filters["date_from"], "2023-01-01T00:00:00")
            self.assertEqual(filters["date_to"], "2023-12-31")

    def test_search_by_category(self):
        """Test search_by_category method."""
        with patch.object(self.search_service, 'search_articles') as mock_search:
            mock_search.return_value = {"hits": [{"id": 1}]}
            
            result = self.search_service.search_by_category("technology", "AI")
            
            mock_search.assert_called_once()
            call_args = mock_search.call_args[1]
            self.assertEqual(call_args["filters"]["categories"], "technology")
            self.assertEqual(call_args["query_text"], "AI")

    def test_get_search_facets(self):
        """Test get_search_facets method."""
        with patch.object(self.search_service, 'search_articles') as mock_search:
            mock_aggregations = {"categories": {"buckets": []}}
            mock_search.return_value = {"aggregations": mock_aggregations}
            
            result = self.search_service.get_search_facets(
                query_text="test",
                filters={"categories": ["tech"]}
            )
            
            mock_search.assert_called_once_with(
                query_text="test",
                filters={"categories": ["tech"]},
                page_size=0,
                include_aggregations=True
            )
            self.assertEqual(result, mock_aggregations)

    def test_get_category_statistics_success(self):
        """Test get_category_statistics with successful response."""
        mock_response = {
            "aggregations": {
                "categories": {
                    "buckets": [
                        {"key": "technology", "doc_count": 50},
                        {"key": "science", "doc_count": 30}
                    ]
                }
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.enabled = True
        
        result = self.search_service.get_category_statistics()
        
        expected = {"technology": 50, "science": 30}
        self.assertEqual(result, expected)

    def test_get_category_statistics_service_unavailable(self):
        """Test get_category_statistics when service is unavailable."""
        self.mock_es_service.enabled = False
        
        result = self.search_service.get_category_statistics()
        
        self.assertEqual(result, {})

    def test_get_source_statistics_success(self):
        """Test get_source_statistics with successful response."""
        mock_response = {
            "aggregations": {
                "sources": {
                    "buckets": [
                        {"key": "BBC", "doc_count": 100},
                        {"key": "CNN", "doc_count": 80}
                    ]
                }
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.enabled = True
        
        result = self.search_service.get_source_statistics()
        
        expected = {"BBC": 100, "CNN": 80}
        self.assertEqual(result, expected)

    def test_build_aggregations_structure(self):
        """Test _build_aggregations returns correct structure."""
        result = self.search_service._build_aggregations()
        
        # Check that all expected aggregations are present
        expected_keys = [
            "categories", "sources", "sentiments", "regions",
            "date_histogram", "urgency_ranges", "impact_ranges", "has_embedding"
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Check specific aggregation structure
        self.assertEqual(result["categories"]["terms"]["field"], "category")
        self.assertEqual(result["categories"]["terms"]["size"], 20)
        
        # Check range aggregation structure
        urgency_ranges = result["urgency_ranges"]["range"]["ranges"]
        self.assertEqual(len(urgency_ranges), 3)
        self.assertEqual(urgency_ranges[0]["key"], "low")

    def test_advanced_search_complex_query(self):
        """Test advanced_search with multiple field-specific queries."""
        with patch.object(self.search_service, 'boolean_search') as mock_bool:
            mock_bool.return_value = [{"id": 1}]
            
            result = self.search_service.advanced_search(
                query_text="general query",
                title_query="specific title",
                content_query="specific content",
                exact_phrase="exact match",
                exclude_terms=["exclude1", "exclude2"]
            )
            
            mock_bool.assert_called_once()
            # Check that multiple must queries and exclusions were passed
            call_args = mock_bool.call_args[1]
            self.assertIsNotNone(call_args["must_queries"])
            self.assertEqual(call_args["must_not_queries"], ["exclude1", "exclude2"])

    def test_search_with_custom_boosting(self):
        """Test search_with_custom_boosting method."""
        with patch.object(self.search_service, 'multi_field_search') as mock_multi:
            mock_multi.return_value = [{"id": 1}]
            
            result = self.search_service.search_with_custom_boosting(
                query_text="test",
                title_boost=5.0,
                keywords_boost=3.0,
                summary_boost=2.0,
                content_boost=1.0
            )
            
            mock_multi.assert_called_once()
            call_args = mock_multi.call_args[1]
            boosts = call_args["field_boosts"]
            
            self.assertEqual(boosts["title"], 5.0)
            self.assertEqual(boosts["keywords"], 3.0)
            self.assertEqual(boosts["summary"], 2.0)
            self.assertEqual(boosts["raw_content"], 1.0)

    def test_error_handling_in_search_methods(self):
        """Test error handling in various search methods."""
        # Test search_articles with ES exception
        self.mock_es_service.search.side_effect = Exception("ES Error")
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.search_articles(query_text="test")
        
        expected = {
            "hits": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "total_pages": 0,
            "aggregations": {}
        }
        self.assertEqual(result, expected)

    def test_pagination_calculation(self):
        """Test pagination calculation in search_articles."""
        mock_response = {
            "hits": {
                "total": {"value": 25},
                "hits": []
            }
        }
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.search_articles(
            query_text="test",
            page=3,
            page_size=10
        )
        
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["page_size"], 10)
        self.assertEqual(result["total"], 25)
        self.assertEqual(result["total_pages"], 3)

    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        # Test multi_field_search with empty query
        result = self.search_service.multi_field_search("")
        self.assertEqual(result, [])
        
        # Test boolean_search with no queries
        mock_response = {"hits": {"hits": []}}
        self.mock_es_service.search.return_value = mock_response
        self.mock_es_service.is_healthy.return_value = True
        
        result = self.search_service.boolean_search()
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()