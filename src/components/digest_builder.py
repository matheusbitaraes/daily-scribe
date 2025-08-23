"""
DigestBuilder service for Daily Scribe application.

This module handles building the HTML digest from article summaries.
"""

from typing import List, Dict

class DigestBuilder:
    @staticmethod
    def build_html_digest(summaries: List[Dict[str, str]]) -> str:
        html_digest = """
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0 20%;
                }
                .article {
                    margin-bottom: 25px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eeeeee;
                }
                .title a {
                    color: #1a0dab;
                    text-decoration: none;
                    font-size: 18px;
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
        for summary in summaries:
            html_digest += f"""
            <div class=\"article\">
                <div class=\"title\">
                    <strong>{summary['title']}</strong>
                </div>
                <p class=\"summary\">
                    {summary['summary']}<br>
                    <a href=\"{summary['link']}\">Leia a matéria completa</a>
                </p>
            </div>
            """
        html_digest += """
            </body>
        </html>
        """
        return html_digest
