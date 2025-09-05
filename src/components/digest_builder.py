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
    def build_html_digest(clustered_summaries: List[List[Dict[str, str]]]) -> str:
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
                    margin: 8px 0 0 18px;
                    padding: 0;
                    list-style-type: disc;
                }
                .related-list li {
                    margin-bottom: 6px;
                    font-size: 14px;
                }
                .related-list a {
                    color: #0a97f5;
                    text-decoration: none;
                }
                .related-list a:hover {
                    text-decoration: underline;
                }
                @media (prefers-color-scheme: dark) {
                    body { background-color: #1a1a1a; color: #e0e0e0; }
                    .title { color: #fff; }
                    .summary { color: #ccc; }
                    .cluster { border-bottom-color: #404040; }
                    .related-list a { color: #4db8ff; }
                }
            </style>
        </head>
        <body>

        <div class="content">
        <div style="background-color: #f0f8ff; border: 1px solid #0a97f5; border-radius: 6px; padding: 12px; margin-bottom: 20px; font-size: 14px; color: #0066cc;">
            <strong>Você está em Beta!</strong> Se tiver algum feedback sobre as notícias, pode responder nesse próprio email.
        </div>
        """

        # Process categories in the specified order
        for category_en in STANDARD_CATEGORY_ORDER:
            category_pt = category_translation.get(category_en, category_en)
            if category_pt in categories:
                html_digest += f'<div class="category">{category_pt}</div>'
                
                # Sort clusters within category by size (largest first), then by date (newest first)
                sorted_clusters = sorted(
                    categories[category_pt],
                    key=lambda cluster: (len(cluster), DigestBuilder._get_cluster_date(cluster)),
                    reverse=True
                )
                
                for cluster in sorted_clusters:
                    html_digest += '<div class="cluster">'
                    main_article = cluster[0]
                    source = main_article.get('source_name')
                    if not source:
                        source = 'link'
                    html_digest += f"""
                    <div class="main-article">
                        <p class="summary">
                            <span class="title">{main_article['title']}:</span>
                            {main_article['summary']} <a href="{main_article['url']}">[{source}]</a>
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