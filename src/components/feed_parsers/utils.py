"""
This module provides utility functions for feed parsing.
"""
import re
from bs4 import BeautifulSoup

def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from a string, unescape HTML entities,
    and strip leading/trailing spaces.

    Args:
        text: The input string.

    Returns:
        The string with HTML tags removed, entities unescaped,
        and leading/trailing spaces stripped.
    """
    if not text:
        return ""
    # It's possible that the text is already plain text.
    # If it's not, we'll use BeautifulSoup to parse it.
    if re.search(r'<\s*[a-z-][^>]*\s*>', text, re.IGNORECASE):
        # BeautifulSoup handles HTML tags and unescapes entities.
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text().strip()
    return text.strip()
