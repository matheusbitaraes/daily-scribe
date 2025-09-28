"""
DigestBuilder service for Daily Scribe application.

This module handles building the HTML digest from article summaries.
"""

import os
from typing import List, Dict
from collections import defaultdict
from urllib.parse import quote
from pybars import Compiler
import logging
from utils.categories import STANDARD_CATEGORY_ORDER, CATEGORY_TRANSLATIONS

class DigestBuilder:
    def __init__(self, template_dir: str = None):
        """
        Initialize DigestBuilder with template directory.
        
        Args:
            template_dir: Directory containing Handlebars templates. 
                         Defaults to 'templates' in project root.
        """
        if template_dir is None:
            # Get the project root directory (assumes this file is in src/components/ and the templates folder is in src/templates/)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            template_dir = os.path.join(project_root, 'src/templates')
        
        self.template_dir = template_dir
        self.compiler = Compiler()
        self._templates = {}
        self.logger = logging.getLogger(__name__)
    
    def _load_template(self, template_name: str):
        """Load and compile a Handlebars template."""
        if template_name not in self._templates:
            template_path = os.path.join(self.template_dir, template_name)
            
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template not found: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_source = f.read()
            
            self._templates[template_name] = self.compiler.compile(template_source)
        
        return self._templates[template_name]
    
    @staticmethod
    def wrap_with_redirect_page(url: str, base_url: str) -> str:
        """
        Wrap an external URL with the redirect page to hide external domains in emails.
        
        Args:
            url: The original URL to wrap
            base_url: The base URL of the application
            
        Returns:
            The wrapped URL using the redirect page
        """
        if not url:
            return url
            
        # URL encode the original URL to safely pass it as a query parameter
        encoded_url = quote(url, safe='')
        
        # Return the redirect URL
        return f"{base_url}/redirect?url={encoded_url}"
    
    def build_html_digest(self, clustered_summaries: List[List[Dict[str, str]]], preference_token: str = "", unsubscribe_link_html: str = "", max_clusters: int = 20, base_url: str = "http://localhost:3000", template_name: str = "digest_v2.hbs") -> str:
        """
        Build HTML digest using Handlebars template.
        
        Args:
            clustered_summaries: List of article clusters
            preference_token: Token for preference management links
            unsubscribe_link_html: HTML for unsubscribe link
            max_clusters: Maximum number of clusters to include
            base_url: Base URL for the application
            template_name: Name of the template file to use
            
        Returns:
            Rendered HTML digest
        """
        # Choose data preparation method based on template
        if template_name.startswith("digest_v2"):
            template_data = self._prepare_template_data_v2(
                clustered_summaries, 
                preference_token, 
                unsubscribe_link_html, 
                max_clusters, 
                base_url
            )
        else:
            template_data = self._prepare_template_data(
                clustered_summaries, 
                preference_token, 
                unsubscribe_link_html, 
                max_clusters, 
                base_url
            )
        
        # Load and render template
        template = self._load_template(template_name)
        return template(template_data)
    
    # todo: remove this method - this should exist only in news_curator!
    def get_cluster_sort_key(self, cluster):
        # Sort all clusters by urgency + impact scores (highest first), then by size (largest first)
        if not cluster:
            return (0, 0, 0)
        main_article = cluster[0]
        urgency_raw = main_article.get('urgency_score', 0) or 0
        impact_raw = main_article.get('impact_score', 0) or 0

        # convert impact score to 1-5 scale
        def convert_score(score):
            return max(1, min(5, int(round(score/20))))  # convert 0-100 to 1-5 scale
            
        urgency = convert_score(urgency_raw)
        impact = convert_score(impact_raw)

        cluster_size = len(cluster) - 1 
        # return a weighted comparisson where urgency + impact is primary and size is secondary
        CLUSTERIZATION_TOP_K = int(os.getenv("CLUSTERIZATION_TOP_K", 20))
        normalized_cluster_size = cluster_size / CLUSTERIZATION_TOP_K if CLUSTERIZATION_TOP_K > 0 else 0

        normalized_urgency_impact_score = (urgency + impact) / 10  # max combined score is 10

        urgency_impact_weighted = normalized_urgency_impact_score * 0.7
        cluster_size_weighted = normalized_cluster_size * 0.3
        score = urgency_impact_weighted + cluster_size_weighted if cluster_size > 0 else 0
        return -score

    # todo: remove this method - this should exist only in news_curator!
    def sort_clusters(self, clusters, limit=None):
        sorted_clusters = sorted(clusters, key=self.get_cluster_sort_key)
        if limit is not None:
            sorted_clusters = sorted_clusters[:limit]


        # log status for first 10 clusters, showing urgency + impact and size
        for i, cluster in enumerate(sorted_clusters[:10]):
            main_article = cluster[0]
            urgency = main_article.get('urgency_score', 0) or 0
            impact = main_article.get('impact_score', 0) or 0
            cluster_size = len(cluster)
            sort_key = self.get_cluster_sort_key(cluster)
            self.logger.debug(f"Cluster {i+1}: Urgency + Impact = {urgency + impact}, Size = {cluster_size}, Sort Key = {sort_key}, Title = {main_article.get('title', '')[:20]}...")

        return sorted_clusters

    
    def _prepare_template_data(self, clustered_summaries: List[List[Dict[str, str]]], preference_token: str, unsubscribe_link_html: str, max_clusters: int, base_url: str) -> Dict:
        """Prepare data structure for Handlebars template."""
        # Group clusters by category
        categories_dict = defaultdict(list)
        for cluster in clustered_summaries:
            if cluster:
                # Use the first article's category for the entire cluster
                category = cluster[0].get('category', 'Other') or 'Other'
                category_pt = CATEGORY_TRANSLATIONS.get(category, category)
                categories_dict[category_pt].append(cluster)

        # Process categories in the specified order
        categories_list = []
        cluster_count = 0
        max_clusters_reached = False
        
        # Calculate how many categories actually have content
        active_categories = [category_en for category_en in STANDARD_CATEGORY_ORDER 
                           if CATEGORY_TRANSLATIONS.get(category_en, category_en) in categories_dict]
        
        # Calculate clusters per category (distribute evenly)
        clusters_per_category = max_clusters // len(active_categories) if active_categories else max_clusters
        remaining_clusters = max_clusters % len(active_categories) if active_categories else 0
        
        for category_index, category_en in enumerate(STANDARD_CATEGORY_ORDER):
            if max_clusters_reached:
                break
                
            category_pt = CATEGORY_TRANSLATIONS.get(category_en, category_en)
            if category_pt in categories_dict:
                # Calculate limit for this category (add 1 extra to first categories if there's remainder)
                category_limit = clusters_per_category + (1 if category_index < remaining_clusters else 0)
                category_cluster_count = 0

                sorted_clusters = self.sort_clusters(categories_dict[category_pt])

                processed_clusters = []
                for cluster in sorted_clusters:
                    # Check if adding this cluster would exceed the category or global limit
                    if category_cluster_count >= category_limit or cluster_count >= max_clusters:
                        if cluster_count >= max_clusters:
                            max_clusters_reached = True
                        break
                    
                    cluster_count += 1
                    category_cluster_count += 1
                    
                    # Process main article
                    main_article = cluster[0]
                    source = main_article.get('source_name') or 'link'
                    
                    # Use Portuguese summary if available, otherwise fallback to English
                    preferred_summary = main_article.get('summary_pt') or main_article.get('summary', '')
                    
                    # Use Portuguese title if available, otherwise fallback to original title
                    preferred_title = main_article.get('title_pt') or main_article.get('title', '')
                    
                    # Wrap the main article URL with redirect page
                    wrapped_url = DigestBuilder.wrap_with_redirect_page(main_article['url'], base_url)
                    
                    # Process related articles
                    related_articles = []
                    if len(cluster) > 1:
                        for article in cluster[1:]:
                            related_source = article.get('source_name')
                            
                            # Use Portuguese title if available, otherwise fallback to original title
                            preferred_related_title = article.get('title_pt') or article.get('title', '')
                            
                            if not related_source:
                                display_title = preferred_related_title
                            else:
                                display_title = f"[{related_source}] {preferred_related_title}"
                            
                            # Wrap the related article URL with redirect page
                            wrapped_related_url = DigestBuilder.wrap_with_redirect_page(article['url'], base_url)
                            
                            related_articles.append({
                                'wrapped_url': wrapped_related_url,
                                'display_title': display_title
                            })
                    
                    processed_clusters.append({
                        'main_article': {
                            'preferred_title': preferred_title,
                            'preferred_summary': preferred_summary,
                            'wrapped_url': wrapped_url,
                            'source': source
                        },
                        'related_articles': related_articles if related_articles else None
                    })
                
                if processed_clusters:
                    categories_list.append({
                        'name': category_pt,
                        'clusters': processed_clusters
                    })
        
        return {
            'categories': categories_list,
            'preference_token': preference_token if preference_token else None,
            'base_url': base_url,
            'unsubscribe_link_html': unsubscribe_link_html if unsubscribe_link_html else None
        }

    def _prepare_template_data_v2(self, clustered_summaries: List[List[Dict[str, str]]], preference_token: str, unsubscribe_link_html: str, max_clusters: int, base_url: str) -> Dict:
        """Prepare data structure for v2 Handlebars templates with main_news and category_links sections."""
        # Keep the original order from clustered_summaries
        # Add category information to each cluster while preserving order
        all_clusters = []
        for cluster in clustered_summaries:
            if cluster:
                # Use the first article's category for the entire cluster
                category = cluster[0].get('category', 'Other') or 'Other'
                category_pt = CATEGORY_TRANSLATIONS.get(category, category)
                all_clusters.append((cluster, category_pt))

        # Split into main_news (top clusters with full content) and category_links (remaining as links)
        # Preserve the original order from clustered_summaries
        MAIN_ARTICLES_NUMBER_FOR_BODY = int(os.getenv("MAIN_ARTICLES_NUMBER_FOR_BODY", 4))
        main_news_count = min(MAIN_ARTICLES_NUMBER_FOR_BODY, len(all_clusters))  # Show top news regardless of total
        main_news_clusters = all_clusters[:main_news_count]
        remaining_clusters = all_clusters[main_news_count:]

        # Prepare main_news section
        main_news = []
        for cluster, category_pt in main_news_clusters:
            main_article = cluster[0]
            source = main_article.get('source_name') or 'link'
            
            # Use Portuguese summary if available, otherwise fallback to English
            preferred_summary = main_article.get('summary_pt') or main_article.get('summary', '')
            
            # Use Portuguese title if available, otherwise fallback to original title
            preferred_title = main_article.get('title_pt') or main_article.get('title', '')
            
            # Wrap the main article URL with redirect page
            wrapped_url = DigestBuilder.wrap_with_redirect_page(main_article['url'], base_url)
            
            # Process related articles
            related_articles = []
            has_more_related = False
            additional_related_count = 0
            
            if len(cluster) > 1:
                all_related = cluster[1:]  # All articles except the main one
                
                # Limit to first 4 related articles for display
                displayed_related = all_related[:4]
                
                # Check if there are more than 4 related articles
                if len(all_related) > 4:
                    has_more_related = True
                    additional_related_count = len(all_related) - 4
                
                for article in displayed_related:
                    related_source = article.get('source_name')
                    
                    # Use Portuguese title if available, otherwise fallback to original title
                    preferred_related_title = article.get('title_pt') or article.get('title', '')
                    
                    if not related_source:
                        display_title = preferred_related_title
                    else:
                        display_title = f"[{related_source}] {preferred_related_title}"
                    
                    # Wrap the related article URL with redirect page
                    wrapped_related_url = DigestBuilder.wrap_with_redirect_page(article['url'], base_url)
                    
                    related_articles.append({
                        'wrapped_url': wrapped_related_url,
                        'display_title': display_title
                    })
            
            main_news.append({
                'category': category_pt,
                'main_article': {
                    'preferred_title': preferred_title,
                    'preferred_summary': preferred_summary,
                    'wrapped_url': wrapped_url,
                    'source': source,
                    'article_id': main_article.get('id')  # Add article_id for the "view more" link
                },
                'related_articles': related_articles if related_articles else None,
                'has_more_related': has_more_related,
                'additional_related_count': additional_related_count
            })

        # Prepare category_links section
        # Group remaining clusters by category while preserving relative order within categories
        category_links_dict = defaultdict(list)
        for cluster, category_pt in remaining_clusters:
            main_article = cluster[0]
            similar_news_count = len(cluster) - 1  # Exclude main article
            
            # Use Portuguese title if available, otherwise fallback to original title
            preferred_title = main_article.get('title_pt') or main_article.get('title', '')
            
            category_links_dict[category_pt].append({
                'article_id': main_article.get('id'),
                'preferred_title': preferred_title,
                'category': category_pt,
                'similar_news_count': similar_news_count
            })

        # Convert to list format ordered by STANDARD_CATEGORY_ORDER
        # This preserves the relative order within each category from the original clustered_summaries
        category_links = []
        for category_en in STANDARD_CATEGORY_ORDER:
            category_pt = CATEGORY_TRANSLATIONS.get(category_en, category_en)
            if category_pt in category_links_dict:
                category_links.append({
                    'category_name': category_pt,
                    'articles': category_links_dict[category_pt],
                    'num_similar_news': len(category_links_dict[category_pt])
                })

        return {
            'main_news': main_news if main_news else None,
            'category_links': category_links if category_links else None,
            'preference_token': preference_token if preference_token else None,
            'base_url': base_url,
            'unsubscribe_link_html': unsubscribe_link_html if unsubscribe_link_html else None
        }

    @staticmethod
    def _get_cluster_date(cluster: List[Dict[str, str]]) -> float:
        """Get the date of a cluster based on its first article."""
        if not cluster:
            return 0.0
        
        article = cluster[0]
        date_str = article.get('published_at') or article.get('processed_at')
        if not date_str:
            return 0.0
            
        try:
            from datetime import datetime
            return datetime.fromisoformat(date_str).timestamp()
        except Exception:
            return 0.0