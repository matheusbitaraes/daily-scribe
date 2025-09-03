"""
Default feed parser.
"""
from typing import List
import feedparser
from .base_parser import BaseParser, ContentPart
from .utils import remove_html_tags

class DefaultParser(BaseParser):
    """Default parser for RSS feeds."""

    def parse(self, entry: feedparser.FeedParserDict) -> List[ContentPart]:
        """
        Parse a single feed entry and return a list of content parts.

        This default parser checks for 'content' and then 'description'.

        Args:
            entry: A feedparser entry dictionary.

        Returns:
            A list of ContentPart objects.
        """
        parts = []
        if 'title_detail' in entry and entry.title_detail and 'value' in entry.title_detail and entry.title_detail.value and entry.title_detail.value != '':
            parts.append(ContentPart(text=remove_html_tags(entry.title_detail.value), type='title'))
        elif 'title' in entry and entry.title:
            parts.append(ContentPart(text=remove_html_tags(entry.title), type='title'))

        # summary append
        if 'summary_detail' in entry and entry.summary_detail and 'value' in entry.summary_detail and entry.summary_detail.value and entry.summary_detail.value != '':
            parts.append(ContentPart(text=remove_html_tags(entry.summary_detail.value), type='summary'))
        elif 'summary' in entry and entry.summary:
            parts.append(ContentPart(text=remove_html_tags(entry.summary), type='summary'))

        # subtitle append
        if 'subtitle_detail' in entry and entry.subtitle_detail and 'value' in entry.subtitle_detail and entry.subtitle_detail.value and entry.subtitle_detail.value != '':
            parts.append(ContentPart(text=remove_html_tags(entry.subtitle_detail.value), type='subtitle'))
        elif 'subtitle' in entry and entry.subtitle:
            parts.append(ContentPart(text=remove_html_tags(entry.subtitle), type='subtitle'))

        # description append
        if 'description_detail' in entry and entry.description_detail and 'value' in entry.description_detail and entry.description_detail.value and entry.description_detail.value != '':
            parts.append(ContentPart(text=remove_html_tags(entry.description_detail.value), type='description'))
        elif 'description' in entry and entry.description:
            parts.append(ContentPart(text=remove_html_tags(entry.description), type='description'))

        # content append
        if 'content' in entry and entry.content:
            for content in entry.content:
                if 'value' in content and content.value and content.value != '':
                    parts.append(ContentPart(text=remove_html_tags(content.value), type='content'))


        return parts
