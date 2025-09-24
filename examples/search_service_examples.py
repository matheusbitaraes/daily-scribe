"""
Example usage of the SearchService component.

This script demonstrates how to use the SearchService for various types of
searches including full-text search, filtering, aggregations, and more.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.search_service import SearchService


def main():
    """Demonstrate SearchService usage."""
    # Initialize the search service (will use default ElasticsearchService)
    search_service = SearchService()
    
    # Check if search is available
    if not search_service.is_available():
        print("Search service is not available. Please ensure Elasticsearch is running.")
        return
    
    print("SearchService is available and ready!\n")
    
    # Example 1: Simple text search
    print("=== Example 1: Simple Search ===")
    results = search_service.simple_search("artificial intelligence", limit=5)
    print(f"Found {len(results)} articles about 'artificial intelligence'")
    for article in results[:2]:  # Show first 2 results
        print(f"- {article.get('title', 'No title')[:50]}...")
    
    # Example 2: Full search with pagination and filters
    print("\n=== Example 2: Advanced Search with Filters ===")
    filters = {
        "categories": ["technology", "science"],
        "date_from": "2023-01-01",
        "urgency_min": 0.5
    }
    
    search_result = search_service.search_articles(
        query_text="machine learning",
        filters=filters,
        sort_by="urgency",
        sort_order="desc",
        page=1,
        page_size=10,
        include_aggregations=True
    )
    
    print(f"Total results: {search_result['total']}")
    print(f"Page {search_result['page']} of {search_result['total_pages']}")
    print(f"Results on this page: {len(search_result['hits'])}")
    
    # Example 3: Boolean search
    print("\n=== Example 3: Boolean Search ===")
    bool_results = search_service.boolean_search(
        must_queries=["python", "programming"],
        should_queries=["tutorial", "guide"],
        must_not_queries=["javascript", "java"]
    )
    print(f"Boolean search found {len(bool_results)} articles")
    
    # Example 4: Multi-field search with custom boosting
    print("\n=== Example 4: Multi-field Search with Custom Boosting ===")
    custom_results = search_service.search_with_custom_boosting(
        query_text="climate change",
        title_boost=5.0,    # Title very important
        keywords_boost=3.0,  # Keywords important
        summary_boost=2.0,   # Summary somewhat important
        content_boost=1.0    # Content normal importance
    )
    print(f"Custom boosting search found {len(custom_results)} articles")
    
    # Example 5: Category-specific search
    print("\n=== Example 5: Category-specific Search ===")
    tech_articles = search_service.search_by_category("politics", "china")
    print(f"Found {len(tech_articles)} politics articles about china")
    
    # Example 6: Date range search
    print("\n=== Example 6: Date Range Search ===")
    from datetime import datetime, timedelta
    
    # Search for articles from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    recent_articles = search_service.search_by_date_range(
        date_from=start_date,
        date_to=end_date,
        query_text="breaking news"
    )
    print(f"Found {len(recent_articles)} recent articles with 'breaking news'")
    
    # Example 7: Get search facets (aggregations)
    print("\n=== Example 7: Search Facets ===")
    facets = search_service.get_search_facets(
        query_text="artificial intelligence"
    )
    
    if "categories" in facets:
        print("Article categories for AI search:")
        for bucket in facets["categories"]["buckets"][:5]:
            print(f"  - {bucket['key']}: {bucket['doc_count']} articles")
    
    # Example 8: Get statistics
    print("\n=== Example 8: Statistics ===")
    category_stats = search_service.get_category_statistics()
    if category_stats:
        print("Top article categories:")
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:5]:
            print(f"  - {category}: {count} articles")
    
    source_stats = search_service.get_source_statistics()
    if source_stats:
        print("\nTop news sources:")
        sorted_sources = sorted(source_stats.items(), key=lambda x: x[1], reverse=True)
        for source, count in sorted_sources[:5]:
            print(f"  - {source}: {count} articles")


if __name__ == "__main__":
    main()