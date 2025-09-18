"""
DigestBuilder service for Daily Scribe application.

This module handles building the HTML digest from article summaries.
"""

from typing import List, Dict
from collections import defaultdict

STANDARD_CATEGORY_ORDER = [  # Fixed typo: STANDAND -> STANDARD
    'Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports', 'Other'
]

class DigestBuilder:
    @staticmethod
    def build_html_digest(clustered_summaries: List[List[Dict[str, str]]], preference_token: str = "", unsubscribe_link_html: str = "", max_clusters: int = 20, base_url: str = "http://localhost:3000") -> str:
        category_translation = {
            'Politics': 'Política',
            'Technology': 'Tecnologia',
            'Science and Health': 'Saúde E Ciência',
            'Business': 'Negócios',
            'Entertainment': 'Entretenimento',
            'Sports': 'Esportes',
            'Other': 'Outros'
        }

        # Group clusters by category
        categories = defaultdict(list)
        for cluster in clustered_summaries:
            if cluster:
                # Use the first article's category for the entire cluster
                category = cluster[0].get('category', 'Other') or 'Other'
                category_pt = category_translation.get(category, category)
                categories[category_pt].append(cluster)

        html_digest = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #fff;
                }
                .content {
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 16px;
                }
                .category {
                    margin: 24px 0 12px 0;
                    font-size: 18px;
                    font-weight: bold;
                    color: #0a97f5;
                    border-bottom: 2px solid #0a97f5;
                    padding-bottom: 6px;
                }
                .cluster {
                    margin-bottom: 20px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid #e0e0e0;
                }
                .title {
                    font-size: 16px;
                    font-weight: 700;
                    color: #1a1a1a;
                    margin-bottom: 6px;
                }
                .summary {
                    font-size: 15px;
                    color: #444;
                    margin-bottom: 10px;
                }
                .related-list {
                    margin: 6px 0 0 16px;
                    padding: 0;
                    list-style-type: disc;
                }
                .related-list li {
                    margin-bottom: 3px;
                    font-size: 12px;
                    line-height: 1.4;
                }
                .related-list a {
                    color: #0a97f5;
                    text-decoration: none;
                    opacity: 0.8;
                }
                .related-list a:hover {
                    text-decoration: underline;
                    opacity: 1;
                }
                .view-more-button {
                    margin: 24px 0;
                    text-align: center;
                }
                .view-more-button a {
                    display: inline-block;
                    background-color: #0a97f5;
                    color: white;
                    text-decoration: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 14px;
                    transition: background-color 0.2s ease;
                    margin: 10px;
                }
                .view-more-button a:hover {
                    background-color: #0878d1;
                }
                /* Mobile optimizations */
                @media (max-width: 600px) {
                    .related-list {
                        margin: 4px 0 0 14px;
                    }
                    .related-list li {
                        margin-bottom: 2px;
                        font-size: 11px;
                        line-height: 1.3;
                    }
                }
            </style>
        </head>
        <body>

        <div class="content">
        """

        # Process categories in the specified order
        cluster_count = 0
        max_clusters_reached = False
        
        # Calculate how many categories actually have content
        active_categories = [category_en for category_en in STANDARD_CATEGORY_ORDER 
                           if category_translation.get(category_en, category_en) in categories]
        
        # Calculate clusters per category (distribute evenly)
        clusters_per_category = max_clusters // len(active_categories) if active_categories else max_clusters
        remaining_clusters = max_clusters % len(active_categories) if active_categories else 0
        
        for category_index, category_en in enumerate(STANDARD_CATEGORY_ORDER):
            if max_clusters_reached:
                break
                
            category_pt = category_translation.get(category_en, category_en)
            if category_pt in categories:
                html_digest += f'<div class="category">{category_pt}</div>'
                
                # Calculate limit for this category (add 1 extra to first categories if there's remainder)
                category_limit = clusters_per_category + (1 if category_index < remaining_clusters else 0)
                category_cluster_count = 0
                
                # Sort clusters within category by urgency + impact scores (highest first), then by size (largest first)
                def get_cluster_sort_key(cluster):
                    if not cluster:
                        return (0, 0, 0)
                    main_article = cluster[0]
                    urgency = main_article.get('urgency_score', 0) or 0
                    impact = main_article.get('impact_score', 0) or 0
                    cluster_size = len(cluster)
                    return (-(urgency + impact), -cluster_size)
                
                sorted_clusters = sorted(categories[category_pt], key=get_cluster_sort_key)
                
                for cluster in sorted_clusters:
                    # Check if adding this cluster would exceed the category or global limit
                    if category_cluster_count >= category_limit or cluster_count >= max_clusters:
                        if cluster_count >= max_clusters:
                            max_clusters_reached = True
                        break
                    
                    cluster_count += 1
                    category_cluster_count += 1
                    html_digest += '<div class="cluster">'
                    main_article = cluster[0]
                    source = main_article.get('source_name')
                    if not source:
                        source = 'link'
                    
                    # Use Portuguese summary if available, otherwise fallback to English
                    preferred_summary = main_article.get('summary_pt') or main_article.get('summary', '')
                    
                    html_digest += f"""
                    <div class="main-article">
                        <p class="summary">
                            <span class="title">{main_article['title']}:</span>
                            {preferred_summary} <a href="{main_article['url']}">[{source}]</a>
                        </p>
                    </div>
                    """
                    if len(cluster) > 1:
                        html_digest += '<ul class="related-list">'
                        for article in cluster[1:]:
                            related_source = article.get('source_name')
                            if not related_source:
                                title = article['title']
                            else:
                                title = f"[{related_source}] {article['title']}"
                            html_digest += f"""
                            <li>
                                <a href="{article['url']}">{title}</a>
                            </li>
                            """
                        html_digest += '</ul>'
                    html_digest += '</div>'
        
        if preference_token:
            html_digest += '<div class="view-more-button">'
            
            # Add "View more in browser" button if cluster limit was reached
            view_more_url = f"{base_url}/news"
            html_digest += f'<a href="{view_more_url}">Ver todas as notícias</a>'
            
            # Add preference button if token is provided
            
            preference_url = f"{base_url}/preferences/{preference_token}"
            # Add margin if both buttons are present
            html_digest += f'<a href="{preference_url}"">Gerenciar preferências</a>'
            
            html_digest += '</div>'

        # Add unsubscribe link at the bottom if provided
        if unsubscribe_link_html:
            html_digest += unsubscribe_link_html

        html_digest += "</div></body></html>"
        return html_digest

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