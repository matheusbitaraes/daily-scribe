"""
DigestBuilder service for Daily Scribe application.

This module handles building the HTML digest from article summaries.
"""

from typing import List, Dict

STANDAND_CATEGORY_ORDER = [
    'Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports', 'Other' ]

class DigestBuilder:
    @staticmethod
    def build_html_digest(summaries: List[Dict[str, str]]) -> str:
        # Category translation map (English to Brazilian Portuguese)
        category_translation = {
            'Politics': 'Política',
            'Technology': 'Tecnologia',
            'Science and Health': 'Saúde E Ciência',
            'Business': 'Negócios',
            'Entertainment': 'Entretenimento',
            'Sports': 'Esportes',
            'Other': 'Outros'
        }
        # Group articles by translated category
        from collections import defaultdict
        categories = defaultdict(list)
        ordered_summaries = DigestBuilder.order_summaries(summaries, STANDAND_CATEGORY_ORDER)
        for summary in ordered_summaries:
            category = summary.get('category', 'Outros') or 'Outros'
            category_pt = category_translation.get(category, category)
            categories[category_pt].append(summary)

        html_digest = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Google Sans", Roboto, RobotoDraft, Helvetica, Arial, sans-serif;
                    line-height: 26px;
                    color: #333333
                }
                .content {
                    margin: 0 20%;
                    min-width: 500px;
                }
                .category {
                    margin-bottom: 10px;
                    font-size: 20px;
                    font-weight: bold;
                    color: #0a97f5;
                    border-bottom: 2px solid #0a97f5;
                    padding-bottom: 5px;
                }
                .article {
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eeeeee;
                }
                .content .last-in-category {
                    border-bottom: none !important;
                }
                .title {
                    font-size: 17px;
                    font-weight: 700;
                }
                .summary {
                    text-align: justify;
                    font-size: 17px;
                    color: #333333
                }
            </style>
        </head>
        <body>
        <div class="content">
        """
        for category, articles in categories.items():
            html_digest += f'<div class="category">{category}</div>'
            for i, summary in enumerate(articles):
                # Check if this is the last article in this category
                is_last_in_category = (i == len(articles) - 1)
                article_class = "article last-in-category" if is_last_in_category else "article"
                
                html_digest += f"""
                <div class=\"{article_class}\">
                    <p class=\"summary\">
                    <span class=\"title\">{summary['title']}:</span> {summary['summary']} <a href=\"{summary['link']}\">[link]</a>
                    </p>
                </div>
                """
        html_digest += """
        </div>
        </body>
        </html>
        """
        return html_digest

    @staticmethod
    def order_summaries(summaries: List[Dict[str, str]], category_order: List[str]) -> List[Dict[str, str]]:
        """
        Order summaries by category (custom order) and date (descending by published_at).
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
            # Parse published_at as string (ISO) or fallback to 0
            date_str = summary.get('published_at')
            try:
                from datetime import datetime
                date_val = datetime.fromisoformat(date_str) if date_str else datetime.min
            except Exception:
                date_val = datetime.min
            # Sort by category priority, then by date descending
            return (cat_idx, -date_val.timestamp())
        return sorted(summaries, key=sort_key)