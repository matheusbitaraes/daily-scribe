"""
Base class for all feed parsers.
"""
from abc import ABC, abstractmethod
from typing import List
import feedparser
from dataclasses import dataclass

@dataclass
class ContentPart:
    """Represents a part of the content extracted from a feed entry."""
    text: str
    type: str  # e.g., 'title', 'summary', 'content'

class BaseParser(ABC):
    """Abstract base class for feed parsers."""

    @abstractmethod
    def parse(self, entry: feedparser.FeedParserDict) -> List[ContentPart]:
        """
        Parse a single feed entry and return a list of content parts.

        Args:
            entry: A feedparser entry dictionary.

        Returns:
            A list of ContentPart objects, or an empty list if no content could be found.
        """
        raise NotImplementedError
