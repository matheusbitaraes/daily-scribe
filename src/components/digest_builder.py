"""
DigestBuilder service for Daily Scribe application.

This module handles building the HTML digest from article summaries.
"""

from typing import List, Dict

class DigestBuilder:
    @staticmethod
    def build_html_digest(summaries: List[Dict[str, str]]) -> str:
        # Category translation map (English to Brazilian Portuguese)
        category_translation = {
            'Politics': 'Política',
            'Technology': 'Tecnologia',
            'Health': 'Saúde',
            'Business': 'Negócios',
            'Entertainment': 'Entretenimento',
            'Sports': 'Esportes',
            'Science': 'Ciência',
            'World': 'Mundo',
            'Economy': 'Economia',
            'Education': 'Educação',
            'Environment': 'Meio Ambiente',
            'Other': 'Outros',
        }
        # Group articles by translated category
        from collections import defaultdict
        categories = defaultdict(list)
        for summary in summaries:
            category = summary.get('category', 'Outros') or 'Outros'
            category_pt = category_translation.get(category, category)
            categories[category_pt].append(summary)

        html_digest = """
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0 20%;
                }
                .category {
                    margin-top: 40px;
                    margin-bottom: 10px;
                    font-size: 22px;
                    font-weight: bold;
                    color: #333366;
                    border-bottom: 2px solid #cccccc;
                    padding-bottom: 5px;
                }
                .article {
                    margin-bottom: 25px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eeeeee;
                }
                .title {
                    font-size: 18px;
                    font-weight: bold;
                }
                .summary {
                    text-align: justify;
                    font-size: 14px;
                    color: #333333;
                }
            </style>
        </head>
        <body>
        """
        for category, articles in categories.items():
            html_digest += f'<div class="category">{category}</div>'
            for summary in articles:
                html_digest += f"""
                <div class=\"article\">
                    <div class=\"title\">{summary['title']}</div>
                    <p class=\"summary\">{summary['summary']}<br>
                    <a href=\"{summary['link']}\">Leia a matéria completa</a>
                    </p>
                </div>
                """
        html_digest += """
            </body>
        </html>
        """
        return html_digest
