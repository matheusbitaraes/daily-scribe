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
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <style>
                /* Reset and base styles */
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                    background-color: #ffffff;
                    -webkit-text-size-adjust: 100%;
                    -ms-text-size-adjust: 100%;
                }
                
                /* Container with mobile-first approach */
                .content {
                    width: 100% !important;
                    max-width: 600px !important;
                    margin: 0 auto !important;
                    padding: 16px !important;
                }
                
                /* Category headers - mobile optimized */
                .category {
                    margin: 24px 0 16px 0 !important;
                    font-size: 18px !important;
                    font-weight: bold !important;
                    color: #0a97f5 !important;
                    border-bottom: 2px solid #0a97f5 !important;
                    padding-bottom: 8px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.5px !important;
                }
                
                /* First category has less top margin */
                .category:first-of-type {
                    margin-top: 8px !important;
                }
                
                /* Article containers */
                .article {
                    margin-bottom: 20px !important;
                    padding-bottom: 16px !important;
                    border-bottom: 1px solid #e0e0e0 !important;
                }
                
                .article.last-in-category {
                    border-bottom: none !important;
                    margin-bottom: 32px !important;
                }
                
                /* Article titles - larger and more prominent on mobile */
                .title {
                    font-size: 16px !important;
                    font-weight: 700 !important;
                    line-height: 1.4 !important;
                    color: #1a1a1a !important;
                    margin-bottom: 8px !important;
                    display: block !important;
                }
                
                /* Summary text - optimized for mobile reading */
                .summary {
                    font-size: 15px !important;
                    line-height: 1.5 !important;
                    color: #444444 !important;
                    text-align: left !important;
                    margin-bottom: 8px !important;
                }
                
                /* Media queries for larger screens */
                @media screen and (min-width: 480px) {
                    .content {
                        padding: 24px !important;
                    }
                    .category {
                        font-size: 20px !important;
                        margin: 32px 0 20px 0 !important;
                    }
                    .title {
                        font-size: 17px !important;
                    }
                    .summary {
                        font-size: 16px !important;
                    }
                }
                
                @media screen and (min-width: 768px) {
                    .content {
                        padding: 32px !important;
                    }
                    .category {
                        font-size: 22px !important;
                    }
                    .title {
                        font-size: 18px !important;
                    }
                }
                
                /* Dark mode support */
                @media (prefers-color-scheme: dark) {
                    body {
                        background-color: #1a1a1a !important;
                        color: #e0e0e0 !important;
                    }
                    .title {
                        color: #ffffff !important;
                    }
                    .summary {
                        color: #cccccc !important;
                    }
                    .article {
                        border-bottom-color: #404040 !important;
                    }
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
                <div class="{article_class}">
                    <p class="summary">
                    <span class="title">{summary['title']}:</span> {summary['summary']} <a href="{summary['url']}">[link]</a>
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