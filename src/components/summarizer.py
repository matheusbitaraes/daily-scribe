"""
Summarization service for Daily Scribe application.

This module handles summarizing article text using the LLM abstraction layer
(LiteLLM) with support for multiple free-tier and paid providers.
"""

import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .llm import LLMClient


class NewsMetadata(BaseModel):
    summary: str = Field(description="Summarize the following text in approximately 40 to 100 words and DO IT ALWAYS IN THE ORIGINAL LANGUAGE OF THE ARTICLE (LIMITED TO ENGLISH OR BRAZILIAN PORTUGUESE).")
    summary_pt: str = Field(description="Summarize the following text in approximately 40 to 100 words and DO IT ALWAYS IN PORTUGUESE, no matter the original language of the article. Make the summary as a news article summary. Don't repeat information that is present in the title. Make it concise and interesting")
    title_pt: str = Field(description="Translate the title of the article to Portuguese. If the original title is already in Portuguese, repeat it exactly as is. Attention: don't make the title will all words in capital leters. Example, instead of 'Dólar Atinge Nível Mais Alto Devido à China', do 'Dólar atinge nível mais alto devido à China")
    sentiment: str = Field(description="The overall sentiment of the article (Positive, Negative, Neutral).")
    keywords: List[str] = Field(description="A list of key people, organizations, or locations mentioned.")
    category: str = Field(description="The main category of the news. Select one of those options: 'Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports'. Use the category 'Other' if none of the options fit.")
    region: str = Field(description="The primary geographical place the news is about (e.g., Brazil, USA, Europe, Asia).")
    urgency_score: int = Field(description="Rate the urgency of this news on a scale of 0-100. 0-20=Evergreen (timeless content), 21-40=Long-Term (relevant for weeks/months), 41-60=Topical (recent events, follow-up), 61-80=Time-Sensitive (urgent, needs attention within days), 81-100=Breaking News (happening now or just occurred).")
    impact_score: int = Field(description="Rate the impact of this news on a scale of 0-100. 0-20=Minor Update (very low impact, small number of people), 21-40=Niche Impact (significant to specific community), 41-60=Moderate Impact (affects large community), 61-80=Significant Impact (major consequences for region/country/industry), 81-100=Major Development (landmark event with profound consequences).")
    subject_pt: str = Field(description="Create a very short 2-4 word phrase in Portuguese that can be used as part of an email subject line to represent this news headline. Make a cohesive very small phrase that captures the essence of the news. You can use prepositions, they don't count. So, intead of 'Conflito Gaza', you should use 'Conflito em Gaza'")


class Summarizer:
    """Handles summarizing text using the LLM abstraction layer (multi-provider)."""

    def __init__(self):
        """Initialize the summarizer with the LLM client."""
        self.logger = logging.getLogger(__name__)
        self._llm = LLMClient()

    def summarize(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Summarize the given text and extract metadata.

        Args:
            text: The article text to summarize.
            max_retries: Number of retries for transient failures (passed to LLM client).

        Returns:
            Dict with keys matching NewsMetadata (summary, summary_pt, title_pt, etc.),
            or empty dict on failure.
        """
        return self._generate_full_metadata(text, max_retries)

    def _generate_full_metadata(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
        """Generate full metadata including summary."""
        return self._generate_with_schema(
            text, NewsMetadata, max_retries,
            "Extract the requested metadata from the following news content"
        )

    def _generate_with_schema(
        self,
        text: str,
        schema_class: type,
        max_retries: int,
        prompt_prefix: str,
    ) -> Dict[str, Any]:
        """Generate content using the specified schema via the LLM abstraction."""
        messages = [
            {
                "role": "system",
                "content": f"{prompt_prefix}. Follow the JSON schema exactly and return only JSON, no prose.",
            },
            {"role": "user", "content": text},
        ]
        result = self._llm.complete_with_schema(
            messages=messages,
            response_model=schema_class,
            prompt_prefix="",
            max_retries=max_retries,
        )
        return result if result is not None else {}
