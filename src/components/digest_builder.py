"""
DigestBuilder service for Daily Scribe application.

This module handles building the HTML digest from article summaries.
"""

from typing import List, Dict

STANDAND_CATEGORY_ORDER = [
    'Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports', 'Other' ]

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

        # Flatten clusters
        all_summaries = []
        for cluster in clustered_summaries:
            if cluster:
                all_summaries.extend(cluster)

        from collections import defaultdict
        categories = defaultdict(list)
        ordered_summaries = DigestBuilder.order_summaries(all_summaries, STANDAND_CATEGORY_ORDER)

        ordered_clusters = []
        for cluster in clustered_summaries:
            if cluster:
                cluster_ordered = sorted(
                    cluster,
                    key=lambda x: next((i for i, s in enumerate(ordered_summaries) if s == x), float('inf'))
                )
                ordered_clusters.append(cluster_ordered)

        for cluster in ordered_clusters:
            if cluster:
                category = cluster[0].get('category', 'Outros') or 'Outros'
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
        """

        for category, clusters in categories.items():
            html_digest += f'<div class="category">{category}</div>'
            for cluster in clusters:
                html_digest += '<div class="cluster">'
                main_article = cluster[0]
                html_digest += f"""
                <div class="main-article">
                    <p class="summary">
                        <span class="title">{main_article['title']}:</span>
                        {main_article['summary']} <a href="{main_article['url']}">[link]</a>
                    </p>
                </div>
                """
                if len(cluster) > 1:
                    html_digest += '<ul class="related-list">'
                    for article in cluster[1:]:
                        html_digest += f"""
                        <li>
                            <a href="{article['url']}">{article['title']}</a>
                        </li>
                        """
                    html_digest += '</ul>'
                html_digest += '</div>'

        html_digest += "</div></body></html>"
        return html_digest

    @staticmethod
    def order_summaries(summaries: List[Dict[str, str]], category_order: List[str]) -> List[Dict[str, str]]:
        """
        Order summaries by category (custom order) and date (descending by published_at or processed_at).
        Args:
            summaries: List of article dicts.
            category_order: List of category names in desired order.
        Returns:
            Ordered list of summaries.
        """
        # Create a mapping for category priority
        category_priority = {cat: i for i, cat in enumerate(category_order)}
        def sort_key(summary):
            cat = summary.get('category', 'Other')
            cat_idx = category_priority.get(cat, len(category_priority))
            # Try published_at, fallback to processed_at, fallback to datetime.min
            date_str = summary.get('published_at') or summary.get('processed_at')
            try:
                from datetime import datetime
                date_val = datetime.fromisoformat(date_str) if date_str else datetime(1970, 1, 1)
            except Exception:
                date_val = datetime(1970, 1, 1)
            # Sort by category priority, then by date descending
            return (cat_idx, -date_val.timestamp())
        return sorted(summaries, key=sort_key)